"""Persistent settings for loadout_manager (JSON next to the code)."""
import json
import os
from core.config import (
    BASE_DIR,
    SETTINGS_FILE, PLAYBOOK_DIR, BUFFER_FILE, LOADOUT_FILE,
    SESSION_FILE, ENGAGEMENT_DIR,
)

# Keys whose values are filesystem paths that MUST stay inside this framework
# instance. A settings.json copied from another tree (or one that shipped with
# absolute paths) must never redirect writes back into the original/live tree.
_PATH_KEYS = ('loadout_file', 'session_file', 'engagement_dir',
              'buffer_file', 'playbook_dir')


def _resolve_path(value, default):
    """Resolve a settings path against THIS framework root (BASE_DIR).

    - Relative fragments are anchored to BASE_DIR.
    - Absolute paths are honoured only if they point INSIDE this framework
      instance; anything outside (e.g. a stale absolute path copied from
      another checkout) is discarded in favour of the computed default.
    """
    if not value:
        return default
    if not os.path.isabs(value):
        value = os.path.join(BASE_DIR, value)
    value = os.path.abspath(value)
    root = os.path.abspath(BASE_DIR)
    if value == root or value.startswith(root + os.sep):
        return value
    return default

DEFAULTS = {
    # where the tool reads collected engagement data from:
    #   "session_yaml"   -> a single YAML data scratchpad (Micro scope) — default
    #   "loadout_md"     -> the markdown quick-capture loadout.md (legacy)
    #   "engagement_dir" -> the full engagement YAML fact tree (Global scope)
    # YAML is the data layer (doctrine); session.yaml is the default single file.
    "data_source": "session_yaml",
    "loadout_file": LOADOUT_FILE,
    "session_file": SESSION_FILE,
    "engagement_dir": ENGAGEMENT_DIR,
    # single-command populate: "paste" (interactive paste-loop) or
    # "buffer" (read + rewrite a staging file).
    "single_command_mode": "paste",
    "buffer_file": BUFFER_FILE,
    "playbook_dir": PLAYBOOK_DIR,
    # include tasks that reference NO engagement placeholders at all
    # (always-applicable prose/manual techniques). Off = only tasks that
    # actually consume at least one loadout value.
    "include_requirementless_tasks": True,
    # applicable-playbook granularity: True = filter PER COMMAND (a structured
    # task shows only the individual commands whose <TOKENS> you have data for);
    # False = per TASK (drop the whole task if any of its tokens are unmet).
    # Legacy prose/`body:` tasks always filter per-task regardless.
    "per_command_applicability": True,
}


def load_settings():
    data = dict(DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data.update(json.load(f))
        except (ValueError, OSError):
            pass
    # Keep every path setting scoped to THIS framework instance (see
    # _resolve_path) so the tool never writes into another/live tree.
    for key in _PATH_KEYS:
        data[key] = _resolve_path(data.get(key), DEFAULTS[key])
    return data


def save_settings(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
