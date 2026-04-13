# Virtuoso Maestro 输出公式分析

## 一、TEST_LNA_MIXER_DIFF3_FINAL_LAYOUT_v2 (接收链)

### 1. Mixer 输出阻抗测量

```
MIX_real = real((vh('hb "/RFOUTP" '((0 1))) - vh('hb "/RFOUTN" '((0 1)))) / ih('hb "/IPRB2/PLUS" '((0 1))))
MIX_imag = imag((vh('hb "/RFOUTP" '((0 1))) - vh('hb "/RFOUTN" '((0 1)))) / ih('hb "/IPRB2/PLUS" '((0 1))))
```

**公式解析**:
- `vh('hb "/node" '((0 1)))` = HB 分析中节点电压的基波分量 (harmonic 0=DC, 1=基波)
- `ih('hb "/IPRB2/PLUS" '((0 1)))` = 通过 IPRB2 电流探针的基波电流
- **物理意义**: Z = V/I = 从 RFOUT 看进去的 **转换阻抗** (Mixer 输出 → TIA 输入)

**关键节点**:
| 节点 | 说明 |
|------|------|
| RFOUTP/N | Mixer 输出差分信号 |
| IPRB2 | Mixer 输出电流探针 |

### 2. 电压增益测量

```
Gain_LNAOUT = db((vh('hb "/LNAOUTP") - vh('hb "/LNAOUTN")) / harmonic((vh('hb "/RFIN<0>") - 0.0) '((0 1))))
Gain_RFOUT  = db((vh('hb "/RFOUTP" '((0 1))) - vh('hb "/RFOUTN" '((0 1)))) / vh('hb "/RFIN<0>" '((0 1))))
```

**公式解析**:
- `harmonic(signal '((0 1)))` = 提取基波分量
- 分子 = 差分输出电压
- 分母 = 单端输入电压 (RFIN<0>)
- **物理意义**: LNA 级增益 / 整体增益

### 3. S 参数测量

```
S21 = db(spm('hbsp 2 1))
```

**公式解析**:
- `spm('hbsp i j)` = HB S 参数，从端口 j 到端口 i
- 端口配置: PORT0 (输入), PORT6 (输出)
- **物理意义**: 整体 S21 增益

### 4. XF 分析

```
I/V /PORT0 = harmonic(getData("/PORT0" ?result "hbxf") '(1))
```

**公式解析**:
- `hbxf` = HB XF (传输函数) 分析结果
- **物理意义**: 端口电流/电压传输函数的基波分量

---

## 二、TEST_LNA_DIFF3_FINAL_LAYOUT (纯 LNA)

### 1. S 参数测量

```
S21 = db(spm('sp 2 1))   # 正向增益
S11 = db(spm('sp 1 1))   # 输入反射
S22 = db(spm('sp 2 2))   # 输出反射
```

**公式解析**:
- `spm('sp i j)` = S 参数，从端口 j 到端口 i

### 2. 稳定性因子

```
Kf = kf(sp(1 1 ?result "sp") sp(1 2 ?result "sp") sp(2 1 ?result "sp") sp(2 2 ?result "sp"))
```

**公式解析**:
- `kf(S11, S12, S21, S22)` = K 因子 (稳定性判断)
- **物理意义**: K > 1 且 |Δ| < 1 则无条件稳定

### 3. 噪声系数

```
NF = db10(getData("F" ?result "sp_noise"))
```

**公式解析**:
- `F` = 噪声因子 (噪声系数)
- `db10()` = 10*log10() (功率比)
- **物理意义**: 噪声系数 (dB)

---

## 三、TEST_XBR818C_BALUN_LNA_TOP_LAYOUT_ALL (完整收发机)

### 1. 电源电流

```
Idc = harmonic(pvi('hb "/VDD3P3" "/GND" "/V13/PLUS" 0) 0) / -3.3
```

**公式解析**:
- `pvi('hb "node1" "node2" "port" 0)` = 端口电压电流乘积 (功率)
- `harmonic(..., 0)` = DC 分量
- **物理意义**: 总电源电流

### 2. 效率

```
Efficiency = ((harmonic(pvi('hb "/net5" "/gnd!" "/PORT0/PLUS" 0) 1) / harmonic(pvi('hb "/VDD3P3" "/GND" "/V10/PLUS" 0) 0)) * -100)
```

