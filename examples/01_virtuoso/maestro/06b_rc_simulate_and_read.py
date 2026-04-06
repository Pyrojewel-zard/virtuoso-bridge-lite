#!/usr/bin/env python3
"""Step 2: Run simulation, open GUI, wait, read results, export waveforms.

Prerequisite: run 06a_rc_create.py first.

Flow:
1. Background session → start simulation (async)
2. Open Maestro GUI (while simulation is running)
3. Poll spectre processes until done (non-blocking, LSCS parallel)
4. Read results + export waveforms via GUI session
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import (
    open_session, close_session, run_simulation, wait_until_done,
    read_results, export_waveform,
)

LIB = "PLAYGROUND_LLM"
CELL = "TB_RC_FILTER"


def parse_wave_file(path: str) -> list[tuple[float, float]]:
    pairs = []
    for line in Path(path).read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                pairs.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return pairs


def main() -> int:
    client = VirtuosoClient.from_env()
    print(f"[info] {LIB}/{CELL}")
    t_total = time.time()

    # 1. Start simulation (background session, async)
    session = open_session(client, LIB, CELL)
    t0 = time.time()
    run_simulation(client, session=session)
    print(f"[sim] Started ({time.time() - t0:.1f}s)")

    # 2. Open GUI while simulation runs
    client.execute_skill(
        f'deOpenCellView("{LIB}" "{CELL}" "maestro" "maestro" nil "r")')
    client.execute_skill('maeMakeEditable()')
    print("[gui] Maestro opened")

    # 3. Wait for simulation (poll spectre processes, non-blocking)
    print("[sim] Waiting...")
    wait_until_done(client, timeout=600)
    elapsed_sim = time.time() - t0
    print(f"[sim] Done ({elapsed_sim:.1f}s)")

    # Close background session (simulation done, GUI session takes over)
    close_session(client, session)

    # Find GUI session
    r = client.execute_skill('''
let((s) s = nil
  foreach(x maeGetSessions() unless(s when(maeGetSetup(?session x) s = x)))
  s)
''')
    gui_session = (r.output or "").strip('"')

    # 4. Read results
    print("\n=== Results ===")
    results = read_results(client, gui_session, lib=LIB, cell=CELL)
    if results:
        for key, (expr, raw) in results.items():
            print(f"[{key}] {expr}")
            print(f"  {raw}")

    # 5. Export waveforms
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get history name from results
    yield_expr = results.get("maeGetOverallYield", ("", ""))[0]
    hm = re.search(r'Interactive\.\d+', yield_expr)
    history = hm.group(0) if hm else ""

    if history:
        print("\n=== Waveforms ===")
        mag_file = str(output_dir / "rc_ac_mag_db.txt")
        export_waveform(client, gui_session, 'dB20(mag(v("/OUT")))',
                        mag_file, analysis="ac", history=history)
        print(f"AC magnitude: {mag_file}")

        phase_file = str(output_dir / "rc_ac_phase.txt")
        export_waveform(client, gui_session, 'phase(v("/OUT"))',
                        phase_file, analysis="ac", history=history)
        print(f"AC phase: {phase_file}")

        # Quick comparison
        data = parse_wave_file(mag_file)
        if data:
            print(f"\n=== {len(data)} frequency points ===")
            for target in [1e6, 1e8, 1e9, 1e10]:
                closest = min(data, key=lambda p: abs(p[0] - target))
                print(f"  {target:.0e} Hz: {closest[1]:.2f} dB")
            for i, (f, db) in enumerate(data):
                if db <= -3.0:
                    if i > 0:
                        f_prev, db_prev = data[i - 1]
                        ratio = (-3.0 - db_prev) / (db - db_prev)
                        f_3db = f_prev + ratio * (f - f_prev)
                    else:
                        f_3db = f
                    print(f"  f_3dB = {f_3db:.3e} Hz")
                    break

    print(f"\n[total] {time.time() - t_total:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
