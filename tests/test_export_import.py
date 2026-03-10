# test_export_import.py - M5-2 测试
"""
导入导出与监控模块测试
"""

import os
import sys
import json
import sqlite3
import tempfile
import shutil
from datetime import datetime

import pytest

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from export_import import ExportImportManager, Monitor, export_project, import_project, create_export_manager, create_monitor


# === 测试夹具 ===

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def temp_db(temp_dir):
    """创建临时数据库"""
    db_path = os.path.join(temp_dir, "test.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS novel_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT UNIQUE,
            title TEXT,
            genre TEXT,
            logline TEXT,
            target_chapters INTEGER DEFAULT 50,
            interval_minutes INTEGER DEFAULT 60,
            status TEXT DEFAULT 'pending',
            current_chapter INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS writing_jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            job_type TEXT,
            chapter_number INTEGER,
            status TEXT DEFAULT 'pending',
            schedule_strategy TEXT,
            content TEXT,
            word_count INTEGER DEFAULT 0,
            created_at TEXT,
            started_at TEXT,
            completed_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            chapter_number INTEGER,
            event_type TEXT,
            summary TEXT,
            data TEXT,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            char_id_1 TEXT,
            char_id_2 TEXT,
            relationship_type TEXT,
            strength INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            source_node TEXT,
            target_node TEXT,
            edge_type TEXT,
            weight REAL DEFAULT 1.0,
            notes TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foreshadowing_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            chapter_introduced INTEGER,
            chapter_revealed INTEGER,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_project(temp_db):
    """创建示例项目"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO novel_projects 
        (project_id, title, genre, logline, target_chapters, interval_minutes, status, current_chapter, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test_project",
        "测试小说",
        "奇幻",
        "这是一个测试小说",
        50,
        60,
        "active",
        2,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    # 添加任务
    cursor.execute("""
        INSERT INTO writing_jobs 
        (project_id, job_type, chapter_number, status, schedule_strategy, content, word_count, created_at, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test_project",
        "chapter_write",
        1,
        "completed",
        "immediate",
        "第一章内容",
        1200,
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    cursor.execute("""
        INSERT INTO writing_jobs 
        (project_id, job_type, chapter_number, status, schedule_strategy, content, word_count, created_at, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test_project",
        "chapter_write",
        2,
        "running",
        "immediate",
        "",
        0,
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        ""
    ))
    
    # 添加事件
    cursor.execute("""
        INSERT INTO events_log 
        (project_id, chapter_number, event_type, summary, data, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "test_project",
        1,
        "chapter_completed",
        "第一章完成",
        '{"word_count": 1200}',
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    return "test_project"


# === ExportImportManager 测试 ===

class TestExportImportManager:
    """导入导出管理器测试"""
    
    def test_init(self, temp_db, temp_dir):
        """测试初始化"""
        manager = ExportImportManager(temp_db, temp_dir, temp_dir)
        assert manager.db_path == temp_db
        assert manager.output_dir == temp_dir
        assert manager.config_dir == temp_dir
    
    def test_export_project_json_not_exists(self, temp_db, temp_dir):
        """测试导出不存在的项目"""
        manager = ExportImportManager(temp_db, temp_dir)
        
        with pytest.raises(ValueError, match="不存在"):
            manager.export_project_json("nonexistent")
    
    def test_export_project_json(self, temp_db, temp_dir, sample_project):
        """测试导出项目为 JSON"""
        manager = ExportImportManager(temp_db, temp_dir)
        
        # 创建输出目录和章节文件
        os.makedirs(temp_dir, exist_ok=True)
        with open(os.path.join(temp_dir, "chapter_1.md"), 'w', encoding='utf-8') as f:
            f.write("# 第一章\n\n这是第一章内容")
        
        with open(os.path.join(temp_dir, "chapter_1_meta.json"), 'w', encoding='utf-8') as f:
            json.dump({"word_count": 1200, "title": "开始"}, f)
        
        # 导出
        data = manager.export_project_json(sample_project, include_chapters=True)
        
        assert "version" in data
        assert "exported_at" in data
        assert "project" in data
        assert data["project"]["project_id"] == sample_project
        assert data["project"]["title"] == "测试小说"
        assert len(data["jobs"]) == 2
        assert len(data["events"]) == 1
        assert len(data["chapters"]) == 1
    
    def test_export_project_sql(self, temp_db, temp_dir, sample_project):
        """测试导出项目为 SQL"""
        manager = ExportImportManager(temp_db, temp_dir)
        
        sql = manager.export_project_sql(sample_project)
        
        assert "INSERT INTO novel_projects" in sql
        assert "INSERT INTO writing_jobs" in sql
        assert "INSERT INTO events_log" in sql
        assert "测试小说" in sql
    
    def test_export_project_sql_not_exists(self, temp_db, temp_dir):
        """测试导出不存在的项目 SQL"""
        manager = ExportImportManager(temp_db, temp_dir)
        
        with pytest.raises(ValueError, match="不存在"):
            manager.export_project_sql("nonexistent")
    
    def test_import_project_json(self, temp_db, temp_dir, sample_project):
        """测试导入项目"""
        # 先导出
        manager = ExportImportManager(temp_db, temp_dir)
        
        # 创建输出目录和章节
        os.makedirs(temp_dir, exist_ok=True)
        
        export_data = manager.export_project_json(sample_project, include_chapters=True)
        
        # 清理并重新创建空数据库
        os.remove(temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 重建表结构
        for table in ["novel_projects", "writing_jobs", "events_log", "character_relationships", 
                      "world_graph_edges", "foreshadowing_ledger"]:
            cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        conn.commit()
        conn.close()
        
        # 重新创建manager
        manager = ExportImportManager(temp_db, temp_dir)
        
        # 导入
        imported_id = manager.import_project_json(export_data)
        
        assert imported_id == sample_project
        
        # 验证导入的数据
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM novel_projects WHERE project_id = ?", (sample_project,))
        project = cursor.fetchone()
        conn.close()
        
        assert project is not None
        assert project[1] == sample_project  # project_id
    
    def test_export_chapter_markdown(self, temp_dir):
        """测试导出章节为 Markdown"""
        manager = ExportImportManager(output_dir=temp_dir)
        
        # 创建章节文件
        os.makedirs(temp_dir, exist_ok=True)
        with open(os.path.join(temp_dir, "chapter_5.md"), 'w', encoding='utf-8') as f:
            f.write("# 第五章\n\n这是第五章的内容")
        
        content = manager.export_chapter_markdown("5")
        
        assert "第五章" in content
        assert "这是第五章的内容" in content
    
    def test_export_chapter_markdown_not_exists(self, temp_dir):
        """测试导出不存在的章节"""
        manager = ExportImportManager(output_dir=temp_dir)
        
        with pytest.raises(ValueError, match="不存在"):
            manager.export_chapter_markdown("999")


# === Monitor 测试 ===

class TestMonitor:
    """监控测试"""
    
    def test_init(self, temp_db, temp_dir):
        """测试初始化"""
        monitor = Monitor(temp_db, temp_dir)
        assert monitor.db_path == temp_db
        assert monitor.output_dir == temp_dir
    
    def test_get_project_health_not_exists(self, temp_db, temp_dir):
        """测试获取不存在的项目健康状态"""
        monitor = Monitor(temp_db, temp_dir)
        
        result = monitor.get_project_health("nonexistent")
        
        assert result["status"] == "error"
    
    def test_get_project_health(self, temp_db, temp_dir, sample_project):
        """测试获取项目健康状态"""
        monitor = Monitor(temp_db, temp_dir)
        
        result = monitor.get_project_health(sample_project)
        
        assert result["status"] == "healthy"
        assert result["project_id"] == sample_project
        assert result["title"] == "测试小说"
        assert "progress" in result
        assert result["progress"]["current"] == 2
        assert result["progress"]["target"] == 50
        assert result["jobs"]["completed"] == 1
        assert result["jobs"]["running"] == 1
    
    def test_get_system_stats(self, temp_db, temp_dir, sample_project):
        """测试获取系统统计"""
        monitor = Monitor(temp_db, temp_dir)
        
        result = monitor.get_system_stats()
        
        assert "projects" in result
        assert "jobs" in result
        assert "chapters" in result
        assert result["projects"]["total"] == 1
        assert result["jobs"]["total"] == 2
    
    def test_get_job_progress(self, temp_db, temp_dir, sample_project):
        """测试获取任务进度"""
        monitor = Monitor(temp_db, temp_dir)
        
        # 先获取 job_id
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT job_id FROM writing_jobs WHERE project_id = ?", (sample_project,))
        job_id = cursor.fetchone()[0]
        conn.close()
        
        result = monitor.get_job_progress(job_id)
        
        assert result["status"] != "error"
        assert result["job_id"] == job_id
        assert result["project_id"] == sample_project
    
    def test_get_job_progress_not_exists(self, temp_db, temp_dir):
        """测试获取不存在的任务进度"""
        monitor = Monitor(temp_db, temp_dir)
        
        result = monitor.get_job_progress(99999)
        
        assert result["status"] == "error"
    
    def test_get_recent_activities(self, temp_db, temp_dir, sample_project):
        """测试获取最近活动"""
        monitor = Monitor(temp_db, temp_dir)
        
        result = monitor.get_recent_activities(limit=10)
        
        assert len(result) > 0
        assert result[0]["project_id"] == sample_project


# === 便捷函数测试 ===

class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_export_manager(self, temp_db, temp_dir):
        """测试创建导入导出管理器"""
        manager = create_export_manager(temp_db, temp_dir)
        assert isinstance(manager, ExportImportManager)
    
    def test_create_monitor(self, temp_db, temp_dir):
        """测试创建监控器"""
        monitor = create_monitor(temp_db, temp_dir)
        assert isinstance(monitor, Monitor)
    
    def test_export_project_json_format(self, temp_db, temp_dir, sample_project):
        """测试导出项目便捷函数"""
        result = export_project(sample_project, format="json", include_chapters=False, db_path=temp_db)
        
        data = json.loads(result)
        assert "project" in data
        assert data["project"]["project_id"] == sample_project
    
    def test_export_project_sql_format(self, temp_db, temp_dir, sample_project):
        """测试导出项目为 SQL"""
        result = export_project(sample_project, format="sql", db_path=temp_db)
        
        assert "INSERT INTO novel_projects" in result
    
    def test_export_project_invalid_format(self, temp_db, temp_dir, sample_project):
        """测试无效格式"""
        with pytest.raises(ValueError, match="不支持"):
            export_project(sample_project, format="invalid", db_path=temp_db)


# === 运行测试 ===

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
