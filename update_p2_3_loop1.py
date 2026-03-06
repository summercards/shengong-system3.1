import json
import datetime
import os

log_entry = {
    "task_id": "P2-3-Loop-1",
    "phase": "P2-3",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "graph_manager.py"},
    "summary": "实现了 GraphManager 类，支持对世界图（地点归属、势力关系）和角色图（信任度、敌对度）进行增删改查更新。代码包含了基本的冲突处理和数据库事务提交。",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

log_file = "artifacts/stage_logs.json"
logs = []
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        try: logs = json.load(f)
        except: pass
logs.append(log_entry)
with open(log_file, "w", encoding="utf-8") as f:
    json.dump(logs, f, indent=2, ensure_ascii=False)

with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("| P2-3 | 世界与关系图更新 | 待执行 | 待执行 | 待执行 |", "| P2-3 | 世界与关系图更新 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P2-3 / Loop-1", "## 当前执行任务： P2-3 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
