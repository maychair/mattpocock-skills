---
name: handoff
description: "Workspace projects: Compact the current conversation into a handoff document for another agent to pick up."
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

## Workspace prerequisite

Read [Workspace contract](../../../WORKSPACE.md) and run its project resolver before using this skill. Use the selected checkout, central entry and output paths. This skill requires a registered Workspace project.

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Resolve its destination with `workspace.py path --kind scratch --topic handoff`; report and carry the actual path into the next session.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
