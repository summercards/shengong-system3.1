# test_lorekeeper.py - M2-3 LoreKeeper 测试
import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = r"I:\项目\shengong-system\godcraft_v4"
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

TEST_PROJECT_ID = "test_lorekeeper_project"
TEST_CHAR_ID = "char_test_001"


def setup_test_db():
    from database import get_connection
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            chapter_number INTEGER,
            event_type TEXT,
            summary TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS character_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            char_id_1 TEXT,
            char_id_2 TEXT,
            relationship_type TEXT,
            strength INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS world_graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            source_node TEXT,
            target_node TEXT,
            edge_type TEXT,
            weight REAL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS foreshadowing_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            chapter_introduced INTEGER,
            chapter_revealed INTEGER,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            parsed_intent TEXT,
            params TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def test_yaml_atomic():
    print("\n[TEST] YAML Atomic Write")
    from utils.yaml_utils import atomic_write_yaml, load_yaml
    
    test_file = "data/test_atomic.yaml"
    test_data = {"key": "value", "nested": {"a": 1}}
    
    success = atomic_write_yaml(test_file, test_data)
    assert success
    
    loaded = load_yaml(test_file)
    assert loaded == test_data
    
    if os.path.exists(test_file):
        os.remove(test_file)
    print("[PASS] YAML Atomic Write")


def test_basic():
    print("\n[TEST] LoreKeeper Basic Functionality")
    
    setup_test_db()
    
    from lorekeeper_agent import LoreKeeper
    
    keeper = LoreKeeper(TEST_PROJECT_ID)
    
    # Test 1: Character state update
    update1 = {
        "update_type": "character_state",
        "entity_id": TEST_CHAR_ID,
        "field_path": "dynamic_state.mood",
        "old_value": "neutral",
        "new_value": "happy",
        "reason": "Test character state update"
    }
    
    result1 = keeper.apply_structured_update(update1)
    print(f"  Status: {result1['status']}")
    assert result1["status"] == "committed", f"Expected committed, got {result1['status']}"
    
    char_file = f"data/characters/{TEST_CHAR_ID}.yaml"
    assert os.path.exists(char_file), f"Character YAML not created: {char_file}"
    print("[PASS] Character State Update")
    
    # Test 2: Relationship update
    update2 = {
        "update_type": "relationship",
        "entity_id": "char_a",
        "new_value": {
            "source": "char_a",
            "target": "char_b",
            "type": "friend",
            "weight": 80
        },
        "reason": "Test relationship"
    }
    
    result2 = keeper.apply_structured_update(update2)
    assert result2["status"] == "committed"
    print("[PASS] Relationship Update")
    
    # Test 3: World state update
    update3 = {
        "update_type": "world_state",
        "entity_id": "city_capital",
        "new_value": {
            "source": "city_capital",
            "target": "forest_enchanted",
            "type": "connects_to",
            "properties": {"distance": "50km"}
        },
        "reason": "Test world state"
    }
    
    result3 = keeper.apply_structured_update(update3)
    assert result3["status"] == "committed"
    print("[PASS] World State Update")
    
    # Test 4: Foreshadowing update
    update4 = {
        "update_type": "foreshadowing",
        "entity_id": "mysterious_prophecy",
        "new_value": {
            "event_description": "Mysterious prophecy",
            "target_chapter": 10,
            "trigger_condition": "Hero enters castle",
            "status": "active"
        },
        "reason": "Test foreshadowing"
    }
    
    result4 = keeper.apply_structured_update(update4)
    assert result4["status"] == "committed"
    print("[PASS] Foreshadowing Update")
    
    # Test 5: Read character
    char_data = keeper.read_character(TEST_CHAR_ID)
    assert char_data.get('dynamic_state', {}).get('mood') == 'happy'
    print("[PASS] Read Character")
    
    # Test 6: Read world state
    world_data = keeper.read_world_state()
    assert len(world_data.get('edges', [])) > 0
    print("[PASS] Read World State")


def test_convenience():
    print("\n[TEST] Convenience Functions")
    
    from lorekeeper_agent import apply_structured_update, read_lore
    
    # Test apply_structured_update
    update = {
        "update_type": "character_state",
        "entity_id": "char_conv_001",
        "field_path": "dynamic_state.location",
        "new_value": "castle",
        "reason": "Convenience function test"
    }
    
    result = apply_structured_update(TEST_PROJECT_ID, update)
    assert result["status"] == "committed"
    print("[PASS] apply_structured_update")
    
    # Test read_lore
    char = read_lore(TEST_PROJECT_ID, "character", "char_conv_001")
    assert char is not None
    assert char.get('dynamic_state', {}).get('location') == 'castle'
    print("[PASS] read_lore")


if __name__ == "__main__":
    test_yaml_atomic()
    test_basic()
    test_convenience()
    print("\n" + "="*50)
    print("ALL TESTS PASSED!")
    print("="*50)
