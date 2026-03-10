# scheduler_adapter.py - M4-2 Scheduler Adapter 注册任务
"""
Scheduler Adapter - 调度适配器
为 JobController 提供多种调度后端支持

支持:
1. CronAdapter - Cron 表达式调度
2. APSchedulerAdapter - APScheduler 高级调度
3. CeleryAdapter - Celery 分布式任务队列
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Any
from abc import ABC, abstractmethod
from croniter import croniter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger as APSCronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入项目模块
from job_controller import JobController, Job, JobStatus, ScheduleStrategy


# === 调度适配器基类 ===

class SchedulerAdapter(ABC):
    """调度适配器抽象基类"""
    
    @abstractmethod
    def start(self):
        """启动调度器"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止调度器"""
        pass
    
    @abstractmethod
    def schedule_job(self, job_id: int, schedule_config: dict):
        """安排任务"""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: int):
        """取消任务"""
        pass
    
    @abstractmethod
    def list_jobs(self) -> List[dict]:
        """列出所有计划任务"""
        pass


# === Cron 适配器 ===

class CronAdapter(SchedulerAdapter):
    """
    Cron 表达式调度适配器
    支持标准 Cron 表达式（5字段）
    """
    
    def __init__(self, job_controller: JobController):
        self.job_controller = job_controller
        self._scheduled_jobs: Dict[int, dict] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self):
        """启动 Cron 调度器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._cron_loop, daemon=True)
        self._thread.start()
        print(f"[CronAdapter] Started")
    
    def stop(self):
        """停止 Cron 调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print(f"[CronAdapter] Stopped")
    
    def schedule_job(self, job_id: int, schedule_config: dict):
        """
        安排 Cron 任务
        
        schedule_config 格式:
        {
            "cron": "0 * * * *",  # 每小时整点
            "job_id": 123,
            "chapter_number": 1,
            "max_runs": 10  # 最多运行次数，可选
        }
        """
        with self._lock:
            cron_expr = schedule_config.get("cron", "0 * * * *")
            
            # 验证 Cron 表达式
            if not croniter.is_valid(cron_expr):
                raise ValueError(f"Invalid cron expression: {cron_expr}")
            
            # 计算下次执行时间
            now = datetime.now()
            cron = croniter(cron_expr, now)
            next_run = cron.get_next(datetime)
            
            self._scheduled_jobs[job_id] = {
                "job_id": job_id,
                "cron": cron_expr,
                "next_run": next_run,
                "chapter_number": schedule_config.get("chapter_number", 1),
                "max_runs": schedule_config.get("max_runs"),
                "run_count": 0,
                "enabled": True
            }
            
            print(f"[CronAdapter] Scheduled job {job_id} with cron '{cron_expr}', next run: {next_run}")
    
    def cancel_job(self, job_id: int):
        """取消任务"""
        with self._lock:
            if job_id in self._scheduled_jobs:
                del self._scheduled_jobs[job_id]
                print(f"[CronAdapter] Cancelled job {job_id}")
    
    def list_jobs(self) -> List[dict]:
        """列出所有计划任务"""
        with self._lock:
            jobs = []
            for job_id, config in self._scheduled_jobs.items():
                jobs.append({
                    "job_id": job_id,
                    "cron": config["cron"],
                    "next_run": config["next_run"].isoformat() if config["next_run"] else None,
                    "chapter_number": config["chapter_number"],
                    "run_count": config["run_count"],
                    "max_runs": config["max_runs"],
                    "enabled": config["enabled"]
                })
            return jobs
    
    def _cron_loop(self):
        """Cron 检查循环"""
        while self._running:
            try:
                now = datetime.now()
                
                with self._lock:
                    to_execute = []
                    
                    for job_id, config in self._scheduled_jobs.items():
                        if not config["enabled"]:
                            continue
                        
                        # 检查是否到达执行时间
                        if config["next_run"] and now >= config["next_run"]:
                            # 检查最大运行次数
                            if config["max_runs"] and config["run_count"] >= config["max_runs"]:
                                del self._scheduled_jobs[job_id]
                                continue
                            
                            to_execute.append(job_id)
                            
                            # 更新运行计数
                            config["run_count"] += 1
                            
                            # 计算下次执行时间
                            cron = croniter(config["cron"], now)
                            config["next_run"] = cron.get_next(datetime)
                    
                    # 执行任务
                    for job_id in to_execute:
                        config = self._scheduled_jobs.get(job_id)
                        if config:
                            print(f"[CronAdapter] Executing job {job_id}")
                            self.job_controller._job_queue.put(job_id)
                
            except Exception as e:
                print(f"[CronAdapter] Cron loop error: {e}")
            
            time.sleep(10)  # 每 10 秒检查一次


