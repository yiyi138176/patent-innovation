# -*- coding: utf-8 -*-
"""
构建 SA 融资约束指数，并把它加入回归分析

SA 指数（Hadlock & Pierce, 2010）：
    SA = -0.737 * Size + 0.043 * Size^2 - 0.040 * Age
    其中 Size = ln(总资产 / 百万元)，Age = 观测年份 - 成立年份

【方向说明】
    SA 越负 → 企业规模越大、成立越久 → 融资约束越轻
    SA 越接近 0 → 企业规模越小、成立越短 → 融资约束越重
    即：SA 指数越大（越不负），融资约束越严重。

输出：
    data/processed/主数据集_含SA.csv
    results/iiii_SA_回归.csv
"""
import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
OUTDIR = os.path.join(BASE, "results")
os.makedirs(OUTDIR, exist_ok=True)

# ---------- 1. 读数据 ----------
df = pd.read_csv(os.path.join(PROC, "主数据集_含语义特征.csv"), dtype={"股票代码": str})
ir = pd.read_csv(os.path.join(PROC, "公司_行业地区.csv"), dtype=str).fillna("")
fd_path = os.path.join(PROC, "公司_成立日期.csv")
if not os.path.exists(fd_path):
    print("❌ 请先运行 fetch_found_date.py 抓取成立日期")
    raise SystemExit
fd = pd.read_csv(fd_path, dtype=str).fillna("")

fin = pd.read_csv(os.path.join(PROC, "企业财务数据_full.csv"), dtype={"股票代码": str})
fin["日期"] = pd.to_datetime(fin["日期"], errors="coerce")
fin["年份"] = fin["日期"].dt.year
q4 = fin[fin["日期"].dt.strftime("%m-%d") == "12-31"].copy()
q4["总资产(元)"] = pd.to_numeric(q4["总资产(元)"], errors="coerce")

for d in (df, ir, fd, q4):
    d["股票代码"] = d["股票代码"].astype(str).str.zfill(6)

m = df.merge(ir[["股票代码", "行业", "地区"]], on="股票代码", how="left")
m = m.merge(fd[["股票代码", "成立日期"]], on="股票代码", how="left")

# ---------- 总资产：优先用主数据集里已有的列，没有才从财务数据补 ----------
ast_col = None
for c in ["总资产(元)", "total_assets"]:
    if c in m.columns:
        ast_col = c
        break
if ast_col is None:
    q4n = q4[["股票代码", "年份", "总资产(元)"]].rename(columns={"总资产(元)": "total_assets"})
    m = m.merge(q4n, on=["股票代码", "年份"], how="left")
    ast_col = "total_assets"
    print("（总资产从财务数据补入）")
else:
    print(f"（总资产用主数据集已有的列：{ast_col}）")
m["total_assets"] = pd.to_numeric(m[ast_col], errors="coerce")

# ---------- 2. 算 SA 指数 ----------
m["成立年份"] = pd.to_datetime(m["成立日期"], errors="coerce").dt.year
m["Age"] = m["年份"] - m["成立年份"]
m["Size"] = np.log(m["total_assets"] / 1e6)          # 单位：百万元
m["SA"] = -0.737 * m["Size"] + 0.043 * m["Size"] ** 2 - 0.040 * m["Age"]

n0 = len(m)
m_sa = m.dropna(subset=["SA"]).copy()
print(f"SA 指数可计算：{len(m_sa):,} / {n0:,} 个观测")
print(f"  SA 均值 {m_sa['SA'].mean():.3f}   标准差 {m_sa['SA'].std():.3f}   "
      f"范围 [{m_sa['SA'].min():.3f}, {m_sa['SA'].max():.3f}]")
print(f"  成立年份范围：{int(m_sa['成立年份'].min())} - {int(m_sa['成立年份'].max())}")
print(f"  Age 均值 {m_sa['Age'].mean():.1f} 年")

