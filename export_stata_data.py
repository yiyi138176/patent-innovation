# -*- coding: utf-8 -*-
"""
导出 Stata 用的 .dta 数据（变量名全改英文，避开 Stata 中文变量名限制）
"""
import os
import numpy as np
import pandas as pd

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
STATA_DIR = os.path.join(BASE, "stata")
os.makedirs(STATA_DIR, exist_ok=True)

# ---------- 读数据 ----------
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
# 用英文编码，Stata 里用 i.industry 时标签是中文字符串会太长，改用数字 + 标签
IND_CODE = {"电子信息": 1, "软件信息": 2, "装备制造": 3,
            "汽车运输": 4, "电气仪器": 5, "其他制造服务": 6}
REG_CODE = {"东部": 1, "中部": 2, "西部": 3, "东北": 4, "其他": 5}

m["行业大类"] = m["行业"].map(IND_MAP).fillna("其他制造服务")
m["地区大区"] = m["地区"].map(REG_MAP).fillna("其他")
m["industry"] = m["行业大类"].map(IND_CODE).fillna(6).astype(int)
m["region"] = m["地区大区"].map(REG_CODE).fillna(5).astype(int)

# ---------- 变量映射（中文 → 英文）----------
MAP = {
    "资产负债率(%)": "y_lev",
    "总资产净利润率(%)": "y_roa",
    "主营业务收入增长率(%)": "y_growth",
    "LLM_novelty": "x_novelty",
    "LLM_science": "x_science",
    "LLM_integration": "x_integration",
    "LLM_distance": "x_distance",
    "专利数": "n_patent",
    "平均权利要求数": "avg_claims",
    "平均被引次数": "avg_cites",
    "平均发明人数": "avg_inventors",
    "平均首权字数": "avg_fcwords",
    "平均同族数": "avg_family",
    "平均合享价值度": "avg_value",
    "平均技术先进性": "avg_tech_adv",
    "平均技术稳定性": "avg_tech_stab",
    "平均保护范围": "avg_protect",
    "平均文献页数": "avg_pages",
    "IPC领域数": "ipc_fields",
    "年份": "year",
}
out = pd.DataFrame()
out["firmname"] = m["公司名"].astype(str)
out["stockcode"] = m["股票代码"].astype(str)
out["firm"] = pd.factorize(m["股票代码"])[0] + 1     # 企业数字 ID
out["year"] = m["年份"].astype(int)
out["industry"] = m["industry"]
out["region"] = m["region"]

for cn, en in MAP.items():
    if cn in m.columns:
        out[en] = pd.to_numeric(m[cn], errors="coerce")

out["ln_patent"] = np.log1p(pd.to_numeric(m["专利数"], errors="coerce"))

# 行业×年份、地区×年份 的交互 ID（方便 Stata 里 i.ind_year）
out["ind_year"] = (out["industry"].astype(str) + "_" + out["year"].astype(str))
out["reg_year"] = (out["region"].astype(str) + "_" + out["year"].astype(str))

# 缺失值处理（与 Python 版一致：专利特征填 0）
CTRL = ["ln_patent", "avg_claims", "avg_cites", "avg_inventors", "avg_fcwords",
        "avg_family", "avg_value", "avg_tech_adv", "avg_tech_stab",
        "avg_protect", "avg_pages", "ipc_fields"]
YV = ["y_lev", "y_roa", "y_growth"]
XV = ["x_novelty", "x_science", "x_integration", "x_distance"]
for c in CTRL + XV:
    out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)
out = out.dropna(subset=YV).copy()

# 结果变量缩尾（与 Python 版一致）
for c in YV:
    lo, hi = out[c].quantile([0.01, 0.99])
    out[c] = out[c].clip(lo, hi)

print(f"导出 {len(out):,} 个观测 / {out['firm'].nunique()} 家公司")
print(f"年份：{int(out['year'].min())} - {int(out['year'].max())}")
print(f"变量：{list(out.columns)}")

dta = os.path.join(STATA_DIR, "main_dataset.dta")
out.to_stata(dta, write_index=False, version=118,
             variable_labels={
                 "y_lev": "Asset-liability ratio (%)",
                 "y_roa": "Return on assets (%)",
                 "y_growth": "Revenue growth rate (%)",
                 "x_integration": "LLM: cross-domain integration",
                 "x_novelty": "LLM: technical novelty",
                 "x_science": "LLM: science linkage",
                 "x_distance": "LLM: distance to commercialization",
                 "ln_patent": "log(1+patent count)",
                 "firm": "firm id", "year": "year",
                 "industry": "industry group (1-6)",
                 "region": "region group (1-4)",
             })
print(f"\n已已导出：{dta}")

# 顺便导一份 CSV 备查
out.to_csv(os.path.join(STATA_DIR, "main_dataset.csv"), index=False, encoding="utf-8-sig")
print(f"已同时导出 CSV：{os.path.join(STATA_DIR, 'main_dataset.csv')}")
