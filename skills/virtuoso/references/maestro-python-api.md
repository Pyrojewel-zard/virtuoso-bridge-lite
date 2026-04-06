# Maestro Python API

Python wrapper for Cadence Maestro (ADE Assembler) SKILL functions.

**Package:** `virtuoso_bridge.virtuoso.maestro`

```python
from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import open_session, close_session, read_config
```

## Session Management

`maestro/session.py`

| Python | SKILL | Description |
|--------|-------|-------------|
| `open_session(client, lib, cell) -> str` | `maeOpenSetup` | Background open, returns session string |
| `close_session(client, ses)` | `maeCloseSession` | Background close |
| `find_open_session(client) -> str \| None` | `maeGetSessions` + `maeGetSetup` | Find first active session with valid test |

```python
ses = open_session(client, "PLAYGROUND_AMP", "TB_AMP_5T_D2S_DC_AC")
# ... do work ...
close_session(client, ses)
```

## Read — Three independent functions

`maestro/reader.py`

All return `dict[str, tuple[str, str]]` where key = label, value = `(skill_expr, raw_output)`.

### read_config — test setup

| Key | SKILL |
|-----|-------|
| `maeGetSetup` | `maeGetSetup(?session ses)` |
| `maeGetEnabledAnalysis` | `maeGetEnabledAnalysis(test ?session ses)` |
| `maeGetAnalysis:<name>` | `maeGetAnalysis(test name ?session ses)` — one per enabled analysis |
| `maeGetTestOutputs` | `maeGetTestOutputs(test ?session ses)` — returns `(name type signal expression)` |
| `variables` | `maeGetSetup(?session ses ?typeName "variables")` |
| `parameters` | `maeGetSetup(?session ses ?typeName "parameters")` |
| `corners` | `maeGetSetup(?session ses ?typeName "corners")` |

### read_env — system settings

| Key | SKILL |
|-----|-------|
| `maeGetEnvOption` | `maeGetEnvOption(test ?session ses)` — model files, view lists, etc. |
| `maeGetSimOption` | `maeGetSimOption(test ?session ses)` — reltol, temp, gmin, etc. |
| `maeGetCurrentRunMode` | `maeGetCurrentRunMode(?session ses)` |
| `maeGetJobControlMode` | `maeGetJobControlMode(?session ses)` |
| `maeGetSimulationMessages` | `maeGetSimulationMessages(?session ses)` |

### read_results — simulation results

| Key | SKILL |
|-----|-------|
| `maeGetResultTests` | `maeGetResultTests()` |
| `maeGetOutputValues` | SKILL loop: `maeGetOutputValue` + `maeGetSpecStatus` for each output |
| `maeGetOverallSpecStatus` | `maeGetOverallSpecStatus()` |
| `maeGetOverallYield` | `maeGetOverallYield(history)` |

History name is auto-detected from `asiGetResultsDir`. Returns empty dict if no results.

### export_waveform — download wave data

| Python | SKILL / OCEAN |
|--------|---------------|
| `export_waveform(client, ses, expression, local_path, *, analysis="ac", history="")` | `maeOpenResults` → `selectResults` → `ocnPrint` → `maeCloseResults` |

For outputs that return `"wave"` instead of a scalar. Downloads the waveform as a text file (freq/time vs value).

```python
ses = open_session(client, "PLAYGROUND_AMP", "TB_AMP_5T_D2S_DC_AC")

# Read config
for key, (expr, raw) in read_config(client, ses).items():
    print(f"[{key}] {expr}")
    print(raw)

# Read env
for key, (expr, raw) in read_env(client, ses).items():
    print(f"[{key}] {expr}")
    print(raw)

# Read results
for key, (expr, raw) in read_results(client, ses).items():
    print(f"[{key}] {expr}")
    print(raw)

# Export waveform
export_waveform(client, ses,
    'dB20(mag(VF("/VOUT") / VF("/VSIN")))',
    "output/gain_db.txt", analysis="ac")

export_waveform(client, ses,
    'getData("out" ?result "noise")',
    "output/noise.txt", analysis="noise")

close_session(client, ses)
```

## Write — Test

`maestro/writer.py`

| Python | SKILL | Description |
|--------|-------|-------------|
| `create_test(client, test, *, lib, cell, view="schematic", simulator="spectre", ses="")` | `maeCreateTest` | Create a new test |
| `set_design(client, test, *, lib, cell, view="schematic", ses="")` | `maeSetDesign` | Change DUT for existing test |

```python
create_test(client, "TRAN2", lib="myLib", cell="myCell")
set_design(client, "TRAN2", lib="myLib", cell="newCell")
```

## Write — Analysis

| Python | SKILL | Description |
|--------|-------|-------------|
| `set_analysis(client, test, analysis, *, enable=True, options="", ses="")` | `maeSetAnalysis` | Enable/disable analysis, set options |

```python
# Enable transient with stop=60n
set_analysis(client, "TRAN2", "tran", options='(("stop" "60n") ("errpreset" "conservative"))')

# Enable AC
set_analysis(client, "TRAN2", "ac", options='(("start" "1") ("stop" "10G") ("dec" "20"))')

# Disable tran
set_analysis(client, "TRAN2", "tran", enable=False)
```

## Write — Outputs & Specs

