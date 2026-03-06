import json
import datetime
import os

log_entry = {
    "task_id": "P1-2-Loop-2",
    "phase": "P1-2",
    "loop": "Loop-2",
    "status": "APPROVED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "report", "url": "artifacts/P1-2_Loop-2_report.md"},
    "summary": "审查 writer_agent.py，确认 Prompt 模板完整性及输入输出 JSON 格式要求。代码包含 <3000 token 的监控机制。P1-2 审核通过。",
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
    
content = content.replace("| P1-2 | Writer Agent 实现 | COMPLETED | 待执行 | 待执行 |", "| P1-2 | Writer Agent 实现 | COMPLETED | APPROVED | 待执行 |")
content = content.replace("## 当前执行任务： P1-2 / Loop-2", "## 当前执行任务： P1-2 / Loop-3")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
