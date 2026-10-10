#!/usr/bin/env python3
"""Check the shipped skill set, resource links and invocation policies."""
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
errors = []
codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
legacy = json.loads((root / ".claude-plugin/plugin.json").read_text())
package = json.loads((root / "package.json").read_text())
if codex != legacy or codex["version"] != package["version"]:
    errors.append("Codex/compatibility/package manifests disagree")
promoted = {str(p.parent.relative_to(root)) for bucket in ("engineering", "productivity") for p in (root / "skills" / bucket).glob("*/SKILL.md")}
shipped = {p.removeprefix("./") for p in codex["skills"]}
if promoted != shipped or len(codex["skills"]) != len(shipped):
    errors.append("Manifest does not ship exactly the promoted skill set")
for directory in sorted(shipped):
    folder = root / directory
    skill = (folder / "SKILL.md").read_text()
    metadata = (folder / "agents/openai.yaml").read_text()
    explicit = bool(re.search(r"^disable-model-invocation: true$", skill, re.M))
    if explicit != ("allow_implicit_invocation: false" in metadata):
        errors.append(f"Invocation policy mismatch: {directory}")
    if "../../../WORKSPACE.md" not in skill:
        errors.append(f"Missing Workspace entry: {directory}")
    prose = re.sub(r"```.*?```", "", skill, flags=re.S)
    prose = re.sub(r"`[^`]*`", "", prose)
    for target in re.findall(r"\]\(([^)]+)\)", prose):
        if "://" in target or target.startswith("#") or "<" in target or target == "link":
            continue
        file = target.split("#", 1)[0]
        if file and not (folder / file).resolve().exists():
            errors.append(f"Missing resource: {directory}: {file}")
    doc = root / "docs" / folder.parent.name / (folder.name + ".md")
    if not doc.is_file() or "Workspace contract" not in doc.read_text():
        errors.append(f"Missing Workspace documentation: {directory}")
market = json.loads((root / ".agents/plugins/marketplace.json").read_text())
if market["name"] != "maychair-workspace" or market["plugins"][0]["name"] != codex["name"]:
    errors.append("Marketplace identity disagrees with plugin")
for error in errors:
    print(error, file=sys.stderr)
if errors:
    raise SystemExit(1)
print(f"Validated {len(shipped)} promoted skills, resources, policies and manifests.")
