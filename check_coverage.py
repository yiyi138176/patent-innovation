# -*- coding: utf-8 -*-
"""检查各财务变量在 2015-2025 各年的覆盖率，用来挑选 y 变量"""
import os
import pandas as pd

PROC = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
fin = pd.read_csv(os.path.join(PROC, "企业财务数据_full.csv"), dtype={"股票代码": str})
fin["日期"] = pd.to_datetime(fin["日期"], errors="coerce")
fin["年份"] = fin["日期"].dt.year
q4 = fin[fin["日期"].dt.strftime("%m-%d") == "12-31"].copy()
print(f"年报行数: {len(q4)}   公司数: {q4['股票代码'].nunique()}")
print(f"年份: {int(q4['年份'].min())} - {int(q4['年份'].max())}")

# 只统计数值型列
num = q4.select_dtypes(include="number")
num = num.drop(columns=["年份"], errors="ignore")
# 去掉全是空的列
num = num.loc[:, num.notna().sum() > 0]

# 覆盖情况：每列在 2015-2025 每年有多少非空
years = [y for y in range(2015, 2026)]
tab = pd.DataFrame(index=num.columns)
for y in years:
    sub = num[q4["年份"] == y]
    tab[y] = sub.notna().sum()
tab["总非空"] = tab[years].sum(axis=1)
tab["覆盖年数"] = (tab[years] > 0).sum(axis=1)
tab["覆盖率"] = (tab["总非空"] / len(q4) * 100).round(1)

# 只留覆盖年数 >= 8 的（几乎全程都有数据的）
good = tab[tab["覆盖年数"] >= 8].sort_values("覆盖率", ascending=False)
print(f"\n=== 覆盖 ≥8 个年份的变量（共 {len(good)} 个）===")
print(good[years + ["覆盖率"]].to_string())

print("\n=== 覆盖不足的变量 ===")
bad = tab[tab["覆盖年数"] < 8].sort_values("覆盖年数")
print(bad[["覆盖年数", "覆盖率"]].to_string())