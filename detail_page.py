# detail_page.py
import streamlit as st
import json


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

    # 核心决策区域
    try:
        # 尝试从 record 中获取 final_decision
        final_decision_str = record.get('analysis_records', {}).get('final_decision', '{}')
        final_decision_data = json.loads(final_decision_str)

        if final_decision_data:
            st.header("💡 核心决策")
            
            # 使用 st.columns 和 st.metric 突出显示关键信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("评级", final_decision_data.get("rating", "N/A"))
            with col2:
                st.metric("目标价", final_decision_data.get("target_price", "N/A"))
            with col3:
                st.metric("止损", final_decision_data.get("stop_loss", "N/A"))
            with col4:
                st.metric("仓位", final_decision_data.get("position_size", "N/A"))

            # 操作建议和风险提示使用 expander 或直接显示
            st.markdown(f"**操作建议:** {final_decision_data.get("operation_advice", "暂无")}")
            st.markdown(f"**入场区间:** {final_decision_data.get("entry_range", "暂无")}")
            st.markdown(f"**止盈:** {final_decision_data.get("take_profit", "暂无")}")
            st.markdown(f"**持仓周期:** {final_decision_data.get("holding_period", "暂无")}")
            st.markdown(f"**风险提示:** {final_decision_data.get("risk_warning", "暂无")}")
            st.markdown(f"**信心水平:** {final_decision_data.get("confidence_level", "N/A")}")

            st.divider() # 在核心决策区下方添加分割线

    except json.JSONDecodeError:
        st.warning("核心决策数据解析失败，可能不是有效的JSON格式。")
    except Exception as e:
        st.error(f"处理核心决策时发生错误: {e}")


    # 使用标签页组织内容
    
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

