#!/usr/bin/env python3
import re
import markdown
import shutil
from pathlib import Path

from utils.common import PROJECT_ROOT, REPORT_FILENAME, DRAFT_SECTIONS
from modules import markdown_generator

OUTPUT_HTML     = PROJECT_ROOT / 'reports' / 'completed' / f'{REPORT_FILENAME}.html'
OUTPUT_MD       = PROJECT_ROOT / 'reports' / 'completed' / f'{REPORT_FILENAME}.md'
DRAFTS_MD       = PROJECT_ROOT / 'reports' / 'completed' / f'{REPORT_FILENAME}_DRAFTS.md'
DELIVERABLE_DIR = PROJECT_ROOT / 'reports' / 'Deliverable'


def parse_drafts():
    print(f"[*] Reading drafts from {DRAFTS_MD.name}...")
    if not DRAFTS_MD.exists():
        print("[-] FATAL: Drafts file not found. Run Generate first.")
        return None

    with open(DRAFTS_MD, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    sections = {}
    current_section = None
    for line in lines:
        m = re.match(r'^###\s*([A-Z_]+)\s*###', line.strip())
        if m:
            current_section = m.group(1)
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    if not sections:
        print("[-] FATAL: No valid sections found in DRAFTS file.")
        return None

    valid = 0
    for key, lines in list(sections.items()):
        raw = "".join(lines).strip()
        if raw.startswith('[...') or raw == '':
            sections[key] = (
                f'<div class="action-required" style="color:red;font-weight:bold;">'
                f'[ACTION REQUIRED] Missing content for {key}.</div>'
            )
        else:
            sections[key] = markdown.markdown(raw, extensions=['tables', 'nl2br'])
            sections[key + '_RAW'] = raw
            valid += 1

    print(f"[+] Parsed {valid} populated sections.")
    return sections


def inject_html(sections):
    print(f"[*] Injecting into {OUTPUT_HTML.name}...")
    with open(OUTPUT_HTML, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    injection_count = 0
    for section in DRAFT_SECTIONS:
        key = section['key']
        if key not in sections or 'action-required' in sections.get(key, ''):
            continue

        # Match the Jinja2-rendered placeholder format
        target = f'Missing content for {key}. Please update the DRAFTS.md file and run this script again.'
        if target in html_content:
            replacement_div = f'<div class="action-required">{target}</div>'
            html_content = html_content.replace(replacement_div, sections[key], 1)
            injection_count += 1
            continue

        pattern = re.compile(rf'<div[^>]*>.*?Missing content for {key}.*?</div>', re.IGNORECASE | re.DOTALL)
        replacement = sections[key]
        html_content, count = pattern.subn(lambda m: replacement, html_content, count=1)
        injection_count += count

    if injection_count == 0:
        print("[-] WARNING: No placeholders found. Already finalized?")
    else:
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[+] HTML finalized — {injection_count} sections injected.")
    return True


def package_deliverable():
    print("\n[*] Packaging deliverable ZIP...")
    if DELIVERABLE_DIR.exists():
        shutil.rmtree(DELIVERABLE_DIR)
    DELIVERABLE_DIR.mkdir(parents=True)

    completed_dir = PROJECT_ROOT / 'reports' / 'completed'
    for ext in ['*.html', '*.pdf', '*.md', '*.docx']:
        for fp in completed_dir.glob(ext):
            if 'DRAFTS' not in fp.name:
                shutil.copy2(fp, DELIVERABLE_DIR / fp.name)

    zip_path = completed_dir / f'{REPORT_FILENAME}_Deliverable'
    shutil.make_archive(str(zip_path), 'zip', DELIVERABLE_DIR)
    shutil.rmtree(DELIVERABLE_DIR)
    print(f"[+] Deliverable ZIP created: {zip_path}.zip\n")


def run_finalizer(formats=None):
    if formats is None:
        formats = {'html', 'md'}

    parsed = parse_drafts()
    if not parsed:
        return False

    fmt_label = ', '.join(f.upper() for f in sorted(formats))
    print(f"\n[*] Finalizing: {fmt_label}...")

    if 'html' in formats:
        if OUTPUT_HTML.exists():
            inject_html(parsed)
        else:
            print(f"[-] SKIPPING HTML: not found. Run Generate first.")

    if 'md' in formats:
        try:
            print("\n[*] Generating Markdown report...")
            markdown_generator.run_markdown_generator(parsed)
        except Exception as e:
            print(f"[-] ERROR generating Markdown: {e}")

    package_deliverable()
    return True