# ---------- 3. 重命名 + 准备回归 ----------
IND_MAP = {
    "计算机、通信和其他电子设备制造业": "电子信息",
    "软件和信息技术服务业": "软件信息", "互联网和相关服务": "软件信息",
    "专用设备制造业": "装备制造", "通用设备制造业": "装备制造",
    "汽车制造业": "汽车运输",
    "铁路、船舶、航空航天和其他运输设备制造业": "汽车运输",
    "电气机械和器材制造业": "电气仪器", "仪器仪表制造业": "电气仪器",
}
REG_MAP = {
    "北京": "东部", "天津": "东部", "上海": "东部", "河北": "东部", "江苏": "东部",
    "浙江": "东部", "福建": "东部", "山东": "东部", "广东": "东部", "海南": "东部",
    "山西": "中部", "安徽": "中部", "江西": "中部", "河南": "中部",
    "湖北": "中部", "湖南": "中部",
    "内蒙古": "西部", "广西": "西部", "重庆": "西部", "四川": "西部", "贵州": "西部",
    "云南": "西部", "西藏": "西部", "陕西": "西部", "甘肃": "西部", "青海": "西部",
    "宁夏": "西部", "新疆": "西部",
    "辽宁": "东北", "吉林": "东北", "黑龙江": "东北",
}
m_sa["行业大类"] = m_sa["行业"].map(IND_MAP).fillna("其他制造服务")
m_sa["地区大区"] = m_sa["地区"].map(REG_MAP).fillna("其他")
m_sa["ln_patent"] = np.log1p(m_sa["专利数"])

RENAME = {
    "股票代码": "firm_id", "年份": "year",
    "行业大类": "industry", "地区大区": "region",
    "资产负债率(%)": "y_lev",
    "总资产净利润率(%)": "y_roa",
    "主营业务收入增长率(%)": "y_growth",
    "LLM_novelty": "x_novelty", "LLM_science": "x_science",
    "LLM_integration": "x_integration", "LLM_distance": "x_distance",
    "平均权利要求数": "avg_claims", "平均被引次数": "avg_cites",
    "平均发明人数": "avg_inventors", "平均首权字数": "avg_fcwords",
    "平均同族数": "avg_family", "平均合享价值度": "avg_value",
    "平均技术先进性": "avg_tech_adv", "平均技术稳定性": "avg_tech_stab",
    "平均保护范围": "avg_protect", "平均文献页数": "avg_pages",
    "IPC领域数": "ipc_fields",
}
m_sa = m_sa.rename(columns={**RENAME, "SA": "y_sa"})

BF = ["ln_patent", "avg_claims", "avg_cites", "avg_inventors", "avg_fcwords",
      "avg_family", "avg_value", "avg_tech_adv", "avg_tech_stab",
      "avg_protect", "avg_pages", "ipc_fields"]
XV = ["x_novelty", "x_science", "x_integration", "x_distance"]
YV = ["y_lev", "y_sa", "y_roa", "y_growth"]
Y_CN = {"y_lev": "资产负债率（杠杆）", "y_sa": "SA指数（融资约束，越大越受约束）",
        "y_roa": "总资产净利润率", "y_growth": "主营业务收入增长率"}
X = "x_integration"

for c in BF + XV + YV:
    m_sa[c] = pd.to_numeric(m_sa[c], errors="coerce")
m_sa[BF + XV] = m_sa[BF + XV].fillna(0)
m_sa = m_sa.dropna(subset=YV).copy()
m_sa["year"] = m_sa["year"].astype(int)
for c in YV:
    lo, hi = m_sa[c].quantile([0.01, 0.99])
    m_sa[c] = m_sa[c].clip(lo, hi)

m_sa.to_csv(os.path.join(PROC, "主数据集_含SA.csv"), index=False, encoding="utf-8-sig")
print(f"\n进入回归：{len(m_sa):,} 个观测 / {m_sa['firm_id'].nunique()} 家公司")

# ---------- 4. 回归 ----------
try:
    import pyfixest as pf
except ImportError:
    print("请先安装 pyfixest")
    raise SystemExit

CONTROLS = " + ".join(BF)
FE = "firm_id + year + industry^year + region^year"

print()
print("=" * 80)
print("四类固定效应 + 企业层面聚类稳健标准误   x = 跨领域整合度")
print("=" * 80)
rows = []
for y in YV:
    fit = pf.feols(f"{y} ~ {X} + {CONTROLS} | {FE}", data=m_sa, vcov={"CRV1": "firm_id"})
    c = float(fit.coef()[X]); s = float(fit.se()[X]); p = float(fit.pvalue()[X])
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"\n【{Y_CN[y]}】")
    print(f"  系数 = {c:+.4f}   聚类标准误 = {s:.4f}   t = {c/s:+.2f}   p = {p:.4f} {st}")
    print(f"  观测数 {int(fit._N):,}")
    rows.append({"被解释变量": Y_CN[y], "变量名": y, "系数": round(c, 4),
                 "聚类标准误": round(s, 4), "t值": round(c / s, 2),
                 "p值": round(p, 4), "显著性": st, "观测数": int(fit._N)})
