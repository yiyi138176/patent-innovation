# -*- coding: utf-8 -*-
"""
量化「线性关系」的具体形式：用 OLS 看每个专利特征的系数方向和大小
（只用 numpy/pandas 实现，含公司层面聚类稳健标准误）
"""
import io
import sys
import numpy as np
import pandas as pd

# 输出重定向到 UTF-8 文件（避免控制台 GBK 编码报错）
_OUT = open(r"C:\Users\YYYi3\Documents\deepseek-harness\default-workspace\_lin.txt", "w", encoding="utf-8")
sys.stdout = _OUT

CSV = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation\data\processed\主数据集_含语义特征.csv"
YCOLS = ["总资产净利润率(%)", "主营业务收入增长率(%)", "资产负债率(%)"]
LLM = ["LLM_novelty", "LLM_science", "LLM_integration", "LLM_distance"]
LLM_CN = {"LLM_novelty": "技术新颖性", "LLM_science": "科学基础强度",
          "LLM_integration": "跨领域整合度", "LLM_distance": "商业化距离"}
BASEn = ["平均权利要求数", "平均被引次数", "平均发明人数", "平均首权字数",
         "平均同族数", "平均合享价值度", "平均技术先进性", "平均技术稳定性",
         "平均保护范围", "平均文献页数", "IPC领域数"]

m = pd.read_csv(CSV, dtype={"股票代码": str})
m["ln专利数"] = np.log1p(m["专利数"])
BF = ["ln专利数"] + [c for c in BASEn if c in m.columns]
LF = [c for c in LLM if c in m.columns]
FE = BF + LF

for c in FE + YCOLS:
    m[c] = pd.to_numeric(m[c], errors="coerce")
m = m.dropna(subset=FE + YCOLS).copy()
print(f"样本：{len(m):,} 个观测 / {m['股票代码'].nunique()} 家公司\n")


def ols_cluster(X, y, groups):
    """OLS + 公司层面聚类稳健标准误，返回 (beta, se, t, R2)"""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    # 聚类稳健协方差
    meat = np.zeros((k, k))
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        Xg = X[idx]
        ug = resid[idx]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    dfc = (n - 1) / (n - k) * G / (G - 1)
    V = XtX_inv @ meat @ XtX_inv * dfc
    se = np.sqrt(np.diag(V))
    t = beta / se
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return beta, se, t, 1 - ss_res / ss_tot


def star(t):
    a = abs(t)
    return "***" if a > 2.58 else ("**" if a > 1.96 else ("*" if a > 1.65 else ""))


# ---- 公司内去均值（设定③，最能说明"同一家公司自己的变化"）----
d = m.copy()
for c in FE + YCOLS:
    d[c] = d[c] - d.groupby("股票代码")[c].transform("mean")

# 标准化系数：把 X 和 y 都除以标准差，系数 = "X 每变动 1 个标准差，y 变动多少"
Xd = d[FE].values
Xd = (Xd - Xd.mean(0)) / Xd.std(0)
X = np.column_stack([np.ones(len(d)), Xd])
names = ["常数项"] + FE
groups = d["股票代码"].values

print("=" * 82)
print("设定③ 公司内去均值：标准化 OLS 系数（公司层面聚类稳健标准误）")
print("  系数含义：该特征每变动 1 个标准差，结果变量变动多少个标准差")
print("=" * 82)

for y in YCOLS:
    yv = d[y].values
    yv = (yv - yv.mean()) / yv.std()
    beta, se, t, r2 = ols_cluster(X, yv, groups)
    print(f"\n【{y}】  R² = {r2:.4f}")
    order = np.argsort(-np.abs(beta[1:])) + 1
    print(f"  {'特征':<16}{'系数':>10}{'t 值':>10}   显著性")
    for i in order:
        nm = LLM_CN.get(names[i], names[i])
        print(f"  {nm:<16}{beta[i]:>10.4f}{t[i]:>10.2f}   {star(t[i])}")

# ---- 设定① 跨公司（便于对比）----
print()
print("=" * 82)
print("设定① 跨公司：标准化 OLS 系数（仅供参考，因省略了公司固定效应）")
print("=" * 82)
Xa = m[FE].values
Xa = (Xa - Xa.mean(0)) / Xa.std(0)
X1 = np.column_stack([np.ones(len(m)), Xa])
for y in YCOLS:
    yv = m[y].values
    yv = (yv - yv.mean()) / yv.std()
    beta, se, t, r2 = ols_cluster(X1, yv, m["股票代码"].values)
    print(f"\n【{y}】  R² = {r2:.4f}")
    order = np.argsort(-np.abs(beta[1:])) + 1
    for i in order[:6]:
        nm = LLM_CN.get(names[i], names[i])
        print(f"  {nm:<16}{beta[i]:>10.4f}{t[i]:>10.2f}   {star(t[i])}")

# ---- 语义特征之间的相关性（维度之间是否独立）----
print()
print("=" * 82)
print("四个语义特征之间的相关系数（看维度之间是否互相独立）")
print("=" * 82)
cc = m[LF].corr()
cc.index = [LLM_CN[c] for c in LF]
cc.columns = [LLM_CN[c] for c in LF]
print(cc.round(3).to_string())
