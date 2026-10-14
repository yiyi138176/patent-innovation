# -*- coding: utf-8 -*-
"""
（ii）大模型语义特征的增量解释力与正交性检验（修正版）

修正点：
  1. 专利特征缺失填 0 —— 与 model_i.py 口径一致（样本 1,270）
  2. A / B / C 三组用同一个模型（RidgeCV），增量才是"特征的贡献"
  3. 改用 5 折「按公司分组」交叉验证，R² 取均值和标准差，更稳

输出：
  results/ii_增量解释力.csv
  results/ii_正交性检验.csv
  results/ii_特征重要性.csv
  data/processed/主数据集_含语义特征.csv
"""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
LLMDIR = os.path.join(BASE, "data", "llm")
OUTDIR = os.path.join(BASE, "results")
os.makedirs(OUTDIR, exist_ok=True)

LLM = ["novelty", "science", "integration", "distance"]
LLM_CN = {"novelty": "技术新颖性", "science": "科学基础强度",
          "integration": "跨领域整合度", "distance": "商业化距离"}
YCOLS = ["总资产净利润率(%)", "主营业务收入增长率(%)", "资产负债率(%)"]
ALPHAS = np.logspace(-3, 3, 25)

# ================= 1. 聚合 =================
print("=" * 76)
print("第 1 步：把专利级打分聚合到「公司—年份」")
print("=" * 76)
sc = pd.read_csv(os.path.join(LLMDIR, "llm_scores_v4.csv"), dtype={"股票代码": str})
print(f"  专利级打分：{sc.shape[0]:,} 条")
for c in LLM:
    sc[c] = pd.to_numeric(sc[c], errors="coerce")
sc["年份"] = pd.to_numeric(sc["年份"], errors="coerce")
sc = sc.dropna(subset=["年份"] + LLM).copy()
sc["年份"] = sc["年份"].astype(int)

agg = (sc.groupby(["公司名", "年份"])
         .agg(**{f"LLM_{c}": (c, "mean") for c in LLM},
              **{"打分专利数": ("novelty", "size")})
         .reset_index())
print(f"  聚合后：{len(agg):,} 个公司—年份，平均每个公司—年份 {agg['打分专利数'].mean():.1f} 条专利")

# ================= 2. 合并 =================
print()
print("=" * 76)
print("第 2 步：与主数据集合并")
print("=" * 76)
df = pd.read_csv(os.path.join(PROC, "主数据集.csv"), dtype={"股票代码": str})
m = df.merge(agg, on=["公司名", "年份"], how="inner")
print(f"  主数据集 {len(df):,} → 合并后 {len(m):,} 个观测 / {m['股票代码'].nunique()} 家公司")
print(f"  年份：{int(m['年份'].min())} - {int(m['年份'].max())}")

BASE_FEATS = ["平均权利要求数", "平均被引次数", "平均发明人数", "平均首权字数",
              "平均同族数", "平均合享价值度", "平均技术先进性", "平均技术稳定性",
              "平均保护范围", "平均文献页数", "IPC领域数"]
BASE_FEATS = [f for f in BASE_FEATS if f in m.columns]
m["ln专利数"] = np.log1p(m["专利数"])
BF = ["ln专利数"] + BASE_FEATS
LF = [f"LLM_{c}" for c in LLM]

# ★ 修正 1：缺失填 0（与 model_i.py 一致）
for c in BF + LF:
    m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0)
m = m.dropna(subset=YCOLS).copy()
m["年份"] = m["年份"].astype(int)
# 结果变量缩尾（与 model_i.py 一致）
for c in YCOLS:
    lo, hi = m[c].quantile([0.01, 0.99])
    m[c] = m[c].clip(lo, hi)

print(f"  ✅ 清理后进入模型：{len(m):,} 个观测（数量特征 {len(BF)} 个，语义特征 {len(LF)} 个）")

# ================= 3. 交叉验证的增量 R² =================
print()
print("=" * 76)
print("第 3 步：三组模型的增量解释力（5 折按公司分组交叉验证，均为 RidgeCV）")
print("=" * 76)


def cv_r2(data, feats, y, groups=None):
    X = data[feats].values
    Yv = data[y].values
    if groups is None:
        groups = data["股票代码"].values
    gkf = GroupKFold(n_splits=5)
    scores = []
    for tr, te in gkf.split(X, Yv, groups=groups):
        sc_ = StandardScaler().fit(X[tr])
        mdl = RidgeCV(alphas=ALPHAS).fit(sc_.transform(X[tr]), Yv[tr])
        scores.append(r2_score(Yv[te], mdl.predict(sc_.transform(X[te]))))
    return float(np.mean(scores)), float(np.std(scores))


