# -*- coding: utf-8 -*-
"""
补充检验：-4.14 是不是「共同因子」的代理？
五组同规格回归，只改解释变量
"""
import os
import numpy as np
import pandas as pd
import pyfixest as pf
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
SRC = os.path.join(BASE, "stata", "main_dataset.csv")
OUT = os.path.join(BASE, "results", "iiii_共同因子检验.csv")

df = pd.read_csv(SRC, dtype={"firm": int})
df["industry_year"] = df["industry"].astype(str) + "_" + df["year"].astype(str)
df["region_year"] = df["region"].astype(str) + "_" + df["year"].astype(str)

X4 = ["x_novelty", "x_science", "x_integration", "x_distance"]
for c in X4 + ["y_growth"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# ① 残差化：剥离另外三个维度后的整合度
Z = df[["x_novelty", "x_science", "x_distance"]].values
xi = df[["x_integration"]].values
df["x_int_resid"] = (xi - LinearRegression().fit(Z, xi).predict(Z)).ravel()

# ② 共同因子：四维度第一主成分（标准化后）
Xs = StandardScaler().fit_transform(df[X4].values)
pca = PCA(n_components=1)
df["pc1"] = pca.fit_transform(Xs).ravel()
print("PC1 解释方差比例：%.3f" % pca.explained_variance_ratio_[0])
print("四维度相关矩阵：")
print(df[X4].corr().round(3).to_string())

FE = "firm + year + industry_year + region_year"
print()
print("=" * 88)
print("补充检验：被解释变量 y_growth（主营业务收入增长率），四类固定效应 + 企业聚类标准误")
print("=" * 88)

specs = [
    ("(1) 仅 x_integration（原设定）", "x_integration"),
    ("(2) 四维同时放入", "x_novelty + x_science + x_integration + x_distance"),
    ("(3) 仅 PC1（共同因子）", "pc1"),
    ("(4) x_int_resid（剥离另外三维）", "x_int_resid"),
    ("(5) x_integration + PC1", "x_integration + pc1"),
]

rows = []
for label, rhs in specs:
    m = pf.feols(f"y_growth ~ {rhs} | {FE}", data=df, vcov={"CRV1": "firm"})
    tb = m.tidy()
    print("\n【%s】" % label)
    for v in tb.index:
        if v == "Intercept":
            continue
        c = float(tb.loc[v, "Estimate"] if "Estimate" in tb.columns else tb.loc[v, "coef"])
        se = float(tb.loc[v, "Std. Error"] if "Std. Error" in tb.columns else tb.loc[v, "std_error"])
        p = float(tb.loc[v, "Pr(>|t|)"] if "Pr(>|t|)" in tb.columns else tb.loc[v, "pvalue"])
        st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
        print("   %-18s 系数 %+9.4f   标准误 %7.4f   t=%+6.2f   p=%.4f %s" % (v, c, se, c / se, p, st))
        rows.append({"设定": label, "变量": v, "系数": round(c, 4),
                     "聚类标准误": round(se, 4), "t值": round(c / se, 2),
                     "p值": round(p, 4), "显著性": st, "观测数": int(m._N)})
    print("   观测数 %d" % int(m._N))

pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")

# ---------- 自动判读 ----------
print()
print("=" * 88)
print("自动判读")
print("=" * 88)
r = {x["变量"]: x for x in rows if x["设定"].startswith("(4)")}
p1 = {x["变量"]: x for x in rows if x["设定"].startswith("(3)")}
if "x_int_resid" in r and "pc1" in p1:
    sig_res = r["x_int_resid"]["p值"] < 0.05
    sig_pc = p1["pc1"]["p值"] < 0.05
    if sig_res:
        print("  ★ 情形 A：残差化后整合度【仍显著】→ -4.14 含超出共同因子的独立信息")
    elif sig_pc:
        print("  ★ 情形 B：残差化后【不显著】、PC1【显著】→ -4.14 就是共同因子的代理")
    else:
        print("  ★ 情形 C：两者都【不显著】→ 原结果由共同因子与设定共同驱动，主结论应作废")
print("\n结果已保存：%s" % OUT)
