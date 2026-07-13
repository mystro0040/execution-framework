import os
import difflib
from core.config import EXECUTION_TEMPLATES_DIR, SHOW_DETAILED_DIFF
from utils.helpers import slugify, read_file


def print_detailed_diff(filename, actual_text, expected_text):
    print(f"\n\033[93m[!] MISMATCH DETECTED: {filename}\033[0m")
    print("=" * 70)
    actual_lines  = actual_text.splitlines()
    expected_lines = expected_text.splitlines()
    matcher = difflib.SequenceMatcher(None, actual_lines, expected_lines)
    issue_count = 1
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        print(f"\033[96m--- Issue #{issue_count} ---\033[0m")
        if tag == 'replace':
            print(f"Type:        \033[93mContent Modified\033[0m")
            print(f"Line(s):     {i1 + 1} to {i2}")
            print("Problem:     \033[91m" + "\n             ".join(actual_lines[i1:i2]) + "\033[0m")
            print("Changing To: \033[92m" + "\n             ".join(expected_lines[j1:j2]) + "\033[0m")
        elif tag == 'delete':
            print(f"Type:        \033[91mExtra Content\033[0m")
            print("Problem:     \033[91m" + "\n             ".join(actual_lines[i1:i2]) + "\033[0m")
            print("Changing To: \033[92m(will be removed)\033[0m")
        elif tag == 'insert':
            print(f"Type:        \033[92mMissing Content\033[0m")
            print("Changing To: \033[92m" + "\n             ".join(expected_lines[j1:j2]) + "\033[0m")
        print()
        issue_count += 1
    print("=" * 70)


def generate_file_markdown(file_name, categories):
    clean_title = file_name.replace('.md', '').replace('_', ' ').title()
    parts = clean_title.split(' ', 1)
    if len(parts) == 2 and parts[0].isdigit():
        clean_title = parts[1]

    md = [f"# {clean_title}\n"]

    md.append("## Checklist")
    for category, items in categories.items():
        if not items:
            continue
        if category != "General":
            md.append(f"\n### {category}")
        for item in items:
            anchor    = slugify(item)
            cl_anchor = f"cl-{anchor}"
            md.append(f'<a id="{cl_anchor}"></a>')
            md.append(f"- [ ] **[{item}](#{anchor})**")

    md.append("\n---\n")

    md.append("## Execution Notes\n")
    for category, items in categories.items():
        if not items:
            continue
        if category != "General":
            md.append(f"### {category}\n")
        for item in items:
            anchor    = slugify(item)
            cl_anchor = f"cl-{anchor}"
            md.append(f'<a id="{anchor}"></a>')
            md.append(f"**[{item}](#{cl_anchor})**")
            md.append("  <details>")
            md.append("  <summary><i>Execution Notes</i></summary>\n")
            md.append("  > *Log execution details here.*\n")
            md.append("  </details>")
            md.append("  <br>\n")

    return "\n".join(md)


def generate_master_log(methodology_data):
    def clean_phase(phase_folder):
        parts = phase_folder.split('_', 1)
        label = parts[1] if len(parts) == 2 and parts[0].isdigit() else phase_folder
        return label.replace('_', ' ').title()

    def clean_file(file_name):
        name = file_name.replace('.md', '')
        parts = name.split('_', 1)
        label = parts[1] if len(parts) == 2 and parts[0].isdigit() else name
        return label.replace('_', ' ').title()

    def phase_anchor(phase_folder):
        return slugify(clean_phase(phase_folder))

    active_phases = [
        p for p in sorted(methodology_data.keys())
        if any(any(len(i) > 0 for i in cats.values()) for cats in methodology_data[p].values())
    ]

    md = ["# Master Log\n"]

    md.append("## Checklist\n")
    for phase_folder in active_phases:
        anchor    = phase_anchor(phase_folder)
        cl_anchor = f"cl-{anchor}"
        md.append(f'<a id="{cl_anchor}"></a>')
        md.append(f"- [ ] **[{clean_phase(phase_folder)}](#{anchor})**")
        for file_name in sorted(methodology_data[phase_folder].keys()):
            if not any(len(i) > 0 for i in methodology_data[phase_folder][file_name].values()):
                continue
            md.append(f"  - [ ] **{clean_file(file_name)}**")
        md.append("")

    md.append("\n---\n")

    md.append("## Execution Notes\n")
    for phase_folder in active_phases:
        anchor    = phase_anchor(phase_folder)
        cl_anchor = f"cl-{anchor}"
        md.append(f'<a id="{anchor}"></a>')
        md.append(f"**[{clean_phase(phase_folder)}](#{cl_anchor})**")
        md.append("  <details>")
        md.append("  <summary><i>Phase Notes</i></summary>\n")
        md.append("  > *Log phase-level outcomes, key artifacts, and completion status here.*\n")
        md.append("  </details>")
        md.append("  <br>\n")

    content = "\n".join(md)
    output_path = os.path.join(EXECUTION_TEMPLATES_DIR, "00_master_log.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Generated -> 00_master_log.md")
    return content


def get_master_log_content(methodology_data):
    return generate_master_log(methodology_data)


def analyze_discrepancies(methodology_data, template_directory):
    discrepancies = []

    expected_master = get_master_log_content(methodology_data)
    master_path = os.path.join(template_directory, "00_master_log.md")
    actual_master = read_file(master_path)

    if not actual_master:
        discrepancies.append(("Master", "00_master_log.md", expected_master, "Missing"))
    elif expected_master.strip() != actual_master.strip():
        discrepancies.append(("Master", "00_master_log.md", expected_master, "Mismatch"))
        if SHOW_DETAILED_DIFF:
            print_detailed_diff("00_master_log.md", actual_master.strip(), expected_master.strip())

    for phase_folder, files in methodology_data.items():
        for file_name, categories in files.items():
            if not any(len(items) > 0 for items in categories.values()):
                continue
            relative_path = os.path.join(phase_folder, file_name)
            filepath      = os.path.join(template_directory, relative_path)
            expected_md   = generate_file_markdown(file_name, categories)
            actual_md     = read_file(filepath)
            if not actual_md:
                discrepancies.append((phase_folder, relative_path, expected_md, "Missing"))
            elif expected_md.strip() != actual_md.strip():
                discrepancies.append((phase_folder, relative_path, expected_md, "Mismatch"))
                if SHOW_DETAILED_DIFF:
                    print_detailed_diff(relative_path, actual_md.strip(), expected_md.strip())

    return discrepancies