rows = []
for tag, kind in [("① 原始（跨公司）", "pool"),
                  ("② 年度去均值", "year"),
                  ("③ 公司内去均值", "firm")]:
    d = m.copy()
    if kind == "year":
        for c in YCOLS + BF + LF:
            d[c] = d[c] - d.groupby("年份")[c].transform("mean")
    elif kind == "firm":
        for c in YCOLS + BF + LF:
            d[c] = d[c] - d.groupby("股票代码")[c].transform("mean")

    for y in YCOLS:
        mA, sA = cv_r2(d, BF, y)
        mB, sB = cv_r2(d, BF + LF, y)
        mC, sC = cv_r2(d, LF, y)
        rows.append({"设定": tag, "结果变量": y,
                     "A_仅数量": round(mA, 4), "B_数量+语义": round(mB, 4),
                     "C_仅语义": round(mC, 4),
                     "增量(B-A)": round(mB - mA, 4),
                     "标准差A": round(sA, 3), "标准差B": round(sB, 3)})

res = pd.DataFrame(rows)
print(res.to_string(index=False))
res.to_csv(os.path.join(OUTDIR, "ii_增量解释力.csv"), index=False, encoding="utf-8-sig")
print(f"\n已保存：{os.path.join(OUTDIR, 'ii_增量解释力.csv')}")

# ================= 4. 语义特征的相对重要性 =================
print()
print("=" * 76)
print("第 4 步：单独加入每个语义维度的增量（逐个加，看谁最有贡献）")
print("=" * 76)
one_rows = []
for y in YCOLS:
    r0, _ = cv_r2(m, BF, y)
    for c in LLM:
        r1, _ = cv_r2(m, BF + [f"LLM_{c}"], y)
        one_rows.append({"结果变量": y, "加入的维度": LLM_CN[c],
                         "基准R2": round(r0, 4), "加入后R2": round(r1, 4),
                         "增量": round(r1 - r0, 4)})
one = pd.DataFrame(one_rows)
print(one.to_string(index=False))
one.to_csv(os.path.join(OUTDIR, "ii_特征重要性.csv"), index=False, encoding="utf-8-sig")
print(f"\n已保存：{os.path.join(OUTDIR, 'ii_特征重要性.csv')}")

# ================= 5. 正交性检验 =================
print()
print("=" * 76)
print("第 5 步：正交性检验（语义特征里有多少是数量特征解释不了的）")
print("=" * 76)

print("\n【5.1】语义特征 × 数量特征 的相关系数")
corr = pd.DataFrame(index=[LLM_CN[c] for c in LLM], columns=[f[:9] for f in BF], dtype=float)
for c in LLM:
    for f in BF:
        corr.loc[LLM_CN[c], f[:9]] = m[f"LLM_{c}"].corr(m[f])
print(corr.round(2).to_string())
print(f"\n  最大 |相关系数|：{np.nanmax(np.abs(corr.values)):.3f}")
print(f"  平均 |相关系数|：{np.nanmean(np.abs(corr.values)):.3f}")
corr.to_csv(os.path.join(OUTDIR, "ii_相关系数矩阵.csv"), encoding="utf-8-sig")

print("\n【5.2】用数量特征回归每个语义特征（R² 越低 = 正交性越强）")
sc_ = StandardScaler()
Xb = sc_.fit_transform(m[BF].values)
orth_rows = []
for c in LLM:
    mdl = RidgeCV(alphas=ALPHAS).fit(Xb, m[f"LLM_{c}"].values)
    r2 = mdl.score(Xb, m[f"LLM_{c}"].values)
    orth_rows.append({"语义维度": LLM_CN[c],
                      "被数量特征解释的R2": round(r2, 4),
                      "正交部分(1-R2)": round(1 - r2, 4)})
orth = pd.DataFrame(orth_rows)
print(orth.to_string(index=False))
orth.to_csv(os.path.join(OUTDIR, "ii_正交性检验.csv"), index=False, encoding="utf-8-sig")

# ================= 6. 保存 =================
m.to_csv(os.path.join(PROC, "主数据集_含语义特征.csv"), index=False, encoding="utf-8-sig")
print()
print("=" * 76)
print(f"✅ 观测数：{len(m):,}（应接近 1,270，说明口径已与 model_i.py 一致）")
print(f"✅ 含语义特征的数据集：{os.path.join(PROC, '主数据集_含语义特征.csv')}")
print("=" * 76)
