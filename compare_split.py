# -*- coding: utf-8 -*-
"""对比：v4（一次调用打四维）vs 分开调用，四种相关性的真实差异。不调用 API。"""
import io, sys
import numpy as np
import pandas as pd

_OUT = open(r"C:\Users\YYYi3\Documents\deepseek-harness\default-workspace\_cmp.txt", "w", encoding="utf-8")
sys.stdout = _OUT

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
LLMDIR = BASE + r"\data\llm"
LLM = ["novelty", "science", "integration", "distance"]
CN = {"novelty": "技术新颖性", "science": "科学基础强度",
      "integration": "跨领域整合度", "distance": "商业化距离"}

v4 = pd.read_csv(LLMDIR + r"\llm_scores_v4.csv")
sp = pd.read_csv(LLMDIR + r"\test_split.csv")
print(f"v4 全量：{len(v4):,} 条    分开调用测试：{len(sp)} 条")

m = sp.merge(v4, on="uid", suffixes=("_split", "_v4"))
print(f"两种方式都有的：{len(m)} 条\n")


def show(tag, df):
    c = df.corr()
    c.index = [CN[i] for i in c.index]
    c.columns = [CN[i] for i in c.columns]
    off = c.values[np.triu_indices(4, 1)]
    print("=" * 74)
    print(f"{tag}")
    print("=" * 74)
    print(c.round(3).to_string())
    print(f"  → 维度间平均相关 {off.mean():.3f}   最大 {off.max():.3f}\n")
    return off.mean(), off.max()


print("########## 第一层：专利级（每条专利一行）##########\n")
a1, a1m = show("【A】v4：一次调用同时打四个维度（200 条专利）",
               m[[f"{c}_v4" for c in LLM]].rename(columns=lambda x: x[:-3]))
b1, b1m = show("【B】分开调用：每个维度独立一次调用（同 200 条专利）",
               m[[f"{c}_split" for c in LLM]].rename(columns=lambda x: x[:-6]))

print("=" * 74)
print("两种方式在同一维度上的一致性（同一条专利，两次评分相关多高）")
print("=" * 74)
for c in LLM:
    r = m[f"{c}_v4"].corr(m[f"{c}_split"])
    print(f"  {CN[c]:<8} r = {r:.3f}")

# 公司-年份层面
print()
print("########## 第二层：公司—年份层面（聚合后，这才是进模型的数据）##########\n")
mv4 = v4.groupby(["公司名", "年份"], as_index=False)[LLM].mean()
msp = sp.merge(v4[["uid", "公司名", "年份"]], on="uid", how="left")
msp = msp.dropna(subset=["公司名"])
msp = msp.groupby(["公司名", "年份"], as_index=False)[LLM].mean()
print(f"v4 聚合出 {len(mv4):,} 个公司—年份；分开调用测试聚合出 {len(msp):,} 个（样本小，仅供参考）\n")

a2, a2m = show("【A】v4 全量在公司—年份层面的四维相关（1,269 个观测）", mv4[LLM])
a3, a3m = show("【B】分开调用在测试样本的公司—年份层面（仅 ~200 条专利聚合，参考）", msp[LLM])

print("=" * 74)
print("结论")
print("=" * 74)
print(f"  专利级：v4 平均相关 {a1:.3f}  →  分开调用 {b1:.3f}   （变化 {b1-a1:+.3f}）")
print(f"  公司—年份级：v4 平均相关 {a2:.3f}  →  分开调用 {a3:.3f}   （变化 {a3-a2:+.3f}，样本不可比）")
print()
if b1 - a1 < -0.15:
    print("  ✅ 分开调用显著降低了相关性 → 值得重跑全量")
elif b1 - a1 < -0.05:
    print("  ◐ 分开调用略有降低 → 收益有限，可自己决定")
else:
    print("  ❌ 分开调用没有降低相关性 → 维度相关是客观规律，保持 v4")
_OUT.close()
print("done")
