# -*- coding: utf-8 -*-
"""合并专利年度特征 + 企业财务数据 -> 主数据集（修正版）"""
import os
import numpy as np
import pandas as pd

PROC = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"

# ---------- 1. 专利年度特征 ----------
pat = pd.read_csv(os.path.join(PROC, "公司年度特征.csv"), dtype={"股票代码": str})
pat["股票代码"] = (pat["股票代码"].fillna("").str.strip()
                .str.replace(r"\.0$", "", regex=True).str.zfill(6))
pat["年份"] = pd.to_numeric(pat["年份"], errors="coerce")
pat = pat.dropna(subset=["年份"]).copy()
pat["年份"] = pat["年份"].astype(int)
pat = pat[pat["股票代码"] != ""]
print("专利年度特征:", pat.shape)

# ---------- 2. 财务数据 -> 年度 ----------
fin = pd.read_csv(os.path.join(PROC, "企业财务数据_full.csv"), dtype={"股票代码": str})
fin["股票代码"] = fin["股票代码"].fillna("").str.strip().str.zfill(6)
fin["日期"] = pd.to_datetime(fin["日期"], errors="coerce")
fin["年份"] = fin["日期"].dt.year

# 结果变量：这三个在 2015-2025 覆盖率均 >= 97.8%
YCOLS = ["总资产净利润率(%)", "主营业务收入增长率(%)", "资产负债率(%)"]
# 控制变量（供后面 (iiii) 回归使用）
CTRL = ["总资产(元)"]
keep = ["股票代码", "年份"] + YCOLS + [c for c in CTRL if c in fin.columns]

q4 = fin[fin["日期"].dt.strftime("%m-%d") == "12-31"][keep].copy()
print("年报行:", len(q4))
for c in YCOLS:
    print(f"  {c:<22} 非空 {q4[c].notna().mean()*100:5.1f}%")
q4 = q4.dropna(subset=YCOLS)
print("三个 y 都非空:", len(q4))

# ---------- 3. 合并 ----------
m = pat.merge(q4, on=["股票代码", "年份"], how="inner")

print("\n===== 合并结果 =====")
print("观测数:", len(m))
print("公司数:", m["股票代码"].nunique())
print("年份范围:", int(m["年份"].min()), "-", int(m["年份"].max()))
print("\n每年观测数:")
print(m.groupby("年份").size().to_string())

if "总资产(元)" in m.columns:
    m["ln资产"] = np.log(pd.to_numeric(m["总资产(元)"], errors="coerce").replace(0, np.nan))

out = os.path.join(PROC, "主数据集.csv")
m.to_csv(out, index=False, encoding="utf-8-sig")
print("\n已保存:", out)
print(m.head(5).to_string())