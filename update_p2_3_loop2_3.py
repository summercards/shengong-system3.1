import json
import datetime
import os

log_file = "artifacts/stage_logs.json"
tasks_file = "tasks_list.md"
acc_file = "artifacts/acceptance_list.json"

def add_log(task_id, phase, loop, status, type_, url, summary):
    log_entry = {
        "task_id": task_id,
        "phase": phase,
        "loop": loop,
        "status": status,
        "actor": "OpenClaw-Agent",
        "artifact": {"type": type_, "url": url},
        "summary": summary,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try: logs = json.load(f)
            except: pass
    logs.append(log_entry)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

# Loop 2
add_log("P2-3-Loop-2", "P2-3", "Loop-2", "APPROVED", "report", "artifacts/P2-3_Loop-2_report.md", "世界与关系图管理审查通过")
# Loop 3
add_log("P2-3-Loop-3", "P2-3", "Loop-3", "COMPLETED", "report", "artifacts/P2-3_Loop-3_acceptance.md", "P2-3世界与关系图管理验收通过")

# Update Markdown
with open(tasks_file, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("| P2-3 | 世界与关系图更新 | COMPLETED | 待执行 | 待执行 |", "| P2-3 | 世界与关系图更新 | COMPLETED | APPROVED | COMPLETED |")
content = content.replace("## 当前执行任务： P2-3 / Loop-2", "## 当前执行任务： P2-4 / Loop-1")
with open(tasks_file, "w", encoding="utf-8") as f:
    f.write(content)

# Update Acceptance List
acc_list = []
if os.path.exists(acc_file):
    with open(acc_file, "r", encoding="utf-8") as f:
        try: acc_list = json.load(f)
        except: pass
acc_list.append({"phase": "P2-3", "status": "DONE", "last_completed_loop": "Loop-3", "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat()})
with open(acc_file, "w", encoding="utf-8") as f:
    json.dump(acc_list, f, indent=2, ensure_ascii=False)
