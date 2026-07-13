#!/usr/bin/env python3
import re
from datetime import datetime
from pathlib import Path
from utils.common import (
    PROJECT_ROOT, EXECUTION_DIR, EXCLUDED_LOG_FILES,
    load_json_data, load_meta_markdown,
    get_engagement_details, get_scope_modifiers,
    REPORT_FILENAME, REPORT_TITLE, DRAFT_SECTIONS,
    CLIENT_ROLE, LEAD_ROLE, FRAMEWORK_NAME,
)
from modules.generator import generate_human_drafts

OUTPUT_PATH = PROJECT_ROOT / 'reports' / 'completed' / f'{REPORT_FILENAME}.md'


def load_execution_logs():
    if not EXECUTION_DIR.exists():
        return "No execution narrative provided."

    all_md = list(EXECUTION_DIR.rglob('*.md'))
    log_files = [f for f in all_md if 'evidence' not in f.parts and 'temp' not in f.parts and f.name not in EXCLUDED_LOG_FILES]
    log_files.sort()

    if not log_files:
        return "No execution log files found."

    md_content = ""
    for fp in log_files:
        with open(fp, 'r', encoding='utf-8') as f:
            md_content += f"\n\n\n{f.read()}"

    md_content = re.sub(r'(?i)##\s*Checklist.*?---', '', md_content, flags=re.DOTALL)
    md_content = re.sub(r'(?im)^##\s*Execution Notes\s*$', '', md_content)
    md_content = re.sub(r'(?m)^[ \t]*-\s*\[[x ]\]\s*\*\*.*?\*\*[ \t]*$', '', md_content)
    md_content = re.sub(r'(?m)^-{3,}\s*$', '', md_content)

    placeholder_pattern = r'<details>\s*<summary><i>Execution Notes</i></summary>\s*>\s*\*Log execution details here\.\*\s*</details>\s*<br>'
    md_content = re.sub(placeholder_pattern, '', md_content, flags=re.IGNORECASE)

    _not_used_kw = r'Not (?:used|run|performed|applicable|required|tested)|N/A|Skipped'
    _not_used = re.compile(
        r'[ \t]*<details[^>]*>[ \t]*\n[ \t]*<summary[^>]*>[^\n]*</summary>[ \t]*\n'
        r'(?:[ \t]*\n)*[ \t]*>\s*\*?(?:' + _not_used_kw + r')[^\n]*\n'
        r'(?:[ \t]*\n)*[ \t]*</details>(?:[ \t]*\n[ \t]*<br>)?',
        re.MULTILINE
    )
    md_content = _not_used.sub('', md_content)

    for _ in range(4):
        md_content = re.sub(r'(?m)^\s*\*\*[^*]+\*\*\s*$(?=\s*(?:^#|^\s*\*\*|\Z))', '', md_content)
        md_content = re.sub(r'(?m)^#{1,4}\s+[^\n]*$(?=\s*(?:^#{1,4}|^-{3,}|\Z))', '', md_content)

    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    return md_content


def run_markdown_generator(draft_sections=None):
    print(f"[*] Assembling Markdown report...")

    eng_type, _ = get_engagement_details()
    networks    = load_json_data('networks')
    assets      = load_json_data('assets')
    users       = load_json_data('users')
    exclusions, allowances = get_scope_modifiers()
    client_info = load_meta_markdown('client')
    lead_info   = load_meta_markdown('lead')

    scope_name = networks[0]['network_name'] if networks else "Project Scope"

    def placeholder(key, label):
        return f"**[ACTION REQUIRED] Missing content for {key}. Please update DRAFTS.md and finalize.**"

    md  = f"# {scope_name} — {REPORT_TITLE}\n\n"
    md += f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n"
    md += f"**Project Type:** {eng_type}\n"
    md += f"**Version:** 1.0\n"
    md += f"**CONFIDENTIAL**\n\n---\n\n"

    md += f"## {CLIENT_ROLE} Contact\n{client_info}\n\n"
    md += f"## {LEAD_ROLE} Contact\n{lead_info}\n\n---\n\n"

    md += f"## Project Scope\n"
    if networks:
        for net in networks:
            md += f"- **{net.get('network_name', 'Scope')}**"
            if net.get('cidr_block'):
                md += f": {net['cidr_block']}"
            md += "\n"
    md += f"\n**Exclusions:** {exclusions}\n**Allowances:** {allowances}\n\n---\n\n"

    # Draft sections
    for section in DRAFT_SECTIONS:
        key   = section['key']
        label = section['label']
        md += f"## {label}\n\n"
        if draft_sections:
            raw_key = key + '_RAW'
            content = draft_sections.get(raw_key, '')
            md += (content if content and not content.startswith('[...') else placeholder(key, label)) + "\n\n"
        else:
            md += placeholder(key, label) + "\n\n"

    md += "---\n\n"
    md += "## Execution Narrative\n\n"
    md += load_execution_logs()
    md += "\n"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"[+] Markdown report saved: {OUTPUT_PATH}")

    if draft_sections is None:
        context = {'networks': networks}
        generate_human_drafts(context, OUTPUT_PATH)

    return True
