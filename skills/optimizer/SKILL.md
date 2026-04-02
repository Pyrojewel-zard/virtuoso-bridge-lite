---
name: optimizer
description: "Circuit parameter optimization skill for analog design using Spectre simulations. Use this skill when the user wants to: (1) optimize transistor sizing, biasing, or any continuous circuit parameter to minimize/maximize performance metrics (power, speed, noise, FOM); (2) set up an optimization loop around Spectre simulations via virtuoso-bridge; (3) understand the optimization pattern — design variables, objective function, simulation, result extraction, convergence. TuRBO (Trust-Region Bayesian Optimization) is the default algorithm, but the pattern applies to any optimizer."
---

# Circuit Optimizer Skill

> **Do not modify skill files during normal use.**
> Write all optimization scripts and results into the **project working directory**.
> Only edit skill-internal files when the user explicitly asks to improve or extend the skill.

---

## Overview

This skill defines the pattern for optimizing analog circuit parameters through simulation. The optimizer drives a loop:

1. **Choose** parameter values (transistor widths, bias currents, capacitor sizes, etc.)
2. **Simulate** the circuit with those values (via Spectre through virtuoso-bridge)
3. **Extract** performance metrics from results (power, delay, noise, gain, etc.)
4. **Decide** the next set of parameters based on all previous results
5. **Repeat** until budget is exhausted or target is met

The default algorithm is **TuRBO** (Trust-Region Bayesian Optimization), which is sample-efficient for expensive simulations. But the pattern works with any optimizer — scipy.optimize, Optuna, genetic algorithms, or even manual sweeps.

---

## Prerequisites

```bash
# For TuRBO (default optimizer):
pip install torch gpytorch
pip install -e TuRBO/    # if using local TuRBO repo

# Verify:
python -c "from turbo import Turbo1; print('OK')"
```

For other optimizers, install their respective packages.

---

## General Pattern

### Step 1 — Define design variables and bounds

```python
import numpy as np

PARAM_NAMES = ["W_tail", "W_inp", "W_lat_n", ...]
LB = np.array([0.5,  0.5,  0.5, ...])    # lower bounds
UB = np.array([10.,  10.,  6.,  ...])     # upper bounds
```

All parameters must be **continuous** and use **consistent units**.

### Step 2 — Write the objective function with Spectre simulation

```python
from virtuoso_bridge.spectre.runner import SpectreSimulator

sim = SpectreSimulator.from_env(work_dir="./opt_output")

def objective(x: np.ndarray) -> float:
    """Run Spectre simulation with parameters x, return scalar to minimize."""
    # 1. Write parameters into netlist
    netlist = generate_netlist(x, PARAM_NAMES)

    # 2. Run Spectre
    try:
        result = sim.run_simulation(netlist, {})
    except Exception as e:
        print(f"  Simulation error: {e}")
        return 1e6    # penalty

    # 3. Extract metrics
    power = extract_power(result)
    delay = extract_delay(result)

    if power is None or delay is None:
        return 1e6

    return power * delay   # minimize power-delay product
```

**Critical rules:**
- Always return a **scalar float**
- Return a **large penalty** (1e6) on simulation failure — never `nan` or `inf`
- The optimizer **minimizes** — to maximize a metric, negate it

### Step 3 — Run optimization

```python
# Using TuRBO:
from turbo import Turbo1

turbo = Turbo1(
    f          = objective,
    lb         = LB,
    ub         = UB,
    n_init     = 2 * len(LB),    # initial random samples
    max_evals  = 100,             # total simulation budget
    batch_size = 1,
    use_ard    = True,
    device     = "cpu",
    dtype      = "float64",
)
turbo.optimize()

# Using scipy (simpler, no GP overhead):
from scipy.optimize import minimize
result = minimize(objective, x0=(LB+UB)/2, bounds=list(zip(LB, UB)), method="Nelder-Mead")
```

### Step 4 — Extract results

```python
X  = turbo.X
fX = turbo.fX.flatten()

valid  = fX < 1e5
best_x = X[valid][np.argmin(fX[valid])]
best_f = fX[valid].min()

for name, val in zip(PARAM_NAMES, best_x):
    print(f"  {name} = {val:.3f}")
```

---

## Connecting to Spectre via virtuoso-bridge

The optimizer needs to run Spectre simulations. Two approaches:

**Approach A: Modify netlist directly** (simpler)
```python
def generate_netlist(x, param_names):
    template = Path("tb_template.scs").read_text()
    for name, val in zip(param_names, x):
        template = template.replace(f"@@{name}@@", f"{val:.6g}")
    out = Path(f"opt_output/tb_run.scs")
    out.write_text(template)
    return out
```

**Approach B: Use Virtuoso schematic** (more realistic)
```python
from virtuoso_bridge import BridgeClient
client = BridgeClient()

def apply_params(x, param_names):
    for name, val in zip(param_names, x):
        # Set instance parameter in schematic
        client.execute_skill(f'setProp(getInstance("MN") "{name}" {val})')
    # Export netlist
    client.execute_skill('exportNetlist()')
```

---

## Common Objective Functions

| Goal | Expression | Notes |
|---|---|---|
| Power-delay product | `power * delay` | Classic FOM |
| Noise-power FOM | `power * noise**2` | For comparators/ADCs |
| Maximize gain-bandwidth | `-(gain_db + 20*log10(bw))` | Negate to minimize |
| Area proxy | `sum(W * L for each device)` | Combine with performance |
| Multi-objective | `w1*power + w2*delay + w3*noise` | Tune weights |

**Soft constraint penalties:**
```python
obj = power * delay
if noise > 500e-6:
    obj += 1e3 * (noise - 500e-6)**2    # penalty, not rejection
return obj
```

---

## Convergence Plot

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_convergence(fX, out_path, title="Optimization Convergence"):
    valid = fX < 1e5
    best = np.full_like(fX, np.nan)
    cur = np.inf
    for i, v in enumerate(fX):
        if valid[i] and v < cur:
            cur = v
        best[i] = cur
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.scatter(np.where(valid)[0], fX[valid], s=20, alpha=0.5, label="Each eval")
    ax.plot(best, color="crimson", lw=2, label="Best so far")
    ax.set_xlabel("Evaluation")
    ax.set_ylabel("Objective")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
```

---

## File Conventions

```
optimization/
├── optimize_{circuit}.py         — main optimization script
├── results/
│   ├── opt_results.json          — per-eval log
│   ├── opt_summary.json          — best result
│   └── convergence.png           — convergence figure
```

Log results **after every evaluation** — a crash loses at most one eval.

---

## TuRBO-Specific Notes

TuRBO (Trust-Region Bayesian Optimization, NeurIPS 2019) is designed for **expensive, noise-free, black-box functions** — exactly what circuit simulation is.

| Variant | When to use |
|---|---|
| `Turbo1` | Single trust region. Best for <200 evals or slow simulations (>30s each). |
| `TurboM` | Multiple trust regions. Better global coverage for larger budgets. |

```python
from turbo import Turbo1, TurboM

# Single trust region (default choice)
turbo = Turbo1(f=objective, lb=LB, ub=UB, n_init=2*len(LB), max_evals=100,
               batch_size=1, use_ard=True, device="cpu", dtype="float64")

# Multiple trust regions (larger budget)
turbo = TurboM(f=objective, lb=LB, ub=UB, n_init=10, max_evals=300,
               n_trust_regions=5, batch_size=1, use_ard=True, device="cpu", dtype="float64")
```
