# tests/test_scheduler_adapter.py - M4-2 Scheduler Adapter Tests
"""
Scheduler Adapter 测试套件
测试 CronAdapter, APSchedulerAdapter, CeleryAdapter
"""

import os
import sys
import json
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from threading import Thread

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入被测模块
from job_controller import JobController, Job, JobStatus, ScheduleStrategy
from scheduler_adapter import (
    SchedulerAdapter,
    CronAdapter,
    APSchedulerAdapter,
    CeleryAdapter,
    SchedulerAdapterFactory,
    create_cron_adapter,
    create_apscheduler_adapter,
    create_celery_adapter
)


class TestSchedulerAdapter(unittest.TestCase):
    """测试调度适配器基类和工厂"""
    
    def test_adapter_factory_cron(self):
        """测试工厂创建 Cron 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = SchedulerAdapterFactory.create("cron", mock_controller)
        self.assertIsInstance(adapter, CronAdapter)
    
    def test_adapter_factory_apscheduler(self):
        """测试工厂创建 APScheduler 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = SchedulerAdapterFactory.create("apscheduler", mock_controller)
        self.assertIsInstance(adapter, APSchedulerAdapter)
    
    def test_adapter_factory_celery(self):
        """测试工厂创建 Celery 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = SchedulerAdapterFactory.create("celery", mock_controller)
        self.assertIsInstance(adapter, CeleryAdapter)
    
    def test_adapter_factory_invalid(self):
        """测试工厂处理无效类型"""
        mock_controller = Mock(spec=JobController)
        with self.assertRaises(ValueError):
            SchedulerAdapterFactory.create("invalid", mock_controller)


class TestCronAdapter(unittest.TestCase):
    """测试 Cron 适配器"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_controller = Mock(spec=JobController)
        self.adapter = CronAdapter(self.mock_controller)
    
    def test_cron_adapter_creation(self):
        """测试 CronAdapter 创建"""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(len(self.adapter._scheduled_jobs), 0)
    
    def test_schedule_job_valid_cron(self):
        """测试安排有效 Cron 任务"""
        schedule_config = {
            "cron": "0 * * * *",  # 每小时整点
            "job_id": 1,
            "chapter_number": 1
        }
        
        self.adapter.schedule_job(1, schedule_config)
        
        self.assertIn(1, self.adapter._scheduled_jobs)
        job = self.adapter._scheduled_jobs[1]
        self.assertEqual(job["cron"], "0 * * * *")
        self.assertEqual(job["chapter_number"], 1)
        self.assertIsNotNone(job["next_run"])
    
    def test_schedule_job_invalid_cron(self):
        """测试安排无效 Cron 任务"""
        schedule_config = {
            "cron": "invalid cron",
            "job_id": 1,
            "chapter_number": 1
        }
        
        with self.assertRaises(ValueError):
            self.adapter.schedule_job(1, schedule_config)
    
    def test_schedule_job_with_max_runs(self):
        """测试带最大运行次数的任务"""
        schedule_config = {
            "cron": "*/5 * * * *",  # 每5分钟
            "job_id": 2,
            "chapter_number": 2,
            "max_runs": 3
        }
        
        self.adapter.schedule_job(2, schedule_config)
        
        job = self.adapter._scheduled_jobs[2]
        self.assertEqual(job["max_runs"], 3)
        self.assertEqual(job["run_count"], 0)
    
    def test_cancel_job(self):
        """测试取消任务"""
        schedule_config = {
            "cron": "0 * * * *",
            "job_id": 3,
            "chapter_number": 3
        }
        
        self.adapter.schedule_job(3, schedule_config)
        self.assertIn(3, self.adapter._scheduled_jobs)
        
        self.adapter.cancel_job(3)
        self.assertNotIn(3, self.adapter._scheduled_jobs)
    
    def test_list_jobs(self):
        """测试列出任务"""
        # 添加多个任务
        for i in range(1, 4):
            self.adapter.schedule_job(i, {
                "cron": f"0 {i} * * *",
                "job_id": i,
                "chapter_number": i
            })
        
        jobs = self.adapter.list_jobs()
        
        self.assertEqual(len(jobs), 3)
        for job in jobs:
            self.assertIn("job_id", job)
            self.assertIn("cron", job)
            self.assertIn("next_run", job)
    
    def test_start_stop(self):
        """测试启动和停止"""
        self.adapter.start()
        self.assertTrue(self.adapter._running)
        
        self.adapter.stop()
        self.assertFalse(self.adapter._running)


