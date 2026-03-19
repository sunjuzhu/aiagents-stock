import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5:7b",
        "prompt": "你好",
        "stream": False  # 先关掉流式，看看能不能跑通
    }
    
    try:
        print("发送请求...")
        response = requests.post(url, json=data)
        print(f"响应内容: {response.json().get('response')}")
    except Exception as e:
        print(f"出错: {e}")

if __name__ == "__main__":
    test_ollama()