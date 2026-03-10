# test_world_setting.py - M1-2 验收测试
import os
import sys
import yaml
import json

# 确保可以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = "config/world_setting.yaml"

def test_world_setting_exists():
    """测试 world_setting.yaml 存在"""
    assert os.path.exists(CONFIG_PATH), f"配置文件不存在: {CONFIG_PATH}"
    print("[PASS] 配置文件存在")

def test_world_setting_required_fields():
    """测试必需字段"""
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        world = yaml.safe_load(f)
    
    # 必需顶层字段
    required_top = ["project_id", "title", "genre"]
    for field in required_top:
        assert field in world, f"缺少必需字段: {field}"
    
    # global_anchors 内部字段
    assert "global_anchors" in world, "缺少 global_anchors"
    anchors = world["global_anchors"]
    required_anchors = ["logline", "core_hook"]
    for field in required_anchors:
        assert field in anchors, f"global_anchors 缺少: {field}"
    
    # absolute_rules
    assert "absolute_rules" in world, "缺少 absolute_rules"
    rules = world["absolute_rules"]
    assert "do_not_include" in rules, "absolute_rules 缺少 do_not_include"
    
    print("[PASS] 必需字段验证通过")

def test_world_setting_extended_fields():
    """测试扩展字段（M1-2 新增）"""
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        world = yaml.safe_load(f)
    
    # chapters 配置
    assert "chapters" in world, "缺少 chapters 配置"
    assert "target_count" in world["chapters"], "chapters 缺少 target_count"
    assert "interval_minutes" in world["chapters"], "chapters 缺少 interval_minutes"
    
    # world 世界设定
    assert "world" in world, "缺少 world 世界设定"
    
    # characters 角色配置
    assert "characters" in world, "缺少 characters 角色配置"
    
    # narrative 叙事配置
    assert "narrative" in world, "缺少 narrative 叙事配置"
    
    # quality 质量控制
    assert "quality" in world, "缺少 quality 质量控制"
    
    print("[PASS] 扩展字段验证通过")

def test_world_setting_value_ranges():
    """测试值范围"""
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        world = yaml.safe_load(f)
    
    # 章节数应为正整数
    target = world.get("chapters", {}).get("target_count", 0)
    assert isinstance(target, int) and target > 0, f"target_count 应为正整数: {target}"
    
    # interval 应为正整数
    interval = world.get("chapters", {}).get("interval_minutes", 0)
    assert isinstance(interval, int) and interval > 0, f"interval_minutes 应为正整数: {interval}"
    
    print("[PASS] 值范围验证通过")

def test_world_setting_yaml_valid():
    """测试 YAML 格式有效性"""
    with open(CONFIG_PATH, "r", encoding="utf8") as f:
        content = f.read()
    
    # 尝试解析
    world = yaml.safe_load(content)
    assert world is not None, "YAML 解析失败"
    assert isinstance(world, dict), "YAML 应解析为字典"
    
    print("[PASS] YAML 格式有效")

if __name__ == "__main__":
    print("=" * 50)
    print("M1-2 验收测试开始")
    print("=" * 50)
    
    try:
        test_world_setting_exists()
        test_world_setting_required_fields()
        test_world_setting_extended_fields()
        test_world_setting_value_ranges()
        test_world_setting_yaml_valid()
        
        print("=" * 50)
        print("[PASS] 所有测试通过！M1-2 验收完成")
        print("=" * 50)
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
