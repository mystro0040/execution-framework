#!/usr/bin/env python3
"""
State Manager — Execution Framework
Manages the working state of the project between active engagement and distribution.
"""
import os
import sys
import shutil
import configparser
from pathlib import Path

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402

BASE_DIR = Path(__file__).parent.parent.parent

# --- Two-root topology (BASE_DIR/config.ini): the working state lives in the
#     active workspace (engagement/); demo-data/ is a sibling sample engagement. ---
_topo = configparser.ConfigParser()
_topo.read(str(BASE_DIR / 'config.ini'))
WORK_DIR = BASE_DIR / _topo.get('topology', 'workspace_dir', fallback='engagement')

DATA_DIR        = WORK_DIR / 'data'
EXECUTION_DIR   = WORK_DIR / 'execution'
REPORTS_DIR     = WORK_DIR / 'reports' / 'completed'
PARSED_JSON_DIR = WORK_DIR / 'data' / 'parsed_json'
DEMO_DATA_DIR   = BASE_DIR / 'demo-data'

# Auto-detect templates iteration directory
TEMPLATES_DATA = WORK_DIR / 'templates' / 'data'
TEMPLATES_ITER = None
for candidate in [
    WORK_DIR / 'templates' / 'execution' / 'iteration',
    WORK_DIR / 'templates' / 'Playbooks' / 'iteration',
    WORK_DIR / 'templates' / 'playbooks' / 'iteration',
]:
    if candidate.exists():
        TEMPLATES_ITER = candidate
        break


def _render(title, menu):
    print("\n============================================================")
    print("      EXECUTION FRAMEWORK - STATE MANAGER            ")
    print("============================================================")
    print("   [1] Restore to Distribution State")
    print("      -> Clears working dirs, loads blank templates")
    print("      -> Ready to commit / share / clone fresh")
    print("")
    print("   [2] Load Demo Data")
    print("      -> Loads demo-data/ into working dirs")
    print("      -> Run Validator then Generate Report to see output")
    print("------------------------------------------------------------")
    print("   [c] Clear Screen    [q] Quit")
    print("============================================================\n")


def restore_distribution_state():
    print("\n[*] Restoring project to distribution state...")

    print("[*] Clearing working data directories...")
    for subdir in ['assets', 'meta', 'scope']:
        target = DATA_DIR / subdir
        if target.exists():
            for f in target.rglob('*.md'):
                f.unlink()

    print("[*] Clearing parsed JSON...")
    if PARSED_JSON_DIR.exists():
        for f in PARSED_JSON_DIR.rglob('*.json'):
            f.unlink()

    print("[*] Clearing reports...")
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.iterdir():
            if f.is_file() and f.name != '.gitkeep':
                f.unlink()

    print("[*] Clearing execution working directories...")
    if EXECUTION_DIR.exists():
        for item in EXECUTION_DIR.iterdir():
            if item.is_dir() and item.name.startswith('iteration_'):
                shutil.rmtree(item)

    print("[*] Copying blank data templates...")
    if TEMPLATES_DATA and TEMPLATES_DATA.exists():
        for src_file in TEMPLATES_DATA.rglob('*'):
            if src_file.is_file() and src_file.name != '.gitkeep':
                rel = src_file.relative_to(TEMPLATES_DATA)
                dst = DATA_DIR / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)

    print("[*] Copying blank execution templates...")
    if TEMPLATES_ITER and TEMPLATES_ITER.exists():
        dest_iter = EXECUTION_DIR / 'iteration_01'
        if dest_iter.exists():
            shutil.rmtree(dest_iter)
        shutil.copytree(TEMPLATES_ITER, dest_iter)

    print("\n[+] SUCCESS! Project restored to distribution state.")
    print("    Working dirs have blank templates. Ready to commit.\n")


def load_demo_data():
    if not DEMO_DATA_DIR.exists():
        print("\n[-] demo-data/ directory not found. Nothing to load.\n")
        return

    print("\n[*] Loading demo data into working directories...")

    print("[*] Loading demo data/...")
    demo_data = DEMO_DATA_DIR / 'data'
    if demo_data.exists():
        for src_file in demo_data.rglob('*'):
            if src_file.is_file() and src_file.name != '.gitkeep':
                rel = src_file.relative_to(demo_data)
                if 'parsed_json' in src_file.parts:
                    continue
                dst = DATA_DIR / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)

    print("[*] Loading demo execution/...")
    demo_exec = DEMO_DATA_DIR / 'execution'
    if demo_exec.exists():
        for src_file in demo_exec.rglob('*'):
            if src_file.is_file() and src_file.name != '.gitkeep':
                rel = src_file.relative_to(demo_exec)
                dst = EXECUTION_DIR / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)

    print("\n[+] SUCCESS! Demo data loaded.")
    print("    Run: Reporting Engine → [1] Validate Data")
    print("    Then: [2] Generate Report → [1] HTML\n")


def restore_distribution_action():
    confirm = input("\n[!] This will clear working dirs and load blank templates. Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        restore_distribution_state()
    else:
        print("[-] Aborted.\n")


def load_demo_action():
    confirm = input("\n[!] This will overwrite working dirs with demo data. Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        load_demo_data()
    else:
        print("[-] Aborted.\n")


def main():
    menu = {
        "1": {"desc": "Restore to Distribution State", "action": restore_distribution_action},
        "2": {"desc": "Load Demo Data", "action": load_demo_action},
    }
    run_menu(menu, "EXECUTION FRAMEWORK - STATE MANAGER", render=_render,
             prompt_text="Select an option: ")
    print("\n[*] Exiting State Manager. Goodbye!\n")


if __name__ == "__main__":
    main()
