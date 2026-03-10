# database.py - M2-1 数据库结构设计
import sqlite3
import json
from typing import Any, Optional

DB_PATH = "data/godcraft.db"

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query: str, params: tuple = ()) -> list:
    """执行查询并返回结果"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def execute_write(query: str, params: tuple = ()) -> int:
    """执行写操作并返回影响的行数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id

# === novel_projects 表操作 ===

def create_project(project_id: str, title: str, genre: str, logline: str = "", 
                   target_chapters: int = 0, interval_minutes: int = 60) -> int:
    """创建新项目"""
    query = """
        INSERT INTO novel_projects 
        (project_id, title, genre, logline, target_chapters, interval_minutes, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """
    return execute_write(query, (project_id, title, genre, logline, target_chapters, interval_minutes))

def get_project(project_id: str) -> Optional[dict]:
    """获取项目信息"""
    results = execute_query(
        "SELECT * FROM novel_projects WHERE project_id = ?", 
        (project_id,)
    )
    return results[0] if results else None

def get_all_projects() -> list:
    """获取所有项目"""
    return execute_query("SELECT * FROM novel_projects ORDER BY created_at DESC")

def update_project_status(project_id: str, status: str) -> int:
    """更新项目状态"""
    query = """
        UPDATE novel_projects 
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE project_id = ?
    """
    return execute_write(query, (status, project_id))

def increment_chapter(project_id: str) -> int:
    """章节数+1"""
    query = """
        UPDATE novel_projects 
        SET current_chapter = current_chapter + 1, updated_at = CURRENT_TIMESTAMP 
        WHERE project_id = ?
    """
    return execute_write(query, (project_id,))

# === writing_jobs 表操作 ===

def create_job(project_id: str, chapter_number: int, job_type: str = "chapter_write", 
               status: str = "pending", schedule_strategy: str = "immediate") -> int:
    """创建写作任务"""
    query = """
        INSERT INTO writing_jobs (project_id, job_type, chapter_number, status, schedule_strategy, content, word_count)
        VALUES (?, ?, ?, ?, ?, '', 0)
    """
    return execute_write(query, (project_id, job_type, chapter_number, status, schedule_strategy))

def get_project_jobs(project_id: str) -> list:
    """获取项目的所有任务"""
    return execute_query(
        "SELECT * FROM writing_jobs WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    )

def get_job(job_id: int) -> Optional[dict]:
    """获取任务信息"""
    results = execute_query(
        "SELECT * FROM writing_jobs WHERE job_id = ?", 
        (job_id,)
    )
    return results[0] if results else None

def update_job_status(job_id: int, status: str) -> int:
    """更新任务状态"""
    import datetime
    now = datetime.datetime.now().isoformat()
    if status == "running":
        query = "UPDATE writing_jobs SET status = ?, started_at = ? WHERE job_id = ?"
        return execute_write(query, (status, now, job_id))
    elif status == "completed":
        query = "UPDATE writing_jobs SET status = ?, completed_at = ? WHERE job_id = ?"
        return execute_write(query, (status, now, job_id))
    else:
        query = "UPDATE writing_jobs SET status = ? WHERE job_id = ?"
        return execute_write(query, (status, job_id))

# === events_log 表操作 ===

def log_event(project_id: str, chapter_number: int, event_type: str, 
              summary: str, data: dict = None) -> int:
    """记录事件"""
    query = """
        INSERT INTO events_log (project_id, chapter_number, event_type, summary, data)
        VALUES (?, ?, ?, ?, ?)
    """
    data_json = json.dumps(data, ensure_ascii=False) if data else None
    return execute_write(query, (project_id, chapter_number, event_type, summary, data_json))

def get_project_events(project_id: str) -> list:
    """获取项目所有事件"""
    return execute_query(
        "SELECT * FROM events_log WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,)
    )

# === character_relationships 表操作 ===

def add_character_relationship(project_id: str, char_id_1: str, char_id_2: str,
                                 relationship_type: str, strength: int = 0, notes: str = "") -> int:
    """添加角色关系"""
    query = """
        INSERT INTO character_relationships 
        (project_id, char_id_1, char_id_2, relationship_type, strength, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    return execute_write(query, (project_id, char_id_1, char_id_2, relationship_type, strength, notes))

def get_character_relationships(project_id: str) -> list:
    """获取项目所有角色关系"""
    return execute_query(
        "SELECT * FROM character_relationships WHERE project_id = ?",
        (project_id,)
    )

# === world_graph_edges 表操作 ===

def add_world_edge(project_id: str, source_node: str, target_node: str,
                   edge_type: str, weight: float = 1.0, notes: str = "") -> int:
    """添加世界图谱边"""
    query = """
        INSERT INTO world_graph_edges 
        (project_id, source_node, target_node, edge_type, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    return execute_write(query, (project_id, source_node, target_node, edge_type, weight, notes))

def get_world_edges(project_id: str) -> list:
    """获取项目所有世界图谱边"""
    return execute_query(
        "SELECT * FROM world_graph_edges WHERE project_id = ?",
        (project_id,)
    )

# === foreshadowing_ledger 表操作 ===

def add_foreshadowing(project_id: str, chapter_introduced: int, chapter_revealed: int,
                      description: str) -> int:
    """添加伏笔"""
    query = """
        INSERT INTO foreshadowing_ledger 
        (project_id, chapter_introduced, chapter_revealed, description, status)
        VALUES (?, ?, ?, ?, 'active')
    """
    return execute_write(query, (project_id, chapter_introduced, chapter_revealed, description))

def get_active_foreshadowings(project_id: str) -> list:
    """获取活跃伏笔"""
    return execute_query(
        "SELECT * FROM foreshadowing_ledger WHERE project_id = ? AND status = 'active'",
        (project_id,)
    )

def resolve_foreshadowing(foreshadowing_id: int) -> int:
    """解决伏笔"""
    query = "UPDATE foreshadowing_ledger SET status = 'resolved' WHERE id = ?"
    return execute_write(query, (foreshadowing_id,))

# === audit_log 表操作 ===

def write_audit_log(user_input: str, parsed_intent: str, params: dict, result: str) -> int:
    """写入审计日志"""
    query = """
        INSERT INTO audit_log (user_input, parsed_intent, params, result)
        VALUES (?, ?, ?, ?)
    """
    params_json = json.dumps(params, ensure_ascii=False)
    return execute_write(query, (user_input, parsed_intent, params_json, result))

def get_audit_logs(limit: int = 100) -> list:
    """获取审计日志"""
    return execute_query(
        f"SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT {limit}"
    )

# === 数据库诊断 ===

def get_table_schema(table_name: str) -> list:
    """获取表结构"""
    return execute_query(f"PRAGMA table_info({table_name})")

def get_all_tables() -> list:
    """获取所有表"""
    results = execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [r['name'] for r in results]