pd.DataFrame(rows).to_csv(os.path.join(OUTDIR, "iiii_SA_回归.csv"),
                          index=False, encoding="utf-8-sig")

# ---------- 5. 对 SA 指数：逐个维度 + DML ----------
print()
print("=" * 80)
print("SA 指数：四个语义维度逐个加入")
print("=" * 80)
one = []
for x in XV:
    fit = pf.feols(f"y_sa ~ {x} + {CONTROLS} | {FE}", data=m_sa, vcov={"CRV1": "firm_id"})
    c = float(fit.coef()[x]); s = float(fit.se()[x]); p = float(fit.pvalue()[x])
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"  {x:<16} {c:+.4f}  (t={c/s:+.2f})  p={p:.4f} {st}")
    one.append({"语义维度": x, "系数": round(c, 4), "聚类标准误": round(s, 4),
                "t值": round(c / s, 2), "p值": round(p, 4), "显著性": st})
pd.DataFrame(one).to_csv(os.path.join(OUTDIR, "iiii_SA_逐维度.csv"),
                         index=False, encoding="utf-8-sig")

print()
print("=" * 80)
print("SA 指数：DML 识别")
print("=" * 80)
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

dml = m_sa.copy()
for c in [X] + BF + ["y_sa"]:
    dml[c + "_dm"] = dml[c] - dml.groupby("firm_id")[c].transform("mean")
Ydum = pd.get_dummies(dml["year"].astype(str), prefix="Y", drop_first=True).astype(float)
dml = pd.concat([dml, Ydum], axis=1)
Zcols = [c + "_dm" for c in BF] + list(Ydum.columns)


def run_dml(data, ycol, xcol, zcols, learner="rf", folds=5, seed=42):
    d = data.dropna(subset=[ycol, xcol] + zcols).copy()
    Y = d[ycol].values.astype(float); Xv = d[xcol].values.astype(float)
    Z = StandardScaler().fit_transform(d[zcols].values.astype(float))
    kf = KFold(n_splits=folds, shuffle=True, random_state=seed)
    yr = np.zeros_like(Y); xr = np.zeros_like(Xv)
    for tr, te in kf.split(Z):
        if learner == "rf":
            my = RandomForestRegressor(n_estimators=200, min_samples_leaf=3,
                                       random_state=seed, n_jobs=-1).fit(Z[tr], Y[tr])
            mx = RandomForestRegressor(n_estimators=200, min_samples_leaf=3,
                                       random_state=seed, n_jobs=-1).fit(Z[tr], Xv[tr])
        else:
            my = LassoCV(cv=3, random_state=seed, max_iter=3000).fit(Z[tr], Y[tr])
            mx = LassoCV(cv=3, random_state=seed, max_iter=3000).fit(Z[tr], Xv[tr])
        yr[te] = Y[te] - my.predict(Z[te])
        xr[te] = Xv[te] - mx.predict(Z[te])
    r = sm.OLS(yr, sm.add_constant(xr.reshape(-1, 1))).fit(cov_type="HC1")
    return r.params[1], r.bse[1], r.pvalues[1], len(d)


dml_rows = []
for learner, nm in [("rf", "随机森林"), ("lasso", "LASSO")]:
    print(f"  正在跑 SA × {nm} ...", flush=True)
    b, se, p, n = run_dml(dml, "y_sa_dm", X + "_dm", Zcols, learner=learner)
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"    theta = {b:+.4f}  se {se:.4f}  t = {b/se:+.2f}  p = {p:.4f} {st}")
    dml_rows.append({"被解释变量": "SA指数", "学习器": nm, "theta": round(b, 4),
                     "标准误": round(se, 4), "t值": round(b / se, 2),
                     "p值": round(p, 4), "显著性": st, "观测数": n})
pd.DataFrame(dml_rows).to_csv(os.path.join(OUTDIR, "iiii_SA_DML.csv"),
                              index=False, encoding="utf-8-sig")

print()
print("=" * 80)
print("完成。结果：iiii_SA_回归.csv / iiii_SA_逐维度.csv / iiii_SA_DML.csv")
print("=" * 80)
