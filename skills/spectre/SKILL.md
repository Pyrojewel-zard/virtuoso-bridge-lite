---
name: spectre
description: "Run Cadence Spectre simulations remotely via virtuoso-bridge: upload netlists, execute, parse results."
---

# Spectre Skill

## What you can do

```python
from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args

sim = SpectreSimulator.from_env(
    spectre_args=spectre_mode_args("ax"),  # APS mode
    work_dir="./output",
    output_format="psfascii",
)
result = sim.run_simulation("tb_inv.scs", {})

print(result.status)            # ExecutionStatus.SUCCESS
print(result.data.keys())       # ['time', 'VOUT', 'VIN', ...]
print(result.data["VOUT"][:5])  # first 5 samples
print(result.errors)            # any errors
print(result.metadata)          # timings, commands, output paths
```

### With Verilog-A include files

```python
result = sim.run_simulation("tb_adc.scs", {
    "include_files": ["adc_ideal.va", "dac_ideal.va"],
})
```

### Check license before running

```python
sim = SpectreSimulator.from_env()
info = sim.check_license()
print(info["spectre_path"])  # /path/to/spectre
print(info["version"])       # spectre version string
print(info["licenses"])      # license feature availability
```

## Setup

Requires `VB_CADENCE_CSHRC` in `.env` — the cshrc that puts `spectre` in PATH and sets `LM_LICENSE_FILE`.

```bash
virtuoso-bridge status   # shows Spectre path + license status
```

## Simulation modes

```python
spectre_mode_args("spectre")  # basic Spectre
spectre_mode_args("aps")      # APS
spectre_mode_args("ax")       # APS extended (default for examples)
spectre_mode_args("cx")       # Spectre X custom
```

## Result object

- `result.status` — SUCCESS / FAILURE / ERROR
- `result.ok` — bool
- `result.data` — dict of signal name → list of values
- `result.errors` / `result.warnings` — lists of strings
- `result.metadata["timings"]` — upload, exec, download, parse times

## Examples

- `examples/02_spectre/01_veriloga_adc_dac.py` — 4-bit ADC/DAC with Verilog-A
- `examples/02_spectre/04_strongarm_pss_pnoise.py` — StrongArm comparator PSS+Pnoise

## Tips

- Use `output_format="psfascii"` for parsed waveform data
- If netlist needs path patching, write a derived netlist to the output dir, don't modify the source asset
- If simulation hangs, check `virtuoso-bridge status` for license availability
