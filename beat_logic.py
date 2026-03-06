import json
import random

class BeatScheduler:
    def __init__(self, config_path="config/beat_scheduler.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    def get_beat_for_chapter(self, chapter_num):
        """根据章节号判定当前应该执行的节奏目标"""
        beats = self.config.get("story_beats", {})
        active_beats = []
        
        for name, info in beats.items():
            b_type = info["type"]
            if b_type == "fixed" and info["value"] == chapter_num:
                active_beats.append(name)
            elif b_type == "range" and info["min"] <= chapter_num <= info["max"]:
                active_beats.append(name)
            elif b_type == "interval" and chapter_num % info["every"] == 0:
                active_beats.append(name)
                
        return active_beats if active_beats else ["normal_progression"]

if __name__ == "__main__":
    scheduler = BeatScheduler()
    # 模拟测试几个关键章节
    for ch in [1, 3, 5, 10, 25]:
        print(f"第 {ch} 章 节奏点: {scheduler.get_beat_for_chapter(ch)}")
