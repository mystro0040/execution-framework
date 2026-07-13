import os
from core.config import TASK_PATTERN, HEADER_PATTERN, GENERIC_HEADERS

def parse_methodology(methodology_directory):
    phase_data = {}
    if not os.path.exists(methodology_directory):
        print(f"[!] Methodology directory not found at {methodology_directory}")
        return phase_data

    for phase_folder in sorted(os.listdir(methodology_directory)):
        phase_path = os.path.join(methodology_directory, phase_folder)
        if not os.path.isdir(phase_path) or phase_folder == "temp":
            continue

        phase_data[phase_folder] = {}

        for file in sorted(os.listdir(phase_path)):
            if not file.endswith('.md'):
                continue

            phase_data[phase_folder][file] = {}
            filepath = os.path.join(phase_path, file)
            current_category = "General"

            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue

                    header_match = HEADER_PATTERN.match(clean_line)
                    if header_match:
                        current_category = header_match.group(1).strip()
                        # Generic/administrative headers collapse to "General".
                        # Empty by default in this framework (see config).
                        if current_category in GENERIC_HEADERS:
                            current_category = "General"
                        continue

                    task_match = TASK_PATTERN.match(clean_line)
                    if task_match:
                        task = task_match.group(1).strip()
                        if current_category not in phase_data[phase_folder][file]:
                            phase_data[phase_folder][file][current_category] = []
                        if task not in phase_data[phase_folder][file][current_category]:
                            phase_data[phase_folder][file][current_category].append(task)

            if not phase_data[phase_folder][file]:
                del phase_data[phase_folder][file]

    return phase_data
