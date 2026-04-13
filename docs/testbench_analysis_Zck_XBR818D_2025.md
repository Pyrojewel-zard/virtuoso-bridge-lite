# Zck_XBR818D_2025 Testbench 全面分析

## 库信息

| 项目 | 值 |
|------|-----|
| **库名** | Zck_XBR818D_2025 |
| **路径** | /home/project/SMIC110MMRF/Pyrojewel/Zck_XBR818D_2025 |
| **总 cells** | 1326 |
| **Testbench 数量** | 11 (含 maestro view) |

---

## Testbench 汇总表

| # | Testbench | 分析类型 | 变量数 | 输出数 | 用途 |
|---|-----------|----------|--------|--------|------|
| 1 | LINE_IND_test | sp | 1 | 1 | 电感测试 |
| 2 | LNA_DIFF3_FINAL_LAYOUT_NPORT_WIPAD_EXMCT_SPEF_ZCK_V2 | - | 0 | 0 | LNA 布局 (空配置) |
| 3 | LNA_DIFF3_FINAL_LAYOUT_NPORT_WIPAD_EXMCT_SPEF_ZCK_V3 | - | 0 | 0 | LNA 布局 (空配置) |
| 4 | LNA_Two_Stage_v1 | sp | 9 | 4 | 两级 LNA 设计 |
| 5 | TEST_LNA_DIFF3_FINAL_LAYOUT | sp, dc | 16 | 8 | LNA 最终布局测试 |
| 6 | TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2 | dc, hb, hbsp, hbxf | 26 | 7 | LNA+Mixer 接收链 |
| 7 | TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL | dc, hb, hbsp, hbnoise | 50 | 35 | 完整收发机 (TX+RX) |
| 8 | TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL_HZM_XBR818C_2025 | dc, sp | 41 | 32 | 收发机 S 参数 |
| 9 | TIA_CHOPPER_2024_Testbench | ac, pss, pac | 19 | 7 | 斩波 TIA 测试 |
| 10 | TIA_CHOPPER_2024_Testbench_Compare | dc, pss, pnoise | 19 | 8 | TIA 噪声对比 |
| 11 | test | dc | 1 | 0 | 简单测试 |

---

## 详细分析

### 1. LINE_IND_test - 电感测试

**分析类型**: SP (S 参数)

**设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| Cap1 | 100f:(1p-100f)/20:1p | 电容扫描 |

**输出**:
- 电感值: `imag(1/ypm('sp 1 1))/2/pi/xval(ypm('sp 1 1))`

---

### 2 & 3. LNA_DIFF3_FINAL_LAYOUT_NPORT_WIPAD_EXMCT_SPEF_ZCK_V2/V3

**状态**: 空配置 (无分析、无变量、无输出)

**说明**: 这两个可能是备份或模板，需要配置后才能使用。

---

### 4. LNA_Two_Stage_v1 - 两级 LNA 设计

**分析类型**: SP (S 参数 + 噪声)

**设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| Ld | 1.2n | 漏极电感 |
| Lg | 800p | 栅极电感 |
| Ls | 178p | 源极电感 |
| VDD | 1.15 | 电源电压 |
| Vg | 0.7 | 栅极偏置 |
| M | 30 | 指数 |
| C1 | 200f | 输入电容 |
| C2 | 170f | 级间电容 |
| Rd | 600 | 负载电阻 |

