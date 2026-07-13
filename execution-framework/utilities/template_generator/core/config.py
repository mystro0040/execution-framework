import os
import configparser

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# --- Two-root topology (BASE_DIR/config.ini): application/ ships with the tool
#     (engine config + YAML methodology source); the workspace (engagement/)
#     holds the live job's templates, execution logs and rendered methodology. ---
_topo = configparser.ConfigParser()
_topo.read(os.path.join(BASE_DIR, 'config.ini'))
APP_DIR   = os.path.join(BASE_DIR, _topo.get('topology', 'application_dir', fallback='application'))
WORK_DIR  = os.path.join(BASE_DIR, _topo.get('topology', 'workspace_dir', fallback='engagement'))
_APP_DATA = os.path.join(APP_DIR, _topo.get('topology', 'app_data_dir', fallback='data'))

_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(APP_DIR, 'config', 'domain.ini'))

# Rendered markdown methodology lives in the workspace; it is a GENERATED artifact
# mirrored from the YAML source-of-truth that ships under application/<data>/.
METHODOLOGY_DIR        = os.path.join(WORK_DIR, _cfg.get('methodology', 'directory', fallback='methodology'))
# YAML source-of-truth for the methodology. The markdown in METHODOLOGY_DIR is
# now a GENERATED artifact rendered from these YAML files.
METHODOLOGY_YAML_DIR   = os.path.join(_APP_DATA, _cfg.get('methodology', 'yaml_directory', fallback='methodology_yaml'))
PLACEHOLDERS_FILE      = os.path.join(APP_DIR, 'config', 'placeholders.yaml')
EXECUTION_TEMPLATES_DIR = os.path.join(WORK_DIR, 'templates', 'execution', 'iteration')
WORKSPACE_DIR          = os.path.join(WORK_DIR, 'execution')

SHOW_DETAILED_DIFF = False
ENABLE_SAFETY_CATCH = True

import re
HEADER_PATTERN     = re.compile(r'^##\s+(.*)')
TASK_PATTERN       = re.compile(r'^\*\*(.+?)\*\*[\s]*$')

# Section headings treated as generic prose (their tasks fall under "General"
# and render without a sub-heading). This framework has none, but the constant
# is shared by the markdown parser and the YAML->methodology_data adapter so
# both stay in agreement. Keep as [] unless generic headers are introduced.
GENERIC_HEADERS = []
