import os
import configparser
BASE_DIR          = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# --- Two-root topology (BASE_DIR/config.ini): the YAML methodology database
#     ships with the tool under application/<data>/<yaml_dir>. ---
_topo = configparser.ConfigParser()
_topo.read(os.path.join(BASE_DIR, 'config.ini'))
APP_DIR   = os.path.join(BASE_DIR, _topo.get('topology', 'application_dir', fallback='application'))
_APP_DATA = os.path.join(APP_DIR, _topo.get('topology', 'app_data_dir', fallback='data'))

_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(APP_DIR, 'config', 'domain.ini'))

# The master source of truth is the YAML methodology database (methodology_yaml/).
# The markdown in the workspace's methodology/ is a GENERATED artifact — after a
# restore, regenerate it with the Template Engine (template_generator -> Option 3).
METHODOLOGY_DIR   = os.path.join(_APP_DATA, _cfg.get('methodology', 'yaml_directory', fallback='methodology_yaml'))
BACKUPS_DIR       = os.path.join(os.path.dirname(__file__), '..', 'backups')
