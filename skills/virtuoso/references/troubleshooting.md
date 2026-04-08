# Virtuoso 调试指南

常见错误、调试步骤、解决方案速查表。

---

## 一、常见错误速查表

| 错误现象 | 根因 | 解决方案 |
|----------|------|----------|
| execute_skill 超时无响应 | GUI 弹窗阻塞 SKILL channel | `hiFormDone(hiGetCurrentForm())` |
| "no such file or directory" | 远程路径错误或未 cd | 检查 VB_REMOTE_HOST + SSH 先 cd |
| netlisting fails with dialog | schematic 未 schCheck+save | 执行 `schCheck(cv)` + `dbSave(cv)` |
| "Change Mode Confirmation" 弹窗 | edit mode 冲突 | `MaestroDismissDialog()` 或 `hiFormDone()` |
| maeSetVar 参数不生效 | schematic CDF 参数是数值而非变量名 | CDF 值设为变量名（如 `"c_val"`） |
| bandwidth() 返回 nil | expression 用 v() 而非 VF() | 频域分析用 `VF("/net")` |
| 仿真结果目录找不到 | .tmpADEDir 路径混淆 | `asiGetResultsDir` + 正则提取 |
| "cellview is locked" | .cdslck 文件残留 | `MaestroClearLocks()` 或手动删除 |
| maeRestoreHistory 无效果 | maestro 未在 edit mode | 先 `maeMakeEditable()` |

---

## 二、GUI 弹窗阻塞（最常见问题）

### 症状
- `execute_skill()` 超时（触发 timeout）
- 返回值始终为空
- Virtuoso GUI 显示等待用户点击的对话框

### 根因
SKILL 执行是单线程的。GUI 弹窗阻塞整个 SKILL channel，直到用户手动点击。

### 解决方案

**方案 1: 预防式关闭**
```python
# 在可能触发弹窗的操作后立即调用
client.execute_skill('hiFormDone(hiGetCurrentForm())')
```

**方案 2: 使用 maestro_utils.il 封装**
```python
client.load_il("examples/01_virtuoso/assets/maestro_utils.il")
client.execute_skill('MaestroDismissDialog()')
```

**方案 3: 远程用户手动操作**
告知远程用户点击弹窗按钮，等待几秒后重试。

### 易触发弹窗的操作

| 操作 | 弹窗类型 | 预防方法 |
|------|----------|----------|
| `maeMakeEditable()` | "Change Mode Confirmation" | `MaestroDismissDialog()` |
| `maeRestoreHistory()` | "Specify history name" | 无（需手动确认） |
| `deOpenCellView` | "Overwrite existing?" | 无（需手动确认） |
| `hiCloseWindow` | "Save changes?" | 先 save 再 close |
| `maeRunSimulation`（无 analysis） | "No analyses enabled" | 先配置 analysis |

---

## 三、原理图检查失败

### 症状
- Maestro netlisting 报错
- 弹窗显示 "Check and Save schematic first"

### 解决方案
```python
cv = "_myCv"
client.execute_skill(f'{cv} = dbOpenCellViewByType("{lib}" "{cell}" "schematic" nil "a")')
r = client.execute_skill(f'schCheck({cv})')  # 返回 (errorCount warningCount)
print(f"Check result: {r.output}")

if "0 0" not in r.output:
    print("Schematic has errors/warnings!")

client.execute_skill(f'dbSave({cv})')
```

**注意**：仿真前必须执行 schCheck + dbSave，否则 netlisting 失败。

---

## 四、Edit Lock 冲突

### 症状
- `maeOpenSetup` 报错 "cellview is locked"
- `.cdslck` 文件残留

### 解决方案

**方案 1: 使用 MaestroClose 强制关闭**
```python
client.load_il("examples/01_virtuoso/assets/maestro_utils.il")
client.execute_skill(f'MaestroClose("{lib}" "{cell}")')
```

**方案 2: 清除锁文件**
```python
client.execute_skill(f'MaestroClearLocks("{lib}" "{cell}")')
```

**方案 3: 手动删除**
```python
# 需先获取库路径
r = client.execute_skill(f'ddGetObj("{lib}")~>writePath')
lib_path = r.output.strip('"')
lock_path = f"{lib_path}/{cell}/maestro/maestro.sdb.cdslck"
client.run_shell_command(f'rm -f "{lock_path}"')
```

---

## 五、仿真运行阻塞

### 症状
- `maeRunSimulation(?waitUntilDone t)` 导致 GUI 无响应
- bridge 连接断开

### 根因
`?waitUntilDone t` 阻塞 Virtuoso 事件循环。GUI 无法刷新，SKILL channel 也被阻塞。

### 解决方案
```python
# ✅ 正确方式：异步运行 + 等待
client.execute_skill(f'maeRunSimulation(?session "{ses}")')
client.execute_skill("maeWaitUntilDone('All)", timeout=300)

# ❌ 错误方式：同步阻塞
# client.execute_skill(f'maeRunSimulation(?waitUntilDone t ?session "{ses}")')
```

---

## 六、结果读取失败

### 症状
- `openResults()` 返回 nil
- `v("/OUT")` 报错 "signal not found"

### 常见原因与解决方案

