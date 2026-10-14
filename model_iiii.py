# -*- coding: utf-8 -*-
"""
（iiii）计量回归 v3 —— 修正中文变量名导致的公式解析错误

修正：
  - pyfixest / formulaic 无法解析含括号和中文的变量名 → 全部改成英文
  - 变量命名与 stata/main_dataset.dta 保持一致（两套工具用同一套变量名）

模型：
  y_it = theta * x_it + controls + 企业FE + 年份FE + 行业×年份FE + 地区×年份FE
  聚类稳健标准误（企业层面）
"""
import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
OUTDIR = os.path.join(BASE, "results")
os.makedirs(OUTDIR, exist_ok=True)

YV = ["y_lev", "y_roa", "y_growth"]
Y_CN = {"y_lev": "资产负债率（融资约束）",
        "y_roa": "总资产净利润率（盈利）",
        "y_growth": "主营业务收入增长率（成长）"}
X = "x_integration"

# ================= 1. 数据（含中文→英文重命名）=================
df = pd.read_csv(os.path.join(PROC, "主数据集_含语义特征.csv"), dtype={"股票代码": str})
ir = pd.read_csv(os.path.join(PROC, "公司_行业地区.csv"), dtype=str).fillna("")
ir["股票代码"] = ir["股票代码"].str.zfill(6)
df["股票代码"] = df["股票代码"].str.zfill(6)
m = df.merge(ir[["股票代码", "行业", "地区"]], on="股票代码", how="left")

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
m["行业大类"] = m["行业"].map(IND_MAP).fillna("其他制造服务")
m["地区大区"] = m["地区"].map(REG_MAP).fillna("其他")

m["ln_patent"] = np.log1p(m["专利数"])

# ★ 全部改成英文变量名（pyfixest 只能解析合法标识符）
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
m = m.rename(columns=RENAME)

BF = ["ln_patent", "avg_claims", "avg_cites", "avg_inventors", "avg_fcwords",
      "avg_family", "avg_value", "avg_tech_adv", "avg_tech_stab",
      "avg_protect", "avg_pages", "ipc_fields"]
XV = ["x_novelty", "x_science", "x_integration", "x_distance"]

for c in BF + XV + YV:
    m[c] = pd.to_numeric(m[c], errors="coerce")
m[BF + XV] = m[BF + XV].fillna(0)
m = m.dropna(subset=YV).copy()
m["year"] = m["year"].astype(int)
for c in YV:                       # 缩尾（与前面口径一致）
    lo, hi = m[c].quantile([0.01, 0.99])
    m[c] = m[c].clip(lo, hi)

print(f"进入回归：{len(m):,} 个观测 / {m['firm_id'].nunique()} 家公司")
print(f"行业 {m['industry'].nunique()} 类   地区 {m['region'].nunique()} 类")
print(f"被解释变量：{YV}")
print(f"控制变量（{len(BF)} 个）：{BF}\n")

CONTROLS = " + ".join(BF)
FE = "firm_id + year + industry^year + region^year"

# ================= 2. 主回归 =================
try:
    import pyfixest as pf
except ImportError:
    print("请先运行：pip install pyfixest -i https://pypi.tuna.tsinghua.edu.cn/simple")
    raise SystemExit

print("=" * 80)
print("第 1 部分：主回归 —— 四类固定效应 + 企业层面聚类稳健标准误")
print("=" * 80)
rows = []
for y in YV:
    fit = pf.feols(f"{y} ~ {X} + {CONTROLS} | {FE}", data=m,
                   vcov={"CRV1": "firm_id"})
    coef = float(fit.coef()[X]); se = float(fit.se()[X]); p = float(fit.pvalue()[X])
    t = coef / se
    stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"\n【{Y_CN[y]}】")
    print(f"  {X} 系数 = {coef:+.4f}   聚类标准误 = {se:.4f}   "
          f"t = {t:+.2f}   p = {p:.4f} {stars}")
    print(f"  观测数 {int(fit._N):,}")
    rows.append({"被解释变量": y, "系数": round(coef, 4), "聚类标准误": round(se, 4),
                 "t值": round(t, 2), "p值": round(p, 4), "显著性": stars,
                 "观测数": int(fit._N)})
pd.DataFrame(rows).to_csv(os.path.join(OUTDIR, "iiii_主回归.csv"),
                          index=False, encoding="utf-8-sig")

# ================= 3. 完整结果表 =================
print()
print("=" * 80)
print("第 2 部分：资产负债率回归的完整结果（全部系数）")
print("=" * 80)
fit0 = pf.feols(f"y_lev ~ {X} + {CONTROLS} | {FE}", data=m, vcov={"CRV1": "firm_id"})
try:
    tb = fit0.tidy()
    print(tb.to_string())
    tb.to_csv(os.path.join(OUTDIR, "iiii_完整结果_资产负债率.csv"), encoding="utf-8-sig")
except Exception as e:
    print("tidy 失败：", e)

# ================= 4. 逐个语义维度（对应题目 iii）=================
print()
print("=" * 80)
print("第 3 部分：四个语义维度逐个加入（看哪个最重要）")
print("=" * 80)
one = []
for y in YV:
    for x in XV:
        fit = pf.feols(f"{y} ~ {x} + {CONTROLS} | {FE}", data=m,
                       vcov={"CRV1": "firm_id"})
        c = float(fit.coef()[x]); s = float(fit.se()[x]); p = float(fit.pvalue()[x])
        st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
        one.append({"被解释变量": y, "语义维度": x, "系数": round(c, 4),
                    "聚类标准误": round(s, 4), "t值": round(c / s, 2),
                    "p值": round(p, 4), "显著性": st})
        print(f"  {Y_CN[y]:<20} {x:<16} {c:+.4f} (t={c/s:+.2f}) {st}")
