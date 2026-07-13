"""
LOADOUT MANAGER — playbook preparation & command population.

Collects engagement data, then:
  [1] generates an "applicable playbook" (only TTPs you have the data for,
      commands pre-populated), as a browsable mirrored TTP folder,
  [2] populates commands in a fast paste-loop (or via a staging buffer file).

Data can come from three sources (Settings):
  * loadout.md      — the markdown quick-capture (legacy)
  * session.yaml    — a single YAML data scratchpad (Micro scope)
  * engagement/     — the full engagement YAML fact tree (Global scope)

Self-contained: reads config/placeholders.yaml + ttps/*.yaml. Drop-in.
"""
import os
import sys

# --- locate the repo's shared cli/ package (walk up to the dir holding it) ---
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "cli")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from cli import run_menu  # noqa: E402
from core.config import LOADOUT_FILE, load_vocab  # noqa: E402
from core.settings import load_settings, save_settings  # noqa: E402
from modules.loadout_parser import write_template  # noqa: E402
from modules.playbook_gen import generate_playbook  # noqa: E402
from modules.single_command import populate_pasted, run_buffer  # noqa: E402
from modules.data_source import (  # noqa: E402
    load_engagement_data, describe_source, source_path, write_session_template,
)

SOURCES = ['loadout_md', 'session_yaml', 'engagement_dir']


def _create_missing_source(settings):
    """Offer to create a starter file for the active source, if it's missing."""
    source = settings.get('data_source', 'loadout_md')
    try:
        if source == 'session_yaml':
            p = settings.get('session_file')
            if input(f"    Create a starter session.yaml at {p}? (y/n): ").strip().lower() == 'y':
                write_session_template(p)
                print(f"[+] Created {p} — open it and add your data.")
        elif source == 'loadout_md':
            if input(f"    Create a starter loadout.md at {LOADOUT_FILE}? (y/n): ").strip().lower() == 'y':
                write_template()
                print(f"[+] Created {LOADOUT_FILE} — open it and add your data.")
        else:
            print(f"    Create the directory {settings.get('engagement_dir')} and add *.yaml fact files.")
    except EOFError:
        pass


def show_data():
    settings = load_settings()
    vocab = load_vocab()
    data = load_engagement_data(settings)
    print(f"\n[ DATA ]  source: {describe_source(settings)}")
    print(f"          path:   {source_path(settings)}")
    visible = sorted(k for k in data if not k.startswith('_'))
    if not visible:
        print("  (empty — no values resolved from this source)")
        _create_missing_source(settings)
        return
    for key in visible:
        token = vocab['key_to_token'].get(key, key)
        vals = data[key]
        shown = ", ".join(v['value'] + (f" ({v['label']})" if v.get('label') else "")
                          for v in vals)
        print(f"  <{token}>  [{len(vals)}]  {shown}")
    accounts = data.get('_accounts') or []
    if accounts:
        print(f"\n  accounts [{len(accounts)}] (correlated for paste mode):")
        for a in accounts:
            tag = " [admin]" if a.get('admin') else ""
            secret = a.get('password') or (f"hash:{a['nt_hash'][:16]}…" if a.get('nt_hash') else "(no secret)")
            print(f"    - {a.get('username') or '(no user)'} : {secret}{tag}")
    print(f"\n  {len(visible)} field(s) populated.")


def _settings_render(title, menu):
    s = load_settings()
    print("\n" + "=" * 60)
    print(" SETTINGS")
    print("=" * 60)
    print(f"[1] Data source ............... {describe_source(s)}")
    print(f"[2] session.yaml path ......... {s['session_file']}")
    print(f"[3] engagement/ dir ........... {s['engagement_dir']}")
    print(f"[4] Single-command mode ....... {s['single_command_mode']}  (paste/buffer)")
    print(f"[5] Buffer file ............... {s['buffer_file']}")
    print(f"[6] Playbook output dir ....... {s['playbook_dir']}")
    print(f"[7] Include requirement-less .. {s['include_requirementless_tasks']}")
    print(f"[8] Per-command applicability . {s['per_command_applicability']}  (else per-task)")
    print("-" * 60)
    print("[B] Back")


