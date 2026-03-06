import json

class WriterAgent:
    def __init__(self, model="gpt-4"):
        self.model = model

    def generate_prompt(self, logline, previous_summary, character_states, beat_metadata):
        prompt = f"""
你是一位顶级的科幻/奇幻小说家。请根据以下世界观和上下文生成小说的最新章节。

【故事大纲 Logline】
{logline}

【前文摘要】
{previous_summary}

【核心角色状态】
{json.dumps(character_states, ensure_ascii=False, indent=2)}

【本章节奏要求 Beat】
{json.dumps(beat_metadata, ensure_ascii=False, indent=2)}

【任务要求】
1. 生成长度约1500-2000字的高质量章节内容。
2. 遵守题材设定的约束，不出现穿越或机械降神等系统级禁忌。
3. 章节结尾需要为接下来的故事留出悬念（符合 foreshadowing 要求）。
4. 输出格式为 JSON，包含 "chapter_content"（章节文本） 和 "events_summary"（本章发生的关键事件提要，用于更新数据库）。
"""
        return prompt

    def call_llm(self, prompt):
        # 这里是伪代码，封装 LLM 调用逻辑
        print(">> [Writer Agent] 调用 LLM 接口，参数 Prompt 长度：", len(prompt))
        return {
            "chapter_content": "在霓虹灯闪烁的阴暗小巷中，Kael 紧握着手中那把老旧的爆裂手枪...",
            "events_summary": "Kael在小巷中遭遇了财阀的机械改造人巡逻队，成功击毁两名敌人但手臂受轻伤。"
        }

    def generate_chapter(self, context):
        prompt = self.generate_prompt(
            context.get("logline", ""),
            context.get("previous_summary", ""),
            context.get("character_states", {}),
            context.get("beat_metadata", {})
        )
        # 确保 prompt 长度不超过限制
        if len(prompt) > 3000:
            print("警告：Prompt 长度超过 3000 字符限制，可能需要截断。")
            
        result = self.call_llm(prompt)
        return result

if __name__ == '__main__':
    agent = WriterAgent()
    sample_context = {
        "logline": "在一个魔法与赛博朋克融合的未来世界，失去记忆的佣兵必须在巨型财阀的阴谋中寻找自己的过去，同时拯救被魔法污染的城市。",
        "previous_summary": "上一章中，主角发现了城市地下的一个废弃魔法实验室。",
        "character_states": {"Kael": {"health": 80, "mental": "警惕"}},
        "beat_metadata": {"beat_type": "hook", "focus": "引入新的反派角色"}
    }
    output = agent.generate_chapter(sample_context)
    print("生成结果：", json.dumps(output, ensure_ascii=False))
