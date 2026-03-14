import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory of app.py to the sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mock streamlit before importing app, as app.py uses streamlit extensively
# This creates a dummy \"streamlit\" module that can be used for patching \"st\"
st_mock = MagicMock()
st_mock.session_state = MagicMock()
sys.modules["streamlit"] = st_mock
sys.modules["streamlit.connections"] = MagicMock()
sys.modules["streamlit.testing.v1"] = MagicMock()

# Mock other external dependencies that app.py imports
sys.modules["plotly.graph_objects"] = MagicMock()
sys.modules["plotly.express"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["json"] = MagicMock()
sys.modules["datetime"] = MagicMock()
sys.modules["time"] = MagicMock()
sys.modules["base64"] = MagicMock()
sys.modules["config"] = MagicMock()
sys.modules["stock_data"] = MagicMock()
sys.modules["ai_agents"] = MagicMock()
sys.modules["pdf_generator"] = MagicMock()
sys.modules["database"] = MagicMock()
sys.modules["monitor_manager"] = MagicMock()
sys.modules["monitor_service"] = MagicMock()
sys.modules["notification_service"] = MagicMock()
sys.modules["config_manager"] = MagicMock()
sys.modules["main_force_ui"] = MagicMock()
sys.modules["sector_strategy_ui"] = MagicMock()
sys.modules["longhubang_ui"] = MagicMock()
sys.modules["smart_monitor_ui"] = MagicMock()
sys.modules["news_flow_ui"] = MagicMock()
sys.modules["low_price_bull_ui"] = MagicMock()
sys.modules["small_cap_ui"] = MagicMock()
sys.modules["profit_growth_ui"] = MagicMock()
sys.modules["value_stock_ui"] = MagicMock()
sys.modules["portfolio_ui"] = MagicMock()
sys.modules["macro_cycle_ui"] = MagicMock()

# Mock the `monitor_db` module itself, and specifically `monitor_db` within that module
monitor_db_module_mock = MagicMock()
sys.modules["monitor_db"] = monitor_db_module_mock
monitor_db_module_mock.monitor_db = MagicMock() # Mock the `monitor_db` object within the module

sys.modules["quarterly_report_data"] = MagicMock()
sys.modules["quarterly_report_data.QuarterlyReportDataFetcher"] = MagicMock()
sys.modules["fund_flow_akshare"] = MagicMock()
sys.modules["fund_flow_akshare.FundFlowAkshareDataFetcher"] = MagicMock()
sys.modules["market_sentiment_data"] = MagicMock()
sys.modules["market_sentiment_data.MarketSentimentDataFetcher"] = MagicMock()
sys.modules["qstock_news_data"] = MagicMock()
sys.modules["qstock_news_data.QStockNewsDataFetcher"] = MagicMock()




# Now import app after mocking everything
from app import check_api_key, parse_stock_list, analyze_single_stock_for_batch, display_add_to_monitor_dialog, main, render_custom_detail_page

class TestAppFunctions(unittest.TestCase):

    def setUp(self):
        # Reset session_state for each test
        # Accessing session_state via st_mock.session_state is correct for tests
        if hasattr(st_mock.session_state, "show_history"):
            del st_mock.session_state["show_history"]
        if hasattr(st_mock.session_state, "show_monitor"):
            del st_mock.session_state["show_monitor"]
        if hasattr(st_mock.session_state, "show_config"):
            del st_mock.session_state["show_config"]
        if hasattr(st_mock.session_state, "selected_model"):
            del st_mock.session_state["selected_model"]
        if hasattr(st_mock.session_state, "batch_mode"):
            del st_mock.session_state["batch_mode"]
        if hasattr(st_mock.session_state, "enable_technical"):
            del st_mock.session_state["enable_technical"]
        if hasattr(st_mock.session_state, "enable_fundamental"):
            del st_mock.session_state["enable_fundamental"]
        if hasattr(st_mock.session_state, "enable_fund_flow"):
            del st_mock.session_state["enable_fund_flow"]
        if hasattr(st_mock.session_state, "enable_risk"):
            del st_mock.session_state["enable_risk"]
        if hasattr(st_mock.session_state, "enable_sentiment"):
            del st_mock.session_state["enable_sentiment"]
        if hasattr(st_mock.session_state, "enable_news"):
            del st_mock.session_state["enable_news"]
        if hasattr(st_mock.session_state, "batch_analysis_results"):
            del st_mock.session_state["batch_analysis_results"]
        if hasattr(st_mock.session_state, "analysis_completed"):
            del st_mock.session_state["analysis_completed"]
        if hasattr(st_mock.session_state, "stock_info"):
            del st_mock.session_state["stock_info"]
        if hasattr(st_mock.session_state, "agents_results"):
            del st_mock.session_state["agents_results"]
        if hasattr(st_mock.session_state, "discussion_result"):
            del st_mock.session_state["discussion_result"]
        if hasattr(st_mock.session_state, "final_decision"):
            del st_mock.session_state["final_decision"]
        if hasattr(st_mock.session_state, "just_completed"):
            del st_mock.session_state["just_completed"]
        if hasattr(st_mock.session_state, "viewing_record_id"):
            del st_mock.session_state["viewing_record_id"]
        if hasattr(st_mock.session_state, "add_to_monitor_id"):
            del st_mock.session_state["add_to_monitor_id"]


    @patch("config.API_KEY", "test_api_key")
    def test_check_api_key_configured(self):
        self.assertTrue(check_api_key())

    @patch("config.API_KEY", "")
    def test_check_api_key_not_configured_empty(self):
        self.assertFalse(check_api_key())

    @patch("config.API_KEY", None)
    def test_check_api_key_not_configured_none(self):
        self.assertFalse(check_api_key())

    def test_parse_stock_list_empty_string(self):
        self.assertEqual(parse_stock_list(""), [])

    def test_parse_stock_list_single_stock(self):
        self.assertEqual(parse_stock_list("AAPL"), ["AAPL"])

    def test_parse_stock_list_newline_separated(self):
        input_str = "AAPL\nMSFT\nGOOG"
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG"])

    def test_parse_stock_list_comma_separated(self):
        input_str = "AAPL, MSFT, GOOG"
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG"])

    def test_parse_stock_list_space_separated(self):
        input_str = "AAPL MSFT GOOG"
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG"])

    def test_parse_stock_list_mixed_separators(self):
        input_str = "AAPL, MSFT\nGOOG TSLA"
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG", "TSLA"])

    def test_parse_stock_list_duplicates_removed(self):
        input_str = "AAPL, MSFT, AAPL\nGOOG, MSFT"
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG"])

    def test_parse_stock_list_with_extra_whitespace(self):
        input_str = "  AAPL ,  MSFT  \n  GOOG "
        self.assertEqual(parse_stock_list(input_str), ["AAPL", "MSFT", "GOOG"])

    def test_parse_stock_list_only_whitespace(self):
        self.assertEqual(parse_stock_list(" \n  , "), [])

    @patch("app.get_stock_data")
    @patch("app.StockDataFetcher")
    @patch("app.StockAnalysisAgents")
    @patch("app.db")
    @patch("quarterly_report_data.QuarterlyReportDataFetcher")
    @patch("fund_flow_akshare.FundFlowAkshareDataFetcher")
    @patch("market_sentiment_data.MarketSentimentDataFetcher")
    @patch("qstock_news_data.QStockNewsDataFetcher")
    def test_analyze_single_stock_for_batch_success(
        self, MockQStockNewsDataFetcher, MockMarketSentimentDataFetcher, 
        MockFundFlowAkshareDataFetcher, MockQuarterlyReportDataFetcher, 
        MockDB, MockStockAnalysisAgents, MockStockDataFetcher, MockGetStockData
    ):
        # Mock dependencies
        mock_stock_info = {"symbol": "000001", "name": "平安银行", "current_price": 10.0}
        mock_stock_data = MagicMock(spec=object) # Use MagicMock for DataFrame-like object
        mock_indicators = {"rsi": 50, "ma20": 9.5}

        MockGetStockData.return_value = (mock_stock_info, mock_stock_data, mock_indicators)
        
        mock_fetcher_instance = MockStockDataFetcher.return_value
        mock_fetcher_instance.get_financial_data.return_value = {"revenue": 100}
        mock_fetcher_instance._is_chinese_stock.return_value = True
        mock_fetcher_instance.get_risk_data.return_value = {"data_success": True, "lifting_ban": {"has_data": True}}

        mock_quarterly_fetcher_instance = MockQuarterlyReportDataFetcher.return_value
        mock_quarterly_fetcher_instance.get_quarterly_reports.return_value = {"data_success": True}

        mock_fund_flow_fetcher_instance = MockFundFlowAkshareDataFetcher.return_value
        mock_fund_flow_fetcher_instance.get_fund_flow_data.return_value = {"data_success": True}

        mock_sentiment_fetcher_instance = MockMarketSentimentDataFetcher.return_value
        mock_sentiment_fetcher_instance.get_market_sentiment_data.return_value = {"data_success": True}

        mock_news_fetcher_instance = MockQStockNewsDataFetcher.return_value
        mock_news_fetcher_instance.get_stock_news.return_value = {"data_success": True}

        mock_agents_instance = MockStockAnalysisAgents.return_value
        mock_agents_instance.run_multi_agent_analysis.return_value = {"technical": {"analysis": "tech analysis"}}
        mock_agents_instance.conduct_team_discussion.return_value = "team discussion"
        mock_agents_instance.make_final_decision.return_value = {"rating": "买入"}

        MockDB.save_analysis.return_value = "record_id_123"

        enabled_analysts_config = {
            "technical": True, "fundamental": True, "fund_flow": True, 
            "risk": True, "sentiment": True, "news": True
        }

        result = analyze_single_stock_for_batch(
            "000001", "1y", enabled_analysts_config=enabled_analysts_config, selected_model="test-model"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "000001")
        self.assertTrue(result["saved_to_db"])
        self.assertEqual(result["final_decision"]["rating"], "买入")

        MockGetStockData.assert_called_once_with("000001", "1y")
        mock_fetcher_instance.get_financial_data.assert_called_once_with("000001")
        mock_agents_instance.run_multi_agent_analysis.assert_called_once()
        mock_agents_instance.conduct_team_discussion.assert_called_once()
        mock_agents_instance.make_final_decision.assert_called_once()
        MockDB.save_analysis.assert_called_once()

    @patch("app.get_stock_data")
    @patch("app.StockDataFetcher")
    def test_analyze_single_stock_for_batch_data_fetch_failure(self, MockStockDataFetcher, MockGetStockData):
        MockGetStockData.return_value = ({"error": "stock not found"}, None, None)

        result = analyze_single_stock_for_batch("INVALID", "1y")

        self.assertFalse(result["success"])
        self.assertEqual(result["symbol"], "INVALID")
        self.assertIn("stock not found", result["error"])

    @patch("app.get_stock_data")
    @patch("app.StockDataFetcher")
    @patch("app.StockAnalysisAgents")
    @patch("app.db")
    def test_analyze_single_stock_for_batch_db_save_failure(
        self, MockDB, MockStockAnalysisAgents, MockStockDataFetcher, MockGetStockData
    ):
        mock_stock_info = {"symbol": "000002", "name": "万科A"}
        mock_stock_data = MagicMock(spec=object)
        mock_indicators = {}

        MockGetStockData.return_value = (mock_stock_info, mock_stock_data, mock_indicators)

        mock_fetcher_instance = MockStockDataFetcher.return_value
        mock_fetcher_instance.get_financial_data.return_value = {}
        mock_fetcher_instance._is_chinese_stock.return_value = True
        mock_fetcher_instance.get_risk_data.return_value = {"data_success": False}

        mock_agents_instance = MockStockAnalysisAgents.return_value
        mock_agents_instance.run_multi_agent_analysis.return_value = {}
        mock_agents_instance.conduct_team_discussion.return_value = ""
        mock_agents_instance.make_final_decision.return_value = {}

        MockDB.save_analysis.side_effect = Exception("DB connection error")

        result = analyze_single_stock_for_batch("000002", "1y")

        self.assertTrue(result["success"]) # Analysis itself completes, only save fails
        self.assertEqual(result["symbol"], "000002")
        self.assertFalse(result["saved_to_db"])
        self.assertIn("DB connection error", result["db_error"])

    @patch("streamlit.columns", side_effect=[[MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]) # For display_add_to_monitor_dialog
    @patch("streamlit.rerun")
    @patch("streamlit.balloons")
    @patch("streamlit.success")
    @patch("streamlit.error") # Added mock for st.error
    @patch("streamlit.warning")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.form_submit_button", side_effect=[True, False]) # Submit, then Cancel
    @patch("streamlit.form", return_value=MagicMock())
    @patch("streamlit.selectbox", return_value="买入")
    @patch("streamlit.checkbox", return_value=True)
    @patch("streamlit.slider", return_value=30)
    @patch("streamlit.number_input", side_effect=[10.5, 12.0, 0.0, 0.0]) # entry_min, entry_max, take_profit, stop_loss
    @patch("monitor_db.monitor_db") # Corrected patch target
    @patch("app.monitor_service.manual_update_stock")
    def test_parse_entry_range_valid_dash(
        self, mock_manual_update_stock, mock_monitor_db_instance, mock_number_input, mock_slider, mock_checkbox, 
        mock_selectbox, mock_form, mock_form_submit_button, mock_subheader, mock_markdown, 
        mock_info, mock_warning, mock_error, mock_success, mock_balloons, mock_rerun, mock_st_columns
    ):
        record = {"id": "rec1", "symbol": "000001", "stock_name": "Test Stock", "final_decision": {"entry_range": "10.5-12.0"}}
        mock_monitor_db_instance.get_monitored_stocks.return_value = []
        mock_monitor_db_instance.add_monitored_stock.return_value = "monitor_id_123"
        
        display_add_to_monitor_dialog(record)
        
        mock_monitor_db_instance.add_monitored_stock.assert_called_once_with(
            symbol=record["symbol"],
            name=record["stock_name"],
            rating="买入",
            entry_range={"min": 10.5, "max": 12.0},
            take_profit=None,
            stop_loss=None,
            check_interval=30,
            notification_enabled=True
        )
        mock_success.assert_called_once_with(f"✅ 已成功将 {record["symbol"]} 加入监测列表！")
        mock_balloons.assert_called_once()
        self.assertTrue(mock_rerun.called)

    @patch("streamlit.columns", side_effect=[[MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]) # For display_add_to_monitor_dialog
    @patch("streamlit.rerun")
    @patch("streamlit.balloons")
    @patch("streamlit.success")
    @patch("streamlit.error") # Added mock for st.error
    @patch("streamlit.warning")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.form_submit_button", side_effect=[True, False]) # Submit, then Cancel
    @patch("streamlit.form", return_value=MagicMock())
    @patch("streamlit.selectbox", return_value="买入")
    @patch("streamlit.checkbox", return_value=True)
    @patch("streamlit.slider", return_value=30)
    @patch("streamlit.number_input", side_effect=[10.5, 12.0, 0.0, 0.0])
    @patch("monitor_db.monitor_db") # Corrected patch target
    @patch("app.monitor_service.manual_update_stock")
    def test_parse_entry_range_valid_tilda(
        self, mock_manual_update_stock, mock_monitor_db_instance, mock_number_input, mock_slider, mock_checkbox, 
        mock_selectbox, mock_form, mock_form_submit_button, mock_subheader, mock_markdown, 
        mock_info, mock_warning, mock_error, mock_success, mock_balloons, mock_rerun, mock_st_columns
    ):
        record = {"id": "rec2", "symbol": "000001", "stock_name": "Test Stock", "final_decision": {"entry_range": "10.5~12.0"}}
        mock_monitor_db_instance.get_monitored_stocks.return_value = []
        mock_monitor_db_instance.add_monitored_stock.return_value = "monitor_id_123"

        display_add_to_monitor_dialog(record)
        
        mock_monitor_db_instance.add_monitored_stock.assert_called_once_with(
            symbol=record["symbol"],
            name=record["stock_name"],
            rating="买入",
            entry_range={"min": 10.5, "max": 12.0},
            take_profit=None,
            stop_loss=None,
            check_interval=30,
            notification_enabled=True
        )
        self.assertTrue(mock_rerun.called)

    @patch("streamlit.columns", side_effect=[[MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]) # For display_add_to_monitor_dialog
    @patch("streamlit.rerun")
    @patch("streamlit.balloons")
    @patch("streamlit.success")
    @patch("streamlit.error") # Added mock for st.error
    @patch("streamlit.warning")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.form_submit_button", side_effect=[True, False]) # Submit, then Cancel
    @patch("streamlit.form", return_value=MagicMock())
    @patch("streamlit.selectbox", return_value="买入")
    @patch("streamlit.checkbox", return_value=True)
    @patch("streamlit.slider", return_value=30)
    @patch("streamlit.number_input", side_effect=[0.0, 0.0, 0.0, 0.0]) # Expect default 0.0-0.0 if parsing fails
    @patch("monitor_db.monitor_db") # Corrected patch target
    @patch("app.monitor_service.manual_update_stock")
    def test_parse_entry_range_single_value(
        self, mock_manual_update_stock, mock_monitor_db_instance, mock_number_input, mock_slider, mock_checkbox, 
        mock_selectbox, mock_form, mock_form_submit_button, mock_subheader, mock_markdown, 
        mock_info, mock_warning, mock_error, mock_success, mock_balloons, mock_rerun, mock_st_columns
    ):
        record = {"id": "rec3", "symbol": "000001", "stock_name": "Test Stock", "final_decision": {"entry_range": "10.5"}}
        mock_monitor_db_instance.get_monitored_stocks.return_value = []
        mock_monitor_db_instance.add_monitored_stock.return_value = "monitor_id_123"
        
        display_add_to_monitor_dialog(record)
        
        mock_monitor_db_instance.add_monitored_stock.assert_not_called() # Changed to assert_not_called
        mock_error.assert_called_once_with("❌ 请输入有效的进场区间（最低价应小于最高价，且都大于0）") # Changed to mock_error
        self.assertFalse(mock_rerun.called)

    @patch("streamlit.columns", side_effect=[[MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]) # For display_add_to_monitor_dialog
    @patch("streamlit.rerun")
    @patch("streamlit.balloons")
    @patch("streamlit.success")
    @patch("streamlit.error") # Added mock for st.error
    @patch("streamlit.warning")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.form_submit_button", side_effect=[True, False]) # Submit, then Cancel
    @patch("streamlit.form", return_value=MagicMock())
    @patch("streamlit.selectbox", return_value="买入")
    @patch("streamlit.checkbox", return_value=True)
    @patch("streamlit.slider", return_value=30)
    @patch("streamlit.number_input", side_effect=[1.0, 2.0, 15.0, 0.0]) # Added valid entry_range for success path
    @patch("monitor_db.monitor_db") # Corrected patch target
    @patch("app.monitor_service.manual_update_stock")
    def test_parse_take_profit_valid(
        self, mock_manual_update_stock, mock_monitor_db_instance, mock_number_input, mock_slider, mock_checkbox, 
        mock_selectbox, mock_form, mock_form_submit_button, mock_subheader, mock_markdown, 
        mock_info, mock_warning, mock_error, mock_success, mock_balloons, mock_rerun, mock_st_columns
    ):
        record = {"id": "rec4", "symbol": "000001", "stock_name": "Test Stock", "final_decision": {"take_profit": "¥15.00元", "entry_range": "1-2"}}
        mock_monitor_db_instance.get_monitored_stocks.return_value = []
        mock_monitor_db_instance.add_monitored_stock.return_value = "monitor_id_123"
        
        display_add_to_monitor_dialog(record)
        
        mock_monitor_db_instance.add_monitored_stock.assert_called_once_with(
            symbol=record["symbol"],
            name=record["stock_name"],
            rating="买入",
            entry_range={"min": 1.0, "max": 2.0},
            take_profit=15.0,
            stop_loss=None,
            check_interval=30,
            notification_enabled=True
        )
        self.assertTrue(mock_rerun.called)

    @patch("streamlit.columns", side_effect=[[MagicMock(), MagicMock()], [MagicMock(), MagicMock(), MagicMock()]]) # For display_add_to_monitor_dialog
    @patch("streamlit.rerun")
    @patch("streamlit.balloons")
    @patch("streamlit.success")
    @patch("streamlit.error") # Added mock for st.error
    @patch("streamlit.warning")
    @patch("streamlit.info")
    @patch("streamlit.markdown")
    @patch("streamlit.subheader")
    @patch("streamlit.form_submit_button", side_effect=[True, False]) # Submit, then Cancel
    @patch("streamlit.form", return_value=MagicMock())
    @patch("streamlit.selectbox", return_value="买入")
    @patch("streamlit.checkbox", return_value=True)
    @patch("streamlit.slider", return_value=30)
    @patch("streamlit.number_input", side_effect=[1.0, 2.0, 0.0, 8.0]) # Added valid entry_range for success path
    @patch("monitor_db.monitor_db") # Corrected patch target
    @patch("app.monitor_service.manual_update_stock")
    def test_parse_stop_loss_valid(
        self, mock_manual_update_stock, mock_monitor_db_instance, mock_number_input, mock_slider, mock_checkbox, 
        mock_selectbox, mock_form, mock_form_submit_button, mock_subheader, mock_markdown, 
        mock_info, mock_warning, mock_error, mock_success, mock_balloons, mock_rerun, mock_st_columns
    ):
        record = {"id": "rec5", "symbol": "000001", "stock_name": "Test Stock", "final_decision": {"stop_loss": "$8.00", "entry_range": "1-2"}}
        mock_monitor_db_instance.get_monitored_stocks.return_value = []
        mock_monitor_db_instance.add_monitored_stock.return_value = "monitor_id_123"
        
        display_add_to_monitor_dialog(record)
        
        mock_monitor_db_instance.add_monitored_stock.assert_called_once_with(
            symbol=record["symbol"],
            name=record["stock_name"],
            rating="买入",
            entry_range={"min": 1.0, "max": 2.0},
            take_profit=None,
            stop_loss=8.0,
            check_interval=30,
            notification_enabled=True
        )
        self.assertTrue(mock_rerun.called)

    # Test cases for the main function\\\"s query param handling
    @patch("streamlit.query_params", {"view_id": "test_id_123"})
    @patch("app.db.get_record_by_id")
    @patch("app.render_custom_detail_page")
    @patch("streamlit.set_page_config") # Mock set_page_config which is called early
    @patch("streamlit.markdown") # Mock markdown for custom CSS
    def test_main_renders_detail_page_with_query_param(self, mock_st_markdown, mock_st_set_page_config, mock_render_custom_detail_page, mock_get_record_by_id):
        # Prepare a mock record
        mock_record = {
            "id": "test_id_123",
            "stock_name": "Test Stock",
            "symbol": "TEST",
            "period": "1y",
            "analysis_date": "2023-01-01",
            "final_decision": {"rating": "持有"},
            "agents_results": {},
            "discussion_result": ""
        }
        mock_get_record_by_id.return_value = mock_record

        main()

        mock_get_record_by_id.assert_called_once_with("test_id_123")
        mock_render_custom_detail_page.assert_called_once_with(mock_record)

    @patch("streamlit.query_params", {})
    @patch("app.db.get_record_by_id")
    @patch("app.render_custom_detail_page")
    @patch("app.show_example_interface")
    @patch("app.show_current_model_info")
    @patch("config.DEFAULT_MODEL_NAME", "test-model")
    @patch("app.check_api_key", return_value=True) # Assume API key is checked
    @patch("streamlit.set_page_config") # Mock set_page_config
    @patch("streamlit.markdown") # Consolidated markdown mock
    @patch("streamlit.info") # Mock info for learning resources
    @patch("streamlit.sidebar.markdown") 
    @patch("streamlit.sidebar.button", return_value=False) # Mock sidebar buttons
    @patch("streamlit.sidebar.expander", return_value=MagicMock())
    @patch("streamlit.sidebar.selectbox")
    @patch("streamlit.sidebar.info")
    @patch("streamlit.sidebar.subheader")
    @patch("streamlit.sidebar.caption")
    @patch("streamlit.sidebar.success")
    @patch("streamlit.radio", return_value="单个分析")
    @patch("streamlit.text_input", return_value="") # No stock input
    @patch("streamlit.subheader")
    @patch("streamlit.columns", side_effect=[
        [MagicMock(), MagicMock()], # 1. col_mode1, col_mode2 = st.columns([1, 3])
        [MagicMock(), MagicMock(), MagicMock()], # 2. col1, col2, col3 = st.columns([2, 1, 1]) (single analysis path)
        [MagicMock(), MagicMock(), MagicMock()], # 3. col1, col2, col3 = st.columns(3) (analyst selection)
        [MagicMock(), MagicMock(), MagicMock()]  # 4. col1, col2, col3 = st.columns(3) (buttons)
    ])
    def test_main_renders_example_interface_without_query_param_or_input(
        self, mock_st_columns, mock_st_subheader, mock_st_text_input, mock_st_radio, 
        mock_st_sidebar_success, mock_st_sidebar_caption, mock_st_sidebar_subheader, 
        mock_st_sidebar_info, mock_st_sidebar_selectbox, mock_st_sidebar_expander, 
        mock_st_sidebar_button, mock_st_sidebar_markdown, mock_st_info, mock_st_markdown, 
        mock_st_set_page_config, mock_check_api_key, mock_show_current_model_info, 
        mock_show_example_interface, mock_render_custom_detail_page, mock_get_record_by_id
    ):
        main()

        mock_get_record_by_id.assert_not_called()
        mock_render_custom_detail_page.assert_not_called()
        mock_show_example_interface.assert_called_once() # Should show example interface if no input


if __name__ == "__main__":
    unittest.main()
