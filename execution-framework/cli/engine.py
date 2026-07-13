"""cli_engine — shared dictionary-routed CLI engine (vendored, single-file).

The ecosystem's "Define Then Assemble" contract in one importable module. A menu
is ``{hotkey: command-dict}``; a command-dict is
``{"desc", "action", optional "args", "catch_error", "exit_after"}``. One loop
renders + dispatches every menu; global utilities (clear/quit/back) and the
confirm / prompt / numbered-select helpers are shared primitives so each tool
declares only its menu table + handler functions.

Vendored per tool (copied next to each tool's main.py) so every tool stays
runnable from its own directory with no cross-package imports — matching how
these standalone tools already work.
"""

import os

# --- terminal + prompt helpers ---------------------------------------------


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def prompt(message, default=None):
    """EOF/Ctrl-C-safe ``input``. Returns ``default`` if the user aborts."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        return default


def confirm(message, default=False):
    """Yes/no prompt returning a bool. EOF/Ctrl-C -> ``default``."""
    ans = prompt(message + (" [Y/n] " if default else " [y/N] "))
    if ans is None or ans == "":
        return default
    return ans.lower() in ("y", "yes")


def numbered_select(options, title="Select", prompt_text="Choose a number: ",
                    labeler=str):
    """Show an enumerated list and return the chosen item (``None`` on cancel).

    ``options`` is a list; ``labeler`` maps an item to its display string.
    Replaces the hand-rolled "enumerate -> read number -> validate range" block.
    """
    if not options:
        return None
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"   [{i}] {labeler(opt)}")
    raw = prompt(prompt_text)
    if raw and raw.isdigit() and 1 <= int(raw) <= len(options):
        return options[int(raw) - 1]
    return None


# --- the dictionary-routed menu loop ---------------------------------------

GLOBAL_UTILITIES = {
    "c": {"desc": "Clear screen", "action": clear_screen},
    "q": {"desc": "Quit", "action": "QUIT_FLAG"},
    "back": {"desc": "Go back", "action": "BACK_FLAG"},
}


def _default_render(title, menu):
    bar = "=" * 60
    print(f"\n{bar}\n {title}\n{bar}")
    for key, cmd in menu.items():
        print(f"   [{key}] {cmd['desc']}")
    print("-" * 60)
    print("   [c] Clear screen          [q] Quit")
    print(bar)


def run_menu(menu, title="Menu", render=None, prompt_text="Select an option: "):
    """Render ``menu`` (via injected ``render`` if given, else a flat default),
    read a hotkey, and run the matching command dict's ``action`` with its
    ``args``. Global utilities (clear/quit/back) are always available. A command
    may set ``catch_error`` (swallow + print) or ``exit_after`` (return after
    running). Returns 0 on quit/back/EOF — call it from a tool's ``main()``.
    """
    while True:
        (render or _default_render)(title, menu)
        try:
            choice = input(prompt_text).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        cmd = menu.get(choice) or GLOBAL_UTILITIES.get(choice)
        if cmd is None:
            print("[!] Invalid selection.")
            continue
        action = cmd["action"]
        if action in ("QUIT_FLAG", "BACK_FLAG"):
            return 0
        try:
            action(*cmd.get("args", ()))
        except Exception as exc:  # noqa: BLE001
            if cmd.get("catch_error", False):
                print(f"[!] {exc}")
            else:
                raise
        if cmd.get("exit_after", False):
            return 0
