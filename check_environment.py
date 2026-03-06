import os
import sys
import sqlite3

def check():
    print("--- 神工系统 V3.1 环境健康检查 ---")
    files = [
        "orchestrator.py", "writer_agent.py", "critic_agent.py", 
        "character_manager.py", "database.sqlite", "config/world_setting.yaml"
    ]
    for f in files:
        if os.path.exists(f):
            print(f"[OK] 核心文件: {f}")
        else:
            print(f"[ERR] 缺失文件: {f}")
            return False

    try:
        conn = sqlite3.connect("database.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        required_tables = ['events_log', 'world_graph_edges', 'character_relationships', 'foreshadowing_ledger']
        for rt in required_tables:
            if rt in tables:
                print(f"[OK] 数据库表: {rt}")
            else:
                print(f"[ERR] 缺失数据库表: {rt}")
                return False
    except Exception as e:
        print(f"[ERR] 数据库访问异常: {e}")
        return False
    
    print("--- 结论：系统已具备独立运行条件 ---")
    return True

if __name__ == "__main__":
    if not check():
        sys.exit(1)
