# -*- coding: utf-8 -*-
"""按股票代码批量拉取财务数据（akshare）"""
import os, time
import pandas as pd
import akshare as ak

CSV = r"C:\Users\YYYi3\Desktop\专利数据\公司_股票代码_对照表.csv"
OUTDIR = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
os.makedirs(OUTDIR, exist_ok=True)

TEST_N = None          # 试跑时填 5；正式跑填 None

tbl = pd.read_csv(CSV, dtype=str).fillna("")
tbl["股票代码"] = tbl["股票代码"].str.strip()
tbl = tbl[tbl["股票代码"] != ""]

# ===== 数据质量修正（依据 akshare 官方代码表校验，见 check_codes.py）=====
# 1) 代码修正：大富科技原误提取为 300127（与银河磁体重复），官方代码为 300134
CODE_FIX = {
    "大富科技(安徽)股份有限公司": "300134",
}
tbl["股票代码"] = tbl.apply(
    lambda r: CODE_FIX.get(r["公司名"], r["股票代码"]), axis=1)

# 2) 剔除异常公司
EXCLUDE = [
    "东富龙科技集团股份有限公司",      # 文件内容与文件名不符（实为华中数控的专利）
    "包头天和磁材科技股份有限公司",    # 工商上市代码为空
]
n0 = len(tbl)
tbl = tbl[~tbl["公司名"].isin(EXCLUDE)]
print(f"剔除异常公司 {n0 - len(tbl)} 家，剩余 {len(tbl)} 家")
# =====================================================================

if TEST_N:
    tbl = tbl.head(TEST_N)
    print(f"（本次只试前 {TEST_N} 家）")

KEEP = ["日期", "总资产净利润率(%)", "主营业务收入增长率(%)", "销售毛利率(%)"]

allrows = []
for i, (name, code) in enumerate(zip(tbl["公司名"], tbl["股票代码"]), 1):
    code = str(code)[:6]
    try:
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2015")
        sub = df.copy()
        sub["公司名"] = name
        sub["股票代码"] = code
        allrows.append(sub)
        print(f"[{i:3d}] {name[:24]:<24} {code}  OK  {len(sub)} 行")
    except Exception as e:
        print(f"[{i:3d}] {name[:24]:<24} {code}  FAIL  {type(e).__name__}: {e}")
    time.sleep(0.5)

if allrows:
    out = pd.concat(allrows, ignore_index=True)
    p = os.path.join(OUTDIR, "企业财务数据_full.csv")
    out.to_csv(p, index=False, encoding="utf-8-sig")
    print("\n合并后形状:", out.shape)
    print("已保存:", p)
    print(out.head(8).to_string())
else:
    print("\n没有拉到任何数据，检查一下上面的报错")