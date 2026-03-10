import os
import json
import subprocess
import requests
import time


class OpenClawClient:

    def __init__(self):
        self.base_url = os.getenv("OPENCLAW_URL")

    def generate_with_retry(self, system_prompt, user_prompt, max_tokens=1500, retries=3):

        for i in range(retries):

            try:
                return self._generate(system_prompt, user_prompt, max_tokens)
            except Exception as e:

                if i == retries - 1:
                    raise e

                time.sleep(1)

    def _generate(self, system_prompt, user_prompt, max_tokens):

        # HTTP模式 (适配 OpenClaw 2026.2.25 兼容 OpenAI 规范的接口)
        if self.base_url:
            url = self.base_url.rstrip("/") + "/v1/chat/completions"
            
            payload = {
                "model": "shengong-agent",  # 默认占位
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens
            }
            
            try:
                # 必须加 timeout，防止大模型处理太久被 requests 默认断开
                r = requests.post(url, json=payload, timeout=600)
                r.raise_for_status()
                data = r.json()
                
                # 兼容标准 OpenAI 格式返回
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                
                # 兼容自定义降级格式
                if "content" in data:
                    return data["content"]
                
            except Exception as e:
                # 如果 HTTP 调用失败，依然降级回 CLI 模式
                print(f"[OpenClaw HTTP 失败，降级 CLI] {e}")

        # CLI模式 (适配 OpenClaw 2026.2.25 版本 agent 语法)
        combined_msg = f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"
        
        # ================= 最原始、最稳定的单条发令模式 =================
        cmd = [
            "openclaw.cmd" if os.name == "nt" else "openclaw",
            "agent",
            "--session-id", "shengong",
            "--message", combined_msg
        ]

        # 禁用 shell=True，直接使用环境变量去找
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())

        # ================== 探针：记录到底抓到了啥 ==================
        os.makedirs("data", exist_ok=True)
        with open("data/openclaw_raw.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [RAW OUTPUT]================\n{result.stdout}\n")
            if result.stderr:
                f.write(f"[STDERR]================\n{result.stderr}\n")
        # ============================================================

        if result.returncode != 0:
            raise RuntimeError(result.stderr)
            
        # 尝试从混杂的输出中提取最后一个 JSON 对象
        out_text = result.stdout.strip()
        try:
            # 找到最后一个换行后的内容，或者整个文本最外层的 {}
            start = out_text.rfind("{")
            end = out_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = out_text[start:end+1]
                out_json = json.loads(json_str)
                # ================= 终极 JSON 结构解析 =================
                
                # 1. 最深层嵌套 (针对长时间运行、带思维链或分段 payload 的新版结构)
                if "result" in out_json and isinstance(out_json["result"], dict):
                    if "payloads" in out_json["result"]:
                        payloads = out_json["result"]["payloads"]
                        if isinstance(payloads, list) and len(payloads) > 0:
                            # 提取所有分段文本，并拼接到一起
                            texts = [p.get("text", "") for p in payloads if isinstance(p, dict) and p.get("text")]
                            if texts:
                                return "\n\n".join(texts)
                
                # 2. 传统/简化结构
                if "content" in out_json:
                    return out_json["content"]
                if "response" in out_json:
                    return out_json["response"]
                if "message" in out_json:
                    return out_json["message"]
        except:
            pass
            
        # 如果解析失败，尽可能清理掉控制台乱码（比如去掉第一行欢迎语）
        lines = out_text.split('\n')
        clean_lines = [l for l in lines if not l.startswith('🦞') and l.strip()]
        return '\n'.join(clean_lines)

    def extract_structured_data(self, text):

        start = text.rfind("{")

        if start == -1:
            return {}

        try:
            return json.loads(text[start:])
        except:
            return {}