**1. 结果目录路径问题**
```python
# 获取实际结果目录
r = client.execute_skill('asiGetResultsDir(asiGetCurrentSession())')
results_dir = r.output.strip('"')

# 处理 .tmpADEDir 路径
if ".tmpADEDir" in results_dir:
    base = results_dir.split(".tmpADEDir")[0]
    r = client.run_shell_command(
        f"ls -1d {base}Interactive.*/psf/AC 2>/dev/null | tail -1")
    results_dir = r.output.strip()
```

**2. 分析类型不匹配**
```python
# 必须先 selectResults
client.execute_skill(f'openResults("{results_dir}")')
client.execute_skill('selectResults("ac")')   # AC 分析
# client.execute_skill('selectResults("tran")')  # TRAN 分析
```

**3. 信号名格式错误**
```python
# ✅ 正确：带斜杠
client.execute_skill('v("/OUT")')

# ❌ 错误：不带斜杠
# client.execute_skill('v("OUT")')
```

---

## 七、Pnoise Jitter Event 限制

### 症状
- pnoise analysis 配置成功
- jitter event 表为空
- `_spectreRFAddJitterEvent` 返回 nil

### 根因
SKILL API 无法完整控制 jitter event 表的 Qt widget 状态。

### 解决方案：复制 active.state
```python
src_maestro = "/path/to/reference/cell/maestro"
dst_maestro = f"{lib_path}/{cell}/maestro"

# 复制并替换实例路径
client.run_shell_command(f"cp {src_maestro}/active.state {dst_maestro}/active.state")
client.run_shell_command(f"sed -i 's|/I_ref/|/{inst_name}/|g' {dst_maestro}/active.state")

# 重开 maestro 以加载
client.execute_skill(f'MaestroClose("{lib}" "{cell}")')
client.execute_skill(f'MaestroOpen("{lib}" "{cell}")')
```

### 探索过但失败的方案

| 方案 | 结果 |
|------|------|
| `_spectreRFAddJitterEvent` | 函数存在但无效 |
| `asiSetAnalysisFieldVal("measTableData" ...)` | 内存更新但不持久化 |
| `asiSetAnalysisFieldVal` + `hiFormApply` | 持久化但 GUI 可能不显示 |
| `maeSetAnalysis` with measTableData | 内存更新但不持久化 |

---

## 八、连接诊断流程

不确定问题时，按此顺序检查：

```bash
# 1. 检查 bridge 状态
virtuoso-bridge status

# 2. 检查 Virtuoso 进程（远程）
ssh <VB_REMOTE_HOST> "pgrep -f virtuoso"

# 3. 检查 Spectre 许可证
virtuoso-bridge license

# 4. 测试 SKILL channel
python -c "
from virtuoso_bridge import VirtuosoClient
c = VirtuosoClient.from_env()
print(c.execute_skill('getVersion()').output)
"

# 5. 检查 SSH 连接
ssh <VB_REMOTE_HOST> "echo ok"
```

---

## 九、SSH 执行路径问题

### 症状
- `ssh RFRLSERVER5 'python3 /path/to/script.py'` 报错 "no such file or directory"

### 根因
远程服务器的工作目录不是项目目录。

### 解决方案：必须先 cd
```python
# ✅ 正确：先 cd 到项目目录
ssh_cmd = f'ssh RFRLSERVER5 "cd /path/to/project && python3 scripts/xxx.py"'
client.run_shell_command(ssh_cmd)

# ❌ 错误：直接执行
# ssh_cmd = f'ssh RFRLSERVER5 "python3 /path/to/project/scripts/xxx.py"'
```

---

## 十、调试技巧速查

### 验证 cellview 创建
```python
r = client.execute_skill(f'ddGetObj("{lib}" "{cell}")')
if r.output == "nil":
    print("Cell not found!")

r = client.execute_skill(f'ddGetObj("{lib}" "{cell}")~>views~>name')
print(f"Views: {r.output}")
```

### 列出 schematic 内容
```python
# 实例列表
r = client.execute_skill(f'{cv}~>instances~>name')
print(f"Instances: {r.output}")

# 网列表
r = client.execute_skill(f'{cv}~>nets~>name')
print(f"Nets: {r.output}")

# 终端列表
r = client.execute_skill(f'{cv}~>terminals~>name')
print(f"Terminals: {r.output}")
```

### 查询实例终端
```python
# 查询 master 的所有终端
r = client.execute_skill(f'dbOpenCellView("{inst_lib}" "{inst_cell}" "symbol")~>terminals~>name')
print(f"Instance terminals: {r.output}")

# 查询终端方向
r = client.execute_skill(f'dbOpenCellView("{inst_lib}" "{inst_cell}" "symbol")~>terminals~>direction')
print(f"Terminal directions: {r.output}")
```

### 读取现有 Maestro 配置
```python
# 打开 GUI 后读取
client.execute_skill(f'deOpenCellView("{lib}" "{cell}" "maestro" "maestro" nil "r")')

# Test 列表
r = client.execute_skill('maeGetSetup()')
print(f"Tests: {r.output}")

# Analysis 配置
r = client.execute_skill(f'maeGetAnalysis("{test}" "ac")')
print(f"AC config: {r.output}")

# Design Variables（用 asi* API）
r = client.execute_skill('asiGetDesignVarList(asiGetCurrentSession())')
print(f"Variables: {r.output}")
```