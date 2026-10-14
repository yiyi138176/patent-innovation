# -*- coding: utf-8 -*-
"""从专利数据里提取 每家公司 -> 股票代码 的对照表"""
import os, re, glob
from collections import Counter
import pandas as pd

FOLDER = r"C:\Users\YYYi3\Desktop\专利数据\专利数据"
TEST_ONLY = None        # 先只跑前 10 个文件试水；跑通了改成 None 跑全部

files = sorted(glob.glob(os.path.join(FOLDER, "*.xlsx")))
print("找到文件数:", len(files))
if TEST_ONLY:
    files = files[:TEST_ONLY]
    print(f"（本次只试前 {TEST_ONLY} 个）")

CODE_RE = re.compile(r"(\d{6})(?:\.(SZ|SH|BJ))?")

def parse_codes(path):
    try:
        df = pd.read_excel(
            path,
            usecols=lambda c: c in ["工商上市代码", "第一申请人", "标准化申请人", "申请人"],
        )
    except Exception as e:
        return None, f"读取失败({type(e).__name__})"
    if "工商上市代码" not in df.columns:
        return None, "无『工商上市代码』列"
    codes = []
    for v in df["工商上市代码"].dropna().astype(str):
        codes += CODE_RE.findall(v) and [m[0] for m in CODE_RE.findall(v)]
    if not codes:
        return None, "没解析出代码"
    top = Counter(codes).most_common(3)
    return top, f"共{len(codes)}个代码样本"

print("\n" + "=" * 70)
rows = []
for i, f in enumerate(files, 1):
    name = os.path.basename(f).replace(".xlsx", "")
    top, msg = parse_codes(f)
    code = top[0][0] if top else ""
    rows.append({"公司名": name, "股票代码": code})
    print(f"[{i:3d}] {name[:26]:<26} -> {code:<8} {msg}")
    if top and len(top) > 1:
        print(f"        其他候选: {top[1:]}")

out = os.path.join(os.path.dirname(FOLDER), "公司_股票代码_对照表.csv")
pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
print("\n已保存:", out)