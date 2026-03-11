"""
风险数据获取模块 - 优化版
1. 强化了数据过滤逻辑，排除非目标股票的干扰
2. 增强了对问财嵌套数据结构的解析能力
"""

import pywencai
import pandas as pd
from typing import Dict, Any, List
import time
import warnings
import os

# 屏蔽pywencai的Node.js警告信息
warnings.filterwarnings('ignore', category=DeprecationWarning)
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
os.environ['NODE_NO_WARNINGS'] = '1'


class RiskDataFetcher:
    """风险数据获取类"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def get_risk_data(self, symbol: str) -> Dict[str, Any]:
        """获取股票风险相关数据"""
        print(f"\n正在获取 {symbol} 的风险数据...")
        
        risk_data = {
            'symbol': symbol,
            'data_success': False,
            'lifting_ban': None,
            'shareholder_reduction': None,
            'important_events': None,
            'error': None
        }
        
        try:
            # 1. 获取限售解禁数据
            print("   查询限售解禁数据...")
            lifting_ban = self._get_lifting_ban_data(symbol)
            risk_data['lifting_ban'] = lifting_ban
            if lifting_ban and lifting_ban.get('has_data'):
                print(f"   获取到限售解禁数据")
            else:
                print(f"   暂无限售解禁数据")
            
            time.sleep(1)
            
            # 2. 获取大股东减持公告
            print("   查询大股东减持公告...")
            reduction = self._get_shareholder_reduction_data(symbol)
            risk_data['shareholder_reduction'] = reduction
            if reduction and reduction.get('has_data'):
                print(f"   获取到大股东减持数据")
            else:
                print(f"   暂无大股东减持数据")
            
            time.sleep(1)
            
            # 3. 获取近期重要事件
            print("   查询近期重要事件...")
            events = self._get_important_events_data(symbol)
            risk_data['important_events'] = events
            if events and events.get('has_data'):
                print(f"   获取到重要事件数据")
            else:
                print(f"   暂无重要事件数据")
            # 成功逻辑判断：只要有一个数据源有真正属于该 symbol 的数据
            if any(risk_data[k].get('has_data') for k in ['lifting_ban', 'shareholder_reduction', 'important_events'] if risk_data[k]):
                risk_data['data_success'] = True
                print(f"风险数据获取完成")
            else:
                print(f"未获取到风险相关数据")
                
        except Exception as e:
            print(f"风险数据获取失败: {str(e)}")
            risk_data['error'] = str(e)
        
        return risk_data

    def _filter_dataframe_by_symbol(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """【新增】核心过滤逻辑：确保数据行中包含目标股票代码，排除噪音"""
        if df is None or df.empty:
            return df
            
        # 寻找包含“代码”字样的列
        code_cols = [c for c in df.columns if '代码' in c]
        if code_cols:
            # 只要有一列匹配代码即可
            mask = df[code_cols[0]].astype(str).str.contains(symbol)
            df = df[mask]
        else:
            # 如果没找到代码列，全行搜索字符串（容错方案）
            mask = df.apply(lambda row: symbol in row.astype(str).values.sum(), axis=1)
            df = df[mask]
        return df

    def _get_lifting_ban_data(self, symbol: str) -> Dict[str, Any]:
        """获取限售解禁数据"""
        result = {'has_data': False, 'query': f"股票代码{symbol}限售解禁列表", 'data': None, 'summary': None}
        try:
            # 问句优化
            response = pywencai.get(query=result['query'], loop=True)
            df_result = self._convert_to_dataframe(response)
            
            # 数据清洗
            df_result = self._filter_dataframe_by_symbol(df_result, symbol)
            
            if df_result is None or df_result.empty:
                return result
            
            result['has_data'] = True
            result['data'] = df_result
            
            # 摘要逻辑增强
            summary = [f"发现 {len(df_result)} 条属于 {symbol} 的解禁记录"]
            time_col = next((c for c in ['解禁时间', '限售解禁日', '解禁日期'] if c in df_result.columns), None)
            
            if time_col:
                for _, row in df_result.head(3).iterrows():
                    info = [f"日期: {row[time_col]}"]
                    if '解禁股数' in row: info.append(f"股数: {row['解禁股数']}")
                    if '股东名称' in row: info.append(f"股东: {row['股东名称']}")
                    summary.append(" | ".join(info))
            result['summary'] = "\n".join(summary)
        except Exception as e:
            result['error'] = str(e)
        return result

    def _get_shareholder_reduction_data(self, symbol: str) -> Dict[str, Any]:
        """获取大股东减持公告数据"""
        result = {'has_data': False, 'query': f"代码{symbol}的大股东减持公告明细", 'data': None, 'summary': None}
        try:
            response = pywencai.get(query=result['query'], loop=True)
            df_result = self._convert_to_dataframe(response)
            
            # 强力过滤：排除类似“海印股份”等噪音
            df_result = self._filter_dataframe_by_symbol(df_result, symbol)
            
            if df_result is None or df_result.empty:
                return result
            
            result['has_data'] = True
            result['data'] = df_result
            
            summary = [f"发现 {len(df_result)} 条属于 {symbol} 的减持公告"]
            date_col = next((c for c in ['公告日期', '减持日期', '时间'] if c in df_result.columns), None)
            
            if date_col:
                for _, row in df_result.head(3).iterrows():
                    info = [f"日期: {row[date_col]}"]
                    if '股东名称' in row: info.append(f"股东: {row['股东名称']}")
                    if '减持比例' in row: info.append(f"比例: {row['减持比例']}")
                    summary.append(" | ".join(info))
            result['summary'] = "\n".join(summary)
        except Exception as e:
            result['error'] = str(e)
        return result

    def _get_important_events_data(self, symbol: str) -> Dict[str, Any]:
        """获取近期重要事件数据"""
        result = {'has_data': False, 'query': f"代码{symbol}最近一个月重要事项", 'data': None, 'summary': None}
        try:
            response = pywencai.get(query=result['query'], loop=True)
            df_result = self._convert_to_dataframe(response)
            df_result = self._filter_dataframe_by_symbol(df_result, symbol)
            
            if df_result is None or df_result.empty:
                return result
            
            result['has_data'] = True
            result['data'] = df_result
            summary = [f"发现 {len(df_result)} 条重要事项"]
            result['summary'] = "\n".join(summary)
        except Exception as e:
            result['error'] = str(e)
        return result

    def _convert_to_dataframe(self, result) -> pd.DataFrame:
        """增强版：处理pywencai多重嵌套和多Tab结果"""
        try:
            if result is None: return None
            
            # 1. 如果返回的是列表，通常是多Tab结果，遍历找到内容最丰富的DataFrame
            if isinstance(result, list):
                if not result: return None
                # 寻找行数最多的DataFrame作为主要数据源
                dfs = [self._convert_to_dataframe(item) for item in result if item is not None]
                dfs = [d for d in dfs if d is not None and not d.empty]
                return max(dfs, key=len) if dfs else None

            # 2. 如果是字典类型
            if isinstance(result, dict):
                # 处理常见的 tableV1 嵌套
                if 'tableV1' in result:
                    return self._convert_to_dataframe(result['tableV1'])
                # 处理单行数据转DF
                try:
                    return pd.DataFrame([result])
                except:
                    return None

            # 3. 如果已经是 DataFrame
            if isinstance(result, pd.DataFrame):
                df_result = result
                if df_result.empty: return None
                
                # 递归处理：如果第一列又是 DataFrame，则继续展开（处理 title_content 嵌套）
                first_col = df_result.columns[0]
                if len(df_result.columns) == 1 and isinstance(df_result.iloc[0][first_col], (pd.DataFrame, list, dict)):
                    inner_data = df_result.iloc[0][first_col]
                    return self._convert_to_dataframe(inner_data)
                
                return df_result
            
            return None
        except Exception as e:
            print(f"   转换DataFrame时出错: {str(e)}")
            return None

    def format_risk_data_for_ai(self, risk_data: Dict[str, Any]) -> str:
        """格式化风险数据供AI分析使用 - 修复版"""
        if not risk_data or not risk_data.get('data_success'):
            return "未获取到有效的风险数据"
        
        formatted_text = []
        symbol = risk_data.get('symbol', '未知代码')
        
        try:
            # 1. 限售解禁数据
            lifting_ban = risk_data.get('lifting_ban')
            if lifting_ban and lifting_ban.get('has_data') and lifting_ban.get('data') is not None:
                formatted_text.append("=" * 30 + f" 【{symbol} 限售解禁风险】 " + "=" * 30)
                df = lifting_ban.get('data')
                # 使用我们自定义的格式化辅助函数
                formatted_text.append(self._format_dataframe_for_ai(df, "限售解禁"))
                formatted_text.append("")
        
            # 2. 大股东减持数据
            reduction = risk_data.get('shareholder_reduction')
            if reduction and reduction.get('has_data') and reduction.get('data') is not None:
                formatted_text.append("=" * 30 + f" 【{symbol} 大股东减持风险】 " + "=" * 30)
                df = reduction.get('data')
                formatted_text.append(self._format_dataframe_for_ai(df, "大股东减持"))
                formatted_text.append("")
        
            # 3. 重要事件数据
            events = risk_data.get('important_events')
            if events and events.get('has_data') and events.get('data') is not None:
                formatted_text.append("=" * 30 + f" 【{symbol} 近期重要事项】 " + "=" * 30)
                df = events.get('data')
                formatted_text.append(self._format_dataframe_for_ai(df, "重要事件"))
                formatted_text.append("")
            
            return "\n".join(formatted_text) if formatted_text else "暂无过滤后的有效风险数据"
            
        except Exception as e:
            return f"格式化风险数据时出错: {str(e)}"
    def _format_dataframe_for_ai(self, df: pd.DataFrame, data_type: str) -> str:
        """将清洗后的DataFrame格式化为AI分析师易读的文本"""
        if df is None or df.empty:
            return f"暂无相关的{data_type}记录。"
            
        lines = []
        # 1. 概览信息
        lines.append(f">>> 已过滤出的{data_type}记录（共 {len(df)} 条）：")
        
        # 2. 识别关键字段（针对不同类型数据优化显示顺序）
        columns = df.columns.tolist()
        
        # 3. 逐行转换（限制前20条，防止由于数据过载导致AI上下文溢出）
        max_rows = min(20, len(df))
        for idx, row in df.head(max_rows).iterrows():
            item_parts = []
            for col in columns:
                val = row[col]
                # 过滤掉无意义的空值，减少AI阅读负担
                if pd.notna(val) and str(val).strip() != "" and str(val).lower() != "nan":
                    # 限制单个字段长度，防止由于超长链接或文本导致的混乱
                    val_str = str(val)[:150] + "..." if len(str(val)) > 150 else str(val)
                    item_parts.append(f"{col}: {val_str}")
            
            lines.append(f"  ({idx + 1}) " + " | ".join(item_parts))
            
        if len(df) > max_rows:
            lines.append(f"  ... 剩余 {len(df) - max_rows} 条记录已省略。")
            
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    fetcher = RiskDataFetcher()
    
    # 测试获取风险数据
    test_symbol = "000001   "
    print(f"测试获取 {test_symbol} 的风险数据...")
    
    risk_data = fetcher.get_risk_data(test_symbol)
    
    print("\n" + "=" * 60)
    print("获取结果:")
    print("=" * 60)
    print(f"数据获取成功: {risk_data['data_success']}")
    
    if risk_data['data_success']:
        print("\n格式化的风险数据:")
        print(fetcher.format_risk_data_for_ai(risk_data))

