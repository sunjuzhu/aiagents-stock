import os
import sys
import pandas as pd

# Add the parent directory to the Python path to allow importing risk_data_fetcher
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from risk_data_fetcher import RiskDataFetcher

def run_simple_test(symbol: str):
    """
    # Runs a simple test for RiskDataFetcher methods and prints the raw output,
    # and then the formatted output using the internal formatting methods.
    # This test makes actual calls to pywencai, so network access is required.
    # """
    # print(f"==================================================")
    # print(f"Running simple test for RiskDataFetcher with symbol: {symbol}")
    # print(f"==================================================\n")

    fetcher = RiskDataFetcher()

    # # Test _get_lifting_ban_data
    # print(f"--- Testing _get_lifting_ban_data for {symbol} ---")
    # lifting_ban_data = fetcher._get_lifting_ban_data(symbol)
    # print("Raw _get_lifting_ban_data output:")
    # print(lifting_ban_data)
    # if lifting_ban_data and lifting_ban_data.get("has_data") and lifting_ban_data.get("data") is not None:
    #     print("\nFormatted _get_lifting_ban_data output (via _format_dataframe_for_ai):\n")
    #     # Direct call to _format_dataframe_for_ai for individual method output
    #     formatted_single_data = fetcher._format_dataframe_for_ai(lifting_ban_data["data"], "限售解禁")
    #     print(formatted_single_data)
    # print("\n")

    # # Test _get_shareholder_reduction_data
    # print(f"--- Testing _get_shareholder_reduction_data for {symbol} ---")
    # shareholder_reduction_data = fetcher._get_shareholder_reduction_data(symbol)
    # print("Raw _get_shareholder_reduction_data output:")
    # print(shareholder_reduction_data)
    # if shareholder_reduction_data and shareholder_reduction_data.get("has_data") and shareholder_reduction_data.get("data") is not None:
    #     print("\nFormatted _get_shareholder_reduction_data output (via _format_dataframe_for_ai):\n")
    #     # Direct call to _format_dataframe_for_ai for individual method output
    #     formatted_single_data = fetcher._format_dataframe_for_ai(shareholder_reduction_data["data"], "大股东减持")
    #     print(formatted_single_data)
    # print("\n")

    # # Test _get_important_events_data
    # print(f"--- Testing _get_important_events_data for {symbol} ---")
    # important_events_data = fetcher._get_important_events_data(symbol)
    # print("Raw _get_important_events_data output:")
    # print(important_events_data)
    # if important_events_data and important_events_data.get("has_data") and important_events_data.get("data") is not None:
    #     print("\nFormatted _get_important_events_data output (via _format_dataframe_for_ai):\n")
    #     # Direct call to _format_dataframe_for_ai for individual method output
    #     formatted_single_data = fetcher._format_dataframe_for_ai(important_events_data["data"], "重要事件")
    #     print(formatted_single_data)
    # print("\n")

    # # Test get_risk_data (orchestration) and its overall formatting
    # print(f"--- Testing get_risk_data (orchestration) for {symbol} ---")
    all_risk_data = fetcher.get_risk_data(symbol)
    print("Raw get_risk_data output:")
    print(all_risk_data)
    print("\n")
    return all_risk_data

import json
import pandas as pd

def save_risk_data_to_json(risk_data, filename="risk_report.json"):
    # 深度拷贝一份数据，避免修改原始对象
    processed_data = risk_data.copy()
    
    # 核心步骤：遍历字典，把里面的 Pandas DataFrame 转为 list/dict
    for key in ['lifting_ban', 'shareholder_reduction', 'important_events']:
        if key in processed_data and isinstance(processed_data[key].get('data'), pd.DataFrame):
            # orient='records' 会转为 [{col1:val1, col2:val2}, ...] 格式
            processed_data[key]['data'] = processed_data[key]['data'].to_dict(orient='records')

    # 写入 JSON 文件
    with open(filename, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 保证中文不乱码，indent=4 保证格式漂亮
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
    
    print(f"数据已完整保存至: {filename}")

# 使用示例：
# save_risk_data_to_json(get_risk_data_output)


if __name__ == "__main__":
    # You can change the test_symbol to any valid stock code
    test_symbol = "000001" # Ping An Bank (平安银行)
    # test_symbol = "600000" # Pudong Development Bank (浦发银行)
    
    get_risk_data_output = run_simple_test(test_symbol)

    print("risk data type is :",type(get_risk_data_output))
    save_risk_data_to_json(get_risk_data_output)

