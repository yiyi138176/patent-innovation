# -*- coding: utf-8 -*-
"""生成《10月10日工作详解》——把日志翻译成大白话"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\YYYi3\Documents\deepseek-harness\default-workspace\10月10日工作详解.docx"
FONT = "微软雅黑"

doc = Document()
for s in doc.sections:
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(2.0)
    s.left_margin = s.right_margin = Cm(2.0)

st = doc.styles["Normal"]
st.font.name = FONT
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.line_spacing = 1.3
st.paragraph_format.space_after = Pt(5)

for name, sz in [("Heading 1", 17), ("Heading 2", 13.5), ("Heading 3", 11.5)]:
    s2 = doc.styles[name]
    s2.font.name = FONT
    s2.font.size = Pt(sz)
    s2.font.bold = True
    s2.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    s2.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    s2.paragraph_format.space_before = Pt(12)
    s2.paragraph_format.space_after = Pt(6)


def P(t="", bold=False, size=10.5, indent=0, color=None, align=None, italic=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if align:
        p.alignment = align
    r = p.add_run(t)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        r.font.color.rgb = color
    return p


def RICH(parts, indent=0, box=False):
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


def BUL(t, indent=0.6):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(t)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(10.5)
    return p


def BOX(title, lines):
    """带底纹的类比框"""
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    cell = t.rows[0].cells[0]
    cell._tc.get_or_add_tcPr().append(OxmlElement("w:shd"))
    cell._tc.get_or_add_tcPr()[-1].set(qn("w:fill"), "FFF3D6")
    cell.width = Cm(17.0)
    cell.text = ""
    p0 = cell.paragraphs[0]
    r = p0.add_run(title)
    r.bold = True
    r.font.size = Pt(10.5)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.color.rgb = RGBColor(0xA0, 0x50, 0x00)
    for ln in lines:
        p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(ln)
        r.font.size = Pt(10)
        r.font.name = FONT
        r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def KEY(text):
    """一句话总结"""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    r = p.add_run("一句话记住：")
    r.bold = True
    r.font.size = Pt(10.5)
    r.font.name = FONT
    r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    r2 = p.add_run(text)
    r2.bold = True
    r2.font.size = Pt(10.5)
    r2.font.name = FONT
    r2.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r2.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    return p


def TABLE(headers, rows, widths=None, fontsize=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(fontsize)
        r.font.name = FONT
        r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCE6F1")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(str(v))
            r.font.size = Pt(fontsize)
            r.font.name = FONT
            r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ================= 封面 =================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("10 月 10 日工作详解")
r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
r.font.size = Pt(24)
r.bold = True
r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("把今天的日志翻译成大白话")
r.font.size = Pt(13)
r.font.name = FONT
r.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

P()
P("说明：日志里那些术语我直接写进去了，但没解释。这份文档逐个解释——")
P("每个问题都用生活里的类比讲清楚，你看完应该能对着别人讲出来。", size=10)
P()
RICH([("使用建议：", True, 10.5, None),
      ("先看第三部分（五个概念），那是今天最重要的收获；再看第一部分（遇到的问题）。", False, 10.5, None)])
doc.add_page_break()

# ================= 第一部分 =================
doc.add_heading("第一部分　今天遇到的 5 个问题", level=1)
P("这五个问题都是真实发生的，我把「怎么发现的、为什么会这样、怎么解决的」都写出来。", size=10)

# --- 问题1 ---
doc.add_heading("问题 1：合并数据后，样本莫名其妙只剩 249 个", level=2)
P("预期：应该有大约 1,500 条记录（143 家公司 × 11 年）。", size=10)
P("实际：只跑出 249 条，而且年份只有 2015–2018。", size=10)
P()
P("排查过程（两轮）：", bold=True, size=10.5)
BUL("第一轮：我以为是「日期格式」有问题，写了个脚本把日期列打出来看 → 日期完全正常。")
BUL("第二轮：我改去看三个结果变量的「缺失情况」→ 找到了真凶。")
P()
P("真正的原因：", bold=True, size=10.5)
P("我们选的三个结果变量里，有一个叫「销售毛利率」。这个变量在 2019 年之后"
  "一条数据都没有（覆盖率只有 19.8%）。而我们要求「三个变量都不能缺」，"
  "于是 2019 年之后的所有记录全被删掉了——样本就塌缩到只剩 2015–2018。", size=10, indent=0.4)
P()
P("怎么解决的：", bold=True, size=10.5)
P("换掉那个变量。我们查了全部 77 个可用的财务变量，发现「资产负债率」"
  "覆盖了 99.9% 的年份，用它替换之后，样本恢复到 1,270 条。", size=10, indent=0.4)
BOX("生活类比", [
    "你要做蛋糕，食谱上写着要「奶油」。你跑遍超市买齐了所有材料，",
    "最后才发现——这家超市根本不卖奶油。",
    "",
    "问题不在于你不会做蛋糕，而在于你事先没确认「这个材料到底有没有」。",
])
KEY("拿到数据后，第一件事是检查每个变量的覆盖范围，而不是直接开始建模。")

# --- 问题2 ---
doc.add_heading("问题 2：模型跑出来的 R² 是负数，我以为程序写错了", level=2)
P("R² 是一种「打分」——衡量模型预测得准不准。", size=10)
P("正常来说它应该在 0 到 1 之间。结果我跑出来是 -0.05、-0.16 这样的负数。", size=10)
P()
P("我一开始的反应：肯定是代码写错了。", size=10, italic=True)
P("但查过之后发现：这是完全正常的，而且它本身就是今天最有价值的发现。", size=10)
P("（为什么是正常的，见第三部分的「概念一」。）", size=10)
KEY("负的 R² 不是 bug，它是一个真实的、有意义的结论。")

# --- 问题3 ---
doc.add_heading("问题 3：同一个股票代码，对应了两家公司", level=2)
P("校验的时候发现：「大富科技」和「成都银河磁体」两家公司，"
  "被分到了同一个股票代码 300127。", size=10)
P()
P("原因：专利数据里有一列叫「工商上市代码」。这一列记录的是"
  "「这项专利的所有申请人」的代码——如果一项专利是几家公司联合申请的，"
  "这一列里就会有多个代码。我们取「出现最多的那个」，结果取错了。", size=10, indent=0.4)
P()
P("怎么发现的：拿 akshare 提供的「A 股官方代码表」，"
  "把 152 家公司的代码一个一个去对。", size=10, indent=0.4)
P("怎么解决的：大富科技的代码改成 300134。", size=10, indent=0.4)
KEY("数据的「名称」和「内容」不一定对得上，必须找一份权威来源逐个核对。")

# --- 问题4 ---
doc.add_heading("问题 4：一个文件名叫「东富龙」，里面装的全是别家的专利", level=2)
P("核对时发现：「东富龙科技集团股份有限公司.xlsx」这个文件里，"
  "全文搜不到「东富龙」三个字，装的全是「华中数控」的专利。", size=10)
P()
P("怎么发现的：我在每个文件里搜它自己的公司名——其他 151 家都能搜到，"
  "只有这一家搜不到。", size=10, indent=0.4)
P("怎么解决的：把这 1 家剔除（不影响整体，还剩 143 家）。", size=10, indent=0.4)
KEY("发现异常要找一个「能批量重复」的验证方法，而不是靠眼睛看。")

# --- 问题5 ---
doc.add_heading("问题 5：API 密钥没保存下来", level=2)
P("注册智谱大模型之后创建了一个密钥，但那个页面显示的是打码版本（5b27...kz0t）。"
  "而平台提示：完整密钥只在创建时显示一次。", size=10)
P()
P("怎么解决的：重新建一个，这次先复制再关窗口。", size=10, indent=0.4)
P("顺便养成了一个习惯：密钥单独放在 config.py 文件里，"
  "并加进 .gitignore，这样上传到 GitHub 时不会泄露。", size=10, indent=0.4)
KEY("密钥只在创建时显示一次，看到就立刻复制；而且永远不要上传到公开的代码仓库。")

doc.add_page_break()

# ================= 第二部分 =================
doc.add_heading("第二部分　今天得到的结果", level=1)

doc.add_heading("2.1　数据方面的结果", level=2)
TABLE(["数字", "是什么意思"], [
    ["152 家公司", "学长给的专利数据，一家一个 Excel 文件"],
    ["11.7 万条专利", "所有公司加起来一共这么多项专利"],
    ["144 家公司", "能成功匹配到财务数据的公司数（152 减去 8 家有问题的）"],
    ["86 个变量", "每个公司的财务指标，比如净利润率、资产负债率、增长率等"],
    ["2,481 个观测", "「公司 × 年份」的组合数。一家公司有 11 年，就是 11 个观测"],
    ["1,270 个观测 / 143 家", "最终用来做分析的数据量（有的公司某一年没申请专利，匹配不上）"],
], widths=[3.8, 12.2])
P()
RICH([("「观测」这个词", True, 10.5, None),
      ("可以理解成「表格里的一行」。一行 = 一家公司在某一年的记录。", False, 10.5, None)])

doc.add_heading("2.2　模型结果：三种看法，结论完全不同", level=2)
P("我们问的问题是：「专利的数量类特征（专利数、被引次数、权利要求数等），"
  "能解释企业的财务表现吗？」", size=10)
P("用了三种「看法」来考察，结果差别很大：", size=10)
P()
TABLE(["看法", "在问什么（大白话）", "总资产净利润率的 R²", "怎么读"], [
    ["① 跨公司", "专利多的公司，业绩就更好吗？", "-0.051", "看不出关系，甚至比瞎猜还差"],
    ["② 去掉年度影响", "把 2020 年疫情这种共同冲击去掉之后呢？", "-0.165", "更差了"],
    ["③ 同一公司自己的变化", "一家公司今年多申请专利，明年业绩会变好吗？", "+0.180", "有一点关系，能解释 18%"],
], widths=[3.0, 5.6, 2.9, 4.5], fontsize=9)
P()
RICH([("最重要的结论：", True, 11, RGBColor(0xC0, 0x00, 0x00)),
      ("看「公司之间」没用；但看「同一家公司自己的年度变化」有用（R² = 0.180）。", False, 11, None)])

doc.add_heading("2.3　线性 vs 非线性：哪个更好？", level=2)
P("我们用了两种模型：", size=10)
BUL("线性模型：假设关系是一条直线（简单）")
BUL("随机森林：一种能自动捕捉复杂关系的模型（复杂）")
P()
P("结果：一共 9 组对比，线性模型赢了 8 组。", bold=True, size=10.5)
P("也就是说——在这个数据量下（1,270 条），复杂的模型反而更差。", size=10)
P("原因见第三部分的「概念四：过拟合」。", size=10)
P()
RICH([("这个结论直接回答了题目的追问：", True, 10.5, None),
      ("「分析基准特征与企业创新结果之间存在的非线性或线性关系」——", False, 10.5, None),
      ("答案是「线性」。", True, 10.5, RGBColor(0xC0, 0x00, 0x00))])

doc.add_heading("2.4　这对下一步（ii）意味着什么？", level=2)
P("数量类特征只能解释 18%，剩下 82% 解释不了。", size=10)
P("那剩下的部分在哪里？可能在专利的「文字内容」里——"
  "比如这项技术有多新、跨了多少个领域、离商业化有多远。", size=10)
P("这就是我们要用大模型读专利文本、打四个维度的分的原因。", bold=True, size=10.5)

doc.add_page_break()

# ================= 第三部分 =================
doc.add_heading("第三部分　必须搞懂的 5 个概念（零基础版）", level=1)
P("这部分是今天最重要的收获。每个概念都配了生活类比，你看完应该能对别人讲出来。", size=10)

# 概念1
doc.add_heading("概念一：R²（决定系数）—— 为什么可以是负数？", level=2)
P("R² 是一个 0 到 1 之间的分数，衡量「模型预测得准不准」。", size=10)
BOX("生活类比：猜同学的考试成绩", [
    "假设你要猜全班同学的期末成绩，有三种情况：",
    "",
    "• R² = 0：你什么都不知道，只好一律猜「平均分 75 分」。",
    "• R² = 1：你能精确预测每个人考多少分（神仙）。",
    "• R² = 0.5：你能解释一半的差异（挺不错了）。",
    "• R² < 0：你用了很多信息去猜，结果比「一律猜 75 分」还差！",
])
P("为什么会小于 0？", bold=True, size=10.5)
P("因为模型用了那些专利特征之后，预测反而比「一律猜平均值」更糟糕。"
  "换句话说：这些信息不但没用，还起了干扰作用。", size=10, indent=0.4)
P()
P("那为什么用专利特征预测企业业绩会失败？", bold=True, size=10.5)
BOX("生活类比：用「做了多少道题」预测成绩", [
    "你想通过「一个学生这学期做了多少道题」来预测他的期末成绩。",
    "",
    "结果你会发现：做了 100 道题的学生，可能考 90 分，也可能考 50 分。",
    "因为成绩主要由「这个学生本身的底子」决定——",
    "聪明程度、基础好不好、老师教得怎么样——而不是「做了多少题」。",
    "",
    "企业完全一样：赚不赚钱主要由「这家公司本身」决定——",
    "所处行业、公司规模、管理水平——而不是「今年申请了多少专利」。",
])
KEY("跨公司预测时 R² 接近 0 甚至为负，是符合预期的，不是程序写错了。")

# 概念2
doc.add_heading("概念二：信息泄漏 —— 为什么不能随机划分数据？", level=2)
P("做模型时要先把数据分成两份：一份用来「教」模型（训练集），"
  "一份留着「考」它（测试集）。", size=10)
BOX("生活类比：考试前老师把原题给了你", [
    "如果考试前老师把考卷原题发给你，你考了 100 分。",
    "但这不代表你学得好——你只是把答案背下来了。",
    "",
    "真正能检验你水平的方法是：给你没见过的题。",
    "",
    "数据里的「信息泄漏」就是这个道理：",
    "如果测试集里的信息，模型在学习时已经见过了，那测试成绩就是虚高的。",
])
P("我们的数据里为什么会有这个问题？", bold=True, size=10.5)
P("同一家公司有 2015–2025 共 11 年的数据。如果随机划分，"
  "这家公司的 2015 年可能进了训练集，2020 年进了测试集。"
  "模型在学习时就「见过」这家公司了——它记住了这家公司的特点，"
  "所以测试成绩会虚高。", size=10, indent=0.4)
P()
P("我们的做法：", bold=True, size=10.5)
P("按「公司」分组划分。让测试集里全是模型从没见过的公司——"
  "这才相当于「考新题」，测出来的才是真实水平。", size=10, indent=0.4)
KEY("按公司分组划分，才能测出模型面对「新公司」时的真实预测能力。")

# 概念3
doc.add_heading("概念三：固定效应（公司内去均值）—— 为什么做完 R² 就变好了？", level=2)
P("这是今天最重要、也最有用的一个方法。", size=10)
BOX("生活类比：比较 10 个学生的「进步幅度」", [
    "你想知道：这 10 个学生，谁进步了？",
    "",
    "但如果直接比考试分数，小明（重点中学）永远比小红（普通中学）高。",
    "你根本看不出谁进步了。",
    "",
    "正确做法：把每个人自己的平均分减掉，",
    "只看他「这次比自己的平均水平高还是低」。",
    "",
    "这样重点中学和普通中学的差异就被消掉了，只剩下「进步」本身。",
])
P("放到企业上：", bold=True, size=10.5)
P("把每家公司的平均水平扣掉，只看它「今年比自己的往年水平怎么样」。"
  "这样公司之间的大小差异（大公司 vs 小公司、好行业 vs 差行业）就被消掉了。", size=10, indent=0.4)
P()
P("结果：R² 从负数变成了 0.180。", bold=True, size=10.5)
P("也就是说——去掉「公司本身的底子」之后，「今年多申请专利」"
  "和「今年业绩变好」之间，确实有一点关系。", size=10, indent=0.4)
BOX("再用那个类比重说一遍", [
    "「做了多少题」不能预测「谁成绩好」——因为底子差异太大。",
    "",
    "但「同一个学生，这个月比上个月多做了 20 道题」，",
    "下个月成绩可能真的会好一点。",
])
KEY("固定效应 = 把个体自己的平均水平扣掉，只看它自己的波动。")

# 概念4
doc.add_heading("概念四：过拟合 —— 为什么复杂的模型反而更差？", level=2)
P("我们试了「随机森林」——一种会自动寻找复杂规律的模型。"
  "按理说它应该比简单的线性模型更强。", size=10)
P("但结果相反：随机森林的 R² 是 -0.157，线性模型是 -0.051。复杂模型输了。", size=10)
BOX("生活类比：背答案 vs 理解题目", [
    "学生 A：把 100 道练习题的标准答案全背下来。",
    "学生 B：理解了解题方法。",
    "",
    "考这 100 道原题：A 考 100 分，B 考 85 分。",
    "考新题：A 考 30 分，B 考 80 分。",
    "",
    "学生 A 就是「过拟合」——它把训练数据（连同里面的噪声）全背下来了，",
    "所以在新数据上表现很差。",
])
P("为什么会这样？", bold=True, size=10.5)
P("因为我们的数据只有 1,270 条，对随机森林这种复杂模型来说太少了。"
  "数据少的时候，模型很容易把「噪声」当成「规律」。", size=10, indent=0.4)
KEY("数据量小的时候，简单的方法往往比复杂的方法更好。")

# 概念5
doc.add_heading("概念五：数据可得性验证 —— 别等做完才发现缺材料", level=2)
P("今天我们踩的最大的坑，就是这个。", size=10)
BOX("生活类比：做蛋糕才发现超市不卖奶油", [
    "你满怀信心地计划做一个蛋糕，食谱上写着要「奶油」。",
    "你把面粉、鸡蛋、糖都买齐了，开始做——",
    "",
    "结果发现：这家超市根本不卖奶油。",
    "",
    "问题不在于你不会做蛋糕，而在于你事先没确认材料到底有没有。",
])
P("正确的做法：", bold=True, size=10.5)
BUL("拿到数据后，先做一张「变量清单」")
BUL("标出每个变量在哪些年份有数据、覆盖率是多少")
BUL("再决定用哪几个变量，而不是先选定再发现缺数据")
KEY("先验证数据的覆盖范围，再决定用它。")

doc.add_page_break()

# ================= 第四部分 =================
doc.add_heading("第四部分　今天的收获", level=1)

doc.add_heading("4.1　技能层面（可以迁移到别的项目）", level=2)
TABLE(["技能", "具体做了什么"], [
    ["批量处理大量文件", "用 Python 一次性读完 152 个 Excel（总计约 1GB），聚合成一张表"],
    ["数据质量校验", "用权威来源（官方股票代码表）逐个核对自己提取的数据"],
    ["异常排查", "看到「249 个观测」这种明显不合理的数字，能一轮轮往下查，最终定位到具体变量"],
    ["数据合并", "按「公司 + 年份」把两张表接起来"],
    ["机器学习基础流程", "划分训练/测试集、跑模型、算 R²、看特征重要性"],
    ["工具链搭建", "装 Python 包、装 Git、注册 API、管理密钥"],
], widths=[4.5, 11.5])

doc.add_heading("4.2　知识层面（今天真的搞懂了 5 个概念）", level=2)
BUL("R² 可以是负数，而且负数是正常现象、有意义的结论")
BUL("信息泄漏是什么，为什么面板数据要按「公司」分组划分")
BUL("固定效应（去均值）是什么，它解决了什么问题")
BUL("过拟合是什么，为什么小数据要用简单模型")
BUL("数据可得性必须提前验证")

doc.add_heading("4.3　方法层面（研究是怎么做的）", level=2)
BUL("拿到一个模糊的大任务，怎么拆成可以动手的小步骤")
BUL("结果不合理时，先怀疑数据，再怀疑代码")
BUL("每一个决策都记下来（今天的决策记录写到了 D18），汇报时才讲得清楚")
BUL("诚实地报告坏结果——负的 R² 比编一个漂亮数字有价值得多")

doc.add_heading("4.4　今天的数字成绩单", level=2)
TABLE(["项目", "结果"], [
    ["专利数据", "152 家公司 / 11.7 万条专利 / 217 个字段"],
    ["发现并修正的数据问题", "3 处（代码错误、文件内容错位、变量缺失）"],
    ["企业财务数据", "144 家公司 × 86 个变量 / 2015–2025"],
    ["主数据集", "1,270 个观测 / 143 家公司 / 11 个年份"],
    ["（i）基准建模", "完成，线性 vs 非线性 × 三种设定"],
    ["（ii）准备", "四个维度已定，prompt v1 已写"],
    ["文档产出", "决策记录（D1–D18）、17 页说明书、日志"],
], widths=[5.0, 11.0])

doc.add_page_break()

# ================= 第五部分 =================
doc.add_heading("第五部分　明天要做什么", level=1)

doc.add_heading("5.1　明天的三个任务", level=2)
TABLE(["#", "任务", "预计时间"], [
    ["1", "重建智谱 API Key（这次先复制再关窗口），填进 config.py", "10 分钟"],
    ["2", "写脚本调 API 给专利打分，先测 20 条", "1 小时"],
    ["3", "测通后批量跑（每个公司—年份抽 10 条，约 12,700 次调用）", "1 小时（挂着跑）"],
], widths=[1.0, 12.0, 3.0])

doc.add_heading("5.2　为什么要做这四个维度", level=2)
P("（ii）要回答的问题是：「让大模型读专利文本打的分，"
  "能不能提供一些『数字特征捕捉不到』的新信息？」", size=10)
P()
P("所以选维度的时候，要挑那些「和数字特征重叠最小」的：", size=10)
TABLE(["维度", "数字特征能捕捉吗", "决定"], [
    ["技术新颖性", "部分（引用次数）", "选用"],
    ["科学基础强度", "不能", "选用（最新）"],
    ["跨领域整合度", "部分（IPC 领域数）", "选用"],
    ["商业化距离", "不能", "选用（最新）"],
    ["权利要求广度", "能（权利要求数量）", "放弃（重叠严重）"],
    ["合作网络属性", "部分（发明人数量）", "放弃"],
    ["技术生命周期阶段", "部分（专利年龄）", "放弃"],
    ["技术通用性", "不能", "备选"],
], widths=[4.0, 6.5, 5.5])

doc.add_heading("5.3　汇报时你要能回答的问题（今天这部分）", level=2)
TABLE(["问题", "你要怎么答"], [
    ["你的数据里有多少观测？", "1,270 个公司—年份观测，143 家公司，2015–2025 年。"],
    ["为什么 R² 是负的？", "负 R² 说明模型比直接猜平均值还差。因为企业财务表现主要由公司自身的稳定特征决定，当年专利数量解释不了。"],
    ["你怎么划分训练测试集？", "按公司分组划分，不是随机划分。因为同一家公司有 11 年数据，随机划分会造成信息泄漏、R² 虚高。"],
    ["为什么复杂模型反而更差？", "过拟合。数据只有 1,270 条，随机森林把训练数据背下来了，在新数据上反而更差。"],
    ["你怎么处理数据质量问题？", "用官方代码表逐条校验；逐家搜索公司名核对文件内容；先检查变量覆盖率再选变量。"],
], widths=[4.5, 11.5])

P()
RICH([("截止时间：2026 年 10 月 15 日。", True, 11, RGBColor(0xC0, 0x00, 0x00))])

doc.save(OUT)
print("已保存:", OUT)
