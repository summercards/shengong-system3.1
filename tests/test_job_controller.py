# test_job_controller.py - M4-1 Job Controller 测试
"""
Job Controller 测试套件
测试任务调度控制器的核心功能
"""

import pytest
import json
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from job_controller import (
    JobController, Job, JobStatus, ScheduleStrategy,
    create_job_controller, create_and_queue_job
)
from database import (
    get_connection, create_project, get_project
)


# === Fixtures ===

@pytest.fixture
def test_project():
    """创建测试项目"""
    project_id = "test_job_ctrl"
    
    # 确保项目存在 - 直接使用 database 函数
    existing = get_project(project_id)
    if not existing:
        from database import create_project
        create_project(
            project_id=project_id,
            title="测试项目",
            genre="测试",
            logline="",
            target_chapters=10,
            interval_minutes=60
        )
    
    yield project_id
    
    # 清理（可选）
    conn = get_connection()
    conn.execute("DELETE FROM writing_jobs WHERE project_id = ?", (project_id,))
    conn.commit()


@pytest.fixture
def controller(test_project):
    """创建 JobController 实例"""
    return JobController(test_project)


# === 测试用例 ===

class TestJobStatus:
    """任务状态枚举测试"""
    
    def test_job_status_values(self):
        """验证所有状态值"""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.PAUSED.value == "paused"


class TestScheduleStrategy:
    """调度策略枚举测试"""
    
    def test_strategy_values(self):
        """验证所有策略值"""
        assert ScheduleStrategy.IMMEDIATE.value == "immediate"
        assert ScheduleStrategy.DELAYED.value == "delayed"
        assert ScheduleStrategy.INTERVAL.value == "interval"
        assert ScheduleStrategy.CRON.value == "cron"
        assert ScheduleStrategy.MANUAL.value == "manual"


class TestJobDataClass:
    """Job 数据类测试"""
    
    def test_create_job_from_dict(self):
        """从字典创建 Job"""
        row = {
            'job_id': 1,
            'project_id': 'test',
            'chapter_number': 1,
            'status': 'pending',
            'schedule_strategy': 'manual',
            'scheduled_time': None,
            'started_at': None,
            'completed_at': None,
            'retry_count': 0,
            'max_retries': 3,
            'error_message': None,
            'result': None,
            'metadata': '{}'
        }
        
        job = Job.from_db_row(row)
        
        assert job.job_id == 1
        assert job.project_id == 'test'
        assert job.chapter_number == 1
        assert job.status == JobStatus.PENDING
        assert job.schedule_strategy == ScheduleStrategy.MANUAL
    
    def test_job_to_dict(self):
        """Job 转字典"""
        job = Job(
            job_id=1,
            project_id='test',
            chapter_number=1,
            status=JobStatus.PENDING,
            schedule_strategy=ScheduleStrategy.MANUAL
        )
        
        d = job.to_dict()
        
        assert d['job_id'] == 1
        assert d['status'] == 'pending'
        assert isinstance(d, dict)


