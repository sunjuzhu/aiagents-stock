"""
数据源管理器
实现akshare和tushare的自动切换机制
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from data_manager import local_data_manager
from smart_monitor_tdx_data import SmartMonitorTDXDataFetcher


# 加载环境变量
load_dotenv()

tdxDataFetcher = SmartMonitorTDXDataFetcher()

import requests

def disable_proxy():
    """彻底禁用当前进程的代理环境变量"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    # 强制让 requests 库不使用代理

class DataSourceManager:
    """数据源管理器 - 实现akshare与tushare自动切换"""
    
    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_available = False
        self.tushare_api = None
        
        # 初始化tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                self.tushare_available = True
                print("✅ Tushare数据源初始化成功")
            except Exception as e:
                print(f"⚠️ Tushare数据源初始化失败: {e}")
                self.tushare_available = False
        else:
            print("ℹ️ 未配置Tushare Token，将仅使用Akshare数据源")
    
    def get_stock_hist_data(self, symbol, start_date=None, end_date=None, adjust='qfq'):
        """
        获取股票历史数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码（6位数字）
            start_date: 开始日期（格式：'20240101'或'2024-01-01'）
            end_date: 结束日期
            adjust: 复权类型（'qfq'前复权, 'hfq'后复权, ''不复权）
            
        Returns:
            DataFrame: 包含日期、开盘、收盘、最高、最低、成交量等列
        """
        # 标准化日期格式
        if start_date:
            start_date = start_date.replace('-', '')
        if end_date:
            end_date = end_date.replace('-', '')
        else:
            end_date = datetime.now().strftime('%Y%m%d')
        disable_proxy()

        # 优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的历史数据...")
            import os
            # 局部禁用代理
            # os.environ['NO_PROXY'] = 'eastmoney.com,127.0.0.1,localhost'
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                df['date'] = pd.to_datetime(df['date'])
                print(f"[Akshare] ✅ 成功获取 {len(df)} 条数据")
                return df
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")

        # --- 替换点：切换到新浪财经源 ---
        try:
            print(f"[Akshare-Sina] 🔄 正在切换至新浪源获取 {symbol}...")
            # 注意：新浪接口需要带上 sh/sz 前缀
            full_symbol = f"sh{symbol}" if symbol.startswith(('6', '9')) else f"sz{symbol}"
            
            # 使用 ak.stock_zh_a_daily (新浪源接口)
            df_sina = ak.stock_zh_a_daily(symbol=full_symbol, start_date=start_date, end_date=end_date, adjust=adjust)
            
            if df_sina is not None and not df_sina.empty:
                # 新浪返回的列名通常已经是英文或不同格式，需要统一化处理
                # 新浪接口通常 index 是日期，我们需要重置它
                df_sina = df_sina.reset_index()
                df_sina = df_sina.rename(columns={
                    'date': 'date', 'open': 'open', 'close': 'close', 
                    'high': 'high', 'low': 'low', 'volume': 'volume',
                    'amount': 'amount', 'outstanding_share': 'turnover'
                })
                print(f"[Akshare-Sina] ✅ 成功通过备份源获取 {len(df_sina)} 条数据")
                return df_sina
        except Exception as e_sina:
            print(f"[Akshare-Sina] ❌ 新浪源也失败了: {e_sina}")
            self.tushare_available = True

        # 如果都失败了，返回空 DataFrame 而不是 None，防止后面 .head() 崩溃
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的历史数据（备用数据源）...")
                
                # 转换股票代码格式（添加市场后缀）
                ts_code = self._convert_to_ts_code(symbol)
                
                # 转换复权类型
                adj_dict = {'qfq': 'qfq', 'hfq': 'hfq', '': None}
                adj = adj_dict.get(adjust, 'qfq')
                
                # 格式化日期
                start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if start_date else None
                end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if end_date else None
                
                # 获取数据
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    adj=adj
                )
                
                if df is not None and not df.empty:
                    # 标准化列名和数据格式
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    
                    # 转换成交量单位（tushare单位是手，转换为股）
                    df['volume'] = df['volume'] * 100
                    # 转换成交额单位（tushare单位是千元，转换为元）
                    df['amount'] = df['amount'] * 1000
                    
                    print(f"[Tushare] ✅ 成功获取 {len(df)} 条数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        # 两个数据源都失败
        print("❌ 所有数据源均获取失败")
        return None
   
        
    def get_stock_basic_info(self, symbol):
        """
        获取股票基本信息（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 股票基本信息
        """
        info = {
            "symbol": symbol,
            "name": "未知",
            "industry": "未知",
            "market": "未知"
        }
        tdx_data = tdxDataFetcher.get_stock_basic_info(symbol)
        local_data = local_data_manager. get_stock_info(symbol)
        tdx_data["industry"] = local_data.get("industry", "未知")  # 优先使用本地数据的行业信息
        tdx_data["list_date"] = local_data.get("list_date", "未知")  # 优先使用本地数据的上市日期信息
        return tdx_data

    
    def get_realtime_quotes(self, symbol):
        """
        获取实时行情数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 实时行情数据
        """
        quotes = {}
        # os.environ['NO_PROXY'] = 'eastmoney.com,sina.com.cn,127.0.0.1,localhost'
        try:
            tencent_quotes = self.get_quote_tencent(symbol)
            if tencent_quotes:
                return tencent_quotes
        except Exception as e:
            print(f"❌ 获取实时行情失败: {e}")

        
        # 优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的实时行情...")
            df = ak.stock_zh_a_spot_em()
            stock_df = df[df['代码'] == symbol]
            
            if not stock_df.empty:
                row = stock_df.iloc[0]
                quotes = {
                    'symbol': symbol,
                    'name': row['名称'],
                    'price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'change': row['涨跌额'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'open': row['今开'],
                    'pre_close': row['昨收']
                }
                print(f"[Akshare] ✅ 成功获取实时行情")
                return quotes
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
            # return self.get_quote_tencent(symbol)
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的实时行情（备用数据源）...")
                
                ts_code = self._convert_to_ts_code(symbol)
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=datetime.now().strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    quotes = {
                        'symbol': symbol,
                        'price': row['close'],
                        'change_percent': row['pct_chg'],
                        'volume': row['vol'] * 100,
                        'amount': row['amount'] * 1000,
                        'high': row['high'],
                        'low': row['low'],
                        'open': row['open'],
                        'pre_close': row['pre_close']
                    }
                    print(f"[Tushare] ✅ 成功获取实时行情")
                    return quotes
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return quotes
    
    def get_financial_data(self, symbol, report_type='income'):
        """
        获取财务数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）
            
        Returns:
            DataFrame: 财务数据
        """
        # 优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的财务数据...")
            
            if report_type == 'income':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            elif report_type == 'balance':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
            elif report_type == 'cashflow':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
            else:
                df = None
            
            if df is not None and not df.empty:
                print(f"[Akshare] ✅ 成功获取财务数据")
                return df
            
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的财务数据（备用数据源）...")
                
                ts_code = self._convert_to_ts_code(symbol)
                
                if report_type == 'income':
                    df = self.tushare_api.income(ts_code=ts_code)
                elif report_type == 'balance':
                    df = self.tushare_api.balancesheet(ts_code=ts_code)
                elif report_type == 'cashflow':
                    df = self.tushare_api.cashflow(ts_code=ts_code)
                else:
                    df = None
                
                if df is not None and not df.empty:
                    print(f"[Tushare] ✅ 成功获取财务数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return None
    
    def _convert_to_ts_code(self, symbol):
        """
        将6位股票代码转换为tushare格式（带市场后缀）
        
        Args:
            symbol: 6位股票代码
            
        Returns:
            str: tushare格式代码（如：000001.SZ）
        """
        if not symbol or len(symbol) != 6:
            return symbol
        
        # 根据代码判断市场
        if symbol.startswith('6'):
            # 上海主板
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            # 深圳主板和创业板
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            # 北交所
            return f"{symbol}.BJ"
        else:
            # 默认深圳
            return f"{symbol}.SZ"
    
    def _convert_from_ts_code(self, ts_code):
        """
        将tushare格式代码转换为6位代码
        
        Args:
            ts_code: tushare格式代码（如：000001.SZ）
            
        Returns:
            str: 6位股票代码
        """
        if '.' in ts_code:
            return ts_code.split('.')[0]
        return ts_code
    import requests

    def get_quote_tencent(self, symbol):
        """
        使用腾讯接口获取实时行情，并对齐东财字段名
        """
        import requests
        # 格式化代码
        full_symbol = f"sh{symbol}" if symbol.startswith(('6', '9')) else f"sz{symbol}"
        url = f"https://qt.gtimg.cn/q={full_symbol}"
        
        try:
            # 强制直连，不走代理
            r = requests.get(url, timeout=5, proxies={"http": None, "https": None})
            if r.status_code == 200 and len(r.text) > 50:
                # 腾讯返回格式: v_sz000630="1~铜陵有色~000630~3.45~3.41~3.42~..."
                data = r.text.split('"')[1].split('~')
                
                # 映射索引位到你的目标字典
                return {
                    'symbol': symbol,
                    'name': data[1],            # 名称
                    'price': float(data[3]),    # 当前价 (最新价)
                    'change_percent': float(data[32]), # 涨跌幅
                    'change': float(data[31]),         # 涨跌额
                    'volume': float(data[6]) * 100,    # 成交量 (腾讯返回单位是手，*100换算成股)
                    'amount': float(data[37]) * 10000, # 成交额 (腾讯单位是万，*10000换算成元)
                    'high': float(data[33]),    # 最高
                    'low': float(data[34]),     # 最低
                    'open': float(data[5]),     # 今开
                    'pre_close': float(data[4]) # 昨收
                }
            else:
                print(f"[Tencent] ❌ 数据格式异常或股票不存在: {symbol}")
        except Exception as e:
            print(f"[Tencent] ❌ 请求异常: {e}")
        
        return {}


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
# bd = data_source_manager.get_stock_basic_info("000630")
bd = data_source_manager.get_realtime_quotes("000630")
# print("基本信息：",bd.columns)
print(bd)

