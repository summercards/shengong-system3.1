import json

class PlannerAgent:
    def __init__(self, model="gpt-4"):
        self.model = model

    def generate_plan_prompt(self, context, beat_metadata, pending_foreshadowing):
        # 针对 P3-3：构建伏笔提醒字符串
        clue_reminders = ""
        if pending_foreshadowing:
            clue_reminders = "\n【!!! 重要提醒：以下伏笔需要考虑在本章或近期回收 !!!】\n"
            for clue in pending_foreshadowing:
                clue_reminders += f"- 伏笔ID: {clue['clue_id']} | 描述: {clue['description']} (埋线章节: {clue['created_chapter']})\n"

        prompt = f"""
你是一位顶级的剧情策划师（Planner）。你的任务是根据当前的剧情节奏目标，规划本章节的具体情节。

【核心背景】
- Logline: {context.get('logline')}
- 前文摘要: {context.get('previous_summary')}

【当前节奏目标 (Beat)】
{json.dumps(beat_metadata, ensure_ascii=False, indent=2)}
{clue_reminders}

【任务要求】
请为本章节生成：
1. 章节情节简述 (Synopsis): 描述本章的主要剧情流程。
2. 关键转折/目标列表 (Key Turns): 列出本章必须达成的核心目标或剧情转折点。

输出格式为 JSON，包含字段 "synopsis" 和 "key_turns" (数组)。
"""
        return prompt

    def plan_chapter(self, context, beat_metadata, pending_foreshadowing):
        prompt = self.generate_plan_prompt(context, beat_metadata, pending_foreshadowing)
        
        # 演示输出提示词中的伏笔部分
        if "重要提醒" in prompt:
            print(">> [Planner] 检测到待处理伏笔，已注入 Prompt 提醒。")
            
        return {
            "synopsis": "Kael 在逃生过程中，无意间触碰了手臂上的伤口，那阵微弱的蓝色荧光再次亮起，并与地下节点的魔法共鸣，指引他发现了一个隐藏的终端。",
            "key_turns": [
                "逃离封锁线",
                "伏笔回收：调查手臂上的蓝色荧光 (CLUE_002)",
                "通过终端获取财阀的实验日志"
            ]
        }

if __name__ == "__main__":
    planner = PlannerAgent()
    sample_context = {"logline": "魔法赛博世界...", "previous_summary": "逃亡中..."}
    sample_beat = {"beat_type": "progression"}
    sample_clues = [{"clue_id": "CLUE_002", "description": "手臂上的蓝色荧光", "created_chapter": 2}]
    
    plan = planner.plan_chapter(sample_context, sample_beat, sample_clues)
    print("规划结果（含伏笔引用）：", json.dumps(plan, ensure_ascii=False, indent=2))
