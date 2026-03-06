import json
import datetime
import os

log_entry = {
    "task_id": "P4-1-Loop-1",
    "phase": "P4-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "interface.py"},
    "summary": "开发了基于 Streamlit 的剧本编辑界面骨架。支持 Logline 的实时编辑与保存，提供了题材规则的维护接口，并预留了章节大纲人工精修的交互区域。",
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
content = content.replace("| P4-1 | 剧本编辑界面 | 待执行 | 待执行 | 待执行 |", "| P4-1 | 剧本编辑界面 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P4-1 / Loop-1", "## 当前执行任务： P4-1 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
