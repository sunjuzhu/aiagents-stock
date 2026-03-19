import requests
import json
import sys

def run_7b_on_gpu():
    url = "http://localhost:11434/api/generate"
    
    # 针对 780M 核显优化的配置
    payload = {
        "model": "qwen2.5:7b",
        "prompt": "请写一段关于‘量化交易’的简短定义，并列出三个核心优势。",
        "stream": True,             # 开启流式，感受 GPU 的爆发力
        "options": {
            "num_gpu": 99,          # 强制全量加载到 GPU (Radeon 780M)
            "num_ctx": 8192,        # 7B 能够稳跑 8k 上下文
            "temperature": 0.7,     # 保持适度的创造力
            "main_gpu": 0,          # 明确指定主显卡索引
            "low_vram": False       # 关闭低显存模式，让 780M 全速运行
        }
    }

    print("🚀 正在请求 7B 模型（强制 GPU 加速模式）...")
    print("-" * 30)

    try:
        # 使用 stream=True 获取实时响应
        with requests.post(url, json=payload, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    # 解析每一行返回的 JSON 片段
                    chunk = json.loads(line)
                    content = chunk.get("response", "")
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n" + "-" * 30)
            print("✅ 任务完成！")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 连接失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    run_7b_on_gpu()