import json
import re
import configparser
import markdown
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent.parent   # inner framework root

# --- Two-root topology (BASE_DIR/config.ini): application/ ships with the tool
#     (engine config); the workspace (engagement/) holds the live job's data,
#     execution logs and reports. PROJECT_ROOT points at the ACTIVE WORKSPACE so
#     every 'data'/'execution'/'reports' path below is scoped to the engagement
#     — never the whole repo. ---
_topo = configparser.ConfigParser()
_topo.read(str(BASE_DIR / 'config.ini'))
APP_DIR      = BASE_DIR / _topo.get('topology', 'application_dir', fallback='application')
PROJECT_ROOT = BASE_DIR / _topo.get('topology', 'workspace_dir', fallback='engagement')

JSON_DIR     = PROJECT_ROOT / 'data' / 'parsed_json'
META_DIR     = PROJECT_ROOT / 'data' / 'meta'
EXECUTION_DIR = PROJECT_ROOT / 'execution'

# ── Load config (engine config ships in application/) ──────────
_domain_cfg = configparser.ConfigParser()
_domain_cfg.read(APP_DIR / 'config' / 'domain.ini')

_report_cfg = configparser.ConfigParser()
_report_cfg.read(APP_DIR / 'config' / 'report.ini')

FRAMEWORK_NAME       = _domain_cfg.get('framework',   'name',          fallback='Execution Framework')
CLIENT_ROLE          = _domain_cfg.get('contacts',    'client_role',   fallback='Client')
LEAD_ROLE            = _domain_cfg.get('contacts',    'lead_role',     fallback='Project Lead')
ASSESSMENT_TYPE_LABEL = _report_cfg.get('scope',      'assessment_type_label',   fallback='Project Type')
DEFAULT_ASSESSMENT_TYPE = _report_cfg.get('scope',    'default_assessment_type', fallback='General Execution')
REPORT_FILENAME      = _report_cfg.get('output',      'filename',      fallback='Execution_Report')
REPORT_TITLE         = _report_cfg.get('output',      'title',         fallback='Execution Report')

EXCLUDED_LOG_FILES = [f.strip() for f in _domain_cfg.get('execution', 'excluded_files', fallback='00_master_log.md').split(',')]

EVIDENCE_MODE = "EMBED"

# ── Draft sections from report.ini ─────────────────────────────
DRAFT_SECTIONS = []
for i in range(1, 10):
    key   = _report_cfg.get('sections', f'section_{i}_key',   fallback=None)
    label = _report_cfg.get('sections', f'section_{i}_label', fallback=None)
    if key and label:
        DRAFT_SECTIONS.append({'key': key, 'label': label})
    else:
        break

# ── Shared functions ───────────────────────────────────────────
def load_json_data(category):
    data_list = []
    cat_dir = JSON_DIR / category
    if cat_dir.exists():
        for json_file in cat_dir.glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                data_list.append(json.load(f))
    return data_list

def parse_inline_markdown(text):
    text = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)',
                  r'<a href="\2" target="_blank" style="color:#e74c3c;">\1</a>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!`)`(?!`)(.*?)(?<!`)`(?!`)',
                  r'<code style="font-family:monospace;color:#c0392b;background:#f9f2f4;padding:2px 4px;border-radius:3px;">\1</code>', text)
    return text

def load_meta_markdown(subfolder):
    target_dir = META_DIR / subfolder
    combined = ""
    if target_dir.exists():
        for md_file in target_dir.glob('*.md'):
            with open(md_file, 'r', encoding='utf-8') as f:
                raw = f.read()
            combined += markdown.markdown(raw, extensions=['tables', 'nl2br']) + "\n"
    return combined or f"<p>No {subfolder} information provided.</p>"

def get_engagement_details():
    scope_path = PROJECT_ROOT / 'data' / 'scope' / 'targets' / 'master_scope.md'
    engagement_type = DEFAULT_ASSESSMENT_TYPE
    if scope_path.exists():
        with open(scope_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r'\*\*Assessment Type:\*\*\s*(.+)', line, re.IGNORECASE)
                if m:
                    engagement_type = m.group(1).strip()
                    break
    return engagement_type, ""

def get_scope_modifiers():
    scope_path = PROJECT_ROOT / 'data' / 'scope' / 'targets' / 'master_scope.md'
    exclusions = "No specific exclusions defined."
    allowances = "No allowances defined."
    if scope_path.exists():
        with open(scope_path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'\*\*Exclusions:\*\*\s*(.+)', content, re.IGNORECASE)
        if m:
            exclusions = m.group(1).strip()
        m = re.search(r'\*\*Allowances:\*\*\s*(.+)', content, re.IGNORECASE)
        if m:
            allowances = m.group(1).strip()
    return exclusions, allowances
