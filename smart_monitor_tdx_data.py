"""
智能盯盘 - TDX数据获取模块
使用TDX股票数据API接口获取实时行情和技术指标
"""

import logging
import requests
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import numpy as np


class SmartMonitorTDXDataFetcher:
    """TDX数据获取器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        """
        初始化TDX数据获取器
        
        Args:
            base_url: TDX API基础地址
        """
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url.rstrip('/')
        self.timeout = 10  # 请求超时时间（秒）
        
        self.logger.info(f"TDX数据源初始化成功，接口地址: {self.base_url}")
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码（如：600519）
            
        Returns:
            实时行情数据
        """
        try:
            url = f"{self.base_url}/api/quote"
            params = {'code': stock_code}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            result = response.json()
            
            if result['code'] != 0:
                self.logger.error(f"TDX获取行情失败: {result.get('message')}")
                return None
            
            data_list = result.get('data', [])
            if not data_list:
                self.logger.warning(f"TDX未返回股票 {stock_code} 的行情数据")
                return None
            
            # 获取第一条数据
            quote_data = data_list[0]
            k_data = quote_data.get('K', {})
            
            # 价格单位转换：厘 -> 元（1元 = 1000厘）
            current_price = k_data.get('Close', 0) / 1000
            pre_close = k_data.get('Last', 0) / 1000
            open_price = k_data.get('Open', 0) / 1000
            high_price = k_data.get('High', 0) / 1000
            low_price = k_data.get('Low', 0) / 1000
            
            # 成交量单位：手（已是手，无需转换）
            volume = quote_data.get('TotalHand', 0)
            
            # 成交额单位转换：厘 -> 元
            amount = quote_data.get('Amount', 0) / 1000
            
            # 计算涨跌幅
            change_amount = current_price - pre_close
            change_pct = (change_amount / pre_close * 100) if pre_close > 0 else 0
            
            # 计算换手率（需要流通股本，TDX不提供，暂时设为0）
            turnover_rate = 0.0
            
            # 计算量比（现量/均量，这里用总手数/平均手数估算）
            vol_ma5 = volume / 1.2  # 简化估算
            volume_ratio = volume / vol_ma5 if vol_ma5 > 0 else 1.0
            
            # 获取股票名称（需要调用搜索接口）
            stock_name = self._get_stock_name(stock_code)
            
            self.logger.info(f"✅ TDX成功获取 {stock_code} ({stock_name}) 实时行情")
            
            return {
                'code': stock_code,
                'name': stock_name,
                'current_price': current_price,
                'change_pct': change_pct,
                'change_amount': change_amount,
                'volume': volume,  # 手
                'amount': amount,  # 元
                'high': high_price,
                'low': low_price,
                'open': open_price,
                'pre_close': pre_close,
                'turnover_rate': turnover_rate,
                'volume_ratio': volume_ratio,
                'update_time': datetime.fromtimestamp(int(quote_data.get('ServerTime', 0))).strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'tdx'
            }
            
        except requests.exceptions.Timeout:
            self.logger.error(f"TDX请求超时 {stock_code}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error(f"TDX连接失败，请检查接口地址: {self.base_url}")
            return None
        except Exception as e:
            self.logger.error(f"TDX获取行情失败 {stock_code}: {type(e).__name__}: {str(e)}")
            return None
    
    def _get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票名称
        """
        try:
            url = f"{self.base_url}/api/search"
            params = {'keyword': stock_code}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            result = response.json()
            
            if result['code'] == 0:
                data_list = result.get('data', [])
                for item in data_list:
                    if item.get('code') == stock_code:
                        return item.get('name', None)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"获取股票名称失败 {stock_code}: {e}")
            return None
    
    def get_stock_basic_info(self, stock_code: str) -> Dict:
        """
        [更新] 从TDX获取股票基本信息 (名称、市场、估算市值)
        """
        # 1. 自动判断市场 (程序员式逻辑)
        market = "沪市" if stock_code.startswith(('60', '68')) else "深市"
        if stock_code.startswith('30'): market = "创业板"
        if stock_code.startswith('8'): market = "北交所"
        
        # 2. 获取实时快照 (利用你已有的 get_realtime_quote)
        quote = self.get_realtime_quote(stock_code)
        
        # 3. 构造返回结构
        info = {
            "symbol": stock_code,
            "name": quote.get('name') if quote else "未知",
            "market": market,
            "industry": "请结合本地CSV获取", # TDX API通常不直接给中文行业名
            "price": quote.get('current_price') if quote else 0,
            "data_source": "tdx_api"
        }
        
        # 4. 如果你想拿更深的数据（如总股本），需要检查你 TDX API 的 data 原始字典
        # 某些 TDX API 扩展版会在 quote 的结果里带上 TotalValue (总市值)
        return info

    def get_kline_data(self, stock_code: str, kline_type: str = 'day', limit: int = 200) -> Optional[pd.DataFrame]:
        try:
            url = f"{self.base_url}/api/kline"
            params = {'code': stock_code, 'type': kline_type}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            result = response.json()
            
            if result['code'] != 0:
                self.logger.error(f"TDX获取K线失败: {result.get('message')}")
                return None
            
            kline_list = result.get('data', {}).get('List', [])
            if not kline_list:
                return None
            
            rows = []
            for item in kline_list:
                # 显式强制转换为 float，防止 JSON 解析出非数值类型
                rows.append({
                    '日期': item.get('Time', '').split('T')[0],
                    '开盘': float(item.get('Open', 0)) / 1000,
                    '收盘': float(item.get('Close', 0)) / 1000,
                    '最高': float(item.get('High', 0)) / 1000,
                    '最低': float(item.get('Low', 0)) / 1000,
                    '成交量': float(item.get('Volume', 0)),
                    '成交额': float(item.get('Amount', 0)) / 1000,
                })
            
            # 1. 创建 DataFrame
            df = pd.DataFrame(rows)
            
            # 2. 核心修正：先转换日期格式
            df['日期'] = pd.to_datetime(df['日期'])
            
            # 3. 核心修正：强制按日期升序排列（最早的在 index 0，最新的在最后）
            # 只有这样，rolling(5).mean() 算出的才是真正的历史均价
            df = df.sort_values('日期').reset_index(drop=True)
            
            # 4. 只保留最近 limit 条
            if len(df) > limit:
                df = df.tail(limit).reset_index(drop=True)
            
            self.logger.info(f"✅ TDX成功获取 {stock_code} K线数据，共{len(df)}条")
            # return df
            # 在 return df 之前建议加入
            if df is not None and not df.empty:
                # 统一列名映射，确保后续计算指标不会因为找不到列名而报错
                rename_map = {
                    'date': '日期', 'open': '开盘', 'high': '最高', 
                    'low': '最低', 'close': '收盘', 'vol': '成交量', 'amount': '成交额'
                }
                df = df.rename(columns=rename_map)
                # 再次确保是升序排列，这样无论哪个数据源进来，后面算 MACD/ARBR 都是对的
                df = df.sort_values('日期').reset_index(drop=True)
                return df
            
        except Exception as e:
            self.logger.error(f"TDX获取K线失败 {stock_code}: {e}")
            return None
    def get_technical_indicators(self, stock_code: str, period: str = 'daily') -> Optional[Dict]:
        """
        计算技术指标
        
        Args:
            stock_code: 股票代码
            period: 周期（daily/weekly/monthly）
            
        Returns:
            技术指标数据
        """
        try:
            # 映射周期类型
            kline_type_map = {
                'daily': 'day',
                'weekly': 'week',
                'monthly': 'month'
            }
            kline_type = kline_type_map.get(period, 'day')
            
            # 获取K线数据（需要足够的数据计算指标，至少200条）
            df = self.get_kline_data(stock_code, kline_type=kline_type, limit=200)
            
            if df is None or df.empty or len(df) < 60:
                self.logger.warning(f"股票 {stock_code} K线数据不足，无法计算技术指标")
                return None
            
            # 计算技术指标
            return self._calculate_all_indicators(df, stock_code)
            
        except Exception as e:
            self.logger.error(f"TDX计算技术指标失败 {stock_code}: {e}")
            return None
    
    def _calculate_all_indicators(self, df: pd.DataFrame, stock_code: str) -> Optional[Dict]:
        """
        根据历史数据计算所有技术指标
        
        Args:
            df: 历史数据DataFrame
            stock_code: 股票代码
            
        Returns:
            技术指标数据
        """
        try:
            if df.empty or len(df) < 60:
                self.logger.warning(f"股票 {stock_code} 历史数据不足")
                return None
            
            # 计算均线
            df['ma5'] = df['收盘'].rolling(window=5).mean()
            df['ma20'] = df['收盘'].rolling(window=20).mean()
            df['ma60'] = df['收盘'].rolling(window=60).mean()
            
            # 计算MACD
            df = self._calculate_macd(df)
            
            # 计算RSI
            df = self._calculate_rsi(df, periods=[6, 12, 24])
            
            # 计算KDJ
            df = self._calculate_kdj(df)
            
            # 计算布林带
            df = self._calculate_bollinger(df)
            
            # 计算量能均线
            df['vol_ma5'] = df['成交量'].rolling(window=5).mean()
            df['vol_ma10'] = df['成交量'].rolling(window=10).mean()
            
            # 取最后一行数据
            latest = df.iloc[-1]
            
            # 判断趋势
            current_price = float(latest['收盘'])
            ma5 = float(latest['ma5'])
            ma20 = float(latest['ma20'])
            ma60 = float(latest['ma60'])
            
            if current_price > ma5 > ma20 > ma60:
                trend = 'up'
            elif current_price < ma5 < ma20 < ma60:
                trend = 'down'
            else:
                trend = 'sideways'
            
            # 布林带位置
            boll_upper = float(latest['boll_upper'])
            boll_mid = float(latest['boll_mid'])
            boll_lower = float(latest['boll_lower'])
            
            if current_price >= boll_upper:
                boll_position = '上轨附近（超买）'
            elif current_price <= boll_lower:
                boll_position = '下轨附近（超卖）'
            elif current_price > boll_mid:
                boll_position = '中轨上方'
            else:
                boll_position = '中轨下方'
            
            return {
                'ma5': ma5,
                'ma20': ma20,
                'ma60': ma60,
                'trend': trend,
                'macd_dif': float(latest['dif']),
                'macd_dea': float(latest['dea']),
                'macd': float(latest['macd']),
                'rsi6': float(latest['rsi6']),
                'rsi12': float(latest['rsi12']),
                'rsi24': float(latest['rsi24']),
                'kdj_k': float(latest['kdj_k']),
                'kdj_d': float(latest['kdj_d']),
                'kdj_j': float(latest['kdj_j']),
                'boll_upper': boll_upper,
                'boll_mid': boll_mid,
                'boll_lower': boll_lower,
                'boll_position': boll_position,
                'vol_ma5': float(latest['vol_ma5']),
                'volume_ratio': float(latest['成交量']) / float(latest['vol_ma5']) if latest['vol_ma5'] > 0 else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败 {stock_code}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None
    
    def get_comprehensive_data(self, stock_code: str) -> Dict:
        """
        获取综合数据（实时行情+技术指标）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            综合数据
        """
        result = {}
        
        # 实时行情
        quote = self.get_realtime_quote(stock_code)
        if quote:
            result.update(quote)
        
        # 技术指标
        indicators = self.get_technical_indicators(stock_code)
        if indicators:
            result.update(indicators)
        
        return result
    
    # ========== 技术指标计算方法 ==========
    
    def _calculate_macd(self, df: pd.DataFrame, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
        
        df['dif'] = ema_fast - ema_slow
        df['dea'] = df['dif'].ewm(span=signal, adjust=False).mean()
        df['macd'] = (df['dif'] - df['dea']) * 2
        
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """计算RSI指标"""
        for period in periods:
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            df[f'rsi{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _calculate_kdj(self, df: pd.DataFrame, n: int = 9, 
                      m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        low_list = df['最低'].rolling(window=n).min()
        high_list = df['最高'].rolling(window=n).max()
        
        rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
        
        df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def _calculate_bollinger(self, df: pd.DataFrame, 
                           period: int = 20, std_num: int = 2) -> pd.DataFrame:
        """计算布林带"""
        df['boll_mid'] = df['收盘'].rolling(window=period).mean()
        std = df['收盘'].rolling(window=period).std()
        
        df['boll_upper'] = df['boll_mid'] + std_num * std
        df['boll_lower'] = df['boll_mid'] - std_num * std
        
        return df
    def calculate_arbr_from_tdx(self, symbol: str, period: int = 26):
        """
        通过 TDX 数据源计算 ARBR 指标
        """
        try:
            # 1. 获取 40 条日线数据
            df_raw = self.get_kline_data(symbol, kline_type='day', limit=40)

            if df_raw is None or len(df_raw) < period + 1:
                self.logger.warning(f"⚠️ {symbol} 数据条数不足 (当前: {len(df_raw) if df_raw is not None else 0})")
                return None, None

            # --- 关键调试步骤：打印列名，确认是否匹配 ---
            # self.logger.info(f"DEBUG: TDX 返回的原始列名为: {df_raw.columns.tolist()}")

            # 2. 统一列名映射（根据你 get_kline_data 的定义）
            # 注意：DataFrame 必须 copy() 否则会报 SettingWithCopy 警告
            df = df_raw.copy()
            
            # 确保列名一致（如果 get_kline_data 已经转为了中文，这里映射回英文方便计算）
            col_map = {'开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close'}
            df = df.rename(columns=col_map)

            # 3. 强制转换数值类型，防止 String 或 Object 类型导致计算失效
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 4. 计算 AR 中间变量
            # AR = SUM(H - O) / SUM(O - L)
            df['h_o'] = df['high'] - df['open']
            df['o_l'] = df['open'] - df['low']

            # 5. 计算 BR 中间变量
            # BR = SUM(H - CY) / SUM(CY - L)
            df['prev_close'] = df['close'].shift(1)
            df['h_cy'] = df['high'] - df['prev_close']
            df['cy_l'] = df['prev_close'] - df['low']

            # 6. 核心修正：剔除首行 NaN 并在计算前处理负值（BR 公式特性）
            # 在极少数跳空情况下，H-CY 可能是负数，但 BR 统计的是意愿能量，通常取正值部分
            analysis_df = df.dropna(subset=['prev_close']).tail(period).copy()
            
            # 7. 执行求和
            ar_up = analysis_df['h_o'].sum()
            ar_down = analysis_df['o_l'].sum()
            br_up = analysis_df['h_cy'].sum()
            br_down = analysis_df['cy_l'].sum()

            # 8. 结果计算：增加极小值保护 epsilon (1e-6) 防止除以零
            ar = (ar_up / ar_down * 100) if abs(ar_down) > 1e-6 else 100.0
            br = (br_up / br_down * 100) if abs(br_down) > 1e-6 else 100.0

            # 正常的平安银行 ARBR 应该在 70 - 150 之间
            self.logger.info(f"✅ {symbol} ARBR 计算结果 -> AR: {ar:.2f}, BR: {br:.2f}")
            return round(float(ar), 2), round(float(br), 2)

        except Exception as e:
            self.logger.error(f"❌ ARBR 计算发生逻辑错误: {e}")
            return None, None
    def get_margin_data_from_tdx(self, symbol: str):
        """
        从 TDX 获取个股融资融券（信用交易）实时快照
        """
        try:
            # 使用 get_realtime_quote 或类似的实时接口
            quote = self.get_realtime_quote(symbol) 
            print(f"TDX 获取 {symbol} 实时行情数据:", quote)  # 调试输出
            if quote:
                # TDX 的实时行情中通常包含这些字段（取决于你本地 TDX 服务端的配置）
                # 某些接口会将其封装在 'MarginBalance' 等字段中
                margin_buy = quote.get('MarginBuy', 0) / 1000 # 转为元
                margin_bal = quote.get('MarginBalance', 0) / 1000
                
                if margin_bal > 0:
                    interpretation = ["融资余额充足，杠杆意愿活跃"] if margin_bal > 1e8 else ["融资规模适中"]
                    return {
                        "margin_balance": margin_bal,
                        "margin_buy": margin_buy,
                        "interpretation": interpretation,
                        "source": "tdx_realtime"
                    }
        except Exception as e:
            self.logger.error(f"TDX 获取两融数据失败: {e}")
            print(f"❌ [TDX] 获取两融数据失败: {e}")
        return None
if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 将计算 ARBR 的方法暴露出来供外部调用 
    arbr = SmartMonitorTDXDataFetcher().calculate_arbr_from_tdx("000001")
    print(f"ARBR 指标: AR={arbr[0]}, BR={arbr[1]}")
    
    # 使用默认地址测试
    fetcher = SmartMonitorTDXDataFetcher(base_url="http://127.0.0.1:8080")
    
    # 测试平安银行(000001)
    print("测试获取平安银行(000001)数据...")
    data = fetcher.get_comprehensive_data('000001')
    
    if data:
        print("\n实时行情:")
        print(f"  股票名称: {data.get('name')}")
        print(f"  当前价: {data.get('current_price')} 元")
        print(f"  涨跌幅: {data.get('change_pct')}%")
        print(f"  数据源: {data.get('data_source')}")
        
        print("\n技术指标:")
        print(f"  MA5: {data.get('ma5', 0):.2f}")
        print(f"  MA20: {data.get('ma20', 0):.2f}")
        print(f"  MACD: {data.get('macd', 0):.4f}")
        print(f"  RSI(6): {data.get('rsi6', 0):.2f}")
        print(f"  趋势: {data.get('trend')}")
    else:
        print("获取数据失败")