def _cycle_data_source():
    s = load_settings()
    i = SOURCES.index(s.get('data_source', 'loadout_md'))
    s['data_source'] = SOURCES[(i + 1) % len(SOURCES)]; save_settings(s)


def _set_session_path():
    s = load_settings()
    v = input("New session.yaml path (blank to cancel): ").strip()
    if v:
        s['session_file'] = os.path.abspath(os.path.expanduser(v)); save_settings(s)


def _set_engagement_dir():
    s = load_settings()
    v = input("New engagement/ dir (blank to cancel): ").strip()
    if v:
        s['engagement_dir'] = os.path.abspath(os.path.expanduser(v)); save_settings(s)


def _toggle_single_command_mode():
    s = load_settings()
    s['single_command_mode'] = 'buffer' if s['single_command_mode'] == 'paste' else 'paste'
    save_settings(s)


def _set_buffer_file():
    s = load_settings()
    v = input("New buffer file path (blank to cancel): ").strip()
    if v:
        s['buffer_file'] = os.path.abspath(os.path.expanduser(v)); save_settings(s)


def _set_playbook_dir():
    s = load_settings()
    v = input("New playbook output dir (blank to cancel): ").strip()
    if v:
        s['playbook_dir'] = os.path.abspath(os.path.expanduser(v)); save_settings(s)


def _toggle_requirementless():
    s = load_settings()
    s['include_requirementless_tasks'] = not s['include_requirementless_tasks']
    save_settings(s)


def _toggle_per_command():
    s = load_settings()
    s['per_command_applicability'] = not s['per_command_applicability']
    save_settings(s)


def settings_menu():
    menu = {
        "1": {"desc": "Data source", "action": _cycle_data_source},
        "2": {"desc": "session.yaml path", "action": _set_session_path},
        "3": {"desc": "engagement/ dir", "action": _set_engagement_dir},
        "4": {"desc": "Single-command mode", "action": _toggle_single_command_mode},
        "5": {"desc": "Buffer file", "action": _set_buffer_file},
        "6": {"desc": "Playbook output dir", "action": _set_playbook_dir},
        "7": {"desc": "Include requirement-less", "action": _toggle_requirementless},
        "8": {"desc": "Per-command applicability", "action": _toggle_per_command},
        "b": {"desc": "Back", "action": "BACK_FLAG"},
    }
    run_menu(menu, "SETTINGS", render=_settings_render, prompt_text="\nSelect: ")


def generate_playbook_action():
    generate_playbook()
    print("-" * 40)


def populate_commands_action():
    s = load_settings()
    if s['single_command_mode'] == 'buffer':
        run_buffer()
    else:
        populate_pasted()
    print("-" * 40)


def show_data_action():
    show_data()
    print("-" * 40)


def _render(title, menu):
    s = load_settings()
    print("=" * 60)
    print(" LOADOUT MANAGER — Playbook Preparation")
    print("=" * 60)
    print(f" data source: {describe_source(s)}")
    print("-" * 60)
    print("[1] Generate Applicable Playbook (browsable TTP folder)")
    print("[2] Populate Commands (paste-loop / buffer)")
    print("[3] Show / Create Data")
    print("[4] Settings")
    print("-" * 60)
    print("[C] Clear Screen | [Q] Quit")
    print("=" * 60)


def main():
    menu = {
        "1": {"desc": "Generate Applicable Playbook (browsable TTP folder)", "action": generate_playbook_action},
        "2": {"desc": "Populate Commands (paste-loop / buffer)", "action": populate_commands_action},
        "3": {"desc": "Show / Create Data", "action": show_data_action},
        "4": {"desc": "Settings", "action": settings_menu},
    }
    run_menu(menu, "LOADOUT MANAGER — Playbook Preparation", render=_render,
             prompt_text="\nSelect an option: ")
    print("\nExiting Loadout Manager.")


if __name__ == "__main__":
    main()
