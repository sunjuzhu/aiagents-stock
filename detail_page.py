# detail_page.py
import streamlit as st
import json

# def render_stock_detail(record_data):
#     # 解析复杂的 JSON 字符串
#     try:
#         # 如果 record_data 是字符串，解析它；如果是字典则直接用
#         data = json.loads(record_data) if isinstance(record_data, str) else record_data
#         tech_analysis = data.get('technical', {}).get('analysis', "暂无数据")
#         fundamental = data.get('fundamental', {}).get('analysis', "暂无数据")
#     except:
#         st.error("解析数据失败")
#         return

#     # 1. 顶部标题栏
#     st.title(f"📊 {data.get('name', '未知股票')} ({data.get('symbol', '')}) 分析报告")
    
#     col_a, col_b, col_c = st.columns(3)
#     col_a.metric("当前价格", f"¥{data.get('current_price')}")
#     col_b.metric("涨跌幅", f"{data.get('change_percent')}%")
#     col_c.metric("市盈率(PE)", data.get('pe_ratio'))

#     st.divider()

#     # 2. 核心内容展示（使用 Tabs）
#     tab1, tab2, tab3, tab4 = st.tabs(["📈 技术分析", "🏢 基本面", "💰 资金流向", "🎙 会议记录"])
    
#     with tab1:
#         st.markdown(tech_analysis)
    
#     with tab2:
#         st.markdown(fundamental)
        
#     with tab3:
#         fund_data = data.get('fund_flow', {}).get('analysis', "暂无资金面分析")
#         st.markdown(fund_data)
        
#     with tab4:
#         # 这里展示你复制的那段“会议记录”文本
#         st.info("投资决策会议纪要")
#         st.markdown(data.get('meeting_notes', '未记录'))

#     # 3. 底部操作建议卡片
#     st.sidebar.header("🎯 投资建议")
#     advice = data.get('advice', {})
#     st.sidebar.success(f"**建议操作：{advice.get('rating', '观望')}**")
#     st.sidebar.write(f"目标价：{advice.get('target_price', 'N/A')}")
#     st.sidebar.write(f"止损价：{advice.get('stop_loss', 'N/A')}")
#     st.sidebar.warning(f"风险提示：{advice.get('risk_warning', '数据缺失')}")
    
#     if st.sidebar.button("🏠 返回监控列表"):
#         st.query_params.clear() # 清除参数回到主页
#         st.rerun()

def render_full_detail_page(record):
    """渲染全屏分析页面"""
    import json
    
    st.set_page_config(page_title=f"分析详情-{record['stock_name']}", layout="wide")
    
    # 解析你数据中的 JSON 字符串
    try:
        data = json.loads(record['analysis_result'])
        tech_analysis = data.get('technical', {}).get('analysis', '')
        fund_analysis = data.get('fundamental', {}).get('analysis', '')
        flow_analysis = data.get('fund_flow', {}).get('analysis', '')
        risk_analysis = data.get('risk_management', {}).get('analysis', '')
    except:
        st.error("数据解析失败")
        st.write(record['analysis_result'])
        return

    st.title(f"📊 {record['stock_name']} ({record['stock_code']}) 深度分析报告")
    st.caption(f"生成时间：{record['created_at']} | 周期：{record['period']}")
    
    st.divider()
    
    # 使用标签页组织内容
    t1, t2, t3, t4, t5 = st.tabs(["📈 技术面", "🏢 基本面", "💰 资金面", "⚠️ 风险评估", "🎙 会议纪要"])
    
    with t1:
        st.markdown(tech_analysis)
    with t2:
        st.markdown(fund_analysis)
    with t3:
        st.markdown(flow_analysis)
    with t4:
        st.markdown(risk_analysis)
    with t5:
        # 这里展示你复制的那段“会议记录”文本
        st.markdown(record.get('meeting_notes', '暂无会议记录'))
        
    # 侧边栏显示操作建议
    with st.sidebar:
        st.header("🎯 投资决策")
        st.info(f"建议：{record.get('investment_advice', '观察')}")
        if st.button("关闭并返回"):
            st.query_params.clear()
            st.rerun()