**公式解析**:
- 分子 = RF 输出功率 (基波)
- 分母 = DC 电源功率
- **物理意义**: 功率效率 (%)

### 3. 输出频率

```
f0 = harmonic(xval(getData("TXOUT" ?result "hb_fd")) '1)
```

**公式解析**:
- `hb_fd` = HB 频域结果
- `xval()` = 获取 x 轴值 (频率)
- **物理意义**: 输出信号频率

### 4. 泄漏

```
Leakage = dbm(harmonic(pvi('hb "/net7" "/gnd!" "/PORT1/PLUS" 0) 1)) - dbm(harmonic(pvi('hb "/net5" "/gnd!" "/PORT0/PLUS" 0) 1))
```

**公式解析**:
- PORT1 = 泄漏端口
- PORT0 = 主输出端口
- **物理意义**: 输出到泄漏端口的功率差

### 5. 差分电压摆幅

```
LOdiffpk = harmonic(mag((vh('hb "/I0/I1/LOP") - vh('hb "/I0/I1/LON"))) 1)
VCOdiffpk = harmonic(mag((vh('hb "/I0/I1/PAINP") - vh('hb "/I0/I1/PAINN"))) 1)
```

**公式解析**:
- `vh('hb "/node")` = 节点电压
- `mag((Vp - Vn))` = 差分电压幅度
- **物理意义**: LO/VCO 差分摆幅 (峰值)

### 6. 相位差

```
phase_diff = abs(harmonic((phaseDegUnwrapped(vh('hb "/I0/I1/LOP")) - phaseDegUnwrapped(vh('hb "/I0/I1/LON"))) 1))
```

**公式解析**:
- `phaseDegUnwrapped()` = 展开相位 (避免 180° 跳变)
- **物理意义**: 差分信号相位差 (应为 180°)

### 7. 噪声测量

```
OPOUT_noise@10Hz = value(rfOutputNoise("V/sqrt(Hz)" ?result "hbnoise") 10)
Input_noise@10Hz = mag((value(rfOutputNoise("V/sqrt(Hz)" ?result "hbnoise") 10) / value(harmonic(getData("/PORT1" ?result "hbxf") '(1)) 10)))
```

**公式解析**:
- `rfOutputNoise("V/sqrt(Hz)")` = 输出噪声电压谱密度
- `hbxf` = 增益传输函数
- **物理意义**: 
  - 输出噪声: V/√Hz
  - 输入等效噪声: V/√Hz (输出噪声/增益)

### 8. 积分噪声

```
OPOUT_noise_10-100Hz = sqrt(integ(rfOutputNoise("V**2/Hz" ?result "hbnoise") 10 100 " "))
```

**公式解析**:
- `integ(V²/Hz, f1, f2)` = 噪声功率积分
- `sqrt()` = 转换回电压
- **物理意义**: 10-100Hz 带宽内 RMS 噪声

### 9. 相位噪声

```
PN@1M = value(pn('hbnoise) 1000000)
```

**公式解析**:
- `pn('hbnoise)` = 相位噪声曲线
- **物理意义**: 1MHz 偏移处相位噪声 (dBc/Hz)

---

## 四、TIA_CHOPPER_2024_Testbench (斩波 TIA)

### 1. AC 增益

```
AC_Gain = vfreq('ac "/OPOUTII") / (vfreq('ac "/net2") - vfreq('ac "/net12"))
```

**公式解析**:
- `vfreq('ac "/node")` = AC 分析中节点电压
- **物理意义**: TIA 闭环增益

### 2. PAC 增益

```
TIA_Gain@1Hz = mag(value((vh('pac "/OPOUTII" '(0)) / (vh('pac "/ip" '(0)) - vh('pac "/in" '(0)))) 1))
```

**公式解析**:
- `vh('pac "/node" '(0))` = PAC 分析中节点电压基波
- **物理意义**: 1Hz 处跨阻增益 (V/A)

### 3. 输入阻抗

```
TIA_Zin_real = value(real(zm(1 ?result "psp")) 1)
TIA_Zin_imag = value(imag(zm(1 ?result "psp")) 1)
```

**公式解析**:
- `zm(1, ?result "psp")` = P-SP 分析中端口 1 的阻抗
- **物理意义**: TIA 输入阻抗 (从 Mixer 看进去)

### 4. 噪声

```
TIA_Self_noise@1Hz = value(rfOutputNoise("V**2/Hz" ?result "pnoise") 1)
```

