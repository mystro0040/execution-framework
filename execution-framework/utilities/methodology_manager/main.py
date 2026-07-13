#!/usr/bin/env python3
import os, sys

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402
from core.config import BACKUPS_DIR  # noqa: E402
from modules.vault import create_backup, list_backups, restore_backup  # noqa: E402

def restore_from_backup():
    backups = list_backups()
    if backups:
        sel = input("Select backup number (or q to cancel): ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(backups):
            restore_backup(os.path.join(BACKUPS_DIR, backups[int(sel)-1]))

def _render(title, menu):
    print("=" * 60)
    print(" METHODOLOGY YAML VAULT & VERSION CONTROL")
    print("=" * 60)
    print("[1] Create Backup")
    print("[2] List Backups")
    print("[3] Restore from Backup")
    print("-" * 60)
    print("[Q] Quit")
    print("=" * 60)

def main():
    menu = {
        "1": {"desc": "Create Backup", "action": create_backup},
        "2": {"desc": "List Backups", "action": list_backups},
        "3": {"desc": "Restore from Backup", "action": restore_from_backup},
    }
    run_menu(menu, "METHODOLOGY YAML VAULT & VERSION CONTROL", render=_render,
             prompt_text="\nSelect an option: ")

if __name__ == "__main__":
    main()
