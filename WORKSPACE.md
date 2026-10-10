# Workspace workflow contract

This fork runs only against registered Workspace projects. It contains an independently written adapter and retains Matt Pocock's engineering flows. Python 3.11+ and Git are required. Install the whole Codex plugin so the shared resources travel with its skills; copying one skill folder alone is unsupported.

## Resolve the task before acting

Run `python3 <plugin-root>/scripts/workspace.py locate` from the actual task cwd. Resolve `<plugin-root>` from this skill's resource path, not from the task cwd. A skill lives at `skills/<bucket>/<name>/SKILL.md`, so this file and the helper are three levels above its directory.

At the Workspace root, add `--project <registered-id>`. In a project or subdirectory, the helper selects its registered identity. An external worktree needs `--workspace <root>`; `--checkout <worktree-root>` can explicitly select a verified checkout. The Workspace root is identified by its v4 mechanism registry, layout entry and project CLI, never by a directory name. The helper calls `Scripts/projects.py`, validates its query contract, and verifies Git worktree membership. It never parses the private project registry or scans unregistered project directories.

Read the selected project's applicable AGENTS/CLAUDE instructions and its returned central configuration before project work. Missing, ambiguous or invalid identities stop the operation. There is no ordinary-repository fallback. Registered primary identity chooses configuration and storage; a worktree's temporary basename does not choose another configuration. Consult Graphify and Workspace LSP when code navigation benefits from them and they are available; follow the owning project's edit and validation policy. This adapter adds no worktree or branch policy.

## Configuration and trackers

`setup-matt-pocock-skills` uses `workspace.py setup`. A new project defaults to Local Markdown. Existing central entries are preserved byte for byte, including remote tracker choices and custom domain paths. Setup writes only `paths.config`; it creates no sample tickets, project agent-entry block or domain skeleton. For an explicit configuration change, read the entry, present the requested change and edit only that entry.

The central entry records tracker, triage labels and project-relative domain paths together. Do not create `docs/agents` tracker configuration or append an `Agent skills` block to a project. Actual glossaries and ADRs belong to the project and are edited only within the requested task scope.

For local work, an effort owns `spec.md`, `map.md` and `issues/NN-<slug>.md` under `paths.ticket_root/<effort>`. Resolve a ticket output with `workspace.py path --kind ticket --topic <effort> --name <filename>`. It checks the central tracker and root; a remote entry cannot silently become local. Read only the named effort or ticket. Do not scan, recover or migrate Tasks history as initialization. Retain the original spec/ticket formats, numbering, blocking edges, claim and resolve semantics. Use `gh`, `glab`, an available connector or the explicitly configured tracker workflow for remote entries; this plugin introduces no host-specific tracker tools.

## Outputs

Use `workspace.py path --kind <kind> --topic <slug>` with the same project selection. It returns an absolute `output_path` without creating directories or files. Create the needed parent only when delivering the requested artifact; preserve existing output files. Optional `--name` must be a single safe filename.

| Content | Kind or returned root |
| --- | --- |
| Local specs, maps and tickets | `ticket`, under `Tasks/<registered-repository-name>` |
| User-facing standalone HTML | `html`, under `Local/Documents/workflow/<project-id>` |
| Research, questionnaire, plan draft and handoff | `scratch`, under `Temporary/Scratch/workflow/<project-id>` |
| Persistent teaching state and its lessons/assets | `teaching`, under `Local/Documents/Teaching/<project-id>/<topic>` |
| Build output and reproducible caches | `build`, under `Local/Builds/<project-id>/workflow` |
| Source, prototypes, glossary and ADRs | The selected checkout and its owning instructions |

Generated filenames default to a UTC timestamp, content kind, topic and random suffix. HTML is retained in Local/Documents; drafts and handoffs in Temporary are subject to cleanup. Report the actual written path and carry it into continuation prompts. Skill resource directories are references, never output destinations. Private traces and project identities remain in ignored Workspace storage, outside this fork's Git history.

The helper rejects symlinked workflow storage and escaping path components. It resolves paths and writes initial configuration, not a filesystem sandbox for all agent file tools; agent edits must follow these returned destinations.

## Codex invocation

Preserve each skill's existing user/model invocation policy. Mention user-invoked workflows explicitly with `$` or the skill picker; auxiliary skills may be selected when their task fits. A request for advice does not start an implementation workflow. If Codex has no generic Skill tool, read the corresponding SKILL.md from this installed plugin and follow it; do not call a nonexistent tool or select an unrelated provider's same-named skill. Other user-invoked workflows still require the user's request. The contract changes environment paths, not task authorization or communication preferences.
