# YAML Architecture & Gotchas

The methodology is a **YAML database**, not markdown. Read this before editing.

## Topology — `application/` (ships) vs `engagement/` (workspace)

The framework has two roots, so the shipped product stays separate from a live job:

| Root | Holds | Nature |
|------|-------|--------|
| `application/` | `config/` (domain.ini, placeholders.yaml, report.ini) + `data/methodology_yaml/` (the YAML methodology **source**) + `references/` (the shipped reference library) | Ships with the tool. Edit the methodology here. |
| `engagement/` | `methodology/` (generated md), `data/`, `execution/`, `reports/`, `templates/`, `loadout/`, `tools/` | The active workspace — your per-job data + generated outputs. |

`demo-data/` (a sample engagement), `docs/` and `utilities/` (the code) sit
beside them at the repo root. **`config.ini` `[topology]` at the root is the
single source of truth for these folder names** — every utility reads it, so
renaming `application`/`engagement` there is a config change, not a code change.

## Source vs. generated — what to edit

| Path | Role | Edit it? |
|------|------|----------|
| `application/data/methodology_yaml/*.yaml` | **Source of truth** (the database) | ✅ **Yes — edit here** |
| `engagement/methodology/*.md` | Generated docs (rendered from YAML) | ❌ No — overwritten on regenerate |
| `engagement/templates/execution/iteration/**` | Generated checklists | ❌ No — overwritten |
| `application/config/placeholders.yaml` | Canonical `<TOKEN>` vocabulary | ✅ Yes |

**Workflow:** edit `application/data/methodology_yaml/*.yaml` → Mirroring Engine
(`utilities/template_generator/main.py`) → **Option 3** → renders
`engagement/methodology/*.md` and rebuilds templates.

## Schema (header-style tasks)

```yaml
title: null                      # this framework's files often have NO H1 title
sections:
  - heading: Scope Definition
    tasks:
      - id: define-project-scope
        name: Define Project Scope   # body-less checklist item
```

Tasks are standalone `**Name**` lines. Here they're usually **body-less**
checklist items (no per-task prose).

## Gotchas

- **Body-less tasks render densely (no blank line between them).** `render_doc`
  only emits a blank line after a task that *has* a body — matching this
  framework's compact checklist style. (In the pentest framework tasks always
  have bodies, so its renderer always spaces them.)
- **No H1 titles.** Files start at `## Heading`; the importer stores
  `title: null` and the renderer omits the title line.
- **`GENERIC_HEADERS = []`** — no heading is remapped to "General" (this
  framework's parser never did). Keep it empty unless you add insight/reference
  sections you want excluded from the checklist.
- **Placeholder vocab is empty** (`fields: {}`) — this domain-agnostic
  methodology ships with no command tokens. Add fields to
  `application/config/placeholders.yaml` and `<TOKEN>`s to task bodies to make
  `loadout_manager` useful here.
- **Loadout files live in `engagement/loadout/`, never `engagement/data/`.** The
  reporting engine's asset validator rglobs the workspace `data/**/*.md`; a stray
  non-asset markdown there halts validation. (The validator is scoped to the
  active `engagement/` workspace — it never rglobs the whole repo.) Generated
  artifacts (`engagement/loadout_playbook/`, loadout `settings.json`,
  `engagement/loadout/command_buffer.md`) are gitignored.
