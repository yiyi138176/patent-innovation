# -*- coding: utf-8 -*-
"""测试 akshare 能不能拉到 A 股公司财务数据"""
import akshare as ak

print("akshare 版本:", ak.__version__)
print("=" * 60)

code = "300161"   # 华中数控

print("\n【测试1】财务指标 stock_financial_analysis_indicator")
try:
    df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2018")
    print("  ✅ 成功！行数:", df.shape[0], " 列数:", df.shape[1])
    print("  前 25 个列名:", list(df.columns)[:25])
    print("  前 3 行:")
    print(df.head(3).to_string()[:1800])
except Exception as e:
    print("  ❌ 失败:", type(e).__name__, "|", e)

print("\n【测试2】财务摘要 stock_financial_abstract")
try:
    df2 = ak.stock_financial_abstract(symbol=code)
    print("  ✅ 成功！行数:", df2.shape[0], " 列数:", df2.shape[1])
    print(df2.head(12).to_string()[:1800])
except Exception as e:
    print("  ❌ 失败:", type(e).__name__, "|", e)

print("\n【测试3】全 A 股代码表 stock_info_a_code_name")
try:
    df3 = ak.stock_info_a_code_name()
    print("  ✅ 成功！共", len(df3), "家公司")
    print(df3.head().to_string())
except Exception as e:
    print("  ❌ 失败:", type(e).__name__, "|", e)