import os, shutil, zipfile
from datetime import datetime
from core.config import METHODOLOGY_DIR, BACKUPS_DIR


def _safe_extract(zipf, dest):
    """Zip-slip guard: refuse any member that would resolve outside dest."""
    dest = os.path.realpath(dest)
    for m in zipf.namelist():
        target = os.path.realpath(os.path.join(dest, m))
        if target != dest and not target.startswith(dest + os.sep):
            raise ValueError(f"Unsafe path in archive: {m}")
    zipf.extractall(dest)

def create_backup():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path  = os.path.join(BACKUPS_DIR, f"methodology_yaml_{timestamp}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(METHODOLOGY_DIR):
            for file in files:
                fp = os.path.join(root, file)
                zf.write(fp, os.path.relpath(fp, os.path.dirname(METHODOLOGY_DIR)))
    print(f"[+] Backup created: {os.path.basename(zip_path)}")
    return zip_path

def list_backups():
    if not os.path.exists(BACKUPS_DIR):
        print("[-] No backups found.")
        return []
    backups = sorted([f for f in os.listdir(BACKUPS_DIR) if f.endswith('.zip')])
    if not backups:
        print("[-] No backups found.")
    for i, b in enumerate(backups, 1):
        print(f"  [{i}] {b}")
    return backups

def restore_backup(zip_path):
    if not os.path.exists(zip_path):
        print(f"[-] Backup not found: {zip_path}")
        return False
    if os.path.exists(METHODOLOGY_DIR):
        shutil.rmtree(METHODOLOGY_DIR)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        _safe_extract(zf, os.path.dirname(METHODOLOGY_DIR))
    print(f"[+] Methodology YAML source restored from: {os.path.basename(zip_path)}")
    print("    -> Regenerate methodology/*.md via template_generator Option 3.")
    return True
