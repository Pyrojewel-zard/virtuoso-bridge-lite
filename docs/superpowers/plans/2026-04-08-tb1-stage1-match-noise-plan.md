# TB1 Stage1 Match Noise 优化系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 LNA 首级自动化仿真优化系统，通过分阶段参数扫描和 Pareto 前沿分析找到最优噪声匹配参数。

**Architecture:** Virtuoso 参数化 testbench + ADE Maestro 仿真 + Python 分阶段控制 + Pareto 分析 + Plotly 可视化。

**Tech Stack:** Virtuoso/SKILL/ADE Maestro, Python (pandas, numpy, plotly), VirtuosoClient API。

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `RFcircuit/LNA/TB1_stage1_match_noise.il` | Virtuoso testbench 创建 SKILL 脚本 |
| `RFcircuit/LNA/optimize_stage1.py` | 分阶段优化控制器主程序 |
| `RFcircuit/LNA/pareto_analyzer.py` | Pareto 前沿计算模块 |
| `RFcircuit/LNA/visualizer.py` | Plotly 可视化生成模块 |
| `RFcircuit/LNA/result_store.py` | 结果持久化（JSON/CSV） |
| `RFcircuit/LNA/results/` | 结果存储目录结构 |
| `docs/superpowers/specs/2026-04-08-tb1-stage1-match-noise-design.md` | 设计文档（已完成） |

---

## Task 1: Virtuoso Testbench 创建

**Files:**
- Create: `RFcircuit/LNA/TB1_stage1_match_noise.il`
- Create: Virtuoso cellview `Zck_XBR818D_2026/TB1_stage1_match_noise/schematic`

**依赖:** @virtuoso skill

- [ ] **Step 1: 检查 stage1_match_noise symbol 是否存在**

使用 VirtuosoClient 执行 ddGetObj 确认 symbol view 存在。

- [ ] **Step 2: 创建 TB1 testbench schematic cellview**

在 Zck_XBR818D_2026 library 下创建 TB1_stage1_match_noise cellview，view 类型为 schematic。

- [ ] **Step 3: 添加 stage1_match_noise symbol instance**

将 stage1_match_noise symbol 作为 instance 放入 testbench。

- [ ] **Step 4: 添加 PORT0 输入端口**

配置为 input 类型，50Ω 源阻抗，用于 S 参数和噪声分析。

- [ ] **Step 5: 添加 PORT1 输出端口**

配置为 output 类型，用于提取 Zout1(f)。

- [ ] **Step 6: 添加电源和偏置端口**

添加 VDD (1.2V)、GND、SUB、VG1_bias 端口连接。

- [ ] **Step 7: 设置 Design Variables**

创建参数化变量：W1, W2, Ls_val, Lg_val, Lp_val, Cin_val, VG1_bias，设置默认值。

- [ ] **Step 8: 连接所有 net**

确保 PORT0 → stage1 input、stage1 output → PORT1、电源/偏置正确连接。

- [ ] **Step 9: Check and Save schematic**

执行 check and save，确保无错误。

- [ ] **Step 10: Commit**

提交 TB1_stage1_match_noise.il 脚本和 Virtuoso cellview 创建记录。

---

## Task 2: ADE Maestro Test Template 配置

**Files:**
- Modify: Virtuoso ADE Maestro session for TB1_stage1_match_noise

**依赖:** @virtuoso skill (ADE mae* API)

- [ ] **Step 1: 创建 ADE Maestro session**

使用 maeOpenSetup 为 TB1_stage1_match_noise 创建 maestro view。

- [ ] **Step 2: 添加 dcOp analysis**

配置直流工作点分析，用于提取 M1/M2 工作点参数。

- [ ] **Step 3: 添加 sp analysis**

配置 S 参数仿真：start=1G, stop=20G, dec=100。

- [ ] **Step 4: 添加 noise analysis**

配置噪声分析，配合 sp 获取 NF、NFmin、Γopt。

- [ ] **Step 5: 添加 Outputs expressions**

添加 S11_dB、S21_dB、NF_dB、K_factor、Zout1_re/im 等输出表达式。

- [ ] **Step 6: 设置通带指标 outputs**

添加 S11_band_max、S21_band_avg、NF_band_avg（针对 9-11GHz）。

- [ ] **Step 7: Save ADE setup**

保存 maestro view 配置。

- [ ] **Step 8: Commit**

记录 ADE template 配置完成。

---

## Task 3: Python ResultStore 模块开发

**Files:**
- Create: `RFcircuit/LNA/result_store.py`
- Test: 单元测试验证 JSON/CSV 写入

- [ ] **Step 1: 设计 ResultStore 类接口**

定义 save_sweep_results、save_pareto_front、save_selected_params、load_params 方法签名。

- [ ] **Step 2: 实现 JSON 参数保存功能**

将选中参数和指标写入 JSON 文件，包含 phase、timestamp 字段。

