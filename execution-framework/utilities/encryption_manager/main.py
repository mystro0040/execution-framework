#!/usr/bin/env python3
import os, sys, getpass

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402
from core.config import VAULT_TARGETS  # noqa: E402
from modules.crypto_engine import encrypt_directory, decrypt_directory  # noqa: E402

def get_password(prompt, confirm=False):
    pw = getpass.getpass(prompt)
    if pw.lower() == 'q': return None
    if confirm:
        if pw != getpass.getpass("Confirm password: "):
            print("\033[91m[-] Passwords do not match.\033[0m"); return None
    return pw

def process(key, action, pw):
    t = VAULT_TARGETS[key]
    print(f"\n[*] Target: {t['label']}")
    if action == 'encrypt':
        if not os.path.exists(t['dir_path']): print("[-] Already locked or missing."); return
        success, msg = encrypt_directory(t['dir_path'], t['encrypted'], t['salt'], pw)
        print(f"\033[92m[+] {msg}\033[0m" if success else f"\033[91m[-] {msg}\033[0m")
    elif action == 'decrypt':
        if not os.path.exists(t['encrypted']): print("[-] No vault found."); return
        success, msg = decrypt_directory(t['encrypted'], t['dir_path'], t['salt'], pw)
        print(f"\033[92m[+] {msg}\033[0m" if success else f"\033[91m[-] {msg}\033[0m")

def lock_workspace():
    pw = get_password("Create password (or q): ", confirm=True)
    if pw:
        for k in ['data', 'execution', 'reports']: process(k, 'encrypt', pw)

def unlock_workspace():
    pw = get_password("Enter password (or q): ")
    if pw:
        for k in ['data', 'execution', 'reports']: process(k, 'decrypt', pw)

def _render(title, menu):
    print("=" * 60)
    print(" SECURE WORKSPACE ENCRYPTION")
    print("=" * 60)
    print("[1] Lock Workspace   (Encrypt data/, execution/, reports/)")
    print("[2] Unlock Workspace (Decrypt data/, execution/, reports/)")
    print("-" * 60)
    print("[Q] Quit")
    print("=" * 60)

def main():
    menu = {
        "1": {"desc": "Lock Workspace", "action": lock_workspace},
        "2": {"desc": "Unlock Workspace", "action": unlock_workspace},
    }
    run_menu(menu, "SECURE WORKSPACE ENCRYPTION", render=_render,
             prompt_text="\nSelect an option: ")

if __name__ == "__main__":
    main()
