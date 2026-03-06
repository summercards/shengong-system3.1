import sqlite3

def init_db():
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events_log
                 (id INTEGER PRIMARY KEY, summary TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS world_graph_edges
                 (source TEXT, target TEXT, relation TEXT, weight INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_relationships
                 (char_a TEXT, char_b TEXT, trust_delta INTEGER, hostility_delta INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS foreshadowing_ledger
                 (clue_id TEXT PRIMARY KEY, description TEXT, status TEXT, created_chapter INTEGER)''')
    conn.commit()
    conn.close()
    print("数据库初始化完成")

if __name__ == '__main__':
    init_db()
