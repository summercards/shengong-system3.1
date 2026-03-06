import sqlite3

class ForeshadowingManager:
    def __init__(self, db_path="database.sqlite"):
        self.db_path = db_path

    def add_foreshadowing(self, clue_id, description, created_chapter):
        """记录新的伏笔线索"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO foreshadowing_ledger (clue_id, description, status, created_chapter) VALUES (?, ?, ?, ?)",
                (clue_id, description, "PENDING", created_chapter)
            )
            conn.commit()
            print(f">> [Foreshadowing] 新增伏笔: {clue_id} (第{created_chapter}章)")
            return True
        except Exception as e:
            print(f"添加伏笔失败: {e}")
            return False
        finally:
            conn.close()

    def resolve_foreshadowing(self, clue_id):
        """标记伏笔已解决（回收）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE foreshadowing_ledger SET status='RESOLVED' WHERE clue_id=?", (clue_id,))
            conn.commit()
            print(f">> [Foreshadowing] 伏笔已回收: {clue_id}")
            return True
        except Exception as e:
            print(f"回收伏笔失败: {e}")
            return False
        finally:
            conn.close()

    def get_pending_clues(self):
        """获取所有未解决的伏笔"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT clue_id, description, created_chapter FROM foreshadowing_ledger WHERE status='PENDING'")
            return cursor.fetchall()
        finally:
            conn.close()

if __name__ == "__main__":
    manager = ForeshadowingManager()
    # 演示新增
    manager.add_foreshadowing("CLUE_001", "Kael 在实验室看到的一串神秘数字，可能与财阀的秘密实验有关。", 1)
    manager.add_foreshadowing("CLUE_002", "主角手臂上的轻伤似乎开始发散出微弱的蓝色荧光。", 2)
    
    # 演示查询
    print("\n待回收的伏笔:")
    for clue in manager.get_pending_clues():
        print(f"ID: {clue[0]} | Chapter: {clue[2]} | Desc: {clue[1]}")
    
    # 演示回收
    manager.resolve_foreshadowing("CLUE_001")
