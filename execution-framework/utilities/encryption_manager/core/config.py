import os
import configparser
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# --- Two-root topology (BASE_DIR/config.ini): the encryptable engagement data
#     all lives in the active workspace (engagement/). ---
_topo = configparser.ConfigParser()
_topo.read(os.path.join(BASE_DIR, 'config.ini'))
WORK_DIR = os.path.join(BASE_DIR, _topo.get('topology', 'workspace_dir', fallback='engagement'))

ENABLE_SAFE_MODE = True

VAULT_TARGETS = {
    "data": {
        "label": "Project Data (data/)",
        "dir_path": os.path.join(WORK_DIR, 'data'),
        "encrypted": os.path.join(WORK_DIR, 'data', 'vault.enc'),
        "salt": os.path.join(WORK_DIR, 'data', 'salt.bin')
    },
    "execution": {
        "label": "Execution Logs (execution/)",
        "dir_path": os.path.join(WORK_DIR, 'execution'),
        "encrypted": os.path.join(WORK_DIR, 'execution', 'vault.enc'),
        "salt": os.path.join(WORK_DIR, 'execution', 'salt.bin')
    },
    "reports": {
        "label": "Generated Reports (reports/)",
        "dir_path": os.path.join(WORK_DIR, 'reports'),
        "encrypted": os.path.join(WORK_DIR, 'reports', 'vault.enc'),
        "salt": os.path.join(WORK_DIR, 'reports', 'salt.bin')
    }
}
