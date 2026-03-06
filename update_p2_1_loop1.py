import json
import datetime
import os

log_entry = {
    "task_id": "P2-1-Loop-1",
    "phase": "P2-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "character_manager.py"},
    "summary": "实现了 CharacterManager 类，具备从 SQLite 读取权威状态并使用原子写入（.tmp 替换方式）同步到角色 YAML 缓存的功能。解决了并发写入导致的文件损坏风险。",
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
content = content.replace("| P2-1 | 角色状态读写 | 待执行 | 待执行 | 待执行 |", "| P2-1 | 角色状态读写 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P2-1 / Loop-1", "## 当前执行任务： P2-1 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
