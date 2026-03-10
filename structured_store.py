# structured_store.py - M2-2 结构化存取与 JSON Schema 验证
"""
结构化数据存取层
结合 database.py 的数据库操作与 schema_validator.py 的验证
"""

import json
from typing import Any, Optional
from database import (
    get_project, create_project, update_project_status, increment_chapter,
    create_job, get_job, update_job_status,
    log_event, get_project_events,
    add_character_relationship, get_character_relationships,
    add_world_edge, get_world_edges,
    add_foreshadowing, get_active_foreshadowings, resolve_foreshadowing,
    write_audit_log, get_audit_logs, execute_write, execute_query
)
from utils.schema_validator import (
    validate_data, check_trust_delta, validate_structured_update,
    SCHEMAS
)


class StructuredStore:
    """
    结构化存储管理器
    提供带 Schema 验证的数据存取接口
    """
    
    def __init__(self):
        self.schema_validator_enabled = True
    
    # === Project 操作 ===
    
    def create_project(self, project_id: str, title: str, genre: str, 
                       logline: str = "", target_chapters: int = 0, 
                       interval_minutes: int = 60) -> tuple[bool, str, int]:
        """
        创建项目（带 Schema 验证）
        返回: (success, message, project_id_or_error_code)
        """
        data = {
            "project_id": project_id,
            "title": title,
            "genre": genre,
            "logline": logline,
            "target_chapters": target_chapters,
            "interval_minutes": interval_minutes
        }
        
        # Schema 验证
        if self.schema_validator_enabled:
            is_valid, errors = validate_data("project", data)
            if not is_valid:
                return False, f"Schema validation failed: {errors}", -1
        
        # 检查项目是否已存在
        existing = get_project(project_id)
        if existing:
            return False, f"Project {project_id} already exists", -1
        
        # 创建项目
        try:
            row_id = create_project(project_id, title, genre, logline, 
                                   target_chapters, interval_minutes)
            return True, "Project created successfully", row_id
        except Exception as e:
            return False, f"Database error: {str(e)}", -1
    
    def get_project(self, project_id: str) -> Optional[dict]:
        """获取项目信息"""
        return get_project(project_id)
    
    def update_project(self, project_id: str, **kwargs) -> tuple[bool, str]:
        """
        更新项目（支持结构化更新与 trust_delta）
        
        用法示例:
        - update_project("proj_001", status="running")
        - update_project("proj_001", current_chapter=5, _trust_delta=True)
        """
        # 解析参数
        trust_delta = kwargs.pop('_trust_delta', False)
        
        # 如果启用了 trust_delta，构建结构化更新
        if trust_delta and 'current_chapter' in kwargs:
            old_project = get_project(project_id)
            if not old_project:
                return False, f"Project {project_id} not found"
            
            old_value = old_project.get('current_chapter', 0)
            new_value = kwargs['current_chapter']
            
            # 检查 trust_delta
            delta_check = check_trust_delta(old_value, new_value)
            
            # 如果需要审核
            if delta_check['needs_review']:
                # 记录到审计日志
                write_audit_log(
                    user_input=f"update_project({project_id})",
                    parsed_intent="structured_update",
                    params={"field": "current_chapter", "old": old_value, "new": new_value, "trust_delta": True},
                    result=f"pending_review: {delta_check['reason']}"
                )
                return False, f"Update requires review: {delta_check['reason']}"
        
        # 直接更新（简单字段）
        allowed_fields = ['title', 'logline', 'target_chapters', 'interval_minutes', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False, "No valid fields to update"
        
        # 构建 SQL
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE novel_projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE project_id = ?"
        
        try:
            execute_write(query, tuple(updates.values()) + (project_id,))
            
            # 记录审计日志
            write_audit_log(
                user_input=f"update_project({project_id})",
                parsed_intent="update_project",
                params=updates,
                result="success"
            )
            
            return True, "Project updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === Job 操作 ===
    
    def create_job(self, project_id: str, chapter_number: int) -> tuple[bool, str, int]:
        """创建写作任务（带验证）"""
        data = {
            "project_id": project_id,
            "chapter_number": chapter_number
        }
        
        if self.schema_validator_enabled:
            is_valid, errors = validate_data("job", data)
            if not is_valid:
                return False, f"Schema validation failed: {errors}", -1
        
        # 验证项目存在
        project = get_project(project_id)
        if not project:
            return False, f"Project {project_id} not found", -1
        
        try:
            row_id = create_job(project_id, chapter_number)
            return True, "Job created successfully", row_id
        except Exception as e:
            return False, f"Database error: {str(e)}", -1
    
    def get_job(self, job_id: int) -> Optional[dict]:
        """获取任务信息"""
        return get_job(job_id)
    
    def update_job(self, job_id: int, status: str = None, 
                   content: str = None, word_count: int = None) -> tuple[bool, str]:
        """更新任务"""
        updates = {}
        if status:
            updates['status'] = status
        if content is not None:
            updates['content'] = content
        if word_count is not None:
            updates['word_count'] = word_count
        
        if not updates:
            return False, "No fields to update"
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE writing_jobs SET {set_clause} WHERE job_id = ?"
        
        try:
            execute_write(query, tuple(updates.values()) + (job_id,))
            return True, "Job updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === 结构化更新（核心功能）===
    
    def structured_update(self, update_type: str, entity_id: str, 
                          field_path: str, new_value: Any,
                          old_value: Any = None, reason: str = "") -> tuple[bool, str, dict]:
        """
        执行结构化更新（核心方法）
        
        参数:
        - update_type: character_state | world_state | relationship | foreshadowing | plot_point
        - entity_id: 实体 ID
        - field_path: 字段路径（如 "dynamic_state.mood"）
        - new_value: 新值
        - old_value: 旧值（用于 trust_delta 计算）
        - reason: 更新原因
        
        返回: (success, message, review_status)
        """
        # 构建更新数据
        update_data = {
            "update_type": update_type,
            "entity_id": entity_id,
            "field_path": field_path,
            "new_value": new_value,
            "reason": reason
        }
        
        if old_value is not None:
            update_data["old_value"] = old_value
            # 计算 delta
            delta_check = check_trust_delta(old_value, new_value)
            update_data["delta"] = delta_check["delta"]
            update_data["trust_delta"] = True
        
        # 验证结构化更新
        is_valid, errors, review_status = validate_structured_update(update_data)
        if not is_valid:
            return False, f"Validation failed: {errors}", {}
        
        # 根据类型执行更新
        try:
            if update_type == "character_state":
                return self._update_character_state(entity_id, field_path, new_value, reason, review_status)
            elif update_type == "world_state":
                return self._update_world_state(entity_id, field_path, new_value, reason, review_status)
            elif update_type == "relationship":
                return self._update_relationship(entity_id, field_path, new_value, reason, review_status)
            elif update_type == "foreshadowing":
                return self._update_foreshadowing(entity_id, field_path, new_value, reason, review_status)
            else:
                return False, f"Unknown update_type: {update_type}", {}
        except Exception as e:
            return False, f"Update failed: {str(e)}", {}
    
    def _update_character_state(self, char_id: str, field_path: str, 
                                new_value: Any, reason: str, review_status: dict) -> tuple[bool, str, dict]:
        """更新角色状态"""
        # 解析 field_path（支持嵌套如 "dynamic_state.mood"）
        parts = field_path.split('.')
        
        if len(parts) == 1:
            # 直接字段更新
            query = f"UPDATE character_relationships SET {parts[0]} = ? WHERE char_id_1 = ? OR char_id_2 = ?"
            execute_write(query, (new_value, char_id, char_id))
        
        # 记录审计日志
        write_audit_log(
            user_input=f"structured_update(character_state, {char_id})",
            parsed_intent="structured_update",
            params={"field_path": field_path, "new_value": new_value, "reason": reason},
            result=f"success: {review_status}"
        )
        
        return True, "Character state updated", review_status
    
    def _update_world_state(self, node_id: str, field_path: str,
                            new_value: Any, reason: str, review_status: dict) -> tuple[bool, str, dict]:
        """更新世界状态"""
        query = f"UPDATE world_graph_edges SET {field_path} = ? WHERE source_node = ? OR target_node = ?"
        execute_write(query, (new_value, node_id, node_id))
        
        write_audit_log(
            user_input=f"structured_update(world_state, {node_id})",
            parsed_intent="structured_update",
            params={"field_path": field_path, "new_value": new_value, "reason": reason},
            result="success"
        )
        
        return True, "World state updated", review_status
    
    def _update_relationship(self, char_id: str, field_path: str,
                            new_value: Any, reason: str, review_status: dict) -> tuple[bool, str, dict]:
        """更新角色关系"""
        # field_path 格式: "char_id_2:relationship_type" 或 "strength"
        query = f"UPDATE character_relationships SET {field_path} = ? WHERE char_id_1 = ? OR char_id_2 = ?"
        execute_write(query, (new_value, char_id, char_id))
        
        return True, "Relationship updated", review_status
    
    def _update_foreshadowing(self, fs_id: str, field_path: str,
                             new_value: Any, reason: str, review_status: dict) -> tuple[bool, str, dict]:
        """更新伏笔"""
        query = f"UPDATE foreshadowing_ledger SET {field_path} = ? WHERE id = ?"
        execute_write(query, (new_value, fs_id))
        
        return True, "Foreshadowing updated", review_status
    
    # === 审计日志 ===
    
    def log_audit(self, user_input: str, parsed_intent: str, 
                  params: dict, result: str) -> int:
        """记录审计日志"""
        return write_audit_log(user_input, parsed_intent, params, result)
    
    def get_audit_logs(self, limit: int = 100) -> list:
        """获取审计日志"""
        return get_audit_logs(limit)


# 全局实例
store = StructuredStore()


# 导出
__all__ = ['StructuredStore', 'store']
