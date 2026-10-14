# -*- coding: utf-8 -*-
"""
补抓企业「成立日期」（用于计算 SA 融资约束指数）
数据源：巨潮公司概况 ak.stock_profile_cninfo

输出：data/processed/公司_成立日期.csv（断点续跑）
"""
import os
import re
import sys
import time

import pandas as pd

try:
    import akshare as ak
except ImportError:
    print("❌ 没装 akshare")
    sys.exit(1)

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
OUT_CSV = os.path.join(PROC, "公司_成立日期.csv")

TEST_N = None

df = pd.read_csv(os.path.join(PROC, "公司_行业地区.csv"), dtype=str).fillna("")
df["股票代码"] = df["股票代码"].str.zfill(6)
print(f"需要抓成立日期的公司：{len(df)} 家")
if TEST_N:
    df = df.head(TEST_N)

done = {}
if os.path.exists(OUT_CSV):
    old = pd.read_csv(OUT_CSV, dtype=str).fillna("")
    old["股票代码"] = old["股票代码"].str.zfill(6)
    done = {r["股票代码"]: r for _, r in old.iterrows()
            if str(r.get("成立日期", "")).strip() not in ("", "nan")}
    print(f"已有 {len(done)} 家，将跳过")

todo = df[~df["股票代码"].isin(done.keys())]
print(f"本次需要查询：{len(todo)} 家\n")
if len(todo) == 0:
    print("都已查完")
    sys.exit(0)

DATE_RE = re.compile(r"(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})")


def get_found_date(code):
    try:
        d = ak.stock_profile_cninfo(symbol=code)
        if isinstance(d, pd.DataFrame) and len(d):
            raw = str(d.iloc[0].get("成立日期", "") or "")
            m = DATE_RE.search(raw)
            if m:
                return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    except Exception:
        pass
    return ""


rows = list(done.values())
t0 = time.time()
for i, r in enumerate(todo.itertuples(), 1):
    code, name = r.股票代码, r.公司名
    fd = get_found_date(code)
    rows.append({"股票代码": code, "公司名": name, "成立日期": fd})
    tag = "✅" if fd else "⚠️"
    print(f"[{i:>3}/{len(todo)}] {tag} {name[:20]:<20} 成立日期 = {fd or '（空）'}")
    if i % 20 == 0:
        pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f"        💾 已存盘（{len(rows)} 家）")
    time.sleep(0.3)

out = pd.DataFrame(rows)
out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print()
print("=" * 66)
print(f"完成，共 {len(out)} 家，耗时 {(time.time()-t0)/60:.1f} 分钟")
ok = (out["成立日期"].astype(str).str.strip() != "").sum()
print(f"成立日期有值：{ok} 家")
if ok:
    yr = pd.to_datetime(out["成立日期"], errors="coerce").dt.year
    print(f"成立年份范围：{int(yr.min())} - {int(yr.max())}")
    print("\n【成立年份分布】")
    print(yr.value_counts().sort_index().tail(20).to_string())
print(f"\n已保存：{OUT_CSV}")
print("=" * 66)
