---
name: TB1 Stage1 Match Noise 优化系统
description: LNA 第一级噪声匹配与输入匹配的分阶段自动化仿真优化设计
type: project
---

# TB1 Stage1 Match Noise 优化系统设计文档

## 目标

为 LNA 首级（stage1_match_noise）构建自动化仿真优化系统，通过分阶段参数扫描和 Pareto 前沿分析，找到噪声、匹配、增益、稳定性之间的最优权衡点。

---

## 目标频带

**9-11GHz**，中心频率约 10GHz。

---

## 系统架构

三层架构，Python 控制层 + Virtuoso 仿真层 + 结果分析层：

| 层 | 组件 | 职责 |
|----|------|------|
| **仿真层** | Virtuoso Testbench + ADE Maestro | 参数化 schematic、SP/Noise 仿真执行 |
| **控制层** | Python StageOptimizer | 分阶段调用 ADE、控制 sweep 变量、收集结果 |
| **分析层** | ParetoAnalyzer + Visualizer | 多目标 Pareto 前沿计算、交互式可视化 |

**数据流**：Python 设置参数 → ADE 执行仿真 → Python 收集结果 → Pareto 分析 → 用户选择最优 → 保存参数 → 下一阶段。

---

## Virtuoso Testbench 设计

### 电路结构

使用 stage1_match_noise symbol 作为 DUT，外接：

- PORT0：输入端口，50Ω 源阻抗，用于 S 参数和噪声分析
- PORT1：输出端口，用于提取 Zout1(f)，为后续级间匹配提供数据
- VDD：电源 1.2V
- GND/SUB：地和衬底
- VG1_bias：M1/M2 栅偏置（参数化）

### 参数化变量

| 变量 | 含义 | Sweep 范围 | 默认值 |
|------|------|------------|--------|
| W1 | M1 总宽 | 40u ~ 120u，步长 20u | 80u |
| W2 | M2 总宽 | 20u ~ 60u | 40u |
| Ls_val | Ls 电感值 | 40p ~ 120p | 80p |
| Lg_val | Lg 电感值 | 150p ~ 350p | 250p |
| Lp_val | Lp 电感值 | 200p ~ 500p | 350p |
| Cin_val | Cin 电容 | 100f ~ 150f | 120f |
| VG1_bias | M1 栅偏置电压 | 0.4V ~ 0.8V | 0.6V |

### ADE Analysis 配置

| Analysis | 参数设置 | 用途 |
|----------|----------|------|
| dcOp | 默认 | 提取 M1/M2 工作点 |
| sp | start=1G, stop=20G, dec=100 | S 参数仿真 |
| noise | 配合 sp | 噪声分析，提取 NF、NFmin、Γopt |

### ADE Outputs

**S 参数**：S11_dB、S21_dB、S22_dB、S12_dB

**噪声**：NF_dB、NFmin_dB、Gamma_opt

**稳定性**：K_factor、MU_factor

**输出阻抗**：Zout1_re、Zout1_im（供 TB3 使用）

**通带指标**（9-11GHz）：
- S11_band_max：通带内 S11 最大值
- S21_band_avg：通带内 S21 平均值
- NF_band_avg：通带内 NF 平均值

---

## 分阶段优化流程

### 阶段 1：噪声匹配核心

**扫描变量**：W1 × Ls_val × VG1_bias（如 5×5×5 = 125 次）

**固定参数**：Lg、Lp、Cin 用默认值

**目标**：Pareto(NF, S11, S21, K) 四目标优化

**输出**：Pareto 前沿候选列表 + 可视化图表

**用户决策**：从 Pareto 前沿选择最优 W1/Ls/VG1_bias 组合

**保存**：phase1/selected_params.json

### 阶段 2：输入匹配轨迹

**固定参数**：W1/Ls/VG1_bias（来自阶段1最优值）

**扫描变量**：Lg_val（5~7 点）

**目标**：Pareto(S11轨迹位置 vs Γopt, NF变化, S21变化)

**输出**：Smith 图 + Pareto 前沿

**用户决策**：选择 S11 轨迹最靠近 Γopt 的 Lg

**保存**：phase2/selected_params.json

### 阶段 3：宽带平坦性

