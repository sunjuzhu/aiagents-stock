import pandas as pd
import os
import re
from datetime import datetime, timedelta
import akshare as ak

def _get_turnover_rate(self, symbol):
    """
    针对特殊格式 CSV 的换手率获取逻辑
    """
    turnover_rate = None
    source_name = ""

    try:
        base_path = "/home/samsun/桌面"
        now = datetime.now()
        
        # 周末回溯逻辑
        if now.weekday() == 5: target_date = now - timedelta(days=1)
        elif now.weekday() == 6: target_date = now - timedelta(days=2)
        else: target_date = now
            
        date_str = target_date.strftime("%Y%m%d")
        file_path = os.path.join(base_path, f"全部Ａ股{date_str}.xls")

        if os.path.exists(file_path):
            # 1. 读取文件，注意处理 GBK 编码和制表符
            # 增加 skipinitialspace=True 处理列名前后的空格
            df_local = pd.read_csv(file_path, sep='\t', encoding='gbk', on_bad_lines='skip', skipinitialspace=True)
            df_local.columns = [str(c).strip() for c in df_local.columns]  # 先清洗列名的空格
            print(f"📊 文件总行数: {len(df_local)}")
            print(f"📋 列名列表: {df_local.columns.tolist()[:5]}") # 打印前5个列名
            print(f"   [Local] 读取文件成功，初始列名示例: {list(df_local.columns)[:20]}")
            # 2. 【核心修复】强制清洗所有列名的空格
            df_local.columns = [str(c).strip() for c in df_local.columns]
            
            # 3. 检查清洗后的列名
            if '代码' in df_local.columns:
                print(f"   [Local] 列名 '代码' 已找到，继续处理数据行。")
                # 4. 清洗数据行中的代码列（去除 =" 和 "）
                df_local['clean_code'] = df_local['代码'].astype(str).apply(lambda x: re.sub(r'[="]', '', x).strip())
                
                # 5. 统一搜索的 symbol 格式（只留数字）
                search_symbol = re.sub(r'[^0-9]', '', str(symbol))
                
                # 6. 执行匹配
                match = df_local[df_local['clean_code'] == search_symbol]
                
                if not match.empty:
                    print(f"   [Local] ✅ 成功匹配到代码 {search_symbol}，正在提取换手率...")
                    # 样本中显示列名是 '换手%'
                    turnover_rate = match.iloc[0].get('换手%', None)
                    source_name = "本地文件"
                    
                    # 如果读到的是带有空格的字符串，转为 float
                    if isinstance(turnover_rate, str):
                        turnover_rate = turnover_rate.strip()
                    
                    print(f"   [Local] ✅ 成功匹配 {symbol}，换手率: {turnover_rate}%")
            else:
                print(f"   [Local] ⚠️ 清洗后的列名中仍未找到'代码'。当前列名: {list(df_local.columns)[:5]}")

    except Exception as e:
        print(f"   [Local] ⚠️ 读取失败: {e}")

    # --- 后续 Akshare 和 Tushare 兜底逻辑保持不变 ---
    if turnover_rate is None:
        # ... (之前的 Akshare 逻辑)
        pass

    # --- 统一解读逻辑 ---
    if turnover_rate is not None:
        try:
            val = float(turnover_rate)
            # ... (之前的 >20, >10 等判断逻辑)
            return {"current_turnover_rate": val, "interpretation": interpretation, "source": source_name}
        except:
            pass

    return None

tr = _get_turnover_rate(None, "000544")  # 示例调用
if tr:
    print(f"换手率: {tr['current_turnover_rate']}%，解读: {tr['interpretation']}，数据来源: {tr['source']}")
else:
    print("未能获取换手率数据")
