# PIC Layout DRC

A Python toolkit for creating, viewing, and running Design Rule Checks (DRC) on **Photonic Integrated Circuit (PIC)** layouts using [KLayout](https://www.klayout.de/) and [Nazca](https://nazca-design.org/).

---

## Project Structure

```
PIC_Layout_DRC/
├── py_klayout_example.py       # KLayout Python API layout example
├── example.py                  # Nazca layout example
├── nazca_example.py            # Nazca layout assignments
├── nazca_online_tutorial.py    # Nazca online tutorial examples
│
├── klayout_opengds.py          # Open GDS file(s) in KLayout Editor
├── klayout_DRCCheck.py         # Run DRC and open results in KLayout
├── klayout_ShowDRCResults.py   # Open existing DRC report in KLayout
├── klayout_utils.py            # Shared KLayout utilities (env, launch, process check)
│
├── drc_rules/
│   └── pic_drc.drc             # KLayout DRC rules (Ruby script)
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

Using Nazca:

```bash
uv run nazca_example.py
```

GDS files are saved to `layout_gds/`.

---

### 2. Open a GDS file in KLayout (Editor)

```bash
uv run klayout_opengds.py layout_gds/py_klayout_example.gds
```

- If KLayout is **not running**: launches KLayout Editor with the file
- If KLayout is **already running**: opens the file in a new panel of the same instance
- Omit the argument to open the default file

---

### 3. Run DRC

```bash
uv run klayout_DRCCheck.py layout_gds/py_klayout_example.gds
```

- DRC rules loaded from `drc_rules/pic_drc.drc`
- Report saved to `drc_outputs/<name>_drc.lyrdb`
- DRC violation layers saved to `drc_outputs/<name>_drc_layers.gds` — named after each check rule, with original GDS layers merged in
- KLayout opens automatically with the GDS and report
- Thread count set automatically from CPU core count (`os.cpu_count()`)

---

### 4. View existing DRC results

```bash
uv run klayout_ShowDRCResults.py                                        # opens latest report
uv run klayout_ShowDRCResults.py drc_outputs/py_klayout_example_drc.lyrdb
uv run klayout_ShowDRCResults.py drc_outputs/py_klayout_example_drc_layers.gds
```

Automatically finds and opens the matching GDS, DRC layers, and report together.

---

## DRC Rules

Defined in `drc_rules/pic_drc.drc`:

| Rule | Layer | Description |
|------|-------|-------------|
| WG.W1 | Waveguide (1/0) | Minimum width ≥ 0.3 µm |
| WG.S1 | Waveguide (1/0) | Minimum spacing ≥ 0.2 µm |
| WG.A1 | Waveguide (1/0) | Minimum area ≥ 0.1 µm² |
| WG.E1 | Waveguide (1/0) | Must be enclosed by cladding by ≥ 1.0 µm |
| M.W1  | Metal (3/0)     | Minimum width ≥ 0.5 µm |
| M.S1  | Metal (3/0)     | Minimum spacing ≥ 0.5 µm |
| M.OL1 | Metal (3/0)     | Must not overlap waveguide |

DRC violation polygons are written to named layers in `_drc_layers.gds`. To add a new output layer, define it in `pic_drc.drc` and add the mapping to `DRC_LAYER_MAP` in `klayout_DRCCheck.py`.

---

## Private Folders

The following are excluded from version control:

| Folder / File | Reason |
|---------------|--------|
| `.env` | Contains local KLayout executable path |
| `PIXCEL/` | Private project files |
