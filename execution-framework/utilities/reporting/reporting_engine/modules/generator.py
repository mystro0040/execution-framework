#!/usr/bin/env python3
import re
import html
import markdown
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from utils.common import (
    BASE_DIR, PROJECT_ROOT, EXECUTION_DIR, EXCLUDED_LOG_FILES,
    load_json_data, load_meta_markdown,
    get_engagement_details, get_scope_modifiers,
    REPORT_FILENAME, REPORT_TITLE, DRAFT_SECTIONS,
    CLIENT_ROLE, LEAD_ROLE, FRAMEWORK_NAME,
)

# TEMPLATE_DIR is engine code — it ships under the inner root, NOT the workspace.
TEMPLATE_DIR = BASE_DIR / 'utilities' / 'reporting' / 'reporting_engine' / 'templates'
TEMPLATE_FILE = 'report_template.html'
OUTPUT_PATH  = PROJECT_ROOT / 'reports' / 'completed' / f'{REPORT_FILENAME}.html'


# ==========================================
# UNTRUSTED-INPUT ESCAPING (stored-XSS hardening)
# The HTML template renders data fields raw (Jinja autoescape is intentionally
# OFF so the framework's own CSS/JS pass through untouched). To stop a <script>
# in a target-derived field from executing in the client-facing report,
# untrusted values are HTML-escaped where they enter the context. Framework-
# owned values (css_content/js_content, framework-built *_html) are left as-is.
# ==========================================
def _escape_untrusted(value):
    """Recursively HTML-escape string values in untrusted JSON-derived data."""
    if isinstance(value, str):
        return html.escape(value)
    if isinstance(value, list):
        return [_escape_untrusted(v) for v in value]
    if isinstance(value, dict):
        return {k: _escape_untrusted(v) for k, v in value.items()}
    return value

def _neutralize_narrative(html_str):
    """Defence-in-depth for the execution-log narrative: neutralise any literal
    <script> tag (never part of legitimate report output) so pasted target
    output cannot execute. Benign narratives render unchanged."""
    html_str = re.sub(r'(?i)<\s*script\b', '&lt;script', html_str)
    html_str = re.sub(r'(?i)<\s*/\s*script\s*>', '&lt;/script&gt;', html_str)
    return html_str


def load_and_convert_execution_log():
    if not EXECUTION_DIR.exists():
        return "<p>No execution narrative provided.</p>"

    all_md = list(EXECUTION_DIR.rglob('*.md'))
    log_files = [f for f in all_md if 'evidence' not in f.parts and 'temp' not in f.parts and f.name not in EXCLUDED_LOG_FILES]
    log_files.sort()

    if not log_files:
        return "<p>No execution log files found.</p>"

    print(f"[*] Concatenating {len(log_files)} execution log files...")
    md_content = ""
    for fp in log_files:
        with open(fp, 'r', encoding='utf-8') as f:
            md_content += f"\n\n\n{f.read()}"

    md_content = re.sub(r'(?i)##\s*Checklist.*?---', '', md_content, flags=re.DOTALL)
    md_content = re.sub(r'(?im)^##\s*Execution Notes\s*$', '', md_content)
    placeholder_pattern = r'<details>\s*<summary><i>Execution Notes</i></summary>\s*>\s*\*Log execution details here\.\*\s*</details>\s*<br>'
    md_content = re.sub(placeholder_pattern, '', md_content, flags=re.IGNORECASE)
    md_content = re.sub(r'^<a\s+id="[^"]+"></a>\s*$', '', md_content, flags=re.MULTILINE)
    md_content = re.sub(r'^[ \t]*-\s*\[[x ]\]\s*\*\*.*?\*\*[ \t]*$', '', md_content, flags=re.MULTILINE)

    # Strip not-performed entries
    _not_used_kw = (
        r'Not (?:used|run|performed|applicable|required|tested|relevant|needed|available)'
        r'|N/A|Skipped|No (?:findings|issues)'
    )
    not_used_pattern = (
        r'#### [^\n]+\n\s*<details[^>]*>\n[ \t]*<summary[^>]*>.*?</summary>\n'
        r'[ \t]*\n*[ \t]*>\s*\*?(?:' + _not_used_kw + r')[^\n]*\n[ \t]*\n*[ \t]*</details>(?:[ \t]*\n[ \t]*<br>)?'
    )
    md_content = re.sub(not_used_pattern, '', md_content, flags=re.IGNORECASE)

    for _ in range(4):
        md_content = re.sub(r'(?m)^\s*\*\*[^*]+\*\*\s*$(?=\s*(?:^#|^\s*\*\*|\Z))', '', md_content)
        md_content = re.sub(r'(?m)^#{1,4}\s+[^\n]*$(?=\s*(?:^#{1,4}|^-{3,}|\Z))', '', md_content)

    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    md_content = re.sub(r'(?m)^(#+)\s*Phase\s*\d+:\s*', r'\1 ', md_content)
    md_content = re.sub(r'<details[^>]*>', '', md_content)
    md_content = re.sub(r'</details>', '', md_content)
    md_content = re.sub(r'<summary[^>]*>(.*?)</summary>', r'<h3>\1</h3>', md_content)
    md_content = md_content.replace('\xa0', ' ')

    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'nl2br', 'md_in_html'])
    return _neutralize_narrative(html_content)


