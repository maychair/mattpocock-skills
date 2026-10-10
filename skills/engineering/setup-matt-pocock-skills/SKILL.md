---
name: setup-matt-pocock-skills
description: "Initialize a registered Workspace project's central tracker, triage mapping and domain layout; new projects default to local tickets."
disable-model-invocation: true
---

# Setup Matt Pocock's Workspace skills

Read [Workspace contract](../../../WORKSPACE.md). Run `python3 <plugin-root>/scripts/workspace.py locate` from the task cwd; at the Workspace root add `--project <registered-id>`. A project or verified worktree can initialize its central entry directly. Stop if identity is missing, unavailable or ambiguous.

Read the selected project's applicable instructions. If `config_exists` is true, read `paths.config` and report its existing tracker, labels and domain layout. Keep it unchanged unless the user explicitly requests a configuration change. The Git remote is a source-code location, not a tracker selection.

For an unconfigured project, run the same helper selection with the `setup` command. It exclusively creates one central Markdown entry with Local Markdown as the tracker, the canonical five triage labels and existing glossary discovery. The user's default is already local; do not ask them to select a backend again. Project instructions and existing domain paths take priority over recorded defaults.

Read back the entry and report its actual location and tracker. Setup writes no project AGENTS/CLAUDE block, docs/agents files, glossary, ADR, map or sample ticket. Existing entries are never regenerated. It neither reads nor migrates Tasks history. A configured project with zero tickets is initialized.

## Explicit changes

If the user asks to switch a tracker, labels or domain layout, inspect the central entry and the requested change. Present the changed sections, resolve any missing decision, then edit only `paths.config`, preserving other content. A layout change records paths; it does not authorize creating or moving project documentation. Never switch an existing remote tracker as a side effect of setup.

Use these references as section guidance inside the single entry, not separate output files:

- [issue-tracker-local.md](issue-tracker-local.md): local spec, map and ticket operations.
- [issue-tracker-github.md](issue-tracker-github.md): explicit GitHub tracker choice.
- [issue-tracker-gitlab.md](issue-tracker-gitlab.md): explicit GitLab tracker choice.
- [triage-labels.md](triage-labels.md): canonical role vocabulary.
- [domain.md](domain.md): project-owned glossary and ADR layout.
