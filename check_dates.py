# -*- coding: utf-8 -*-
"""诊断：财务数据的日期列到底是什么样"""
import os
import pandas as pd

PROC = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
fin = pd.read_csv(os.path.join(PROC, "企业财务数据.csv"), dtype={"股票代码": str})

print("总行数:", len(fin))
print("\n【日期列原始值（前 20 个）】")
print(fin["日期"].head(20).to_string())
print("\n日期列 dtype:", fin["日期"].dtype)

d = pd.to_datetime(fin["日期"], errors="coerce")
print("\n解析失败(NaT)数:", d.isna().sum())

print("\n【月份-日期 分布】")
print(d.dt.strftime("%m-%d").value_counts(dropna=False).to_string())

print("\n【年份分布】")
print(d.dt.year.value_counts(dropna=False).sort_index().to_string())

print("\n【每家公司行数分布】")
print(fin.groupby("公司名").size().describe().to_string())

print("\n【最后一家的完整日期序列】")
last = fin["公司名"].iloc[-1]
print("公司:", last)
print(fin[fin["公司名"] == last][["日期"]].to_string())