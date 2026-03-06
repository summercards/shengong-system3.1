import json
import datetime
import os

log_entry = {
    "task_id": "P4-2-Loop-1",
    "phase": "P4-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "interface.py"},
    "summary": "在 interface.py 中集成了角色状态监控模块。实现了对 data/characters/ 目录下 YAML 文件的自动化读取、展示以及针对 dynamic_state 字段的在线编辑功能。",
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
content = content.replace("| P4-2 | 角色状态监控界面 | 待执行 | 待执行 | 待执行 |", "| P4-2 | 角色状态监控界面 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P4-2 / Loop-1", "## 当前执行任务： P4-2 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
