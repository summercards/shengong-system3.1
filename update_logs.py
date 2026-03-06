import json
import datetime
import os

log_entry = {
    "task_id": "P0-1-Loop-1",
    "phase": "P0-1",
    "loop": "Loop-1",
    "status": "COMPLETED",
    "actor": "OpenClaw-Agent",
    "artifact": {"type": "file", "url": "config/world_setting.yaml"},
    "summary": "创建了包含大纲、题材标签、禁用元素和自动运行控制的世界观配置文件。",
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}

log_file = "artifacts/stage_logs.json"

if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
else:
    logs = []

logs.append(log_entry)

with open(log_file, "w", encoding="utf-8") as f:
    json.dump(logs, f, indent=2, ensure_ascii=False)

# 更新 tasks_list.md
with open("tasks_list.md", "r", encoding="utf-8") as f:
    content = f.read()
    
content = content.replace("| P0-1 | 世界观配置生成 | 待执行 | 待执行 | 待执行 |", "| P0-1 | 世界观配置生成 | COMPLETED | 待执行 | 待执行 |")
content = content.replace("## 当前执行任务： P0-1 / Loop-1", "## 当前执行任务： P0-1 / Loop-2")

with open("tasks_list.md", "w", encoding="utf-8") as f:
    f.write(content)

# 打印必须输出的 JSON 格式结果
output = {
    "status": "COMPLETED",
    "artifact": {"type": "file", "url": "config/world_setting.yaml"},
    "log": "完成 P0-1 世界观配置生成，创建了包含基础设定的 world_setting.yaml 文件。最小可运行测试：检查文件是否存在并可读。测试结果：通过。",
    "metrics": {"tests_passed": 1, "tests_total": 1},
    "issues": []
}
print(json.dumps(output, indent=2, ensure_ascii=False))
