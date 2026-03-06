import json
import datetime
import os

log_entry = {
    "task_id": "P1-4-Loop-1",
    "phase": "P1-4",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "dry_run_test.py"},
    "summary": "完成了核心管道的干跑测试。集成 Orchestrator, WriterAgent, 和 CriticAgent 进行模拟运行。输出章节符合结构预期，且通过了 Critic 审查。",
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
content = content.replace("| P1-4 | 小规模验证 | 待执行 | 待执行 | 待执行 |", "| P1-4 | 小规模验证 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P1-4 / Loop-1", "## 当前执行任务： P1-4 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
