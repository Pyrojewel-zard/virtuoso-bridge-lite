#!/usr/bin/env python3
"""一键解读 Virtuoso Maestro 仿真配置。

输入: library + cell 名称
输出:
  1. 测试列表及分析配置
  2. 设计变量（扫描参数）
  3. 输出表达式
  4. 模型文件路径

原理:
  - SKILL API (maeGetSetup, maeGetAnalysis) 能读取测试和分析配置
  - 设计变量和输出表达式需要从 maestro.sdb 和 active.state XML 文件解析
  - 这是因为 maeGetVarList() 和 maeGetTestOutputs()~>expr 经常返回 nil

使用:
  python read_maestro_full_config.py <lib> <cell>
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from virtuoso_bridge import VirtuosoClient


def skill(client: VirtuosoClient, expr: str, **kw) -> str:
    """执行 SKILL 并返回清理后的输出"""
    r = client.execute_skill(expr, **kw)
    if r.output and r.output != "nil":
        return r.output.strip('"')
    return ""


def get_lib_path(client: VirtuosoClient, lib: str) -> str:
    """获取库的物理路径"""
    r = client.execute_skill(f'ddGetObj("{lib}")~>readPath')
    return r.output.strip('"') if r.output else ""


def parse_maestro_sdb(content: str) -> dict:
    """解析 maestro.sdb XML 文件，提取设计变量"""
    vars = {}

    # 提取变量定义（多行格式）
    # <var>W1
    #     <value>40u,60u,80u</value>
    # </var>
    var_blocks = re.findall(r'<var>(\w+)\s*\n\s*<value>([^<]+)</value>', content)
    for name, value in var_blocks:
        vars[name] = value

    return vars


def parse_active_state(content: str) -> dict:
    """解析 active.state XML 文件，提取分析参数和输出表达式"""
    config = {
        "analyses": {},
        "outputs": []
    }

    # 提取分析配置
    # <analysis Name="sp">...<field Name="start" Type="string">"1G"</field>...
    for ana_match in re.finditer(r'<analysis Name="(\w+)">(.*?)</analysis>', content, re.DOTALL):
        ana_name = ana_match.group(1)
        fields = {}
        for field_match in re.finditer(r'<field Name="(\w+)"[^>]*>([^<]*)</field>', ana_match.group(2)):
            name = field_match.group(1)
            value = field_match.group(2).strip('"')
            if value and value != "nil":
                fields[name] = value
        if fields:
            config["analyses"][ana_name] = fields

    # 提取输出表达式
    # <field Name="name" Type="string">"S21_dB"</field>
    # <field Name="expression" Type="list">dB20((S 2 1))</field>
    output_pattern = r'<field Name="outputList_\d+"[^>]*>.*?<field Name="name"[^>]*>"([^"]+)"</field>.*?<field Name="expression"[^>]*>([^<]+)</field>'
    for match in re.finditer(output_pattern, content, re.DOTALL):
        name = match.group(1)
        expr = match.group(2).strip()
        config["outputs"].append({"name": name, "expression": expr})

    return config


def read_maestro_config(client: VirtuosoClient, lib: str, cell: str) -> dict:
    """完整读取 Maestro 配置"""
    config = {
        "lib": lib,
        "cell": cell,
        "tests": [],
        "vars": {},
        "outputs": [],
        "analyses": {},
        "model_files": []
    }

    # 1. 打开 Maestro session
    r = client.execute_skill(f'maeOpenSetup("{lib}" "{cell}" "maestro")')
    ses = r.output.strip('"') if r.output else ""
    if not ses:
        print(f"[error] 无法打开 {lib}/{cell} maestro")
        return config

    print(f"[session] {ses}")

    # 2. 获取测试列表
    r = client.execute_skill("maeGetSetup()")
    tests_raw = r.output
    if tests_raw and tests_raw != "nil":
        tests = tests_raw.strip('()').replace('"', '').split()
        config["tests"] = tests
    print(f"[tests] {config['tests']}")

    # 3. 获取每个测试的分析配置（通过 SKILL API）
    for test in config["tests"]:
        r = client.execute_skill(f'maeGetEnabledAnalysis("{test}")')
        enabled = r.output.strip('()').replace('"', '').split() if r.output else []
        print(f"[{test}] 分析: {enabled}")

        for ana in enabled:
            r = client.execute_skill(f'maeGetAnalysis("{test}" "{ana}")')
            print(f"  [{ana}] {r.output[:200] if r.output else 'nil'}...")

        # 获取模型文件
        r = client.execute_skill(f'maeGetEnvOption("{test}" ?option "modelFiles")')
        if r.output and r.output != "nil":
            config["model_files"].append(r.output)

    # 4. 获取库路径
    lib_path = get_lib_path(client, lib)
    print(f"[lib_path] {lib_path}")

    # 5. 从 XML 文件读取设计变量和输出表达式
    if lib_path:
        # 下载 maestro.sdb
        sdb_remote = f"{lib_path}/{cell}/maestro/maestro.sdb"
        sdb_local = "/tmp/maestro_sdb.xml"
        try:
            client.download_file(sdb_remote, sdb_local)
            sdb_content = Path(sdb_local).read_text()
            config["vars"] = parse_maestro_sdb(sdb_content)
            print(f"[vars from sdb] {config['vars']}")
        except Exception as e:
            print(f"[warn] 无法下载 maestro.sdb: {e}")

        # 下载 active.state
        state_remote = f"{lib_path}/{cell}/maestro/active.state"
        state_local = "/tmp/active_state.xml"
        try:
            client.download_file(state_remote, state_local)
            state_content = Path(state_local).read_text()
            state_config = parse_active_state(state_content)
            config["outputs"] = state_config["outputs"]
            config["analyses"] = state_config["analyses"]
            print(f"[outputs from state] {len(config['outputs'])} outputs")
            for o in config["outputs"]:
                print(f"  {o['name']}: {o['expression']}")
        except Exception as e:
            print(f"[warn] 无法下载 active.state: {e}")

    # 6. 关闭 session
    client.execute_skill(f'maeCloseSession(?session "{ses}" ?forceClose t)')
    print("[done] Session 已关闭")

    return config


def print_config_summary(config: dict):
    """打印配置摘要"""
    print("\n" + "=" * 60)
    print(f"=== {config['lib']}/{config['cell']} Maestro 配置摘要 ===")
    print("=" * 60)

    print("\n[设计变量]")
    for name, value in config["vars"].items():
        sweep_count = len(value.split(",")) if "," in value else 1
        print(f"  {name} = {value} ({sweep_count} 个扫描点)")

    print("\n[测试]")
    for test in config["tests"]:
        print(f"  {test}")

    print("\n[输出表达式]")
    for o in config["outputs"]:
        print(f"  {o['name']}: {o['expression']}")

    # 计算总仿真次数
    sweep_vars = [v for v in config["vars"].values() if "," in v]
    if sweep_vars:
        total = 1
        for v in sweep_vars:
            total *= len(v.split(","))
        print(f"\n[总扫描组合数] {total}")


def main():
    if len(sys.argv) < 3:
        print("用法: python read_maestro_full_config.py <lib> <cell>")
        print("示例: python read_maestro_full_config.py Zck_XBR818D_2026 TB1_stage1_match_noise")
        return 1

    lib = sys.argv[1]
    cell = sys.argv[2]

    client = VirtuosoClient.from_env()
    config = read_maestro_config(client, lib, cell)
    print_config_summary(config)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())