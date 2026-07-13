#!/usr/bin/env python3
import os
import sys

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402
from core.config import METHODOLOGY_DIR, EXECUTION_TEMPLATES_DIR, WORKSPACE_DIR  # noqa: E402
from core.parser import parse_methodology  # noqa: E402
from core.yaml_store import load_docs, docs_to_methodology_data  # noqa: E402
from modules.ttp_docs_gen import regenerate_methodology_docs  # noqa: E402
from modules.execution_gen import (  # noqa: E402
    analyze_discrepancies, generate_file_markdown,
    get_master_log_content, generate_master_log
)
from modules.linter import run_linter  # noqa: E402
from utils.helpers import write_file, slugify  # noqa: E402
import shutil  # noqa: E402

def is_template_dir_empty(directory):
    if not os.path.exists(directory):
        return True
    for root, dirs, files in os.walk(directory):
        if any(f.endswith('.md') for f in files):
            return False
    return True

def generate_next_iteration():
    existing = sorted([
        d for d in os.listdir(WORKSPACE_DIR)
        if os.path.isdir(os.path.join(WORKSPACE_DIR, d)) and d.startswith('iteration_')
    ]) if os.path.exists(WORKSPACE_DIR) else []

    if not existing:
        next_iter = 'iteration_01'
    else:
        last_num = int(existing[-1].split('_')[1])
        next_iter = f"iteration_{last_num + 1:02d}"

    src  = EXECUTION_TEMPLATES_DIR
    dest = os.path.join(WORKSPACE_DIR, next_iter)

    if not os.path.exists(src) or is_template_dir_empty(src):
        print("[!] No templates found. Run Option 3 first.")
        return

    shutil.copytree(src, dest)
    print(f"[+] Created workspace: execution/{next_iter}/")

def parse_methodology_action():
    print("\n[*] Parsing Methodology directory...")
    if is_template_dir_empty(EXECUTION_TEMPLATES_DIR):
        print("[!] No templates found. Run Option 3 first.")
        return
    methodology_data = docs_to_methodology_data(load_docs())
    discrepancies = analyze_discrepancies(methodology_data, EXECUTION_TEMPLATES_DIR)
    if not discrepancies:
        print("[+] All templates perfectly mirror your Methodology.")
    else:
        print(f"[!] Found {len(discrepancies)} discrepancy(s):\n")
        for phase, path, _, reason in discrepancies:
            print(f"    - {path} [{reason}]")
    print("\n" + "-" * 40)

def sync_templates_action():
    print("\n[*] Syncing templates...")
    if is_template_dir_empty(EXECUTION_TEMPLATES_DIR):
        print("[!] No templates found. Run Option 3 first.")
        return
    methodology_data = docs_to_methodology_data(load_docs())
    discrepancies = analyze_discrepancies(methodology_data, EXECUTION_TEMPLATES_DIR)
    if not discrepancies:
        print("[+] No discrepancies. Nothing to sync.")
    else:
        for phase, relative_path, expected_md, reason in discrepancies:
            filepath = os.path.join(EXECUTION_TEMPLATES_DIR, relative_path)
            write_file(filepath, expected_md)
            print(f"[+] Fixed: {relative_path} ({reason})")
        print("\n[+] Sync complete.")
    print("\n" + "-" * 40)

def regenerate_all_action():
    print("\n[!] WARNING: This renders methodology docs (methodology/*.md) AND")
    print("    rebuilds all templates from the YAML source (methodology_yaml/*.yaml).")
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        docs = load_docs()

        print("\n[*] Rendering methodology markdown docs from YAML...")
        doc_count = regenerate_methodology_docs(docs, quiet=True)
        print(f"[+] Rendered {doc_count} methodology docs -> {METHODOLOGY_DIR}")

        print("\n[*] Building execution templates...")
        methodology_data = docs_to_methodology_data(docs)
        generate_master_log(methodology_data)
        count = 0
        for phase_folder, files in methodology_data.items():
            for file_name, categories in files.items():
                if any(len(items) > 0 for items in categories.values()):
                    write_file(
                        os.path.join(EXECUTION_TEMPLATES_DIR, phase_folder, file_name),
                        generate_file_markdown(file_name, categories)
                    )
                    print(f"[+] Generated -> {phase_folder}/{file_name}")
                    count += 1
        print(f"\n[+] Mirrored {count} template files.")
    else:
        print("[-] Aborted.")
    print("\n" + "-" * 40)

def _render(title, menu):
    print("=" * 60)
    print(" EXECUTION FRAMEWORK — TEMPLATE ENGINE")
    print("=" * 60)
    print(" Source of truth: methodology_yaml/*.yaml -> methodology docs + templates")
    print("-" * 60)
    print("[1] Parse Methodology (Generate Delta Report)")
    print("[2] Sync Templates (Fix Discrepancies Only)")
    print("[3] Regenerate All (Render Methodology Docs + Build Templates)")
    print("[4] Run Project Linter")
    print("[5] Generate Next Iteration Workspace")
    print("-" * 60)
    print("[C] Clear Screen | [Q] Quit")
    print("=" * 60)

def main():
    menu = {
        "1": {"desc": "Parse Methodology (Generate Delta Report)", "action": parse_methodology_action},
        "2": {"desc": "Sync Templates (Fix Discrepancies Only)", "action": sync_templates_action},
        "3": {"desc": "Regenerate All (Render Methodology Docs + Build Templates)", "action": regenerate_all_action},
        "4": {"desc": "Run Project Linter", "action": run_linter},
        "5": {"desc": "Generate Next Iteration Workspace", "action": generate_next_iteration},
    }
    run_menu(menu, "EXECUTION FRAMEWORK — TEMPLATE ENGINE", render=_render,
             prompt_text="\nSelect an option: ")
    print("\nExiting.")

if __name__ == "__main__":
    main()
