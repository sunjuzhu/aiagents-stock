from openai import OpenAI

# 1. 初始化客户端，指定 DeepSeek 的服务器地址
client = OpenAI(
    api_key="你的_DEEPSEEK_API_KEY", 
    base_url="https://api.deepseek.com"
)

# 2. 发起请求
response = client.chat.completions.create(
    # 选择模型：deepseek-chat (V3) 或 deepseek-reasoner (R1)
    model="deepseek-reasoner", 
    messages=[
        {"role": "system", "content": "你是一个量化投资专家。"},
        {"role": "user", "content": "帮我分析一下 A 股中 ARBR 指标在底部的有效性。"}
    ],
    stream=False
)

# 3. 输出结果
print(response.choices[0].message.content)

# 如果使用 R1 模型，你还可以提取它的“内心独白”（推理过程）
if hasattr(response.choices[0].message, 'reasoning_content'):
    print("--- 思考过程 ---")
    print(response.choices[0].message.reasoning_content)