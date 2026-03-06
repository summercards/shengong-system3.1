import json
import datetime
import os

log_entry = {
    "task_id": "P5-2-Loop-1",
    "phase": "P5-2",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "code", "url": "context_compressor.py"},
    "summary": "实现了上下文压缩与 Token 监控模块。通过提炼历史摘要的方式有效缩减了后续请求的 Prompt 长度，并建立了基础的 Token 消耗统计机制，旨在优化长篇生成时的 API 效率。",
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
content = content.replace("| P5-2 | 大模型效率优化 | 待执行 | 待执行 | 待执行 |", "| P5-2 | 大模型效率优化 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P5-2 / Loop-1", "## 当前执行任务： P5-2 / Loop-2")
with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)
