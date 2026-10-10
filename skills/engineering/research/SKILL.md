---
name: research
description: "Workspace projects: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in Workspace scratch storage. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent."
---

## Workspace prerequisite

Read [Workspace contract](../../../WORKSPACE.md) and run its project resolver before using this skill. Use the selected checkout, central entry and output paths. This skill requires a registered Workspace project.

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it to the returned scratch destination from `workspace.py path --kind scratch --topic <topic>`. Report that actual path; do not save a session report in project source.
