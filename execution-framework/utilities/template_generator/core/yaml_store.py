"""
YAML source-of-truth access for the methodology.

The `methodology_yaml/` YAML tree is the database. This module loads it, and —
crucially — adapts it into the exact `methodology_data` shape the rest of the
engine already consumes:

    { "PhaseFolder": { "file.md": { "Category": ["Task Name", ...] } } }

Because task names and category grouping are preserved verbatim, every
downstream consumer (execution templates, linter, next-iteration, reporting)
keeps producing identical output.
"""
import os
import yaml

from core.config import METHODOLOGY_YAML_DIR, PLACEHOLDERS_FILE, GENERIC_HEADERS


# --- authoring-friendly YAML dumper: multiline strings as literal | blocks ---
class BlockDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


BlockDumper.add_representer(str, _str_presenter)


def dump_doc(doc):
    """Serialize a single methodology document dict to authoring-friendly YAML."""
    return yaml.dump(
        doc, Dumper=BlockDumper, sort_keys=False,
        allow_unicode=True, width=10 ** 9, default_flow_style=False,
    )


def load_placeholders():
    """Load the canonical placeholder vocabulary (fields + ignore list)."""
    with open(PLACEHOLDERS_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_docs(yaml_dir=METHODOLOGY_YAML_DIR):
    """
    Load every methodology YAML file into:
        { "PhaseFolder": { "file.md": <doc dict> } }
    The .md key mirrors the eventual generated markdown filename.
    """
    docs = {}
    if not os.path.isdir(yaml_dir):
        return docs
    for phase in sorted(os.listdir(yaml_dir)):
        pdir = os.path.join(yaml_dir, phase)
        if not os.path.isdir(pdir) or phase == 'temp':
            continue
        docs[phase] = {}
        for fn in sorted(os.listdir(pdir)):
            if not fn.endswith('.yaml'):
                continue
            with open(os.path.join(pdir, fn), 'r', encoding='utf-8') as f:
                doc = yaml.safe_load(f) or {}
            docs[phase][fn[:-5] + '.md'] = doc
    return docs


def docs_to_methodology_data(docs):
    """
    Collapse the rich YAML docs into the legacy `methodology_data` shape consumed
    by the rest of the engine. Empty files (no tasks) are omitted, matching the
    old markdown parser exactly.
    """
    data = {}
    for phase, files in docs.items():
        data[phase] = {}
        for md_name, doc in files.items():
            categories = {}
            for section in (doc or {}).get('sections', []):
                heading = (section.get('heading') or 'General').strip()
                category = 'General' if heading in GENERIC_HEADERS else heading
                for task in section.get('tasks', []) or []:
                    name = (task.get('name') or '').strip()
                    if not name:
                        continue
                    bucket = categories.setdefault(category, [])
                    if name not in bucket:
                        bucket.append(name)
            if categories:
                data[phase][md_name] = categories
    return data


# Backwards/alias-friendly name mirroring the pentest reference API.
docs_to_ttp_data = docs_to_methodology_data


def load_methodology_data(yaml_dir=METHODOLOGY_YAML_DIR):
    """Convenience: load YAML and return legacy methodology_data in one call."""
    return docs_to_methodology_data(load_docs(yaml_dir))
