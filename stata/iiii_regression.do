* ==============================================================================
* （iiii）计量回归：跨领域整合度 x 对企业融资约束 y 的影响
* 项目：20261009 智能大数据 fxy 笔试
* 日期：2026-10-11
* ------------------------------------------------------------------------------
* 模型设定：
*   y_it = theta * x_it + controls_it + mu_i + lambda_t + delta_(ind,t) + gamma_(reg,t) + e_it
*   其中控制：企业固定效应 + 年份固定效应 + 行业×年份固定效应 + 地区×年份固定效应
*   标准误：企业层面聚类稳健标准误
*   x = 跨领域整合度（LLM 语义特征）
*   y = 资产负债率（主）/ 总资产净利润率 / 主营业务收入增长率
* ==============================================================================

clear all
set more off
version 14

* ------------------------------------------------------------------------------
* 0. 路径设置（如路径不同，只需改这一行）
* ------------------------------------------------------------------------------
global root "C:/Users/YYYi3/Desktop/笔试准备/patent-innovation"
cd "$root/stata"

* ------------------------------------------------------------------------------
* 1. 开启日志（提交要求：do 文件与日志）
* ------------------------------------------------------------------------------
capture log close
log using "iiii_regression.log", replace text

display "=============================================================="
display "  （iiii）计量回归  开始时间：$S_DATE $S_TIME"
display "=============================================================="

* ------------------------------------------------------------------------------
* 2. 安装依赖包（首次运行需取消注释；装好后可注释掉）
*    说明：reghdfe 用于高维固定效应吸收，等价于 areg 但支持多重固定效应
* ------------------------------------------------------------------------------
* ssc install ftools, replace
* ssc install reghdfe, replace
* ssc install estout, replace

capture which reghdfe
if _rc {
    display as error "未安装 reghdfe，请先运行：ssc install ftools, replace"
    display as error "                        ssc install reghdfe, replace"
    exit
}

* ------------------------------------------------------------------------------
* 3. 读入数据
* ------------------------------------------------------------------------------
use "main_dataset.dta", clear

* 行业×年份、地区×年份 需要数值型编码才能被 absorb()
encode ind_year, gen(indyear_id)
encode reg_year, gen(regyear_id)
label var indyear_id "行业×年份"
label var regyear_id "地区×年份"

* 变量组
global ctrl "ln_patent avg_claims avg_cites avg_inventors avg_fcwords avg_family ///
             avg_value avg_tech_adv avg_tech_stab avg_protect avg_pages ipc_fields"

xtset firm year

display ""
display "样本规模："
count
display "公司数："
quietly levelsof firm, local(f)
display "  `: word count `f''"
display "年份范围："
summarize year

* ------------------------------------------------------------------------------
* 4. 描述性统计（对应报告的表 1）
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  表 1  描述性统计"
display "=============================================================="
summarize x_integration x_novelty x_science x_distance ///
          y_lev y_roa y_growth ln_patent avg_cites avg_claims, detail

estpost summarize x_integration x_novelty x_science x_distance ///
                 y_lev y_roa y_growth ln_patent avg_cites avg_claims
esttab using "table1_descriptive.rtf", replace ///
    cells("count mean sd min p50 max") ///
    noobs nonumber nomtitle ///
    title("表 1  描述性统计")

* ------------------------------------------------------------------------------
* 5. 主回归（对应报告的表 2）
*    reghdfe：吸收四类固定效应；vce(cluster firm)：企业层面聚类稳健标准误
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  表 2  主回归：跨领域整合度对三类企业结果的影响"
display "=============================================================="

* (1) 资产负债率（融资约束）
reghdfe y_lev x_integration $ctrl, ///
    absorb(firm year indyear_id regyear_id) vce(cluster firm)
estimates store m1_lev

* (2) 总资产净利润率（盈利能力）
reghdfe y_roa x_integration $ctrl, ///
    absorb(firm year indyear_id regyear_id) vce(cluster firm)
estimates store m2_roa

* (3) 主营业务收入增长率（成长性）
reghdfe y_growth x_integration $ctrl, ///
    absorb(firm year indyear_id regyear_id) vce(cluster firm)
estimates store m3_growth

* 输出表格（只显示核心解释变量，控制变量系数见附表）
esttab m1_lev m2_roa m3_growth using "table2_main.rtf", replace ///
    keep(x_integration) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    b(%9.4f) se(%9.4f) ///
    mtitles("资产负债率" "总资产净利润率" "营收增长率") ///
    stats(N r2_within, labels("观测数" "组内R2")) ///
    title("表 2  跨领域整合度与企业结果：四类固定效应回归") ///
    addnotes("注：括号内为企业层面聚类稳健标准误。所有回归均控制企业、年份、行业×年份、地区×年份固定效应及12个数量类专利特征。")

* 完整结果（含全部控制变量）
esttab m1_lev m2_roa m3_growth using "table2_main_full.rtf", replace ///
    star(* 0.10 ** 0.05 *** 0.01) b(%9.4f) se(%9.4f) ///
    mtitles("资产负债率" "总资产净利润率" "营收增长率") ///
    stats(N r2_within, labels("观测数" "组内R2")) ///
    title("附表 2  完整回归结果")

* ------------------------------------------------------------------------------
* 6. 稳健性检验 1：逐个语义维度
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  表 3  逐个语义维度的回归（看哪个维度最重要，对应题目 iii）"
display "=============================================================="

