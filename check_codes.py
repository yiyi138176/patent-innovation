# -*- coding: utf-8 -*-
"""用官方代码表校验 152 家公司的股票代码是否正确"""
import pandas as pd
import akshare as ak

CSV = r"C:\Users\YYYi3\Desktop\专利数据\公司_股票代码_对照表.csv"
t = pd.read_csv(CSV, dtype=str).fillna("")
t["股票代码"] = t["股票代码"].str.strip()

print("正在拉取官方代码表...")
off = ak.stock_info_a_code_name()
off["code"] = off["code"].astype(str).str.zfill(6)
m = dict(zip(off["code"], off["name"]))
print("对照表:", len(t), "行   官方:", len(off), "家")
print("=" * 74)

print("\n【一、重复的代码】")
d = t[(t["股票代码"] != "") & t["股票代码"].duplicated(keep=False)]
print(d.to_string() if len(d) else "  无")

print("\n【二、代码为空】")
e = t[t["股票代码"] == ""]
print(e.to_string() if len(e) else "  无")

print("\n【三、代码在官方表里查不到】")
b = t[(t["股票代码"] != "") & (~t["股票代码"].isin(m.keys()))]
print(b.to_string() if len(b) else "  无")

print("\n【四、名称对不上的（重点人工核对）】")
t["官方名称"] = t["股票代码"].map(m)
flag = 0
for _, r in t.iterrows():
    code, our, off_name = r["股票代码"], str(r["公司名"]), str(r["官方名称"])
    if code == "":
        continue
    a = our.replace("股份有限公司", "").replace("有限公司", "").replace("集团", "")[:2]
    if off_name != "nan" and a and a not in off_name:
        print(f"  ⚠️ {our[:26]:<26} {code}   官方: {off_name}")
        flag += 1
if flag == 0:
    print("  无")

print("\n【五、完整对照（人工扫一遍）】")
print(t[["公司名", "股票代码", "官方名称"]].to_string())