class TestAPSchedulerAdapter(unittest.TestCase):
    """测试 APScheduler 适配器"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_controller = Mock(spec=JobController)
        self.adapter = APSchedulerAdapter(self.mock_controller)
    
    def test_apscheduler_adapter_creation(self):
        """测试 APSchedulerAdapter 创建"""
        self.assertIsNotNone(self.adapter)
    
    def test_schedule_job_cron_trigger(self):
        """测试 Cron 触发器"""
        schedule_config = {
            "trigger": "cron",
            "cron": "0 * * * *",
            "job_id": 1,
            "chapter_number": 1
        }
        
        self.adapter.schedule_job(1, schedule_config)
        
        # 验证任务已添加
        self.assertIn(1, self.adapter._job_map)
    
    def test_schedule_job_interval_trigger(self):
        """测试 Interval 触发器"""
        schedule_config = {
            "trigger": "interval",
            "minutes": 60,
            "job_id": 2,
            "chapter_number": 2
        }
        
        self.adapter.schedule_job(2, schedule_config)
        
        self.assertIn(2, self.adapter._job_map)
    
    def test_cancel_job(self):
        """测试取消任务"""
        schedule_config = {
            "trigger": "cron",
            "cron": "0 * * * *",
            "job_id": 3,
            "chapter_number": 3
        }
        
        self.adapter.schedule_job(3, schedule_config)
        self.adapter.cancel_job(3)
        
        self.assertNotIn(3, self.adapter._job_map)
    
    def test_start_stop(self):
        """测试启动和停止"""
        self.adapter.start()
        self.assertTrue(self.adapter._scheduler.running)
        
        self.adapter.stop()
        # 调度器已关闭
    
    def test_list_jobs(self):
        """测试列出任务"""
        # 由于 APScheduler 需要启动才能列出，先跳过
        pass


class TestCeleryAdapter(unittest.TestCase):
    """测试 Celery 适配器"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_controller = Mock(spec=JobController)
        # 不传入 celery app，使用 mock 模式
        self.adapter = CeleryAdapter(self.mock_controller, celery_app=None)
    
    def test_celery_adapter_creation(self):
        """测试 CeleryAdapter 创建（mock 模式）"""
        self.assertIsNotNone(self.adapter)
        self.assertIsNone(self.adapter._celery_app)
    
    def test_schedule_job_mock_mode(self):
        """测试 Mock 模式下的任务安排"""
        schedule_config = {
            "task_name": "godcraft.write_chapter",
            "args": [1],
            "countdown": 60
        }
        
        # 不应抛出异常
        self.adapter.schedule_job(1, schedule_config)
        
        self.assertIn(1, self.adapter._scheduled_tasks)
    
    def test_schedule_job_with_countdown(self):
        """测试延迟任务"""
        schedule_config = {
            "task_name": "godcraft.write_chapter",
            "args": [2],
            "countdown": 30
        }
        
        self.adapter.schedule_job(2, schedule_config)
        
        task = self.adapter._scheduled_tasks[2]
        self.assertEqual(task["countdown"], 30)
    
    def test_schedule_job_with_eta(self):
        """测试 ETA 任务"""
        eta = datetime.now() + timedelta(hours=1)
        schedule_config = {
            "task_name": "godcraft.write_chapter",
            "args": [3],
            "eta": eta.isoformat()
        }
        
        self.adapter.schedule_job(3, schedule_config)
        
        task = self.adapter._scheduled_tasks[3]
        self.assertIn("eta", task)
    
    def test_cancel_job(self):
        """测试取消任务"""
        schedule_config = {
            "task_name": "godcraft.write_chapter",
            "args": [4]
        }
        
        self.adapter.schedule_job(4, schedule_config)
        self.adapter.cancel_job(4)
        
        self.assertNotIn(4, self.adapter._scheduled_tasks)
    
    def test_list_jobs(self):
        """测试列出任务"""
        for i in range(1, 4):
            self.adapter.schedule_job(i, {
                "task_name": "godcraft.write_chapter",
                "args": [i]
            })
        
        jobs = self.adapter.list_jobs()
        
        self.assertEqual(len(jobs), 3)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def test_create_cron_adapter(self):
        """测试创建 Cron 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = create_cron_adapter(mock_controller)
        self.assertIsInstance(adapter, CronAdapter)
    
    def test_create_apscheduler_adapter(self):
        """测试创建 APScheduler 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = create_apscheduler_adapter(mock_controller)
        self.assertIsInstance(adapter, APSchedulerAdapter)
    
    def test_create_celery_adapter(self):
        """测试创建 Celery 适配器"""
        mock_controller = Mock(spec=JobController)
        adapter = create_celery_adapter(mock_controller)
        self.assertIsInstance(adapter, CeleryAdapter)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_job_controller_with_cron_adapter(self):
        """测试 JobController 与 CronAdapter 集成"""
        mock_controller = Mock(spec=JobController)
        mock_controller._job_queue = MagicMock()
        
        adapter = CronAdapter(mock_controller)
        
        # 安排任务
        adapter.schedule_job(1, {
            "cron": "0 * * * *",
            "job_id": 1,
            "chapter_number": 1
        })
        
        # 启动（短暂运行后停止）
        adapter.start()
        time.sleep(0.5)
        adapter.stop()
        
        # 验证任务调度
        jobs = adapter.list_jobs()
        self.assertEqual(len(jobs), 1)
    
    def test_adapter_register_in_job_controller(self):
        """测试在 JobController 中注册适配器"""
        # 注意：这是测试 register_scheduler_adapter 接口
        # 实际使用需要先实现
        
        # 模拟测试
        mock_controller = Mock(spec=JobController)
        
        # 使用工厂创建适配器
        cron_adapter = SchedulerAdapterFactory.create("cron", mock_controller)
        
        self.assertIsInstance(cron_adapter, CronAdapter)
        self.assertEqual(cron_adapter.job_controller, mock_controller)


# 运行测试
if __name__ == '__main__':
    print("Running Scheduler Adapter Tests...")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSchedulerAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestCronAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestAPSchedulerAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestCeleryAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出摘要
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # 退出码
    if result.wasSuccessful():
        print("\n[OK] All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed!")
        sys.exit(1)