foreach v in x_novelty x_science x_integration x_distance {
    display ""
    display "-------- 解释变量：`v' --------"
    reghdfe y_lev `v' $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster firm)
}
* 汇总输出
foreach v in x_novelty x_science x_integration x_distance {
    quietly reghdfe y_lev `v' $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster firm)
    estimates store lev_`v'
}
esttab lev_x_novelty lev_x_science lev_x_integration lev_x_distance ///
    using "table3_dimensions.rtf", replace ///
    keep(x_novelty x_science x_integration x_distance) ///
    star(* 0.10 ** 0.05 *** 0.01) b(%9.4f) se(%9.4f) ///
    mtitles("新颖性" "科学强度" "跨领域" "商业化距离") ///
    stats(N r2_within, labels("观测数" "组内R2")) ///
    title("表 3  四个语义维度对资产负债率的效应（逐个加入）")

* ------------------------------------------------------------------------------
* 7. 稳健性检验 2：滞后一期解释变量（缓解反向因果）
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  表 4  稳健性：滞后一期解释变量"
display "=============================================================="

bysort firm (year): gen x_integration_lag = x_integration[_n-1]

foreach y in y_lev y_roa y_growth {
    display ""
    display "-------- 被解释变量：`y'（滞后一期 x）--------"
    reghdfe `y' x_integration_lag $ctrl, ///
        absorb(firm year indyear_id regyear_id) vce(cluster firm)
    estimates store lag_`y'
}
esttab lag_y_lev lag_y_roa lag_y_growth using "table4_lag.rtf", replace ///
    keep(x_integration_lag) ///
    star(* 0.10 ** 0.05 *** 0.01) b(%9.4f) se(%9.4f) ///
    mtitles("资产负债率" "总资产净利润率" "营收增长率") ///
    stats(N r2_within, labels("观测数" "组内R2")) ///
    title("表 4  稳健性检验：滞后一期跨领域整合度")

* ------------------------------------------------------------------------------
* 8. 稳健性检验 3：更换聚类层级
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  表 5  稳健性：标准误聚类在不同层级"
display "=============================================================="
display "--- 企业层面聚类（基准）---"
reghdfe y_lev x_integration $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster firm)
estimates store cl_firm
display "--- 行业层面聚类 ---"
reghdfe y_lev x_integration $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster industry)
estimates store cl_ind
display "--- 地区层面聚类 ---"
reghdfe y_lev x_integration $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster region)
estimates store cl_reg
display "--- 企业与年份双向聚类 ---"
reghdfe y_lev x_integration $ctrl, absorb(firm year indyear_id regyear_id) vce(cluster firm year)
estimates store cl_two

esttab cl_firm cl_ind cl_reg cl_two using "table5_cluster.rtf", replace ///
    keep(x_integration) star(* 0.10 ** 0.05 *** 0.01) b(%9.4f) se(%9.4f) ///
    mtitles("聚类:企业" "聚类:行业" "聚类:地区" "聚类:企业+年份") ///
    stats(N, labels("观测数")) ///
    title("表 5  稳健性检验：不同聚类层级的标准误")

* ------------------------------------------------------------------------------
* 9. 内生性讨论与识别策略
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  第 9 部分  内生性讨论"
display "=============================================================="
display "潜在内生性来源："
display "  (1) 反向因果：融资约束低的企业可能有更多资源投入跨领域研发"
display "  (2) 遗漏变量：企业技术战略、管理层能力等同时影响两者"
display "  (3) 测量误差：LLM 语义评分存在测量误差"
display ""
display "本文的处理："
display "  (1) 控制企业固定效应，吸收所有不随时间变化的企业异质性"
display "  (2) 控制行业×年份、地区×年份固定效应，吸收行业与地区的时变冲击"
display "  (3) 使用滞后一期解释变量，缓解反向因果（见表 4）"
display "  (4) 更换聚类层级检验标准误稳健性（见表 5）"

* 尝试双重机器学习（需安装 ddml；未安装则跳过）
capture which ddml
if !_rc {
    display ""
    display "--- 双重机器学习（DML）---"
    * 注意：ddml 需要机器学习学习器，此处使用内置 regress 作为学习器
    ddml init partial, kfolds(5) reps(1)
    ddml E[y_lev:], learners(regress)
    ddml E[x_integration:], learners(regress)
    ddml crossfit
    ddml estimate, robust
}
else {
    display ""
    display "（未安装 ddml，跳过。如需：ssc install ddml, replace）"
}

* ------------------------------------------------------------------------------
* 10. 工具变量法（备选识别策略，若有合适工具变量）
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  第 10 部分  关于工具变量的说明"
display "=============================================================="
display "严格的因果识别需要外生工具变量。本文样本中缺乏可信的工具变量，"
display "因此以高维固定效应 + 滞后解释变量 + 多种稳健性检验作为识别策略，"
display "并如实说明这一局限。"

* ------------------------------------------------------------------------------
* 11. 收尾
* ------------------------------------------------------------------------------
display ""
display "=============================================================="
display "  回归完成  结束时间：$S_DATE $S_TIME"
display "=============================================================="

log close
translate "iiii_regression.log" "iiii_regression.txt", replace

* ==============================================================================
* 结束
* ==============================================================================
