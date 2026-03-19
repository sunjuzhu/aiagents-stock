import os
import pandas as pd

def save_hist_data_to_tmp(df, filename="hist_data.json"):
    """
    将历史行情 DataFrame 保存到 /tmp，并自动处理重复列名问题
    """
    if df is None or df.empty:
        print("⚠️ DataFrame 为空")
        return None

    # --- 关键修复步骤：处理重复列名 ---
    # 1. 检查是否有重复
    if df.columns.duplicated().any():
        print(f"⚠️ 发现重复列名: {df.columns[df.columns.duplicated()].unique().tolist()}，正在自动去重...")
        # 仅保留第一次出现的列（通常是主数据源的列）
        df = df.loc[:, ~df.columns.duplicated()]
    
    # 2. 统一转换为小写（可选，防止 Close 和 close 同时存在导致的混淆）
    df.columns = [c.lower() for c in df.columns]
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    file_path = os.path.join("/tmp", filename)
    
    try:
        # 确保目录存在
        df.to_json(
            file_path, 
            orient='records', 
            force_ascii=False, 
            indent=4, 
            date_format='iso'
        )
        print(f"✅ 历史数据已去重并保存至: {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None
    
import os
from datetime import datetime

def save_report_to_md(stock_name, stock_code, content):
    """
    将分析报告缓存到 ~/technical_analyst_report/
    文件名格式: 股票名_股票代码_20260319_1815.md
    """
    # 1. 确定基础路径并进行波浪号扩展 (Expands ~ to /home/lin)
    base_dir = os.path.expanduser("~/technical_analyst_report")
    
    # 2. 如果目录不存在则创建 (recursive)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        print(f"📁 已创建报告目录: {base_dir}")

    # 3. 生成安全的时间戳文件名 (避免使用 : / \ 等特殊字符)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 过滤股票名称中的空格
    safe_name = stock_name.replace(" ", "")
    filename = f"{safe_name}_{stock_code}_{timestamp}.md"
    file_path = os.path.join(base_dir, filename)

    try:
        # 4. 写入 Markdown 内容 (确保使用 utf-8 编码防止中文乱码)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 5. 修改权限，方便你在 T490 的 VS Code 中直接编辑
        os.chmod(file_path, 0o644)
        
        print(f"📝 报告已成功缓存至: {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ 报告保存失败: {str(e)}")
        return None

# --- 调用示例 ---
# report_content = llm_client.call_api(messages)
# save_report_to_md("铜陵有色", "000630", report_content)