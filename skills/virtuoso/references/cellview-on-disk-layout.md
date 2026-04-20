# Cadence DFII Cellview On-Disk Layout

Reference for what lives inside a library/cell/view on disk — which files
are text, which are binary, which tool to use to modify them safely.

Written for IC6.1.8. Formats are stable across minor versions.

## Three-tier structure

```
<Project>/
└── <LIB>/                        # library (entry in cds.lib)
    ├── cdsinfo.tag               # library-level metadata
    └── <CELL>/                   # cell
        ├── data.dm               # (optional) cell-level prop bag
        ├── schematic/            # view
        ├── symbol/               # view
        ├── config/               # view (may not exist)
        ├── maestro/              # view (only when ADE Assembler is used)
        ├── layout/               # view
        └── ...                   # other views
```

## Cell root

### `<CELL>/data.dm` (optional)

DFII cell-level property bag. Stores view enumeration, CDF parameters,
other cell-wide metadata. Same binary format as view-level `data.dm`
(see §"data.dm binary format"). **Not always present** — Cadence
reconstructs views by directory scan when absent.

## Schematic view

```
schematic/
├── sch.oa                                # OpenAccess DB (binary)
├── data.dm                               # view-level prop bag
├── master.tag                            # view identity tag
├── thumbnail_128x128.png                 # auto-generated preview
├── sch.oa.cdslck                         # (edit-only) write lock
└── sch.oa.cdslck.<distro>.<host>.<pid>   # (edit-only) lock detail, hard-link to above
```

- `sch.oa` — OA binary. **Only modify via DFII SKILL API** (`dbCreateInst`,
  `dbCopyCellView`, etc.). Text tools corrupt it.
- `thumbnail_128x128.png` — harmless to delete; regenerated on next save.

## Symbol view

```
symbol/
├── symbol.oa
├── data.dm
├── master.tag
└── symbol.oa.cdslck{,.<...>}   # same lock family
```

Same format as `schematic/`, just a different OA cellview type.

## Config view

```
config/
├── expand.cfg          # text — design binding + sub-cell binding rules
├── master.tag
└── expand.cfg%         # (SOS sources only) "not checked out" marker
```

`expand.cfg` (text):

```
config <top_cell>;
design <LIB>.<CELL>:<view>;
liblist <libs>;
viewlist <views>;
stoplist <views>;
cell <LIB>.<SUB_CELL> binding :<view>;     # per-subcell overrides
endconfig
```

Editable with `sed`. The `design` line is the authoritative
top-level binding; rewrite it when renaming cells across libs.

### Config-less testbench

Not every TB has a `config/` view. Maestro can bind directly to
`schematic` — check `<option>view` in `maestro.sdb`.

## Maestro view

```
maestro/
├── maestro.sdb                # text XML — setup (tests, corners, history)
├── active.state               # text XML — current test details (analyses, outputs, vars)
├── data.dm                    # view-level prop bag
├── master.tag
├── maestro.sdb.cdslck         # (edit-only) write lock
├── namedStimuli/              # XML stimulus definitions (often empty)
├── test_states/               # saved test snapshots (XML, same schema as active.state)
├── states/                    # (rare) saved setup checkpoints
├── documents/                 # (rare) user notes
└── results/maestro/           # (only after runs) per-run artifacts
    ├── Interactive.N.log      # text run summary
    ├── Interactive.N.msg.db   # SQLite (table `logs`: level/tool/message)
    ├── Interactive.N.rdb      # SQLite (scalar outputs)
    └── Interactive.N/         # (optional) netlist + psf + sharedData
```

### `maestro.sdb`

XML skeleton:

```xml
<setupdb version="6">maestro
  <active>
    <tests><test enabled="1">TestName
      <tooloptions>
        <option>cell  <value>...</value></option>
        <option>lib   <value>...</value></option>
        <option>view  <value>config|schematic</value></option>
      </tooloptions>
    </test></tests>
    <vars>...</vars>
  </active>
  <history>
    <historyentry>Interactive.N<timestamp>...</timestamp>...</historyentry>
  </history>
</setupdb>
```

`<active>/<tests>/<test>/<tooloptions>` holds the authoritative DUT
binding. `<history>` is a run log; safe to trim (Cadence rescans
`results/maestro/` at open time).

### `active.state`

Per-test detail — one `<Test Name="...">` block per test, each containing:

- `<component Name="adeInfo">/<field Name="designInfo">` — `(LIB CELL VIEW spectre)` tuple
- `<analyses>` — `<analysis Name="ac|dc|tran|pss|pnoise|pac|noise">` blocks, each with an `<field Name="enable">` symbol
- `<outputs>` — `<field Name="outputList_N">` structs, sequentially numbered; each has a `uniqueName`, `expression`, `plot`, `save`, `index`

When pruning outputs or analyses, renumber `outputList_N` sequentially
and keep `<field Name="index">` in sync.

### Sidecar directories

| Dir | Contents | Safe to wipe? |
|-----|----------|---------------|
| `test_states/` | Auto-saved per-run state (`Interactive.N.state`) + user-saved named states | Yes (Interactive.*); no (user names) |
| `namedStimuli/` | `stimuli.xml` with digital bit-stream configs | Don't touch |
| `states/` | URL-encoded directories for "automatic starting point" | Yes |
| `documents/` | User notes | Yes |
| `results/maestro/` | Run artifacts | Yes (Cadence allocates a fresh `Interactive.N` after scan) |

## `data.dm` binary format

Layout (IC6.1.8):

