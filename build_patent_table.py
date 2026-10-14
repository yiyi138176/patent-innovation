# -*- coding: utf-8 -*-
"""读取专利 Excel -> 产出【专利明细】+【公司年度特征】"""
import os, re, glob, time
from collections import Counter
import pandas as pd

FOLDER = r"C:\Users\YYYi3\Desktop\专利数据\专利数据"
OUTDIR = r"C:\Users\YYYi3\Desktop\patent-innovation\data\processed"
os.makedirs(OUTDIR, exist_ok=True)

WANT = ["申请日", "公开（公告）日", "公开（公告）号", "标题 (中文)", "摘要 (中文)",
        "首项权利要求", "权利要求数量", "被引证次数", "发明人数量", "首权字数",
        "简单同族个数", "合享价值度", "技术先进性", "技术稳定性", "保护范围",
        "IPC主分类", "文献页数", "工商上市代码"]

NUM_MAP = {
    "平均权利要求数": "权利要求数量",
    "平均被引次数": "被引证次数",
    "平均发明人数": "发明人数量",
    "平均首权字数": "首权字数",
    "平均同族数": "简单同族个数",
    "平均合享价值度": "合享价值度",
    "平均技术先进性": "技术先进性",
    "平均技术稳定性": "技术稳定性",
    "平均保护范围": "保护范围",
    "平均文献页数": "文献页数",
}

CODE_RE = re.compile(r"(\d{6})")

# ===== 数据质量修正 =====
# 剔除东富龙：该文件内容与文件名不符（实为华中数控的专利）
EXCLUDE_FILES = ["东富龙科技集团股份有限公司.xlsx"]
# 大富科技代码修正（原误提取为 300127，与银河磁体重复）
CODE_FIX = {"大富科技(安徽)股份有限公司": "300134"}
# ========================

files = sorted(glob.glob(os.path.join(FOLDER, "*.xlsx")))
n0 = len(files)
files = [f for f in files if os.path.basename(f) not in EXCLUDE_FILES]
print(f"文件总数 {n0} -> 剔除异常后 {len(files)}")

details, summaries = [], []

for i, f in enumerate(files, 1):
    name = os.path.basename(f).replace(".xlsx", "")
    t0 = time.time()
    try:
        df = pd.read_excel(f, usecols=lambda c: c in WANT)
    except Exception as e:
        print(f"[{i:3d}] {name[:22]:<22} 读取失败 {type(e).__name__}")
        continue

    code = ""
    if "工商上市代码" in df.columns:
        cs = []
        for v in df["工商上市代码"].dropna().astype(str):
            cs += CODE_RE.findall(v)
        if cs:
            code = Counter(cs).most_common(1)[0][0]
    code = CODE_FIX.get(name, code)

    if "申请日" in df.columns:
        df["年份"] = pd.to_datetime(df["申请日"], errors="coerce").dt.year
    else:
        df["年份"] = pd.NA
    df["公司名"] = name
    df["股票代码"] = code

    keep = [c for c in ["公司名", "股票代码", "年份", "公开（公告）号", "标题 (中文)",
                        "摘要 (中文)", "首项权利要求", "权利要求数量", "被引证次数",
                        "发明人数量", "首权字数", "简单同族个数", "合享价值度",
                        "技术先进性", "技术稳定性", "保护范围", "IPC主分类", "文献页数"]
            if c in df.columns]
    details.append(df[keep].copy())

    g = df.dropna(subset=["年份"]).groupby("年份")
    if len(g) == 0:
        print(f"[{i:3d}] {name[:22]:<22} 无有效年份")
        continue
    agg = pd.DataFrame({"专利数": g.size()})
    for out_c, src_c in NUM_MAP.items():
        if src_c in df.columns:
            agg[out_c] = g[src_c].mean()
    if "IPC主分类" in df.columns:
        agg["IPC领域数"] = g["IPC主分类"].nunique()
    agg = agg.reset_index()
    agg["公司名"] = name
    agg["股票代码"] = code
    summaries.append(agg)

    print(f"[{i:3d}] {name[:22]:<22} {code}  {len(df)} 专利  {len(agg)} 年  {time.time()-t0:.1f}s")

if details:
    d = pd.concat(details, ignore_index=True)
    dp = os.path.join(OUTDIR, "专利明细.csv")
    d.to_csv(dp, index=False, encoding="utf-8-sig")
    print("\n专利明细:", d.shape, "->", dp)

if summaries:
    s = pd.concat(summaries, ignore_index=True)
    sp = os.path.join(OUTDIR, "公司年度特征.csv")
    s.to_csv(sp, index=False, encoding="utf-8-sig")
    print("公司年度特征:", s.shape, "->", sp)
    print(s.head(10).to_string())