- [ ] **Step 3: 实现 CSV sweep 结果保存功能**

将 sweep 结果写入 CSV，列包含参数名和指标名。

- [ ] **Step 4: 实现参数加载功能**

从 JSON 文件加载上一阶段选中的参数。

- [ ] **Step 5: 编写单元测试**

测试 JSON/CSV 写入和读取的正确性。

- [ ] **Step 6: 运行测试验证**

执行 pytest 确保测试通过。

- [ ] **Step 7: Commit**

提交 result_store.py 及测试文件。

---

## Task 4: Python ParetoAnalyzer 模块开发

**Files:**
- Create: `RFcircuit/LNA/pareto_analyzer.py`
- Test: 单元测试验证 Pareto 前沿计算

- [ ] **Step 1: 设计 ParetoAnalyzer 类接口**

定义 compute_pareto、recommend_best 方法签名，输入为 pandas DataFrame。

- [ ] **Step 2: 实现目标归一化逻辑**

将 NF、S11、S21、K 归一化到 [0,1] 区间，处理最大化/最小化方向。

- [ ] **Step 3: 实现非支配排序算法**

实现快速非支配排序，找出 rank=0 的 Pareto 前沿。

- [ ] **Step 4: 实现加权推荐逻辑**

根据默认权重（NF=0.4, S11=0.3, S21=0.2, K=0.1）计算加权得分并推荐最优。

- [ ] **Step 5: 编写单元测试**

使用已知测试数据验证 Pareto 前沿计算正确性。

- [ ] **Step 6: 运行测试验证**

执行 pytest 确保测试通过。

- [ ] **Step 7: Commit**

提交 pareto_analyzer.py 及测试文件。

---

## Task 5: Python Visualizer 模块开发

**Files:**
- Create: `RFcircuit/LNA/visualizer.py`
- Test: 验证 HTML 图表生成

- [ ] **Step 1: 设计 Visualizer 类接口**

定义 plot_pareto_2d、plot_smith_s11、plot_s21_band、plot_heatmap 方法签名。

- [ ] **Step 2: 实现 Pareto 2D scatter plot**

使用 Plotly 生成交互式 Pareto 前沿散点图，hover 显示参数值。

- [ ] **Step 3: 实现 Smith Chart plot**

生成 S11 轨迹和 Γopt 的 Smith 图对比。

- [ ] **Step 4: 实现 S21 vs freq 曲线族 plot**

生成不同参数下的 S21 频响曲线对比图。

- [ ] **Step 5: 实现 Heatmap plot**

生成 W1-Ls 平面上的 NF/S11 分布热图。

- [ ] **Step 6: 实现 HTML 保存功能**

将图表保存为 HTML 文件供用户交互查看。

- [ ] **Step 7: 编写单元测试**

验证生成的 HTML 文件包含正确的数据点。

- [ ] **Step 8: 运行测试验证**

执行 pytest 确保测试通过。

- [ ] **Step 9: Commit**

提交 visualizer.py 及测试文件。

---

## Task 6: Python StageOptimizer 核心模块开发

**Files:**
- Create: `RFcircuit/LNA/optimize_stage1.py`
- Create: `RFcircuit/LNA/results/` 目录结构

**依赖:** VirtuosoClient API, @virtuoso skill (ADE mae* API)

- [ ] **Step 1: 设计 StageOptimizer 类接口**

定义 run_phase1、run_phase2、run_phase3、user_select 方法签名。

- [ ] **Step 2: 实现 ADE 变量设置逻辑**

通过 maeSetVar 设置 Design Variables 参数值。

- [ ] **Step 3: 实现 ADE sweep 配置逻辑**

通过 mae 设置 sweep 变量和范围。

- [ ] **Step 4: 实现 ADE 仿真运行逻辑**

调用 maeRunSimulation 和 maeWaitUntilDone 执行仿真。

- [ ] **Step 5: 实现 ADE 结果提取逻辑**

通过 maeGetOutput 提取仿真结果数据。

- [ ] **Step 6: 实现 Phase1 逻辑（W1/Ls/VG1_bias sweep）**

组合 sweep 变量设置、仿真执行、结果收集、Pareto 计算流程。

- [ ] **Step 7: 实现 Phase2 逻辑（Lg sweep）**

固定 Phase1 参数，扫描 Lg，分析 S11 轨迹。

- [ ] **Step 8: 实现 Phase3 逻辑（Lp sweep）**

固定 Phase1+2 参数，扫描 Lp，分析通带平坦性。

- [ ] **Step 9: 实现用户选择交互逻辑**

展示 Pareto 前沿，接收用户输入选择最优参数。

- [ ] **Step 10: 实现 Zout1 提取逻辑**

在最终参数下提取 Zout1(f) 数据供 TB3 使用。

- [ ] **Step 11: 创建 results 目录结构**

