import sqlite3
import datetime

class EventManager:
    def __init__(self, db_path="database.sqlite"):
        self.db_path = db_path

    def insert_event(self, summary):
        """将重要事件摘要写入 events_log 数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events_log (summary, timestamp) VALUES (?, ?)",
                (summary, datetime.datetime.now().isoformat())
            )
            conn.commit()
            print(f">> [DB] 成功写入事件: {summary}")
            return True
        except Exception as e:
            print(f"写入事件失败: {e}")
            return False
        finally:
            conn.close()

    def query_recent_events(self, limit=5):
        """查询最近的事件历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, summary, timestamp FROM events_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            events = cursor.fetchall()
            return events
        except Exception as e:
            print(f"查询事件历史失败: {e}")
            return []
        finally:
            conn.close()

if __name__ == "__main__":
    manager = EventManager()
    # 演示插入
    manager.insert_event("Kael 在旧城区的地下室发现了一枚古老的魔法徽章。")
    manager.insert_event("财阀的巡逻兵开始对贫民窟进行大规模封锁。")
    
    # 演示查询
    print("\n最近的事件历史:")
    for event in manager.query_recent_events():
        print(f"ID: {event[0]} | Time: {event[2]} | Summary: {event[1]}")
