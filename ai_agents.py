from llm_client import LLMClient
from typing import Dict, Any
import time
import config

class StockAnalysisAgents:
    """股票分析AI智能体集合"""
    
    def __init__(self, model=None):
        self.model = model or config.DEFAULT_MODEL_NAME
        self.llm_client = LLMClient(model=self.model)
        
    def technical_analyst_agent(self, stock_info: Dict, stock_data: Any, indicators: Dict) -> Dict[str, Any]:
        """技术面分析智能体"""
        print("🔍 技术分析师正在分析中...")
        time.sleep(1)  # 模拟分析时间
        
        analysis = self.llm_client.technical_analysis(stock_info, stock_data, indicators)
        
        return {
            "agent_name": "技术分析师",
            "agent_role": "负责技术指标分析、图表形态识别、趋势判断",
            "analysis": analysis,
            "focus_areas": ["技术指标", "趋势分析", "支撑阻力", "交易信号"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fundamental_analyst_agent(self, stock_info: Dict, financial_data: Dict = None, quarterly_data: Dict = None) -> Dict[str, Any]:
        """基本面分析智能体"""
        print("📊 基本面分析师正在分析中...")
        
        # 如果有季报数据，显示数据来源
        if quarterly_data and quarterly_data.get('data_success'):
            income_count = quarterly_data.get('income_statement', {}).get('periods', 0) if quarterly_data.get('income_statement') else 0
            balance_count = quarterly_data.get('balance_sheet', {}).get('periods', 0) if quarterly_data.get('balance_sheet') else 0
            cash_flow_count = quarterly_data.get('cash_flow', {}).get('periods', 0) if quarterly_data.get('cash_flow') else 0
            print(f"   ✓ 已获取季报数据：利润表{income_count}期，资产负债表{balance_count}期，现金流量表{cash_flow_count}期")
        else:
            print("   ⚠ 未获取到季报数据，将基于基本财务数据分析")
        
        time.sleep(1)
        
        analysis = self.llm_client.fundamental_analysis(stock_info, financial_data, quarterly_data)
        
        return {
            "agent_name": "基本面分析师", 
            "agent_role": "负责公司财务分析、行业研究、估值分析",
            "analysis": analysis,
            "focus_areas": ["财务指标", "行业分析", "公司价值", "成长性", "季报趋势"],
            "quarterly_data": quarterly_data,  # 保存季报数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def fund_flow_analyst_agent(self, stock_info: Dict, indicators: Dict, fund_flow_data: Dict = None) -> Dict[str, Any]:
        """资金面分析智能体"""
        print("💰 资金面分析师正在分析中...")
        
        # 如果有资金流向数据，显示数据来源
        if fund_flow_data and fund_flow_data.get('data_success'):
            print("   ✓ 已获取资金流向数据（akshare数据源）")
        else:
            print("   ⚠ 未获取到资金流向数据，将基于技术指标分析")
        
        time.sleep(1)
        
        analysis = self.llm_client.fund_flow_analysis(stock_info, indicators, fund_flow_data)
        
        return {
            "agent_name": "资金面分析师",
            "agent_role": "负责资金流向分析、主力行为研究、市场情绪判断", 
            "analysis": analysis,
            "focus_areas": ["资金流向", "主力动向", "市场情绪", "流动性"],
            "fund_flow_data": fund_flow_data,  # 保存资金流向数据以供后续使用
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    def risk_analysis(self, stock_info: Dict, indicators: Dict, risk_data: Any) -> str:
        """全面深度风险评估"""
        
        # 将原始风险数据（如解禁、减持、立案等）转为文字
        risk_data_text = str(risk_data) if risk_data else "暂无实时风险监控数据（注意：数据缺失可能隐藏潜在风险）"
        
        prompt = f"""
            你是一名资深风险管理专家。请基于以下信息进行全面深度的风险评估：

            【基本信息】
            - 股票代码：{stock_info.get('symbol', None)}
            - 股票名称：{stock_info.get('name', None)}
            - 当前价格：{stock_info.get('current_price', None)}
            - Beta系数：{stock_info.get('beta', None)}
            - 52周最高：{stock_info.get('52_week_high', None)}
            - 52周最低：{stock_info.get('52_week_low', None)}

            【技术指标】
            - RSI：{indicators.get('rsi', None)}
            - 布林带位置：当前价格相对于上下轨的位置（参考价格与布林线数据）
            - 波动率：参考当前价格与52周高低点的偏离度

            【原始风险监控数据（问财实时数据）】
            {risk_data_text}

            ⚠️ 重要提示：以上风险数据是完整原始数据，请你执行以下专家级任务：
            1. 仔细解析记录字段，识别关键点（如限售解禁时间、规模、股东减持意图等）。
            2. 特别关注即将发生的解禁事件和连续减持动作。
            3. 给出量化的评估，而非空泛描述。

            请从以下角度输出评估报告：
            1. **限售解禁风险**（解禁规模、冲击评估）
            2. **股东减持风险**（频率、力度、信心影响）
            3. **重要事件风险**（性质判断、时间维度）
            4. **流动性与波动风险**（买卖盘深度、52周位阶风险）
            5. **综合风险评定**（风险分级：低/中/高）
            6. **核心风控建议**（明确的仓位控制、具体止损位建议、风险规避信号）
            """
        messages = [
                    {"role": "system", "content": "你是一名严谨的首席风险官（CRO）。"},
                    {"role": "user", "content": prompt}
                ]
        analysis = self.llm_client.call_api(messages, max_tokens=3000)
        
        # 3. 返回结构化结果 (就是你问的那段代码)
        import time
        return {
            "agent_name": "风险管理师",
            "agent_role": "负责风险识别、风险评估、风险控制策略制定",
            "analysis": analysis,  # 这里存储了 AI 生成的深度风险报告
            "focus_areas": ["限售解禁风险", "股东减持风险", "重要事件风险", "风险识别", "风险量化", "风险控制", "资产配置"],
            "risk_data": risk_data,  # 极其重要：保留原始数据供其他 Agent 或 UI 校验
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def market_sentiment_agent(self, stock_info: Dict, sentiment_data: Dict = None) -> Dict:
        """
        市场情绪分析师：解读投资者心理与ARBR指标联动
        """
        import time
        print("📈 市场情绪分析师正在捕捉市场温度...")
        
        # 情绪数据格式化处理
        sentiment_data_text = "暂无详细ARBR及情绪指标数据，将基于大盘氛围分析。"
        if sentiment_data and sentiment_data.get('data_success'):
            from market_sentiment_data import MarketSentimentDataFetcher
            fetcher = MarketSentimentDataFetcher()
            sentiment_data_text = f"\n【实时市场情绪数据】\n{fetcher.format_sentiment_data_for_ai(sentiment_data)}"

        sentiment_prompt = f"""
作为市场心理学专家，请基于以下数据对 {stock_info.get('name')} 进行情绪面剖析：

股票背景：{stock_info.get('sector')} 行业 - {stock_info.get('industry')} 细分领域
{sentiment_data_text}

分析要点：
1. **ARBR情绪解析**：解读人气指标AR和意愿指标BR。若BR>AR且同步上升，说明人气汇聚；若BR远超AR后掉头，预警派发。
2. **活跃度与热度**：换手率是否异常放大？当前是“无人问津”还是“散户蜂拥”？
3. **情绪对冲逻辑**：当前情绪是支撑股价上涨，还是已经透支了未来涨幅？
4. **投资建议**：从情绪面给出具体的“贪婪”或“恐惧”操作建议。

请确保结论客观，重点识别“情绪过热”后的退潮风险。
"""
        messages = [
            {"role": "system", "content": "你是一名顶尖的市场情绪分析师，精通行为金融学，擅长捕捉主力诱多与恐慌割肉的情绪拐点。"},
            {"role": "user", "content": sentiment_prompt}
        ]
        
        analysis = self.llm_client.call_api(messages, max_tokens=2000)
        
        return {
            "agent_name": "市场情绪分析师",
            "agent_role": "负责市场心理研究、人气监测及热点追踪",
            "analysis": analysis,
            "focus_areas": ["ARBR指标", "换手率分析", "群体心理", "恐慌贪婪指数"],
            "sentiment_data": sentiment_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def conduct_team_discussion(self, agents_results: Dict[str, Any], stock_info: Dict) -> str:
        """进行团队讨论 - 引入强制反向思维与风险辩论机制"""
        import time
        print(f"🤝 投委会正在对 {stock_info.get('name')} 进行最后博弈与质询...")
        time.sleep(2)
        
        # 收集参与分析的分析师名单和报告
        participants = []
        reports = []
        
        # 这里的 key 需要与你 run_multi_agent_analysis 中 agents_results 的 key 保持一致
        mapping = {
            "technical": "技术分析师",
            "fundamental": "基本面分析师",
            "fund_flow": "资金面分析师",
            "risk_management": "风险管理师",
            "market_sentiment": "市场情绪分析师",
            "news": "新闻分析师"
        }
        
        for key, role_name in mapping.items():
            if key in agents_results:
                participants.append(role_name)
                reports.append(f"【{role_name}报告】\n{agents_results[key].get('analysis', '')}")
        
        all_reports = "\n\n".join(reports)
        
        # 核心：加入“首席质疑官”指令
        discussion_prompt = f"""
现在进入投资决策团队会议。
股票：{stock_info.get('name', None)} ({stock_info.get('symbol', None)})
参会人员：{', '.join(participants)}，以及一名 **[首席质疑官]**。

各席位原始分析报告：
{all_reports}

会议议程要求：
1. **观点对垒**：请模拟一场真实的博弈讨论。不仅要看观点的一致性，更要挖掘分歧。
2. **强制反向思维（魔鬼代言人）**：
   - 会议中必须由 [首席质疑官] 针对目前的乐观共识提出 2-3 条“极端负面假设”。
   - 例如：如果技术面看涨，质疑官必须质询是否为“无量诱多”或“分时骗线”？
   - 如果基本面看好，质疑官必须质询是否存在“行业周期见顶”或“利好兑现”风险？
3. **风控权衡**：风险管理师需针对质疑点，给出如果逻辑错误，最坏会跌到哪里的预判。
4. **达成深度共识**：讨论最终必须明确：在什么条件下维持看多，在什么信号出现时必须立刻撤退。

请以会议纪要的对话形式展现，体现专业团队的逻辑碰撞和反向压测过程。
"""
        
        messages = [
            {"role": "system", "content": "你是一名资深的投委会主席，擅长通过‘辩证法’和‘反向压测’来剔除投资中的虚假繁荣。"},
            {"role": "user", "content": discussion_prompt}
        ]
        
        discussion_result = self.llm_client.call_api(messages, max_tokens=6000)
        
        print("✅ 深度团队讨论与反向压测完成")
        return discussion_result
        """进行团队讨论"""
        print("🤝 分析团队正在进行综合讨论...")
        time.sleep(2)
        
        # 收集参与分析的分析师名单和报告
        participants = []
        reports = []
        
        if "technical" in agents_results:
            participants.append("技术分析师")
            reports.append(f"【技术分析师报告】\n{agents_results['technical'].get('analysis', '')}")
        
        if "fundamental" in agents_results:
            participants.append("基本面分析师")
            reports.append(f"【基本面分析师报告】\n{agents_results['fundamental'].get('analysis', '')}")
        
        if "fund_flow" in agents_results:
            participants.append("资金面分析师")
            reports.append(f"【资金面分析师报告】\n{agents_results['fund_flow'].get('analysis', '')}")
        
        if "risk_management" in agents_results:
            participants.append("风险管理师")
            reports.append(f"【风险管理师报告】\n{agents_results['risk_management'].get('analysis', '')}")
        
        if "market_sentiment" in agents_results:
            participants.append("市场情绪分析师")
            reports.append(f"【市场情绪分析师报告】\n{agents_results['market_sentiment'].get('analysis', '')}")
        
        if "news" in agents_results:
            participants.append("新闻分析师")
            reports.append(f"【新闻分析师报告】\n{agents_results['news'].get('analysis', '')}")
        
        # 组合所有报告
        all_reports = "\n\n".join(reports)
        
        discussion_prompt = f"""
现在进行投资决策团队会议，参会人员包括：{', '.join(participants)}。

股票：{stock_info.get('name', None)} ({stock_info.get('symbol', None)})

各分析师报告：

{all_reports}

请模拟一场真实的投资决策会议讨论：
1. 各分析师观点的一致性和分歧
2. 不同维度分析的权重考量
3. 风险收益评估
4. 投资时机判断
5. 策略制定思路
6. 达成初步共识

请以对话形式展现讨论过程，体现专业团队的思辨过程。
注意：只讨论参与分析的分析师的观点。
"""
        
        messages = [
            {"role": "system", "content": "你需要模拟一场专业的投资团队讨论会议，体现不同角色的观点碰撞和最终共识形成。"},
            {"role": "user", "content": discussion_prompt}
        ]
        
        discussion_result = self.llm_client.call_api(messages, max_tokens=6000)
        
        print("✅ 团队讨论完成")
        return discussion_result
    
    def make_final_decision(self, discussion_result: str, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
        """制定最终投资决策"""
        print("📋 正在制定最终投资决策...")
        time.sleep(1)
        
        decision = self.llm_client.final_decision(discussion_result, stock_info, indicators)
        
        print("✅ 最终投资决策完成")
        return decision


    def news_analyst_agent(self, stock_info: Dict, news_data: Dict = None) -> Dict[str, Any]:
            """新闻分析智能体 - 强化预期差与利好出货识别"""
            import time
            print("📰 新闻分析师正在深度拆解消息面...")
            
            # 数据获取逻辑
            news_text = "⚠️ 暂无近期重大新闻，将基于行业普遍动态进行推演。"
            if news_data and news_data.get('data_success'):
                from qstock_news_data import QStockNewsDataFetcher
                fetcher = QStockNewsDataFetcher()
                news_text = f"\n【实时新闻数据流】\n{fetcher.format_news_for_ai(news_data)}"

            news_prompt = f"""
    作为专业的新闻分析师，请对 {stock_info.get('name')} 的消息面进行深度穿透分析：

    【背景】行业：{stock_info.get('sector')} | 细分：{stock_info.get('industry')}
    {news_text}

    请从以下硬核维度输出报告：
    1. **核心要点萃取**：按【极重要/重要/一般】对新闻进行优先级排序。
    2. **性质与预期差分析**：
    - 识别该新闻是“突发性惊喜”还是“市场早已预期的旧闻”。
    - 特别预警：是否存在“利好落地即利空（出货）”的盘面风险。
    3. **影响评估（时间维度）**：
    - 短期（1-3天）：对股价脉冲的影响。
    - 长期（3-6个月）：是否改变了公司经营的基本逻辑。
    4. **重大事件连锁反应**：识别新闻背后的产业趋势或政策导向。
    5. **风险提示（重点）**：识别新闻描述中隐藏的“负面潜台词”或“不确定性风险”。
    6. **投资建议**：给出明确的“利好兑现”或“利空出局”信号。

    要求：分析必须剔除软文干扰，直击利益核心。
    """
            messages = [
                {"role": "system", "content": "你是一名冷酷的新闻调研员，擅长识破公司的公关辞令，捕捉那些能让股价剧烈波动的真实商业逻辑。"},
                {"role": "user", "content": news_prompt}
            ]
            
            analysis = self.llm_client.call_api(messages, max_tokens=3000)
            
            return {
                "agent_name": "新闻分析师",
                "agent_role": "负责事件驱动研究、预期差挖掘、舆情陷阱识别",
                "analysis": analysis,
                "focus_areas": ["预期差", "利好出货预警", "重大事件", "舆情反转"],
                "news_data": news_data,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    def run_multi_agent_analysis(self, stock_info: Dict, stock_data: Any, indicators: Dict, 
                                    financial_data: Dict = None, fund_flow_data: Dict = None, 
                                    sentiment_data: Dict = None, news_data: Dict = None,
                                    quarterly_data: Dict = None, risk_data: Dict = None,
                                    enabled_analysts: Dict = None) -> Dict[str, Any]:
            """运行多智能体分析（已修正方法调用匹配）"""
            if enabled_analysts is None:
                enabled_analysts = {
                    'technical': True, 'fundamental': True, 'fund_flow': True,
                    'risk': True, 'sentiment': True, 'news': True
                }
            
            print(f"🚀 启动多智能体分析系统：{stock_info.get('name')} ({stock_info.get('symbol')})")
            print("=" * 50)
            
            agents_results = {}
            
            # 依次调用各个分析师（注意这里的方法名要与类中定义的保持一致）
            if enabled_analysts.get('technical', True):
                agents_results["technical"] = self.technical_analyst_agent(stock_info, stock_data, indicators)
            
            if enabled_analysts.get('fundamental', True):
                agents_results["fundamental"] = self.fundamental_analyst_agent(stock_info, financial_data, quarterly_data)
            
            if enabled_analysts.get('fund_flow', True):
                agents_results["fund_flow"] = self.fund_flow_analyst_agent(stock_info, indicators, fund_flow_data)
            
            # 调用我们刚刚重构好的 risk_analysis 方法
            if enabled_analysts.get('risk', True):
                agents_results["risk_management"] = self.risk_analysis(stock_info, indicators, risk_data)
            
            if enabled_analysts.get('sentiment', True):
                agents_results["market_sentiment"] = self.market_sentiment_agent(stock_info, sentiment_data)
            
            if enabled_analysts.get('news', True):
                agents_results["news"] = self.news_analyst_agent(stock_info, news_data)
            
            print(f"✅ 完成分析，共计 {len(agents_results)} 位分析师出具报告")
            print("=" * 50)
            
            return agents_results