**输出**:
| 输出 | 表达式 | 说明 |
|------|--------|------|
| NFmin | db10(Fmin) | 最小噪声系数 |
| Gmax | db10(gmax(...)) | 最大增益 |
| Gmin | gmin(...) | 最小增益 |
| S22 | spm('sp 2 2) | 输出匹配 |

---

### 5. TEST_LNA_DIFF3_FINAL_LAYOUT - LNA 最终布局测试

**分析类型**: SP + DC

**设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| prf | -80 | RF 功率 (dBm) |
| ENLNA | 3.3 | LNA 使能 |
| ENNOTCH | 0 | Notch 关闭 |
| ENRF | 3.3 | RF 使能 |
| VDD3P3 | 3.3 | 3.3V 电源 |
| SWN1 | 1.2 | Notch 开关 1 |
| fif | 100 | 中频 (MHz) |

**输出**:
| 输出 | 说明 |
|------|------|
| S21 dB20 | 增益 |
| S11 dB20 | 输入匹配 |
| Kf | K 稳定性因子 |
| NF dB10 | 噪声系数 |

---

### 6. TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2 - LNA+Mixer 接收链 ⭐

**分析类型**: DC + HB + HBSP + HBXF (谐波平衡)

**设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| **flo** | 10.5136G | 本振频率 |
| **fif** | 100 | 中频 (MHz) |
| **prf** | -70 | RF 功率 (dBm) |
| **vlo** | 0.23 | LO 振幅 |
| ENLNA | 3.3 | LNA 使能 |
| ENNOTCH | 1.2 | Notch 使能 |
| ENRF | 3.3 | RF 使能 |
| SWDC1-3 | 3.3/3.3/0 | 直流开关 |
| SWN1-4 | 1.2/0/0/0 | Notch 开关 |
| rtia | 1k | TIA 电阻 |
| C1 | 224f | 电容 |
| ZinTia | 4.52 | TIA 输入阻抗 |
| RFC | 450p | RFC 电感 |

**输出**:
| 输出 | 说明 |
|------|------|
| LNAOUT 增益 | LNA 级增益 (dB) |
| RFOUT 增益 | 整体增益 (dB) |
| MIX_real/imag | Mixer 转换阻抗 |
| S21 | S 参数增益 |

---

### 7. TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL - 完整收发机 ⭐⭐

**分析类型**: DC + HB + HBSP + HBNoise

**这是最完整的系统级 testbench！**

**关键设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| **temperature** | -40, 27, 85, 125 | 温度扫描 (4 点) |
| ENRF | 3.3 | RF 使能 |
| MIX_SWDC1-3 | 1/1/0 | Mixer 开关 |
| VCO_CNT1-5 | 0/0/0/0/1 | VCO 控制字 |
| (共 50 个变量) | | |

**关键输出** (35 个):
| 输出 | 说明 |
|------|------|
| (hb)Idc | 电源电流 |
| (hb)Efficiency | 效率 |
| (hb)f0 | 输出频率 |
| (hb)Leakage | 泄漏 |
| (hb)LOdiffpk | LO 差分幅度 |

---

### 8. TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL_HZM_XBR818C_2025

**分析类型**: DC + SP

**设计变量**: 41 个 (包含温度扫描和 VCO 控制字扫描)

**VCO 控制字扫描**:
```
VCO_CNT1-5 = 0,1 (各 2 点)
```

---

### 9. TIA_CHOPPER_2024_Testbench - 斩波 TIA 测试

**分析类型**: AC + PSS + PAC

**设计变量**:
| 变量 | 值 | 说明 |
|------|-----|------|
| ileak | 0 | 漏电流 |
| fclk | 500K | 斩波频率 |
| vofs | 0 | 失调电压 |
| rtia | 1k | TIA 电阻 |
| clk_en | 1 | 时钟使能 |
| FLT_CAP | 100f:(2.2u-220n)/10:2.2u,220n | 滤波电容扫描 (2 点) |
| Vref | 1.2 | 参考电压 |

**输出**:
| 输出 | 说明 |
|------|------|
| AC Gain | AC 增益 |
| TIA Gain@1Hz | 1Hz 处增益 |
| TIA Self_noise@1Hz | 1Hz 处噪声 |
| TIA_Zin_real | 输入阻抗实部 |

**扫描组合**: 2

---

### 10. TIA_CHOPPER_2024_Testbench_Compare

**分析类型**: DC + PSS + PNoise

**与 #9 的区别**: 关闭斩波 (clk_en=0)，用于对比噪声性能

---

### 11. test

**简单测试电路**: 仅 DC 分析

---

## 系统架构推断

根据 testbench 配置，推断接收机系统架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    完整收发机系统                            │
│              TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  Balun  │───▶│   LNA   │───▶│  Mixer  │───▶│   TIA   │  │
│  │ (TFM)   │    │(DIFF3)  │    │(Gilbert)│    │(Chopper)│  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │       │
│       │         ┌────┴────┐         │              │       │
│       │         │  Notch  │         │              │       │
│       │         │ Filter  │         │              │       │
│       │         └─────────┘         │              │       │
│       │                             │              │       │
│       ▼                             ▼              ▼       │
│   RF_IN ◀────────────────────────▶ LO ◀────────▶ IF_OUT   │
│  (10.5GHz)                    (10.5GHz)        (100MHz)    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Bias & Control                     │   │
│  │  - RFBIAS_TOP (电流基准)                              │   │
│  │  - LDO (3.3V, 2.5V, 1.2V)                            │   │
│  │  - VCO (频率合成)                                     │   │
│  │  - DAC (增益控制)                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 关键参数汇总

| 参数 | 值 | 说明 |
|------|-----|------|
| RF 频率 | ~10.5 GHz | 工作频段 |
| LO 频率 | 10.5136 GHz | 本振 |
| IF 频率 | 100 MHz | 中频 |
| 电源 | 3.3V / 2.5V / 1.2V | 多电源域 |
| 温度范围 | -40°C ~ 125°C | 工业级 |

---

## 分析日期

2026-04-08