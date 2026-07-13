"""
Render the human-readable methodology markdown from the YAML source.

The markdown in METHODOLOGY_DIR is a build artifact: this module rebuilds it
from `methodology_yaml/*.yaml`. Prose, fenced code, per-task bodies and
interleaved sub-headings are all preserved.

NOTE (framework-specific): this framework's tasks are body-less checklist items
packed densely with NO blank lines between them. The renderer therefore only
emits a trailing blank line after a task that actually has a body — emitting one
after every task (as the pentest reference does) would inject spurious blanks.
"""
import os

from core.config import METHODOLOGY_DIR, METHODOLOGY_YAML_DIR
from core.yaml_store import load_docs


def render_doc(doc):
    """Render one methodology document dict back into markdown text."""
    out = []
    if doc.get('title'):
        out.append(f"# {doc['title']}")
        out.append("")
    if doc.get('preamble'):
        out.append(doc['preamble'])
        out.append("")
    for section in doc.get('sections', []):
        heading = section.get('heading')
        if heading:
            out.append(f"## {heading}")
            out.append("")
        if section.get('body'):
            out.append(section['body'])
            out.append("")
        for task in section.get('tasks', []) or []:
            if task.get('lead'):
                out.append(task['lead'])
                out.append("")
            out.append(f"**{task['name']}**")
            if task.get('body'):
                out.append(task['body'])
                # Only body-carrying tasks get a trailing blank separator.
                # Body-less checklist tasks stay densely packed.
                out.append("")
    return "\n".join(out).rstrip() + "\n"


def regenerate_methodology_docs(docs=None, methodology_dir=METHODOLOGY_DIR, quiet=False):
    """Write METHODOLOGY_DIR/<phase>/<file>.md for every YAML doc. Returns count."""
    if docs is None:
        docs = load_docs(METHODOLOGY_YAML_DIR)
    count = 0
    for phase, files in docs.items():
        for md_name, doc in files.items():
            path = os.path.join(methodology_dir, phase, md_name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(render_doc(doc))
            if not quiet:
                print(f"[+] Rendered methodology doc -> {phase}/{md_name}")
            count += 1
    return count
