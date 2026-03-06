import json
import datetime
import os

log_entry = {
    "task_id": "P6-2-Loop-1",
    "phase": "P6-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "release_manager.py"},
    "summary": "实现了发布版本管理模块。能够自动化生成 VERSION 文件、维护 CHANGELOG.md 并执行（模拟）Git 标签管理流程，确保项目各阶段成果均有版本可溯。",
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
content = content.replace("| P6-2 | 发布版本管理 | 待执行 | 待执行 | 待执行 |", "| P6-2 | 发布版本管理 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P6-2 / Loop-1", "## 当前执行任务： P6-2 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
