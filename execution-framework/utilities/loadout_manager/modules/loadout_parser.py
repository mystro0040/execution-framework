"""
Parse the low-friction `loadout.md` quick-capture file into structured data.

Accepted, forgiving markdown syntax:

    target_ip: 10.10.10.5
    target_domain: acme.local          # inline comment (2+ spaces) = label
    dc_ip:
      - 10.10.10.1                      # DC01
      - 10.10.10.2                      # DC02

Returns: { field_key: [ {"value": str, "label": str|None}, ... ] }
Markdown headings, blank lines and HTML comments are ignored. Values may
contain '#'; only a '#' preceded by 2+ spaces is treated as a label.
"""
import os
import re

from core.config import LOADOUT_FILE, load_vocab

KEY_RE   = re.compile(r'^([a-z][a-z0-9_]*):\s*(.*)$')
BULLET_RE = re.compile(r'^\s*[-*]\s+(.*)$')
LABEL_RE = re.compile(r'^(.*?)\s{2,}#\s*(.*)$')


def _split_label(raw):
    raw = raw.strip()
    m = LABEL_RE.match(raw)
    if m:
        return m.group(1).strip(), m.group(2).strip() or None
    return raw, None


def parse_loadout(path=LOADOUT_FILE):
    """Parse loadout.md. Returns (data, unknown_keys)."""
    vocab = load_vocab()
    valid_keys = set(vocab['key_to_token'].keys())
    data = {}
    unknown = set()
    if not os.path.exists(path):
        return data, unknown

    current_key = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('<!--'):
                # markdown heading / comment / blank — but a bullet may follow a key
                if not BULLET_RE.match(line):
                    current_key = None
                continue

            bm = BULLET_RE.match(line)
            if bm and current_key:
                value, label = _split_label(bm.group(1))
                if value:
                    data.setdefault(current_key, []).append({'value': value, 'label': label})
                continue

            km = KEY_RE.match(stripped)
            if km:
                key, rest = km.group(1), km.group(2)
                if key not in valid_keys:
                    unknown.add(key)
                    current_key = None
                    continue
                current_key = key
                data.setdefault(key, [])
                if rest.strip():
                    value, label = _split_label(rest)
                    if value:
                        data[key].append({'value': value, 'label': label})
                continue

            current_key = None

    # drop keys that ended up with no values
    data = {k: v for k, v in data.items() if v}
    return data, unknown


def write_template(path=LOADOUT_FILE):
    """Create a starter loadout.md listing every canonical field with examples."""
    vocab = load_vocab()
    lines = [
        "# Loadout — collected engagement data",
        "",
        "> Quick-capture as you go. `field: value`, or a bulleted list for",
        "> multiple values. Add `  # label` (2+ spaces) to tag a value.",
        "> loadout_manager reads this to filter + populate applicable TTPs.",
        "",
    ]
    for key, meta in vocab['key_to_meta'].items():
        lines.append(f"# {meta['label']}  (e.g. {meta['example']})")
        lines.append(f"# {key}: ")
        lines.append("")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines).rstrip() + "\n")
    return path


def available_keys(data):
    """Field keys that have at least one value (reserved `_`-keys excluded)."""
    return {k for k, v in data.items() if v and not k.startswith('_')}