**公式解析**:
- `pnoise` = 周期稳态噪声分析
- **物理意义**: 1Hz 处输出噪声谱密度

---

## 五、公式分类总结

### 按分析类型分类

| 分析类型 | 函数前缀 | 用途 |
|----------|----------|------|
| **HB** | `vh('hb ...)`, `ih('hb ...)` | 大信号谐波平衡 |
| **HBSP** | `spm('hbsp ...)` | HB S 参数 |
| **HBXF** | `getData(..., ?result "hbxf")` | HB 传输函数 |
| **HBNoise** | `rfOutputNoise(..., ?result "hbnoise")` | HB 噪声 |
| **SP** | `spm('sp ...)`, `sp(...)` | 小信号 S 参数 |
| **SP_noise** | `getData("F", ?result "sp_noise")` | S 参数噪声 |
| **AC** | `vfreq('ac ...)` | 小信号 AC |
| **PAC** | `vh('pac ...)` | 周期 AC |
| **PSP** | `zm(..., ?result "psp")` | 周期 S 参数 |
| **PNoise** | `rfOutputNoise(..., ?result "pnoise")` | 周期噪声 |

### 按功能分类

| 功能 | 关键函数 | 示例 |
|------|----------|------|
| **电压/电流** | `vh()`, `ih()` | `vh('hb "/OUTP")` |
| **谐波提取** | `harmonic(signal, order)` | `harmonic(V, '(0 1))` |
| **差分信号** | `(Vp - Vn)` | `vh('hb "/P") - vh('hb "/N")` |
| **阻抗** | `V/I` 或 `zm()` | `vh(...)/ih(...)` |
| **增益** | `db()`, `db10()`, `db20()` | `db(spm('sp 2 1))` |
| **功率** | `pvi()`, `dbm()` | `dbm(pvi(...))` |
| **相位** | `phaseDegUnwrapped()` | `phaseDegUnwrapped(V)` |
| **噪声** | `rfOutputNoise()`, `pn()` | `rfOutputNoise("V**2/Hz")` |
| **积分** | `integ()`, `value()` | `integ(noise, f1, f2)` |
| **稳定性** | `kf()`, `gmin()`, `gmax()` | `kf(S11, S12, S21, S22)` |

---

## 六、关键公式模板

### 1. 差分阻抗测量 (HB)

```scheme
; 需要在路径上放置 iprobe
Z_diff_real = real((vh('hb "/OUTP" '((0 1))) - vh('hb "/OUTN" '((0 1)))) / ih('hb "/IPRB/PLUS" '((0 1))))
Z_diff_imag = imag((vh('hb "/OUTP" '((0 1))) - vh('hb "/OUTN" '((0 1)))) / ih('hb "/IPRB/PLUS" '((0 1))))
```

### 2. 差分电压增益 (HB)

```scheme
Gain_dB = db((vh('hb "/OUTP" '((0 1))) - vh('hb "/OUTN" '((0 1)))) / vh('hb "/IN" '((0 1))))
```

### 3. 转换增益 (下变频)

```scheme
; 基波频率处的输出电压 / 基波频率处的输入电压
ConvGain_dB = db((vh('hb "/IF_OUT" '((0 1)))) / vh('hb "/RF_IN" '((0 1))))
```

### 4. 输入等效噪声

```scheme
Input_noise = mag(rfOutputNoise("V/sqrt(Hz)" ?result "hbnoise") / harmonic(getData("/PORT" ?result "hbxf") '(1)))
```

### 5. 相位噪声

```scheme
PN_at_offset = value(pn('hbnoise) offset_frequency)
```

---

## 七、注意事项

### 1. 谐波阶数

- `'(0 1)` = DC + 基波
- `'(1)` = 仅基波
- `0` = DC 分量
- `1` = 基波分量
- `2` = 二次谐波

### 2. 差分信号

- 差分电压 = `(Vp - Vn)`
- 差分相位差应为 180°
- 注意单端转差分时的节点命名

### 3. 噪声分析

- `V**2/Hz` = 功率谱密度
- `V/sqrt(Hz)` = 电压谱密度
- 积分后需要 `sqrt()` 转换回电压

### 4. 端口编号

- S 参数中 `spm(i, j)` 表示从端口 j 到端口 i
- 阻抗中 `zm(n)` 表示从端口 n 看进去

---

**文档生成时间**: 2026-04-08