def generate_human_drafts(context, output_path):
    draft_path = output_path.parent / f"{output_path.stem}_DRAFTS.md"
    if draft_path.exists():
        return
    scope_name = context['networks'][0].get('network_name', 'the project scope') if context['networks'] else 'the project scope'
    lines = []
    for section in DRAFT_SECTIONS:
        lines.append(f"### {section['key']} ###")
        lines.append(f"[... Write your {section['label']} here ...]")
        lines.append("")
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"[+] DRAFTS template created at: {draft_path.name}")


def run_generator():
    if not (TEMPLATE_DIR / TEMPLATE_FILE).exists():
        print(f"[-] Template not found: {TEMPLATE_DIR / TEMPLATE_FILE}")
        return False

    css_path = TEMPLATE_DIR / 'assets' / 'css' / 'styles.css'
    js_path  = TEMPLATE_DIR / 'assets' / 'js'  / 'app.js'
    css_content = css_path.read_text(encoding='utf-8') if css_path.exists() else ""
    js_content  = js_path.read_text(encoding='utf-8')  if js_path.exists()  else ""

    eng_type, _  = get_engagement_details()
    exclusions, allowances = get_scope_modifiers()
    networks = load_json_data('networks')

    context = {
        'networks':           _escape_untrusted(networks),
        'assets':             _escape_untrusted(load_json_data('assets')),
        'users':              _escape_untrusted(load_json_data('users')),
        'technical_narrative': load_and_convert_execution_log(),
        'client_info':        load_meta_markdown('client'),
        'lead_info':          load_meta_markdown('lead'),
        'engagement_type':    html.escape(eng_type),
        'scope_exclusions':   html.escape(exclusions),
        'client_allowances':  html.escape(allowances),
        'report_title':       REPORT_TITLE,
        'framework_name':     FRAMEWORK_NAME,
        'client_role':        CLIENT_ROLE,
        'lead_role':          LEAD_ROLE,
        'draft_sections':     DRAFT_SECTIONS,
        'current_date':       datetime.now().strftime("%B %d, %Y"),
        'css_content':        css_content,
        'js_content':         js_content,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate_human_drafts(context, OUTPUT_PATH)

    if not networks:
        print("[-] WARNING: No network scope data found. HTML will generate with placeholder sections.")
    try:
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template(TEMPLATE_FILE)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(template.render(context))
        print(f"[+] SUCCESS! Report generated at: {OUTPUT_PATH}")
        return True
    except Exception as e:
        print(f"[-] FATAL ERROR: {e}")
        return False
