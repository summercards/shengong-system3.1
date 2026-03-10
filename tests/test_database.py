# tests/test_database.py - M2-1 数据库测试
import pytest
import os
import sys
import sqlite3
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

TEST_DB_PATH = "data/test_godcraft.db"

@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 使用测试数据库
    original_db = database.DB_PATH
    database.DB_PATH = TEST_DB_PATH
    
    # 重新初始化测试数据库
    conn = sqlite3.connect(TEST_DB_PATH)
    c = conn.cursor()
    
    # 删除旧表
    c.execute("DROP TABLE IF EXISTS novel_projects")
    c.execute("DROP TABLE IF EXISTS writing_jobs")
    c.execute("DROP TABLE IF EXISTS events_log")
    c.execute("DROP TABLE IF EXISTS character_relationships")
    c.execute("DROP TABLE IF EXISTS world_graph_edges")
    c.execute("DROP TABLE IF EXISTS foreshadowing_ledger")
    c.execute("DROP TABLE IF EXISTS audit_log")
    conn.commit()
    conn.close()
    
    # 导入原始 schema
    exec(open("init_project.py", encoding="utf8").read().split("DEFAULT_SCHEMA")[1].split('"""')[1])
    
    yield TEST_DB_PATH
    
    # 恢复
    database.DB_PATH = original_db
    # 不删除测试文件以便调试

class TestNovelProjects:
    """测试 novel_projects 表操作"""
    
    def test_create_project(self, test_db):
        """测试创建项目"""
        result = database.create_project(
            project_id="test_project_001",
            title="测试小说",
            genre="奇幻",
            logline="这是一个测试",
            target_chapters=20,
            interval_minutes=60
        )
        assert result > 0
        
        # 验证
        project = database.get_project("test_project_001")
        assert project is not None
        assert project['title'] == "测试小说"
        assert project['genre'] == "奇幻"
        assert project['status'] == "pending"
    
    def test_update_project_status(self, test_db):
        """测试更新项目状态"""
        database.create_project("test_002", "测试2", "科幻")
        result = database.update_project_status("test_002", "active")
        assert result > 0
        
        project = database.get_project("test_002")
        assert project['status'] == "active"
    
    def test_increment_chapter(self, test_db):
        """测试章节递增"""
        database.create_project("test_003", "测试3", "奇幻")
        database.increment_chapter("test_003")
        database.increment_chapter("test_003")
        
        project = database.get_project("test_003")
        assert project['current_chapter'] == 2


class TestWritingJobs:
    """测试 writing_jobs 表操作"""
    
    def test_create_job(self, test_db):
        """测试创建写作任务"""
        database.create_project("test_job_001", "测试项目", "奇幻")
        job_id = database.create_job("test_job_001", 1)
        assert job_id > 0
        
        job = database.get_job(job_id)
        assert job['chapter_number'] == 1
        assert job['status'] == "pending"
    
    def test_update_job_status(self, test_db):
        """测试更新任务状态"""
        database.create_project("test_job_002", "测试项目2", "奇幻")
        job_id = database.create_job("test_job_002", 1)
        
        database.update_job_status(job_id, "running")
        job = database.get_job(job_id)
        assert job['status'] == "running"
        assert job['started_at'] is not None
        
        database.update_job_status(job_id, "completed")
        job = database.get_job(job_id)
        assert job['status'] == "completed"
        assert job['completed_at'] is not None


class TestEventsLog:
    """测试 events_log 表操作"""
    
    def test_log_event(self, test_db):
        """测试记录事件"""
        database.create_project("test_event_001", "测试项目", "奇幻")
        event_id = database.log_event(
            "test_event_001", 1, "chapter_start", "第1章开始", 
            {"word_count": 0}
        )
        assert event_id > 0
        
        events = database.get_project_events("test_event_001")
        assert len(events) >= 1
        assert events[0]['event_type'] == "chapter_start"


class TestCharacterRelationships:
    """测试角色关系操作"""
    
    def test_add_relationship(self, test_db):
        """测试添加角色关系"""
        database.create_project("test_char_001", "测试项目", "奇幻")
        rel_id = database.add_character_relationship(
            "test_char_001", "char_1", "char_2", "friend", 80, "好朋友"
        )
        assert rel_id > 0
        
        rels = database.get_character_relationships("test_char_001")
        assert len(rels) == 1
        assert rels[0]['relationship_type'] == "friend"


class TestWorldGraph:
    """测试世界图谱操作"""
    
    def test_add_edge(self, test_db):
        """测试添加世界图谱边"""
        database.create_project("test_world_001", "测试项目", "奇幻")
        edge_id = database.add_world_edge(
            "test_world_001", "village_a", "forest_b", "connects", 0.8
        )
        assert edge_id > 0
        
        edges = database.get_world_edges("test_world_001")
        assert len(edges) == 1
        assert edges[0]['source_node'] == "village_a"


class TestForeshadowing:
    """测试伏笔管理"""
    
    def test_add_foreshadowing(self, test_db):
        """测试添加伏笔"""
        database.create_project("test_foreshadow_001", "测试项目", "奇幻")
        fs_id = database.add_foreshadowing(
            "test_foreshadow_001", 1, 10, "神秘宝物的秘密"
        )
        assert fs_id > 0
        
        fses = database.get_active_foreshadowings("test_foreshadow_001")
        assert len(fses) == 1
        assert fses[0]['description'] == "神秘宝物的秘密"
    
    def test_resolve_foreshadowing(self, test_db):
        """测试解决伏笔"""
        database.create_project("test_foreshadow_002", "测试项目", "奇幻")
        fs_id = database.add_foreshadowing(
            "test_foreshadow_002", 1, 5, "将解决的伏笔"
        )
        database.resolve_foreshadowing(fs_id)
        
        fses = database.get_active_foreshadowings("test_foreshadow_002")
        assert len(fses) == 0


class TestAuditLog:
    """测试审计日志"""
    
    def test_write_audit_log(self, test_db):
        """测试写入审计日志"""
        log_id = database.write_audit_log(
            "创建项目", "create_project", 
            {"title": "测试"}, "成功"
        )
        assert log_id > 0
        
        logs = database.get_audit_logs(10)
        assert len(logs) >= 1
        assert logs[0]['parsed_intent'] == "create_project"


class TestDatabaseUtilities:
    """测试数据库工具函数"""
    
    def test_get_all_tables(self, test_db):
        """测试获取所有表"""
        tables = database.get_all_tables()
        expected = ['novel_projects', 'writing_jobs', 'events_log', 
                   'character_relationships', 'world_graph_edges', 
                   'foreshadowing_ledger', 'audit_log']
        for t in expected:
            assert t in tables
    
    def test_get_table_schema(self, test_db):
        """测试获取表结构"""
        schema = database.get_table_schema("novel_projects")
        assert len(schema) > 0
        # 检查关键字段
        field_names = [s['name'] for s in schema]
        assert 'project_id' in field_names
        assert 'title' in field_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
