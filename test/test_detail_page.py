import pytest
from unittest.mock import patch, MagicMock
import json
from detail_page import render_full_detail_page

def test_render_full_detail_page_with_final_decision():
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
        'stock_name': '测试股票',
        'stock_code': '000001',
        'created_at': '2023-01-01',
        'period': '日报',
        'analysis_result': json.dumps({
            'technical': {'analysis': '技术面分析'},
            'fundamental': {'analysis': '基本面分析'},
            'fund_flow': {'analysis': '资金面分析'},
            'risk_management': {'analysis': '风险评估'},
        }),
        'meeting_notes': '这是一段会议纪要。',
        'investment_advice': '买入',
        'analysis_records': {
            'final_decision': json.dumps(mock_final_decision_content)
        }
    }

    # Patch Streamlit functions
    with patch('streamlit.set_page_config') as mock_set_page_config,
         patch('streamlit.title') as mock_title,
         patch('streamlit.caption') as mock_caption,
         patch('streamlit.divider') as mock_divider,
         patch('streamlit.tabs') as mock_tabs,
         patch('streamlit.markdown') as mock_markdown,
         patch('streamlit.sidebar') as mock_sidebar,
         patch('streamlit.header') as mock_header,
         patch('streamlit.info') as mock_info,
         patch('streamlit.button') as mock_button,
         patch('streamlit.query_params') as mock_query_params,
         patch('streamlit.rerun') as mock_rerun,
         patch('streamlit.metric') as mock_metric,
         patch('streamlit.warning') as mock_warning,
         patch('streamlit.error') as mock_error:

        mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_sidebar.__enter__.return_value = MagicMock()

        render_full_detail_page(mock_record)

        # Assert that key Streamlit functions were called
        mock_set_page_config.assert_called_once()
        mock_title.assert_called_once_with(f"📊 {mock_record["stock_name"]} ({mock_record["stock_code"]}) 深度分析报告")
        mock_caption.assert_called_once()
        assert mock_divider.call_count >= 2 # At least two dividers, one after header, one after final decision
        mock_tabs.assert_called_once()
        mock_markdown.assert_any_call(mock_record['analysis_result'])
        mock_header.assert_any_call("💡 核心决策")
        mock_metric.assert_any_call("评级", "持有")
        mock_metric.assert_any_call("目标价", "19.46")
        mock_metric.assert_any_call("止损", "17.50")
        mock_metric.assert_any_call("仓位", "轻仓")
        mock_sidebar.assert_called_once()
        mock_info.assert_called_once_with(f"建议：{mock_record.get("investment_advice", "观察")}")

        # Ensure error/warning handlers were NOT called for valid data
        mock_warning.assert_not_called()
        mock_error.assert_not_called()

def test_render_full_detail_page_no_final_decision():
    mock_record = {
        'stock_name': '无决策股票',
        'stock_code': '000002',
        'created_at': '2023-01-01',
        'period': '日报',
        'analysis_result': json.dumps({
            'technical': {'analysis': '技术面分析'},
            'fundamental': {'analysis': '基本面分析'},
            'fund_flow': {'analysis': '资金面分析'},
            'risk_management': {'analysis': '风险评估'},
        }),
        'meeting_notes': '暂无会议纪要',
        'investment_advice': '观望',
        'analysis_records': {}
    }

    with patch('streamlit.set_page_config') as mock_set_page_config,
         patch('streamlit.title') as mock_title,
         patch('streamlit.caption') as mock_caption,
         patch('streamlit.divider') as mock_divider,
         patch('streamlit.tabs') as mock_tabs,
         patch('streamlit.markdown') as mock_markdown,
         patch('streamlit.sidebar') as mock_sidebar,
         patch('streamlit.header') as mock_header,
         patch('streamlit.info') as mock_info,
         patch('streamlit.button') as mock_button,
         patch('streamlit.query_params') as mock_query_params,
         patch('streamlit.rerun') as mock_rerun,
         patch('streamlit.metric') as mock_metric,
         patch('streamlit.warning') as mock_warning,
         patch('streamlit.error') as mock_error:
        
        mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_sidebar.__enter__.return_value = MagicMock()

        render_full_detail_page(mock_record)

        mock_set_page_config.assert_called_once()
        mock_title.assert_called_once()
        mock_header.assert_any_call("🎯 投资决策") # Only sidebar header should be called
        mock_metric.assert_not_called() # No final decision metrics should be displayed
        mock_warning.assert_not_called()
        mock_error.assert_not_called()

def test_render_full_detail_page_invalid_final_decision_json():
    mock_record = {
        'stock_name': '错误JSON股票',
        'stock_code': '000003',
        'created_at': '2023-01-01',
        'period': '日报',
        'analysis_result': json.dumps({
            'technical': {'analysis': '技术面分析'},
            'fundamental': {'analysis': '基本面分析'},
            'fund_flow': {'analysis': '资金面分析'},
            'risk_management': {'analysis': '风险评估'},
        }),
        'meeting_notes': '暂无会议纪要',
        'investment_advice': '观望',
        'analysis_records': {
            'final_decision': 'this is not valid json'
        }
    }

    with patch('streamlit.set_page_config'),
         patch('streamlit.title'),
         patch('streamlit.caption'),
         patch('streamlit.divider'),
         patch('streamlit.tabs') as mock_tabs,
         patch('streamlit.markdown'),
         patch('streamlit.sidebar') as mock_sidebar,
         patch('streamlit.header'),
         patch('streamlit.info'),
         patch('streamlit.button'),
         patch('streamlit.query_params'),
         patch('streamlit.rerun'),
         patch('streamlit.metric'),
         patch('streamlit.warning') as mock_warning,
         patch('streamlit.error') as mock_error:

        mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_sidebar.__enter__.return_value = MagicMock()

        render_full_detail_page(mock_record)

        mock_warning.assert_called_once_with("核心决策数据解析失败，可能不是有效的JSON格式。")
        mock_error.assert_not_called()

