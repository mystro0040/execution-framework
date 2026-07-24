# Test expectations (auto-generated — do not edit by hand)

Regenerate with `workspace.py test --write-expectations`. This lists the suites whose tests live in THIS directory, what each covers, how to run it, and the expected result.

> **Directive:** Tests are a REGRESSION FLOOR, not a substitute for exercising the real tool. When you change or upgrade a tool you MUST do BOTH: (1) drive the actual application to confirm the change works, and (2) run AND update its suite here. Green tests on unchanged code prove nothing about code you just changed. Never skip the live app because tests pass; never skip updating tests because the app works.

## exf-reporting-engine  ·  framework

- **Run:** `python3 test_reporting_engine.py` (from this directory)
- **Expected:** exit 0, all checks pass. Execution framework reporting engine (existing suite). Needs python-docx. NOT isolated — opt-in via --all.
- **Covers:** execution-framework/utilities/reporting
- **Isolation:** NOT isolated — writes into the repo; run via `--all` and revert after.
- **Needs:** docx (absent → the suite SKIPS, it does not fail).

## exf-template-generator  ·  framework

- **Run:** `python3 test_template_generator.py` (from this directory)
- **Expected:** exit 0, all checks pass. Execution framework template generator (existing suite). NOT isolated — opt-in via --all.
- **Covers:** execution-framework/utilities/template_generator
- **Isolation:** NOT isolated — writes into the repo; run via `--all` and revert after.
