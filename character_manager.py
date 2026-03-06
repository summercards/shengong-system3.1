import os
import yaml
import sqlite3
import tempfile
import shutil

class CharacterManager:
    def __init__(self, db_path="database.sqlite", character_dir="data/characters"):
        self.db_path = db_path
        self.character_dir = character_dir
        if not os.path.exists(self.character_dir):
            os.makedirs(self.character_dir)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def atomic_write_yaml(self, path, data):
        """原子写入 YAML 文件，避免损坏"""
        dirn = os.path.dirname(path)
        fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_")
        os.close(fd)
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            shutil.move(tmp, path)
        except Exception as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise e

    def load_character(self, name):
        """
        从 YAML 读取角色状态。
        注意：实际开发中应先从数据库读取权威数据，这里演示同步逻辑。
        """
        path = os.path.join(self.character_dir, f"{name}.yaml")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def update_character_state(self, name, updates):
        """
        更新角色状态：
        1. 更新 SQLite (权威数据源)
        2. 原子写入同步到 YAML (可读缓存)
        """
        # 1. 更新数据库 (模拟)
        conn = self._get_connection()
        try:
            # 这里简单演示，实际应有角色表更新
            print(f">> [DB] 更新角色 {name} 数据库记录: {updates}")
            
            # 2. 读取并同步 YAML
            data = self.load_character(name)
            if not data:
                print(f"角色 {name} 配置文件不存在，跳过 YAML 同步。")
                return False
                
            data['dynamic_state'].update(updates)
            
            yaml_path = os.path.join(self.character_dir, f"{name}.yaml")
            self.atomic_write_yaml(yaml_path, data)
            print(f">> [YAML] 原子写入成功: {yaml_path}")
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    manager = CharacterManager()
    # 模拟更新 Kael (之前 P0-2 创建的是 hero.yaml，其 name 是 Kael)
    # 统一一下，假设文件名和角色名一致，或者映射
    success = manager.update_character_state("hero", {"physical_health": 75, "mental_state": "疲惫但清醒"})
    if success:
        print("P2-1 功能演示成功。")
