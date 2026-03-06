import json
import datetime
import os

log_entry = {
    "task_id": "P4-4-Loop-1",
    "phase": "P4-4",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "pipeline_manager.py"},
    "summary": "实现了并行触发控制逻辑。引入了 PipelineManager，利用队列和线程锁机制，实现了“并行规划、顺序生成”的流水线模式。确保了规划任务的并发效率，同时严格遵守大文本生成的串行调用限制，防止上下文冲突或模型负载超限。",
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
content = content.replace("| P4-4 | 并行触发控制 | 待执行 | 待执行 | 待执行 |", "| P4-4 | 并行触发控制 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P4-4 / Loop-1", "## 当前执行任务： P4-4 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
