# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test

```bash
pip install -e ".[dev]"   # 安装开发依赖
pytest                     # 运行测试（当前无 tests 目录）
```

## CLI Commands

```bash
virtuoso-bridge init      # 创建 .env 配置模板
virtuoso-bridge start     # 启动 SSH 隧道 + 部署远程 daemon
virtuoso-bridge stop      # 停止隧道
virtuoso-bridge restart   # 重启隧道
virtuoso-bridge status    # 检查隧道 + Virtuoso daemon + Spectre 状态
virtuoso-bridge license   # 检查 Spectre 许可证

# 多 profile 支持
virtuoso-bridge start -p worker1   # 使用特定 profile
```

## Architecture

三层架构，完全解耦：

| 层 | 模块 |职责 |
|----|------|------|
| **传输层** | `transport/` | SSH 隧道管理、端口转发、文件传输 |
| **客户端层** | `VirtuosoClient` | 纯 TCP SKILL 执行，无 SSH 依赖 |
| **业务层** | `layout/`, `schematic/`, `spectre/` | 高级 API 封装 |

**关键设计**：
- `VirtuosoClient` 只处理 TCP 通信，可用于任何 `localhost:port` 端点
- `SSHClient` 可选，本地模式完全绕过
- `SpectreSimulator` 独立于 Virtuoso GUI，可直接运行 `.scs` 网表

## Two Connection Modes

| 模式 | 使用场景 | 配置 |
|------|----------|------|
| **远程模式** | Virtuoso 在服务器 | 配置 `.env` + `virtuoso-bridge start` |
| **本地模式** | Virtuoso 在本机 | `VirtuosoClient.local(port=65432)` |

远程模式三主机架构（常见 EDA 环境）：
```
本机 ──SSH──► 跳板机 (VB_JUMP_HOST) ──SSH──► 计算主机 (VB_REMOTE_HOST, Virtuoso 运行处)
```

**重要**：`VB_REMOTE_HOST` 必须是 Virtuoso 实际运行的主机，不是跳板机。

## Skills Directory

| Skill | 文件 | 覆盖范围 |
|-------|------|----------|
| `virtuoso` | `skills/virtuoso/SKILL.md` | SKILL 执行、layout/schematic 编辑、ADE Maestro |
| `spectre` | `skills/spectre/SKILL.md` | 网表驱动仿真、PSF 结果解析 |

**加载 skill 时阅读对应 SKILL.md 和 references/ 子目录。**

## Remote Virtuoso Setup

用户首次连接远程 Virtuoso 时，按此流程检查：

1. 检查 `.env` 是否存在且 `VB_REMOTE_HOST` 已设置
2. 测试 SSH：`ssh <VB_REMOTE_HOST> echo ok`
3. 检查 Virtuoso 进程：`ssh <VB_REMOTE_HOST> "pgrep -f virtuoso"`
4. 启动桥接：`virtuoso-bridge start`
5. 在 Virtuoso CIW 中加载：`load("/tmp/virtuoso_bridge_<user>/virtuoso_bridge/virtuoso_setup.il")`
6. 验证：`virtuoso-bridge status`

## Python API Levels — 调用优先级

**优先使用 Python 高级 API，仅在覆盖不到时降级到 SKILL。**

| 优先级 | 方式 | 使用场景 | 示例 |
|--------|------|----------|------|
| **1️⃣ 首选** | Python 高级 API | Layout/Schematic 编辑 — 结构化、安全、自动上下文管理 | `client.schematic.edit(lib, cell)` |
| **2️⃣ 次选** | `execute_skill()` | ADE Maestro 控制、CDF 参数设置、Python API 未覆盖的功能 | `client.execute_skill('maeRunSimulation()')` |
| **3️⃣ 补充** | `.il` 文件 | 批量操作、复杂循环 — 保持 payload 小 | `client.load_il("script.il")` |

### 为什么优先 Python API

```python
# ✅ 推荐：Python API — 可读、有类型提示、上下文管理器自动保存
with client.schematic.edit(lib, cell) as sch:
    sch.add_instance("analogLib", "vdc", (0, 0), "V0", params={"vdc": "0.9"})

# ⚠️ 可行但不推荐：直接写 SKILL — 需处理转义、无类型检查
client.execute_skill('dbCreateInst(...)')  # 易出错
```

**Python API 优势**：
- 上下文管理器自动保存/关闭 cellview
- 终端感知连线辅助（`add_wire_between_instance_terms` — 不用手算坐标）
- 错误处理友好、代码可读性高

### 何时降级到 `execute_skill`

Python API 覆盖不到的场景：
- **ADE Maestro**：`maeCreateTest`, `maeSetAnalysis`, `maeAddOutput`, `maeRunSimulation`
- **CDF 参数**：`cdfGetInstCDF`, `cdfFindParamByName`
- **数据库查询**：`dbGetq`, `dbOpenCellViewByType`

## Key Patterns from Examples

### Schematic 创建流程

1. `with client.schematic.edit(lib, cell) as sch:` — 创建并自动保存
2. `sch.add_instance()` — 添加器件
3. `sch.add_wire_between_instance_terms()` — 终端感知连线（优于手算坐标）
4. `sch.add_pin_to_instance_term()` — 直接连接 pin 到器件终端
5. CDF 参数需降级：`cdfFindParamByName(cdfGetInstCDF(inst), "param")~>value = "val"`
6. **仿真前必须**：`schCheck(cv)` + `dbSave(cv)` — 否则 netlist 失败

### Maestro 仿真流程

1. `maeOpenSetup(lib, cell, "maestro")` → 获取 session 字符串
2. `maeCreateTest()` → 创建 test
3. `maeSetAnalysis()` → 配置分析（backtick 语法：`` `(("start" "1")) ``）
4. `maeAddOutput()` → 添加输出（net 波形或 point 表达式）
5. `maeSetVar("var", "val1,val2")` → comma-separated = parametric sweep
6. `maeSaveSetup()` → 保存配置
7. **异步运行**：`maeRunSimulation()` + `maeWaitUntilDone('All)` — 禁用 `?waitUntilDone t`（阻塞事件循环）

**关键坑**：
- `?session` 必须是字符串（如 `"fnxSession4"`），不是变量
- GUI dialogs 会阻塞 SKILL 通道 — 用 `hiFormDone(hiGetCurrentForm())` 关闭
- Maestro 结果表达式用 `VF()`（频域电压），不是 `v()`

详细经验见 memory 文件 `virtuoso-schematic-creation-workflow.md` 和 `virtuoso-maestro-workflow.md`。

## Examples

`examples/01_virtuoso/` 和 `examples/02_spectre/` 包含 30+ 可运行示例。
实现类似功能时，先查阅对应示例作为模板。