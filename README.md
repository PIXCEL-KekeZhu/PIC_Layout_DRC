# PIC Layout DRC

A Python toolkit for creating, viewing, running Design Rule Checks (DRC), and visualizing **Photonic Integrated Circuit (PIC)** layouts in 2.5D using [KLayout](https://www.klayout.de/) and [Nazca](https://nazca-design.org/).

---

## Project Structure

```
PIC_Layout_DRC/
├── py_klayout_example.py       # KLayout Python API layout example
├── klayout_PIC_example.py      # Full MZI PIC layout (MMI, phase shifter, bond pads, GC)
├── klayout_simple_MZI.py       # Minimal MZI layout
├── nazca_example.py            # Nazca layout assignments
├── nazca_online_tutorial.py    # Nazca online tutorial examples
│
├── klayout_opengds.py          # Open GDS file(s) in KLayout Editor
├── klayout_DRCCheck.py         # Run DRC (any rule script) and open results in KLayout
├── klayout_ShowDRCResults.py   # Open latest or specified DRC report in KLayout
├── klayout_2p5DViews.py        # Generate 2.5D view macro and open GDS in KLayout
├── klayout_utils.py            # Shared KLayout utilities (env, launch, process check)
│
├── drc_rules/
│   ├── pic_drc.drc             # General PIC DRC rules (width, spacing, enclosure, metal)
│   └── pic_freeform.drc        # Freeform / bent waveguide DRC (bend radius, sharp corners)
├── layout_gds/                 # Generated GDS output files
├── drc_outputs/                # DRC report (.lyrdb) and DRC layer GDS files
├── vendor/
│   └── nazca/                  # Nazca-Design 0.6.1 (local source)
└── .env                        # Private config (not tracked by git)
```

---

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- [KLayout](https://www.klayout.de/build.html) (desktop app, installed separately)

Install Python dependencies:

```bash
uv sync
```

Nazca is bundled in `vendor/nazca/` — no separate install needed.

---

## Configuration

Create a `.env` file in the project root (private, not pushed to GitHub):

```
KLAYOUT_EXE=C:\Users\<your-username>\AppData\Roaming\KLayout\klayout_app.exe
```

On macOS this is not needed — KLayout is found automatically. On Windows, `klayout_utils.py` also auto-detects the standard install path as a fallback.

---

## Usage

### 1. Generate a GDS layout

Using the KLayout Python API:

```bash
uv run py_klayout_example.py
```

Using the full MZI PIC example (MMI splitter/combiner, S-bend arms, thermo-optic phase shifter, bond pads, grating couplers, photodetector pad):

```bash
uv run klayout_PIC_example.py
```

Using Nazca:

```bash
uv run nazca_example.py
```

GDS files are saved to `layout_gds/`.

---

### 2. Open a GDS file in KLayout (Editor)

```bash
uv run klayout_opengds.py layout_gds/klayout_PIC_example.gds
uv run klayout_opengds.py          # opens the latest GDS from layout_gds/
```

- If KLayout is **not running**: launches KLayout Editor with the file
- If KLayout is **already running**: opens the file in a new panel of the same instance

---

### 3. 2.5D View

Generates a `pixcel_mzi_view.lyd25` macro and opens the GDS in KLayout:

```bash
uv run klayout_2p5DViews.py layout_gds/klayout_PIC_example.gds
uv run klayout_2p5DViews.py        # opens the latest GDS
```

The macro is installed to `~/KLayout/d25/pixcel_mzi_view.lyd25`. After KLayout opens:

1. **Tools → 2.5D View → pixcel_mzi_view**

PIC layer stack used for 2.5D extrusion:

| Layer | Material       | z-start (µm) | z-stop (µm) |
|-------|---------------|-------------|------------|
| 2/0   | Cladding (SiO2) | −1.0       | +2.0       |
| 1/0   | Waveguide (Si)  | 0.0        | +0.22      |
| 3/0   | Metal           | +0.5       | +1.0       |

> **Note:** If KLayout is already running, close it first so the new macro is loaded at startup.

---

### 4. Run DRC

**General PIC rules** (width, spacing, cladding enclosure, metal overlap):

```bash
uv run klayout_DRCCheck.py layout_gds/klayout_PIC_example.gds
```

**Freeform / bent waveguide rules** (bend radius, sharp corners, curved spacing):

```bash
uv run klayout_DRCCheck.py layout_gds/klayout_PIC_example.gds --drc drc_rules/pic_freeform.drc
```

- `--drc` selects the rule script; defaults to `drc_rules/pic_drc.drc`
- Report saved to `drc_outputs/<gds>_<script>.lyrdb`
- Violation markers saved to `drc_outputs/<gds>_<script>_layers.gds` (original shapes merged in)
- KLayout opens automatically with violations highlighted
- Thread count set automatically from `os.cpu_count()`

---

### 5. View existing DRC results

```bash
uv run klayout_ShowDRCResults.py                                                          # latest report
uv run klayout_ShowDRCResults.py drc_outputs/klayout_PIC_example_pic_freeform.lyrdb      # explicit report
uv run klayout_ShowDRCResults.py drc_outputs/klayout_PIC_example_pic_freeform_layers.gds # or the GDS
```

Automatically pairs the `.lyrdb` with its companion `_layers.gds` regardless of DRC script name.
The companion GDS already contains the original layout shapes, so no separate source file is needed.

---

## MZI PIC Layout (`klayout_PIC_example.py`)

```
  y(µm)
   65 ┤   ┌──────────────┐         ┌──────────────┐
      │   │  V+ bond pad │         │ GND bond pad │
   25 ┤   │   (40×40µm)  ├─ lead ──┤   (40×40µm)  │
      │   └──────┬───────┘         └───────┬──────┘
   21 ┤          └──────── heater ──────────┘
   20 ┤  ╭────────────────────────────────────────╮  upper arm
      │ ╱  S-bend                         S-bend  ╲
    0 ┼─░░░░░──[MMI]────────────────────[MMI]──░░░░░──[PD pad]
      │ ╲  S-bend                         S-bend  ╱
  -20 ┤  ╰────────────────────────────────────────╯  lower arm
      └──┬────┬──┬───┬──────────────────┬───┬──┬────┬──┬──── x(µm)
         0   20 35  41  61           141 161 167   207 232
```

| Component              | x-range (µm) | Layer |
|------------------------|-------------|-------|
| Input grating coupler  | 0 .. 20     | 1/0   |
| MMI splitter (1×2)     | 35 .. 41    | 1/0   |
| Upper / lower arms     | 61 .. 141   | 1/0   |
| Heater stripe          | 76 .. 126   | 3/0   |
| V+ / GND bond pads     | 56..96 / 106..146 | 3/0 |
| MMI combiner (2×1)     | 161 .. 167  | 1/0   |
| Output grating coupler | 187 .. 207  | 1/0   |
| Photodetector pad      | 212 .. 252  | 3/0   |
| SiO2 cladding          | full chip   | 2/0   |

---

## DRC Rules

### `drc_rules/pic_drc.drc` — General PIC rules

| Rule   | Layer           | Description                                |
|--------|-----------------|--------------------------------------------|
| WG.W1  | Waveguide (1/0) | Minimum width ≥ 0.3 µm                    |
| WG.S1  | Waveguide (1/0) | Minimum spacing ≥ 0.2 µm                  |
| WG.A1  | Waveguide (1/0) | Minimum area ≥ 0.1 µm²                    |
| WG.E1  | Waveguide (1/0) | Must be enclosed by cladding by ≥ 1.0 µm  |
| M.W1   | Metal (3/0)     | Minimum width ≥ 0.5 µm                    |
| M.S1   | Metal (3/0)     | Minimum spacing ≥ 0.5 µm                  |
| M.OL1  | Metal (3/0)     | Must not overlap waveguide                 |

### `drc_rules/pic_freeform.drc` — Freeform / bent waveguide rules

| Rule       | GDS layer | Description                                              |
|------------|-----------|----------------------------------------------------------|
| WG.W1      | (1,1)     | Minimum waveguide width ≥ 0.35 µm                        |
| WG.W2      | (1,2)     | Maximum waveguide width ≤ 3.0 µm                         |
| WG.SP1     | (1,3)     | Minimum waveguide spacing ≥ 0.2 µm                       |
| WG.A1      | (1,4)     | Minimum area — removes slivers and orphaned fragments     |
| WG.NOTCH   | (1,5)     | Inward notch / pinch on waveguide edges                  |
| WG.AC1     | (1,6)     | Acute corner (< 45°) — near-zero bend radius             |
| WG.BR1     | (1,10)    | Bend radius < 5 µm at waveguide center-line              |
| WG.BR2     | (1,11)    | Critical bend radius < 2 µm — severe loss expected       |
| WG.SP2     | (1,12)    | Bent waveguide spacing < 0.4 µm inside bend zones        |
| WG.E1      | (2,1)     | Cladding enclosure < 1.0 µm                              |
| WG.E2      | (2,2)     | Bend outer-edge cladding < 1.5 µm                        |
| RIB.W1     | (4,1)     | Rib slab width < 0.5 µm *(rib WG only)*                  |
| RIB.OVL1   | (4,2)     | Waveguide core extends outside etch layer *(rib WG only)*|
| RIB.ENC1   | (4,3)     | Etch enclosure < 0.3 µm *(rib WG only)*                  |
| RIB.SP1    | (4,4)     | Rib slab spacing < 0.3 µm *(rib WG only)*                |

Bend radius is checked via **morphological opening**: the waveguide is eroded by `R_min − W_nom/2` then dilated back; regions that disappear had an inner-edge bend radius tighter than `R_min`.

DRC violation polygons are written to named layers in the companion `_layers.gds`.

---

## Private Folders

The following are excluded from version control:

| Folder / File   | Reason                              |
|-----------------|-------------------------------------|
| `.env`          | Contains local KLayout executable path |
| `PIXCEL/`       | Private project files               |
| `nazca_course.py` | Private course exercises          |
