import pandas as pd
import akshare as ak
import time
import random

def get_hist_data_failover(symbol="000975"):
    """
    当东方财富断连时，自动切换到新浪数据源
    """
    # 格式化代码：新浪需要 sz000975 或 sh600000
    if symbol.startswith(('6', '9')):
        full_symbol = f"sh{symbol}"
    else:
        full_symbol = f"sz{symbol}"
        
    print(f"🔄 正在尝试从新浪财经获取 {symbol} 的数据...")
    
    try:
        # 使用新浪日线接口，这个接口目前对爬虫识别较松
        df = ak.stock_zh_a_daily(symbol=full_symbol, adjust="qfq")
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"❌ 新浪接口也失败了: {e}")
    
    return pd.DataFrame() # 保证返回的是 DF 而不是 None，避免 .head() 报错

# --- 测试代码 ---
df = get_hist_data_failover("000975")

if not df.empty:
    print(f"✅ 成功从备份源获取数据！最新日期: {df.index[-1]}")
    print(df.tail())
else:
    print("💀 所有数据源均已失效，请检查网络或更换代理节点。")