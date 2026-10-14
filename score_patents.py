# -*- coding: utf-8 -*-
"""
（ii）用大模型给专利文本打分

流程：
  1. 读专利明细.csv
  2. 每个「公司—年份」随机抽最多 PER_FIRM_YEAR 条专利
  3. 逐条调用智谱 API，输出四个维度的分数
  4. 结果保存到 data/llm/llm_scores_<版本>.csv（支持断点续跑 + 每 SAVE_EVERY 条自动存盘）

用法：
  python score_patents.py
  （配置在下面的「配置区」，不用改代码）
"""
import os
import re
import sys
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

# ==================== 配置区（改这里）====================
PROMPT_VER = "v4"          # 用哪一版 prompt：v1 / v2 / v3 / v4
TEST_N = None              # 试跑时填 50；正式跑全部填 None
YEAR_MIN = 2015            # 只给主数据集覆盖的年份打分（省时间）
YEAR_MAX = 2025
PER_FIRM_YEAR = 10         # 每个「公司—年份」最多抽几条
WORKERS = 10               # 并发数（5 约 100 分钟，10 约 50 分钟）
SAVE_EVERY = 100           # 每完成多少条自动存盘一次（防止中断丢进度）
MAX_RETRY = 3
# ========================================================

try:
    from config import ZHIPU_API_KEY, ZHIPU_MODEL
except ImportError:
    print("❌ 找不到 config.py —— 请先 cd 到 patent-innovation 文件夹再运行")
    sys.exit(1)

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
LLMDIR = os.path.join(BASE, "data", "llm")
PROMPT_FILE = os.path.join(BASE, "prompts", f"prompt_{PROMPT_VER}.txt")
OUT_CSV = os.path.join(LLMDIR, f"llm_scores_{PROMPT_VER}.csv")

URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

os.makedirs(LLMDIR, exist_ok=True)

# ---------------- 读取 prompt 模板 ----------------
if not os.path.exists(PROMPT_FILE):
    print(f"❌ 找不到 prompt 模板：{PROMPT_FILE}")
    sys.exit(1)
TEMPLATE = open(PROMPT_FILE, encoding="utf-8").read()
print(f"使用 prompt 版本：{PROMPT_VER}（{len(TEMPLATE)} 字符）")
print(f"输出文件：{OUT_CSV}")

# ---------------- 读取专利明细 ----------------
print("\n正在读取专利明细（175MB，需要一会儿）...")
USE = ["公司名", "股票代码", "年份", "公开（公告）号", "标题 (中文)", "摘要 (中文)", "首项权利要求"]
df = pd.read_csv(os.path.join(PROC, "专利明细.csv"), usecols=lambda c: c in USE)
print(f"  读取完成：{len(df):,} 条")

df["年份"] = pd.to_numeric(df["年份"], errors="coerce")
df = df.dropna(subset=["年份", "摘要 (中文)"]).copy()
df["年份"] = df["年份"].astype(int)
_n0 = len(df)
df = df[(df["年份"] >= YEAR_MIN) & (df["年份"] <= YEAR_MAX)].copy()
print(f"  按年份 {YEAR_MIN}-{YEAR_MAX} 过滤：{_n0:,} -> {len(df):,} 条")
df["专利号"] = df.get("公开（公告）号", pd.Series([""] * len(df))).astype(str)
df["uid"] = df["公司名"].astype(str) + "|" + df["年份"].astype(str) + "|" + df["专利号"]

samp = (df.sample(frac=1.0, random_state=42)
          .groupby(["公司名", "年份"], sort=False)
          .head(PER_FIRM_YEAR)
          .reset_index(drop=True))
print(f"  抽样后：{len(samp):,} 条（每个公司—年份最多 {PER_FIRM_YEAR} 条）")

if TEST_N:
    samp = samp.head(TEST_N).copy()
    print(f"  ⚠️ 测试模式：只跑前 {TEST_N} 条")

# ---------------- 断点续跑 ----------------
results = []          # 内存里累积的全部结果（含上一轮的）
done = set()
if os.path.exists(OUT_CSV):
    try:
        old = pd.read_csv(OUT_CSV)
        results = old.to_dict("records")
        done = set(old["uid"].astype(str).tolist())
        print(f"  ✅ 已有结果 {len(done)} 条，将跳过（断点续跑）")
    except Exception as e:
        print(f"  ⚠️ 读取已有结果失败（{e}），将从头开始")

