# test_init.py - M1-1 验收测试
import os
import sys
import sqlite3
import yaml
import json

# 确保可以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_init_creates_required_files():
    """测试初始化创建必需文件"""
    from init_project import run_init, create_dirs, write_world_setting, init_db, create_sample_character
    
    # 清理可能存在的旧文件
    test_files = [
        "config/world_setting.yaml",
        "data/godcraft.db",
        "data/characters/sample_char.yaml"
    ]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)
    
    # 执行初始化
    result = run_init(
        logline="失忆猎人在黑雾城寻找身份",
        genre="黑暗奇幻",
        title="黑雾猎人",
        core_hook="我是谁？"
    )
    
    # 验证返回结构
    assert result["status"] == "success", f"初始化失败: {result}"
    assert "project_id" in result, "缺少 project_id"
    assert "created_files" in result, "缺少 created_files"
    
    # 验证文件存在
    for f in result["created_files"]:
        assert os.path.exists(f), f"文件不存在: {f}"
    
    print("[PASS] 文件创建测试通过")
    return result

def test_world_setting_yaml():
    """测试 world_setting.yaml 内容"""
    with open("config/world_setting.yaml", "r", encoding="utf8") as f:
        world = yaml.safe_load(f)
    
    assert "project_id" in world, "缺少 project_id"
    assert "title" in world, "缺少 title"
    assert "global_anchors" in world, "缺少 global_anchors"
    assert "logline" in world["global_anchors"], "缺少 logline"
    
    print("[PASS] world_setting.yaml 内容验证通过")

def test_database_tables():
    """测试数据库表创建"""
    conn = sqlite3.connect("data/godcraft.db")
    c = conn.cursor()
    
    # 检查必需的表
    required_tables = [
        "novel_projects",
        "writing_jobs", 
        "events_log",
        "character_relationships",
        "world_graph_edges",
        "foreshadowing_ledger",
        "audit_log"
    ]
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in c.fetchall()]
    
    for table in required_tables:
        assert table in existing_tables, f"表不存在: {table}"
    
    conn.close()
    print("[PASS] 数据库表结构验证通过")

def test_sample_character_yaml():
    """测试示例角色 YAML"""
    with open("data/characters/sample_char.yaml", "r", encoding="utf8") as f:
        char = yaml.safe_load(f)
    
    assert "character_id" in char, "缺少 character_id"
    assert "static_profile" in char, "缺少 static_profile"
    assert "dynamic_state" in char, "缺少 dynamic_state"
    
    print("[PASS] sample_char.yaml 验证通过")

def test_json_output():
    """测试 JSON 输出格式"""
    from init_project import run_init
    import io
    from contextlib import redirect_stdout
    
    # 捕获 stdout
    f = io.StringIO()
    with redirect_stdout(f):
        run_init(logline="测试输出", title="测试项目")
    
    output = f.getvalue()
    result = json.loads(output)
    
    assert result["status"] == "success"
    assert "project_id" in result
    
    print("[PASS] JSON 输出格式验证通过")

if __name__ == "__main__":
    print("=" * 50)
    print("M1-1 验收测试开始")
    print("=" * 50)
    
    try:
        test_init_creates_required_files()
        test_world_setting_yaml()
        test_database_tables()
        test_sample_character_yaml()
        test_json_output()
        
        print("=" * 50)
        print("[PASS] 所有测试通过！M1-1 验收完成")
        print("=" * 50)
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
