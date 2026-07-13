import os
import re
from core.config import METHODOLOGY_DIR, EXECUTION_TEMPLATES_DIR

def run_linter():
    print("\n[*] Initializing Project Linter...")
    errors = 0

    # Lint methodology source files
    print("[*] Scanning Methodology Source Structure...")
    if os.path.exists(METHODOLOGY_DIR):
        for root, dirs, files in os.walk(METHODOLOGY_DIR):
            for file in files:
                if not file.endswith('.md'):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not re.search(r'^\*\*.+\*\*', content, re.MULTILINE):
                    print(f"  [!] {os.path.relpath(filepath, METHODOLOGY_DIR)} — no bolded tasks found")
                    errors += 1

    # Lint execution templates
    print("[*] Scanning Execution Template Structure...")
    if os.path.exists(EXECUTION_TEMPLATES_DIR):
        for root, dirs, files in os.walk(EXECUTION_TEMPLATES_DIR):
            for file in files:
                if not file.endswith('.md') or file.startswith('00_'):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                for required in ['## Checklist', '## Execution Notes']:
                    if required not in content:
                        print(f"  [!] {os.path.relpath(filepath, EXECUTION_TEMPLATES_DIR)} — missing '{required}'")
                        errors += 1

    print()
    if errors == 0:
        print("=" * 50)
        print("[+] LINT PASSED: Framework structure is perfectly intact.")
        print("=" * 50)
    else:
        print(f"[-] LINT FAILED: {errors} issue(s) found.")
