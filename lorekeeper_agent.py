# lorekeeper_agent.py - M2-3 LoreKeeper 读写 & YAML 原始同步
"""
LoreKeeper 负责把经校验的 structured_update 写入 DB（事务化）
并在成功后同步 YAML（原子替换）

核心职责：
1. 事务化写入 DB (events_log, character_relationships, world_graph_edges, foreshadowing_ledger)
2. 原子同步 YAML 文件
3. 审计日志记录
"""

import json
import os
from datetime import datetime
from typing import Any, Optional
from database import (
    get_connection, execute_write, execute_query, 
    log_event as db_log_event,
    add_character_relationship as db_add_relationship,
    add_world_edge as db_add_edge,
    add_foreshadowing as db_add_foreshadowing,
    resolve_foreshadowing, write_audit_log
)
from utils.yaml_utils import atomic_write_yaml, load_yaml


# YAML 角色文件目录
CHARACTERS_DIR = "data/characters"
WORLD_STATE_FILE = "data/world_state.yaml"


class LoreKeeper:
    """
    LoreKeeper - 世界观守护者
    负责结构化数据的持久化：DB 事务 + YAML 同步
    """
    
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def apply_structured_update(self, structured_update: dict, user_input: str = "") -> dict:
        """
        应用结构化更新
        1. 验证 structured_update
        2. 写入 DB 事务
        3. 同步 YAML
        
        Args:
            structured_update: 经 schema_validator 验证的结构化更新
            user_input: 原始用户输入（用于审计）
            
        Returns: {
            "status": "committed" | "failed",
            "db_write": {...},
            "yaml_sync": [...],
            "errors": []
        }
        """
        errors = []
        db_result = {}
        yaml_synced = []
        
        update_type = structured_update.get("update_type")
        entity_id = structured_update.get("entity_id")
        
        # 1. DB 事务写入
        try:
            db_result = self._write_to_db(structured_update)
        except Exception as e:
            errors.append(f"DB 写入失败: {str(e)}")
            return {
                "status": "failed",
                "db_write": {},
                "yaml_sync": [],
                "errors": errors
            }
        
        # 2. YAML 原子同步（仅当 DB 成功后执行）
        try:
            yaml_files = self._sync_to_yaml(structured_update)
            yaml_synced = yaml_files
        except Exception as e:
            # YAML 同步失败不影响 DB 状态，记录警告
            errors.append(f"YAML 同步警告: {str(e)}")
        
        # 3. 审计日志 (将复杂对象转为 JSON 字符串)
        status = "committed" if db_result else "failed"
        audit_result = json.dumps({
            "db_write": db_result,
            "yaml_synced": yaml_synced,
            "status": status
        }, ensure_ascii=False)
        
        write_audit_log(
            user_input or "system",
            "apply_structured_update",
            json.dumps(structured_update, ensure_ascii=False),
            audit_result
        )
        
        return {
            "status": "committed",
            "db_write": db_result,
            "yaml_sync": yaml_synced,
            "errors": errors
        }
    
    def _write_to_db(self, update: dict) -> dict:
        """根据 update_type 执行不同的 DB 写入"""
        update_type = update.get("update_type")
        entity_id = update.get("entity_id")
        field_path = update.get("field_path")
        new_value = update.get("new_value")
        reason = update.get("reason", "")
        
        result = {"events": [], "relationships": [], "edges": [], "foreshadowings": []}
        
        if update_type == "character_state":
            # 写入事件日志 (使用 chapter_number=0 作为默认值)
            event_data = {
                "entity_type": "character",
                "entity_id": entity_id,
                "field": field_path,
                "old_value": update.get("old_value"),
                "new_value": new_value,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            event_id = db_log_event(
                self.project_id,
                0,  # chapter_number
                f"character_state_update:{entity_id}:{field_path}",
                f"character_state_update:{entity_id}:{field_path}",
                event_data
            )
            result["events"].append({"event_id": event_id, "entity_id": entity_id})
            
        elif update_type == "relationship":
            # 写入角色关系 (使用 project_id 作为第一个参数)
            rel_data = new_value if isinstance(new_value, dict) else {}
            source = rel_data.get("source", entity_id)
            target = rel_data.get("target")
            rel_type = rel_data.get("type", "unknown")
            weight = rel_data.get("weight", 0)
            
            rel_id = db_add_relationship(
                self.project_id,
                source,
                target,
                rel_type,
                weight,
                reason
            )
            result["relationships"].append({"rel_id": rel_id, "source": source, "target": target})
            
        elif update_type == "world_state":
            # 写入世界图边
            edge_data = new_value if isinstance(new_value, dict) else {}
            source_node = edge_data.get("source", entity_id)
            target_node = edge_data.get("target")
            edge_type = edge_data.get("type", "unknown")
            
            edge_id = db_add_edge(
                self.project_id,
                source_node,
                target_node,
                edge_type,
                edge_data.get("weight", 1.0),
                reason
            )
            result["edges"].append({"edge_id": edge_id, "source": source_node, "target": target_node})
            
        elif update_type == "foreshadowing":
            # 写入伏笔账本
            foreshadow_data = new_value if isinstance(new_value, dict) else {}
            # database.py 的签名: (project_id, chapter_introduced, chapter_revealed, description)
            foreshadow_id = db_add_foreshadowing(
                self.project_id,
                foreshadow_data.get("chapter_introduced", 1),  # chapter_introduced
                foreshadow_data.get("target_chapter", 1),  # chapter_revealed
                foreshadow_data.get("event_description", entity_id)  # description
            )
            result["foreshadowings"].append({"foreshadow_id": foreshadow_id})
            
        elif update_type == "plot_point":
            # 写入事件日志（剧情点）
            event_data = {
                "plot_point": entity_id,
                "description": new_value,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            event_id = db_log_event(
                self.project_id,
                0,  # chapter_number
                f"plot_point:{entity_id}",
                f"plot_point:{entity_id}",
                event_data
            )
            result["events"].append({"event_id": event_id, "plot_point": entity_id})
        
        return result
    
    def _sync_to_yaml(self, update: dict) -> list:
        """将更新同步到 YAML 文件"""
        update_type = update.get("update_type")
        entity_id = update.get("entity_id")
        new_value = update.get("new_value")
        
        synced_files = []
        
        if update_type == "character_state":
            # 同步到角色 YAML 文件
            char_file = os.path.join(CHARACTERS_DIR, f"{entity_id}.yaml")
            
            # 加载现有数据
            existing_data = {}
            if os.path.exists(char_file):
                existing_data = load_yaml(char_file) or {}
            
            # 更新 dynamic_state
            field_path = update.get("field_path", "")
            if field_path:
                # 支持嵌套字段更新，如 "dynamic_state.mood"
                parts = field_path.split(".")
                current = existing_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = new_value
            else:
                # 整体更新
                if "dynamic_state" not in existing_data:
                    existing_data["dynamic_state"] = {}
                existing_data["dynamic_state"].update(new_value if isinstance(new_value, dict) else {"value": new_value})
            
            # 原子写入
            atomic_write_yaml(char_file, existing_data)
            synced_files.append(char_file)
            
        elif update_type == "relationship":
            # 同步到角色关系文件
            rel_file = os.path.join(CHARACTERS_DIR, "relationships.yaml")
            existing_rels = {}
            if os.path.exists(rel_file):
                existing_rels = load_yaml(rel_file) or {"relationships": []}
            
            if "relationships" not in existing_rels:
                existing_rels["relationships"] = []
            
            rel_data = new_value if isinstance(new_value, dict) else {}
            existing_rels["relationships"].append({
                "source": entity_id,
                "target": rel_data.get("target"),
                "type": rel_data.get("type"),
                "weight": rel_data.get("weight", 0),
                "reason": update.get("reason", "")
            })
            
            atomic_write_yaml(rel_file, existing_rels)
            synced_files.append(rel_file)
            
        elif update_type == "world_state":
            # 同步到世界状态文件
            existing_world = {}
            if os.path.exists(WORLD_STATE_FILE):
                existing_world = load_yaml(WORLD_STATE_FILE) or {}
            
            if "edges" not in existing_world:
                existing_world["edges"] = []
            
            edge_data = new_value if isinstance(new_value, dict) else {}
            existing_world["edges"].append({
                "source": entity_id,
                "target": edge_data.get("target"),
                "type": edge_data.get("type"),
                "properties": edge_data.get("properties", {}),
                "reason": update.get("reason", "")
            })
            
            atomic_write_yaml(WORLD_STATE_FILE, existing_world)
            synced_files.append(WORLD_STATE_FILE)
            
        elif update_type == "foreshadowing":
            # 同步到伏笔文件
            foreshadow_file = "data/foreshadowing.yaml"
            existing = {}
            if os.path.exists(foreshadow_file):
                existing = load_yaml(foreshadow_file) or {}
            
            if "foreshadowings" not in existing:
                existing["foreshadowings"] = []
            
            foreshadow_data = new_value if isinstance(new_value, dict) else {}
            existing["foreshadowings"].append({
                "description": entity_id,
                "target_chapter": foreshadow_data.get("target_chapter"),
                "trigger_condition": foreshadow_data.get("trigger_condition", ""),
                "status": "active"
            })
            
            atomic_write_yaml(foreshadow_file, existing)
            synced_files.append(foreshadow_file)
        
        return synced_files
    
    def read_character(self, char_id: str) -> dict:
        """读取角色数据（从 YAML）"""
        char_file = os.path.join(CHARACTERS_DIR, f"{char_id}.yaml")
        if os.path.exists(char_file):
            return load_yaml(char_file) or {}
        return {}
    
    def read_world_state(self) -> dict:
        """读取世界状态（从 YAML）"""
        if os.path.exists(WORLD_STATE_FILE):
            return load_yaml(WORLD_STATE_FILE) or {}
        return {}
    
    def read_all_relationships(self) -> list:
        """读取所有角色关系"""
        rel_file = os.path.join(CHARACTERS_DIR, "relationships.yaml")
        if os.path.exists(rel_file):
            data = load_yaml(rel_file) or {}
            return data.get("relationships", [])
        return []


def apply_structured_update(project_id: str, structured_update: dict, user_input: str = "") -> dict:
    """
    便捷函数：应用结构化更新
    """
    keeper = LoreKeeper(project_id)
    return keeper.apply_structured_update(structured_update, user_input)


def read_lore(project_id: str, lore_type: str, entity_id: str = None) -> dict:
    """
    便捷函数：读取世界观数据
    
    Args:
        project_id: 项目 ID
        lore_type: lore 类型 (character, world, relationships, foreshadowing)
        entity_id: 实体 ID（可选）
        
    Returns:
        读取的数据
    """
    keeper = LoreKeeper(project_id)
    
    if lore_type == "character":
        if entity_id:
            return keeper.read_character(entity_id)
        # 返回所有角色
        chars = {}
        for f in os.listdir(CHARACTERS_DIR):
            if f.endswith(".yaml") and f != "relationships.yaml":
                char_id = f[:-5]  # 去掉 .yaml
                chars[char_id] = keeper.read_character(char_id)
        return chars
    elif lore_type == "world":
        return keeper.read_world_state()
    elif lore_type == "relationships":
        return keeper.read_all_relationships()
    
    return {}


# 导出
__all__ = [
    'LoreKeeper',
    'apply_structured_update',
    'read_lore'
]
