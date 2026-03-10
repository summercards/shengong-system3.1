# orchestrator.py - M3-1 Orchestrator / StoryCycle 核心实现
"""
Orchestrator - 故事循环核心编排器
负责协调整个写作流程：Planner → Writer → Critic → LoreKeeper

核心职责：
1. StoryCycle 管理 - 章节写作循环
2. Agent 协调 - Planner/Writer/Critic/LoreKeeper 协作
3. 任务队列管理 - writing_jobs 表操作
4. 质量控制 - 审查与重写机制
"""

import os
import json
import yaml
import glob
from typing import Optional, Any
from datetime import datetime

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加父目录（神工系统根目录）到路径，以便导入 openclaw_api
PARENT_DIR = os.path.dirname(PROJECT_ROOT)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# 导入项目模块
from database import (
    get_connection, execute_write, execute_query,
    create_project, get_project, update_project_status, increment_chapter,
    create_job, get_job, update_job_status, log_event
)
from structured_store import StructuredStore
from utils.schema_validator import validate_data


# 默认配置
DEFAULT_TARGET_LENGTH = 1200  # 每章默认字数
DEFAULT_BEAT_TYPES = ["hook", "setup", "conflict", "peak", "cliffhanger"]


class Orchestrator:
    """
    Orchestrator - 故事循环编排器
    协调整个 AI 写作流程
    """
    
    def __init__(self, project_id: str = "default", config_path: str = "config/world_setting.yaml"):
        self.project_id = project_id
        self.config_path = config_path
        self.config = self._load_config()
        self.store = StructuredStore()
        
        # Agent 实例（延迟初始化）
        self._planner = None
        self._writer = None
        self._critic = None
        self._lorekeeper = None
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    # === Agent 初始化 ===
    
    @property
    def planner(self):
        """Planner Agent - 章节规划"""
        if self._planner is None:
            from openclaw_api import OpenClawClient
            
            # 加载 Planner Prompt
            prompt_path = "prompts/planner_prompt.txt"
            system_prompt = ""
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
            else:
                system_prompt = self._get_default_planner_prompt()
            
            self._planner = {
                "client": OpenClawClient(),
                "system_prompt": system_prompt
            }
        return self._planner
    
    @property
    def writer(self):
        """Writer Agent - 内容生成"""
        if self._writer is None:
            from openclaw_api import OpenClawClient
            
            # 加载 Writer Prompt
            prompt_path = "prompts/writer_prompt.txt"
            system_prompt = ""
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
            else:
                system_prompt = self._get_default_writer_prompt()
            
            self._writer = {
                "client": OpenClawClient(),
                "system_prompt": system_prompt
            }
        return self._writer
    
    @property
    def critic(self):
        """Critic Agent - 内容审查"""
        if self._critic is None:
            from openclaw_api import OpenClawClient
            
            # 加载 Critic Prompt
            prompt_path = "prompts/critic_prompt.txt"
            system_prompt = ""
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
            else:
                system_prompt = self._get_default_critic_prompt()
            
            self._critic = {
                "client": OpenClawClient(),
                "system_prompt": system_prompt
            }
        return self._critic
    
    @property
    def lorekeeper(self):
        """LoreKeeper - 世界观同步"""
        if self._lorekeeper is None:
            from lorekeeper_agent import LoreKeeper
            self._lorekeeper = LoreKeeper(self.project_id)
        return self._lorekeeper
    
    # === StoryCycle 核心方法 ===
    
    def start_project(self, title: str, genre: str, logline: str = "", 
                      target_chapters: int = 10, interval_minutes: int = 60) -> dict:
        """
        启动新项目
        """
        # 创建项目
        success, msg, row_id = self.store.create_project(
            project_id=self.project_id,
            title=title,
            genre=genre,
            logline=logline,
            target_chapters=target_chapters,
            interval_minutes=interval_minutes
        )
        
        if not success:
            return {"status": "failed", "message": msg}
        
        # 更新状态为 running
        self.store.update_project(self.project_id, status="running")
        
        # 记录事件
        log_event(
            project_id=self.project_id,
            chapter_number=0,
            event_type="project_started",
            summary=f"项目启动: {title}",
            data={"genre": genre, "target_chapters": target_chapters}
        )
        
        return {
            "status": "success",
            "message": f"项目 {title} 启动成功",
            "project_id": self.project_id,
            "target_chapters": target_chapters
        }
    
    def get_next_chapter(self) -> int:
        """
        获取下一章编号
        """
        project = get_project(self.project_id)
        if not project:
            return 1
        current = project.get('current_chapter', 0)
        return current + 1
    
    def plan_chapter(self, chapter_num: int, user_outline: str = "") -> dict:
        """
        规划章节 - 调用 Planner Agent
        """
        # 构建上下文
        context = self._build_planning_context(chapter_num)
        
        # 添加用户大纲
        if user_outline:
            context += f"\n\n用户指定大纲:\n{user_outline}"
        
        # 调用 Planner
        try:
            result = self.planner["client"].generate_with_retry(
                system_prompt=self.planner["system_prompt"],
                user_prompt=context,
                max_tokens=2000
            )
            
            # 解析结果
            plan = self._parse_planner_result(result)
            
            # 记录事件
            log_event(
                project_id=self.project_id,
                chapter_number=chapter_num,
                event_type="chapter_planned",
                summary=f"第 {chapter_num} 章规划完成",
                data=plan
            )
            
            return {
                "status": "success",
                "chapter_num": chapter_num,
                "plan": plan
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"规划失败: {str(e)}"
            }
    
    def write_chapter(self, chapter_num: int, outline: str = "", 
                      target_length: int = None) -> dict:
        """
        写作章节 - 调用 Writer Agent
        """
        if target_length is None:
            target_length = self.config.get('chapters', {}).get('target_length', DEFAULT_TARGET_LENGTH)
        
        # 获取项目信息
        project = get_project(self.project_id)
        if not project:
            return {"status": "failed", "message": "项目不存在"}
        
        # 创建写作任务
        success, msg, job_id = self.store.create_job(self.project_id, chapter_num)
        if not success:
            return {"status": "failed", "message": msg}
        
        # 更新任务状态为 running
        update_job_status(job_id, "running")
        
        # 构建写作上下文
        context = self._build_writing_context(chapter_num, outline, target_length)
        
        # 调用 Writer
        try:
            result = self.writer["client"].generate_with_retry(
                system_prompt=self.writer["system_prompt"],
                user_prompt=context,
                max_tokens=3000
            )
            
            # 解析结果（分离正文和结构化数据）
            text, structured = self._parse_writer_result(result)
            
            # 更新任务
            word_count = len(text)
            self.store.update_job(job_id, status="completed", content=text, word_count=word_count)
            
            # 记录事件
            log_event(
                project_id=self.project_id,
                chapter_number=chapter_num,
                event_type="chapter_written",
                summary=f"第 {chapter_num} 章写作完成",
                data={"word_count": word_count, "job_id": job_id}
            )
            
            return {
                "status": "success",
                "chapter_num": chapter_num,
                "content": text,
                "structured": structured,
                "word_count": word_count,
                "job_id": job_id
            }
        except Exception as e:
            update_job_status(job_id, "failed")
            return {
                "status": "failed",
                "message": f"写作失败: {str(e)}"
            }
    
    def review_chapter(self, text: str) -> dict:
        """
        审查章节 - 调用 Critic Agent
        """
        # 调用 Critic
        try:
            result = self.critic["client"].generate_with_retry(
                system_prompt=self.critic["system_prompt"],
                user_prompt=f"请审查以下章节内容:\n\n{text[:5000]}",
                max_tokens=1500
            )
            
            # 解析审查结果
            review = self._parse_critic_result(result)
            
            return review
        except Exception as e:
            return {
                "score": 0,
                "feedback": f"审查失败: {str(e)}",
                "needs_revision": True
            }
    
    def sync_lore(self, structured_data: dict) -> dict:
        """
        同步世界观 - 调用 LoreKeeper
        """
        try:
            # 转换为 LoreKeeper 格式
            updates = self._convert_to_lorekeeper_updates(structured_data)
            
            results = []
            for update in updates:
                result = self.lorekeeper.apply_structured_update(update)
                results.append(result)
            
            return {
                "status": "success",
                "updates_applied": len(results),
                "results": results
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"世界观同步失败: {str(e)}"
            }
    
    # === StoryCycle 完整流程 ===
    
    def story_cycle(self, chapter_num: int = None, user_outline: str = "",
                    target_length: int = None, auto_advance: bool = True) -> dict:
        """
        完整的故事循环：规划 → 写作 → 审查 → 同步
        
        参数:
            chapter_num: 指定章节编号（None 则自动获取下一章）
            user_outline: 用户提供的章节大纲
            target_length: 目标字数
            auto_advance: 是否自动进入下一章
        
        返回: 完整的执行结果
        """
        # 确定章节编号
        if chapter_num is None:
            chapter_num = self.get_next_chapter()
        
        results = {
            "chapter_num": chapter_num,
            "stages": {}
        }
        
        # Stage 1: 规划
        print(f"\n{'='*50}")
        print(f"[Orchestrator] 第 {chapter_num} 章 - 故事循环开始")
        print(f"{'='*50}")
        
        plan_result = self.plan_chapter(chapter_num, user_outline)
        results["stages"]["planning"] = plan_result
        
        if plan_result["status"] != "success":
            return results
        
        outline = plan_result.get("plan", {}).get("outline", "")
        
        # Stage 2: 写作
        write_result = self.write_chapter(chapter_num, outline, target_length)
        results["stages"]["writing"] = write_result
        
        if write_result["status"] != "success":
            return results
        
        text = write_result["content"]
        structured = write_result.get("structured", {})
        
        # Stage 3: 审查
        review_result = self.review_chapter(text)
        results["stages"]["review"] = review_result
        
        # 如果审查不通过，标记需要修改
        if review_result.get("needs_revision", False):
            print(f"[Orchestrator] 章节 {chapter_num} 审查未通过，需要修改")
            results["needs_revision"] = True
        
        # Stage 4: 同步世界观
        if structured:
            sync_result = self.sync_lore(structured)
            results["stages"]["sync"] = sync_result
        
        # 保存输出
        self._save_chapter_output(chapter_num, text, results)
        
        # 更新章节计数
        if auto_advance:
            increment_chapter(self.project_id)
        
        # 完成事件
        log_event(
            project_id=self.project_id,
            chapter_number=chapter_num,
            event_type="chapter_completed",
            summary=f"第 {chapter_num} 章完成",
            data={"word_count": write_result.get("word_count", 0)}
        )
        
        print(f"\n[Orchestrator] 第 {chapter_num} 章故事循环完成!")
        
        return results
    
    # === 辅助方法 ===
    
    def _build_planning_context(self, chapter_num: int) -> str:
        """构建规划上下文"""
        project = get_project(self.project_id)
        
        context = f"""项目信息:
- 标题: {project.get('title', '')}
- 类型: {project.get('genre', '')}
- 故事线: {project.get('logline', '')}
- 当前章节: {chapter_num}
- 目标章节数: {project.get('target_chapters', 10)}

"""
        
        # 添加前几章摘要
        events = execute_query(
            "SELECT chapter_number, summary FROM events_log WHERE project_id = ? AND event_type = 'chapter_completed' ORDER BY chapter_number DESC LIMIT 3",
            (self.project_id,)
        )
        if events:
            context += "前几章概要:\n"
            for e in reversed(events):
                context += f"- 第{e['chapter_number']}章: {e['summary']}\n"
        
        # 添加角色状态
        context += "\n当前角色状态:\n"
        for char_file in glob.glob("data/characters/*.yaml"):
            with open(char_file, 'r', encoding='utf-8') as f:
                char = yaml.safe_load(f)
                context += f"- {char.get('name', 'Unknown')}: {char.get('dynamic_state', {})}\n"
        
        return context
    
    def _build_writing_context(self, chapter_num: int, outline: str, target_length: int) -> str:
        """构建写作上下文"""
        project = get_project(self.project_id)
        
        context = f"""## 写作任务

### 项目信息
- 标题: {project.get('title', '')}
- 类型: {project.get('genre', '')}
- 故事线: {project.get('logline', '')}

### 章节信息
- 章节编号: {chapter_num}
- 目标字数: {target_length}
- 大纲: {outline}

"""
        
        # 添加详细章节规划
        events = execute_query(
            "SELECT data FROM events_log WHERE project_id = ? AND event_type = 'chapter_planned' AND chapter_number = ?",
            (self.project_id, chapter_num)
        )
        if events and events[0].get('data'):
            try:
                plan_data = json.loads(events[0]['data'])
                context += f"\n章节规划:\n{json.dumps(plan_data, ensure_ascii=False, indent=2)}\n"
            except:
                pass
        
        # 添加角色信息
        context += "\n### 角色状态\n"
        for char_file in glob.glob("data/characters/*.yaml"):
            with open(char_file, 'r', encoding='utf-8') as f:
                char = yaml.safe_load(f)
                char_id = char.get('char_id', '')
                name = char.get('name', '')
                static = char.get('static_profile', {})
                dynamic = char.get('dynamic_state', {})
                context += f"\n**{name}** (ID: {char_id}):\n"
                context += f"- 背景: {static.get('background', '')}\n"
                context += f"- 性格: {static.get('personality', '')}\n"
                context += f"- 当前状态: {dynamic}\n"
        
        return context
    
    def _parse_planner_result(self, result: str) -> dict:
        """解析 Planner 结果"""
        try:
            # 尝试提取 JSON
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "{" in result and "}" in result:
                start = result.find("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
            else:
                return {"outline": result, "beat_tags": ["normal"]}
            
            return json.loads(json_str)
        except:
            return {"outline": result, "beat_tags": ["normal"]}
    
    def _parse_writer_result(self, result: str) -> tuple[str, dict]:
        """解析 Writer 结果"""
        text = result
        structured = {}
        
        try:
            # 尝试提取 JSON 块
            if "```json" in result:
                parts = result.split("```json")
                text = parts[0].strip()
                json_str = parts[1].split("```")[0]
                structured = json.loads(json_str)
            elif "{" in result and "}" in result:
                start = result.rfind("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
                text = result[:start].strip()
                structured = json.loads(json_str)
        except:
            pass
        
        return text, structured
    
    def _parse_critic_result(self, result: str) -> dict:
        """解析 Critic 结果"""
        try:
            # 尝试提取 JSON
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "{" in result and "}" in result:
                start = result.find("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
            else:
                return self._parse_critic_text(result)
            
            return json.loads(json_str)
        except:
            return self._parse_critic_text(result)
    
    def _parse_critic_text(self, text: str) -> dict:
        """从文本解析审查结果"""
        score = 0.5
        needs_revision = True
        feedback = text
        
        # 简单解析
        if "score" in text.lower():
            import re
            match = re.search(r'score[:\s]*(\d+\.?\d*)', text.lower())
            if match:
                score = float(match.group(1))
        
        if "pass" in text.lower() or "good" in text.lower():
            needs_revision = score >= 0.7
        
        return {
            "score": score,
            "needs_revision": needs_revision,
            "feedback": feedback
        }
    
    def _convert_to_lorekeeper_updates(self, structured: dict) -> list:
        """将 Writer 输出的结构化数据转换为 LoreKeeper 格式"""
        updates = []
        
        # 角色更新
        if "character_updates" in structured:
            for char_id, updates_dict in structured["character_updates"].items():
                for field, value in updates_dict.items():
                    update = {
                        "update_type": "character_state",
                        "entity_id": char_id,
                        "field_path": field,
                        "new_value": value,
                        "reason": "Writer output"
                    }
                    updates.append(update)
        
        # 关系更新
        if "events" in structured:
            for event in structured["events"]:
                if event.get("type") == "relationship_change":
                    # 需要从 event 提取关系信息
                    pass
        
        return updates
    
    def _save_chapter_output(self, chapter_num: int, text: str, results: dict):
        """保存章节输出"""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存正文
        with open(f"{output_dir}/chapter_{chapter_num}.md", 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存元数据
        meta = {
            "chapter_num": chapter_num,
            "word_count": len(text),
            "timestamp": datetime.now().isoformat(),
            "results": {
                k: v.get("status", str(v)) for k, v in results.get("stages", {}).items()
            }
        }
        with open(f"{output_dir}/chapter_{chapter_num}_meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # === 默认 Prompt ===
    
    def _get_default_planner_prompt(self) -> str:
        return """你是章节规划 Agent。你的任务是为小说章节创建详细的大纲和节奏规划。

输出格式要求:
```json
{
  "outline": "详细章节大纲",
  "beat_tags": ["hook", "setup", "conflict", "peak", "cliffhanger"],
  "key_events": ["事件1", "事件2"],
  "characters_in_scene": ["char_id1", "char_id2"]
}
```"""
    
    def _get_default_writer_prompt(self) -> str:
        return """你是专业网文写手 Agent。你的任务是按照大纲生成高质量的章节内容。

输出格式:
章节正文内容 + 结尾附加 JSON:
```json
{
  "events": [{"type": "类型", "description": "描述", "involved_characters": ["id1", "id2"]}],
  "character_updates": {"char_id": {"field": "value"}}
}
```"""
    
    def _get_default_critic_prompt(self) -> str:
        return """你是章节审查 Agent。你的任务是评估章节质量。

评估维度:
- 剧情流畅度
- 人物塑造
- 节奏控制
- 文笔质量
- 悬念设置

输出格式:
```json
{
  "score": 0.0-1.0,
  "needs_revision": true/false,
  "feedback": "具体改进建议"
}
```"""


# === 便捷函数 ===

def create_orchestrator(project_id: str = "default") -> Orchestrator:
    """创建 Orchestrator 实例"""
    return Orchestrator(project_id)


def run_story_cycle(project_id: str, chapter_num: int = None, 
                    user_outline: str = "", **kwargs) -> dict:
    """运行完整的故事循环"""
    orch = create_orchestrator(project_id)
    return orch.story_cycle(chapter_num, user_outline, **kwargs)


# 导出
__all__ = ['Orchestrator', 'create_orchestrator', 'run_story_cycle']
