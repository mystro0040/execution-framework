#!/usr/bin/env python3
import json
import re
import ipaddress
from pathlib import Path
from utils.common import PROJECT_ROOT, EXECUTION_DIR, EXCLUDED_LOG_FILES

BASE_DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR    = BASE_DATA_DIR / 'parsed_json'

def validate_execution_logs():
    print("[*] Linting execution logs...")
    if not EXECUTION_DIR.exists():
        print(f"[-] Execution directory not found.")
        return 0

    all_md = list(EXECUTION_DIR.rglob('*.md'))
    log_files = [f for f in all_md if 'evidence' not in f.parts and 'temp' not in f.parts and f.name not in EXCLUDED_LOG_FILES]
    log_files.sort()
    errors = 0

    for md_file in log_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        in_code = False
        details_stack = []
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if s.startswith('```'):
                in_code = not in_code
            if not in_code:
                if '<details' in s:
                    details_stack.append(i)
                if '</details>' in s:
                    if details_stack:
                        details_stack.pop()
                    else:
                        print(f"  [!] {md_file.name} line {i}: orphaned </details>")
                        errors += 1
        if details_stack:
            for ln in details_stack:
                print(f"  [!] {md_file.name} line {ln}: unclosed <details>")
                errors += 1

    if errors == 0:
        print(f"[+] Execution Log Linting PASSED. {len(log_files)} files clean.")
    else:
        print(f"[-] Execution Log Linting FAILED. {errors} error(s).")
    return errors

def parse_markdown_to_dicts(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    parsed = {'networks': [], 'assets': [], 'users': []}
    current_category = None
    current_object = {}

    key_mapping = {
        'network name': 'network_name', 'cidr block': 'cidr_block',
        'assessment type': 'assessment_type',
        'asset name': 'asset_name', 'asset id': 'asset_id',
        'description': 'description', 'owner': 'owner',
        'username': 'username', 'role': 'role', 'email': 'email',
        'ip address': 'ip_address',
    }

    def normalize(text):
        return re.sub(r'[^a-zA-Z0-9\s]', '', text).strip().lower()

    def clean(text):
        v = text.strip('*_` \t\n')
        return None if v.lower() in ['n/a', 'none', 'null', ''] else v

    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        clean_raw = raw.replace('\\', '').strip()
        if clean_raw.startswith('---') or raw.startswith('##'):
            if current_object and current_category:
                parsed[current_category].append(current_object)
                current_object = {}
            continue

        normed = normalize(raw)
        if 'network scope' in normed or 'project scope' in normed or normed == 'network scope':
            if current_object and current_category:
                parsed[current_category].append(current_object)
            current_category = 'networks'; current_object = {}; continue
        elif 'asset data' in normed or 'assets' in normed:
            if current_object and current_category:
                parsed[current_category].append(current_object)
            current_category = 'assets'; current_object = {}; continue
        elif 'user data' in normed or 'users' in normed or 'personnel' in normed:
            if current_object and current_category:
                parsed[current_category].append(current_object)
            current_category = 'users'; current_object = {}; continue

        if current_category and ':' in raw:
            parts = raw.split(':', 1)
            potential_key = normalize(parts[0])
            potential_val = clean(parts[1])
            if potential_key in key_mapping:
                current_object[key_mapping[potential_key]] = potential_val

    if current_object and current_category:
        parsed[current_category].append(current_object)
    return parsed

def validate_and_save():
    print("[*] Validating asset data...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for cat in ['networks', 'assets', 'users']:
        (OUTPUT_DIR / cat).mkdir(exist_ok=True)

    total = 0
    errors = 0

    for md_file in BASE_DATA_DIR.rglob('*.md'):
        if 'meta' in md_file.parts or 'parsed_json' in md_file.parts:
            continue
        parsed = parse_markdown_to_dicts(md_file)

        for net in parsed.get('networks', []):
            if not net.get('network_name'):
                net['network_name'] = 'Primary_Scope'
            safe = net['network_name'].replace(' ', '_').replace('/', '_')
            with open(OUTPUT_DIR / 'networks' / f"{safe}.json", 'w') as f:
                json.dump(net, f, indent=4)
            total += 1

        for asset in parsed.get('assets', []):
            if asset.get('asset_name'):
                safe = asset['asset_name'].replace(' ', '_')
                with open(OUTPUT_DIR / 'assets' / f"{safe}.json", 'w') as f:
                    json.dump(asset, f, indent=4)
                total += 1

        for user in parsed.get('users', []):
            if user.get('username'):
                with open(OUTPUT_DIR / 'users' / f"{user['username']}.json", 'w') as f:
                    json.dump(user, f, indent=4)
                total += 1

    if errors > 0:
        print(f'[-] Validation FAILED with {errors} error(s).')
        return errors
    print(f"[+] Asset Validation PASSED. Converted {total} entries to JSON.")
    return 0

def run_validator():
    log_errors  = validate_execution_logs()
    print()
    data_errors = validate_and_save()
    if log_errors > 0 or data_errors > 0:
        print("\n[!] Fix errors before generating report.")
        return False
    return True
