"""cli — the repo's shared dictionary-routed CLI engine (drop-in).

Update the CLI framework-wide by replacing this one `cli/` directory; every tool
imports from here. Tools reach it via a tiny path bootstrap (see any tool's
main.py), then declare a ``{hotkey: command-dict}`` menu and call ``run_menu``.
"""

from .engine import (
    run_menu,
    clear_screen,
    confirm,
    prompt,
    numbered_select,
    GLOBAL_UTILITIES,
)

__all__ = [
    "run_menu",
    "clear_screen",
    "confirm",
    "prompt",
    "numbered_select",
    "GLOBAL_UTILITIES",
]
