import json

class CriticAgent:
    def __init__(self, model="gpt-4"):
        self.model = model

    def generate_prompt(self, chapter_text, genre_rules, forbidden_elements, char_profiles, beat_metadata):
        prompt = f"""
你是一位严谨的内容审查编辑（Critic）。你的任务是审核以下生成的章节内容。

【生成章节内容】
{chapter_text}

【审查标准】
1. 是否违反题材规则 (Genre Rules): {genre_rules}
2. 是否存在违禁元素 (Forbidden Elements): {forbidden_elements}
3. 角色是否 OOC (Out of Character): 结合角色设定 {json.dumps(char_profiles, ensure_ascii=False)} 检查角色行为动机是否合理。
4. 剧情节奏是否匹配本章 Beat: {json.dumps(beat_metadata, ensure_ascii=False)}
请注意：不以“是否像爆款小说”作为判断标准。

【输出要求】
请输出 JSON 格式的结果，包含：
- "passed" (boolean): 审查是否通过
- "score" (integer 0-100): 满足基础逻辑的综合评分，低于70分视为未通过
- "feedback" (string): 如果未通过，详细列出触发了上述哪条问题；如果通过，可以写简短的评语
"""
        return prompt

    def call_llm(self, prompt):
        # 伪代码：调用大模型进行审查
        print(">> [Critic Agent] 调用 LLM 进行内容审查，Prompt 长度:", len(prompt))
        # 模拟模型输出
        return {
            "passed": True,
            "score": 85,
            "feedback": "通过。未发现系统流或机械降神，角色行为符合设定，且引入新反派的节奏合理。"
        }

    def review_chapter(self, chapter_text, context):
        genre_rules = context.get("genre_rules", [])
        forbidden_elements = context.get("forbidden_elements", [])
        char_profiles = context.get("char_profiles", {})
        beat_metadata = context.get("beat_metadata", {})

        prompt = self.generate_prompt(chapter_text, genre_rules, forbidden_elements, char_profiles, beat_metadata)
        
        # 单次处理限制 ~2000 token 的监控逻辑
        if len(prompt) > 2000:
            print("警告：Critic Prompt 长度超过 2000 token，可能需要截断章节文本。")
            
        return self.call_llm(prompt)

if __name__ == '__main__':
    agent = CriticAgent()
    sample_text = "在霓虹灯闪烁的阴暗小巷中，Kael 紧握着手中那把老旧的爆裂手枪..."
    sample_context = {
        "genre_rules": ["魔法与科技的平衡", "反乌托邦背景"],
        "forbidden_elements": ["穿越/系统流", "机械降神"],
        "char_profiles": {"Kael": {"archetype": "失忆佣兵", "core_motive": "生存"}},
        "beat_metadata": {"beat_type": "hook", "focus": "引入新的反派角色"}
    }
    result = agent.review_chapter(sample_text, sample_context)
    print("审查结果：", json.dumps(result, ensure_ascii=False))
