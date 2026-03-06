import json
import datetime
import os

log_entry = {
    "task_id": "P1-4-Loop-2",
    "phase": "P1-4",
    "loop": "Loop-2",
    "status": "APPROVED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P1-4_Loop-2_report.md"},
    "summary": "审查了 P1-4 干跑测试结果，确认核心管道集成调用成功，Writer 与 Critic 的闭环逻辑符合预期。",
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
content = content.replace("| P1-4 | 小规模验证 | COMPLETED | 待执行 | 待执行 |", "| P1-4 | 小规模验证 | COMPLETED | APPROVED | 待执行 |")
content = content.replace("## 当前执行任务： P1-4 / Loop-2", "## 当前执行任务： P1-4 / Loop-3")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
