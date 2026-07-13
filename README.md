# Execution Framework

A general-purpose, methodology-driven execution workspace. Define your process, mirror it into structured execution templates, log your work, and generate professional deliverables — for any domain.

---

## What It Is

The Execution Framework is a domain-agnostic workspace built around one core idea: **your methodology drives your workspace automatically**.

You define your process as a structured **YAML database** in `methodology_yaml/` — the single source of truth. The mirroring engine renders it into both your markdown methodology docs *and* a structured execution workspace with two-way linked checklists and log templates. You work through it, then the reporting engine generates HTML, Markdown, and packaged deliverables from your logs and narrative sections.

Built to work for any repeatable professional process — security, consulting, research, product, operations, or anything else.

> **Data model:** `methodology_yaml/*.yaml` is authoritative; `methodology/*.md` is generated. Edit the YAML, then regenerate (mirroring engine → Option 3). See [docs/YAML_ARCHITECTURE.md](./execution-framework/docs/YAML_ARCHITECTURE.md).

---

## Configuration

Everything domain-specific lives in `execution-framework/config/`:

| File | Controls |
|------|----------|
| `domain.ini` | Terminology (phase type, task type, contact roles), YAML source dir, excluded files |
| `report.ini` | Report title, output filename, the five narrative section labels |
| `placeholders.yaml` | Canonical `<TOKEN>` vocabulary for the Loadout Manager (empty by default) |

Change the config files to rename the framework for your domain without touching any code.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# 1. Define your methodology
#    Edit methodology/ with your phases and tasks

# 2. Mirror to execution templates
cd execution-framework/utilities/template_generator && python3 main.py
# Select Option 3 — Regenerate All

# 3. Start a workspace
# Select Option 5 — Generate Next Iteration

# 4. Do your work in execution/iteration_01/

