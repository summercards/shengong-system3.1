# test_app.py - M5-1 Streamlit UI / API Tests
"""
M5-1 测试套件
测试 Streamlit UI 和 Minimal API 功能
"""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# === 测试配置 ===

@pytest.fixture
def temp_project_dir(tmp_path):
    """创建临时项目目录"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # 创建必要的目录
    (project_dir / "data").mkdir()
    (project_dir / "output").mkdir()
    (project_dir / "config").mkdir()
    
    # 创建数据库
    db_path = project_dir / "data" / "godcraft.db"
    
    return project_dir


# === API 端点测试 ===

class TestAPIHealth:
    """健康检查端点测试"""
    
    def test_root_endpoint(self):
        """测试根路径"""
        # Mock the FastAPI app
        with patch('api.get_connection') as mock_conn:
            mock_conn.return_value = MagicMock()
            
            from api import root
            result = root()
            
            assert "name" in result
            assert "version" in result
            assert result["name"] == "神工系统 API"
    
    def test_health_check(self):
        """测试健康检查"""
        with patch('api.get_connection') as mock_conn:
            mock_conn.return_value = MagicMock()
            
            with patch('api.os.path.exists', return_value=True):
                from api import health_check
                result = health_check()
                
                assert "status" in result
                assert "database" in result
                assert result["database"] == "ok"


class TestAPIProjects:
    """项目接口测试"""
    
    @patch('api.get_all_projects')
    def test_list_projects_empty(self, mock_get_all):
        """测试空项目列表"""
        mock_get_all.return_value = []
        
        from api import list_projects
        result = list_projects()
        
        assert result == []
    
    @patch('api.get_all_projects')
    def test_list_projects_with_data(self, mock_get_all):
        """测试有数据的项目列表"""
        mock_get_all.return_value = [
            {
                "project_id": "test_001",
                "title": "测试小说",
                "genre": "奇幻",
                "status": "active",
                "current_chapter": 5,
                "target_chapters": 50,
                "logline": "测试简介",
                "created_at": "2026-03-10"
            }
        ]
        
        from api import list_projects
        result = list_projects()
        
        assert len(result) == 1
        assert result[0].project_id == "test_001"
        assert result[0].title == "测试小说"
    
    @patch('api.db_create_project')
    @patch('api.log_event')
    @patch('api.db_get_project')
    def test_create_project(self, mock_get, mock_log, mock_create):
        """测试创建项目"""
        # Mock project doesn't exist
        mock_get.return_value = None
        mock_create.return_value = 1
        
        from api import ProjectCreate, create_project
        request = ProjectCreate(
            project_id="new_project",
            title="新小说",
            genre="科幻",
            logline="新简介",
            target_chapters=30,
            interval_minutes=45
        )
        
        result = create_project(request)
        
        assert result.project_id == "new_project"
        assert result.title == "新小说"
        mock_create.assert_called_once()
        mock_log.assert_called_once()
    
    @patch('api.db_get_project')
    def test_get_project_not_found(self, mock_get):
        """测试获取不存在的项目"""
        mock_get.return_value = None
        
        from api import get_project
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_project("nonexistent")
        
        assert exc_info.value.status_code == 404


class TestAPIJobs:
    """任务接口测试"""
    
    @patch('api.get_connection')
    def test_list_jobs_empty(self, mock_conn):
        """测试空任务列表"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        from api import list_jobs
        result = list_jobs()
        
        assert result == []
    
    @patch('api.get_connection')
    def test_list_jobs_with_filter(self, mock_conn):
        """测试带筛选的任务列表"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "job_id": "job_001",
                "project_id": "test_001",
                "job_type": "chapter_write",
                "chapter_number": 1,
                "status": "completed",
                "schedule_strategy": "immediate",
                "created_at": "2026-03-10",
                "completed_at": "2026-03-10"
            }
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        from api import list_jobs
        result = list_jobs(status="completed")
        
        assert len(result) == 1
        assert result[0].status == "completed"


class TestAPIChapters:
    """章节接口测试"""
    
    @patch('api.get_output_dir')
    def test_list_chapters_empty(self, mock_output_dir):
        """测试空章节列表"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_output_dir.return_value = tmpdir
            
            from api import list_chapters
            result = list_chapters(project_id="test")
            
            assert result["total"] == 0
            assert result["chapters"] == []
    
    @patch('api.get_output_dir')
    def test_list_chapters_with_data(self, mock_output_dir):
        """测试有章节数据"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试章节文件
            chapter_file = os.path.join(tmpdir, "chapter_1.md")
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write("# 第一章\n\n测试内容")
            
            # 创建元数据文件
            meta_file = os.path.join(tmpdir, "chapter_1_meta.json")
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({"title": "第一章"}, f)
            
            mock_output_dir.return_value = tmpdir
            
            from api import list_chapters
            result = list_chapters(project_id="test")
            
            assert result["total"] == 1
            assert result["chapters"][0]["number"] == "1"
            assert result["chapters"][0]["has_meta"] is True


class TestAPIStats:
    """统计接口测试"""
    
    @patch('api.get_connection')
    @patch('api.get_output_dir')
    def test_get_stats(self, mock_output_dir, mock_conn):
        """测试系统统计"""
        # Mock database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            5,  # project count
            ["completed", 10],  # job stats
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # Mock output directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test chapter files
            for i in range(3):
                chapter_file = os.path.join(tmpdir, f"chapter_{i+1}.md")
                with open(chapter_file, 'w') as f:
                    f.write("test")
            
            mock_output_dir.return_value = tmpdir
            
            from api import get_stats
            result = get_stats()
            
            assert result["projects"] == 5
            assert result["chapters"] == 3
            assert "jobs" in result


# === Streamlit UI 功能测试 ===

class TestUIComponents:
    """UI 组件测试"""
    
    def test_db_path_function(self):
        """测试数据库路径函数"""
        from api import get_db_path
        path = get_db_path()
        
        assert path.endswith("godcraft.db")
        assert "godcraft_v4" in path or "data" in path
    
    def test_output_dir_function(self):
        """测试输出目录函数"""
        with patch('api.os.makedirs') as mock_makedirs:
            with patch('api.os.path.exists', return_value=True):
                from api import get_output_dir
                path = get_output_dir()
                
                assert "output" in path
    
    @patch('api.load_config')
    def test_load_world_setting(self, mock_config):
        """测试加载世界设置"""
        mock_config.return_value = {
            "world": {
                "name": "测试世界",
                "description": "测试描述"
            }
        }
        
        from api import load_world_setting
        result = load_world_setting()
        
        assert "world" in result
        assert result["world"]["name"] == "测试世界"


class TestUIIntegration:
    """UI 集成测试"""
    
    @patch('api.get_connection')
    @patch('api.os.path.exists')
    def test_render_home_page(self, mock_exists, mock_conn):
        """测试首页渲染"""
        mock_exists.return_value = True
        
        # Mock database cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # project count
            (2,),  # pending jobs
            (1,),  # running jobs
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # 测试页面函数可以被导入
        from api import render_home, render_project_management
        
        # 这些函数需要 Streamlit 环境，这里只测试导入
        assert render_home is not None


# === 数据模型测试 ===

class TestDataModels:
    """数据模型测试"""
    
    def test_project_create_model(self):
        """测试项目创建模型"""
        from api import ProjectCreate
        
        project = ProjectCreate(
            project_id="test_001",
            title="测试项目",
            genre="奇幻",
            logline="测试简介",
            target_chapters=20,
            interval_minutes=30
        )
        
        assert project.project_id == "test_001"
        assert project.title == "测试项目"
        assert project.genre == "奇幻"
    
    def test_chapter_write_request_model(self):
        """测试章节写作请求模型"""
        from api import ChapterWriteRequest
        
        request = ChapterWriteRequest(
            chapter_number=5,
            target_length=1500,
            enable_review=True
        )
        
        assert request.chapter_number == 5
        assert request.target_length == 1500
        assert request.enable_review is True
    
    def test_project_response_model(self):
        """测试项目响应模型"""
        from api import ProjectResponse
        
        response = ProjectResponse(
            project_id="test_001",
            title="测试项目",
            genre="奇幻",
            status="active",
            current_chapter=3,
            target_chapters=20,
            logline="测试",
            created_at="2026-03-10"
        )
        
        assert response.project_id == "test_001"
        assert response.current_chapter == 3


# === 错误处理测试 ===

class TestErrorHandling:
    """错误处理测试"""
    
    @patch('api.db_get_project')
    def test_write_chapter_project_not_found(self, mock_get):
        """测试章节写作 - 项目不存在"""
        mock_get.return_value = None
        
        from api import write_chapter, ChapterWriteRequest
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            write_chapter("nonexistent", ChapterWriteRequest(chapter_number=1))
        
        assert exc_info.value.status_code == 404
    
    @patch('api.get_output_dir')
    def test_get_chapter_not_found(self, mock_output_dir):
        """测试获取不存在的章节"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_output_dir.return_value = tmpdir
            
            from api import get_chapter
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                get_chapter("999")
            
            assert exc_info.value.status_code == 404


# === 运行测试 ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
