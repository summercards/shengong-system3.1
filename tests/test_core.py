import os
import sys
import sqlite3
import yaml

# 将当前目录（项目根目录）添加到 sys.path
sys.path.append(os.getcwd())

from character_manager import CharacterManager
from event_manager import EventManager

def test_character_update(char_manager):
    """验证角色状态更新是否正确修改 YAML 和模拟数据库"""
    test_char = "hero"
    updates = {"physical_health": 99, "mental_state": "极度兴奋"}
    
    success = char_manager.update_character_state(test_char, updates)
    assert success is True
    
    # 验证 YAML 文件内容
    data = char_manager.load_character(test_char)
    assert data["dynamic_state"]["physical_health"] == 99
    assert data["dynamic_state"]["mental_state"] == "极度兴奋"

def test_event_insertion(event_manager):
    """验证事件插入功能"""
    test_summary = "单元测试生成的测试事件"
    success = event_manager.insert_event(test_summary)
    assert success is True
    
    # 验证数据库中是否存在该事件
    events = event_manager.query_recent_events(limit=1)
    assert events[0][1] == test_summary

if __name__ == "__main__":
    print("正在手动执行单元测试...")
    try:
        cm = CharacterManager()
        em = EventManager()
        test_character_update(cm)
        test_event_insertion(em)
        print("所有测试通过！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
