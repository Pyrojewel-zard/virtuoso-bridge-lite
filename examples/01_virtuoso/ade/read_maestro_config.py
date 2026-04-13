#!/usr/bin/env python3
"""读取 TB1_stage1_match_noise 的 Maestro 仿真配置和参数变量。

输出：
1. 测试列表
2. 各测试的分析配置（启用的分析类型 + 参数）
3. 设计变量列表
4. 输出配置
5. 环境选项（模型文件、仿真器等）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from virtuoso_bridge import VirtuosoClient

LIB = "TB1_LNA"
CELL = "TB1_stage1_match_noise"


def skill(client: VirtuosoClient, expr: str, **kw):
    """执行 SKILL 并返回结果"""
    r = client.execute_skill(expr, **kw)
    return r


def parse_list_output(output: str) -> list[str]:
    """解析 SKILL 列表输出 '(item1 item2)' 或 nil"""
    if not output or output.strip() in ("nil", ""):
        return []
    # 移除括号和引号
    output = output.strip()
    if output.startswith("(") and output.endswith(")"):
        output = output[1:-1]
    items = []
    for item in output.split():
        item = item.strip('"')
        if item:
            items.append(item)
    return items


def parse_nested_list(output: str) -> list:
    """解析嵌套列表 '((key val) (key val))'"""
    if not output or output.strip() in ("nil", ""):
        return []
    # 简单解析：提取 (key val) 对
    import re
    pairs = re.findall(r'\("([^"]+)"[^)]*\)', output)
    return pairs


def main():
    client = VirtuosoClient.from_env()
    print(f"[info] 读取 {LIB}/{CELL} 的 Maestro 配置")

    # 1. 打开 Maestro session
    r = skill(client, f'maeOpenSetup("{LIB}" "{CELL}" "maestro" ?mode "a")')
    ses = r.output.strip('"') if r.output else None
    if not ses:
        print("[error] 无法打开 Maestro session")
        return 1
    print(f"[session] {ses}")

    # 2. 获取测试列表
    r = skill(client, "maeGetSetup()")
    tests = parse_list_output(r.output)
    print(f"\n=== 测试列表 ({len(tests)} 个) ===")
    for t in tests:
        print(f"  - {t}")

    # 3. 遍历每个测试，读取配置
    for test in tests:
        print(f"\n=== 测试: {test} ===")

        # 启用的分析类型
        r = skill(client, f'maeGetEnabledAnalysis("{test}")')
        enabled_analyses = parse_list_output(r.output)
        print(f"  启用的分析: {enabled_analyses}")

        # 各分析的具体参数
        for ana in enabled_analyses:
            r = skill(client, f'maeGetAnalysis("{test}" "{ana}")')
            print(f"  [{ana}] 参数:")
            if r.output and r.output.strip() != "nil":
                # 打印完整输出（嵌套列表格式）
                print(f"    {r.output}")

        # 输出配置
        r = skill(client, f'maeGetTestOutputs("{test}")')
        print(f"  输出:")
        if r.output and r.output.strip() != "nil":
            print(f"    {r.output}")

        # 仿真器
        r = skill(client, f'maeGetEnvOption("{test}" ?option "simExecName")')
        simulator = r.output.strip('"') if r.output else "unknown"
        print(f"  仿真器: {simulator}")

        # 模型文件
        r = skill(client, f'maeGetEnvOption("{test}" ?option "modelFiles")')
        if r.output and r.output.strip() != "nil":
            print(f"  模型文件: {r.output}")

    # 4. 设计变量（使用 asi API，更可靠）
    print(f"\n=== 设计变量 ===")
    r = skill(client, "asiGetDesignVarList(asiGetCurrentSession())")
    if r.output and r.output.strip() != "nil":
        # 格式: (("var1" "val1") ("var2" "val2"))
        import re
        vars_output = r.output.strip()
        # 提取变量名和值
        var_pairs = re.findall(r'\("([^"]+)"\s+"([^"]*)"\)', vars_output)
        for name, val in var_pairs:
            print(f"  {name} = {val}")
        if not var_pairs:
            # 尝试另一种格式
            print(f"  原始输出: {vars_output}")
    else:
        print("  (无设计变量)")

    # 5. 也可以尝试 maeGetSetup(?typeName "globalVar")
    print(f"\n=== globalVar (maeGetSetup) ===")
    r = skill(client, 'maeGetSetup(?typeName "globalVar")')
    if r.output and r.output.strip() != "nil":
        print(f"  {r.output}")
    else:
        print("  (nil)")

    # 6. 运行模式
    r = skill(client, "maeGetCurrentRunMode()")
    run_mode = r.output.strip('"') if r.output else "unknown"
    print(f"\n=== 运行模式 ===")
    print(f"  {run_mode}")

    # 7. 关闭 session
    skill(client, f'maeCloseSession(?session "{ses}" ?forceClose t)')
    print(f"\n[done] Session 已关闭")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())