创建 phase1/phase2/phase3/final 子目录。

- [ ] **Step 12: Commit**

提交 optimize_stage1.py。

---

## Task 7: 阶段 1 仿真执行与验证

**Files:**
- Create: `RFcircuit/LNA/results/phase1/*`

- [ ] **Step 1: 运行 optimize_stage1.py Phase1**

执行阶段 1 sweep（W1/Ls/VG1_bias）。

- [ ] **Step 2: 检查 sweep_results.csv**

确认数据行数与 sweep 组合数一致，列包含所有参数和指标。

- [ ] **Step 3: 检查 pareto_front.csv**

确认 Pareto 前沿候选点合理（非空、指标范围正确）。

- [ ] **Step 4: 检查 pareto_plot.html**

在浏览器中打开图表，确认交互功能正常。

- [ ] **Step 5: 用户选择最优参数**

从 Pareto 前沿选择 W1/Ls/VG1_bias 组合，保存到 selected_params.json。

- [ ] **Step 6: Commit**

提交 phase1 结果文件。

---

## Task 8: 阶段 2 仿真执行与验证

**Files:**
- Create: `RFcircuit/LNA/results/phase2/*`

- [ ] **Step 1: 加载 Phase1 参数**

从 selected_params.json 加载 Phase1 最优参数。

- [ ] **Step 2: 运行 optimize_stage1.py Phase2**

执行阶段 2 sweep（Lg）。

- [ ] **Step 3: 检查 sweep_results.csv**

确认数据正确，Lg 列存在。

- [ ] **Step 4: 检查 smith_plot.html**

确认 Smith 图中 S11 轨迹和 Γopt 显示正确。

- [ ] **Step 5: 用户选择最优 Lg**

选择 S11 轨迹最靠近 Γopt 的 Lg 值，保存到 selected_params.json。

- [ ] **Step 6: Commit**

提交 phase2 结果文件。

---

## Task 9: 阶段 3 仿真执行与验证

**Files:**
- Create: `RFcircuit/LNA/results/phase3/*`
- Create: `RFcircuit/LNA/results/final/*`

- [ ] **Step 1: 加载 Phase1+2 参数**

从 selected_params.json 加载累积最优参数。

- [ ] **Step 2: 运行 optimize_stage1.py Phase3**

执行阶段 3 sweep（Lp）。

- [ ] **Step 3: 检查 sweep_results.csv**

确认数据正确，Lp 列存在。

- [ ] **Step 4: 检查 s21_band_plot.html**

确认 9-11GHz 通带 S21 曲线族显示正确，可评估平坦性。

- [ ] **Step 5: 用户选择最优 Lp**

选择通带最平坦的 Lp 值，保存到 selected_params.json。

- [ ] **Step 6: 生成 stage1_optimized.json**

汇总最终参数和指标，保存到 final 目录。

- [ ] **Step 7: 提取 Zout1_vs_freq.csv**

运行仿真提取 Zout1(f) 数据，保存供 TB3 使用。

- [ ] **Step 8: Commit**

提交 phase3 和 final 结果文件。

---

## Task 10: 最终验证与文档更新

**Files:**
- Update: `docs/superpowers/specs/2026-04-08-tb1-stage1-match-noise-design.md`

- [ ] **Step 1: 验证最终参数指标**

确认 stage1_optimized.json 中各指标达到预期目标范围。

- [ ] **Step 2: 验证 Zout1 数据**

确认 Zout1_vs_freq.csv 数据格式正确，频率范围覆盖通带。

- [ ] **Step 3: 更新设计文档**

记录实际优化结果和最终参数值。

- [ ] **Step 4: 准备 TB3 输入**

标记 Zout1 数据已准备好，可用于 TB3 级间匹配。

- [ ] **Step 5: Commit**

提交所有最终更新。

---

## 关键依赖关系

```
Task 1 (Testbench) ──► Task 2 (ADE Template)
                      │
                      ▼
Task 3-6 (Python Modules) ──► Task 7 (Phase1)
                               │
                               ▼
                            Task 8 (Phase2)
                               │
                               ▼
                            Task 9 (Phase3)
                               │
                               ▼
                            Task 10 (Final)
```

---

## 测试策略

| 模块 | 测试方法 |
|------|----------|
| ResultStore | 单元测试验证 JSON/CSV 读写 |
| ParetoAnalyzer | 单元测试验证非支配排序 |
| Visualizer | 验证 HTML 文件生成和数据嵌入 |
| StageOptimizer | 集成测试验证 ADE 交互流程 |

---

## 回滚策略

若某阶段仿真失败或结果异常：

1. 检查 Virtuoso 连接状态（virtuoso-bridge status）
2. 检查 ADE session 是否正确保存
3. 检查 design variables 命名是否与 schematic 一致
4. 回退到上一阶段参数，重新调试 sweep 范围