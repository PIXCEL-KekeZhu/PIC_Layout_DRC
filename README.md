# PIC Layout DRC

A Python toolkit for creating, viewing, and running Design Rule Checks (DRC) on **Photonic Integrated Circuit (PIC)** layouts using [KLayout](https://www.klayout.de/) and [Nazca](https://nazca-design.org/).

---

## Project Structure

```
PIC_Layout_DRC/
├── py_klayout_example.py   # KLayout Python API layout example
├── example.py              # Nazca layout example
├── klayout_opengds.py      # Open a GDS file in KLayout GUI
├── klayout_drc.py          # Run DRC on a GDS file
├── drc_rules/
│   └── pic_drc.drc         # KLayout DRC rules (Ruby script)
├── layout_gds/             # Generated GDS output files
├── drc_outputs/            # DRC report output files (.lyrdb)
└── .env                    # Private config (not tracked by git)
```

---

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- [KLayout](https://www.klayout.de/build.html) (desktop app, installed separately)

Install Python dependencies:

```bash
uv sync
```

---

## Configuration

Create a `.env` file in the project root (this file is private and not pushed to GitHub):

```
KLAYOUT_EXE=C:\Users\<your-username>\AppData\Roaming\KLayout\klayout_app.exe
```

On macOS, this is not needed — KLayout is found automatically at `/Applications/klayout.app`.

---

## Usage

### 1. Generate a GDS layout

Using the KLayout Python API:

```bash
uv run py_klayout_example.py
```

Using Nazca:

```bash
uv run example.py
```

GDS files are saved to `layout_gds/`.

---

### 2. Open a GDS file in KLayout

```bash
uv run klayout_opengds.py layout_gds/py_klayout_example.gds
```

Omit the argument to open the default file:

```bash
uv run klayout_opengds.py
```

---

### 3. Run DRC

```bash
uv run klayout_drc.py layout_gds/py_klayout_example.gds
```

- DRC rules are loaded from `drc_rules/pic_drc.drc`
- Reports are saved to `drc_outputs/<filename>_drc.lyrdb`
- KLayout opens automatically with the GDS and DRC report loaded
- Thread count is set automatically from your CPU core count

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

---

## Private Folders

The following are excluded from version control:

| Folder / File | Reason |
|---------------|--------|
| `.env` | Contains local KLayout path |
| `PIXCEL/` | Private project files |
