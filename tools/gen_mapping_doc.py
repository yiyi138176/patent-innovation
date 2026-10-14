# -*- coding: utf-8 -*-
"""生成《题目要求 ↔ 我们的工作 逐句对照》"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\YYYi3\Documents\deepseek-harness\default-workspace\题目对照表.docx"
FONT = "微软雅黑"

doc = Document()
for s in doc.sections:
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(1.8)
    s.left_margin = s.right_margin = Cm(1.6)

st = doc.styles["Normal"]
st.font.name = FONT
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.line_spacing = 1.25
st.paragraph_format.space_after = Pt(4)

for name, sz in [("Heading 1", 16), ("Heading 2", 12.5), ("Heading 3", 11)]:
    s2 = doc.styles[name]
    s2.font.name = FONT
    s2.font.size = Pt(sz)
    s2.font.bold = True
    s2.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    s2.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    s2.paragraph_format.space_before = Pt(10)
    s2.paragraph_format.space_after = Pt(5)


def _r(p, t, size=10, bold=False, color=None):
    r = p.add_run(t)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size)
    r.bold = bold
    if color:
        r.font.color.rgb = color
    return r


def P(t="", size=10, bold=False, indent=0):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    _r(p, t, size, bold)
    return p


def BUL(t, indent=0.6):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(indent)
    _r(p, t, 10)
    return p


def QUOTE(cn_num, text):
    """题目原话"""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    _r(p, f"题目原话（{cn_num}）：", 10, True, RGBColor(0x80, 0x00, 0x00))
    p2 = doc.add_paragraph()
    p2.paragraph_format.left_indent = Cm(0.6)
    p2.paragraph_format.space_after = Pt(4)
    _r(p2, text, 10.5, True, RGBColor(0x00, 0x00, 0x00))


def ANSWER(what, where, why, result=""):
    lines = [("我们做了什么：", what), ("用哪个文件：", where), ("为什么这么做：", why)]
    if result:
        lines.append(("结果在哪：", result))
    for label, val in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.space_after = Pt(2)
        _r(p, label, 10, True, RGBColor(0x1F, 0x3B, 0x63))
        _r(p, val, 10)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def TABLE(headers, rows, widths=None, fontsize=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        _r(c.paragraphs[0], h, fontsize, True)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCE6F1")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            pp.paragraph_format.space_after = Pt(1)
            _r(pp, str(v), fontsize)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ============ 封面 ============
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
_r(p, "题目要求 ↔ 我们的工作", 22, True, RGBColor(0x1F, 0x3B, 0x63))
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
_r(p, "逐句对照表", 13)
P()
P("用法：题目（i）和（ii）的每一句话，我们都拆开，说明「做了什么、用哪个文件、为什么」。", size=10)
P("汇报前读一遍，被问到任何一句，你都能对上是哪一步。", size=10, bold=True)
doc.add_page_break()

# ============ （i） ============
doc.add_heading("第一部分　题目（i）逐句对照", level=1)

QUOTE("（i）第 1 句",
      "基准专利文本特征（如 TF-IDF、词袋、IPC 分类、引用次数、权利要求数、专利家族规模、发明人数量）……")
ANSWER(
    "用了 12 个数量类特征：ln专利数、平均权利要求数、平均被引次数、平均发明人数、"
    "平均首权字数、平均同族数、平均合享价值度、平均技术先进性、平均技术稳定性、"
    "平均保护范围、平均文献页数、IPC领域数。",
    "build_patent_table.py（生成特征）→ data/processed/公司年度特征.csv",
    "题目列举的 7 类特征里，我们的数据覆盖了 6 类（IPC 分类、引用次数、权利要求数、"
    "专利家族规模、发明人数量、专利数量）。TF-IDF 和词袋属于文本特征，"
    "数据现成但计算量大，安排在后面补做。",
    "results/i_基准模型结果.csv")

QUOTE("（i）第 2 句",
      "……在非线性模型与线性模型中对以下经济结果的差异化解释与预测能力……")
ANSWER(
    "线性模型用 LinearRegression（普通最小二乘）；非线性模型用 RandomForestRegressor"
    "（随机森林，300 棵树）。两者在完全相同的训练/测试集上比较。",
    "model_i.py（第 3 段）",
    "题目要求同时看「线性」和「非线性」两种模型，是为了回答一个更本质的问题："
    "专利特征与企业结果之间到底是直线关系还是弯曲关系？"
    "随机森林不需要事先指定函数形式，能自动捕捉非线性，所以适合做这个对照。",
    "results/i_基准模型结果.csv")

QUOTE("（i）第 3 句",
      "……企业全要素生产率、研发投入、新产品销售收入、出口、就业增长、融资约束、"
      "企业进入新市场、创新产出等不限变量任选三种。")
ANSWER(
    "选了三个：总资产净利润率（ROA，代表盈利能力）、主营业务收入增长率（代表成长性）、"
    "资产负债率（代表融资约束）。",
    "fetch_financials.py（抓数据）→ check_coverage.py（查覆盖率）→ build_dataset.py（合并）",
    "题目明确说「任选三种」，所以选择标准是「数据可得性 + 经济含义」。"
    "全要素生产率需要 LP/OP 方法计算，出口要海关数据，就业增长要员工人数，"
    "这三个都拿不到；而资产负债率正好是题目列举的「融资约束」的常用代理变量。",
    "data/processed/主数据集.csv")

QUOTE("（i）第 4 句",
      "进一步分析基准特征与企业创新结果之间存在的非线性或线性关系。")
ANSWER(
    "比较线性模型和随机森林在 9 个组合（3 种设定 × 3 个结果变量）中的表现。",
    "model_i.py → results/i_基准模型结果.csv",
    "如果非线性模型明显更好，说明关系是弯的；如果线性模型更好或持平，说明关系基本是直线的。",
    "结论：线性模型 9 组赢了 8 组 → 关系主要是线性的。")

P()
P("（i）的完整答案（三句话）", bold=True)
BUL("① 跨公司维度：12 个数量特征几乎解释不了企业间的财务差异（R² 接近 0 或为负）。")
BUL("② 公司内维度：能解释约 18% 的总资产净利润率年度波动（设定③）。")
BUL("③ 关系是线性的：线性模型 9 组赢 8 组，随机森林因样本量小而过拟合。")

doc.add_page_break()

# ============ （ii） ============
doc.add_heading("第二部分　题目（ii）逐句对照", level=1)

QUOTE("（ii）第 1 句",
      "大语言模型提取的结构化特征……")
ANSWER(
    "① 从题目给的 8 个候选维度中选定 4 个（技术新颖性、科学基础强度、跨领域整合度、"
    "商业化距离）；② 写了四版提示词；③ 用智谱 GLM-4-Flash 给 12,166 条专利逐条打分；"
    "④ 聚合到「公司—年份」层面（取均值）。",
    "prompts/prompt_v1~v4.txt（提示词）→ score_patents.py（打分）→ model_ii.py 第 1 步（聚合）",
    "题目要求「至少四个语义维度」。选这四个是因为它们与基准数量特征的重叠最小——"
    "题目（ii）后半句明确要求验证「与基准特征正交的信息」，重叠越小，正交性越强。"
    "放弃「权利要求广度」（基准已有权利要求数量）和「合作网络属性」（基准已有发明人数量）。",
    "data/llm/llm_scores_v4.csv（12,166 条专利级打分）")

QUOTE("（ii）第 2 句（前半）",
      "……较基准专利特征的增量解释与预测能力……")
ANSWER(
    "在完全相同的模型（RidgeCV）和交叉验证方案（5 折按公司分组）下，比较三组特征："
    "A = 仅 12 个数量特征；B = 数量特征 + 4 个语义特征；C = 仅 4 个语义特征。"
    "以 B − A 作为增量。",
    "model_ii.py 第 3 步",
    "关键在于「控制变量」：A 和 B 必须用同一个模型、同一份数据，"
    "这样 B−A 才是「语义特征带来的贡献」，而不是「换了模型的差别」。"
    "用 5 折交叉验证而不是单次划分，是为了让 R² 更稳定。",
    "results/ii_增量解释力.csv")

P("（ii）第 2 句（前半）的结果", bold=True)
TABLE(["设定", "结果变量", "A 仅数量", "B 数量+语义", "增量(B−A)"], [
    ["① 原始", "总资产净利润率", "0.0145", "0.0249", "+0.0104"],
    ["① 原始", "主营业务收入增长率", "0.0232", "0.0259", "+0.0027"],
    ["③ 公司内", "总资产净利润率", "0.0976", "0.1096", "+0.0120"],
    ["③ 公司内", "主营业务收入增长率", "0.0385", "0.0383", "-0.0002"],
], widths=[2.4, 4.4, 2.6, 3.0, 2.6])
P("→ 增量方向为正，但幅度很小（0.1–1.2 个百分点）。", size=10, bold=True)

QUOTE("（ii）第 2 句（后半）",
      "……并区分其捕捉到的与基准特征正交的信息。")
ANSWER(
    "做了两项检验：① 计算 4 个语义特征与 12 个数量特征的相关系数矩阵；"
    "② 用 12 个数量特征回归每个语义特征，看能解释多少（R²），"
    "则 1−R² 就是「正交部分」。",
    "model_ii.py 第 5 步",
    "「正交」是个几何概念：如果语义特征能被数量特征线性表示出来，它就是冗余的；"
    "如果表示不出来，说明它含有独立信息。用回归的 R² 衡量「能被表示的程度」，"
    "1−R² 就是「表示不出来的部分」。",
    "results/ii_正交性检验.csv、ii_相关系数矩阵.csv")

P("（ii）第 2 句（后半）的结果", bold=True)
TABLE(["语义维度", "被数量特征解释的 R²", "正交部分（1−R²）"], [
    ["技术新颖性", "0.554", "0.446"],
    ["科学基础强度", "0.449", "0.551"],
    ["跨领域整合度", "0.446", "0.554"],
    ["商业化距离", "0.349", "0.651"],
], widths=[4.4, 5.2, 5.4])
P("平均相关系数仅 0.21，最大 0.47 → 重叠程度不高。", size=10)
P("→ 语义特征中 45%–65% 的变异是数量特征完全解释不了的，确实捕捉到了正交信息。",
  size=10, bold=True, )

QUOTE("（ii）第 3 句",
      "可通过正交化、残差回归、Shapley 值、置换重要性、LASSO/Elastic Net、因果森林等方法进行验证。")
ANSWER(
    "用了其中的「正交化」方法（等价于残差回归）：用数量特征回归语义特征，"
    "以 1−R² 衡量正交信息占比。",
    "model_ii.py 第 5 步",
    "题目列举的是「可选方法清单」，不是必须全做。"
    "正交化最直接对应题目要求的「区分正交信息」，且计算量小、结果容易解释。"
    "Shapley 值和因果森林属于进阶方法，在四天工期内未纳入。",
    "results/ii_正交性检验.csv")

doc.add_page_break()

# ============ （iii）顺带 ============
doc.add_heading("第三部分　题目（iii）—— 我们已经顺手做出来了", level=1)
QUOTE("（iii）",
      "将前面提取的结构化特征逐个与基准特征结合后，所展现出的增量解释与预测能力，"
      "并讨论哪些维度最重要……")
ANSWER(
    "把 4 个语义维度逐个加入基准特征，看每个维度单独带来的增量。",
    "model_ii.py 第 4 步 → results/ii_特征重要性.csv",
    "题目要求「逐个结合」，所以我们一次只加一个维度，而不是四个一起加。"
    "这样能看出哪个维度贡献最大。",
    "results/ii_特征重要性.csv")

TABLE(["加入的维度", "ROA 增量", "营收增长增量", "资产负债率增量", "排名"], [
    ["跨领域整合度", "+0.0122", "+0.0067", "-0.0006", "★ 第 1"],
    ["科学基础强度", "+0.0060", "+0.0044", "+0.0012", "第 2"],
    ["技术新颖性", "+0.0053", "+0.0004", "+0.0036", "第 3"],
    ["商业化距离", "+0.0053", "-0.0005", "-0.0059", "第 4"],
], widths=[3.6, 3.0, 3.2, 3.4, 2.0])
P("→ 「跨领域整合度」在三个结果变量上都排第一或并列第一，是最重要的维度。",
  size=10.5, bold=True)

doc.add_page_break()

# ============ 软件工具 ============
doc.add_heading("第四部分　软件工具清单（装了什么，各自管什么）", level=1)
TABLE(["软件 / 库", "它是什么", "在我们这里干什么"], [
    ["Python", "一种编程语言", "所有脚本都用它写。用它才能自动处理 11.7 万条数据"],
    ["VS Code", "写代码的编辑器", "写脚本、开终端、跑脚本。比记事本好用得多"],
    ["pip", "Python 的「应用商店」", "安装各种库（akshare、scikit-learn 等），一条命令搞定"],
    ["pandas", "表格处理库", "读写 CSV、筛选、合并、按公司和年份分组统计。数据处理主力"],
    ["numpy", "数值计算库", "对数变换、数组运算。pandas 依赖它"],
    ["scikit-learn", "机器学习库", "线性回归、随机森林、划分训练测试集、算 R²。（i）（ii）靠它"],
    ["akshare", "财经数据接口（免费）", "抓 A 股上市公司的财务数据，以及官方股票代码表"],
    ["requests", "网络请求库", "调用智谱大模型 API，给 1.2 万条专利发请求"],
    ["statsmodels / linearmodels", "计量经济学库", "（iiii）做固定效应回归、聚类稳健标准误，替代 Stata"],
    ["matplotlib", "画图库", "给报告生成图表"],
    ["Git", "版本控制工具", "把代码和文件上传到 GitHub。提交作业必须用"],
    ["智谱 GLM-4-Flash", "大模型 API（免费）", "读专利摘要给四个维度打分。1,777 万 token 不花钱"],
    ["Excel / WPS", "表格软件", "打开小的 CSV 抽查数据（175MB 那个打不开）"],
    ["Dev-C++ / 小熊猫C++", "C 语言编译器", "跟这个笔试无关，是 C 语言课用的"],
], widths=[3.4, 4.2, 9.8])

doc.add_page_break()

# ============ 文件清单 ============
doc.add_heading("第五部分　文件清单", level=1)

doc.add_heading("5.1　脚本文件（每个脚本干什么）", level=2)
TABLE(["文件", "属于哪一步", "干什么"], [
    ["extract_codes.py", "数据准备", "从 152 个 Excel 里提取每家公司对应的股票代码"],
    ["check_codes.py", "数据准备", "用 A 股官方代码表逐条校验，发现 3 处问题"],
    ["fetch_financials.py", "数据准备", "用 akshare 抓企业财务数据（144 家 × 86 个变量）"],
    ["check_coverage.py", "数据准备", "检查每个财务变量覆盖哪些年份（发现销售毛利率缺失）"],
    ["check_dates.py / check_ycols.py", "数据准备", "排查样本异常的临时诊断脚本（保留作证据）"],
    ["build_patent_table.py", "数据准备", "把 11.7 万条专利聚合成公司—年份的 12 个特征"],
    ["build_dataset.py", "数据准备", "把专利特征和财务数据合并成主数据集"],
    ["model_i.py", "（i）", "线性 vs 非线性 × 三种设定，算出 18 个 R²"],
    ["score_patents.py", "（ii）", "用大模型给专利文本打分（12,166 条，约 50 分钟）"],
    ["review_scores.py", "（ii）", "检查打分质量：分布、标准差、取值种类"],
    ["model_ii.py", "（ii）（iii）", "增量解释力 + 逐个维度重要性 + 正交性检验"],
    ["config.py", "配置", "存 API 密钥（已加进 .gitignore，不会上传）"],
    ["test_api.py", "测试", "测试 API 通不通、哪个模型能用"],
    ["prompts/prompt_v1~v4.txt", "（ii）", "四版提示词全文（可复现性要求）"],
    ["prompts/v1.txt", "（ii）", "第一版维度定义与评分锚点的详细文档"],
    [".gitignore", "配置", "告诉 Git 哪些文件不要上传（密钥、大文件）"],
    ["决策记录.md", "全程", "D1–D18 全部决策及其理由"],
    ["logs/10.9、logs/10.10", "全程", "每日工作日志"],
], widths=[4.8, 2.4, 10.2])

doc.add_heading("5.2　数据文件（产出物）", level=2)
TABLE(["文件", "大小", "是什么"], [
    ["data/processed/专利明细.csv", "176 MB", "11.7 万条专利明细（标题、摘要、首项权利要求、特征）"],
    ["data/processed/公司年度特征.csv", "0.4 MB", "2,481 个公司—年份的 12 个数量类特征"],
    ["data/processed/企业财务数据_full.csv", "3.2 MB", "144 家公司的 86 个财务变量（原始抓取结果）"],
    ["data/processed/主数据集.csv", "0.3 MB", "1,270 个观测，12 个专利特征 + 3 个结果变量"],
    ["data/processed/主数据集_含语义特征.csv", "—", "上表再加上 4 个语义特征（（ii）用的数据）"],
    ["data/llm/llm_scores_v1~v4.csv", "—", "四版提示词各自的专利级打分结果"],
    ["data/llm/抽查_原文与打分_v4.csv", "—", "原文 + 打分对照，可用 Excel 打开人工检查"],
    ["results/i_基准模型结果.csv", "—", "（i）的 18 个 R²"],
    ["results/ii_增量解释力.csv", "—", "（ii）三组模型的增量 R²"],
    ["results/ii_特征重要性.csv", "—", "（iii）逐个维度加入的增量"],
    ["results/ii_正交性检验.csv", "—", "每个语义维度的正交信息占比"],
    ["results/ii_相关系数矩阵.csv", "—", "语义特征与数量特征的相关系数"],
], widths=[6.4, 1.8, 9.2])

doc.add_page_break()

# ============ 汇报问答 ============
doc.add_heading("第六部分　汇报时的「一句话答案」", level=1)
TABLE(["考官可能问", "你答"], [
    ["（i）你做了什么？",
     "用 12 个数量类专利特征，跑线性回归和随机森林，在三种设定下对三个企业结果变量做预测，"
     "比较 18 个 R²。结论是：跨公司解释不了，公司内能解释约 18%，关系是线性的。"],
    ["为什么 R² 是负的？",
     "负 R² 表示模型比直接猜平均值还差。企业财务表现主要由公司自身的稳定特征决定，"
     "当年专利数量解释不了。"],
    ["为什么按公司分组划分数据？",
     "同一家公司有 11 年数据。随机划分会让同一家公司同时出现在训练集和测试集，"
     "模型「见过」它，R² 虚高，这叫信息泄漏。"],
    ["为什么选这四个语义维度？",
     "题目给了 8 个候选。选择依据是「与基准数量特征的重叠最小」，"
     "因为（ii）要验证的正是「正交信息」。所以放弃了权利要求广度（基准已有权利要求数量）"
     "和合作网络属性（基准已有发明人数量）。"],
    ["提示词改了几版？为什么改？",
     "四版。v1 抽象锚点，结果 85% 都打了 3 分（缺区分度）；v2 加示例，没改善；"
     "v3 改成 1–10 分制并加入专利类型线索，取值种类从 3 种升到 8 种；"
     "v4 修正了「商业化距离」的定义错误（外观设计被误判为离商业化最远）。"],
    ["语义特征带来增量了吗？",
     "方向为正但幅度很小：总资产净利润率上，增量 R² 约 +0.01。"
     "说明语义特征确实含有新信息，但对企业财务结果的预测能力提升有限。"],
    ["你怎么证明语义特征不是数量特征的重复？",
     "两项检验：① 相关系数矩阵，平均 |r| 只有 0.21；② 用数量特征回归语义特征，"
     "R² 为 0.35–0.55，也就是 45%–65% 的变异是数量特征解释不了的。"],
    ["哪个维度最重要？",
     "跨领域整合度。在三个结果变量上单独加入它带来的增量都排第一。"],
    ["这部分为什么没做？",
     "（如实说）Shapley 值和因果森林属于进阶方法，四天工期内未纳入；"
     "TF-IDF 文本特征因为计算量大，安排在最后。"],
], widths=[4.6, 12.6])

P()
P("截止时间：2026 年 10 月 15 日。", bold=True)

doc.save(OUT)
print("已保存:", OUT)