# === APScheduler 适配器 ===

class APSchedulerAdapter(SchedulerAdapter):
    """
    APScheduler 高级调度适配器
    支持 Cron、Interval、Date 等多种触发器
    """
    
    def __init__(self, job_controller: JobController):
        self.job_controller = job_controller
        self._scheduler = BackgroundScheduler()
        self._job_map: Dict[int, str] = {}  # job_id -> apscheduler job id
        self._lock = threading.Lock()
    
    def start(self):
        """启动 APScheduler"""
        if self._scheduler.running:
            return
        
        self._scheduler.start()
        print(f"[APSchedulerAdapter] Started")
    
    def stop(self):
        """停止 APScheduler"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
        print(f"[APSchedulerAdapter] Stopped")
    
    def schedule_job(self, job_id: int, schedule_config: dict):
        """
        安排 APScheduler 任务
        
        schedule_config 格式:
        {
            "trigger": "cron",  # cron, interval, date
            "cron": "0 * * * *",  # 当 trigger=cron 时
            "minutes": 60,        # 当 trigger=interval 时
            "chapter_number": 1,
            "job_id": job_id
        }
        """
        trigger_type = schedule_config.get("trigger", "cron")
        
        if trigger_type == "cron":
            cron_expr = schedule_config.get("cron", "0 * * * *")
            # 解析 Cron 表达式 (分钟 小时 日 月 周)
            parts = cron_expr.split()
            if len(parts) == 5:
                trigger = APSCronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                trigger = APSCronTrigger.from_crontab(cron_expr)
        
        elif trigger_type == "interval":
            minutes = schedule_config.get("minutes", 60)
            trigger = IntervalTrigger(minutes=minutes)
        
        else:
            raise ValueError(f"Unsupported trigger type: {trigger_type}")
        
        # 添加任务
        def job_executor():
            print(f"[APSchedulerAdapter] Executing job {job_id}")
            self.job_controller._job_queue.put(job_id)
        
        with self._lock:
            aps_job = self._scheduler.add_job(
                job_executor,
                trigger=trigger,
                id=str(job_id),
                replace_existing=True
            )
            self._job_map[job_id] = aps_job.id
        
        print(f"[APSchedulerAdapter] Scheduled job {job_id} with {trigger_type} trigger")
    
    def cancel_job(self, job_id: int):
        """取消任务"""
        with self._lock:
            if job_id in self._job_map:
                self._scheduler.remove_job(self._job_map[job_id])
                del self._job_map[job_id]
                print(f"[APSchedulerAdapter] Cancelled job {job_id}")
    
    def list_jobs(self) -> List[dict]:
        """列出所有计划任务"""
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "job_id": int(job.id),
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "trigger": str(job.trigger)
            })
        return jobs


# === Celery 适配器 ===

class CeleryAdapter(SchedulerAdapter):
    """
    Celery 分布式任务队列适配器
    需要安装 celery 并配置 broker
    """
    
    def __init__(self, job_controller: JobController, celery_app=None):
        self.job_controller = job_controller
        self._celery_app = celery_app
        self._scheduled_tasks: Dict[int, dict] = {}
        self._lock = threading.Lock()
        
        # 如果没有传入 celery app，尝试导入
        if celery_app is None:
            try:
                from celery import Celery
                # 默认配置（实际使用时应配置 broker）
                self._celery_app = Celery('godcraft')
                self._celery_app.config_from_object({
                    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
                    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
                })
            except ImportError:
                print("[CeleryAdapter] Celery not installed, running in mock mode")
                self._celery_app = None
    
    def start(self):
        """启动 Celery 监控"""
        if self._celery_app:
            print(f"[CeleryAdapter] Started (connected to {self._celery_app.main})")
        else:
            print(f"[CeleryAdapter] Started (mock mode)")
    
    def stop(self):
        """停止"""
        print(f"[CeleryAdapter] Stopped")
    
    def schedule_job(self, job_id: int, schedule_config: dict):
        """
        创建 Celery 任务
        
        schedule_config 格式:
        {
            "task_name": "godcraft.write_chapter",
            "args": [job_id],
            "cron": "0 * * * *",  # 可选的 Cron 调度
            "countdown": 60,      # 延迟秒数
            "eta": "2026-03-10T16:00:00",  # 精确执行时间
        }
        """
        with self._lock:
            if self._celery_app:
                task_name = schedule_config.get("task_name", "godcraft.write_chapter")
                args = schedule_config.get("args", [job_id])
                
                # 延迟执行
                if "countdown" in schedule_config:
                    self._celery_app.send_task(
                        task_name,
                        args=args,
                        countdown=schedule_config["countdown"]
                    )
                # 定时执行 (ETA)
                elif "eta" in schedule_config:
                    eta = datetime.fromisoformat(schedule_config["eta"])
                    self._celery_app.send_task(
                        task_name,
                        args=args,
                        eta=eta
                    )
                # Cron 调度 (需要 celery beat)
                elif "cron" in schedule_config:
                    # Celery Beat 会定期发送任务
                    print(f"[CeleryAdapter] Cron scheduling requires celery beat")
                
                print(f"[CeleryAdapter] Scheduled Celery task for job {job_id}")
            else:
                # Mock 模式
                print(f"[CeleryAdapter] Mock: would schedule job {job_id}")
            
            self._scheduled_tasks[job_id] = schedule_config
    
    def cancel_job(self, job_id: int):
        """撤销任务"""
        with self._lock:
            if job_id in self._scheduled_tasks:
                if self._celery_app:
                    # 尝试撤销任务（需要 task_id）
                    pass
                del self._scheduled_tasks[job_id]
                print(f"[CeleryAdapter] Cancelled job {job_id}")
    
    def list_jobs(self) -> List[dict]:
        """列出所有计划任务"""
        with self._lock:
            return [
                {**config, "job_id": job_id}
                for job_id, config in self._scheduled_tasks.items()
            ]


# === 适配器工厂 ===

class SchedulerAdapterFactory:
    """调度适配器工厂"""
    
    @staticmethod
    def create(adapter_type: str, job_controller: JobController, config: dict = None) -> SchedulerAdapter:
        """
        创建调度适配器
        
        参数:
            adapter_type: 适配器类型 ("cron", "apscheduler", "celery")
            job_controller: JobController 实例
            config: 适配器配置
        
        返回:
            SchedulerAdapter 实例
        """
        config = config or {}
        
        if adapter_type == "cron":
            return CronAdapter(job_controller)
        elif adapter_type == "apscheduler":
            return APSchedulerAdapter(job_controller)
        elif adapter_type == "celery":
            celery_app = config.get("celery_app")
            return CeleryAdapter(job_controller, celery_app)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")


# === 便捷函数 ===

def create_cron_adapter(job_controller: JobController) -> CronAdapter:
    """创建 Cron 适配器"""
    return CronAdapter(job_controller)


def create_apscheduler_adapter(job_controller: JobController) -> APSchedulerAdapter:
    """创建 APScheduler 适配器"""
    return APSchedulerAdapter(job_controller)


def create_celery_adapter(job_controller: JobController, celery_app=None) -> CeleryAdapter:
    """创建 Celery 适配器"""
    return CeleryAdapter(job_controller, celery_app)


# 导出
__all__ = [
    'SchedulerAdapter',
    'CronAdapter',
    'APSchedulerAdapter', 
    'CeleryAdapter',
    'SchedulerAdapterFactory',
    'create_cron_adapter',
    'create_apscheduler_adapter',
    'create_celery_adapter'
]
