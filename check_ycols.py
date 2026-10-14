# -*- coding: utf-8 -*-
"""诊断：三个 y 变量在各年份的缺失情况"""
import os
import pandas as pd

PROC = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
fin = pd.read_csv(os.path.join(PROC, "企业财务数据.csv"), dtype={"股票代码": str})
YCOLS = ["总资产净利润率(%)", "主营业务收入增长率(%)", "销售毛利率(%)"]

print("=== 全部 5830 行里，每列的非空率 ===")
for c in YCOLS:
    print(f"  {c:<22} 非空 {fin[c].notna().mean()*100:5.1f}%  ({fin[c].notna().sum()} 行)")

fin["日期"] = pd.to_datetime(fin["日期"], errors="coerce")
q4 = fin[fin["日期"].dt.strftime("%m-%d") == "12-31"].copy()
q4["年份"] = q4["日期"].dt.year
print(f"\n=== 只看 12-31 的年报行（共 {len(q4)} 行）===")
for c in YCOLS:
    print(f"  {c:<22} 非空 {q4[c].notna().mean()*100:5.1f}%  ({q4[c].notna().sum()} 行)")

print("\n=== 每年：12-31 行数 / 三个都非空的行数 ===")
g = q4.groupby("年份")
tab = pd.DataFrame({
    "年报行数": g.size(),
    "三个都非空": g.apply(lambda x: x[YCOLS].notna().all(axis=1).sum()),
})
for c in YCOLS:
    tab[f"{c[:8]}非空"] = g.apply(lambda x, c=c: x[c].notna().sum())
print(tab.to_string())

print("\n=== 三个都没非空的行，长什么样（前 10 行）===")
bad = q4[q4[YCOLS].isna().any(axis=1)]
print(bad[["年份"] + YCOLS].head(10).to_string())