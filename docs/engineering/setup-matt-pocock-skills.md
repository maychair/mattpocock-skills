## What it does

Initializes one registered Workspace project's tracker, triage labels and domain layout in a single central Markdown entry. New projects default to local tickets; an existing entry is preserved unchanged. Setup creates no project files or sample tasks.

## When to reach for it

Select `setup-matt-pocock-skills` explicitly in Codex when a registered project needs its first configuration, or when you explicitly want to change its central settings. The agent does not start setup on its own.

## Prerequisites

Requires a marked v4 Workspace and an available registered project. Project and worktree sessions can resolve their owner; a root session selects a project ID. See the [Workspace contract](https://github.com/maychair/mattpocock-skills/blob/main/WORKSPACE.md).

## Where it fits

Run before the engineering skills need a tracker. The [ask-matt router](https://github.com/maychair/mattpocock-skills/blob/main/skills/engineering/ask-matt/SKILL.md) helps select the later flow.

## Common questions

### Does setup modify the project repository?

No. It writes only Local/mattskills under the Workspace root. The selected project's agent instructions, source, glossary and ADRs are unchanged.

### Does an existing GitLab or GitHub tracker become local?

No. Existing configuration is preserved byte for byte. An explicit tracker change edits only the requested central sections.

### Where are local tickets?

Tasks/<registered-repository-name>/<effort>, outside the project checkout. Each effort contains a spec, map and separate numbered ticket files as needed. A worktree reuses the primary repository's entry.

### Does initialization read old tickets or create examples?

No. A project with a central entry and zero tickets is initialized. Actual task files are created lazily when requested.

## It's working if

- The returned central entry exists and declares the selected tracker and domain layout.
- A fresh entry uses Local Markdown and the canonical five triage roles.
- Existing entries and project files are unchanged.
- Worktrees resolve the same configuration and ticket root as their primary repository.
