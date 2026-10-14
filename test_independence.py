# -*- coding: utf-8 -*-
"""
测试：把四个维度拆成四次独立调用，看它们之间的相关性会不会降下来

做法：
  1. 从已经用 v4（一次调用打四维）打过分的数据里，随机抽 N 条专利
  2. 对这些专利，用「分开调用」的方式各打一次分（每条专利 4 次调用）
  3. 比较两种方式的四维相关系数矩阵

输出：
  data/llm/test_split.csv
  （终端打印两个相关系数矩阵）
"""
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests

try:
    from config import ZHIPU_API_KEY, ZHIPU_MODEL
except ImportError:
    print("❌ 找不到 config.py —— 请先 cd 到 patent-innovation 文件夹再运行")
    sys.exit(1)

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
LLMDIR = os.path.join(BASE, "data", "llm")
SPLIT_FILE = os.path.join(BASE, "prompts", "prompt_split.txt")
OUT_CSV = os.path.join(LLMDIR, "test_split.csv")

URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
LLM = ["novelty", "science", "integration", "distance"]
LLM_CN = {"novelty": "技术新颖性", "science": "科学基础强度",
          "integration": "跨领域整合度", "distance": "商业化距离"}

N_TEST = 200        # 抽多少条专利做测试
WORKERS = 10
MAX_RETRY = 3

# ---------------- 读取四个独立提示词 ----------------
raw = open(SPLIT_FILE, encoding="utf-8").read()
TEMPLATES = {}
for m in re.finditer(r"===(\w+)===(.*?)(?====\w+===|$)", raw, re.S):
    TEMPLATES[m.group(1)] = m.group(2).strip()
for k in LLM:
    if k not in TEMPLATES:
        print(f"❌ 提示词文件里缺少 {k}")
        sys.exit(1)
print(f"已载入 4 个独立提示词：{list(TEMPLATES.keys())}")

# ---------------- 抽样：从 v4 已打分的专利里选 ----------------
v4 = pd.read_csv(os.path.join(LLMDIR, "llm_scores_v4.csv"), dtype={"专利号": str})
v4["年份"] = pd.to_numeric(v4["年份"], errors="coerce")
v4 = v4.dropna(subset=["年份"])
pick = v4.sample(min(N_TEST, len(v4)), random_state=123)[["uid", "公司名", "年份", "专利号"]].copy()
print(f"从 v4 结果里随机抽 {len(pick)} 条专利做测试")

print("正在读取专利明细...")
det = pd.read_csv(os.path.join(PROC, "专利明细.csv"),
                  usecols=lambda c: c in ["公开（公告）号", "标题 (中文)", "摘要 (中文)", "首项权利要求"])
det["专利号"] = det["公开（公告）号"].astype(str)
pick = pick.merge(det[["专利号", "标题 (中文)", "摘要 (中文)", "首项权利要求"]],
                  on="专利号", how="left")
miss = pick["摘要 (中文)"].isna().sum()
if miss:
    print(f"  ⚠️ 有 {miss} 条匹配不到原文，将跳过")
    pick = pick.dropna(subset=["摘要 (中文)"])
print(f"  实际测试 {len(pick)} 条")


def build_prompt(dim, row):
    def cut(v, n):
        s = "" if pd.isna(v) else str(v)
        return s[:n]
    return (TEMPLATES[dim]
            .replace("{title}", cut(row["标题 (中文)"], 200))
            .replace("{abstract}", cut(row["摘要 (中文)"], 1000))
            .replace("{claim}", cut(row["首项权利要求"], 700)))


NUM_RE = re.compile(r"\b(\d{1,2})\b")


