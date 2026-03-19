import os
import sys
from dotenv import load_dotenv

# 确保可以导入当前目录下的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from llm_client import LLMClient
except ImportError as e:
    print(f"导入 llm_client 失败: {e}")
    print("请确保在项目根目录下运行此脚本。")
    sys.exit(1)

def test_llm_connection():
    """
    测试 LLM API 连接的脚本
    """
    # 1. 加载环境变量
    print("正在从 .env 文件加载环境变量...")
    # 即使 config.py 也会加载，这里显式加载以符合用户要求
    load_dotenv(override=True)
    
    # 2. 检查关键配置（从环境变量获取以验证加载是否成功）
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
    model_name = os.getenv("DEFAULT_MODEL_NAME", "deepseek-chat")
    
    if not api_key or api_key == "your_actual_API_KEY_here":
        print("\n❌ 错误: 未在 .env 中配置有效的 API_KEY")
        print("请检查 .env 文件并填入真实的 DeepSeek API Key。")
        return
        
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "****"
    print(f"\n当前 API 配置:")
    print(f"  - 模型: {model_name}")
    print(f"  - 接口地址: {base_url}")
    print(f"  - API Key: {masked_key}")
    print("-" * 50)

    # 3. 初始化 LLMClient
    print("正在初始化 LLMClient...")
    try:
        client = LLMClient()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 4. 测试简单的 API 调用
    test_messages = [
        {"role": "system", "content": "你是一个专业的金融分析助手，请使用中文回答。"},
        {"role": "user", "content": "你好，请简单介绍一下什么是‘量价背离’，并说明它在股市分析中的核心作用。"}
    ]
    
    print(f"正在向 {model_name} 发送测试请求，请稍候...")
    try:
        # 记录开始时间
        import time
        start_time = time.time()
        
        response = client.call_api(test_messages)
        
        duration = time.time() - start_time
        
        print(f"\n✅ API 调用成功! (耗时: {duration:.2f}秒)")
        print("\n--- AI 响应内容 ---")
        print(response)
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ API 调用过程中出现异常: {e}")
        print("\n调试建议:")
        print("1. 检查网络连接是否正常")
        print("2. 确认 API_KEY 是否有效且余额充足")
        print("3. 确认 BASE_URL 是否能从当前环境访问")

if __name__ == "__main__":
    test_llm_connection()
