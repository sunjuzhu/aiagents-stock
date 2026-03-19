import requests
import json

def stream_14b():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5-14b-local",
        "prompt": "请简单回复：14B模型启动成功了吗？", # 先用超短问题测试
        "stream": True, # 开启流式，看它蹦字
        "options": {"num_gpu": 35, "num_ctx": 2048}
    }

    print("正在观察 14B 的呼吸...")
    with requests.post(url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                print(chunk.get("response", ""), end="", flush=True)

if __name__ == "__main__":
    stream_14b()