def call_one(dim, row):
    prompt = build_prompt(dim, row)
    for attempt in range(MAX_RETRY):
        try:
            r = requests.post(
                URL,
                headers={"Authorization": f"Bearer {ZHIPU_API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": ZHIPU_MODEL,
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.0},
                timeout=90,
            )
            if r.status_code == 200:
                txt = r.json()["choices"][0]["message"]["content"]
                m = NUM_RE.search(txt or "")
                if m:
                    v = int(m.group(1))
                    if 1 <= v <= 10:
                        return v
                return None
            elif r.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                time.sleep(1)
        except Exception:
            time.sleep(2 ** attempt)
    return None


print(f"\n开始测试（每条专利 4 次独立调用，共 {len(pick)*4} 次，并发 {WORKERS}）...")
t0 = time.time()
rows = []
lock = threading.Lock()
done = {"n": 0}

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {}
    for _, row in pick.iterrows():
        for dim in LLM:
            futs[ex.submit(call_one, dim, row)] = (row["uid"], dim)
    got = {}
    for fut in as_completed(futs):
        uid, dim = futs[fut]
        try:
            v = fut.result()
        except Exception:
            v = None
        with lock:
            got.setdefault(uid, {})[dim] = v
            done["n"] += 1
            if done["n"] % 100 == 0:
                print(f"   已完成 {done['n']}/{len(pick)*4} 次调用  "
                      f"（{time.time()-t0:.0f} 秒）")

out = pd.DataFrame([{"uid": k, **v} for k, v in got.items()])
out = out.dropna()
print(f"\n✅ 成功打分 {len(out)} 条（每条 4 个维度）")
out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

# ---------------- 比较相关系数 ----------------
v4map = v4.set_index("uid")[LLM]
merged = out.set_index("uid").join(v4map, rsuffix="_v4", how="inner")
print(f"两种方式都成功的：{len(merged)} 条\n")

print("=" * 70)
print("【方式 A：一次调用打四维（v4）】相关系数矩阵")
print("=" * 70)
cA = merged[[f"{c}_v4" for c in LLM]].rename(columns=lambda x: x[:-3]).corr()
cA.index = [LLM_CN[c] for c in cA.index]
cA.columns = [LLM_CN[c] for c in cA.columns]
print(cA.round(3).to_string())
offA = cA.values[np.triu_indices(4, 1)]
print(f"\n  维度间平均相关系数：{offA.mean():.3f}   最大：{offA.max():.3f}")

print()
print("=" * 70)
print("【方式 B：四次独立调用（本次测试）】相关系数矩阵")
print("=" * 70)
cB = merged[LLM].corr()
cB.index = [LLM_CN[c] for c in cB.index]
cB.columns = [LLM_CN[c] for c in cB.columns]
print(cB.round(3).to_string())
offB = cB.values[np.triu_indices(4, 1)]
print(f"\n  维度间平均相关系数：{offB.mean():.3f}   最大：{offB.max():.3f}")

print()
print("=" * 70)
print("两种方式在同一维度上的一致性（同一条专利，两次评分相关多高）")
print("=" * 70)
for c in LLM:
    print(f"  {LLM_CN[c]:<8} r = {merged[f'{c}_v4'].corr(merged[c]):.3f}")
print()
print("=" * 70)
d = offA.mean() - offB.mean()
if offB.mean() < offA.mean() - 0.15:
    print(f"✅ 独立调用把平均相关从 {offA.mean():.3f} 降到 {offB.mean():.3f}（降了 {d:.3f}）")
    print("   → 值得重跑全量（4 倍调用量，约 3.5 小时）")
elif offB.mean() < offA.mean() - 0.05:
    print(f"◐ 略有下降：{offA.mean():.3f} → {offB.mean():.3f}（降了 {d:.3f}）")
    print("   → 可以重跑，但收益有限；也可以保持现状并在报告中说明")
else:
    print(f"❌ 几乎没降：{offA.mean():.3f} → {offB.mean():.3f}（降了 {d:.3f}）")
    print("   → 说明维度相关是客观规律，不是提示词设计问题；保持 v4，报告中说明")
print("=" * 70)
