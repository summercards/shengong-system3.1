# export_import.py - M5-2 导入导出与监控
"""
数据导入导出模块
支持项目、章节、配置的导入导出

功能：
1. 项目导出 - JSON/SQL 格式
2. 项目导入 - 从 JSON 恢复项目
3. 章节导出 - Markdown 格式
4. 配置导出 - YAML 格式
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "godcraft.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")


class ExportImportManager:
    """导入导出管理器"""
    
    def __init__(self, db_path: str = None, output_dir: str = None, config_dir: str = None):
        self.db_path = db_path or DB_PATH
        self.output_dir = output_dir or OUTPUT_DIR
        self.config_dir = config_dir or CONFIG_DIR
    
    # === 数据库操作 ===
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[dict]:
        """执行查询"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    def _execute_write(self, query: str, params: tuple = ()) -> int:
        """执行写操作"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id
    
    # === 项目导出 ===
    
    def export_project_json(self, project_id: str, include_chapters: bool = True) -> Dict[str, Any]:
        """导出项目为 JSON"""
        # 获取项目基本信息
        project = self._execute_query(
            "SELECT * FROM novel_projects WHERE project_id = ?",
            (project_id,)
        )[0] if self._execute_query(
            "SELECT * FROM novel_projects WHERE project_id = ?",
            (project_id,)
        ) else None
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取任务
        jobs = self._execute_query(
            "SELECT * FROM writing_jobs WHERE project_id = ?",
            (project_id,)
        )
        
        # 获取事件
        events = self._execute_query(
            "SELECT * FROM events_log WHERE project_id = ?",
            (project_id,)
        )
        
        # 获取角色关系
        relationships = self._execute_query(
            "SELECT * FROM character_relationships WHERE project_id = ?",
            (project_id,)
        )
        
        # 获取世界图谱
        world_edges = self._execute_query(
            "SELECT * FROM world_graph_edges WHERE project_id = ?",
            (project_id,)
        )
        
        # 获取伏笔
        foreshadowings = self._execute_query(
            "SELECT * FROM foreshadowing_ledger WHERE project_id = ?",
            (project_id,)
        )
        
        # 导出数据
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "project": project,
            "jobs": jobs,
            "events": events,
            "character_relationships": relationships,
            "world_edges": world_edges,
            "foreshadowings": foreshadowings
        }
        
        # 导出章节
        if include_chapters:
            chapters = []
            if os.path.exists(self.output_dir):
                for f in os.listdir(self.output_dir):
                    if f.startswith("chapter_") and f.endswith(".md"):
                        chapter_num = f.replace("chapter_", "").replace(".md", "")
                        chapter_path = os.path.join(self.output_dir, f)
                        
                        with open(chapter_path, 'r', encoding='utf-8') as fp:
                            content = fp.read()
                        
                        # 读取元数据
                        meta = None
                        meta_path = os.path.join(self.output_dir, f"chapter_{chapter_num}_meta.json")
                        if os.path.exists(meta_path):
                            with open(meta_path, 'r', encoding='utf-8') as fp:
                                meta = json.load(fp)
                        
                        chapters.append({
                            "chapter_number": chapter_num,
                            "content": content,
                            "meta": meta
                        })
            
            export_data["chapters"] = chapters
        
        return export_data
    
    def export_project_sql(self, project_id: str) -> str:
        """导出项目为 SQL 脚本"""
        # 获取项目数据
        project = self._execute_query(
            "SELECT * FROM novel_projects WHERE project_id = ?",
            (project_id,)
        )
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        project = project[0]
        
        # 生成 SQL
        sql_statements = []
        
        # 项目表
        sql_statements.append(f"-- 项目: {project['title']}")
        sql_statements.append(f"INSERT INTO novel_projects (project_id, title, genre, logline, target_chapters, interval_minutes, status, current_chapter, created_at, updated_at)")
        sql_statements.append(f"VALUES ('{project['project_id']}', '{project['title']}', '{project['genre']}', '{project['logline']}', {project['target_chapters']}, {project['interval_minutes']}, '{project['status']}', {project.get('current_chapter', 0)}, '{project.get('created_at', '')}', '{project.get('updated_at', '')}');")
        
        # 任务表
        jobs = self._execute_query(
            "SELECT * FROM writing_jobs WHERE project_id = ?",
            (project_id,)
        )
        
        for job in jobs:
            sql_statements.append(f"\n-- 写作任务: Chapter {job.get('chapter_number', 0)}")
            sql_statements.append(f"INSERT INTO writing_jobs (project_id, job_type, chapter_number, status, schedule_strategy, content, word_count, created_at, started_at, completed_at)")
            sql_statements.append(f"VALUES ('{job['project_id']}', '{job['job_type']}', {job.get('chapter_number', 0)}, '{job['status']}', '{job.get('schedule_strategy', '')}', '{job.get('content', '').replace(chr(39), chr(39)+chr(39))}', {job.get('word_count', 0)}, '{job.get('created_at', '')}', '{job.get('started_at', '')}', '{job.get('completed_at', '')}');")
        
        # 事件表
        events = self._execute_query(
            "SELECT * FROM events_log WHERE project_id = ?",
            (project_id,)
        )
        
        for event in events:
            sql_statements.append(f"\n-- 事件: {event.get('summary', '')}")
            sql_statements.append(f"INSERT INTO events_log (project_id, chapter_number, event_type, summary, data, created_at)")
            data_str = event.get('data', '').replace(chr(39), chr(39)+chr(39)) if event.get('data') else ''
            sql_statements.append(f"VALUES ('{event['project_id']}', {event.get('chapter_number', 0)}, '{event['event_type']}', '{event.get('summary', '').replace(chr(39), chr(39)+chr(39))}', '{data_str}', '{event.get('created_at', '')}');")
        
        return "\n".join(sql_statements)
    
    # === 项目导入 ===
    
    def import_project_json(self, json_data: Dict[str, Any]) -> str:
        """从 JSON 导入项目"""
        if "project" not in json_data:
            raise ValueError("无效的导入数据：缺少 project 字段")
        
        project = json_data["project"]
        project_id = project["project_id"]
        
        # 检查是否已存在
        existing = self._execute_query(
            "SELECT project_id FROM novel_projects WHERE project_id = ?",
            (project_id,)
        )
        
        if existing:
            raise ValueError(f"项目 {project_id} 已存在")
        
        # 导入项目
        self._execute_write(
            """INSERT INTO novel_projects 
               (project_id, title, genre, logline, target_chapters, interval_minutes, status, current_chapter, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project["project_id"],
                project["title"],
                project["genre"],
                project.get("logline", ""),
                project.get("target_chapters", 50),
                project.get("interval_minutes", 60),
                project.get("status", "pending"),
                project.get("current_chapter", 0),
                project.get("created_at", datetime.now().isoformat()),
                project.get("updated_at", datetime.now().isoformat())
            )
        )
        
        # 导入任务
        if "jobs" in json_data:
            for job in json_data["jobs"]:
                self._execute_write(
                    """INSERT INTO writing_jobs 
                       (project_id, job_type, chapter_number, status, schedule_strategy, content, word_count, created_at, started_at, completed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        job["project_id"],
                        job.get("job_type", "chapter_write"),
                        job.get("chapter_number", 0),
                        job.get("status", "pending"),
                        job.get("schedule_strategy", "immediate"),
                        job.get("content", ""),
                        job.get("word_count", 0),
                        job.get("created_at", ""),
                        job.get("started_at", ""),
                        job.get("completed_at", "")
                    )
                )
        
        # 导入事件
        if "events" in json_data:
            for event in json_data["events"]:
                self._execute_write(
                    """INSERT INTO events_log 
                       (project_id, chapter_number, event_type, summary, data, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        event["project_id"],
                        event.get("chapter_number", 0),
                        event.get("event_type", ""),
                        event.get("summary", ""),
                        event.get("data"),
                        event.get("created_at", "")
                    )
                )
        
        # 导入章节
        if "chapters" in json_data:
            os.makedirs(self.output_dir, exist_ok=True)
            
            for chapter in json_data["chapters"]:
                chapter_num = chapter.get("chapter_number", "0")
                
                # 保存内容
                chapter_path = os.path.join(self.output_dir, f"chapter_{chapter_num}.md")
                with open(chapter_path, 'w', encoding='utf-8') as f:
                    f.write(chapter.get("content", ""))
                
                # 保存元数据
                if chapter.get("meta"):
                    meta_path = os.path.join(self.output_dir, f"chapter_{chapter_num}_meta.json")
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(chapter["meta"], f, ensure_ascii=False, indent=2)
        
        return project_id
    
    # === 章节导出 ===
    
    def export_chapter_markdown(self, chapter_number: str, project_id: str = "default") -> str:
        """导出章节为 Markdown"""
        chapter_path = os.path.join(self.output_dir, f"chapter_{chapter_number}.md")
        
        if not os.path.exists(chapter_path):
            raise ValueError(f"章节 {chapter_number} 不存在")
        
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    def export_chapters_zip(self, project_id: str = None, output_path: str = None) -> str:
        """导出所有章节为 ZIP"""
        import zipfile
        
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"chapters_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
            )
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.exists(self.output_dir):
                for f in os.listdir(self.output_dir):
                    if f.startswith("chapter_") and (f.endswith(".md") or f.endswith(".json")):
                        file_path = os.path.join(self.output_dir, f)
                        zipf.write(file_path, f)
        
        return output_path
    
    # === 配置导出 ===
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置文件"""
        config = {}
        
        # 世界设置
        world_setting_path = os.path.join(self.config_dir, "world_setting.yaml")
        if os.path.exists(world_setting_path):
            import yaml
            with open(world_setting_path, 'r', encoding='utf-8') as f:
                config["world_setting"] = yaml.safe_load(f)
        
        return config
    
    def import_config(self, config_data: Dict[str, Any]) -> None:
        """导入配置文件"""
        # 世界设置
        if "world_setting" in config_data:
            import yaml
            world_setting_path = os.path.join(self.config_dir, "world_setting.yaml")
            with open(world_setting_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data["world_setting"], f, allow_unicode=True, default_flow_style=False)


# === 监控模块 ===

class Monitor:
    """系统监控"""
    
    def __init__(self, db_path: str = None, output_dir: str = None):
        self.db_path = db_path or DB_PATH
        self.output_dir = output_dir or OUTPUT_DIR
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_project_health(self, project_id: str) -> Dict[str, Any]:
        """获取项目健康状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 项目信息
        cursor.execute("SELECT * FROM novel_projects WHERE project_id = ?", (project_id,))
        project = cursor.fetchone()
        
        if not project:
            conn.close()
            return {"status": "error", "message": "项目不存在"}
        
        project = dict(project)  # 转换为字典
        
        # 任务统计
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM writing_jobs WHERE project_id = ? GROUP BY status",
            (project_id,)
        )
        job_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 章节数量
        chapter_count = 0
        if os.path.exists(self.output_dir):
            chapter_count = len([
                f for f in os.listdir(self.output_dir) 
                if f.startswith("chapter_") and f.endswith(".md")
            ])
        
        # 计算进度
        target = project.get("target_chapters", 0)
        current = project.get("current_chapter", 0)
        progress = (current / target * 100) if target > 0 else 0
        
        # 健康评估
        health = "healthy"
        issues = []
        
        if progress < 10 and target > 10:
            issues.append("进度较慢")
        
        if job_stats.get("failed", 0) > job_stats.get("completed", 1):
            health = "warning"
            issues.append("失败任务较多")
        
        if target > 0 and current >= target:
            health = "completed"
        
        conn.close()
        
        return {
            "status": health,
            "project_id": project_id,
            "title": project.get("title", ""),
            "progress": {
                "current": current,
                "target": target,
                "percentage": round(progress, 2)
            },
            "chapters_generated": chapter_count,
            "jobs": job_stats,
            "issues": issues
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 项目统计
        cursor.execute("SELECT COUNT(*), status FROM novel_projects GROUP BY status")
        project_stats = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 任务统计
        cursor.execute("SELECT status, COUNT(*) FROM writing_jobs GROUP BY status")
        job_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 章节数量
        chapter_count = 0
        if os.path.exists(self.output_dir):
            chapter_count = len([
                f for f in os.listdir(self.output_dir) 
                if f.startswith("chapter_") and f.endswith(".md")
            ])
        
        # 事件统计
        cursor.execute("SELECT COUNT(*) FROM events_log")
        event_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "projects": {
                "total": sum(project_stats.values()),
                "by_status": project_stats
            },
            "jobs": {
                "total": sum(job_stats.values()),
                "by_status": job_stats
            },
            "chapters": chapter_count,
            "events": event_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_job_progress(self, job_id: int) -> Dict[str, Any]:
        """获取任务进度"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM writing_jobs WHERE job_id = ?", (job_id,))
        job = cursor.fetchone()
        
        conn.close()
        
        if not job:
            return {"status": "error", "message": "任务不存在"}
        
        job = dict(job)  # 转换为字典
        
        return {
            "job_id": job["job_id"],
            "project_id": job["project_id"],
            "chapter_number": job.get("chapter_number", 0),
            "status": job["status"],
            "schedule_strategy": job.get("schedule_strategy", ""),
            "word_count": job.get("word_count", 0),
            "created_at": job.get("created_at", ""),
            "started_at": job.get("started_at", ""),
            "completed_at": job.get("completed_at", "")
        }
    
    def get_recent_activities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近活动"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            f"SELECT * FROM events_log ORDER BY created_at DESC LIMIT {limit}"
        )
        events = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in events]


# === 便捷函数 ===

def create_export_manager(db_path: str = None, output_dir: str = None, config_dir: str = None) -> ExportImportManager:
    """创建导入导出管理器"""
    return ExportImportManager(db_path, output_dir, config_dir)


def create_monitor(db_path: str = None, output_dir: str = None) -> Monitor:
    """创建监控器"""
    return Monitor(db_path, output_dir)


def export_project(project_id: str, format: str = "json", include_chapters: bool = True, db_path: str = None) -> str:
    """导出项目便捷函数"""
    manager = ExportImportManager(db_path)
    
    if format == "json":
        data = manager.export_project_json(project_id, include_chapters)
        return json.dumps(data, ensure_ascii=False, indent=2)
    elif format == "sql":
        return manager.export_project_sql(project_id)
    else:
        raise ValueError(f"不支持的格式: {format}")


def import_project(json_data: str, db_path: str = None) -> str:
    """导入项目便捷函数"""
    manager = ExportImportManager(db_path)
    data = json.loads(json_data)
    return manager.import_project_json(data)
