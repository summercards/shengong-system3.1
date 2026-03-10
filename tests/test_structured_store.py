# test_structured_store.py - M2-2 测试
"""
结构化存取与 JSON Schema 验证测试
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.schema_validator import (
    validate_data, check_trust_delta, validate_structured_update, SCHEMAS
)
from structured_store import StructuredStore, store
from database import create_project, get_project, create_job, get_job, execute_write


class TestSchemaValidator:
    """JSON Schema 验证测试"""
    
    def test_validate_project_valid(self):
        """测试有效项目数据"""
        data = {
            "project_id": "test_proj_001",
            "title": "Test Novel",
            "genre": "fantasy",
            "logline": "A test story",
            "target_chapters": 100,
            "interval_minutes": 60
        }
        is_valid, errors = validate_data("project", data)
        assert is_valid, f"Should be valid: {errors}"
    
    def test_validate_project_missing_required(self):
        """测试缺少必填字段"""
        data = {
            "project_id": "test_proj_002",
            "title": "Test Novel"
            # 缺少 genre
        }
        is_valid, errors = validate_data("project", data)
        assert not is_valid
    
    def test_validate_project_invalid_genre(self):
        """测试无效的 genre"""
        data = {
            "project_id": "test_proj_003",
            "title": "Test Novel",
            "genre": "invalid_genre"
        }
        is_valid, errors = validate_data("project", data)
        assert not is_valid
    
    def test_validate_job_valid(self):
        """测试有效任务数据"""
        data = {
            "project_id": "proj_001",
            "chapter_number": 1
        }
        is_valid, errors = validate_data("job", data)
        assert is_valid, f"Should be valid: {errors}"
    
    def test_validate_character_valid(self):
        """测试有效角色数据"""
        data = {
            "char_id": "char_001",
            "name": "Hero",
            "static_profile": {
                "age": 25,
                "gender": "male",
                "occupation": "warrior"
            },
            "dynamic_state": {
                "current_location": "castle",
                "mood": "happy",
                "health": 100
            }
        }
        is_valid, errors = validate_data("character", data)
        assert is_valid, f"Should be valid: {errors}"
    
    def test_validate_structured_update_valid(self):
        """测试有效结构化更新"""
        data = {
            "update_type": "character_state",
            "entity_id": "char_001",
            "field_path": "dynamic_state.mood",
            "new_value": "sad",
            "reason": "Character learned bad news"
        }
        is_valid, errors = validate_structured_update(data)
        assert is_valid, f"Should be valid: {errors}"
    
    def test_check_trust_delta_no_review_needed(self):
        """测试 trust_delta - 小变化不需要审核"""
        result = check_trust_delta(5, 6)
        assert result["delta"] == 1
        assert not result["needs_review"]
    
    def test_check_trust_delta_review_needed(self):
        """测试 trust_delta - 大变化需要审核"""
        # delta > 3 且 |delta| > 5
        result = check_trust_delta(0, 10)
        assert result["delta"] == 10
        assert result["needs_review"]
        assert "delta=10" in result["reason"]
    
    def test_check_trust_delta_negative_review_needed(self):
        """测试 trust_delta - 负向大变化"""
        result = check_trust_delta(100, 50)
        assert result["delta"] == -50
        assert result["needs_review"]
    
    def test_check_trust_delta_non_numeric(self):
        """测试非数值类型"""
        result = check_trust_delta("happy", "sad")
        assert result["delta"] == 0
        assert not result["needs_review"]


class TestStructuredStore:
    """结构化存储测试"""
    
    @pytest.fixture
    def clean_store(self):
        """清理测试数据"""
        # 创建测试项目
        try:
            create_project("test_struct_001", "Test Story", "fantasy", "Test logline", 50, 30)
        except:
            pass
        yield
        # 清理
        try:
            execute_write("DELETE FROM novel_projects WHERE project_id = ?", ("test_struct_001",))
        except:
            pass
    
    def test_create_project_with_validation(self, clean_store):
        """测试带验证创建项目"""
        success, msg, result = store.create_project(
            project_id="struct_test_001",
            title="Validation Test",
            genre="scifi",
            logline="Testing schema validation",
            target_chapters=30
        )
        assert success, msg
        
        # 验证项目已创建
        proj = get_project("struct_test_001")
        assert proj is not None
        assert proj["title"] == "Validation Test"
    
    def test_create_project_duplicate(self, clean_store):
        """测试重复创建项目"""
        # 先创建
        store.create_project("dup_test_001", "Duplicate Test", "romance")
        
        # 尝试重复创建
        success, msg, result = store.create_project("dup_test_001", "Duplicate Test 2", "romance")
        assert not success
        assert "already exists" in msg
    
    def test_create_job_with_validation(self, clean_store):
        """测试带验证创建任务"""
        success, msg, job_id = store.create_job("test_struct_001", 1)
        assert success, msg
        assert job_id > 0
    
    def test_create_job_invalid_project(self):
        """测试为不存在的项目创建任务"""
        success, msg, result = store.create_job("nonexistent_project", 1)
        assert not success
        assert "not found" in msg
    
    def test_update_job_status(self, clean_store):
        """测试更新任务状态"""
        # 先创建任务
        _, _, job_id = store.create_job("test_struct_001", 1)
        
        # 更新状态
        success, msg = store.update_job(job_id, status="running")
        assert success, msg
        
        # 验证
        job = get_job(job_id)
        assert job["status"] == "running"
    
    def test_structured_update_character_state(self, clean_store):
        """测试结构化更新角色状态"""
        # 先创建角色关系记录（简化测试）
        execute_write(
            """INSERT INTO character_relationships 
               (project_id, char_id_1, char_id_2, relationship_type, strength, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_struct_001", "char_test", "npc_001", "ally", 50, "Test")
        )
        
        # 执行结构化更新
        success, msg, review = store.structured_update(
            update_type="character_state",
            entity_id="char_test",
            field_path="strength",
            new_value=75,
            old_value=50,
            reason="Character grew stronger"
        )
        assert success, msg
    
    def test_structured_update_trust_delta_review(self, clean_store):
        """测试 trust_delta 需要审核"""
        # 这是一个测试场景，实际会触发审核
        result = check_trust_delta(0, 10)
        assert result["needs_review"]


class TestSchemaFiles:
    """Schema 文件测试"""
    
    def test_schemas_loaded(self):
        """测试所有 Schema 已加载"""
        assert "project" in SCHEMAS
        assert "job" in SCHEMAS
        assert "character" in SCHEMAS
        assert "structured_update" in SCHEMAS
    
    def test_project_schema_has_required_fields(self):
        """测试 project schema 包含必填字段"""
        schema = SCHEMAS["project"]
        assert "required" in schema
        assert "project_id" in schema["required"]
        assert "title" in schema["required"]
        assert "genre" in schema["required"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
