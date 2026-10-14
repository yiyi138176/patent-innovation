# -*- coding: utf-8 -*-
"""诊断：试几个 akshare 接口，看哪个能拿到「行业」"""
import sys
import pandas as pd

try:
    import akshare as ak
except ImportError:
    print("❌ 没装 akshare")
    sys.exit(1)

CODE = "000682"          # 东方电子
XQ = "SZ000682"

print("akshare 版本：", ak.__version__)
print("=" * 74)


def test(tag, fn, **kw):
    print(f"\n【{tag}】")
    if not hasattr(ak, fn):
        print("   ❌ 这个接口在当前版本中不存在")
        return None
    try:
        d = getattr(ak, fn)(**kw)
        if isinstance(d, pd.DataFrame):
            print(f"   ✅ 成功  形状={d.shape}")
            print(f"   列名：{list(d.columns)[:12]}")
            print("   前 3 行：")
            print(d.head(3).to_string()[:900])
        else:
            print(f"   ✅ 返回：{str(d)[:300]}")
        return d
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {str(e)[:180]}")
        return None


test("1) stock_individual_info_em（个股信息-东财）",
     "stock_individual_info_em", symbol=CODE)

test("2) stock_individual_basic_info_xq（个股基本信息-雪球）",
     "stock_individual_basic_info_xq", symbol=XQ)

test("3) stock_zyjs_ths（主营介绍-同花顺）",
     "stock_zyjs_ths", symbol=CODE)

test("4) stock_profile_cninfo（公司概况-巨潮）",
     "stock_profile_cninfo", symbol=CODE)

test("5) stock_industry_category_cninfo（巨潮行业分类）",
     "stock_industry_category_cninfo", symbol="巨潮行业分类标准")

print()
print("=" * 74)
print("【6) 行业板块列表 stock_board_industry_name_em】")
try:
    b = ak.stock_board_industry_name_em()
    print(f"   ✅ 共 {len(b)} 个行业板块")
    print(f"   列名：{list(b.columns)}")
    print(b.head(8).to_string()[:700])
except Exception as e:
    print(f"   ❌ {type(e).__name__}: {str(e)[:180]}")

print()
print("=" * 74)
print("【7) 看某个行业板块的成分股 stock_board_industry_cons_em】")
try:
    c = ak.stock_board_industry_cons_em(symbol="电力")
    print(f"   ✅ 成功 形状={c.shape}  列名={list(c.columns)[:8]}")
    print(c.head(5).to_string()[:600])
except Exception as e:
    print(f"   ❌ {type(e).__name__}: {str(e)[:180]}")
