# api.py - M5-1 Minimal API
"""
Minimal API for GodCraft
提供 RESTful API 接口，支持外部系统集成

端点：
- GET  /health          - 健康检查
- GET  /projects        - 项目列表
- POST /projects        - 创建项目
- GET  /projects/{id}   - 项目详情
- POST /projects/{id}/write - 触发章节写作
- GET  /jobs            - 任务列表
- GET  /jobs/{id}       - 任务详情
- GET  /chapters/{id}   - 章节内容
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入项目模块
from database import (
    get_connection, execute_query, execute_write,
    create_project as db_create_project,
    get_project as db_get_project,
    get_all_projects,
    create_job as db_create_job,
    get_job as db_get_job,
    get_project_jobs,
    update_job_status,
    log_event as db_log_event
)
from orchestrator import Orchestrator
from job_controller import JobController, JobStatus
from structured_store import StructuredStore
from export_import import ExportImportManager, Monitor, export_project, import_project


# === FastAPI 应用 ===
app = FastAPI(
    title="神工系统 API",
    description="GodCraft - AI 小说创作系统 REST API",
    version="1.0.0"
)


# === 数据模型 ===

class ProjectCreate(BaseModel):
    """创建项目请求"""
    project_id: str = Field(..., description="项目 ID")
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="类型")
    logline: str = Field(default="", description="一句话简介")
    target_chapters: int = Field(default=50, description="目标章节数")
    interval_minutes: int = Field(default=60, description="写作间隔（分钟）")


class ChapterWriteRequest(BaseModel):
    """章节写作请求"""
    chapter_number: int = Field(..., description="章节号")
    target_length: int = Field(default=1200, description="目标字数")
    enable_review: bool = Field(default=True, description="启用审查")


class ProjectResponse(BaseModel):
    """项目响应"""
    project_id: str
    title: str
    genre: str
    status: str
    current_chapter: int
    target_chapters: int
    logline: str
    created_at: str


class JobResponse(BaseModel):
    """任务响应"""
    job_id: str
    project_id: str
    job_type: str
    chapter_number: int
    status: str
    schedule_strategy: str
    created_at: str
    completed_at: Optional[str] = None


class ChapterResponse(BaseModel):
    """章节响应"""
    number: str
    content: str
    meta: Optional[Dict[str, Any]] = None


# === 工具函数 ===

def get_db_path() -> str:
    """获取数据库路径"""
    return os.path.join(PROJECT_ROOT, "data", "godcraft.db")


def get_output_dir() -> str:
    """获取输出目录"""
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# === API 端点 ===

@app.get("/")
def root():
    """根路径"""
    return {
        "name": "神工系统 API",
        "version": "1.0.0",
        "description": "GodCraft - AI 小说创作系统"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    # 检查数据库
    try:
        conn = get_connection()
        conn.close()
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    # 检查配置
    config_exists = os.path.exists(os.path.join(PROJECT_ROOT, "config", "world_setting.yaml"))
    
    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status,
        "config": "ok" if config_exists else "missing",
        "timestamp": datetime.now().isoformat()
    }


# === 项目接口 ===

@app.get("/projects", response_model=List[ProjectResponse])
def list_projects():
    """获取项目列表"""
    try:
        projects = get_all_projects()
        return [
            ProjectResponse(
                project_id=p["project_id"],
                title=p["title"],
                genre=p["genre"],
                status=p["status"],
                current_chapter=p.get("current_chapter", 0),
                target_chapters=p.get("target_chapters", 0),
                logline=p.get("logline", ""),
                created_at=p.get("created_at", "")
            )
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    """创建项目"""
    try:
        # 检查是否已存在
        existing = db_get_project(project.project_id)
        if existing:
            raise HTTPException(status_code=400, detail="项目已存在")
        
        # 创建项目
        db_create_project(
            project_id=project.project_id,
            title=project.title,
            genre=project.genre,
            logline=project.logline,
            target_chapters=project.target_chapters,
            interval_minutes=project.interval_minutes
        )
        
        log_event(project.project_id, "project_created", "Project created via API")
        
        # 返回创建的项目
        created = db_get_project(project.project_id)
        return ProjectResponse(
            project_id=created["project_id"],
            title=created["title"],
            genre=created["genre"],
            status=created["status"],
            current_chapter=created.get("current_chapter", 0),
            target_chapters=created.get("target_chapters", 0),
            logline=created.get("logline", ""),
            created_at=created.get("created_at", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    """获取项目详情"""
    project = db_get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return ProjectResponse(
        project_id=project["project_id"],
        title=project["title"],
        genre=project["genre"],
        status=project["status"],
        current_chapter=project.get("current_chapter", 0),
        target_chapters=project.get("target_chapters", 0),
        logline=project.get("logline", ""),
        created_at=project.get("created_at", "")
    )


@app.post("/projects/{project_id}/write")
def write_chapter(project_id: str, request: ChapterWriteRequest):
    """触发章节写作"""
    # 检查项目是否存在
    project = db_get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        # 创建写作任务
        job_id = db_create_job(
            project_id=project_id,
            job_type="chapter_write",
            chapter_number=request.chapter_number,
            status="pending",
            schedule_strategy="immediate"
        )
        
        log_event(project_id, "chapter_write_started", f"Chapter {request.chapter_number} write started via API")
        
        # 初始化 Orchestrator 并运行
        orchestrator = Orchestrator(project_id=project_id)
        
        # 运行故事循环（同步执行）
        result = orchestrator.story_cycle(
            chapter_number=request.chapter_number,
            target_length=request.target_length,
            enable_review=request.enable_review
        )
        
        # 更新任务状态
        if result.get("success"):
            update_job_status(job_id, "completed")
            return {
                "success": True,
                "job_id": job_id,
                "chapter": request.chapter_number,
                "message": "章节写作完成",
                "content_preview": result.get("content", "")[:500]
            }
        else:
            update_job_status(job_id, "failed")
            return {
                "success": False,
                "job_id": job_id,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 任务接口 ===

@app.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    project_id: str = Query(None, description="项目 ID 筛选"),
    status: str = Query(None, description="状态筛选"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制")
):
    """获取任务列表"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM writing_jobs"
        conditions = []
        params = []
        
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        conn.close()
        
        return [
            JobResponse(
                job_id=j["job_id"],
                project_id=j["project_id"],
                job_type=j["job_type"],
                chapter_number=j.get("chapter_number", 0),
                status=j["status"],
                schedule_strategy=j.get("schedule_strategy", ""),
                created_at=j.get("created_at", ""),
                completed_at=j.get("completed_at")
            )
            for j in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    """获取任务详情"""
    job = db_get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return JobResponse(
        job_id=job["job_id"],
        project_id=job["project_id"],
        job_type=job["job_type"],
        chapter_number=job.get("chapter_number", 0),
        status=job["status"],
        schedule_strategy=job.get("schedule_strategy", ""),
        created_at=job.get("created_at", ""),
        completed_at=job.get("completed_at")
    )


# === 章节接口 ===

@app.get("/chapters/{chapter_num}")
def get_chapter(chapter_num: str, project_id: str = Query("default", description="项目 ID")):
    """获取章节内容"""
    output_dir = get_output_dir()
    
    # 查找章节文件
    chapter_file = f"chapter_{chapter_num}.md"
    chapter_path = os.path.join(output_dir, chapter_file)
    
    if not os.path.exists(chapter_path):
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 读取内容
    with open(chapter_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 读取元数据
    meta_path = os.path.join(output_dir, f"chapter_{chapter_num}_meta.json")
    meta = None
    if os.path.exists(meta_path):
        import json
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    return ChapterResponse(
        number=chapter_num,
        content=content,
        meta=meta
    )


@app.get("/chapters")
def list_chapters(project_id: str = Query("default", description="项目 ID")):
    """获取章节列表"""
    output_dir = get_output_dir()
    
    chapters = []
    for f in os.listdir(output_dir):
        if f.startswith("chapter_") and f.endswith(".md"):
            chapter_num = f.replace("chapter_", "").replace(".md", "")
            
            meta_path = os.path.join(output_dir, f"chapter_{chapter_num}_meta.json")
            meta = None
            if os.path.exists(meta_path):
                import json
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            
            chapters.append({
                "number": chapter_num,
                "has_meta": meta is not None,
                "meta": meta
            })
    
    # 排序
    chapters = sorted(chapters, key=lambda x: x["number"])
    
    return {
        "project_id": project_id,
        "total": len(chapters),
        "chapters": chapters
    }


# === 统计接口 ===

@app.get("/stats")
def get_stats():
    """获取系统统计"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 项目统计
        cursor.execute("SELECT COUNT(*) FROM novel_projects")
        project_count = cursor.fetchone()[0]
        
        # 任务统计
        cursor.execute("SELECT status, COUNT(*) FROM writing_jobs GROUP BY status")
        job_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 章节统计
        output_dir = get_output_dir()
        chapter_count = len([f for f in os.listdir(output_dir) if f.startswith("chapter_") and f.endswith(".md")])
        
        conn.close()
        
        return {
            "projects": project_count,
            "chapters": chapter_count,
            "jobs": job_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 导入导出接口 ===

@app.get("/export/{project_id}")
def export_project_api(
    project_id: str,
    format: str = Query("json", description="导出格式: json 或 sql"),
    include_chapters: bool = Query(True, description="是否包含章节内容")
):
    """导出项目"""
    try:
        manager = ExportImportManager()
        
        if format == "json":
            data = manager.export_project_json(project_id, include_chapters)
            return {
                "format": "json",
                "data": data
            }
        elif format == "sql":
            sql = manager.export_project_sql(project_id)
            return {
                "format": "sql",
                "data": sql
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/import")
def import_project_api(request: dict):
    """导入项目"""
    try:
        manager = ExportImportManager()
        
        project_id = manager.import_project_json(request)
        
        return {
            "success": True,
            "project_id": project_id,
            "message": "项目导入成功"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 监控接口 ===

@app.get("/monitor/health/{project_id}")
def monitor_project_health(project_id: str):
    """获取项目健康状态"""
    try:
        monitor = Monitor()
        return monitor.get_project_health(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/system")
def monitor_system():
    """获取系统统计"""
    try:
        monitor = Monitor()
        return monitor.get_system_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/job/{job_id}")
def monitor_job_progress(job_id: int):
    """获取任务进度"""
    try:
        monitor = Monitor()
        result = monitor.get_job_progress(job_id)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitor/activities")
def monitor_activities(limit: int = Query(20, ge=1, le=100, description="返回数量限制")):
    """获取最近活动"""
    try:
        monitor = Monitor()
        return {
            "activities": monitor.get_recent_activities(limit)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 运行 ===

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """运行 API 服务器"""
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server()
