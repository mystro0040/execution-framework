"""
Generate an "applicable playbook": a mirrored TTP directory containing only the
tasks whose placeholder requirements the current loadout satisfies, with every
command pre-populated. Re-runnable — wipes and rebuilds, so tasks appear/vanish
as the loadout changes.
"""
import os
import shutil
import yaml

from core.config import TTP_YAML_DIR, load_vocab
from core.settings import load_settings
from modules.loadout_parser import parse_loadout, available_keys
from modules.data_source import load_engagement_data
from modules.populate import ValueResolver, canonical_fields_in, populate_text


def _load_docs(yaml_dir=TTP_YAML_DIR):
    docs = {}
    if not os.path.isdir(yaml_dir):
        return docs
    for phase in sorted(os.listdir(yaml_dir)):
        pdir = os.path.join(yaml_dir, phase)
        if not os.path.isdir(pdir):
            continue
        docs[phase] = {}
        for fn in sorted(os.listdir(pdir)):
            if fn.endswith('.yaml'):
                with open(os.path.join(pdir, fn), 'r', encoding='utf-8') as f:
                    docs[phase][fn[:-5] + '.md'] = yaml.safe_load(f) or {}
    return docs


def _task_text(task):
    return "\n".join(filter(None, [task.get('lead'), task.get('body')]))


def _render(doc):
    out = []
    if doc.get('title'):
        out += [f"# {doc['title']}", ""]
    for section in doc.get('sections', []):
        if section.get('heading'):
            out += [f"## {section['heading']}", ""]
        if section.get('body'):
            out += [section['body'], ""]
        for task in section.get('tasks', []) or []:
            if task.get('lead'):
                out += [task['lead'], ""]
            out.append(f"**{task['name']}**")
            if task.get('body'):
                out.append(task['body'])
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def generate_playbook(loadout_path=None, interactive=True):
    vocab = load_vocab()
    settings = load_settings()
    data = load_engagement_data(settings, path=loadout_path)   # loadout.md / session.yaml / engagement dir
    available = available_keys(data)
    include_reqless = settings.get('include_requirementless_tasks', True)

    docs = _load_docs()
    if not docs:
        print(f"[-] No YAML methodology found at {TTP_YAML_DIR}")
        return None

    # -- Pass 1: decide inclusion, collect the fields actually used --
    filtered = {}
    used_fields = set()
    stats = {'files': 0, 'tasks_kept': 0, 'tasks_excluded': 0}
    for phase, files in docs.items():
        for md_name, doc in files.items():
            new_sections = []
            for section in doc.get('sections', []):
                kept = []
                for task in section.get('tasks', []) or []:
                    fields = canonical_fields_in(_task_text(task), vocab)
                    if fields - available:            # needs data we don't have
                        stats['tasks_excluded'] += 1
                        continue
                    if not fields and not include_reqless:
                        continue
                    kept.append(task)
                    used_fields |= fields
                    stats['tasks_kept'] += 1
                if kept:
                    s = {'heading': section.get('heading')}
                    if section.get('body'):
                        s['body'] = section['body']
                    s['tasks'] = kept
                    new_sections.append(s)
            if new_sections:
                filtered.setdefault(phase, {})[md_name] = {
                    'title': doc.get('title'), 'sections': new_sections}
                stats['files'] += 1

    if not filtered:
        print("[-] No applicable TTPs for the current loadout.")
        print("    Add values to loadout.md (or relax the requirement-less setting).")
        return None

    # -- Resolve each used field once (prompt for multi-value now, in order) --
    resolver = ValueResolver(data, vocab, auto=not interactive)
    if used_fields:
        print(f"\n[*] Resolving {len(used_fields)} engagement value(s)...")
    for key in sorted(used_fields):
        resolver.resolve(key)

    # -- Pass 2: populate + write --
    out_dir = settings.get('playbook_dir')
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    for phase, files in filtered.items():
        for md_name, doc in files.items():
            for section in doc['sections']:
                if section.get('body'):
                    section['body'], _ = populate_text(section['body'], resolver, vocab)
                for task in section['tasks']:
                    if task.get('lead'):
                        task['lead'], _ = populate_text(task['lead'], resolver, vocab)
                    if task.get('body'):
                        task['body'], _ = populate_text(task['body'], resolver, vocab)
            path = os.path.join(out_dir, phase, md_name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(_render(doc))

    _write_summary(out_dir, resolver, used_fields, vocab, stats)
    print(f"\n[+] Applicable playbook generated -> {out_dir}")
    print(f"    {stats['files']} files | {stats['tasks_kept']} tasks kept | "
          f"{stats['tasks_excluded']} excluded (missing data)")
    return out_dir


def _write_summary(out_dir, resolver, used_fields, vocab, stats):
    lines = ["# Loadout Playbook — Summary", "",
             "Generated from the current loadout. Values used:", ""]
    if used_fields:
        for key in sorted(used_fields):
            token = vocab['key_to_token'].get(key, key)
            lines.append(f"- `<{token}>` = `{resolver.cache.get(key, '(unset)')}`")
    else:
        lines.append("_(no placeholder values were required)_")
    lines += ["", f"**{stats['files']}** files · **{stats['tasks_kept']}** tasks "
              f"kept · **{stats['tasks_excluded']}** excluded for missing data.", ""]
    with open(os.path.join(out_dir, "00_LOADOUT_SUMMARY.md"), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
