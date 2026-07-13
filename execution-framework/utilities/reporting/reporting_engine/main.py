#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402
from modules import validator, generator, finalizer, markdown_generator  # noqa: E402
from utils.common import PROJECT_ROOT, REPORT_FILENAME  # noqa: E402

def write_log(msg):
    log_dir = PROJECT_ROOT / 'reports' / 'completed'
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / 'engine_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def _export_render(title, menu):
    print("\n------------------------------------------------------------")
    print("   SELECT EXPORT FORMAT")
    print("------------------------------------------------------------")
    print("   [1] HTML (Web View / Print to PDF)")
    print("   [2] Markdown (Raw Text)")
    print("   [3] ALL Formats")
    print("   [b] Back")

def export_html():
    if generator.run_generator():
        write_log("HTML Generated")

def export_md():
    if markdown_generator.run_markdown_generator():
        write_log("Markdown Generated")

def export_all():
    generator.run_generator()
    markdown_generator.run_markdown_generator()
    write_log("ALL Formats Generated")

def generate_report():
    menu = {
        "1": {"desc": "HTML (Web View / Print to PDF)", "action": export_html, "exit_after": True},
        "2": {"desc": "Markdown (Raw Text)", "action": export_md, "exit_after": True},
        "3": {"desc": "ALL Formats", "action": export_all, "exit_after": True},
        "b": {"desc": "Back", "action": "BACK_FLAG"},
    }
    run_menu(menu, "SELECT EXPORT FORMAT", render=_export_render,
             prompt_text="Format choice: ")

def _finalize_render(title, menu):
    completed = PROJECT_ROOT / 'reports' / 'completed'
    html_status = "[EXISTS]" if (completed / f'{REPORT_FILENAME}.html').exists() else "[not generated]"
    md_status   = "[EXISTS]" if (completed / f'{REPORT_FILENAME}.md').exists()   else "[not generated]"
    print("\n------------------------------------------------------------")
    print("   FINALIZE — INJECT DRAFTS & PACKAGE")
    print("------------------------------------------------------------")
    print(f"   [1] HTML        {html_status}")
    print(f"   [2] Markdown    {md_status}")
    print("   [3] ALL Formats")
    print("   [b] Back")

def finalize_with(formats):
    print("\n[*] Launching Finalizer...")
    if finalizer.run_finalizer(formats=formats):
        write_log(f"Finalized ({', '.join(sorted(formats)).upper()})")

def finalize_report():
    menu = {
        "1": {"desc": "HTML", "action": finalize_with, "args": ({'html'},), "exit_after": True},
        "2": {"desc": "Markdown", "action": finalize_with, "args": ({'md'},), "exit_after": True},
        "3": {"desc": "ALL Formats", "action": finalize_with, "args": ({'html', 'md'},), "exit_after": True},
        "b": {"desc": "Back", "action": "BACK_FLAG"},
    }
    run_menu(menu, "FINALIZE — INJECT DRAFTS & PACKAGE", render=_finalize_render,
             prompt_text="Format choice: ")

def validate_data():
    print("\n[*] Launching Validator...")
    validator.run_validator()

def _render(title, menu):
    print("\n============================================================")
    print("   EXECUTION FRAMEWORK — REPORTING ENGINE")
    print("============================================================")
    print("   [1] Validate Data")
    print("   [2] Generate Report (Export Menu)")
    print("   [3] Finalize Report (Inject Drafts & Package)")
    print("------------------------------------------------------------")
    print("   [c] Clear Screen    [q] Quit")
    print("============================================================\n")

def main():
    menu = {
        "1": {"desc": "Validate Data", "action": validate_data},
        "2": {"desc": "Generate Report (Export Menu)", "action": generate_report},
        "3": {"desc": "Finalize Report (Inject Drafts & Package)", "action": finalize_report},
    }
    run_menu(menu, "EXECUTION FRAMEWORK — REPORTING ENGINE", render=_render,
             prompt_text="Select an option: ")
    print("\n[*] Exiting. Goodbye!\n")

if __name__ == "__main__":
    main()
