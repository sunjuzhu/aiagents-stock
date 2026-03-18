import pandas as pd
import os
import re
import numpy as np
from datetime import datetime, timedelta

class LocalDataManager:
    _instance = None
    _data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalDataManager, cls).__new__(cls)
        return cls._instance

    def load_data(self):
        """精准清洗中金财富格式数据"""
        base_path = "/home/samsun/桌面"
        now = datetime.now()
        
        # 自动日期回溯逻辑
        if now.weekday() == 5: target_date = now - timedelta(days=1)
        elif now.weekday() == 6: target_date = now - timedelta(days=2)
        else: target_date = now
            
        date_str = target_date.strftime("%Y%m%d")
        
        file_path = None
        for ext in ['.xls', ' (副本).csv', '.csv']:
            p = os.path.join(base_path, f"全部Ａ股{date_str}{ext}")
            if os.path.exists(p):
                file_path = p
                break

        if not file_path:
            return False

        try:
            # 1. 自动识别分隔符
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='gbk', on_bad_lines='skip')
            
            # 2. 强制清洗列名
            df.columns = [re.sub(r'[\s\"\'=]', '', str(c)) for c in df.columns]
            
            if '代码' in df.columns:
                # 3. 处理代码格式
                df['symbol_clean'] = df['代码'].astype(str).apply(
                    lambda x: re.sub(r'[^0-9]', '', x).zfill(6)
                )
                
                # 4. 增强版字段映射：加入融资融券和股本相关字段
              # 4. 增强版字段映射
                mapping = {
                    '名称': 'name',
                    '现价': 'price',
                    '今开': 'open',
                    '最高': 'high',
                    '最低': 'low',
                    '昨收': 'prev_close',
                    '换手%': 'turnover_rate',
                    '涨幅%': 'pct_chg',
                    '总金额': 'amount',
                    '量比': 'volume_ratio',
                    '振幅%': 'amplitude',
                    '流通股(亿)': 'active_shares_bn',  # 关键字段：亿股单位
                    '总股本(亿)': 'total_shares_bn',
                    '市盈(TTM)': 'pe_ttm',
                    '市净率': 'pb',
                    '细分行业': 'industry',      # AI分析的关键
                    '上市日期': 'list_date'
                }
                
                # 找出文件中真正存在的列
                available_columns = [k for k in mapping.keys() if k in df.columns]
                
                # 提取并重命名
                self._data = df[['symbol_clean'] + available_columns].rename(columns=mapping)
                
                # 关键：如果你把 symbol_clean 设为 index，查询时要特别注意
                self._data = self._data.set_index('symbol_clean')
                
                # 5. 【核心优化】强制将数值列转为 float，处理 "--" 或空值
                numeric_cols = ['price', 'open', 'high', 'low', 'prev_close', 
                               'turnover_rate', 'pct_chg', 'margin_balance', 
                               'margin_buy', 'active_shares', 'total_shares']
                
                # 重命名以便转换
                self._data = self._data.rename(columns=mapping)
                
                for col in numeric_cols:
                    if col in self._data.columns:
                        # 转换前先去掉可能存在的逗号（如 1,234.56）
                        if self._data[col].dtype == 'object':
                            self._data[col] = self._data[col].str.replace(',', '')
                        self._data[col] = pd.to_numeric(self._data[col], errors='coerce').fillna(0)

                
                print(f"✅ [Local] 加载成功：包含两融及股本字段，已缓存 {len(self._data)} 只股票")
                return True
            return False
        except Exception as e:
            print(f"❌ [Local] 读取失败: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def get_stock_info(self, symbol):
        """安全获取单只股票信息，防止空结果"""
        # 预定义结果字典，防止 UnboundLocalError
        res = {
            'price': 0.0, 'turnover_rate': 0.0, 'open': 0.0, 
            'high': 0.0, 'low': 0.0, 'prev_close': 0.0,
            'name': '未知', 'source': 'None'
        }
        
        if self._data is None:
            self.load_data()

        # --- 核心修复逻辑 ---
        # 1. 如果传进来的是字符串 "symbol"，尝试从上层作用域找真实值（或报错提醒）
        symbol_str = str(symbol).strip()
        if symbol_str == "symbol":
            print("⚠️ 警告：你传入的是变量名字符串 'symbol' 而非变量本身！")
            return res
            
        # 2. 提取 6 位数字
        clean_query = re.sub(r'[^0-9]', '', symbol_str)
        if len(clean_query) > 6:
            clean_query = clean_query[-6:]
        elif len(clean_query) > 0:
            clean_query = clean_query.zfill(6)
        
        # 3. 匹配
        if self._data is not None and clean_query in self._data.index:
            row = self._data.loc[clean_query]
            if isinstance(row, pd.DataFrame): 
                row = row.iloc[0]
            res.update(row.to_dict())
            res['source'] = 'Local'
        else:
            print(f"🔍 [Local] 未命中：'{symbol_str}' (清洗后: '{clean_query}')")
            
        return res
    def get_market_sentiment_stats(self):
        """
        利用本地全市场快照计算大盘情绪
        包含：涨跌分布、涨跌停统计、赚钱效应
        """
        if self._data is None:
            if not self.load_data():
                return None

        # 这里的 copy() 是为了避免修改原始数据导致后续逻辑冲突
        df = self._data.copy()
        
        # --- 【关键修复：强制转换数据类型】 ---
        # errors='coerce' 会把无法转换的字符（如 '--'）变成 NaN
        # .fillna(0) 把 NaN 填充为 0，确保比较运算不报错
        if 'pct_chg' in df.columns:
            df['pct_chg'] = pd.to_numeric(df['pct_chg'], errors='coerce').fillna(0)
        
        if 'turnover_rate' in df.columns:
            df['turnover_rate'] = pd.to_numeric(df['turnover_rate'], errors='coerce').fillna(0)
        # --------------------------------------

        # 1. 涨跌分布统计
        total_count = len(df)
        up_count = int(len(df[df['pct_chg'] > 0]))  # 转换为原生 int，方便后续 JSON 序列化
        down_count = int(len(df[df['pct_chg'] < 0]))
        flat_count = total_count - up_count - down_count
        
        # 2. 涨跌停统计 (粗略估算，由于数值转换，现在的 9.8 是 float)
        limit_up = int(len(df[df['pct_chg'] >= 9.8]))
        limit_down = int(len(df[df['pct_chg'] <= -9.8]))
        
        # 3. 赚钱效应 (涨幅中位数)
        profit_effect = float(df['pct_chg'].median())
        
        # 4. 市场活跃度 (全市场平均换手率)
        avg_turnover = float(df['turnover_rate'].mean())

        return {
            "up_count": up_count,
            "down_count": down_count,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "profit_effect": f"{profit_effect:.2f}%",
            "avg_turnover": f"{avg_turnover:.2f}%",
            "sentiment_label": "贪婪" if profit_effect > 1 else ("恐慌" if profit_effect < -1 else "中性")
        }
    def get_stock_margin_info(self, symbol):
        """从本地全市场快照中提取两融数据"""
        if self._data is None:
            self.load_data()
        
        df = self._data
        # 查找对应股票
        stock_row = df[df['code'] == symbol]
        if stock_row.empty:
            return None
        
        row = stock_row.iloc[0]
        
        # --- 关键：匹配你 CSV 里的实际表头 ---
        # 请打开你的 CSV 确认一下，表头可能是 '融资余额(元)' 或 '融资余额'
        margin_bal = row.get('融资余额') or row.get('margin_balance')
        margin_buy = row.get('融资买入额') or row.get('margin_buy')
        
        if margin_bal is not None:
            # 强制数值化，防止 '--' 报错
            bal_val = pd.to_numeric(margin_bal, errors='coerce') or 0
            buy_val = pd.to_numeric(margin_buy, errors='coerce') or 0
            
            return {
                "margin_balance": bal_val,
                "margin_buy": buy_val,
                "source": "local_csv_snapshot"
            }
        return None
   

local_data_manager = LocalDataManager()