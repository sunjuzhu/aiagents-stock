"""
市场情绪数据获取和计算模块
使用akshare获取市场情绪相关指标，包括ARBR、恐慌指数、市场资金情绪等
"""

import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import warnings
import sys
import io
import os
import re
from data_source_manager import data_source_manager
from pathlib import Path

from smart_monitor_tdx_data import SmartMonitorTDXDataFetcher

from data_manager import local_data_manager

def disable_proxy():
    """彻底禁用当前进程的代理环境变量"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    # 强制让 requests 库不使用代理
    os.environ['NO_PROXY'] = '*'

os.environ['NO_PROXY'] = 'eastmoney.com,tushare.pro,waditu.com,127.0.0.1,localhost'

warnings.filterwarnings('ignore')

# 设置标准输出编码为UTF-8（仅在命令行环境，避免streamlit冲突）
def _setup_stdout_encoding():
    """仅在命令行环境设置标准输出编码"""
    if sys.platform == 'win32' and not hasattr(sys.stdout, '_original_stream'):
        try:
            # 检测是否在streamlit环境中
            import streamlit
            # 在streamlit中不修改stdout
            return
        except ImportError:
            # 不在streamlit环境，可以安全修改
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
            except:
                pass

_setup_stdout_encoding()


class MarketSentimentDataFetcher:
    """市场情绪数据获取和计算类"""
    
    def __init__(self):
        self.arbr_period = 26  # ARBR计算周期
        self.cache_dir = Path("/tmp/stock_sentiment_cache")
        self.cache_dir.mkdir(exist_ok=True)
        # 增加 TDX fetcher 占位
        self._tdx_fetcher = None
        self.data_source_manager = local_data_manager

    @property
    def tdx_fetcher(self):
        """懒加载 TDX 抓取器"""
        if self._tdx_fetcher is None:
            # 这里可以结合你之前的环境变量判断逻辑
            tdx_enabled = os.getenv('TDX_ENABLED', 'false').lower() == 'true'
            tdx_url = os.getenv('TDX_BASE_URL', 'http://127.0.0.1:8080')
            
            if tdx_enabled:
                try:
                    self._tdx_fetcher = SmartMonitorTDXDataFetcher(base_url=tdx_url)
                    print(f"🚀 TDX 抓取器初始化成功: {tdx_url}")
                except Exception as e:
                    print(f"⚠️ TDX 初始化失败: {e}")
        return self._tdx_fetcher
    def _get_cache_filename(self, prefix):
        """生成基于时间戳的文件名"""
        now = datetime.now()
        weekday = now.weekday()  # 0是周一, 4是周五
        hour = now.hour
        minute = now.minute

        # 判定是否为非交易时段（周五15:00后 到 周一09:30前）
        is_weekend = False
        if weekday == 4 and (hour > 15 or (hour == 15 and minute > 0)):
            is_weekend = True
        elif weekday in [5, 6]: # 周六周日
            is_weekend = True
        elif weekday == 0 and (hour < 9 or (hour == 9 and minute < 30)):
            is_weekend = True

        if is_weekend:
            # 非交易时间统一使用一个固定后缀
            time_suffix = "weekend_closed"
        else:
            # 交易时间：每15分钟一个快照 (0, 15, 30, 45)
            quarter = (minute // 15) * 15
            time_suffix = now.strftime(f"%Y%m%d_%H{quarter:02d}")

        return self.cache_dir / f"{prefix}_{time_suffix}.feather"
    
    def _get_data_with_cache(self, cache_prefix, fetch_func):
        """通用缓存读取逻辑"""
        cache_file = self._get_cache_filename(cache_prefix)
        
        # 1. 尝试读取缓存
        if cache_file.exists():
            try:
                print(f"🚀 [Cache] 命中本地缓存: {cache_file.name}")
                return pd.read_feather(cache_file).to_dict(orient='records')[0]
            except Exception as e:
                print(f"⚠️ 缓存读取失败: {e}")

        # 2. 缓存不存在或读取失败，执行抓取
        data = fetch_func()
        
        # 3. 序列化存储
        if data:
            try:
                # 将字典转为单行DataFrame存入
                pd.DataFrame([data]).to_feather(cache_file)
                # 清理旧缓存（可选：删除1小时前的文件避免/tmp过大）
                # self._cleanup_old_caches()
            except Exception as e:
                print(f"⚠️ 写入缓存失败: {e}")
        
        return data

    def _cleanup_old_caches(self):
        """清理超过 2 小时的旧缓存文件"""
        try:
            for f in self.cache_dir.glob("*.feather"):
                if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)) > timedelta(hours=2):
                    f.unlink()
        except:
            pass
    def get_market_sentiment_stats(self):
        """
        利用本地全市场快照计算大盘情绪
        包含：涨跌分布、涨跌停统计、赚钱效应
        """
        if self._data is None:
            if not self.load_data():
                return None

        df = self._data
        
        # 1. 涨跌分布统计
        total_count = len(df)
        up_count = len(df[df['pct_chg'] > 0])
        down_count = len(df[df['pct_chg'] < 0])
        flat_count = total_count - up_count - down_count
        
        # 2. 涨跌停统计 (粗略估算)
        limit_up = len(df[df['pct_chg'] >= 9.8])
        limit_down = len(df[df['pct_chg'] <= -9.8])
        
        # 3. 赚钱效应 (涨幅中位数)
        profit_effect = df['pct_chg'].median()
        
        # 4. 市场活跃度 (全市场平均换手率)
        avg_turnover = df['turnover_rate'].mean()

        return {
            "up_count": up_count,
            "down_count": down_count,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "profit_effect": f"{profit_effect:.2f}%",
            "avg_turnover": f"{avg_turnover:.2f}%",
            "sentiment_label": "贪婪" if profit_effect > 1 else ("恐慌" if profit_effect < -1 else "中性")
        }
    
    def get_market_sentiment_data(self, symbol, stock_data=None):
        """
        获取完整的市场情绪分析数据
        
        Args:
            symbol: 股票代码
            stock_data: 股票历史数据（如果已有）
            
        Returns:
            dict: 包含各类市场情绪指标的字典
        """
        sentiment_data = {
            "symbol": symbol,
            "arbr_data": None,          # ARBR指标数据
            "market_index": None,       # 大盘指数数据
            "sector_index": None,       # 板块指数数据
            "turnover_rate": None,      # 换手率数据
            "limit_up_down": None,      # 涨跌停数据
            "margin_trading": None,     # 融资融券数据
            "fear_greed_index": None,   # 市场恐慌贪婪指数
            "data_success": False
        }
        
        try:
            disable_proxy()
            # 判断是否为中国股票
            is_chinese = self._is_chinese_stock(symbol)
            
            if is_chinese:
                
               # 1. 计算ARBR指标
                print("📊 正在计算ARBR情绪指标...")
                
                arbr_data = None
                
                # --- 修改部分开始 ---
                # 优先尝试从 TDX 获取精准的 26日 ARBR
                if self.tdx_fetcher:
                    try:
                        # 实例已经缓存，此处直接调用方法
                        ar, br = self.tdx_fetcher.calculate_arbr_from_tdx(symbol)
                        if ar is not None and br is not None:
                            arbr_data = {
                                "ar": ar, 
                                "br": br, 
                                "source": "tdx_api",
                                "update_time": datetime.now().strftime('%H:%M:%S')
                            }
                            print(f"✅ 已通过 TDX 获取精准 ARBR: AR={ar}, BR={br}")
                    except Exception as e:
                        print(f"⚠️ TDX 计算异常，尝试本地计算: {e}")

                # 如果 TDX 未启用或获取失败，降级使用原有的本地方法
                if not arbr_data:
                    arbr_data = self._calculate_arbr(symbol, stock_data)
                    if arbr_data:
                        arbr_data["source"] = "local_calc"
                # --- 修改部分结束 ---

                if arbr_data:
                    sentiment_data["arbr_data"] = arbr_data

                # 2. 获取换手率数据
                print("📊 正在获取换手率数据...")
                turnover_data = self._get_turnover_rate(symbol)
                print(f"📊 获取到的换手率数据: {turnover_data}")
                if turnover_data:
                    sentiment_data["turnover_rate"] = turnover_data
                
                # # 3. 获取大盘情绪
                # print("📊 正在获取大盘情绪数据...")
                # market_data = self._get_market_index_sentiment()
                # if market_data:
                #     sentiment_data["market_index"] = market_data
                
                # # 4. 获取涨跌停数据
                # print("📊 正在获取涨跌停数据...")
                # limit_data = self._get_limit_up_down_stats()
                # if limit_data:
                #     sentiment_data["limit_up_down"] = limit_data
                

                # # 6. 获取市场恐慌指数
                # print("📊 正在计算市场恐慌指数...")
                # fear_greed = self._get_fear_greed_index()
                # if fear_greed:
                #     sentiment_data["fear_greed_index"] = fear_greed
                # --- 3 & 4 & 6. 大盘/涨跌停/恐慌指数 (本地快照优先) ---
                print("📊 正在进行全市场情绪分析...")
                market_stats = local_data_manager.get_market_sentiment_stats()
                
                if market_stats and market_stats.get('up_count') is not None:
                    # 命中本地快照逻辑
                    sentiment_data["limit_up_down"] = {
                        "up": market_stats['up_count'],
                        "down": market_stats['down_count'],
                        "limit_up": market_stats.get('limit_up', 0),
                        "source": "local_snapshot"
                    }
                    sentiment_data["fear_greed_index"] = market_stats.get('sentiment_label', "未知")
                    sentiment_data["market_index"] = {
                        "avg_turnover": market_stats.get('avg_turnover', 0)
                    }
                    print(f"✅ 已分析本地快照: 上涨{market_stats['up_count']} / 下跌{market_stats['down_count']}")
                else:
                    # 本地快照失效，降级去网上拿
                    print("⚠️ 本地快照缺失，尝试在线获取大盘情绪...")
                    sentiment_data["market_index"] = self._get_market_index_sentiment()
                    sentiment_data["limit_up_down"] = self._get_limit_up_down_stats()
                    sentiment_data["fear_greed_index"] = self._get_fear_greed_index()

                sentiment_data["data_success"] = True

                # 5. 获取融资融券数据
                print("📊 正在获取融资融券数据...")
                # margin_data = local_data_manager.get_stock_margin_info(symbol)
                margin_data = None
                print(f"📊 获取到的融资融券数据: {margin_data}")
                if not margin_data:
                    margin_data = self._get_margin_trading_data(symbol)
                if margin_data:
                    sentiment_data["margin_trading"] = margin_data
                
                
                sentiment_data["data_success"] = True
                print("✅ 市场情绪数据获取完成")
            else:
                # 美股的情绪指标（简化版）
                print("ℹ️ 美股暂不支持完整的市场情绪数据")
                sentiment_data["error"] = "美股暂不支持完整的市场情绪数据"
            
        except Exception as e:
            print(f"❌ 获取市场情绪数据失败: {e}")
            sentiment_data["error"] = str(e)
        
        return sentiment_data
    
    def _is_chinese_stock(self, symbol):
        """判断是否为中国股票"""
        return symbol.isdigit() and len(symbol) == 6
    
    def _calculate_arbr(self, symbol, stock_data=None):
        """
        计算ARBR指标
        AR = (N日内(H-O)之和 / N日内(O-L)之和) × 100
        BR = (N日内(H-CY)之和 / N日内(CY-L)之和) × 100
        """
        try:
            # 如果没有提供stock_data，则重新获取（支持akshare和tushare自动切换）
            if stock_data is None or stock_data.empty:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=150)).strftime('%Y%m%d')
                
                # 使用数据源管理器获取数据
                df = data_source_manager.get_stock_hist_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'
                )
                
                if df is None or df.empty:
                    return None
                
                # 数据源管理器返回的数据列名已经是小写，无需重命名
            else:
                # 使用已有数据
                df = stock_data.copy()
                # 确保列名正确
                if 'Open' in df.columns:
                    df = df.rename(columns={
                        'Open': 'open',
                        'Close': 'close',
                        'High': 'high',
                        'Low': 'low',
                        'Volume': 'volume'
                    })
                df = df.reset_index()
                if 'Date' in df.columns:
                    df = df.rename(columns={'Date': 'date'})
            
            # 确保日期列为datetime类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 计算各项差值
            df['HO'] = df['high'] - df['open']    # 最高价-开盘价
            df['OL'] = df['open'] - df['low']     # 开盘价-最低价
            df['HCY'] = df['high'] - df['close'].shift(1)  # 最高价-前收
            df['CYL'] = df['close'].shift(1) - df['low']   # 前收-最低价
            
            # 计算AR指标
            df['AR'] = (df['HO'].rolling(window=self.arbr_period).sum() / 
                       df['OL'].rolling(window=self.arbr_period).sum()) * 100
            
            # 计算BR指标
            df['BR'] = (df['HCY'].rolling(window=self.arbr_period).sum() / 
                       df['CYL'].rolling(window=self.arbr_period).sum()) * 100
            
            # 处理无穷大和空值
            df['AR'] = df['AR'].replace([np.inf, -np.inf], np.nan)
            df['BR'] = df['BR'].replace([np.inf, -np.inf], np.nan)
            
            # 移除空值
            df = df.dropna(subset=['AR', 'BR'])
            
            if df.empty:
                return None
            
            # 获取最新值和统计信息
            latest = df.iloc[-1]
            ar_value = latest['AR']
            br_value = latest['BR']
            
            # 解读ARBR
            interpretation = self._interpret_arbr(ar_value, br_value)
            
            # 生成交易信号
            signals = self._generate_arbr_signals(ar_value, br_value)
            
            # 计算历史统计
            stats = {
                "ar_mean": df['AR'].mean(),
                "ar_std": df['AR'].std(),
                "ar_min": df['AR'].min(),
                "ar_max": df['AR'].max(),
                "br_mean": df['BR'].mean(),
                "br_std": df['BR'].std(),
                "br_min": df['BR'].min(),
                "br_max": df['BR'].max(),
            }
            
            # 计算信号统计
            df['ar_signal'] = 0
            df['br_signal'] = 0
            df.loc[df['AR'] > 150, 'ar_signal'] = -1
            df.loc[df['AR'] < 70, 'ar_signal'] = 1
            df.loc[df['BR'] > 300, 'br_signal'] = -1
            df.loc[df['BR'] < 50, 'br_signal'] = 1
            df['combined_signal'] = df['ar_signal'] + df['br_signal']
            
            buy_signals = len(df[df['combined_signal'] > 0])
            sell_signals = len(df[df['combined_signal'] < 0])
            neutral_signals = len(df) - buy_signals - sell_signals
            
            signal_stats = {
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "neutral_signals": neutral_signals,
                "total_signals": len(df),
                "buy_ratio": f"{buy_signals/len(df)*100:.1f}%" if len(df) > 0 else "0%",
                "sell_ratio": f"{sell_signals/len(df)*100:.1f}%" if len(df) > 0 else "0%"
            }
            
            return {
                "latest_ar": float(ar_value),
                "latest_br": float(br_value),
                "interpretation": interpretation,
                "signals": signals,
                "statistics": stats,
                "signal_statistics": signal_stats,
                "calculation_date": latest.get('date', datetime.now()).strftime('%Y-%m-%d') if pd.notna(latest.get('date')) else datetime.now().strftime('%Y-%m-%d'),
                "period": self.arbr_period
            }
            
        except Exception as e:
            print(f"计算ARBR指标失败: {e}")
            return None
    
    def _interpret_arbr(self, ar_value, br_value):
        """解读ARBR数值的含义"""
        interpretation = []
        
        # AR指标解读
        if ar_value > 180:
            interpretation.append("AR极度超买（>180），市场过热，风险极高，建议谨慎")
        elif ar_value > 150:
            interpretation.append("AR超买（>150），市场情绪过热，注意回调风险")
        elif ar_value < 40:
            interpretation.append("AR极度超卖（<40），市场过冷，可能存在机会")
        elif ar_value < 70:
            interpretation.append("AR超卖（<70），市场情绪低迷，可关注反弹机会")
        else:
            interpretation.append(f"AR处于正常区间（{ar_value:.2f}），市场情绪相对平稳")
        
        # BR指标解读
        if br_value > 400:
            interpretation.append("BR极度超买（>400），投机情绪过热，警惕泡沫")
        elif br_value > 300:
            interpretation.append("BR超买（>300），投机情绪旺盛，注意风险")
        elif br_value < 30:
            interpretation.append("BR极度超卖（<30），投机情绪冰点，可能触底")
        elif br_value < 50:
            interpretation.append("BR超卖（<50），投机情绪低迷，关注企稳信号")
        else:
            interpretation.append(f"BR处于正常区间（{br_value:.2f}），投机情绪适中")
        
        # ARBR关系解读
        if ar_value > 100 and br_value > 100:
            interpretation.append("多头力量强劲（AR>100且BR>100），但需警惕过热风险")
        elif ar_value < 100 and br_value < 100:
            interpretation.append("空头力量占优（AR<100且BR<100），市场情绪偏空")
        
        if ar_value > br_value:
            interpretation.append("人气指标强于意愿指标（AR>BR），市场基础较好，投资者信心相对稳定")
        else:
            interpretation.append("意愿指标强于人气指标（BR>AR），投机性较强，需注意资金稳定性")
        
        return interpretation
    
    def _generate_arbr_signals(self, ar_value, br_value):
        """生成ARBR交易信号"""
        signals = []
        signal_strength = 0
        
        # AR信号
        if ar_value > 150:
            signals.append("AR卖出信号")
            signal_strength -= 1
        elif ar_value < 70:
            signals.append("AR买入信号")
            signal_strength += 1
        
        # BR信号
        if br_value > 300:
            signals.append("BR卖出信号")
            signal_strength -= 1
        elif br_value < 50:
            signals.append("BR买入信号")
            signal_strength += 1
        
        # 综合信号
        if signal_strength >= 2:
            overall = "强烈买入信号"
        elif signal_strength == 1:
            overall = "买入信号"
        elif signal_strength == -1:
            overall = "卖出信号"
        elif signal_strength <= -2:
            overall = "强烈卖出信号"
        else:
            overall = "中性信号"
        
        return {
            "individual_signals": signals if signals else ["中性"],
            "overall_signal": overall,
            "signal_strength": signal_strength
        }
    
    def _get_turnover_rate(self, symbol):
        print(f"📊 正在获取换手率数据...")
        # --- 1. Local 获取 ---
        source_name = "Local"
        stock_info = local_data_manager.get_stock_info(symbol)
        turnover_rate = None
        if stock_info:
            turnover_rate = stock_info.get('turnover_rate')
            name = stock_info.get('name')
            price = stock_info.get('close')
            print(f"{name} ({symbol}) -> 现价: {price}, 换手率: {turnover_rate}%")
        else:
            print("本地数据未命中")
        # --- 2. Akshare 兜底 ---
        if turnover_rate is None:
            try:
                print(f"   [Akshare] 正在获取实时数据...")
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    # Akshare 的 symbol 通常不带后缀
                    clean_symbol = re.sub(r'[^0-9]', '', symbol)
                    stock_data = df[df['代码'] == clean_symbol]
                    if not stock_data.empty:
                        turnover_rate = stock_data.iloc[0].get('换手率', None)
                        source_name = "Akshare"
                        print(f"   [Akshare] ✅ 获取成功: {turnover_rate}%")
            except Exception as e:
                print(f"   [Akshare] ❌ 失败: {e}")

        # --- 3. Tushare 最终尝试 ---
        if turnover_rate is None and data_source_manager.tushare_available:
            print(f"   [Tushare] 正在获取换手率数据（备用数据源）...")
            ts_code = data_source_manager._convert_to_ts_code(symbol)
            
            # 获取最近一个交易日的数据
            df = data_source_manager.tushare_api.daily_basic(
                ts_code=ts_code,
                trade_date=datetime.now().strftime('%Y%m%d')
            )
                        

        # --- 4. 统一解读与返回 ---
        if turnover_rate is not None:
            try:
                val = float(turnover_rate)
                if val > 20: interpretation = "换手率极高（>20%），资金活跃度极高"
                elif val > 10: interpretation = "换手率较高（>10%），交易活跃"
                elif val > 5: interpretation = "换手率正常（5%-10%），交易适中"
                elif val > 2: interpretation = "换手率偏低（2%-5%），交易清淡"
                else: interpretation = "换手率很低（<2%），交易清淡"
                
                return {
                    "current_turnover_rate": val,
                    "interpretation": interpretation,
                    "source": source_name
                }
            except:
                return {"current_turnover_rate": turnover_rate, "interpretation": "数据格式异常", "source": source_name}
        return None
    
    def _get_market_index_sentiment(self):
        """获取大盘指数情绪（支持akshare和tushare自动切换）"""
        try:
            # 优先使用akshare获取上证指数实时数据
            print(f"   [Akshare] 正在获取大盘指数数据...")
            # 使用正确的symbol参数
            print("正在获取上证指数数据...")
            df = ak.stock_zh_index_spot_em(symbol="上证系列指数")
            if df is not None and not df.empty:
                # 查找上证指数（代码为000001）
                sh_index = df[df['代码'] == '000001']
                if not sh_index.empty:
                    row = sh_index.iloc[0]
                    change_pct = row.get('涨跌幅', 0)
                    
                    # 获取涨跌家数
                    try:
                        market_summary = ak.stock_zh_a_spot_em()
                        if market_summary is not None and not market_summary.empty:
                            up_count = len(market_summary[market_summary['涨跌幅'] > 0])
                            down_count = len(market_summary[market_summary['涨跌幅'] < 0])
                            total_count = len(market_summary)
                            flat_count = total_count - up_count - down_count
                            
                            # 计算市场情绪指数
                            sentiment_score = (up_count - down_count) / total_count * 100
                            
                            # 解读市场情绪
                            if sentiment_score > 30:
                                sentiment = "市场情绪极度乐观"
                            elif sentiment_score > 10:
                                sentiment = "市场情绪偏多"
                            elif sentiment_score > -10:
                                sentiment = "市场情绪中性"
                            elif sentiment_score > -30:
                                sentiment = "市场情绪偏空"
                            else:
                                sentiment = "市场情绪极度悲观"
                            
                            print(f"   [Akshare] ✅ 成功获取大盘数据")
                            return {
                                "index_name": "上证指数",
                                "change_percent": change_pct,
                                "up_count": up_count,
                                "down_count": down_count,
                                "flat_count": flat_count,
                                "total_count": total_count,
                                "sentiment_score": f"{sentiment_score:.2f}",
                                "sentiment_interpretation": sentiment
                            }
                    except Exception as e:
                        print(f"   [Akshare] 获取涨跌家数失败: {e}")
                    
                    print(f"   [Akshare] ✅ 成功获取指数涨跌幅")
                    return {
                        "index_name": "上证指数",
                        "change_percent": change_pct
                    }
        except Exception as e:
            print(f"   [Akshare] ❌ 获取大盘指数失败: {e}")
            
            # akshare失败，尝试tushare
            if data_source_manager.tushare_available:
                try:
                    print(f"   [Tushare] 正在获取大盘指数数据（备用数据源）...")
                    
                    # 获取上证指数数据
                    df = data_source_manager.tushare_api.index_daily(
                        ts_code='000001.SH',
                        start_date=datetime.now().strftime('%Y%m%d'),
                        end_date=datetime.now().strftime('%Y%m%d')
                    )
                    
                    if df is not None and not df.empty:
                        row = df.iloc[0]
                        change_pct = row.get('pct_chg', 0)
                        
                        print(f"   [Tushare] ✅ 成功获取大盘指数涨跌幅: {change_pct}%")
                        return {
                            "index_name": "上证指数",
                            "change_percent": change_pct
                        }
                except Exception as te:
                    print(f"   [Tushare] ❌ 获取失败: {te}")
        
        return None

    # def _get_market_index_sentiment(self):
    #     """升级版：带本地 Feather 缓存的大盘指数情绪获取"""
        
    #     def _fetch():
    #         """原始抓取逻辑：仅在缓存失效时执行"""
    #         print("🌐 [Network] 正在从网络抓取大盘情绪数据...")
    #         try:
    #             disable_proxy()
    #             # 1. 优先使用 akshare 获取数据
    #             print(f"   [Akshare] 正在获取大盘指数数据...")
    #             df = ak.stock_zh_index_spot_em(symbol="上证系列指数")
                
    #             if df is not None and not df.empty:
    #                 sh_index = df[df['代码'] == '000001']
    #                 if not sh_index.empty:
    #                     row = sh_index.iloc[0]
    #                     change_pct = row.get('涨跌幅', 0)
                        
    #                     # 2. 获取全市场摘要（计算涨跌家数，这一步最耗时，缓存收益最高）
    #                     try:
    #                         market_summary = ak.stock_zh_a_spot_em()
    #                         if market_summary is not None and not market_summary.empty:
    #                             up_count = int(len(market_summary[market_summary['涨跌幅'] > 0]))
    #                             down_count = int(len(market_summary[market_summary['涨跌幅'] < 0]))
    #                             total_count = int(len(market_summary))
    #                             flat_count = total_count - up_count - down_count
                                
    #                             # 计算分数
    #                             sentiment_score = (up_count - down_count) / total_count * 100
                                
    #                             # 解读
    #                             if sentiment_score > 30: sentiment = "市场情绪极度乐观"
    #                             elif sentiment_score > 10: sentiment = "市场情绪偏多"
    #                             elif sentiment_score > -10: sentiment = "市场情绪中性"
    #                             elif sentiment_score > -30: sentiment = "市场情绪偏空"
    #                             else: sentiment = "市场情绪极度悲观"
                                
    #                             print(f"   [Akshare] ✅ 成功获取全市场统计数据")
    #                             return {
    #                                 "index_name": "上证指数",
    #                                 "change_percent": float(change_pct),
    #                                 "up_count": up_count,
    #                                 "down_count": down_count,
    #                                 "flat_count": flat_count,
    #                                 "total_count": total_count,
    #                                 "sentiment_score": f"{sentiment_score:.2f}",
    #                                 "sentiment_interpretation": sentiment
    #                             }
    #                     except Exception as e:
    #                         print(f"   [Akshare] 获取涨跌家数子流程失败: {e}")
                        
    #                     return {
    #                         "index_name": "上证指数",
    #                         "change_percent": float(change_pct)
    #                     }
    #         except Exception as e:
    #             print(f"   [Akshare] 主流程失败: {e}")
                
    #             # 3. 备用数据源 Tushare
    #             if data_source_manager.tushare_available:
    #                 try:
    #                     print(f"   [Tushare] 正在获取备用数据...")
    #                     df_ts = data_source_manager.tushare_api.index_daily(
    #                         ts_code='000001.SH',
    #                         start_date=datetime.now().strftime('%Y%m%d'),
    #                         end_date=datetime.now().strftime('%Y%m%d')
    #                     )
    #                     if not df_ts.empty:
    #                         row = df_ts.iloc[0]
    #                         return {
    #                             "index_name": "上证指数",
    #                             "change_percent": float(row.get('pct_chg', 0))
    #                         }
    #                 except Exception as te:
    #                     print(f"   [Tushare] ❌ 获取失败: {te}")
            
    #         return None

    #     # 调用通用的缓存逻辑（prefix 为 "market_index"）
    #     return self._get_data_with_cache("market_index", _fetch)

    
    def _get_limit_up_down_stats(self):
        """升级版：带缓存的涨跌停统计"""
        def _fetch():
            try:
                disable_proxy()
                # 获取今日涨停和跌停统计
                today = datetime.now().strftime('%Y%m%d')
                
                # 获取涨停股票
                try:
                    limit_up_df = ak.stock_zt_pool_em(date=today)
                    limit_up_count = len(limit_up_df) if limit_up_df is not None and not limit_up_df.empty else 0
                except:
                    limit_up_count = 0
                
                # 获取跌停股票
                try:
                    limit_down_df = ak.stock_zt_pool_dtgc_em(date=today)
                    limit_down_count = len(limit_down_df) if limit_down_df is not None and not limit_down_df.empty else 0
                except:
                    limit_down_count = 0
                
                # 计算涨跌停比例
                if limit_up_count + limit_down_count > 0:
                    limit_ratio = limit_up_count / (limit_up_count + limit_down_count) * 100
                else:
                    limit_ratio = 50
                
                # 解读涨跌停情况
                if limit_ratio > 70:
                    interpretation = "涨停股远多于跌停股，市场情绪火热"
                elif limit_ratio > 60:
                    interpretation = "涨停股多于跌停股，市场情绪较好"
                elif limit_ratio > 40:
                    interpretation = "涨跌停数量相当，市场情绪分化"
                elif limit_ratio > 30:
                    interpretation = "跌停股多于涨停股，市场情绪较弱"
                else:
                    interpretation = "跌停股远多于涨停股，市场情绪低迷"
                
                return {
                    "limit_up_count": limit_up_count,
                    "limit_down_count": limit_down_count,
                    "limit_ratio": f"{limit_ratio:.1f}%",
                    "interpretation": interpretation,
                    "date": today
                }
            except Exception as e:
                print(f"获取涨跌停数据失败: {e}")
            return None
            # ... (保持原代码抓取逻辑不变)
            print("🌐 [Network] 正在从网络抓取涨跌停数据...")

            return {"limit_up_count": 50, "limit_down_count": 5, "limit_ratio": "90%"}

        return self._get_data_with_cache("limit_stats", _fetch)
        
    
    def _get_margin_trading_data(self, symbol):
        """获取融资融券数据"""
        try:
            # 获取个股融资融券数据（尝试多个API）
            try:
                disable_proxy()
                # 方法1：获取沪深融资融券明细
                df = ak.stock_margin_underlying_info_szse(date=datetime.now().strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    stock_data = df[df['证券代码'] == symbol]
                    if not stock_data.empty:
                        latest = stock_data.iloc[0]
                        
                        margin_balance = latest.get('融资余额', 0)
                        short_balance = latest.get('融券余额', 0)
                        
                        # 解读融资融券
                        interpretation = []
                        if margin_balance > short_balance * 10:
                            interpretation.append("融资余额远大于融券余额，投资者看多情绪强")
                        elif margin_balance > short_balance * 3:
                            interpretation.append("融资余额大于融券余额，投资者偏看多")
                        else:
                            interpretation.append("融资融券相对平衡")
                        
                        return {
                            "margin_balance": margin_balance,
                            "short_balance": short_balance,
                            "interpretation": interpretation,
                            "date": datetime.now().strftime('%Y-%m-%d')
                        }
            except:
                pass
            
            # 方法2：获取融资融券汇总数据
            try:
                df = ak.stock_margin_szsh()
                if df is not None and not df.empty:
                    # 获取最新数据
                    latest = df.iloc[-1]
                    return {
                        "margin_balance": latest.get('融资余额', None),
                        "short_balance": latest.get('融券余额', None),
                        "interpretation": ["市场整体融资融券数据"],
                        "date": latest.get('交易日期', None)
                    }
            except:
                pass
                
        except Exception as e:
            print(f"获取融资融券数据失败: {e}")
        return None
    
    def _get_fear_greed_index(self):
        """升级版：恐慌贪婪指数"""
        disable_proxy()
        def fetch_logic():
            # 这里的计算通常涉及全市场 scan，耗时较长
            try:
                # 基于多个市场指标计算恐慌贪婪指数
                # 1. 涨跌家数比例
                # 2. 涨跌停比例
                # 3. 成交量变化
                
                score = 50  # 基准分数
                factors = []
                
                # 获取涨跌家数
                try:
                    market_summary = ak.stock_zh_a_spot_em()
                    if market_summary is not None and not market_summary.empty:
                        up_count = len(market_summary[market_summary['涨跌幅'] > 0])
                        down_count = len(market_summary[market_summary['涨跌幅'] < 0])
                        total = len(market_summary)
                        
                        up_ratio = up_count / total
                        # 根据涨跌家数比例调整分数（权重30%）
                        score += (up_ratio - 0.5) * 60
                        factors.append(f"涨跌家数比例: {up_ratio:.1%}")
                except:
                    pass
                
                # 确保分数在0-100之间
                score = max(0, min(100, score))
                
                # 解读恐慌贪婪指数
                if score >= 75:
                    level = "极度贪婪"
                    interpretation = "市场情绪极度乐观，投资者贪婪，需警惕回调风险"
                elif score >= 60:
                    level = "贪婪"
                    interpretation = "市场情绪乐观，投资者偏向贪婪"
                elif score >= 40:
                    level = "中性"
                    interpretation = "市场情绪中性，投资者相对理性"
                elif score >= 25:
                    level = "恐慌"
                    interpretation = "市场情绪悲观，投资者偏向恐慌"
                else:
                    level = "极度恐慌"
                    interpretation = "市场情绪极度悲观，投资者恐慌，可能存在超卖机会"
                
                return {
                    "score": f"{score:.1f}",
                    "level": level,
                    "interpretation": interpretation,
                    "factors": factors
                }
            except Exception as e:
                print(f"计算恐慌贪婪指数失败: {e}")
            return None
            print("🌐 [Network] 正在重新计算全市场恐慌贪婪指数...")
            return {"score": "65.5", "level": "贪婪", "interpretation": "市场情绪乐观"}

        return self._get_data_with_cache("fear_greed", fetch_logic)
       
    
    def format_sentiment_data_for_ai(self, sentiment_data):
        """
        将市场情绪数据格式化为适合AI阅读的文本
        """
        if not sentiment_data or not sentiment_data.get("data_success"):
            return "未能获取市场情绪数据"
        
        text_parts = []
        
        # ARBR指标
        if sentiment_data.get("arbr_data"):
            arbr = sentiment_data["arbr_data"]
            # --- 关键修复点：兼容多个可能的键名，并提供 0 兜底 ---
            ar_val = arbr.get('ar') or arbr.get('latest_ar') or 0
            br_val = arbr.get('br') or arbr.get('latest_br') or 0
            
            # 使用 float() 确保数值类型，避免 NoneType 报错
            text_parts.append(f"""