```
+0x000  magic      67 45 23 01        # 0x01234567 LE
        version    05 00 03 00
+0x010  offset table, 8-byte LE integers, each pointing into string pool
...
+0x5xx  string pool: NUL-terminated ASCII, 8-byte aligned
        "viewSubType\0" "maestro\0"
        "testName\0"    "<test_name>\0"
        "22.60.077\0"   # tool version
        ...
```

**The offset table holds absolute byte positions.** Any change to string
length shifts the pool, invalidates every downstream offset, and causes
`DB-260009: dbOpenBag: Fail to open prop. bag` on next open.

**Do not sed `data.dm`.** To modify:
- Clone a cell: `cp` the file verbatim (embedded strings are metadata
  hints; Cadence treats filesystem path as authoritative).
- Programmatic changes: use DFII — `dbOpenBag("a")` +
  `dbCreateProp`/`dbReplaceProp` + `dbSavePropBag`. Cadence rebuilds
  the offset table on save.

## Lock files

Cadence creates `<primary_file>.cdslck` on write-open:

```
sch.oa.cdslck                          # short lock: hostname:user:pid:session
sch.oa.cdslck.RHEL30.thu-wei.212340    # detailed "Lock-Stake" text, hard-linked to above
```

The two files share an inode (`ls -la` shows link count 2). Content of
the detailed one:

```
LockStakeVersion               1.1
LoginName                      <user>
HostName                       <host>
ProcessIdentifier              <pid>
ProcessCreationTime_UTC        <timestamp>
ReasonForPlacingEditLock       OpenAccess edit lock
FilePathUsedToEditLock         <absolute path>
TimeEditLocked                 <timestamp>
```

### What to do with stray locks

- **`.cdslck.<distro>.<host>.<pid>` pointing at your own Virtuoso PID**
  — process-level edit claim, persists until Virtuoso exits. Harmless.
- **`.cdslck.<distro>.<other_user>.<pid>` pointing at someone else** —
  source-library lock that came along via `cp -r`. Stale. Remove: `rm -f`.
- **`maestro.sdb.cdslck`** — maestro session lock; cleared by
  `maeCloseSession(?forceClose t)` when the session closes cleanly. If
  it persists after close, the session didn't shut down fully; `rm` is
  safe if `maeGetSessions()` shows no active session.

### Avoid copying them in the first place

`rsync -a --exclude='*.cdslck' --exclude='*.cdslck.*' src/ dst/` keeps
other users' stale locks off the destination from the start. Once a
stale lock touches disk, Cadence's DD may cache "this cellview is being
edited by someone else", after which `dbOpenCellViewByType('a')`
silently returns nil.

## Cliosoft SOS source libraries

Libraries managed by Cliosoft SOS look distinctive on disk:

- `master.tag` is a symlink into `/.../sos_cache/<LIB>#<CELL>#<view>_<N>_sospack/PACK/master#tag_<N>`
- Files like `expand.cfg%`, `sch.oa%` — `%`-suffix means "managed by SOS,
  currently not checked out"
- File mode is `r--r--r--` (SOS's checked-in state)
- Ownership may be a different user

Detection — one command:

```bash
ls -la <cell>/*/master.tag
```

If any `master.tag` is a symlink into `sos_cache` or `#_sospack/`, the
source is SOS-managed. Handle accordingly:

- Do not preserve `%`-marker files when cloning — Cadence refuses to
  make `%`-marked views editable.
- Dereference symlink `master.tag` into a real file — SOS cache can
  be pruned, making the symlink dangle.
- `chmod -R u+w` after cp — SOS defaults to read-only.

## Format summary table

| File | Type | Safe to sed? | How to modify |
|------|------|--------------|---------------|
| `sch.oa`, `symbol.oa`, `layout.oa` | OA binary | No | DFII SKILL API |
| `expand.cfg` | Text | Yes | `sed` or direct edit |
| `maestro.sdb`, `active.state`, `test_states/*.state` | XML | Yes (simple), lxml (complex) | `sed` for literals, `lxml` for structural changes |
| `namedStimuli/*.xml` | XML | Yes | `sed` |
| `states/*.sdb`, `states/<dir>/active.state` | XML | Yes | `sed` |
| `data.dm` (cell-level or view-level) | DFII binary prop bag | **No** | `cp` verbatim, or DFII API |
| `master.tag` | Text (or symlink if SOS) | Yes | Dereference symlinks before editing |
| `*.cdslck`, `*.cdslck.*` | Text (Lock-Stake format) | Don't edit | `rm -f` stale ones |
| `*%` (trailing `%`) | SOS marker | Don't edit | `rm -f` when cloning out of SOS |
| `thumbnail_128x128.png` | PNG | Don't edit | Cadence regenerates |
| `*.log` (in results/) | Text | Read-only | n/a |
| `*.msg.db`, `*.rdb` | SQLite 3 | Don't edit | `sqlite3` to query |

## Debug quick-reference

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `DB-260009: dbOpenBag: Fail to open prop. bag` | `data.dm` edited with sed | Restore from source with `cp` |
| `maeGetEnabledAnalysis` returns nil, `maeGetSetup` ok | `active.state` test name mismatches `maestro.sdb` | sed cell name in `active.state` to match |
| `dbOpenCellViewByType(... "a")` returns nil | Stale `.cdslck.<user>.<pid>` from someone else | `rm -f` the lock |
| `maeMakeEditable` refuses | `*%` SOS marker still present | `rm -f '<view>/*%'` |
| Config view silently read-only | Same as above, or SOS-owned file perms | `rm -f *%` and `chmod -R u+w <cell>` |
| History picker shows runs for a different TB | `results/` copied from source | `rm -rf results/` and recreate empty |
