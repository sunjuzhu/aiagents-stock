import requests

def ask_qwen_14b(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-14b-local", # 换回你的 14B 模型名
        "prompt": prompt,
        "stream": False,             # 核心：必须关闭流式
        "options": {
            "num_gpu": 35,           # 核心：不要给满 99，留几层给 CPU 缓冲
            "num_ctx": 4096,         # 核心：上下文锁死在 4k，防止 KV Cache 撑爆
            "num_thread": 8          # 利用你的 CPU 核心分担压力
        }
    }
    print("14B 正在深度思考（同步模式）...")
    try:
        response = requests.post(url, json=payload, timeout=120) # 14B 比较慢，超时设长点
        return response.json().get('response')
    except Exception as e:
        return f"发生错误: {e}"

# 测试 14B 的逻辑能力
res = ask_qwen_14b("请帮我写一个 Python 爬虫框架思路，用于获取中金财富的公开公告。")
print(f"14B 回复:\n{res}")  