【ARBR市场情绪指标】
- 数据来源：{arbr.get('source', '未知')}
- 计算周期：{arbr.get('period', 26)}日
- AR值：{float(ar_val):.2f}（人气指标）
- BR值：{float(br_val):.2f}（意愿指标）
- 信号：{arbr.get('signals', {}).get('overall_signal', '无')}
- 解读：
{chr(10).join(['  * ' + str(item) for item in arbr.get('interpretation', ['暂无深度解读'])])}
""")
        
        # 换手率 (增加 None 保护)
        if sentiment_data.get("turnover_rate"):
            turnover = sentiment_data["turnover_rate"]
            # 兼容字典格式或直接数值格式
            rate = turnover.get('current_turnover_rate') if isinstance(turnover, dict) else turnover
            text_parts.append(f"""
【换手率数据】
- 当前换手率：{rate or 0}%
- 解读：{turnover.get('interpretation', '正常') if isinstance(turnover, dict) else '暂无解读'}
""")
        
        # 大盘情绪 (优化合并你的本地快照数据)
        if sentiment_data.get("market_index") or sentiment_data.get("limit_up_down"):
            limit = sentiment_data.get("limit_up_down", {})
            market = sentiment_data.get("market_index", {})
            
            text_parts.append(f"""
【大盘市场情绪 (全市场快照)】
- 涨家数：{limit.get('up', 0)}只
- 跌家数：{limit.get('down', 0)}只
- 涨停数：{limit.get('limit_up', 0)}只
- 市场状态：{sentiment_data.get('fear_greed_index', '中性')}
- 平均换手：{market.get('avg_turnover', '未知')}
""")
        
        # 融资融券
        if sentiment_data.get("margin_trading"):
            margin = sentiment_data["margin_trading"]
            text_parts.append(f"""
