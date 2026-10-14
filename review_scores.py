# -*- coding: utf-8 -*-
"""
抽查工具：把专利原文和 LLM 打的分放在一起，方便人肉判断分数合不合理

会自动找出 data/llm/ 下所有 llm_scores_*.csv（各版本），
对每个版本打印分数分布，并导出可在 Excel 打开的小文件。
"""
import os
import glob
import pandas as pd

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
LLMDIR = os.path.join(BASE, "data", "llm")
DETAIL = os.path.join(BASE, "data", "processed", "专利明细.csv")

SHOW = 6        # 每个版本在终端打印几条
MAXSCORE = 10   # 分数上限（v1/v2 是 5，v3 起是 10）

files = sorted(glob.glob(os.path.join(LLMDIR, "llm_scores_*.csv")))
if not files:
    print("❌ 还没有打分结果，先跑 llm_score.py")
    raise SystemExit

print("正在读取专利明细（175MB）...")
det = pd.read_csv(DETAIL, usecols=lambda c: c in
                  ["公开（公告）号", "标题 (中文)", "摘要 (中文)", "首项权利要求"])
det["专利号"] = det["公开（公告）号"].astype(str)
print(f"  专利明细 {len(det):,} 条\n")

NAMES = [("novelty", "新颖性"), ("science", "科学强度"),
         ("integration", "跨领域"), ("distance", "商业化距离")]


def show_dist(m, ver):
    print("=" * 78)
    print(f"【prompt 版本 {ver}】共 {len(m)} 条")
    print("=" * 78)
    for k, name in NAMES:
        vals = pd.to_numeric(m[k], errors="coerce").dropna().astype(int)
        total = len(vals)
        vc = vals.value_counts().sort_index()
        mx = int(vals.max()) if total else MAXSCORE
        top = vc.max() if total else 0
        line = " ".join(f"{i}:{int(vc.get(i, 0))}" for i in range(1, max(mx, 5) + 1))
        flag = "  ⚠️ 过于集中" if total and top / total >= 0.8 else ""
        print(f"  {name:<7} {line}")
        print(f"          → 取值种类 {len(vc)} 种，最常见值占 {top/total*100:.0f}%"
              f"，标准差 {vals.std():.2f}{flag}")
    print()


for f in files:
    ver = os.path.basename(f).replace("llm_scores_", "").replace(".csv", "")
    sc = pd.read_csv(f, dtype=str)
    if sc.empty:
        continue
    m = sc.merge(det[["专利号", "标题 (中文)", "摘要 (中文)", "首项权利要求"]],
                 on="专利号", how="left", suffixes=("", "_d"))

    show_dist(m, ver)

    for _, r in m.sample(min(SHOW, len(m)), random_state=7).iterrows():
        print(f"  · 【{r['公司名']} / {r['年份']}】{str(r['标题 (中文)'])[:46]}")
        print(f"      分数：n={r['novelty']} s={r['science']} i={r['integration']} d={r['distance']}")
        ab = str(r.get("摘要 (中文)", ""))
        print(f"      摘要：{ab[:150]}{'...' if len(ab) > 150 else ''}")
    print()

    cols = [c for c in ["公司名", "股票代码", "年份", "标题 (中文)", "novelty", "science",
                        "integration", "distance", "摘要 (中文)", "首项权利要求"] if c in m.columns]
    out = os.path.join(LLMDIR, f"抽查_原文与打分_{ver}.csv")
    m[cols].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  ✅ 已导出（可直接用 Excel 打开）：{out}\n")

print("=" * 78)
print("📊 判断标准")
print("=" * 78)
print("  ① 「最常见值占比」越低越好。超过 80% 说明这版 prompt 缺区分度。")
print("  ② 「标准差」越大说明分数越分散，作为特征越有用。")
print("  ③ 「取值种类」越多越好（理想情况 5-10 种都有）。")
