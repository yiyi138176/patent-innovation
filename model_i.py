# -*- coding: utf-8 -*-
"""（i）基准专利特征的解释力：线性 vs 非线性 × 三种设定"""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

PROC = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
OUTDIR = r"C:\Users\YYYi3\Desktop\patent-innovation\results"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(os.path.join(PROC, "主数据集.csv"), dtype={"股票代码": str})
print("原始:", df.shape)

BASE = ["平均权利要求数", "平均被引次数", "平均发明人数", "平均首权字数",
        "平均同族数", "平均合享价值度", "平均技术先进性", "平均技术稳定性",
        "平均保护范围", "平均文献页数", "IPC领域数"]
BASE = [f for f in BASE if f in df.columns]
df["ln专利数"] = np.log1p(df["专利数"])
FEATS = ["ln专利数"] + BASE
YCOLS = ["总资产净利润率(%)", "主营业务收入增长率(%)", "资产负债率(%)"]

# 修正1：专利特征缺失填 0（无引用记录 = 0 次引用）
for c in FEATS:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

df = df.dropna(subset=YCOLS).copy()
df["年份"] = df["年份"].astype(int)
df["_firm"] = df["股票代码"]

# 修正2：结果变量 1%/99% 缩尾
for c in YCOLS:
    lo, hi = df[c].quantile([0.01, 0.99])
    df[c] = df[c].clip(lo, hi)

print("进入模型:", df.shape)

def run(tag, data):
    X = data[FEATS].values
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(X, data[YCOLS[0]].values, groups=data["_firm"].values))
    out, r2info = [], {}
    for y in YCOLS:
        Yv = data[y].values
        sc = StandardScaler().fit(X[tr])
        lin = LinearRegression().fit(sc.transform(X[tr]), Yv[tr])
        r2l = r2_score(Yv[te], lin.predict(sc.transform(X[te])))
        rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
        rf.fit(X[tr], Yv[tr])
        r2r = r2_score(Yv[te], rf.predict(X[te]))
        out.append({"设定": tag, "结果变量": y, "线性R2": round(r2l, 4),
                    "随机森林R2": round(r2r, 4), "非线性提升": round(r2r - r2l, 4)})
        r2info[y] = (r2l, r2r)
    return out, r2info

res = []
# 设定①：原始（跨公司）
r1, _ = run("① 原始(跨公司)", df.copy())
res += r1

# 设定②：年度去均值（剥离年度共同冲击）
d2 = df.copy()
for c in YCOLS + FEATS:
    d2[c] = d2[c] - d2.groupby("年份")[c].transform("mean")
r2, _ = run("② 年度去均值", d2)
res += r2

# 设定③：公司内去均值（剥离公司固定效应 —— 问"同一公司自己的年度波动能否被解释"）
d3 = df.copy()
for c in YCOLS + FEATS:
    d3[c] = d3[c] - d3.groupby("_firm")[c].transform("mean")
r3, _ = run("③ 公司内去均值", d3)
res += r3

r = pd.DataFrame(res)
print("\n===== 汇总 =====")
print(r.to_string(index=False))
r.to_csv(os.path.join(OUTDIR, "i_基准模型结果.csv"), index=False, encoding="utf-8-sig")
print("\n已保存:", os.path.join(OUTDIR, "i_基准模型结果.csv"))