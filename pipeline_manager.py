import threading
import time
import queue

class PipelineManager:
    def __init__(self, max_parallel_plans=1):
        self.plan_queue = queue.Queue()
        self.generate_lock = threading.Lock()
        self.max_parallel_plans = max_parallel_plans

    def schedule_planning(self, chapter_id):
        """预排下一章节规划（并行触发）"""
        print(f">> [Pipeline] 正在预排第 {chapter_id} 章的规划任务...")
        # 模拟并行规划（耗时短）
        time.sleep(1) 
        self.plan_queue.put(chapter_id)
        print(f">> [Pipeline] 第 {chapter_id} 章规划完成，已进入生成队列。")

    def execute_sequential_generation(self):
        """顺序执行章节生成（串行调用）"""
        while True:
            try:
                chapter_id = self.plan_queue.get(timeout=5)
                with self.generate_lock:
                    print(f"\n[CRITICAL] 正在顺序执行第 {chapter_id} 章的大文本生成...")
                    # 模拟大模型生成耗时
                    time.sleep(2)
                    print(f"[CRITICAL] 第 {chapter_id} 章生成完毕。\n")
                self.plan_queue.task_done()
            except queue.Empty:
                print(">> [Pipeline] 生成队列已空，停止执行。")
                break

if __name__ == "__main__":
    pm = PipelineManager()
    
    # 模拟并行规划 3 个章节
    for i in range(1, 4):
        t = threading.Thread(target=pm.schedule_planning, args=(i,))
        t.start()
        
    # 开启顺序生成
    pm.execute_sequential_generation()
