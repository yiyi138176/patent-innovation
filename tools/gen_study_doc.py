# -*- coding: utf-8 -*-
"""生成《项目说明书 + 学习清单》Word 文档"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\YYYi3\Documents\deepseek-harness\default-workspace\笔试-项目说明书与学习清单.docx"

FONT = "微软雅黑"
MONO = "Consolas"

doc = Document()

# ---------- 页面 A4 ----------
for s in doc.sections:
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(2.0)
    s.left_margin = s.right_margin = Cm(2.0)

# ---------- 默认字体 ----------
st = doc.styles["Normal"]
st.font.name = FONT
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.line_spacing = 1.25
st.paragraph_format.space_after = Pt(4)

for name, sz in [("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)]:
    s2 = doc.styles[name]
    s2.font.name = FONT
    s2.font.size = Pt(sz)
    s2.font.bold = True
    s2.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    s2.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    s2.paragraph_format.space_before = Pt(10)
    s2.paragraph_format.space_after = Pt(5)


def P(text="", bold=False, size=10.5, indent=0, color=None, align=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if align:
        p.alignment = align
    r = p.add_run(text)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size)
    r.bold = bold
    if color:
        r.font.color.rgb = color
    return p


def RICH(parts, indent=0):
    """parts: [(text, bold, size, color_or_None), ...]"""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    for t, b, s, c in parts:
        r = p.add_run(t)
        r.font.name = FONT
        r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r.font.size = Pt(s)
        r.bold = b
        if c:
            r.font.color.rgb = c
    return p


def BUL(text, indent=0.6):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(text)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(10.5)
    return p


def TABLE(headers, rows, widths=None, fontsize=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(fontsize)
        r.font.name = FONT
        r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCE6F1")
        hdr[i]._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(v))
            r.font.size = Pt(fontsize)
            r.font.name = FONT
            r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
            p.paragraph_format.space_after = Pt(1)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def CODE(lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(ln if ln else " ")
        r.font.name = MONO
        r.font.size = Pt(9)


# ============ 封面 ============
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("笔试项目说明书\n与学习清单")
r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
r.font.size = Pt(24)
r.bold = True
r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("专利文本特征与企业经济结果")
r.font.size = Pt(13)
r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

P()
RICH([("这份文档解决三个问题：", True, 11, None)], indent=0)
BUL("我们到底在做什么？（第一部分）")
BUL("我们已经做完了什么？（第二部分）")
BUL("我需要学什么、背什么？（第三～五部分）")
BUL("还要装什么软件？（第六部分）")

P()
P("打印建议：全部打印，装订成册，随时翻阅第四部分的术语词典。", size=9.5)
doc.add_page_break()

# ============ 第一部分 ============
doc.add_heading("第一部分　我们到底在做什么", level=1)

doc.add_heading("1.1　任务的来源", level=2)
P("2026 年 10 月 9 日，蒋浩东学长给了一份笔试任务（一周内完成，最晚 10 月 15 日）：")
BUL("不是考试，是一份小型科研训练任务")
BUL("要求提交 GitHub 代码仓库 + 实验报告 + 可复现性说明")
BUL("最后要带着电脑到创业学院线下汇报整个实验过程")
BUL("明确说明：不做 PPT")

doc.add_heading("1.2　一句话说清要研究什么", level=2)
p = doc.add_paragraph()
r = p.add_run("他想知道：专利的文本里，除了「有多少件专利」这种数字，")
r.font.size = Pt(11); r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
p = doc.add_paragraph()
r = p.add_run("还藏着哪些「有用」但「不重复」的信息？这些信息能不能解释企业的经营表现？")
r.font.size = Pt(11); r.bold = True; r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

P()
RICH([("「有用」", True, 10.5, None), (" = 能预测企业的财务结果", False, 10.5, None)])
RICH([("「不重复」", True, 10.5, None), (" = 不是「专利数量」的另一种说法", False, 10.5, None)])

doc.add_heading("1.3　四个部分分别在问什么", level=2)
TABLE(
    ["部分", "他在问什么（大白话）", "状态"],
    [
        ["（i）", "先做对照组。用传统的「数数字」方法（专利数、被引次数、权利要求数、IPC 分类…），能解释企业结果多少？关系是直线还是弯的？", "已完成"],
        ["（ii）", "核心。让大模型读专利文本，给每篇打四个维度的分。加上这些分，是不是解释得更准了？而且这些分是不是「新信息」（不是传统特征的重复）？", "待做"],
        ["（iii）", "逐个拆开看。四个维度一个个加进去，哪个最重要？对什么企业、什么行业最重要？", "待做"],
        ["（iiii）", "经济学的部分。自己造一个指标 x，配企业数据 y，用计量方法证明关系是真的（控制固定效应、讨论内生性、至少一种识别策略）。", "待做"],
    ],
    widths=[1.5, 12.5, 2.0])

RICH([("（i）和（ii）是主战场，（iiii）是加分项。", True, 10.5, None)])

doc.add_heading("1.4　要交什么", level=2)
TABLE(["交付物", "内容"], [
    ["GitHub 仓库", "代码（5 个模块）+ 日志 + 数据说明"],
    ["实验报告", "方法论 / 结果 / 讨论 / 附件"],
    ["可复现性说明", "环境配置、提示词版本、数据版本"],
    ["线下汇报", "带电脑到创业学院，当场演示整个实验过程"],
], widths=[4.0, 12.0])
doc.add_page_break()

# ============ 第二部分 ============
doc.add_heading("第二部分　我们已经做完了什么", level=1)

doc.add_heading("2.1　数据管线（今天一天从零走通）", level=2)
CODE([
    "专利原始数据（343MB，152 个 Excel）",
    "   |  extract_codes.py        提取每家公司对应的股票代码",
    "   |  check_codes.py           用官方代码表逐条校验（发现 3 处问题）",
    "   |  fetch_financials.py      从 akshare 抓取企业财务数据",
    "   |  build_patent_table.py    把 11.7 万条专利聚合成「公司-年份」特征",
    "   |  build_dataset.py         与企业财务数据合并",
    "   v",
    "主数据集.csv ：1,270 个观测 / 143 家公司 / 2015-2025 年",
])

doc.add_heading("2.2　已完成清单", level=2)
TABLE(["#", "完成的事", "结果"], [
    ["1", "搭建 Python 环境", "Python 3.14.8 + pandas / numpy / scikit-learn / akshare"],
    ["2", "拿到专利数据", "152 家公司、217 个字段、11.7 万条专利"],
    ["3", "提取股票代码", "152 家全部跑通"],
    ["4", "校验股票代码", "发现大富科技代码错误（已修正）、1 家代码缺失"],
    ["5", "抓取企业财务数据", "144 家公司 × 86 个变量，覆盖 2015-2025"],
    ["6", "筛选结果变量", "从 77 个变量中选出覆盖率 ≥97.8% 的三个"],
    ["7", "专利特征聚合", "2,481 个「公司-年份」观测，12 个特征"],
    ["8", "合并主数据集", "1,270 个观测 / 143 家公司 / 2015-2025"],
    ["9", "跑通（i）基准模型", "得出可解释的结论（见 2.4）"],
], widths=[1.0, 6.0, 9.0])

doc.add_heading("2.3　路上踩到的三个「数据坑」（都是加分项）", level=2)
TABLE(["#", "问题", "怎么发现", "怎么处理"], [
    ["1", "「东富龙」的 Excel 里装的是华中数控的专利", "逐家打开文件搜公司名", "剔除该样本"],
    ["2", "大富科技的代码误提取为 300127（与银河磁体重复）", "用 akshare 官方代码表逐条比对", "修正为 300134"],
    ["3", "「销售毛利率」2019 年后全部缺失，导致样本塌缩到 249 个", "合并后数字明显不对，回头逐项排查", "换成「资产负债率」，样本恢复到 1,270"],
], widths=[1.0, 4.8, 4.4, 5.8])

RICH([("这三个坑写进报告的「数据质量校验」一节，比什么都管用。", True, 10.5, None)])

doc.add_heading("2.4　（i）的结论：三个可以直接讲出来的发现", level=2)
P("问：基准专利特征（12 个「数数字」类特征）能解释企业的经济结果吗？")
P("答：看哪个角度，结论完全不同。")
P()
P("发现一：看「公司之间」——几乎解释不了", bold=True)
BUL("总资产净利润率的 R² = -0.051，主营业务收入增长率 = 0.026，资产负债率 = 0.039")
BUL("R² 接近 0 甚至为负，说明模型比「直接猜平均值」还差")
BUL("原因：企业的盈利、成长、杠杆水平主要由公司自身的稳定特征决定（行业、规模、技术积累），不是「今年申请了多少专利」")

P("发现二：看「同一家公司自己的年度变化」——能解释一部分", bold=True)
BUL("总资产净利润率的 R² = 0.180（约解释了 18% 的年度波动）")
BUL("说明：专利活动确实与公司自身的业绩起伏相关")

P("发现三：关系主要是「线性」的，不是「非线性」的", bold=True)
BUL("线性模型在 9 个组合里赢了 8 个")
BUL("随机森林（非线性模型）在 1,270 个观测上过拟合，表现反而更差")
BUL("这直接回答了题目里「进一步分析基准特征与企业创新结果之间存在的非线性或线性关系」的追问")

P()
P("对（ii）的启示", bold=True)
BUL("数量类特征只能解释约 18% 的公司内变异，剩下 82% 解释不了")
BUL("剩下的部分可能藏在专利的文本语义里（技术有多新、跨多少领域、有多通用）")
BUL("这就是（ii）要用大模型的原因")
doc.add_page_break()

# ============ 第三部分 ============
doc.add_heading("第三部分　知识地图：你需要学什么", level=1)

doc.add_heading("3.1　第一优先级：汇报时会被问到的概念（必背）", level=2)
P("这七个概念是学长最可能问的。不需要会推导，但必须能用大白话讲清楚。")
TABLE(["#", "概念", "你必须能回答的问题"], [
    ["1", "R²（决定系数）", "它衡量什么？为什么可以是负数？负的意味着什么？"],
    ["2", "训练集 / 测试集划分", "为什么要把数据分成两份？不分成吗？"],
    ["3", "信息泄漏", "什么是信息泄漏？我们是怎么避免的？为什么要按「公司」分组？"],
    ["4", "过拟合", "什么是过拟合？有什么现象？我们的数据里哪里出现了？"],
    ["5", "固定效应", "什么是固定效应？为什么要做「公司内去均值」？做完之后 R² 为什么变好了？"],
    ["6", "聚类稳健标准误", "为什么要用？不用会怎样？"],
    ["7", "内生性", "什么是内生性？为什么它让「相关」不能当「因果」？"],
], widths=[1.0, 3.6, 11.4])

doc.add_heading("3.2　第二优先级：数学基础（对照你的课程）", level=2)
P("你现在的进度：高数上了两节课，自学到「无穷小」。这个进度做这件事是够的，但下面这些要补。")
TABLE(["数学分支", "需要知道什么", "和你的课对应", "急迫度"], [
    ["线性代数", "向量、矩阵、矩阵乘法（不用会证明）", "大一上或大一下", "中"],
    ["概率统计", "期望、方差、协方差、条件期望、相关系数", "大一下（概率论与数理统计）", "高"],
    ["微积分", "偏导数、最小值/最大值（理解「最小二乘」即可）", "你现在学的高数", "中"],
    ["统计学", "假设检验、显著性、p 值、置信区间", "概率论与数理统计的后半部分", "高"],
], widths=[2.4, 6.6, 5.0, 1.6])

P()
P("建议：先自学「期望、方差、协方差、相关系数」这四个概念。它们是大白话解释 R² 和过拟合的基础，B 站搜「可汗学院 统计学」或「统计学的本质」即可。", size=10)

doc.add_heading("3.3　第三优先级：经济学背景（知道就行）", level=2)
BUL("这三个结果变量代表什么经济含义：盈利能力（ROA）、成长性（营收增长率）、融资约束（资产负债率）")
BUL("创新经济学的基本问题：「企业创新投入能否转化为经营绩效」")
BUL("专利质量的经典文献衡量指标：引用次数、权利要求数、同族规模、技术覆盖领域数")
BUL("这些不要求读原文，但要知道「为什么这些指标能代表专利质量」")
doc.add_page_break()

# ============ 第四部分 ============
doc.add_heading("第四部分　专业名词大白话词典", level=1)
P("这一部分最重要。所有术语都用大白话解释，并标注我们哪里用到了。")

doc.add_heading("4.1　统计学与计量经济学", level=2)
TABLE(["术语", "大白话解释", "我们的例子里哪里用"], [
    ["回归", "找一个公式，描述「X 变化时 Y 大概怎么变」。", "全部建模"],
    ["线性回归", "假设关系是一条直线：Y = a + bX。b 就是「X 每多 1 个单位，Y 平均变化多少」。优点是简单、好解释。", "设定①②③的线性模型"],
    ["非线性 / 非线性模型", "关系不是直线，是弯的或者有拐点。例如：专利从 0 增到 10 件很有用，但从 1000 增到 1010 件没区别。", "我们用的非线性模型是随机森林"],
    ["随机森林", "种很多棵「决策树」，每棵树各预测一次，最后取平均。能自动捕捉弯曲复杂的关系，但数据少时容易过拟合。", "三种设定里的非线性模型"],
    ["过拟合", "模型把训练数据「背下来」了，包括噪声，所以在新数据上表现很差。类比：背答案不理解题目，考原题满分、考新题完蛋。", "随机森林 R² 比线性还低，就是过拟合"],
    ["R²（决定系数）", "模型解释了 Y 的多少比例的变异。① R²=1 完美；② R²=0 和「直接猜平均值」一样；③ R²<0 比猜平均值还差。", "（i）的核心指标"],
    ["训练集 / 测试集", "把数据分两份：一份教模型（训练集），一份留着考它（测试集）。不分开的话「考得好」是假的。", "1270 个观测 → 1016 训练 / 254 测试"],
    ["信息泄漏", "测试集里混进了模型「见过」的信息，成绩虚高。", "同一公司有 11 年数据，所以按「公司」分组划分"],
    ["交叉验证", "把数据切成 K 份，轮流拿其中一份当测试集，最后取平均。比单次划分更稳定。", "时间够可以补做"],
    ["面板数据", "同一批对象、多个时间点的数据。", "143 家公司 × 11 年 = 1270 个观测"],
    ["非平衡面板", "不是每个对象都有全部时间点的数据。", "有的公司 2024 年才上市，只有 2 年数据"],
    ["均值去心 / 去均值", "把每个个体自己的平均值扣掉，只看它在自己均值上下的波动。", "设定③「公司内去均值」"],
    ["固定效应", "控制每个个体「不随时间变化」的特征。做完之后，比较的就是「同一家公司自己今年和去年比」。", "设定③，R² 从负变成 0.18"],
    ["年度效应", "控制所有公司共同经历的年度冲击，比如 2020 年疫情。", "设定②「年度去均值」"],
    ["聚类稳健标准误", "同一家公司的数据不独立（今年业绩和去年相关），普通检验会高估确定性。聚类标准误把这一点算进去，让结论更保守可信。", "（iiii）回归要用"],
    ["缩尾（Winsorize）", "把极端大和极端小的值截断到某个分位点。", "把营收增长率里 155% 和 -45% 截到 1%/99% 分位"],
    ["残差", "实际值减去模型预测值，剩下的部分。直觉上就是「模型没解释掉的东西」。", "正交化时要用"],
    ["内生性", "X 和 Y 之间「谁影响谁」说不清，或者有第三个因素同时影响两者。例如：是专利导致业绩好，还是业绩好的公司才有钱申请专利？", "（iiii）要讨论"],
    ["识别策略", "一套用来证明「这是因果关系而不是相关关系」的方法。常见的有工具变量、双重差分、断点回归、合成控制法。", "（iiii）至少要做一种"],
    ["工具变量（IV）", "找一个「只影响 X、不直接影响 Y」的变量，用它来「清洗」X。", "（iiii）备选识别策略"],
    ["双重差分（DID）", "比较「受政策影响的组」和「不受影响的组」在政策前后的变化，两次差分掉共同趋势。", "（iiii）备选识别策略"],
    ["断点回归（RDD）", "利用某个「门槛」（比如分数线、规模线）两侧的跳跃来识别因果。", "（iiii）备选识别策略"],
    ["合成控制法", "人工造一个「假对照组」，让它和真实处理组在政策前走势一致，再比较政策后的差异。", "（iiii）备选识别策略"],
    ["正交化", "把新特征里「已经被旧特征解释掉的部分」去掉，只留新信息。做法：用基准特征回归新特征，取残差当新特征。", "（ii）验证 LLM 特征是不是新信息"],
    ["增量解释力", "加入新特征后，R² 提高了多少。", "（ii）的核心指标"],
    ["Shapley 值", "一种「公平分配功劳」的方法，考虑某个特征和其他特征的各种组合，算出它对预测的净贡献。来自博弈论。", "（ii）的可选方法"],
    ["置换重要性", "把某一列特征的值随机打乱，看模型性能掉多少。掉得多说明这列重要。", "（ii）的可选方法"],
    ["LASSO", "一种会自动把没用特征的系数「压到 0」的回归方法，能帮你挑特征。", "（ii）的可选方法"],
    ["因果森林", "随机森林的升级版，用来估计「影响」在不同个体之间的差异。属于进阶方法。", "（ii）提到，时间不够可跳过"],
], widths=[2.7, 9.5, 3.8])

doc.add_heading("4.2　机器学习与文本处理", level=2)
TABLE(["术语", "大白话解释", "我们的例子里哪里用"], [
    ["特征（Feature）", "模型用来做预测的输入变量。", "12 个专利特征，如平均被引次数"],
    ["特征重要性", "每个特征对预测的贡献有多大。", "随机森林自带，我们打印了 Top5"],
    ["TF-IDF", "一种给词打分的文本表示法。TF = 词在这篇文档里出现多少次；IDF = 这个词在所有文档里有多罕见。一个词「在这篇常见、在所有文档罕见」→ 分数高、有区分度。例：「专利」到处都是，分数低；「钙钛矿」很少见，分数高。", "（i）的文本基准特征"],
    ["词袋（Bag of Words）", "把文本当成一袋词，只管每个词出现多少次，不管顺序。", "（i）的文本基准特征"],
    ["降维 / SVD / PCA", "把很多个特征压缩成少数几个，保留主要信息。", "TF-IDF 维度太高时要用"],
    ["大模型 / LLM", "像 DeepSeek 这样能理解和生成语言的模型。", "（ii）用它读专利摘要打分"],
    ["Prompt（提示词）", "给大模型的指令。", "要求每改一版都存下来（v1、v2）"],
    ["语义特征", "从文本「意思」里提取出来的特征，而不是数数字得到的。", "（ii）的四个维度"],
], widths=[2.7, 9.5, 3.8])

doc.add_heading("4.3　经济学概念", level=2)
TABLE(["术语", "大白话解释", "我们的例子里哪里用"], [
    ["盈利能力", "赚不赚钱。", "总资产净利润率（ROA）"],
    ["成长性", "长不长个。", "主营业务收入增长率"],
    ["融资约束", "企业想融资但融不到、或者融资成本高的程度。", "用资产负债率代理"],
    ["全要素生产率（TFP）", "衡量生产效率：投入（资本、劳动）之外，还有多少产出增长。计算复杂，需要 LP/OP 方法。", "放弃（时间不够）"],
    ["专利质量", "专利在技术上的重要程度，不等于专利数量。", "（ii）要捕捉的就是它"],
], widths=[2.7, 9.5, 3.8])
doc.add_page_break()

# ============ 第五部分 ============
doc.add_heading("第五部分　你现在能讲出的结论（背下来）", level=1)
P("汇报时如果紧张，就按这个顺序说。")

doc.add_heading("5.1　三分钟版本", level=2)
P("「我用 152 家上市公司的 11.7 万条专利数据，做完了第一部分的基准实验。」")
P("「我把专利的数量类特征——引用次数、权利要求数、同族规模、发明人数、IPC 领域数等 12 个——汇总到公司—年份层面，和企业的三个财务结果匹配。」")
P("「结果分两面：从公司之间看，这些特征几乎解释不了财务差异，R² 接近 0；但从同一家公司自己的年度变化看，能解释约 18% 的总资产净利润率波动。」")
P("「另外，题目问关系是线性还是非线性——答案是线性。线性模型在 9 个组合里赢了 8 个，随机森林在 1,270 个观测上过拟合了。」")
P("「这说明剩下 82% 的变异解释不了，我认为可能藏在专利的文本语义里，所以下一步要用大模型提取文本特征。」")

doc.add_heading("5.2　被问到时的标准答法", level=2)
TABLE(["如果他问…", "你就答…"], [
    ["你的样本为什么是 1,270 个？", "原始 152 家，剔除 1 家文件内容错位、1 家代码缺失、6 家北交所无财务数据，剩 144 家；再和专利数据按公司—年份匹配，得到 1,270 个观测、143 家公司。"],
    ["为什么 R² 是负的？", "负 R² 说明模型比直接猜平均值还差。因为企业财务表现主要由公司自身的稳定特征决定，不是当年专利数量能解释的。"],
    ["你怎么划分训练测试集？", "按「公司」分组划分，不是随机划分。因为同一家公司有 11 年数据，随机划分会让同一家公司同时出现在训练集和测试集，造成信息泄漏、R² 虚高。"],
    ["怎么证明这些特征不是重复的？", "目前是看特征重要性，下一步（ii）会用正交化、LASSO 和置换重要性来严格验证。"],
    ["为什么不用 Stata？", "Stata 授权有困难，而且破解版有安全风险。Python 的 statsmodels 和 linearmodels 能实现同样的固定效应和聚类稳健标准误，代码还更容易复现。"],
    ["你的研究有什么局限？", "样本 143 家、非平衡面板；2025 年专利数据不完整；财务数据来自公开网页接口；只用摘要和首项权利要求，没用说明书全文；内生性只做了有限处理。"],
    ["这部分为什么没做？", "（如实说）时间不够，或者我还没学会。"],
], widths=[4.5, 11.5])
doc.add_page_break()

# ============ 第六部分 ============
doc.add_heading("第六部分　软件与工具清单", level=1)

doc.add_heading("6.1　已经装好的（不用管）", level=2)
TABLE(["软件 / 包", "版本", "用途"], [
    ["Python", "3.14.8", "主语言"],
    ["pip", "26.2.1", "装包"],
    ["VS Code + Python 插件", "—", "写代码"],
    ["pandas", "3.0.6", "数据表处理"],
    ["numpy", "2.5.3", "数值计算"],
    ["scikit-learn", "1.9.1", "机器学习模型"],
    ["akshare", "1.19.1", "抓取 A 股财务数据"],
    ["requests", "2.34.2", "网络请求"],
    ["scipy", "1.18.1", "科学计算"],
    ["openpyxl", "3.1.5", "读写 Excel"],
], widths=[4.5, 2.5, 9.0])

doc.add_heading("6.2　还需要装的（重要）", level=2)
TABLE(["#", "软件 / 包", "为什么需要", "怎么装", "急迫度"], [
    ["1", "Git", "GitHub 仓库必须用 Git 上传。现在没装。", "搜「Git for Windows 下载」，装完在终端敲 git --version 验证", "高"],
    ["2", "statsmodels", "（iiii）的计量回归（固定效应、聚类标准误）", "pip install statsmodels -i https://pypi.tuna.tsinghua.edu.cn/simple", "高"],
    ["3", "linearmodels", "面板数据模型（PanelOLS），比 statsmodels 更好用", "pip install linearmodels -i https://pypi.tuna.tsinghua.edu.cn/simple", "高"],
    ["4", "matplotlib", "画图（报告和汇报要放图）", "pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple", "中"],
    ["5", "小熊猫 C++", "C 语言课用。Dev-C++ 在 Windows 11 上编译报错（它自己的头文件问题），换这个", "搜「小熊猫C++ 官网」下载", "中（课程用）"],
    ["6", "大模型 API", "（ii）要用大模型给专利打分。你没有 API，但可以用免费的", "见 6.3", "高"],
], widths=[0.9, 2.8, 5.4, 5.4, 1.5])

doc.add_heading("6.3　关于大模型 API（（ii）的前提）", level=2)
P("你选了「方案 B：抽样打分」，但它仍然需要一个能批量调用的 API。你说你没有——有一个免费的选择：")
P()
RICH([("智谱 GLM-4-Flash", True, 11, RGBColor(0xC0, 0x00, 0x00)), ("（免费）", True, 11, RGBColor(0xC0, 0x00, 0x00))])
BUL("网址：open.bigmodel.cn（智谱 AI 开放平台）")
BUL("注册需要手机号 + 实名认证（学生也可以）")
BUL("GLM-4-Flash 这个模型是免费的，适合我们这种「大量短文本打分」的任务")
BUL("注册后在「API Keys」页面拿到密钥（一串以 . 分隔的字符），保存好，不要外泄")
P()
P("备选的免费额度平台：", bold=True)
BUL("硅基流动 SiliconFlow（注册送额度）")
BUL("阿里云百炼（通义千问，有免费额度）")
BUL("讯飞星火（有免费额度）")
P()
RICH([("如果实在拿不到 API", True, 10.5, None), ("，我们就走「关键词词典法」：用词表给四个维度打分。能出结果，但报告里必须如实写明「本文使用词典法而非大模型」。", False, 10.5, None)])

doc.add_heading("6.4　接下来要装的顺序", level=2)
CODE([
    "# 1) 装三个 Python 包（在 VS Code 终端里逐行敲）",
    "pip install statsmodels linearmodels matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple",
    "",
    "# 2) 验证",
    "python -c \"import statsmodels, linearmodels, matplotlib; print('OK')\"",
    "",
    "# 3) 装 Git（下载安装包，一路下一步即可）",
    "git --version",
    "",
    "# 4) 去 open.bigmodel.cn 注册，拿 API Key",
])

doc.add_heading("6.5　环境配置要写进报告", level=2)
P("题目要求交「可复现性说明」。装完上面的包之后，在终端运行下面命令，把输出贴进报告：")
CODE([
    "python --version",
    "pip freeze > requirements.txt",
])
P("requirements.txt 这个文件要一起提交到 GitHub。）", size=9.5)

doc.add_page_break()
# ============ 附录 ============
doc.add_heading("附录　今日（10 月 10 日）进度速览", level=1)
TABLE(["模块", "状态", "说明"], [
    ["环境搭建", "完成", "Python + 全部依赖"],
    ["专利数据", "完成", "152 家 / 11.7 万条 / 217 字段"],
    ["股票代码提取与校验", "完成", "发现并修正 3 处问题"],
    ["企业财务数据", "完成", "144 家 × 86 个变量"],
    ["专利特征聚合", "完成", "2,481 个公司—年份观测"],
    ["主数据集", "完成", "1,270 观测 / 143 家 / 2015-2025"],
    ["（i）基准建模", "完成", "线性 vs 非线性 × 三种设定"],
    ["（ii）LLM 特征提取", "待做", "需要先解决 API"],
    ["（iii）维度重要性", "待做", "依赖（ii）"],
    ["（iiii）计量回归", "待做", "需要 statsmodels / linearmodels"],
    ["实验报告", "待做", "—"],
    ["GitHub 仓库", "待做", "需要先装 Git"],
], widths=[4.5, 2.0, 9.5])

P()
P("截止时间：2026 年 10 月 15 日。剩余 5 天。", bold=True)

doc.save(OUT)
print("已保存:", OUT)
