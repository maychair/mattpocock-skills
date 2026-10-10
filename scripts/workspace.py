#!/usr/bin/env python3
"""Resolve registered Workspace projects and their workflow storage (Python 3.11+)."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from uuid import uuid4


class WorkspaceError(Exception):
    pass


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise WorkspaceError("Required project or Git query failed; repair the registration or checkout.")
    return result.stdout.strip()


def marker(root):
    file = root / "repos.toml"
    if not file.exists() or not (root / "Config/layout.md").is_file() or not (root / "Scripts/projects.py").is_file():
        return False
    try:
        data = tomllib.loads(file.read_text())
    except (OSError, ValueError) as exc:
        raise WorkspaceError("Workspace identity is unreadable or malformed.") from exc
    if set(data) != {"schema_version", "workspace_id"} or data["schema_version"] != 4 or not isinstance(data["workspace_id"], str) or not data["workspace_id"].strip():
        raise WorkspaceError("A complete v4 Workspace mechanism identity is required.")
    return True


def workspace_root(cwd, explicit=None):
    if explicit:
        root = Path(explicit).expanduser().resolve(strict=True)
        if marker(root):
            return root
        raise WorkspaceError("The selected directory is not a marked Workspace.")
    for root in (cwd, *cwd.parents):
        if marker(root):
            return root
    raise WorkspaceError("No marked Workspace found. For an external worktree, pass --workspace explicitly.")


def query(root, selector=None, available=True):
    command = [sys.executable, str(root / "Scripts/projects.py"), "--workspace", str(root), "--all", "--json"]
    if selector:
        command.append(selector)
    try:
        data = json.loads(run(command, root))
    except ValueError as exc:
        raise WorkspaceError("Project query did not return valid JSON.") from exc
    if data.get("query_schema_version") != 1 or data.get("registry_schema_version") != 4 or data.get("legacy") is not False or data.get("scope") != "local" or not isinstance(data.get("projects"), list):
        raise WorkspaceError("Unsupported project query contract.")
    identity = tomllib.loads((root / "repos.toml").read_text())["workspace_id"]
    if data.get("workspace_id") != identity:
        raise WorkspaceError("Project query belongs to another Workspace identity.")
    return [row for row in data["projects"] if row.get("kind") == "registration" and (not available or row.get("status") == "available")]


def git(root, *args):
    return run(["git", "-C", str(root), *args], root)


def git_root(cwd):
    try:
        return Path(git(cwd, "rev-parse", "--show-toplevel")).resolve(strict=True)
    except WorkspaceError:
        return None


def registered_checkout(primary, checkout):
    if checkout == primary:
        return
    common = lambda p: Path(git(p, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve(strict=True)
    if git_root(checkout) != checkout or common(primary) != common(checkout):
        raise WorkspaceError("Checkout does not belong to the selected registered Git repository.")
    worktrees = [Path(line[9:]).resolve() for line in git(primary, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")]
    if checkout not in worktrees:
        raise WorkspaceError("Checkout is not a registered worktree.")


def component(value):
    if not value or value in {".", ".."} or any(c in value for c in "/\\\0\n\r") or any(ord(c) < 32 for c in value):
        raise WorkspaceError("A single safe path component is required.")
    return value


def guarded(root, *parts):
    target = root.joinpath(*parts)
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise WorkspaceError("Workflow storage must not contain symbolic links.")
    if not target.resolve().is_relative_to(root):
        raise WorkspaceError("Workflow storage escapes the Workspace.")
    return target


def locate(args):
    cwd = Path(args.cwd or os.getcwd()).expanduser().resolve(strict=True)
    root = workspace_root(cwd, args.workspace)
    rows = query(root, args.project)
    actual_git = git_root(cwd)
    if args.project:
        if len(rows) != 1:
            raise WorkspaceError("Select exactly one available registered project.")
        row = rows[0]
    else:
        candidates = []
        for item in rows:
            primary = Path(item["resolved_path"]).resolve(strict=True)
            if cwd.is_relative_to(primary):
                candidates.append(item)
            elif actual_git and item.get("vcs") == "git":
                try:
                    registered_checkout(primary, actual_git)
                    candidates.append(item)
                except WorkspaceError:
                    pass
        if len(candidates) != 1:
            raise WorkspaceError("Project identity is missing or ambiguous; pass --project with a registered ID.")
        row = candidates[0]
    primary = Path(row["resolved_path"]).resolve(strict=True)
    if args.checkout:
        checkout = Path(args.checkout).expanduser().resolve(strict=True)
    elif row.get("vcs") == "git" and actual_git and cwd.is_relative_to(actual_git):
        checkout = actual_git if cwd.is_relative_to(primary) else primary
        if checkout == primary and actual_git != root and row.get("vcs") == "git":
            try:
                registered_checkout(primary, actual_git)
                checkout = actual_git
            except WorkspaceError:
                if not args.project:
                    raise
    else:
        checkout = primary
    if row.get("vcs") == "git":
        registered_checkout(primary, checkout)
    elif checkout != primary:
        raise WorkspaceError("Alternate checkouts require a registered Git project.")
    name = component(primary.name)
    project = component(row["id"])
    # Basenames preserve the existing central format; duplicates cannot share state.
    same_names = [r for r in query(root, available=False) if Path(r["resolved_path"]).name == name]
    if len(same_names) != 1:
        raise WorkspaceError("Repository basenames collide in the central configuration namespace.")
    config = guarded(root, "Local", "mattskills", name + ".md")
    paths = {
        "config": str(config),
        "ticket_root": str(guarded(root, "Tasks", name)),
        "html_root": str(guarded(root, "Local", "Documents", "workflow", project)),
        "scratch_root": str(guarded(root, "Temporary", "Scratch", "workflow", project)),
        "teaching_root": str(guarded(root, "Local", "Documents", "Teaching", project)),
        "build_root": str(guarded(root, "Local", "Builds", project, "workflow")),
    }
    return {"schema_version": 1, "workspace_root": str(root), "project_id": project,
            "repository_name": name, "primary_root": str(primary), "source_root": str(checkout),
            "entry_points": [str(checkout / f) for f in ("AGENTS.md", "CLAUDE.md") if (checkout / f).is_file()],
            "config_exists": config.is_file(), "paths": paths}


def initialize(context):
    file = Path(context["paths"]["config"])
    if file.exists():
        if not file.is_file():
            raise WorkspaceError("Central entry is not a regular file.")
        return {**context, "action": "preserved-existing"}
    source = Path(context["source_root"])
    glossary = next((n for n in ("GLOSSARY-MAP.md", "GLOSSARY.md", "CONTEXT.md") if (source / n).is_file()), "GLOSSARY.md")
    name = context["repository_name"]
    text = f"""# {name} mattskills configuration

