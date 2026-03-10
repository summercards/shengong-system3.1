# init_project.py - M1-1 项目初始化
import os
import yaml
import sqlite3
import json
import sys

DEFAULT_SCHEMA = """
CREATE TABLE IF NOT EXISTS novel_projects (
    project_id TEXT PRIMARY KEY,
    title TEXT,
    genre TEXT,
    logline TEXT,
    target_chapters INTEGER DEFAULT 0,
    current_chapter INTEGER DEFAULT 0,
    interval_minutes INTEGER DEFAULT 60,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS writing_jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    chapter_number INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES novel_projects(project_id)
);

CREATE TABLE IF NOT EXISTS events_log (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    chapter_number INTEGER,
    event_type TEXT,
    summary TEXT,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS character_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    char_id_1 TEXT,
    char_id_2 TEXT,
    relationship_type TEXT,
    strength INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    source_node TEXT,
    target_node TEXT,
    edge_type TEXT,
    weight REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS foreshadowing_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    chapter_introduced INTEGER,
    chapter_revealed INTEGER,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    parsed_intent TEXT,
    params TEXT,
    result TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def create_dirs():
    """创建项目目录结构"""
    dirs = [
        "config",
        "data/characters",
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs

def write_world_setting(world):
    """写入 world_setting.yaml"""
    with open("config/world_setting.yaml", "w", encoding="utf8") as f:
        yaml.safe_dump(world, f, allow_unicode=True, default_flow_style=False)

def init_db(db_path="data/godcraft.db"):
    """初始化 SQLite 数据库"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript(DEFAULT_SCHEMA)
    conn.commit()
    conn.close()
    return db_path

def create_sample_character():
    """创建示例角色 YAML"""
    sample = {
        "character_id": "char_main_01",
        "name": "主角",
        "static_profile": {
            "age": None,
            "appearance": "",
            "background": ""
        },
        "dynamic_state": {
            "location": "",
            "mood": "",
            "goals": []
        }
    }
    with open("data/characters/sample_char.yaml", "w", encoding="utf8") as f:
        yaml.safe_dump(sample, f, allow_unicode=True, default_flow_style=False)
    return "data/characters/sample_char.yaml"

def run_init(logline, genre="奇幻", title="未命名项目", core_hook=""):
    """
    初始化项目主函数
    
    Args:
        logline: 项目一句话简介
        genre: 题材类型
        title: 项目标题
        core_hook: 核心钩子/悬念
    
    Returns:
        dict: 包含 status, project_id, created_files
    """
    project_id = f"novel_{int(os.times().elapsed * 1000)}"
    
    # 创建目录
    created_dirs = create_dirs()
    
    # 生成 world_setting
    world = {
        "project_id": project_id,
        "title": title,
        "genre": genre,
        "global_anchors": {
            "logline": logline,
            "core_hook": core_hook
        },
        "absolute_rules": {
            "do_not_include": []
        }
    }
    write_world_setting(world)
    
    # 初始化数据库
    db_path = init_db()
    
    # 创建示例角色
    char_file = create_sample_character()
    
    created_files = [
        "config/world_setting.yaml",
        db_path,
        char_file
    ]
    
    result = {
        "status": "success",
        "project_id": project_id,
        "title": title,
        "genre": genre,
        "logline": logline,
        "created_files": created_files,
        "created_dirs": created_dirs
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    # 支持 CLI 参数
    import argparse
    parser = argparse.ArgumentParser(description="初始化小说项目")
    parser.add_argument("--title", "-t", default="未命名项目", help="项目标题")
    parser.add_argument("--logline", "-l", default="", help="项目一句话简介")
    parser.add_argument("--genre", "-g", default="奇幻", help="题材类型")
    parser.add_argument("--core-hook", "-c", default="", help="核心钩子/悬念")
    
    args = parser.parse_args()
    
    if not args.logline:
        print("错误: 需要提供 --logline 参数")
        sys.exit(1)
    
    run_init(
        logline=args.logline,
        genre=args.genre,
        title=args.title,
        core_hook=args.core_hook
    )