【融资融券数据】
- 融资买入额：{margin.get('margin_buy', '未获取')}
- 解读：{'; '.join(margin.get('interpretation', ['暂无解读']))}
""")
        
        return "\n".join(text_parts)

    def get_god_view_info(self, symbol: str):
        """
        [上帝视角] 利用本地 120+ 字段底数，缝合 TDX 实时行情
        """
        clean_symbol = symbol.zfill(6)
        
        # 1. 获取实时“变量” (TDX API)
        # 这里我们只取最核心的：现价、成交量、涨跌幅
        quote = self.tdx_fetcher.get_realtime_quote(clean_symbol)
        if not quote:
            return {"error": "TDX接口响应超时"}

        # 2. 获取本地“全量底数” (你的 120+ 字段字典)
        # 假设你 load_data 时已经把这些字段存入了 self.stock_dict
        local = self.data_source_manager.get_stock_info(clean_symbol
        if not local:
            return {"error": "本地数据库未匹配到该代码"}

        # 3. 核心计算：用实时价格更新关键指标
        price = quote['current_price']
        total_shares = local.get('total_shares_bn', 0) # 对应你的“总股本(亿)”
        active_shares = local.get('active_shares_bn', 0) # 对应你的“流通股(亿)”
        
        # 4. 组装 AI 深度分析字典
        # 我们把字段分为：实时、基本面、财务、技术形态
        full_stitched = {
            # --- 实时动态区 ---
            "code": clean_symbol,
            "name": local.get('name'),
            "price": price,
            "pct_chg": quote['change_pct'],
            "turnover_rate": round((quote['volume'] * 100) / (active_shares * 10**8) * 100, 2) if active_shares else 0,
            "market_cap": round(price * total_shares, 2), # 实时总市值
            
            # --- 深度背景 (来自你提供的表头) ---
            "industry": local.get('industry'),      # 细分行业
            "region": local.get('地区'),
            "list_date": local.get('list_date'),
            
            # --- 财务稳健度 ---
            "pe_ttm": local.get('pe_ttm'),          # 市盈(TTM)
            "pb": local.get('市净率'),
            "debt_ratio": local.get('资产负债率%'),
            "gross_margin": local.get('毛利率%'),
            "roe": local.get('净益率%'),             # 净资产收益率
            
            # --- 筹码与形态 ---
            "shareholders": local.get('股东人数'),
            "avg_hold": local.get('人均持股'),
            "short_term_shape": local.get('短期形态'), # 连涨天、短期形态等
            "main_net_ratio": local.get('主力净比%'),
            
            # --- 核心更新 ---
            "last_update": quote['update_time']
        }

        return full_stitched
# 测试函数
if __name__ == "__main__":
    print("测试市场情绪数据获取...")
    fetcher = MarketSentimentDataFetcher()
    
    # # 测试平安银行
    # symbol = "002993"
    # print(f"\n正在获取 {symbol} 的市场情绪数据...")
    
    # sentiment_data = fetcher.get_market_sentiment_data(symbol)

    # print("\n获取的市场情绪数据:",sentiment_data)
    
    # if sentiment_data.get("data_success"):
    #     print("市场情绪数据获取成功！")
    #     print("="*60)
        
    #     formatted_text = fetcher.format_sentiment_data_for_ai(sentiment_data)
    #     print(formatted_text)
    # else:
    #     print(f"\n获取失败: {sentiment_data.get('error', '未知错误')}")
    # 测试上帝视角
    symbol = "002993"
    print(f"\n正在获取 {symbol} 的上帝视角信息...")
    god_view_info = fetcher.get_god_view_info(symbol)
    print("\n上帝视角信息:", god_view_info)
