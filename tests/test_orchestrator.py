# test_orchestrator.py - M3-1 Orchestrator 测试
import os
import sys
import json
import tempfile
import shutil

# 添加项目根目录到路径
PROJECT_ROOT = r"I:\项目\shengong-system\godcraft_v4"
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 测试配置
TEST_PROJECT_ID = "test_orch_project"
TEST_DB_PATH = "data/godcraft.db"


def setup_test_env():
    """设置测试环境"""
    # 确保必要的目录存在
    os.makedirs("data/characters", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)
    
    # 创建测试配置文件
    test_config = {
        "project": {
            "title": "测试小说",
            "genre": "fantasy",
            "logline": "测试故事线"
        },
        "chapters": {
            "target_length": 1200,
            "target_count": 10,
            "interval_minutes": 60
        }
    }
    
    with open("config/world_setting.yaml", 'w', encoding='utf-8') as f:
        import yaml
        yaml.dump(test_config, f, allow_unicode=True)
    
    # 创建简单的测试 Prompts
    with open("prompts/planner_prompt.txt", 'w', encoding='utf-8') as f:
        f.write("你是规划 Agent。输出 JSON 格式的大纲。")
    
    with open("prompts/writer_prompt.txt", 'w', encoding='utf-8') as f:
        f.write("你是写作 Agent。输出章节内容和 JSON 格式的结构化数据。")
    
    with open("prompts/critic_prompt.txt", 'w', encoding='utf-8') as f:
        f.write("你是审查 Agent。输出 JSON 格式的审查结果。")


def test_orchestrator_init():
    """测试 Orchestrator 初始化"""
    print("\n[TEST] Orchestrator 初始化")
    
    setup_test_env()
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    assert orch.project_id == TEST_PROJECT_ID
    assert orch.config is not None
    assert orch.store is not None
    
    print("[PASS] Orchestrator 初始化")


def test_orchestrator_properties():
    """测试 Agent 属性访问"""
    print("\n[TEST] Agent 属性访问")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 检查属性是否存在（延迟初始化）
    assert hasattr(orch, 'planner')
    assert hasattr(orch, 'writer')
    assert hasattr(orch, 'critic')
    assert hasattr(orch, 'lorekeeper')
    
    print("[PASS] Agent 属性访问")


def test_start_project():
    """测试项目启动"""
    print("\n[TEST] 启动项目")
    
    from orchestrator import Orchestrator
    from database import get_project
    
    # 创建新 Orchestrator
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 启动项目
    result = orch.start_project(
        title="测试小说",
        genre="fantasy",
        logline="这是一个测试故事",
        target_chapters=10
    )
    
    assert result["status"] == "success", f"启动失败: {result}"
    
    # 验证项目创建
    project = get_project(TEST_PROJECT_ID)
    assert project is not None
    assert project["title"] == "测试小说"
    assert project["genre"] == "fantasy"
    assert project["status"] == "running"
    
    print("[PASS] 启动项目")


def test_get_next_chapter():
    """测试获取下一章编号"""
    print("\n[TEST] 获取下一章编号")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 新项目应该是第 1 章
    next_ch = orch.get_next_chapter()
    assert next_ch == 1, f"期望 1, 实际 {next_ch}"
    
    print("[PASS] 获取下一章编号")


def test_plan_chapter():
    """测试章节规划"""
    print("\n[TEST] 章节规划")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 规划第 1 章
    result = orch.plan_chapter(1, "这是一个测试大纲")
    
    # 由于没有真实的 LLM 响应，这里只检查返回结构
    # 实际调用会失败，但应该返回错误而不是崩溃
    assert "status" in result
    assert "chapter_num" in result
    
    print(f"  规划结果: {result.get('status')}")
    print("[PASS] 章节规划")


def test_write_chapter():
    """测试章节写作"""
    print("\n[TEST] 章节写作")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 写作第 1 章
    result = orch.write_chapter(1, "测试大纲", 500)
    
    # 检查返回结构
    assert "status" in result
    assert "chapter_num" in result
    
    print(f"  写作结果: {result.get('status')}")
    print("[PASS] 章节写作")


def test_review_chapter():
    """测试章节审查"""
    print("\n[TEST] 章节审查")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 审查测试文本
    test_text = "这是一个测试章节的内容。" * 50
    result = orch.review_chapter(test_text)
    
    # 检查返回结构
    assert "score" in result
    assert "feedback" in result
    
    print(f"  审查得分: {result.get('score')}")
    print("[PASS] 章节审查")


def test_sync_lore():
    """测试世界观同步"""
    print("\n[TEST] 世界观同步")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 同步测试数据
    test_data = {
        "character_updates": {
            "char_test": {
                "dynamic_state.mood": "happy"
            }
        }
    }
    
    result = orch.sync_lore(test_data)
    
    assert "status" in result
    print(f"  同步状态: {result.get('status')}")
    print("[PASS] 世界观同步")


def test_story_cycle_structure():
    """测试 StoryCycle 结构"""
    print("\n[TEST] StoryCycle 流程结构")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 检查 story_cycle 方法存在
    assert hasattr(orch, 'story_cycle')
    assert callable(orch.story_cycle)
    
    # 检查关键方法
    assert hasattr(orch, 'plan_chapter')
    assert hasattr(orch, 'write_chapter')
    assert hasattr(orch, 'review_chapter')
    assert hasattr(orch, 'sync_lore')
    
    print("[PASS] StoryCycle 流程结构")


def test_orchestrator_save_output():
    """测试输出保存"""
    print("\n[TEST] 输出保存")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator(TEST_PROJECT_ID)
    
    # 测试保存功能
    test_text = "测试章节内容"
    test_results = {
        "stages": {
            "planning": {"status": "success"},
            "writing": {"status": "success"},
            "review": {"score": 0.8}
        }
    }
    
    # 不实际保存，只检查方法存在
    assert hasattr(orch, '_save_chapter_output')
    
    print("[PASS] 输出保存")


def test_convenience_functions():
    """测试便捷函数"""
    print("\n[TEST] 便捷函数")
    
    from orchestrator import create_orchestrator, run_story_cycle
    
    # 测试创建函数
    orch = create_orchestrator("test_conv")
    assert orch is not None
    assert orch.project_id == "test_conv"
    
    # 测试 run_story_cycle 函数存在
    assert callable(run_story_cycle)
    
    print("[PASS] 便捷函数")


def cleanup_test_data():
    """清理测试数据"""
    # 清理测试输出
    if os.path.exists("output"):
        for f in os.listdir("output"):
            if f.startswith("chapter_"):
                try:
                    os.remove(f"output/{f}")
                except:
                    pass


if __name__ == "__main__":
    print("="*50)
    print("Orchestrator 测试套件")
    print("="*50)
    
    # 运行测试
    test_orchestrator_init()
    test_orchestrator_properties()
    test_start_project()
    test_get_next_chapter()
    test_plan_chapter()
    test_write_chapter()
    test_review_chapter()
    test_sync_lore()
    test_story_cycle_structure()
    test_orchestrator_save_output()
    test_convenience_functions()
    
    # 清理
    cleanup_test_data()
    
    print("\n" + "="*50)
    print("所有测试完成!")
    print("="*50)
