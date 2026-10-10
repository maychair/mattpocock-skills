# Issue tracker: Local Markdown

Tickets and specs live as Markdown files under the absolute `paths.ticket_root` returned by the Workspace helper. The central entry declares `Local root: Tasks/<registered-repository-name>` relative to the Workspace root. Worktrees use their registered primary repository's entry.

## Conventions

- One feature per directory: `<ticket_root>/<feature-slug>/`
- The spec is `<ticket_root>/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `<ticket_root>/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Resolve a path with `workspace.py path --kind ticket --topic <feature-slug> --name spec.md`, `map.md` or `NN-<slug>.md`. Create only the needed directory and file for the requested work. Preserve existing files; do not inspect other efforts or create demonstration tickets.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `<ticket_root>/<effort>/map.md` (the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `<ticket_root>/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `<ticket_root>/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