class TestJobController:
    """JobController 核心功能测试"""
    
    def test_create_job_manual(self, controller):
        """测试创建手动任务"""
        success, msg, job_id = controller.create_job(
            chapter_number=1,
            schedule_strategy=ScheduleStrategy.MANUAL
        )
        
        assert success is True
        assert job_id > 0
        assert "created successfully" in msg
        
        # 验证任务存在
        job = controller.get_job(job_id)
        assert job is not None
        assert job.chapter_number == 1
        assert job.status == JobStatus.PENDING
    
    def test_create_job_immediate(self, controller):
        """测试创建立即执行任务"""
        success, msg, job_id = controller.create_job(
            chapter_number=2,
            schedule_strategy=ScheduleStrategy.IMMEDIATE
        )
        
        assert success is True
        assert job_id > 0
    
    def test_create_job_delayed(self, controller):
        """测试创建延迟任务"""
        scheduled_time = datetime.now() + timedelta(minutes=30)
        
        success, msg, job_id = controller.create_job(
            chapter_number=3,
            schedule_strategy=ScheduleStrategy.DELAYED,
            scheduled_time=scheduled_time
        )
        
        assert success is True
        assert job_id > 0
        
        job = controller.get_job(job_id)
        assert job.schedule_strategy == ScheduleStrategy.DELAYED
        assert job.scheduled_time is not None
    
    def test_get_pending_jobs(self, controller):
        """测试获取待执行任务"""
        # 创建多个任务
        for i in range(1, 4):
            controller.create_job(
                chapter_number=i,
                schedule_strategy=ScheduleStrategy.MANUAL
            )
        
        pending = controller.get_pending_jobs()
        assert len(pending) >= 3
    
    def test_get_scheduled_jobs(self, controller):
        """测试获取计划任务"""
        # 创建定时任务
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        controller.create_job(
            chapter_number=10,
            schedule_strategy=ScheduleStrategy.INTERVAL,
            scheduled_time=scheduled_time
        )
        
        scheduled = controller.get_scheduled_jobs()
        # 可能有其他测试的数据
        assert isinstance(scheduled, list)
    
    def test_cancel_job(self, controller):
        """测试取消任务"""
        success, msg, job_id = controller.create_job(
            chapter_number=5,
            schedule_strategy=ScheduleStrategy.MANUAL
        )
        
        # 取消
        success, msg = controller.cancel_job(job_id)
        assert success is True
        
        # 验证已取消
        job = controller.get_job(job_id)
        assert job.status == JobStatus.CANCELLED
    
    def test_cancel_running_job_fails(self, controller):
        """测试无法取消运行中的任务"""
        success, msg, job_id = controller.create_job(
            chapter_number=6,
            schedule_strategy=ScheduleStrategy.MANUAL
        )
        
        # 手动设置为运行中
        from database import execute_write
        execute_write("UPDATE writing_jobs SET status = 'running' WHERE job_id = ?", (job_id,))
        
        # 尝试取消
        success, msg = controller.cancel_job(job_id)
        assert success is False
        assert "running" in msg.lower()
    
    def test_get_job_stats(self, controller):
        """测试获取任务统计"""
        # 创建一些任务
        for i in range(7, 10):
            controller.create_job(
                chapter_number=i,
                schedule_strategy=ScheduleStrategy.MANUAL
            )
        
        stats = controller.get_job_stats()
        
        assert 'total' in stats
        assert stats['total'] > 0
        assert 'pending' in stats
    
    def test_get_job_history(self, controller):
        """测试获取任务历史"""
        history = controller.get_job_history(limit=5)
        
        assert isinstance(history, list)
        # 可能有之前测试的数据


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_job_controller(self):
        """测试创建控制器实例"""
        controller = create_job_controller("test")
        
        assert controller is not None
        assert controller.project_id == "test"
    
    def test_create_and_queue_job(self):
        """测试快速创建并队列任务"""
        project_id = "test_queue_job"
        
        # 确保项目存在 - 直接使用 database
        from database import create_project, get_project
        existing = get_project(project_id)
        if not existing:
            create_project(
                project_id=project_id,
                title="队列测试",
                genre="测试",
                logline="",
                target_chapters=5,
                interval_minutes=30
            )
        
        success, msg, job_id = create_and_queue_job(
            project_id=project_id,
            chapter_number=1,
            execute_now=True
        )
        
        assert success is True
        assert job_id > 0


class TestJobExecution:
    """任务执行测试"""
    
    def test_execute_job_without_executor(self, controller):
        """测试无执行器的任务执行（应失败因为没有 orchestrator）"""
        success, msg, job_id = controller.create_job(
            chapter_number=100,
            schedule_strategy=ScheduleStrategy.MANUAL
        )
        
        # 执行会调用默认执行器，需要 OpenClaw API
        # 这里只测试状态更新，不实际执行
        result = controller.execute_job(job_id, executor=None)
        
        # 由于没有 mock，结果可能是 failed（因为没有真实的 LLM）
        assert 'status' in result


# === 运行测试 ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
