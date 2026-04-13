#!/usr/bin/env python3
"""读取 TB1_stage1_match_noise 的 schematic 配置和参数变量。

输出：
1. TB schematic 实例配置（PORT0, PORT1, VG1_SRC, VDD_SRC）
2. DUT (stage1_match_noise) 实例配置
3. 设计变量列表（W1, W2, Lg_val, Lp_val, Ls_val, Cin_val, VG1_bias）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from virtuoso_bridge import VirtuosoClient

LIB = "Zck_XBR818D_2026"
TB_CELL = "TB1_stage1_match_noise"
DUT_CELL = "stage1_match_noise"


def skill(client: VirtuosoClient, expr: str, **kw):
    r = client.execute_skill(expr, **kw)
    return r.output.strip('"') if r.output else ""


def get_cdf_param(client: VirtuosoClient, cv_var: str, inst_name: str, param: str) -> str:
    """获取实例的 CDF 参数值"""
    r = client.execute_skill(
        f'let((cdf) '
        f'  cdf = cdfGetInstCDF(car(setof(i {cv_var}~>instances i~>name == "{inst_name}")))'
        f'  if(cdf then cdfFindParamByName(cdf "{param}")~>value else nil)'
        f')'
    )
    if r.output and r.output != "nil":
        return r.output.strip('"')
    return ""


def main():
    client = VirtuosoClient.from_env()

    # 打开 TB schematic
    client.execute_skill(f'tb_cv = dbOpenCellViewByType("{LIB}" "{TB_CELL}" "schematic" nil "r")')
    print(f"=== {LIB}/{TB_CELL} schematic 配置 ===")

    # TB 实例列表
    r = client.execute_skill("tb_cv~>instances~>name")
    print(f"实例: {r.output}")

    # PORT0 (输入 port)
    print("\n[PORT0] (输入 port)")
    print(f"  r: {get_cdf_param(client, 'tb_cv', 'PORT0', 'r')}")
    print(f"  sourceType: {get_cdf_param(client, 'tb_cv', 'PORT0', 'sourceType')}")

    # PORT1 (输出 port)
    print("\n[PORT1] (输出 port)")
    print(f"  r: {get_cdf_param(client, 'tb_cv', 'PORT1', 'r')}")
    print(f"  sourceType: {get_cdf_param(client, 'tb_cv', 'PORT1', 'sourceType')}")

    # VG1_SRC (偏置)
    print("\n[VG1_SRC] (偏置 vdc)")
    print(f"  vdc: {get_cdf_param(client, 'tb_cv', 'VG1_SRC', 'vdc')}")

    # VDD_SRC (电源)
    print("\n[VDD_SRC] (电源 vdc)")
    print(f"  vdc: {get_cdf_param(client, 'tb_cv', 'VDD_SRC', 'vdc')}")

    # 打开 DUT schematic
    client.execute_skill(f'dut_cv = dbOpenCellViewByType("{LIB}" "{DUT_CELL}" "schematic" nil "r")')
    print(f"\n=== {LIB}/{DUT_CELL} (DUT) schematic 配置 ===")

    # DUT 实例列表
    r = client.execute_skill("dut_cv~>instances~>name")
    print(f"实例: {r.output}")

    r = client.execute_skill("dut_cv~>instances~>cellName")
    print(f"cellName: {r.output}")

    # M1 (n12_ckt_rf)
    print("\n[M1] (n12_ckt_rf - 主放大管)")
    print(f"  w: {get_cdf_param(client, 'dut_cv', 'M1', 'w')}")
    print(f"  l: {get_cdf_param(client, 'dut_cv', 'M1', 'l')}")
    print(f"  fingers: {get_cdf_param(client, 'dut_cv', 'M1', 'fingers')}")
    print(f"  m: {get_cdf_param(client, 'dut_cv', 'M1', 'm')}")

    # M2 (n12_ckt_rf)
    print("\n[M2] (n12_ckt_rf - 共源共栅管)")
    print(f"  w: {get_cdf_param(client, 'dut_cv', 'M2', 'w')}")
    print(f"  l: {get_cdf_param(client, 'dut_cv', 'M2', 'l')}")
    print(f"  fingers: {get_cdf_param(client, 'dut_cv', 'M2', 'fingers')}")
    print(f"  m: {get_cdf_param(client, 'dut_cv', 'M2', 'm')}")

    # Lg (ind - 栅极电感)
    print("\n[Lg] (ind - 栅极电感)")
    print(f"  l: {get_cdf_param(client, 'dut_cv', 'Lg', 'l')}")

    # Lp (ind - 并联电感)
    print("\n[Lp] (ind - 并联电感)")
    print(f"  l: {get_cdf_param(client, 'dut_cv', 'Lp', 'l')}")

    # Ls (ind - 源极电感)
    print("\n[Ls] (ind - 源极电感)")
    print(f"  l: {get_cdf_param(client, 'dut_cv', 'Ls', 'l')}")

    # Cin (cap - 输入电容)
    print("\n[Cin] (cap - 输入电容)")
    print(f"  c: {get_cdf_param(client, 'dut_cv', 'Cin', 'c')}")

    # 总结设计变量
    print("\n" + "=" * 60)
    print("=== 设计变量汇总 ===")
    print("=" * 60)
    print("""
  VG1_bias  - VG1_SRC.vdc (栅极偏置电压)
  W1        - M1.w (主放大管宽度)
  W2        - M2.w (共源共栅管宽度)
  Lg_val    - Lg.l (栅极电感)
  Lp_val    - Lp.l (并联电感)
  Ls_val    - Ls.l (源极电感)
  Cin_val   - Cin.c (输入电容)

  VDD_SRC.vdc = 1.2 (固定电源电压)
  PORT0.r = PORT1.r = 50 (端口阻抗)
""")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())