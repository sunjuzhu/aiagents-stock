import streamlit as st
import json
from detail_page import render_full_detail_page

st.set_page_config(layout="wide")

st.title("Detail Page Test Runner")
st.write("This script demonstrates the `render_full_detail_page` function.")

# Mock data for testing
mock_final_decision_content = {
    "rating": "持有",
    "target_price": "19.46",
    "operation_advice": "现有持仓者可继续持有，空仓者等待放量突破19.46元或回调至17.73附近企稳时轻仓介入",
    "entry_range": "17.73-19.46",
    "take_profit": "19.46",
    "stop_loss": "17.50",
    "holding_period": "2-4周",
    "position_size": "轻仓",
    "risk_warning": "估值偏高，基本面数据缺失，成交量萎缩显示市场观望情绪浓厚，存在中高风险",
    "confidence_level": "6"
}

mock_record = {
    "stock_name": "测试股票",
    "stock_code": "000001",
    "created_at": "2023-01-01 10:00:00",
    "period": "日报",
    "analysis_result": json.dumps({
        "technical": {"analysis": "### 技术面分析\n\n该股票近期表现出强劲的上涨趋势，MACD金叉，KDJ指标显示超买，短期内可能面临回调压力。支撑位17.00元，阻力位19.50元。"},
        "fundamental": {"analysis": "### 基本面分析\n\n公司基本面稳健，营收和利润持续增长。行业前景广阔，但估值略高于行业平均水平，需警惕高位风险。"},
        "fund_flow": {"analysis": "### 资金面分析\n\n主力资金近期有小幅流入迹象，但成交量未能有效放大，市场观望情绪较浓。"},
        "risk_management": {"analysis": "### 风险评估\n\n主要风险包括宏观经济下行、行业政策变化、公司业绩不及预期等。估值偏高带来一定风险。"},
    }),
    "meeting_notes": "### 会议纪要\n\n内部会议讨论认为，尽管短期有回调风险，但中长期看好公司发展。建议关注市场情绪变化和成交量情况。",
    "investment_advice": "现有持仓者可继续持有，空仓者等待放量突破19.46元或回调至17.73附近企稳时轻仓介入", # This is actually operation_advice, just filling a field that exists
    "analysis_records": {
        "final_decision": json.dumps(mock_final_decision_content)
    }
}

# Render the full detail page with the mock record
render_full_detail_page(mock_record)

st.success("Page rendered successfully with mock data. Run `streamlit run run_detail_page.py` in your terminal to view.")