pd.DataFrame(one).to_csv(os.path.join(OUTDIR, "iiii_逐个维度.csv"),
                         index=False, encoding="utf-8-sig")

# ================= 5. 稳健性：滞后一期 =================
print()
print("=" * 80)
print("第 4 部分：稳健性 —— 滞后一期解释变量")
print("=" * 80)
m2 = m.sort_values(["firm_id", "year"]).copy()
m2["x_lag"] = m2.groupby("firm_id")[X].shift(1)
lag = []
for y in YV:
    d = m2.dropna(subset=["x_lag"]).copy()
    fit = pf.feols(f"{y} ~ x_lag + {CONTROLS} | {FE}", data=d, vcov={"CRV1": "firm_id"})
    c = float(fit.coef()["x_lag"]); s = float(fit.se()["x_lag"]); p = float(fit.pvalue()["x_lag"])
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"  {Y_CN[y]:<20} 系数 {c:+.4f}  se {s:.4f}  t={c/s:+.2f}  p={p:.4f} {st}   n={int(fit._N):,}")
    lag.append({"被解释变量": y, "系数": round(c, 4), "聚类标准误": round(s, 4),
                "t值": round(c / s, 2), "p值": round(p, 4), "显著性": st,
                "观测数": int(fit._N)})
pd.DataFrame(lag).to_csv(os.path.join(OUTDIR, "iiii_滞后回归.csv"),
                         index=False, encoding="utf-8-sig")

# ================= 6. 稳健性：更换聚类层级 =================
print()
print("=" * 80)
print("第 5 部分：稳健性 —— 更换聚类层级（以资产负债率为例）")
print("=" * 80)
cluster_rows = []
for cl, nm in [("firm_id", "企业"), ("industry", "行业"), ("region", "地区")]:
    fit = pf.feols(f"y_lev ~ {X} + {CONTROLS} | {FE}", data=m, vcov={"CRV1": cl})
    c = float(fit.coef()[X]); s = float(fit.se()[X]); p = float(fit.pvalue()[X])
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    print(f"  聚类到「{nm}」： 系数 {c:+.4f}  标准误 {s:.4f}  t={c/s:+.2f}  p={p:.4f} {st}")
    cluster_rows.append({"聚类层级": nm, "系数": round(c, 4), "标准误": round(s, 4),
                         "t值": round(c / s, 2), "p值": round(p, 4), "显著性": st})
pd.DataFrame(cluster_rows).to_csv(os.path.join(OUTDIR, "iiii_聚类稳健性.csv"),
                                  index=False, encoding="utf-8-sig")

# ================= 7. DML（识别策略）=================
print()
print("=" * 80)
print("第 6 部分：识别策略 —— 双重机器学习（DML，5 折交叉拟合）")
print("=" * 80)
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

dml = m.copy()
for c in [X] + BF + YV:
    dml[c + "_dm"] = dml[c] - dml.groupby("firm_id")[c].transform("mean")
Ydum = pd.get_dummies(dml["year"].astype(str), prefix="Y", drop_first=True).astype(float)
dml = pd.concat([dml, Ydum], axis=1)
Zcols = [c + "_dm" for c in BF] + list(Ydum.columns)
Xdm = X + "_dm"


def run_dml(data, ycol, xcol, zcols, learner="rf", folds=5, seed=42):
    d = data.dropna(subset=[ycol, xcol] + zcols).copy()
    Y = d[ycol].values.astype(float)
    Xv = d[xcol].values.astype(float)
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
for y in YV:
    for learner, nm in [("rf", "随机森林"), ("lasso", "LASSO")]:
        print(f"  正在跑 {Y_CN[y]} × {nm} ...", flush=True)
        try:
            b, se, p, n = run_dml(dml, y + "_dm", Xdm, Zcols, learner=learner)
            st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            print(f"    theta = {b:+.4f}   se {se:.4f}   t = {b/se:+.2f}   p = {p:.4f} {st}")
            dml_rows.append({"被解释变量": y, "学习器": nm, "theta": round(b, 4),
                             "标准误": round(se, 4), "t值": round(b / se, 2),
                             "p值": round(p, 4), "显著性": st, "观测数": n})
        except Exception as e:
            print(f"    ❌ {type(e).__name__}: {str(e)[:120]}")
pd.DataFrame(dml_rows).to_csv(os.path.join(OUTDIR, "iiii_DML.csv"),
                              index=False, encoding="utf-8-sig")

# ================= 8. 描述性统计 =================
print()
print("=" * 80)
print("第 7 部分：描述性统计")
print("=" * 80)
cols = [X] + YV + ["ln_patent", "avg_cites", "avg_claims"]
desc = m[cols].describe().T
desc["中位数"] = m[cols].median()
print(desc[["mean", "std", "min", "中位数", "max"]].round(3).to_string())
desc.to_csv(os.path.join(OUTDIR, "iiii_描述性统计.csv"), encoding="utf-8-sig")

print()
print("=" * 80)
print("完成。结果：iiii_主回归 / iiii_完整结果_资产负债率 / iiii_逐个维度")
print("             iiii_滞后回归 / iiii_聚类稳健性 / iiii_DML / iiii_描述性统计")
print("=" * 80)
