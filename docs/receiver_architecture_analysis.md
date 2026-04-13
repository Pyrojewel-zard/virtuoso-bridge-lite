# Zck_XBR818D_2025 接收机架构分析

## 顶层测试电路: TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2

### Maestro 仿真配置

| 项目 | 配置 |
|------|------|
| **测试名** | Zck_Copy_LYB_XBR818C_BALUN_LNA_EMX_TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2_1 |
| **分析类型** | dc, hb (谐波平衡), hbsp (HB S参数), hbxf (HB XF) |
| **仿真器** | spectre |

### 关键设计变量

| 变量 | 值 | 说明 |
|------|-----|------|
| **flo** | 10.5136G | 本振频率 |
| **fif** | 100 | 中频 |
| **prf** | -70 | RF 输入功率 (dBm) |
| **vlo** | 0.23 | LO 振幅 |
| **ENLNA** | 3.3 | LNA 使能电压 |
| **ENRF** | 3.3 | RF 使能电压 |
| **ENNOTCH** | 1.2 | Notch 滤波器使能 |
| **rtia** | 1k | TIA 电阻 |
| **RFC** | 450p | RFC 电感 |

### 输出表达式

| 输出 | 表达式 | 说明 |
|------|--------|------|
| MIX_real/imag | V(RFOUT) / I(IPRB2) | Mixer 转换阻抗 |
| LNAOUT 增益 | dB(V(LNAOUTP-N) / V(RFIN)) | LNA 级增益 |
| RFOUT 增益 | dB(V(RFOUTP-N) / V(RFIN)) | 整体增益 |
| S21 | db(spm('hbsp 2 1)) | S 参数增益 |

---

## 接收机架构层级

```
TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2
├── I2: LNA_DIFF3_FINAL_LAYOUT_NPORT_WIPAD_EXMCT_SPEF  [LNA 主模块]
│   ├── I90: TFM_LNA_V18_NPORT_WIPAD_EXSCT (变压器/巴伦)
│   ├── NM0-24: n12_ckt_rf / n33_ckt_rf (RF MOS 管)
│   ├── I41: dac8b_r2r_8bdac_818c (8-bit DAC)
│   ├── I13: ldo_rf (RF LDO)
│   ├── L1: TFM_CHOKE_8SHAPE (RFC 电感)
│   └── 多个 inv, mim电容, 电阻
│
├── I45: MIXER_FINAL_LAYOUT_SPEF  [混频器模块]
│   ├── NM0-1, NM7-8: n12_ckt_rf (开关管)
│   ├── NM2, NM13-14: n33_ckt_rf (跨导管)
│   ├── 多个 rhrpo_ckt_rf (多晶电阻)
│   ├── I12: pnsw (PMOS/NMOS 开关)
│   └── 多个 inv (LO 缓冲反相器)
│
├── I286: if_op_top_tia  [中频放大器 + TIA]
│   ├── I33: if_op_tia (TIA 核心运放)
│   ├── I35: if_op_clk_div (时钟分频)
│   ├── I34: ldo25_capless (无电容 LDO)
│   └── I29: if_op_test
│
├── I138: RFBIAS_TOP  [RF 偏置电路]
│   ├── I2: iref_a (电流基准)
│   ├── I35: lvr2 (低压稳压器)
│   └── C6: cap_For_LYB (滤波电容)
│
└── 外围元件
    ├── PORT0-6: 测试端口
    ├── L3-4, L5-7, L34-56: 匹配电感
    ├── V0-13: 偏置电压源
    └── C12-81: 耦合/去耦电容
```

---

## 各模块功能详解

### 1. LNA (LNA_DIFF3_FINAL_LAYOUT_NPORT_WIPAD_EXMCT_SPEF)

**功能**: 低噪声放大器，接收 RF 信号并放大

**关键器件**:
- **TFM_LNA_V18_NPORT_WIPAD_EXSCT**: 输入变压器/巴伦，实现单端转差分
- **n12_ckt_rf × 7**: 主放大管 (NM0, NM6, NM15, NM19-22)
- **n33_ckt_rf × 1**: 高压管 (NM24)
- **dac8b_r2r_8bdac**: 8-bit R-2R DAC，用于增益控制
- **ldo_rf**: 专用 LDO，提供稳定电源

**信号流**:
```
RFIN → TFM (巴伦) → NM 放大级 → TFM_CHOKE (负载) → LNAOUT
```

### 2. Mixer (MIXER_FINAL_LAYOUT_SPEF)

**功能**: 有源混频器，将 RF 信号下变频到 IF

**关键器件**:
- **n12_ckt_rf × 4**: 开关管 (NM0-1, NM7-8)
- **n33_ckt_rf × 3**: 跨导管 (NM2, NM13-14)
- **rhrpo_ckt_rf × 10**: 负载电阻
- **inv × 6**: LO 缓冲反相器

**结构**: Gilbert 单元结构
```
LNAOUT → 跨导管 (NM2, NM13-14) → 开关管 (NM0-1, NM7-8) → RFOUT
                                           ↑
                                          LO
```

### 3. TIA + IF Amp (if_op_top_tia)

**功能**: 跨阻放大器，将 Mixer 输出电流转换为电压

**关键器件**:
- **if_op_tia**: TIA 核心运放 (54 个器件)
- **if_op_clk_div**: 时钟分频器 (31 个器件)
- **ldo25_capless**: 无电容 LDO (46 个器件)

**配置参数**:
- rtia = 1k (跨阻增益)
- ZinTia = 4.52 (输入阻抗匹配)

### 4. RF Bias (RFBIAS_TOP)

**功能**: 为 RF 电路提供基准电流和偏置

**关键器件**:
- **iref_a**: 带隙基准电流源
- **lvr2**: 低压稳压器
- **cap_For_LYB**: 滤波电容

---

## 信号链总结

```
RF_IN (10.5GHz)
    ↓
[Balun/TFM] 单端→差分
    ↓
[LNA] 增益 ~20dB, NF < 2dB
    ↓
[Mixer] LO=10.5136GHz, IF=100MHz
    ↓
[TIA] 跨阻增益 1kΩ
    ↓
IF_OUT (100MHz)
```

## 电源域

| 电源 | 电压 | 用途 |
|------|------|------|
| VDD_RF | 3.3V | LNA, Mixer RF 部分 |
| VDD_DIG | 1.2V | 数字控制, DAC |
| VDD_IF | 2.5V | TIA, IF 放大器 |

## 控制信号

| 信号 | 作用 |
|------|------|
| ENLNA (3.3V) | LNA 使能 |
| ENRF (3.3V) | RF 路径使能 |
| ENNOTCH (1.2V) | Notch 滤波器使能 |
| SWDC1-3 | 直流开关控制 |
| SWN1-4 | Notch 开关控制 |

---

## 生成时间

2026-04-08