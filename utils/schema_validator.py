# schema_validator.py - M2-2 结构化存取与 JSON Schema 验证
"""
结构化数据验证模块
使用 JSON Schema 进行数据验证，支持 trust_delta 机制
"""

import json
import re
from typing import Any, Optional
from jsonschema import validate, ValidationError, Draft7Validator

# 基础结构 Schema
PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]{1,64}$"},
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "genre": {"type": "string", "enum": ["fantasy", "scifi", "romance", "mystery", "horror", "other"]},
        "logline": {"type": "string", "maxLength": 500},
        "target_chapters": {"type": "integer", "minimum": 1, "maximum": 10000},
        "interval_minutes": {"type": "integer", "minimum": 1},
        "status": {"type": "string", "enum": ["pending", "running", "completed", "paused"]}
    },
    "required": ["project_id", "title", "genre"]
}

JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_id": {"type": "integer"},
        "project_id": {"type": "string"},
        "chapter_number": {"type": "integer", "minimum": 1},
        "status": {"type": "string", "enum": ["pending", "running", "completed", "failed"]},
        "content": {"type": "string"},
        "word_count": {"type": "integer", "minimum": 0},
        "started_at": {"type": "string", "format": "date-time"},
        "completed_at": {"type": "string", "format": "date-time"}
    },
    "required": ["project_id", "chapter_number"]
}

CHARACTER_SCHEMA = {
    "type": "object",
    "properties": {
        "char_id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]{1,32}$"},
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "static_profile": {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "gender": {"type": "string"},
                "occupation": {"type": "string"},
                "background": {"type": "string"},
                "personality": {"type": "string"}
            }
        },
        "dynamic_state": {
            "type": "object",
            "properties": {
                "current_location": {"type": "string"},
                "mood": {"type": "string"},
                "health": {"type": "integer", "minimum": 0, "maximum": 100},
                "relationships": {"type": "object"}
            }
        }
    },
    "required": ["char_id", "name"]
}

# 结构化更新 Schema（用于 trust_delta 机制）
STRUCTURED_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "update_type": {
            "type": "string",
            "enum": ["character_state", "world_state", "relationship", "foreshadowing", "plot_point"]
        },
        "entity_id": {"type": "string"},
        "field_path": {"type": "string", "pattern": "^[a-zA-Z0-9_.-]+$"},
        "old_value": {},
        "new_value": {},
        "delta": {"type": "number"},
        "reason": {"type": "string", "maxLength": 500},
        "trust_delta": {"type": "boolean"},
        "pending_review": {"type": "boolean"}
    },
    "required": ["update_type", "entity_id", "field_path", "new_value"]
}

# 存储所有 Schema
SCHEMAS = {
    "project": PROJECT_SCHEMA,
    "job": JOB_SCHEMA,
    "character": CHARACTER_SCHEMA,
    "structured_update": STRUCTURED_UPDATE_SCHEMA
}

# 缓存已编译的 Validator
_validators = {}


def get_validator(schema_name: str) -> Optional[Draft7Validator]:
    """获取或创建 Validator 实例"""
    if schema_name not in _validators:
        schema = SCHEMAS.get(schema_name)
        if schema:
            _validators[schema_name] = Draft7Validator(schema)
        else:
            return None
    return _validators[schema_name]


def validate_data(schema_name: str, data: dict) -> tuple[bool, list]:
    """
    验证数据是否符合 Schema
    返回: (is_valid, error_messages)
    """
    validator = get_validator(schema_name)
    if not validator:
        return False, [f"Unknown schema: {schema_name}"]
    
    errors = list(validator.iter_errors(data))
    if errors:
        error_messages = [f"{e.json_path}: {e.message}" for e in errors]
        return False, error_messages
    return True, []


def validate_with_return(data: dict, schema_name: str) -> Optional[ValidationError]:
    """
    验证数据，返回第一个错误（如果有）
    """
    validator = get_validator(schema_name)
    if not validator:
        return ValidationError(f"Unknown schema: {schema_name}")
    
    errors = list(validator.iter_errors(data))
    return errors[0] if errors else None


def check_trust_delta(old_value: Any, new_value: Any) -> dict:
    """
    检查 trust_delta 机制
    当 delta > 3 且 |delta| > 5 时标记为需要审核
    
    返回: {
        "delta": float,
        "needs_review": bool,
        "reason": str
    }
    """
    result = {
        "delta": 0,
        "needs_review": False,
        "reason": ""
    }
    
    # 计算数值变化
    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
        delta = float(new_value) - float(old_value)
        result["delta"] = delta
        
        # 阈值检查
        if abs(delta) > 3 and abs(delta) > 5:
            result["needs_review"] = True
            result["reason"] = f"delta={delta} 超过阈值 (|delta|>3 且 |delta|>5)"
    
    return result


def validate_structured_update(update: dict) -> tuple[bool, list, dict]:
    """
    验证结构化更新
    1. 验证 JSON Schema
    2. 检查 trust_delta 机制
    
    返回: (is_valid, errors, review_status)
    """
    # 1. Schema 验证
    is_valid, errors = validate_data("structured_update", update)
    if not is_valid:
        return is_valid, errors, {}
    
    # 2. trust_delta 检查
    review_status = {}
    if "delta" in update and update.get("trust_delta", False):
        old_val = update.get("old_value", 0)
        new_val = update.get("new_value", 0)
        delta_check = check_trust_delta(old_val, new_val)
        review_status = {
            "needs_pending_review": delta_check["needs_review"],
            "delta": delta_check["delta"],
            "reason": delta_check["reason"]
        }
        
        # 自动设置 pending_review 标记
        if delta_check["needs_review"]:
            update["pending_review"] = True
    
    return True, [], review_status


def load_schema_from_file(schema_path: str) -> dict:
    """从文件加载 JSON Schema"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_schema_to_file(schema: dict, schema_path: str) -> None:
    """保存 JSON Schema 到文件"""
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


# 导出主要函数
__all__ = [
    'validate_data',
    'validate_with_return',
    'check_trust_delta',
    'validate_structured_update',
    'load_schema_from_file',
    'save_schema_to_file',
    'SCHEMAS'
]
