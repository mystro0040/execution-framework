"""
ONE-TIME migration: import the existing markdown methodology corpus into the
YAML source-of-truth tree, applying placeholder-token normalization on the way
in.

After this runs, `methodology_yaml/*.yaml` is authoritative and
`methodology/*.md` is regenerated from it (see modules/ttp_docs_gen.py). Safe to
re-run: it overwrites the YAML tree from the current markdown. Keep for
reference / disaster recovery.

    python3 tools/import_markdown_to_yaml.py

Framework notes:
  - Some methodology files start directly with `##` and have NO `# H1 title`.
    parse_markdown handles that: title stays None.
  - This framework has no <PLACEHOLDER> tokens; the alias map is a harmless
    no-op, but is kept so future tokens normalize automatically.
"""
import os
import re
import sys

# make `core` / `modules` importable when run directly from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml  # noqa: E402
from core.config import METHODOLOGY_DIR, METHODOLOGY_YAML_DIR, PLACEHOLDERS_FILE  # noqa: E402
from core.yaml_store import dump_doc  # noqa: E402

H1 = re.compile(r'^#\s+(.+?)\s*$')
H2 = re.compile(r'^##(?!#)\s+(.+?)\s*$')
TASK = re.compile(r'^\*\*(.+?)\*\*\s*$')
TOKEN = re.compile(r'<([A-Za-z][A-Za-z0-9_ ]*)>')


def _slug(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def build_alias_map():
    """token-as-written -> canonical token, from placeholders.yaml."""
    vocab = yaml.safe_load(open(PLACEHOLDERS_FILE, encoding='utf-8')) or {}
    alias_to_canon = {}
    for canon, spec in (vocab.get('fields') or {}).items():
        alias_to_canon[canon] = canon
        for a in ((spec or {}).get('aliases') or []):
            alias_to_canon[a] = canon
    return alias_to_canon


def normalize_tokens(text, alias_to_canon):
    """Rewrite <alias> -> <CANONICAL>. Unknown / ignored tokens untouched."""
    def repl(m):
        inner = m.group(1)
        canon = alias_to_canon.get(inner)
        return f"<{canon}>" if canon else m.group(0)
    return TOKEN.sub(repl, text)


def _strip_block(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) if lines else None


def _parse_section(heading, sec_lines):
    section = {}
    if heading is not None:
        section['heading'] = heading
    tasks = []
    lead_buf = []
    body_lines = None
    cur_task = None
    cur_body = []
    seen_task = False

    def flush_task():
        nonlocal cur_task, cur_body
        if cur_task is not None:
            b = _strip_block(list(cur_body))
            if b is not None:
                cur_task['body'] = b
            tasks.append(cur_task)
        cur_task, cur_body = None, []

    for line in sec_lines:
        m = TASK.match(line)
        if m:
            flush_task()
            name = m.group(1).strip()
            lead = _strip_block(list(lead_buf))
            lead_buf = []
            if not seen_task:
                body_lines = lead
                seen_task = True
            cur_task = {'id': _slug(name), 'name': name}
            if tasks and lead is not None:
                cur_task['lead'] = lead
            cur_body = []
        else:
            (cur_body if cur_task is not None else lead_buf).append(line)
    flush_task()

    if not seen_task:
        body_lines = _strip_block(list(lead_buf))
    if body_lines is not None:
        section['body'] = body_lines
    if tasks:
        section['tasks'] = tasks
    return section


def parse_markdown(text):
    lines = text.replace('\r\n', '\n').split('\n')
    idx = 0
    title = None
    while idx < len(lines):
        if not lines[idx].strip():
            idx += 1
            continue
        m = H1.match(lines[idx])
        if m:
            title = m.group(1).strip()
            idx += 1
        break

    doc = {'title': title, 'sections': []}
    preamble = []
    cur = None
    for line in lines[idx:]:
        h2 = H2.match(line)
        if h2:
            if cur is not None:
                doc['sections'].append(_parse_section(cur['heading'], cur['_lines']))
                cur = None
            cur = {'heading': h2.group(1).strip(), '_lines': []}
        else:
            (cur['_lines'] if cur is not None else preamble).append(line)
    if cur is not None:
        doc['sections'].append(_parse_section(cur['heading'], cur['_lines']))

    pre = _strip_block(preamble)
    if pre:
        doc['preamble'] = pre
    return doc


def run(methodology_dir=METHODOLOGY_DIR, out_dir=METHODOLOGY_YAML_DIR):
    alias_to_canon = build_alias_map()
    count = 0
    for root, _, files in os.walk(methodology_dir):
        for fn in sorted(files):
            if not fn.endswith('.md'):
                continue
            src = os.path.join(root, fn)
            rel = os.path.relpath(src, methodology_dir)
            with open(src, encoding='utf-8') as f:
                text = f.read()
            text = normalize_tokens(text, alias_to_canon)
            doc = parse_markdown(text)
            out = os.path.join(out_dir, rel[:-3] + '.yaml')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, 'w', encoding='utf-8') as f:
                f.write(dump_doc(doc))
            print(f"[+] Imported -> {rel[:-3]}.yaml")
            count += 1
    print(f"\n[+] Imported {count} methodology files into {out_dir}")
    return count


if __name__ == '__main__':
    run()
