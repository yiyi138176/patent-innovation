# -*- coding: utf-8 -*-
"""
（iiii）DML 修正版 v2 —— 让 DML 与主回归的固定效应设定一致

修正历史：
  - 原 DML 只做「企业内去均值 + 年份虚拟变量」，没控制行业×年份、地区×年份固定效应
    → 与主回归不是同一设定，导致 SA 指数上结论相反
  - 用 pyfixest 求残差时，它会剔除 singleton 观测，导致残差长度与样本不一致
    → 改用**交替投影法（alternating projections）**自己求残差，
      这是 reghdfe / pyfixest 内部使用的同一算法，但索引完全由我们控制

做法：把 y、x、控制变量分别对「企业 + 年份 + 行业×年份 + 地区×年份」四类固定效应
      做迭代去均值（交替投影），再对残差做 5 折交叉拟合 DML。

输出：results/iiii_DML_修正版.csv
"""
import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
OUTDIR = os.path.join(BASE, "results")
os.makedirs(OUTDIR, exist_ok=True)

YV = ["y_lev", "y_sa", "y_roa", "y_growth"]
Y_CN = {"y_lev": "资产负债率（杠杆）", "y_sa": "SA指数（融资约束）",
        "y_roa": "总资产净利润率", "y_growth": "主营业务收入增长率"}
X = "x_integration"
XV = ["x_novelty", "x_science", "x_integration", "x_distance"]

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

# ---------- 1. 数据 ----------
m = pd.read_csv(os.path.join(PROC, "主数据集_含SA.csv"), dtype={"firm_id": str})
BF = ["ln_patent", "avg_claims", "avg_cites", "avg_inventors", "avg_fcwords",
      "avg_family", "avg_value", "avg_tech_adv", "avg_tech_stab",
      "avg_protect", "avg_pages", "ipc_fields"]
for c in BF + XV + YV:
    m[c] = pd.to_numeric(m[c], errors="coerce")
m = m.dropna(subset=YV).copy()
m["year"] = m["year"].astype(int)
m = m.reset_index(drop=True)
print(f"样本：{len(m):,} 个观测 / {m['firm_id'].nunique()} 家公司")

# 固定效应维度（行业×年份、地区×年份 用组合键）
m["iy"] = m["industry"].astype(str) + "_" + m["year"].astype(str)
m["ry"] = m["region"].astype(str) + "_" + m["year"].astype(str)
FE_DIMS = ["firm_id", "year", "iy", "ry"]


# ---------- 2. 交替投影法去均值 ----------
def demean_all(df, cols, fe_dims, tol=1e-10, max_iter=500):
    Xm = df[cols].astype(float).copy()
    keys = [df[d].values for d in fe_dims]
    n_iter = 0
    for it in range(max_iter):
        n_iter = it + 1
        delta = 0.0
        for k in keys:
            means = Xm.groupby(k).transform("mean")
            delta = max(delta, float(np.abs(means.values).max()))
            Xm = Xm - means
        if delta < tol:
            break
    return Xm, n_iter


print("\n正在用交替投影法把变量对四类固定效应去均值（这一步最慢）...")
cols = [X] + BF + YV
R, n_it = demean_all(m, cols, FE_DIMS)
print(f"  收敛用了 {n_it} 轮迭代")
for c in cols:
    print(f"    {c:<16} 去均值后标准差 = {R[c].std():.4f}")

R = R.reset_index(drop=True)
R["firm_id"] = m["firm_id"].values
Xr = X
Zr = list(BF)


# ---------- 3. 交叉拟合 DML ----------
def dml(data, ycol, xcol, zcols, learner="rf", folds=5, seed=42):
    d = data.dropna(subset=[ycol, xcol] + zcols).copy()
    Y = d[ycol].values.astype(float)
    Xv = d[xcol].values.astype(float)
    Z = StandardScaler().fit_transform(d[zcols].values.astype(float))
    kf = KFold(n_splits=folds, shuffle=True, random_state=seed)
    yr = np.zeros_like(Y); xr = np.zeros_like(Xv)
    for tr, te in kf.split(Z):
        if learner == "rf":
            my = RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                       random_state=seed, n_jobs=-1).fit(Z[tr], Y[tr])
            mx = RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                       random_state=seed, n_jobs=-1).fit(Z[tr], Xv[tr])
        else:
            my = LassoCV(cv=3, random_state=seed, max_iter=3000).fit(Z[tr], Y[tr])
            mx = LassoCV(cv=3, random_state=seed, max_iter=3000).fit(Z[tr], Xv[tr])
        yr[te] = Y[te] - my.predict(Z[te])
        xr[te] = Xv[te] - mx.predict(Z[te])
    r = sm.OLS(yr, sm.add_constant(xr.reshape(-1, 1))).fit(cov_type="HC1")
    return r.params[1], r.bse[1], r.pvalues[1], len(d)


print()
print("=" * 84)
print("DML 修正版：y、x、控制变量都已对【四类固定效应】去均值，与主回归设定一致")
print("=" * 84)
rows = []
for y in YV:
    for learner, nm in [("rf", "随机森林"), ("lasso", "LASSO")]:
        print(f"  正在跑 {Y_CN[y]} × {nm} ...", flush=True)
        b, se, p, n = dml(R, y, Xr, Zr, learner=learner)
        st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
        print(f"    theta = {b:+.4f}   se {se:.4f}   t = {b/se:+.2f}   p = {p:.4f} {st}   n={n:,}")
        rows.append({"被解释变量": Y_CN[y], "变量名": y, "学习器": nm,
                     "theta": round(b, 4), "标准误": round(se, 4),
                     "t值": round(b / se, 2), "p值": round(p, 4),
                     "显著性": st, "观测数": n})
pd.DataFrame(rows).to_csv(os.path.join(OUTDIR, "iiii_DML_修正版.csv"),
                          index=False, encoding="utf-8-sig")

# ---------- 4. 与主回归并列对比 ----------
print()
print("=" * 84)
print("与主回归对比（修正后是否一致）")
print("=" * 84)
main_map = {}
for fn, xcol in [("iiii_SA_回归.csv", "变量名")]:
    p = os.path.join(OUTDIR, fn)
    if os.path.exists(p):
        t = pd.read_csv(p, dtype=str)
        main_map = {r["变量名"]: r for _, r in t.iterrows()}

print(f"{'被解释变量':<24}{'主回归':>20}{'DML-随机森林':>22}{'DML-LASSO':>22}")
print("-" * 88)
for y in YV:
    mr = main_map.get(y)
    a = f"{mr['系数']} (p={mr['p值']})" if mr is not None else "—"
    r1 = next((r for r in rows if r["变量名"] == y and r["学习器"] == "随机森林"), None)
    r2 = next((r for r in rows if r["变量名"] == y and r["学习器"] == "LASSO"), None)
    b = f"{r1['theta']} (p={r1['p值']})" if r1 else "—"
    c = f"{r2['theta']} (p={r2['p值']})" if r2 else "—"
    print(f"{Y_CN[y]:<24}{a:>20}{b:>22}{c:>22}")

print()
print("=" * 84)
print("完成。结果：results/iiii_DML_修正版.csv")
print("=" * 84)
