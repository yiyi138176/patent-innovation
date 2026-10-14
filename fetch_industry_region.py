# -*- coding: utf-8 -*-
"""
（iiii）第一步：为公司补充「行业」和「地区」变量

数据源：巨潮资讯公司概况 ak.stock_profile_cninfo
  → 「所属行业」列 = 行业
  → 「注册地址」列 = 提取省份
（之前用的 stock_individual_info_em 接口返回 ConnectionError，已弃用）

输出：data/processed/公司_行业地区.csv
"""
import os
import sys
import time

import pandas as pd

try:
    import akshare as ak
except ImportError:
    print("❌ 没装 akshare")
    sys.exit(1)

BASE = r"C:\Users\YYYi3\Desktop\笔试准备\patent-innovation"
PROC = os.path.join(BASE, "data", "processed")
OUT_CSV = os.path.join(PROC, "公司_行业地区.csv")

TEST_N = None      # 先试 5 家；正式跑填 None

PROVINCES = ["北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
             "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
             "广东", "广西", "海南", "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
             "青海", "宁夏", "新疆", "内蒙古", "香港", "澳门", "台湾"]

CITY2PROV = {
    "深圳": "广东", "广州": "广东", "东莞": "广东", "佛山": "广东", "珠海": "广东",
    "中山": "广东", "惠州": "广东", "汕头": "广东",
    "杭州": "浙江", "宁波": "浙江", "温州": "浙江", "绍兴": "浙江", "嘉兴": "浙江",
    "台州": "浙江", "金华": "浙江", "湖州": "浙江",
    "南京": "江苏", "苏州": "江苏", "无锡": "江苏", "常州": "江苏", "南通": "江苏",
    "徐州": "江苏", "扬州": "江苏", "镇江": "江苏", "泰州": "江苏", "盐城": "江苏",
    "成都": "四川", "绵阳": "四川", "德阳": "四川",
    "武汉": "湖北", "宜昌": "湖北", "襄阳": "湖北",
    "西安": "陕西", "咸阳": "陕西", "宝鸡": "陕西",
    "青岛": "山东", "烟台": "山东", "潍坊": "山东", "威海": "山东", "淄博": "山东",
    "济南": "山东",
    "大连": "辽宁", "沈阳": "辽宁", "鞍山": "辽宁",
    "长春": "吉林", "哈尔滨": "黑龙江",
    "郑州": "河南", "洛阳": "河南", "长沙": "湖南", "株洲": "湖南", "湘潭": "湖南",
    "合肥": "安徽", "芜湖": "安徽", "马鞍山": "安徽",
    "福州": "福建", "厦门": "福建", "泉州": "福建", "龙岩": "福建",
    "南昌": "江西", "赣州": "江西", "昆明": "云南", "贵阳": "贵州", "太原": "山西",
    "石家庄": "河北", "唐山": "河北", "保定": "河北", "廊坊": "河北",
    "呼和浩特": "内蒙古", "包头": "内蒙古", "南宁": "广西", "柳州": "广西",
    "兰州": "甘肃", "银川": "宁夏", "西宁": "青海", "乌鲁木齐": "新疆",
    "海口": "海南", "三亚": "海南",
}


def extract_province(text):
    if not text or pd.isna(text):
        return ""
    s = str(text)
    for p in PROVINCES:
        if p in s:
            return p
    for city, prov in CITY2PROV.items():
        if city in s:
            return prov
    return ""


def fetch_profile(code):
    """一次调用拿到「所属行业」和「注册地址」"""
    try:
        d = ak.stock_profile_cninfo(symbol=code)
        if isinstance(d, pd.DataFrame) and len(d):
            row = d.iloc[0]
            ind = str(row.get("所属行业", "") or "").strip()
            addr = str(row.get("注册地址", "") or "").strip()
            if ind in ("nan", "None"):
                ind = ""
            if addr in ("nan", "None"):
                addr = ""
            return ind, addr
    except Exception:
        pass
    return "", ""


# ---------------- 公司清单 ----------------
df = pd.read_csv(os.path.join(PROC, "主数据集_含语义特征.csv"), dtype={"股票代码": str})
comp = df.groupby(["股票代码", "公司名"], as_index=False).agg(观测数=("年份", "size"))
comp["股票代码"] = comp["股票代码"].str.strip().str.zfill(6)
print(f"需要补行业/地区的公司：{len(comp)} 家")
if TEST_N:
    comp = comp.head(TEST_N)
    print(f"⚠️ 测试模式：只跑前 {TEST_N} 家")

# ---------------- 断点续跑（只跳过「行业已填」的）----------------
rows = []
done_codes = set()
if os.path.exists(OUT_CSV):
    old = pd.read_csv(OUT_CSV, dtype=str).fillna("")
    # 只认「行业非空」的为已完成
    ok = old[old["行业"].astype(str).str.strip() != ""]
    rows = ok.to_dict("records")
    done_codes = set(ok["股票代码"].astype(str).str.zfill(6))
    print(f"已有 {len(done_codes)} 家行业已填，将跳过")

todo = comp[~comp["股票代码"].isin(done_codes)]
print(f"本次需要查询：{len(todo)} 家\n")
if len(todo) == 0:
    print("🎉 都已查完")
    sys.exit(0)

t0 = time.time()
for i, r in enumerate(todo.itertuples(), 1):
    code, name = r.股票代码, r.公司名
    ind, addr = fetch_profile(code)
    reg = extract_province(addr) or extract_province(name)
    rows.append({"股票代码": code, "公司名": name, "行业": ind,
                 "地区": reg, "注册地址": addr, "观测数": r.观测数})
    tag = "✅" if ind else "⚠️"
    print(f"[{i:>3}/{len(todo)}] {tag} {name[:20]:<20} 行业={ind or '（空）':<14} 地区={reg or '（空）'}")
    if i % 20 == 0:
        pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f"        💾 已存盘（{len(rows)} 家）")
    time.sleep(0.3)

out = pd.DataFrame(rows)
out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print()
print("=" * 72)
print(f"✅ 完成，共 {len(out)} 家  耗时 {(time.time()-t0)/60:.1f} 分钟")
print(f"   行业有值：{(out['行业'].astype(str).str.strip() != '').sum()} 家")
print(f"   地区有值：{(out['地区'].astype(str).str.strip() != '').sum()} 家")
print()
print("【行业分布】")
print(out["行业"].replace("", "（空）").value_counts().to_string())
print()
print("【地区分布 Top15】")
print(out["地区"].replace("", "（空）").value_counts().head(15).to_string())
print()
print(f"已保存：{OUT_CSV}")
print("=" * 72)