todo = samp[~samp["uid"].isin(done)].copy()
print(f"  本次需要打分：{len(todo)} 条\n")

if len(todo) == 0:
    print("🎉 已经全部完成了，不需要再跑")
    sys.exit(0)

# ---------------- 打分 ----------------
def build_prompt(row):
    def cut(v, n):
        s = "" if pd.isna(v) else str(v)
        return s[:n]
    return (TEMPLATE
            .replace("{title}", cut(row["标题 (中文)"], 200))
            .replace("{abstract}", cut(row["摘要 (中文)"], 1000))
            .replace("{claim}", cut(row["首项权利要求"], 700)))


JSON_RE = re.compile(r"\{[^{}]*\}")
KEYS = ["novelty", "science", "integration", "distance"]


def parse_scores(txt):
    m = JSON_RE.search(txt or "")
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None
    out = {}
    for k in KEYS:
        if k not in d:
            return None
        try:
            v = int(d[k])
        except Exception:
            return None
        if not (1 <= v <= 10):      # v1/v2 是 1-5，v3 起是 1-10
            return None
        out[k] = v
    return out


lock = threading.Lock()
counter = {"ok": 0, "fail": 0, "tokens": 0}
t0 = time.time()
last_save = [0]


def save_now():
    """把内存里的结果全部写入文件"""
    try:
        pd.DataFrame(results).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        last_save[0] = counter["ok"]
    except Exception as e:
        print(f"  ⚠️ 存盘失败：{e}")


def score_one(row):
    prompt = build_prompt(row)
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
                d = r.json()
                txt = d["choices"][0]["message"]["content"]
                sc = parse_scores(txt)
                tok = d.get("usage", {}).get("total_tokens", 0)
                if sc:
                    return {**sc, "uid": row["uid"], "公司名": row["公司名"],
                            "股票代码": row["股票代码"], "年份": row["年份"],
                            "专利号": row["专利号"], "tokens": tok,
                            "prompt_ver": PROMPT_VER}
                return None
            elif r.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                time.sleep(1)
        except Exception:
            time.sleep(2 ** attempt)
    return None


print(f"开始打分（并发 {WORKERS}，模型 {ZHIPU_MODEL}，每 {SAVE_EVERY} 条自动存盘）...")
print("-" * 66)

fails = []
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(score_one, row): row for _, row in todo.iterrows()}
    for i, fut in enumerate(as_completed(futs), 1):
        row = futs[fut]
        try:
            res = fut.result()
        except Exception:
            res = None
        with lock:
            if res:
                results.append(res)
                counter["ok"] += 1
                counter["tokens"] += res.get("tokens", 0)
                tag = "✅"
            else:
                fails.append(row["uid"])
                counter["fail"] += 1
                tag = "❌"

            if i % 20 == 0 or i == len(todo):
                el = time.time() - t0
                speed = i / el if el > 0 else 0
                eta = (len(todo) - i) / speed / 60 if speed > 0 else 0
                print(f"[{i:>5}/{len(todo)}] {tag}  成功{counter['ok']} 失败{counter['fail']}  "
                      f"已用{el/60:.1f}分  预计还需{eta:.0f}分")

            # 定期存盘
            if counter["ok"] - last_save[0] >= SAVE_EVERY:
                save_now()
                print(f"        💾 已存盘（累计 {len(results)} 条）")

# ---------------- 最后一次存盘 ----------------
save_now()

if fails:
    fp = os.path.join(LLMDIR, f"failed_{PROMPT_VER}.txt")
    with open(fp, "a", encoding="utf-8") as f:
        for u in fails:
            f.write(u + "\n")
    print(f"\n失败的 uid 已记录到 {fp}")

el = time.time() - t0
print()
print("=" * 66)
print(f"prompt 版本：{PROMPT_VER}")
print(f"本次成功 {counter['ok']} 条，失败 {counter['fail']} 条")
print(f"累计已存盘：{len(results)} 条")
print(f"总 token：{counter['tokens']:,}")
print(f"耗时：{el/60:.1f} 分钟   平均 {el/max(len(todo),1):.2f} 秒/条")
print(f"结果文件：{OUT_CSV}")
print("=" * 66)
print()
print("👉 下一步：python review_scores.py")
