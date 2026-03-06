import json
from orchestrator import Orchestrator
from writer_agent import WriterAgent
from critic_agent import CriticAgent

def dry_run():
    print("开始 P1-4 小规模验证（干跑测试）...")
    
    # 1. 初始化组件
    orch = Orchestrator()
    writer = WriterAgent()
    critic = CriticAgent()
    
    # 2. 模拟上下文
    context = {
        "logline": orch.config.get("logline", ""),
        "previous_summary": "这是干跑测试的初始章节。",
        "character_states": {"Kael": {"health": 100, "mental": "稳定"}},
        "beat_metadata": {"beat_type": "hook", "focus": "建立世界观"}
    }
    
    # 3. 执行 Writer Agent
    print("\n[Step 1] 执行 Writer Agent...")
    writer_result = writer.generate_chapter(context)
    chapter_content = writer_result.get("chapter_content")
    print(f"生成的章节内容预览: {chapter_content[:50]}...")
    
    # 4. 执行 Critic Agent
    print("\n[Step 2] 执行 Critic Agent...")
    critic_context = {
        "genre_rules": orch.config.get("genre_rules", []),
        "forbidden_elements": orch.config.get("forbidden_elements", []),
        "char_profiles": {"Kael": {"archetype": "失忆佣兵", "core_motive": "生存"}},
        "beat_metadata": context["beat_metadata"]
    }
    critic_result = critic.review_chapter(chapter_content, critic_context)
    
    # 5. 验证结果
    print("\n[Step 3] 验证最终结果...")
    passed = critic_result.get("passed", False)
    score = critic_result.get("score", 0)
    feedback = critic_result.get("feedback", "")
    
    print(f"审查是否通过: {passed}")
    print(f"评分: {score}")
    print(f"反馈: {feedback}")
    
    if passed and score >= 70:
        print("\n结论: 小规模验证通过！核心管道正常运转。")
        return True
    else:
        print("\n结论: 小规模验证未通过。")
        return False

if __name__ == "__main__":
    success = dry_run()
    if not success:
        exit(1)
