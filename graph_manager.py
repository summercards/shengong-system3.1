import sqlite3

class GraphManager:
    def __init__(self, db_path="database.sqlite"):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def update_world_graph(self, source, target, relation, weight=1):
        """更新世界关系图（如地点连接、势力归属）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # 检查是否已存在
            cursor.execute("SELECT weight FROM world_graph_edges WHERE source=? AND target=? AND relation=?", (source, target, relation))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE world_graph_edges SET weight=? WHERE source=? AND target=? AND relation=?", (weight, source, target, relation))
            else:
                cursor.execute("INSERT INTO world_graph_edges (source, target, relation, weight) VALUES (?, ?, ?, ?)", (source, target, relation, weight))
            conn.commit()
            print(f">> [Graph] 世界图更新: {source} --({relation})--> {target}")
            return True
        except Exception as e:
            print(f"更新世界图失败: {e}")
            return False
        finally:
            conn.close()

    def update_character_relationship(self, char_a, char_b, trust_delta=0, hostility_delta=0):
        """更新角色间关系（信任度、敌对度）"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # 这里的逻辑根据指南，如果 delta 很大（>=3）应当标记为 pending_review，这里先实现基础更新
            cursor.execute("SELECT trust_delta, hostility_delta FROM character_relationships WHERE char_a=? AND char_b=?", (char_a, char_b))
            row = cursor.fetchone()
            if row:
                new_trust = row[0] + trust_delta
                new_hostility = row[1] + hostility_delta
                cursor.execute("UPDATE character_relationships SET trust_delta=?, hostility_delta=? WHERE char_a=? AND char_b=?", (new_trust, new_hostility, char_a, char_b))
            else:
                cursor.execute("INSERT INTO character_relationships (char_a, char_b, trust_delta, hostility_delta) VALUES (?, ?, ?, ?)", (char_a, char_b, trust_delta, hostility_delta))
            conn.commit()
            print(f">> [Graph] 角色关系更新: {char_a} & {char_b} (信任变动:{trust_delta}, 敌对变动:{hostility_delta})")
            return True
        except Exception as e:
            print(f"更新角色关系失败: {e}")
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    manager = GraphManager()
    # 演示：更新城市归属
    manager.update_world_graph("旧城区", "财阀联合体", "占领", 100)
    # 演示：更新角色关系
    manager.update_character_relationship("Kael", "财阀巡逻队长", trust_delta=-2, hostility_delta=5)