## Issue tracker: Local Markdown

Local root: Tasks/{name}

One effort per directory. Specs and maps are spec.md and map.md; tickets are issues/NN-<slug>.md.
Read only the effort or ticket selected for the current task. Create files lazily for actual work.

## Triage labels

| Role | Label |
| --- | --- |
| needs-triage | needs-triage |
| needs-info | needs-info |
| ready-for-agent | ready-for-agent |
| ready-for-human | ready-for-human |
| wontfix | wontfix |

## Domain docs

Read the owning project's instructions first. Existing glossary: {glossary}. ADR directory: docs/adr/.
These paths are project-relative defaults; project instructions take priority. Initialization creates no domain documents.
"""
    file.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves another session's simultaneous setup.
    try:
        with file.open("x", encoding="utf-8") as stream:
            stream.write(text)
    except FileExistsError:
        return {**context, "action": "preserved-existing"}
    return {**context, "config_exists": True, "action": "created-local-config"}


def artifact_path(context, args):
    topic = component(args.topic)
    root = Path(context["workspace_root"])
    if args.kind == "ticket":
        if not context["config_exists"]:
            raise WorkspaceError("Run setup before requesting a local ticket path.")
        config = Path(context["paths"]["config"]).read_text()
        if not re.search(r"^## Issue tracker: Local Markdown\s*$", config, re.M):
            raise WorkspaceError("This project already uses another tracker; follow its central entry.")
        expected = f"Local root: Tasks/{context['repository_name']}"
        roots = re.findall(r"^Local root: (.+)$", config, re.M)
        if roots != [expected.removeprefix("Local root: ")]:
            raise WorkspaceError("Central local root does not match the selected project.")
        name = component(args.name or "spec.md")
        relative = Path(context["paths"]["ticket_root"]).relative_to(root) / topic
        if name not in {"spec.md", "map.md"}:
            if not re.fullmatch(r"[0-9]{2,}-[A-Za-z0-9][A-Za-z0-9._-]*\.md", name):
                raise WorkspaceError("Ticket names must be NN-slug.md, spec.md or map.md.")
            relative /= "issues"
        target = guarded(root, *relative.parts, name)
    else:
        base = Path(context["paths"][args.kind + "_root"]).relative_to(root)
        if args.kind == "teaching" or (args.kind == "build" and not args.name):
            target = guarded(root, *base.parts, topic)
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            suffix = "html" if args.kind == "html" else "md"
            name = component(args.name or f"{stamp}-{args.kind}-{topic}-{uuid4().hex[:8]}.{suffix}")
            if args.kind == "html" and not name.endswith(".html"):
                raise WorkspaceError("HTML outputs require a .html filename.")
            target = guarded(root, *base.parts, topic, name)
    return {**context, "output_path": str(target), "creates_files": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("locate", "setup", "path"))
    parser.add_argument("--workspace")
    parser.add_argument("--cwd")
    parser.add_argument("--project")
    parser.add_argument("--checkout")
    parser.add_argument("--kind", choices=("ticket", "html", "scratch", "teaching", "build"))
    parser.add_argument("--topic")
    parser.add_argument("--name")
    args = parser.parse_args()
    try:
        context = locate(args)
        if args.command == "setup":
            context = initialize(context)
        elif args.command == "path":
            if not args.kind or not args.topic:
                parser.error("path requires --kind and --topic")
            context = artifact_path(context, args)
        print(json.dumps(context, ensure_ascii=False, indent=2))
    except (WorkspaceError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
