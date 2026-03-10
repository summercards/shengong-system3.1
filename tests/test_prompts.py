# test_prompts.py - M3-2 Prompts 定义测试
import os
import sys
import json

# 添加项目根目录到路径
PROJECT_ROOT = r"I:\项目\shengong-system\godcraft_v4"
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def test_prompts_exist():
    """测试 prompts 文件存在"""
    print("\n[TEST] Prompts 文件存在")
    
    required_prompts = [
        "prompts/planner_prompt.txt",
        "prompts/writer_prompt.txt",
        "prompts/critic_prompt.txt"
    ]
    
    for prompt_file in required_prompts:
        assert os.path.exists(prompt_file), f"Missing {prompt_file}"
        print(f"  [OK] {prompt_file} exists")
    
    print("[PASS] Prompts 文件存在")


def test_prompts_not_empty():
    """测试 prompts 文件不为空"""
    print("\n[TEST] Prompts 内容非空")
    
    prompts = {
        "planner": "prompts/planner_prompt.txt",
        "writer": "prompts/writer_prompt.txt",
        "critic": "prompts/critic_prompt.txt"
    }
    
    for name, path in prompts.items():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert len(content) > 100, f"{name} prompt too short"
        print(f"  [OK] {name}: {len(content)} chars")
    
    print("[PASS] Prompts 内容非空")


def test_prompts_structure():
    """测试 prompts 内容结构"""
    print("\n[TEST] Prompts 内容结构")
    
    # Planner 应该包含大纲、beat_tags、key_events
    with open("prompts/planner_prompt.txt", 'r', encoding='utf-8') as f:
        planner = f.read()
    
    assert "outline" in planner, "Planner missing outline"
    assert "beat_tags" in planner, "Planner missing beat_tags"
    assert "key_events" in planner, "Planner missing key_events"
    assert "JSON" in planner, "Planner should contain JSON format"
    print("  [OK] Planner: contains outline, beat_tags, key_events")
    
    # Writer 应该包含章节正文、结构化数据
    with open("prompts/writer_prompt.txt", 'r', encoding='utf-8') as f:
        writer = f.read()
    
    assert "正文" in writer or "内容" in writer, "Writer missing content"
    assert "events" in writer, "Writer missing events"
    assert "character_updates" in writer, "Writer missing character_updates"
    assert "JSON" in writer, "Writer should contain JSON format"
    print("  [OK] Writer: contains content, events, character_updates")
    
    # Critic 应该包含评估维度、评分
    with open("prompts/critic_prompt.txt", 'r', encoding='utf-8') as f:
        critic = f.read()
    
    assert "评分" in critic or "score" in critic.lower(), "Critic missing score"
    assert "needs_revision" in critic, "Critic missing needs_revision"
    assert "feedback" in critic, "Critic missing feedback"
    assert "JSON" in critic, "Critic should contain JSON format"
    print("  [OK] Critic: contains score, feedback, review results")
    
    print("[PASS] Prompts 内容结构")


def test_orchestrator_loads_prompts():
    """测试 Orchestrator 正确加载 prompts"""
    print("\n[TEST] Orchestrator 加载 Prompts")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator("test_prompts_load")
    
    # 测试 planner 加载
    assert hasattr(orch, 'planner')
    assert 'system_prompt' in orch.planner
    assert len(orch.planner['system_prompt']) > 100
    print(f"  [OK] Planner prompt: {len(orch.planner['system_prompt'])} chars")
    
    # 测试 writer 加载
    assert hasattr(orch, 'writer')
    assert 'system_prompt' in orch.writer
    assert len(orch.writer['system_prompt']) > 100
    print(f"  [OK] Writer prompt: {len(orch.writer['system_prompt'])} chars")
    
    # 测试 critic 加载
    assert hasattr(orch, 'critic')
    assert 'system_prompt' in orch.critic
    assert len(orch.critic['system_prompt']) > 100
    print(f"  [OK] Critic prompt: {len(orch.critic['system_prompt'])} chars")
    
    print("[PASS] Orchestrator 加载 Prompts")


def test_prompts_guide_agents():
    """测试 Prompts 指导 Agent 行为"""
    print("\n[TEST] Prompts 指导 Agent 行为")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator("test_guide")
    
    # Planner prompt 应该指导输出 JSON 格式
    planner_prompt = orch.planner['system_prompt']
    assert "JSON" in planner_prompt or "json" in planner_prompt
    assert "outline" in planner_prompt
    print("  [OK] Planner: guides JSON outline output")
    
    # Writer prompt 应该指导输出正文 + JSON
    writer_prompt = orch.writer['system_prompt']
    assert "JSON" in writer_prompt or "json" in writer_prompt
    assert "events" in writer_prompt
    print("  [OK] Writer: guides content + structured data output")
    
    # Critic prompt 应该指导评分和反馈
    critic_prompt = orch.critic['system_prompt']
    assert "score" in critic_prompt.lower()
    assert "feedback" in critic_prompt
    print("  [OK] Critic: guides score and feedback output")
    
    print("[PASS] Prompts 指导 Agent 行为")


def test_prompts_complete():
    """测试 Prompts 完整性"""
    print("\n[TEST] Prompts 完整性检查")
    
    from orchestrator import Orchestrator
    
    orch = Orchestrator("test_complete")
    
    # 检查所有必需元素
    planner = orch.planner['system_prompt']
    writer = orch.writer['system_prompt']
    critic = orch.critic['system_prompt']
    
    # Planner 必需元素
    planner_required = ["outline", "beat_tags", "key_events", "characters_in_scene"]
    missing_planner = [e for e in planner_required if e not in planner]
    assert not missing_planner, f"Planner missing: {missing_planner}"
    print("  [OK] Planner contains all required elements")
    
    # Writer 必需元素
    writer_required = ["events", "character_updates", "world_updates"]
    missing_writer = [e for e in writer_required if e not in writer]
    assert not missing_writer, f"Writer missing: {missing_writer}"
    print("  [OK] Writer contains all required elements")
    
    # Critic 必需元素
    critic_required = ["score", "needs_revision", "feedback", "dimension_scores"]
    missing_critic = [e for e in critic_required if e not in critic]
    assert not missing_critic, f"Critic missing: {missing_critic}"
    print("  [OK] Critic contains all required elements")
    
    print("[PASS] Prompts 完整性检查")


if __name__ == "__main__":
    print("="*50)
    print("M3-2 Prompts Definition Test Suite")
    print("="*50)
    
    # 运行测试
    test_prompts_exist()
    test_prompts_not_empty()
    test_prompts_structure()
    test_orchestrator_loads_prompts()
    test_prompts_guide_agents()
    test_prompts_complete()
    
    print("\n" + "="*50)
    print("All tests passed!")
    print("="*50)
