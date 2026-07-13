"""
Single-command population — two modes (chosen in Settings):

  paste  : type/paste a command in the terminal, get it back populated.
  buffer : read a staging file with a `## Values` section (pinned choices) and a
           `## Commands` section (templates), and (re)write a `## Populated`
           section with the filled commands. Templates are preserved for re-runs.
"""
import os
import re

from core.config import load_vocab
from core.settings import load_settings
from modules.data_source import load_engagement_data, source_signature, describe_source
from modules.populate import ValueResolver, populate_text

SECTION_RE = re.compile(r'^##\s+(.+?)\s*$')


# ----------------------------- paste mode -----------------------------

def populate_pasted():
    """Fast paste-loop: data loads once, you paste command after command.

    Reloads automatically when the source file changes on disk; `r` forces a
    reload, `q` (or empty line) exits. Multi-value fields prompt once and the
    choice is reused across the whole session.
    """
    vocab = load_vocab()
    settings = load_settings()
    data = load_engagement_data(settings)
    resolver = ValueResolver(data, vocab, correlate=True)
    sig = source_signature(settings)

    print("\n" + "=" * 60)
    print(f" PASTE-AND-POPULATE  —  source: {describe_source(settings)}")
    print("=" * 60)
    print(" Paste a command (with <TOKENS>) + Enter → filled command back.")
    print(" <ADMIN_USER> filters to admin accounts; creds stay account-correct.")
    print(" [r] reload data   [q] or empty line → done")
    print(f" {len(data)} field(s) loaded.")
    print("-" * 60)

    while True:
        try:
            line = input("\n[paste] ")
        except EOFError:
            break
        cmd = line.strip()
        if cmd.lower() in ('q', 'quit', 'exit') or cmd == '':
            break
        if cmd.lower() in ('r', 'reload'):
            data = load_engagement_data(settings)
            resolver = ValueResolver(data, vocab, correlate=True)
            sig = source_signature(settings)
            print(f"[+] reloaded — {len(data)} field(s).")
            continue

        new_sig = source_signature(settings)
        if new_sig != sig:
            data = load_engagement_data(settings)
            resolver = ValueResolver(data, vocab, correlate=True)
            sig = new_sig
            print("[*] data changed on disk — reloaded.")

        resolver.reset_accounts()          # each pasted command picks its own account
        result, unmet = populate_text(line, resolver, vocab)
        print("   " + result)
        if unmet:
            toks = ", ".join(f"<{vocab['key_to_token'].get(k, k)}>" for k in sorted(unmet))
            print(f"   [!] unfilled: {toks}")


# ----------------------------- buffer mode ----------------------------

def _split_sections(text):
    """Return ordered list of (heading, body_text)."""
    sections, heading, buf = [], None, []
    for line in text.split('\n'):
        m = SECTION_RE.match(line)
        if m:
            if heading is not None:
                sections.append((heading, "\n".join(buf).strip('\n')))
            heading, buf = m.group(1), []
        else:
            buf.append(line)
    if heading is not None:
        sections.append((heading, "\n".join(buf).strip('\n')))
    return sections


def _parse_values(body, valid_keys):
    overrides = {}
    for line in body.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([a-z][a-z0-9_]*):\s*(.*)$', line)
        if m and m.group(1) in valid_keys and m.group(2).strip():
            overrides[m.group(1)] = m.group(2).strip()
    return overrides


def run_buffer(interactive=True):
    vocab = load_vocab()
    settings = load_settings()
    buffer_path = settings.get('buffer_file')

    if not os.path.exists(buffer_path):
        write_buffer_template(buffer_path)
        print(f"[+] Created a starter buffer file: {buffer_path}")
        print("    Add command templates under '## Commands', then run again.")
        return

    with open(buffer_path, 'r', encoding='utf-8') as f:
        original = f.read()

    sections = _split_sections(original)
    values_body = next((b for h, b in sections if h.lower().startswith('values')), "")
    commands_body = next((b for h, b in sections if h.lower().startswith('commands')), "")

    overrides = _parse_values(values_body, set(vocab['key_to_token'].keys()))
    data = load_engagement_data(settings)
    resolver = ValueResolver(data, vocab, overrides=overrides,
                             auto=not interactive, correlate=True)

    populated_lines, unmet_all = [], set()
    for line in commands_body.split('\n'):
        if not line.strip() or line.strip().startswith('#'):
            continue
        resolver.reset_accounts()          # each command line picks its own account
        filled, unmet = populate_text(line, resolver, vocab)
        populated_lines.append(filled)
        unmet_all |= unmet

    # rebuild: keep Values + Commands verbatim, refresh Populated
    kept = [(h, b) for h, b in sections if not h.lower().startswith('populated')]
    rebuilt = []
    for h, b in kept:
        rebuilt.append(f"## {h}")
        if b:
            rebuilt.append(b)
        rebuilt.append("")
    rebuilt.append("## Populated")
    rebuilt.append("<!-- auto-generated on each run — copy from here -->")
    rebuilt.append("")
    rebuilt.extend(populated_lines if populated_lines else ["_(no command templates found)_"])
    rebuilt.append("")

    with open(buffer_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(rebuilt).rstrip() + "\n")

    print(f"[+] Populated {len(populated_lines)} command(s) -> {buffer_path} (## Populated)")
    if unmet_all:
        toks = ", ".join(f"<{vocab['key_to_token'].get(k, k)}>" for k in sorted(unmet_all))
        print(f"[!] No value for: {toks} (left as placeholders).")


def write_buffer_template(path):
    tmpl = (
        "# Command Buffer — execution staging\n\n"
        "## Values\n"
        "# Pin specific values here as `field: value` (overrides loadout.md).\n"
        "# Leave blank to use loadout.md (you'll be prompted for multi-value fields).\n"
        "target_ip: \n"
        "dc_ip: \n\n"
        "## Commands\n"
        "# Paste command templates containing <TOKENS>. Example:\n"
        "# nmap -sV -p- <TARGET_IP>\n"
        "# nxc smb <DC_IP> -u <USERNAME> -p <PASSWORD>\n\n"
        "## Populated\n"
        "<!-- auto-generated on each run — copy from here -->\n"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(tmpl)
    return path
