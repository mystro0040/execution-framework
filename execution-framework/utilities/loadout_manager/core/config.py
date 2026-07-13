"""
Paths + canonical placeholder vocabulary access for loadout_manager.

Self-contained: loadout_manager reads the shared `config/placeholders.yaml`
vocabulary and the YAML methodology source directly, so it can be dropped into
any framework instance without importing the template engine.

Zero-edit drop-in: the methodology dir names are read from the framework's
`config/domain.ini`, so this file is identical across every framework instance.
"""
import os
import configparser
import yaml

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# --- Two-root topology (BASE_DIR/config.ini): application/ ships with the tool
#     (engine config + YAML methodology source); the workspace (engagement/)
#     holds the live job's data, quick-capture and generated outputs. ---
_topo = configparser.ConfigParser()
_topo.read(os.path.join(BASE_DIR, 'config.ini'))
APP_DIR       = os.path.join(BASE_DIR, _topo.get('topology', 'application_dir', fallback='application'))
WORKSPACE_DIR = os.path.join(BASE_DIR, _topo.get('topology', 'workspace_dir', fallback='engagement'))
_APP_DATA     = os.path.join(APP_DIR, _topo.get('topology', 'app_data_dir', fallback='data'))

_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(APP_DIR, 'config', 'domain.ini'))
# Methodology: the YAML source-of-truth ships under application/<data>/<yaml_dir>;
# the rendered markdown lives in the workspace under <dir>.
TTP_MD_DIR        = os.path.join(WORKSPACE_DIR, _cfg.get('methodology', 'directory', fallback='TTPs'))
TTP_YAML_DIR      = os.path.join(_APP_DATA, _cfg.get('methodology', 'yaml_directory', fallback='ttps'))
PLACEHOLDERS_FILE = os.path.join(APP_DIR, 'config', 'placeholders.yaml')

# Engagement quick-capture + outputs (defaults; some overridable in settings).
# Kept in a dedicated `loadout/` dir — deliberately OUTSIDE `data/` so the
# reporting engine's asset validator (which rglobs data/*.md) never tries to
# parse these as asset forms.
LOADOUT_FILE      = os.path.join(WORKSPACE_DIR, 'loadout', 'loadout.md')
PLAYBOOK_DIR      = os.path.join(WORKSPACE_DIR, 'loadout_playbook')
BUFFER_FILE       = os.path.join(WORKSPACE_DIR, 'loadout', 'command_buffer.md')

# YAML data sources (Micro = one file; Global = the engagement data tree).
# session.yaml is the fast, single-file data scratchpad (workspace root, easy to
# reach). ENGAGEMENT_DIR is the full per-engagement YAML fact tree (data/).
SESSION_FILE      = os.path.join(WORKSPACE_DIR, 'session.yaml')
ENGAGEMENT_DIR    = os.path.join(WORKSPACE_DIR, 'data')

SETTINGS_FILE     = os.path.join(os.path.dirname(__file__), 'settings.json')


def load_vocab():
    """Return the canonical placeholder vocabulary as convenient lookup maps."""
    with open(PLACEHOLDERS_FILE, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    fields = raw.get('fields', {}) or {}
    ignore = set(raw.get('ignore', []) or [])

    token_to_key = {}   # <TARGET_IP> inner "TARGET_IP" -> "target_ip"
    key_to_token = {}   # "target_ip" -> "TARGET_IP"
    key_to_meta  = {}   # "target_ip" -> {"label":..., "example":...}
    for token, spec in fields.items():
        key = spec['key']
        token_to_key[token] = key
        key_to_token[key] = token
        key_to_meta[key] = {'label': spec.get('label', key),
                            'example': spec.get('example', '')}
    return {
        'token_to_key': token_to_key,
        'key_to_token': key_to_token,
        'key_to_meta': key_to_meta,
        'ignore': ignore,
        'fields': fields,
    }
