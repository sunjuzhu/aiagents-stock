from openai import OpenAI
import sys

def call_ollama_openai():
    # 1. 初始化客户端，指向本地 Ollama 服务
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # 必填但不校验
    )

    print("🚀 正在通过 OpenAI 接口请求 7B 模型 (GPU加速)...")

    try:
        # 2. 发起对话请求
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": "你是一个资深的金融量化分析师。"},
                {"role": "user", "content": "请分析一下量化交易中‘网格交易’策略的优缺点。"}
            ],
            stream=True,  # 开启流式输出
            # 关键：通过 extra_body 强制 Ollama 使用 GPU
            extra_body={
                "options": {
                    "num_gpu": 99,
                    "num_ctx": 8192
                }
            }
        )

        # 3. 健壮的流式打印逻辑
        print("\nAI 回复：\n" + "-"*30)
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
        print("\n" + "-"*30)

    except Exception as e:
        print(f"\n❌ 调用出错: {e}")
        print("💡 提示：请确保执行了 'ollama serve' 且模型名正确。")

if __name__ == "__main__":
    call_ollama_openai()