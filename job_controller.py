# job_controller.py - M4-1 Job Controller 任务调度控制器
"""
Job Controller - 任务调度控制器
负责管理写作任务的队列、调度执行、定时触发

核心职责：
1. 任务队列管理 - 创建、获取、更新、删除
2. 定时调度 - 按 interval_minutes 自动触发章节写作
3. 任务依赖 - 任务之间的依赖关系管理
4. 调度策略 - 支持立即执行、延迟执行、定时执行
5. Scheduler Adapter 接口 - M4-2 实现具体适配器
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from queue import Queue, Empty

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入项目模块
from database import (
    get_connection, execute_write, execute_query,
    create_job as db_create_job,
    get_job as db_get_job,
    update_job_status as db_update_job_status,
    get_project, increment_chapter
)
from structured_store import StructuredStore


# 任务状态枚举
class JobStatus(Enum):
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 执行失败
    CANCELLED = "cancelled"   # 已取消
    PAUSED = "paused"         # 已暂停


# 调度策略枚举
class ScheduleStrategy(Enum):
    IMMEDIATE = "immediate"     # 立即执行
    DELAYED = "delayed"         # 延迟执行
    INTERVAL = "interval"       # 间隔执行
    CRON = "cron"               # Cron 表达式
    MANUAL = "manual"           # 手动触发


@dataclass
class Job:
    """任务数据类"""
    job_id: int
    project_id: str
    chapter_number: int
    status: JobStatus
    schedule_strategy: ScheduleStrategy
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[dict] = None
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Job':
        """从数据库行创建 Job 对象"""
        return cls(
            job_id=row['job_id'],
            project_id=row['project_id'],
            chapter_number=row['chapter_number'],
            status=JobStatus(row['status']),
            schedule_strategy=ScheduleStrategy(row.get('schedule_strategy', 'manual')),
            scheduled_time=datetime.fromisoformat(row['scheduled_time']) if row.get('scheduled_time') else None,
            started_at=datetime.fromisoformat(row['started_at']) if row.get('started_at') else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None,
            retry_count=row.get('retry_count', 0),
            max_retries=row.get('max_retries', 3),
            error_message=row.get('error_message'),
            result=json.loads(row['result']) if row.get('result') else None,
            metadata=json.loads(row['metadata']) if row.get('metadata') else {}
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "chapter_number": self.chapter_number,
            "status": self.status.value,
            "schedule_strategy": self.schedule_strategy.value,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "result": self.result,
            "metadata": self.metadata
        }


class JobController:
    """
    Job Controller - 任务调度控制器
    管理整个写作任务的生命周期
    """
    
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.store = StructuredStore()
        self._job_queue: Queue = Queue()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        
        # 调度器配置
        self._schedule_jobs: Dict[int, dict] = {}  # job_id -> schedule config
    
    # === 任务队列操作 ===
    
    def create_job(self, chapter_number: int, 
                   schedule_strategy: ScheduleStrategy = ScheduleStrategy.MANUAL,
                   scheduled_time: Optional[datetime] = None,
                   max_retries: int = 3,
                   metadata: dict = None) -> tuple[bool, str, int]:
        """
        创建新任务
        
        参数:
            chapter_number: 章节编号
            schedule_strategy: 调度策略
            scheduled_time: 计划执行时间
            max_retries: 最大重试次数
            metadata: 额外元数据
        
        返回: (success, message, job_id)
        """
        # 验证项目存在
        project = get_project(self.project_id)
        if not project:
            return False, f"Project {self.project_id} not found", -1
        
        # 创建数据库记录
        try:
            job_id = db_create_job(self.project_id, chapter_number)
            
            # 更新调度策略和计划时间
            if schedule_strategy != ScheduleStrategy.MANUAL or scheduled_time:
                execute_write(
                    """UPDATE writing_jobs 
                       SET schedule_strategy = ?, scheduled_time = ?, max_retries = ?, metadata = ?
                       WHERE job_id = ?""",
                    (schedule_strategy.value, 
                     scheduled_time.isoformat() if scheduled_time else None,
                     max_retries,
                     json.dumps(metadata or {}),
                     job_id)
                )
            
            # 如果是立即执行，加入队列
            if schedule_strategy == ScheduleStrategy.IMMEDIATE:
                self._job_queue.put(job_id)
            
            return True, f"Job {job_id} created successfully", job_id
        except Exception as e:
            return False, f"Failed to create job: {str(e)}", -1
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """获取任务"""
        row = db_get_job(job_id)
        if not row:
            return None
        return Job.from_db_row(row)
    
    def get_pending_jobs(self, limit: int = 10) -> List[Job]:
        """获取待执行任务列表"""
        rows = execute_query(
            """SELECT * FROM writing_jobs 
               WHERE project_id = ? AND status = 'pending'
               ORDER BY chapter_number ASC LIMIT ?""",
            (self.project_id, limit)
        )
        return [Job.from_db_row(row) for row in rows]
    
    def get_scheduled_jobs(self) -> List[Job]:
        """获取计划中的任务"""
        rows = execute_query(
            """SELECT * FROM writing_jobs 
               WHERE project_id = ? AND schedule_strategy != 'manual'
               AND status IN ('pending', 'paused')
               ORDER BY scheduled_time ASC""",
            (self.project_id,)
        )
        return [Job.from_db_row(row) for row in rows]
    
    def cancel_job(self, job_id: int) -> tuple[bool, str]:
        """取消任务"""
        job = self.get_job(job_id)
        if not job:
            return False, f"Job {job_id} not found"
        
        if job.status == JobStatus.RUNNING:
            return False, "Cannot cancel running job"
        
        db_update_job_status(job_id, "cancelled")
        return True, f"Job {job_id} cancelled"
    
    def retry_job(self, job_id: int) -> tuple[bool, str]:
        """重试失败的任务"""
        job = self.get_job(job_id)
        if not job:
            return False, f"Job {job_id} not found"
        
        if job.status != JobStatus.FAILED:
            return False, "Only failed jobs can be retried"
        
        if job.retry_count >= job.max_retries:
            return False, "Max retries reached"
        
        # 重置状态
        execute_write(
            "UPDATE writing_jobs SET status = 'pending', error_message = NULL, retry_count = retry_count + 1 WHERE job_id = ?",
            (job_id,)
        )
        
        # 加入队列
        self._job_queue.put(job_id)
        
        return True, f"Job {job_id} queued for retry"
    
    # === 任务执行 ===
    
    def execute_job(self, job_id: int, executor: Callable[[int], dict] = None) -> dict:
        """
        执行任务
        
        参数:
            job_id: 任务 ID
            executor: 自定义执行器函数，接收 chapter_number，返回结果字典
        
        返回: 执行结果
        """
        job = self.get_job(job_id)
        if not job:
            return {"status": "failed", "message": f"Job {job_id} not found"}
        
        if job.status == JobStatus.RUNNING:
            return {"status": "failed", "message": "Job is already running"}
        
        # 更新状态为 running
        db_update_job_status(job_id, "running")
        execute_write(
            "UPDATE writing_jobs SET started_at = ? WHERE job_id = ?",
            (datetime.now().isoformat(), job_id)
        )
        
        try:
            # 使用默认执行器或自定义执行器
            if executor:
                result = executor(job.chapter_number)
            else:
                result = self._default_executor(job.chapter_number)
            
            # 成功
            db_update_job_status(job_id, "completed")
            execute_write(
                """UPDATE writing_jobs 
                   SET completed_at = ?, result = ? 
                   WHERE job_id = ?""",
                (datetime.now().isoformat(), json.dumps(result), job_id)
            )
            
            # 更新项目章节计数
            increment_chapter(self.project_id)
            
            # 触发回调
            self._trigger_callback("on_job_complete", job, result)
            
            return {"status": "success", "job_id": job_id, "result": result}
            
        except Exception as e:
            # 失败
            error_msg = str(e)
            db_update_job_status(job_id, "failed")
            execute_write(
                """UPDATE writing_jobs 
                   SET error_message = ?, retry_count = retry_count + 1 
                   WHERE job_id = ?""",
                (error_msg, job_id)
            )
            
            # 触发回调
            self._trigger_callback("on_job_failed", job, error_msg)
            
            # 自动重试
            if job.retry_count < job.max_retries:
                self._job_queue.put(job_id)
            
            return {"status": "failed", "job_id": job_id, "error": error_msg}
    
    def _default_executor(self, chapter_number: int) -> dict:
        """默认执行器 - 调用 Orchestrator"""
        from orchestrator import Orchestrator
        
        orch = Orchestrator(self.project_id)
        result = orch.story_cycle(chapter_num=chapter_number)
        
        return result
    
    # === 调度器控制 ===
    
    def start_scheduler(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动调度检查线程
        self._scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._scheduler_thread.start()
        
        # 启动工作线程
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        
        print(f"[JobController] Scheduler started for project {self.project_id}")
    
    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        
        print(f"[JobController] Scheduler stopped for project {self.project_id}")
    
    def _schedule_loop(self):
        """调度检查循环"""
        while self._running:
            try:
                # 检查计划任务
                now = datetime.now()
                
                rows = execute_query(
                    """SELECT job_id FROM writing_jobs 
                       WHERE project_id = ? 
                       AND status = 'pending' 
                       AND schedule_strategy IN ('interval', 'delayed')
                       AND scheduled_time <= ?""",
                    (self.project_id, now.isoformat())
                )
                
                for row in rows:
                    self._job_queue.put(row['job_id'])
                
                # 检查 interval 任务（根据项目配置）
                project = get_project(self.project_id)
                if project and project.get('status') == 'running':
                    interval = project.get('interval_minutes', 60)
                    last_chapter_time = project.get('updated_at')
                    
                    # 如果是间隔执行模式，检查是否需要创建新任务
                    pass
                
            except Exception as e:
                print(f"[JobController] Schedule loop error: {e}")
            
            time.sleep(10)  # 每 10 秒检查一次
    
    def _worker_loop(self):
        """工作线程循环"""
        while self._running:
            try:
                # 从队列获取任务（阻塞等待）
                job_id = self._job_queue.get(timeout=1)
                
                # 执行任务
                self.execute_job(job_id)
                
                self._job_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                print(f"[JobController] Worker loop error: {e}")
    
    # === 定时任务调度 ===
    
    def schedule_interval_job(self, chapter_number: int, interval_minutes: int) -> tuple[bool, str, int]:
        """
        创建定时间隔任务
        
        参数:
            chapter_number: 章节编号
            interval_minutes: 间隔分钟数
        
        返回: (success, message, job_id)
        """
        scheduled_time = datetime.now() + timedelta(minutes=interval_minutes)
        
        return self.create_job(
            chapter_number=chapter_number,
            schedule_strategy=ScheduleStrategy.INTERVAL,
            scheduled_time=scheduled_time,
            metadata={"interval_minutes": interval_minutes}
        )
    
    def schedule_delayed_job(self, chapter_number: int, delay_minutes: int) -> tuple[bool, str, int]:
        """创建延迟任务"""
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        
        return self.create_job(
            chapter_number=chapter_number,
            schedule_strategy=ScheduleStrategy.DELAYED,
            scheduled_time=scheduled_time
        )
    
    # === 回调机制 ===
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调"""
        self._callbacks[event] = callback
    
    def _trigger_callback(self, event: str, job: Job, data: Any):
        """触发回调"""
        if event in self._callbacks:
            try:
                self._callbacks[event](job, data)
            except Exception as e:
                print(f"[JobController] Callback error: {e}")
    
    # === 调度适配器接口 (M4-2 预留) ===
    
    def register_scheduler_adapter(self, adapter_name: str, adapter_config: dict):
        """
        注册调度适配器 (M4-2)
        
        支持的适配器:
        - "cron": Cron 表达式调度
        - "apscheduler": APScheduler 高级调度
        - "celery": Celery 分布式任务队列
        """
        # TODO: M4-2 实现
        print(f"[JobController] Scheduler adapter '{adapter_name}' registered (M4-2)")
        self._schedule_jobs[f"adapter_{adapter_name}"] = adapter_config
    
    # === 统计和报告 ===
    
    def get_job_stats(self) -> dict:
        """获取任务统计"""
        rows = execute_query(
            """SELECT status, COUNT(*) as count 
               FROM writing_jobs 
               WHERE project_id = ?
               GROUP BY status""",
            (self.project_id,)
        )
        
        stats = {s['status']: s['count'] for s in rows}
        
        # 添加总计
        stats['total'] = sum(stats.values())
        
        return stats
    
    def get_job_history(self, limit: int = 20) -> List[dict]:
        """获取任务历史"""
        rows = execute_query(
            """SELECT * FROM writing_jobs 
               WHERE project_id = ?
               ORDER BY created_at DESC 
               LIMIT ?""",
            (self.project_id, limit)
        )
        
        return [Job.from_db_row(row).to_dict() for row in rows]


# === 便捷函数 ===

def create_job_controller(project_id: str = "default") -> JobController:
    """创建 JobController 实例"""
    return JobController(project_id)


def create_and_queue_job(project_id: str, chapter_number: int, 
                         execute_now: bool = True) -> tuple[bool, str, int]:
    """
    快速创建并加入队列的任务
    
    参数:
        project_id: 项目 ID
        chapter_number: 章节编号
        execute_now: 是否立即执行
    
    返回: (success, message, job_id)
    """
    controller = JobController(project_id)
    
    strategy = ScheduleStrategy.IMMEDIATE if execute_now else ScheduleStrategy.MANUAL
    
    return controller.create_job(
        chapter_number=chapter_number,
        schedule_strategy=strategy
    )


# 导出
__all__ = [
    'JobController', 
    'Job',
    'JobStatus', 
    'ScheduleStrategy',
    'create_job_controller',
    'create_and_queue_job'
]