**固定参数**：W1/Ls/VG1_bias/Lg（来自阶段1+2）

**扫描变量**：Lp_val（5~7 点）

**目标**：Pareto(通带平坦度, NF, 增益峰值)

**输出**：S21 vs freq 曲线族 + Pareto

**用户决策**：选择 9-11GHz 通带最平坦的 Lp

**保存**：final/stage1_optimized.json + Zout1_vs_freq.csv

---

## Pareto 分析逻辑

### 目标空间

- f1：NF（最小化）
- f2：|S11|（最小化）
- f3：S21（最大化）
- f4：K（最大化，稳定性）

### Pareto 定义

点 A 支配点 B，当 A 在所有目标上不劣于 B，且至少一个目标严格优于。

### 推荐策略

默认权重：NF=0.4、S11=0.3、S21=0.2、K=0.1（噪声优先，其次是匹配）。

用户可从 Pareto 前沿手动选择，系统提供加权推荐作为参考。

---

## 可视化输出

| 图表类型 | 内容 | 用途 |
|----------|------|------|
| Pareto 2D scatter | NF vs S11、S21 vs K 等 | 用户直观选择权衡点 |
| Smith Chart | S11 轨迹 vs Γopt | 验证噪声匹配轨迹 |
| S21 vs freq | 通带曲线族 | 验证 9-11GHz 平坦性 |
| Heatmap | W1-Ls 平面上的 NF/S11 分布 | 辅助参数空间理解 |

使用 Plotly 生成交互式 HTML，用户可在浏览器中 hover 查看参数值并选择。

---

## 文件组织结构

```
RFcircuit/LNA/
├── TB1_stage1_match_noise.il     # Virtuoso testbench 创建脚本
├── optimize_stage1.py            # Python 优化控制器
├── pareto_analyzer.py            # Pareto 分析模块
├── results/
│   ├── phase1/
│   │   ├── sweep_results.csv
│   │   ├── pareto_front.csv
│   │   ├── pareto_plot.html
│   │   └── selected_params.json
│   ├── phase2/
│   │   ├── sweep_results.csv
│   │   ├── smith_plot.html
│   │   └── selected_params.json
│   ├── phase3/
│   │   ├── sweep_results.csv
│   │   ├── s21_band_plot.html
│   │   └── selected_params.json
│   └── final/
│       ├── stage1_optimized.json
│       └── Zout1_vs_freq.csv     # 输出阻抗（供 TB3 使用）
```

---

## 关键交付物

| 交付物 | 描述 |
|--------|------|
| TB1_stage1_match_noise cellview | Virtuoso 参数化 testbench schematic |
| optimize_stage1.py | Python 分阶段优化控制器 |
| pareto_analyzer.py | Pareto 前沿计算模块 |
| stage1_optimized.json | 最终优化参数汇总 |
| Zout1_vs_freq.csv | 输出阻抗数据（供 TB3 级间匹配使用） |

---

## 与后续 Testbench 的关系

TB1 完成后，输出 Zout1(f) 数据，用于：

- TB3：两线圈 MCR 宽带网络的源端阻抗设置
- TB4：三线圈 MCR + notch 的源端阻抗设置
- TB6：整机验证时的参数回标

---

## Why

**Why 分阶段而非一次性全扫**：
- 全参数组合（如 5×5×5×5×5）sweep 量过大，仿真时间长
- 分阶段让用户参与决策，避免错过 Pareto 前沿上的关键权衡点
- 符合 LNA 设计的自然流程：先噪声匹配，再输入匹配，再宽带优化

**Why Pareto 而非单一目标**：
- LNA 设计是多目标权衡问题（噪声、匹配、增益、稳定性）
- 单一目标优化容易陷入局部最优，错过全局最优权衡
- Pareto 前沿让用户直观看到各指标间的权衡关系

---

## How to Apply

执行实现计划时：

1. 先创建 Virtuoso testbench，确保参数化变量和 ADE template 正确设置
2. Python 脚本开发顺序：StageOptimizer → ParetoAnalyzer → Visualizer → ResultStore
3. 阶段执行顺序：phase1 → phase2 → phase3，每阶段用户确认后才进入下一阶段
4. 最终输出 Zout1 数据，标记为 TB3 输入依赖