| Python | SKILL | Description |
|--------|-------|-------------|
| `add_output(client, name, test, *, output_type="", signal_name="", expr="", ses="")` | `maeAddOutput` | Add waveform or expression output |
| `set_spec(client, name, test, *, lt="", gt="", ses="")` | `maeSetSpec` | Set pass/fail spec |

```python
# Waveform output
add_output(client, "OutPlot", "TRAN2", output_type="net", signal_name="/OUT")

# Expression output
add_output(client, "maxOut", "TRAN2", output_type="point", expr='ymax(VT(\\"/OUT\\"))')

# Spec: maxOut < 400mV
set_spec(client, "maxOut", "TRAN2", lt="400m")

# Spec: BW > 1GHz
set_spec(client, "BW", "AC", gt="1G")
```

## Write — Variables

| Python | SKILL | Description |
|--------|-------|-------------|
| `set_var(client, name, value, *, type_name="", type_value="", ses="")` | `maeSetVar` | Set global variable or corner sweep |
| `get_var(client, name, *, ses="")` | `maeGetVar` | Get variable value |

```python
set_var(client, "vdd", "1.35")
get_var(client, "vdd")  # => '"1.35"'

# Corner sweep
set_var(client, "vdd", "1.2 1.4", type_name="corner", type_value='("myCorner")')
```

## Write — Parameters (Parametric Sweep)

| Python | SKILL | Description |
|--------|-------|-------------|
| `get_parameter(client, name, *, type_name="", type_value="", ses="")` | `maeGetParameter` | Read parameter value |
| `set_parameter(client, name, value, *, type_name="", type_value="", ses="")` | `maeSetParameter` | Add/update parameter |

```python
set_parameter(client, "cload", "1p")
set_parameter(client, "cload", "1p 2p", type_name="corner", type_value='("myCorner")')
```

## Write — Environment & Simulator Options

| Python | SKILL | Description |
|--------|-------|-------------|
| `set_env_option(client, test, options, *, ses="")` | `maeSetEnvOption` | Set model files, view lists, etc. |
| `set_sim_option(client, test, options, *, ses="")` | `maeSetSimOption` | Set reltol, temp, gmin, etc. |

```python
# Change model file section
set_env_option(client, "TRAN2",
    '(("modelFiles" (("/path/model.scs" "ff"))))')

# Change temperature
set_sim_option(client, "TRAN2", '(("temp" "85"))')
```

## Write — Corners

| Python | SKILL | Description |
|--------|-------|-------------|
| `set_corner(client, name, *, disable_tests="", ses="")` | `maeSetCorner` | Create/modify corner |
| `load_corners(client, filepath, *, sections="corners", operation="overwrite")` | `maeLoadCorners` | Load corners from CSV |

```python
set_corner(client, "myCorner", disable_tests='("AC" "TRAN")')
load_corners(client, "my_corners.csv")
```

## Write — Run Mode & Job Control

| Python | SKILL | Description |
|--------|-------|-------------|
| `set_current_run_mode(client, run_mode, *, ses="")` | `maeSetCurrentRunMode` | Switch run mode |
| `set_job_control_mode(client, mode, *, ses="")` | `maeSetJobControlMode` | Set Local/LSF/etc. |
| `set_job_policy(client, policy, *, test_name="", job_type="", ses="")` | `maeSetJobPolicy` | Set job policy |

```python
set_current_run_mode(client, "Single Run, Sweeps and Corners")
set_job_control_mode(client, "Local")
```

## Write — Simulation

| Python | SKILL | Description |
|--------|-------|-------------|
| `run_simulation(client, *, ses="")` | `maeRunSimulation` | Run (async) |
| `wait_until_done(client, timeout=300)` | `maeWaitUntilDone` | Block until done |

```python
run_simulation(client)
wait_until_done(client, timeout=600)
```

## Write — Export

| Python | SKILL | Description |
|--------|-------|-------------|
| `create_netlist_for_corner(client, test, corner, output_dir)` | `maeCreateNetlistForCorner` | Export netlist for one corner |
| `export_output_view(client, filepath, *, view="Detail")` | `maeExportOutputView` | Export results to CSV |
| `write_script(client, filepath)` | `maeWriteScript` | Export setup as SKILL script |

```python
create_netlist_for_corner(client, "TRAN2", "myCorner_2", "./myNetlistDir")
export_output_view(client, "./results.csv")
write_script(client, "mySetupScript.il")
```

## Write — Migration

| Python | SKILL | Description |
|--------|-------|-------------|
| `migrate_adel_to_maestro(client, lib, cell, state)` | `maeMigrateADELStateToMaestro` | ADE L → Maestro |
| `migrate_adexl_to_maestro(client, lib, cell, view="adexl", *, maestro_view="maestro")` | `maeMigrateADEXLToMaestro` | ADE XL → Maestro |

```python
migrate_adel_to_maestro(client, "myLib", "myCell", "spectre_state1")
migrate_adexl_to_maestro(client, "myLib", "myCell")
```

## Write — Save

| Python | SKILL | Description |
|--------|-------|-------------|
| `save_setup(client, lib, cell, *, ses="")` | `maeSaveSetup` | Save maestro to disk |

```python
save_setup(client, "myLib", "myCell", ses=ses)
```