# 5. Generate and finalize reports
cd execution-framework/utilities/reporting/reporting_engine && python3 main.py
```

---

## Demo Data

A complete demo engagement dataset is included in `execution-framework/demo-data/` — a generic product launch project with pre-filled execution notes and a finalized report. Load it to explore the full framework output without starting from scratch.

**macOS / Linux:**
```bash
cd execution-framework
cp -r demo-data/data/*      data/
cp -r demo-data/execution/* execution/
cp -r demo-data/reports/*   reports/
```

**Windows (PowerShell):**
```powershell
cd execution-framework
Copy-Item -Recurse demo-data\data\*      data\
Copy-Item -Recurse demo-data\execution\* execution\
Copy-Item -Recurse demo-data\reports\*   reports\
```

---

## Project Structure

```
execution-framework/
├── config/
│   ├── domain.ini              # Terminology, contact roles, YAML dir, excluded files
│   ├── report.ini              # Report title, filename, section labels
│   └── placeholders.yaml       # Canonical command-placeholder vocabulary (Loadout)
│
├── methodology_yaml/           # SOURCE OF TRUTH — process defined as YAML
│   ├── 01_Planning/            #   (methodology/*.md below is generated from this)
│   └── ...
│
├── methodology/                # GENERATED markdown docs (rendered from methodology_yaml/)
│   ├── 01_Planning/
│   ├── 02_Research/
│   ├── 03_Execution/
│   ├── 04_Review/
│   └── 05_Delivery/
│
├── loadout/                    # Loadout Manager quick-capture (loadout.md)
│
├── templates/                  # Pristine source templates
│   ├── data/                   # Data form templates (scope, contacts)
│   ├── execution/iteration/    # Mirrored from methodology — copy to start a workspace
│   ├── methodology/            # Methodology scaffolding reference
│   └── reports/                # Report template references
│
├── execution/                  # Active workspace iterations
│   └── iteration_01/           # Current engagement — phase folders + master log
│
├── reports/
│   └── completed/              # Generated HTML, Markdown, and deliverable ZIP
│
├── references/                 # Domain reference library
│   ├── General_Resources/
│   ├── Standards_and_Frameworks/
│   └── Domain_References/
│
├── data/                       # Structured project data
│   ├── assets/targets/         # Asset and scope markdown forms
│   ├── meta/                   # Client and lead contact info
│   ├── parsed_json/            # Auto-generated JSON (from validator)
│   └── scope/targets/          # Project scope definition
│
├── tools/
│   └── custom/                 # Custom tooling for your domain
│
├── demo-data/                  # Demo dataset — restore anytime with cp -r
│
└── utilities/
    ├── template_generator/     # YAML Mirroring Engine (methodology docs + templates)
    ├── loadout_manager/        # Applicable-playbook + command populator
    ├── reporting/              # HTML, Markdown, and deliverable ZIP generation
    ├── encryption_manager/     # AES-256 encryption for data/, execution/, reports/
    ├── methodology_manager/    # Methodology-YAML backup, versioning, and restore
    └── references_manager/     # Reference library lookup
```

---

## The Utilities

### Template Generator (YAML Mirroring Engine)
`utilities/template_generator/main.py`

Renders both the `methodology/*.md` docs and the execution templates from the `methodology_yaml/` YAML source.

| Option | Function |
|--------|----------|
| [1] Parse Methodology | Reports discrepancies between the YAML and the active workspace |
| [2] Sync Templates | Patches only the files that have diverged |
| [3] Regenerate All | Renders methodology docs + rebuilds templates from the YAML |
| [4] Run Linter | Validates structural integrity of methodology and templates |
| [5] Generate Next Iteration | Clones current iteration for next project cycle |

### Loadout Manager
`utilities/loadout_manager/main.py`

Quick-capture collected data into `loadout/loadout.md`, then generate a pre-populated playbook or fill a single command. Applicability + population are driven by `<TOKEN>`s in your task bodies (via `config/placeholders.yaml`). The vocabulary ships **empty** — add fields + tokens to make it useful for your domain.

| Option | Function |
|--------|----------|
| [1] Generate Applicable Playbook | Filters + populates tasks you have the data for → `loadout_playbook/` |
| [2] Populate a Single Command | Paste a command to fill it — or use a staging buffer file |
| [3] Show / Create Loadout | Displays parsed loadout data, or scaffolds a starter `loadout.md` |
| [4] Settings | Paste vs. buffer mode, buffer/playbook paths |

### Reporting Engine
`utilities/reporting/reporting_engine/main.py`

| Option | Function |
|--------|----------|
| [1] Validate Data | Lints execution logs and converts data forms to JSON |
| [2] Generate Report | Exports to HTML, Markdown, or both |
| [3] Finalize Report | Injects DRAFTS narrative, packages deliverable ZIP |

### Encryption Manager
`utilities/encryption_manager/main.py`

Locks and unlocks `data/`, `execution/`, and `reports/` with AES-256 encryption. Vault files (`vault.enc`, `salt.bin`) are always excluded from git.

### Methodology Manager
`utilities/methodology_manager/main.py`

Timestamp-archives your `methodology_yaml/` source before changes, lets you diff or roll back to any prior state. (After a restore, regenerate the docs + templates via the mirroring engine → Option 3.)

---

## Git Commit Strategy

By default, everything commits — working data included. The `.gitignore` contains a clearly labelled section that is **commented out by default**. Uncommenting it excludes `data/`, `execution/`, and `reports/completed/` contents from commits while preserving directory structure via `.gitkeep` files.

---

## Companion Frameworks

- [Pentest Execution Framework](../pentest-execution-framework/) — offensive security instance
- [Risk Management Framework](../risk-management-framework/) — defensive security instance
---

## Shared CLI engine (`cli/`)

Every tool in this repo runs on one shared, dictionary-routed CLI engine in the
**`cli/`** directory (`engine.py` + `__init__.py`). Each tool's `main.py`
imports it via a small path bootstrap and declares its menu as data:

```python
menu = {"1": {"desc": "Do a thing", "action": handler}, ...}
run_menu(menu, "TITLE", render=_render)   # c / q / back are global
```

The engine also provides `clear_screen()`, `confirm()`, `prompt()`, and
`numbered_select()`. **To update the CLI framework-wide, replace the one `cli/`
directory** — every tool picks it up. Overview: `cybersec-pro/ECOSYSTEM.md`.

Run tools as before: `cd utilities/<tool> && python3 main.py`.
