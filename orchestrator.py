import yaml

class Orchestrator:
    def __init__(self, config_path="config/world_setting.yaml"):
        self.config = self.load_config(config_path)
        self.auto_run_enabled = self.config.get('auto_run', {}).get('enabled', False)
        self.max_chapters = self.config.get('auto_run', {}).get('max_chapters_per_run', 1)
        self.pause_on_high_risk = self.config.get('auto_run', {}).get('pause_on_high_risk', True)
        self.current_run_count = 0

    def load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"配置文件读取失败: {e}")
            return {}

    def fetch_database_state(self):
        # 伪代码：查询数据库获取最新章节、当前事件状态等
        print("查询数据库状态...")
        return {"last_chapter": 0}

    def call_writer_agent(self, context):
        # 伪代码：调用 Writer Agent 生成章节内容
        print("调用 Writer Agent 生成章节...")
        return "第一章 草稿内容..."

    def call_critic_agent(self, chapter_text):
        # 伪代码：调用 Critic Agent 审查章节
        print("调用 Critic Agent 检查章节...")
        # 返回 (是否通过, 评分或问题列表)
        return True, "通过"

    def detect_high_risk_update(self, chapter_events):
        # 伪代码：LoreKeeper 检查高风险更新
        print("检查高风险更新...")
        return False

    def run(self):
        print("Orchestrator 启动...")
        state = self.fetch_database_state()

        while True:
            if self.auto_run_enabled and self.current_run_count >= self.max_chapters:
                print(f"已达到自动运行上限: {self.max_chapters}章，暂停执行。")
                break

            chapter_text = self.call_writer_agent(state)
            passed, feedback = self.call_critic_agent(chapter_text)

            if not passed:
                print("Critic 审查未通过，暂停运行等待人工干预。反馈:", feedback)
                break

            high_risk = self.detect_high_risk_update({})
            if self.pause_on_high_risk and high_risk:
                print("检测到高风险更新，暂停运行等待人工确认。")
                break

            # 成功生成一章
            print("章节生成成功！")
            self.current_run_count += 1
            if not self.auto_run_enabled:
                print("自动运行未启用，执行单次后停止。")
                break

if __name__ == '__main__':
    orch = Orchestrator()
    orch.run()
