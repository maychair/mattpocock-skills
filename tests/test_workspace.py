"""Exercise the workflow CLI against isolated registry/Git/storage fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "scripts/workspace.py"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-workspace-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "PersonalRoot"
        self.project = self.root / "Projects/Personal/app"
        self.project.mkdir(parents=True)
        (self.root / "Config").mkdir()
        (self.root / "Scripts").mkdir()
        (self.root / "Local").mkdir()
        (self.root / "repos.toml").write_text('schema_version = 4\nworkspace_id = "fixture"\n')
        (self.root / "Config/layout.md").write_text('# Layout\n')
        # Only the fixture CLI reads this inventory; the adapter must call the CLI.
        self.inventory = self.root / "Local/fixture.json"
        self.rows = [{"id": "app", "kind": "registration", "status": "available",
                      "vcs": "git", "resolved_path": str(self.project)}]
        self.save_rows()
        (self.root / "Scripts/projects.py").write_text('''import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'Local/fixture.json').read_text())
selector=sys.argv[-1] if sys.argv[-1] != '--json' else None
if selector:
 rows=[r for r in rows if r['id']==selector]
 if not rows: raise SystemExit(2)
print(json.dumps(dict(query_schema_version=1,registry_schema_version=4,legacy=False,scope='local',workspace_id='fixture',projects=rows)))
''')
        self.git(self.project, "init", "--quiet")
        (self.project / "AGENTS.md").write_text('# Project instructions\n')
        (self.project / "CONTEXT.md").write_text('# Terms\n')
        self.git(self.project, "add", "AGENTS.md", "CONTEXT.md")
        self.git(self.project, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "Fixture")
        self.config = self.root / "Local/mattskills/app.md"

    def save_rows(self):
        self.inventory.write_text(json.dumps(self.rows))

    def git(self, cwd, *args):
        subprocess.run(["git", "-C", str(cwd), *args], check=True, text=True, capture_output=True)

    def cli(self, command="locate", *args, cwd=None, ok=True):
        result = subprocess.run([sys.executable, str(HELPER), command, *args], cwd=cwd or self.project,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def test_nested_project_selects_primary_and_does_not_create_storage(self):
        nested = self.project / "src/nested"
        nested.mkdir(parents=True)
        result = self.cli(cwd=nested)
        self.assertEqual(result["project_id"], "app")
        self.assertEqual(result["source_root"], str(self.project))
        self.assertFalse(self.config.exists())
        self.assertFalse((self.root / "Tasks").exists())

    def test_root_requires_selection_and_rejects_unregistered_identity(self):
        self.cli(cwd=self.root, ok=False)
        self.cli("locate", "--project", "missing", cwd=self.root, ok=False)
        result = self.cli("locate", "--project", "app", cwd=self.root)
        self.assertEqual(result["source_root"], str(self.project))

    def test_setup_creates_only_local_config_and_preserves_project_files(self):
        before = {f.name: f.read_bytes() for f in self.project.glob("*.md")}
        result = self.cli("setup")
        self.assertEqual(result["action"], "created-local-config")
        text = self.config.read_text()
        self.assertIn("## Issue tracker: Local Markdown", text)
        self.assertIn("CONTEXT.md", text)
        self.assertFalse((self.root / "Tasks").exists())
        self.assertFalse((self.project / ".scratch").exists())
        self.assertFalse((self.project / "docs/agents").exists())
        self.assertEqual(before, {f.name: f.read_bytes() for f in self.project.glob("*.md")})
        self.assertEqual(self.cli("setup")["action"], "preserved-existing")
        self.assertEqual(self.config.read_text(), text)

    def test_existing_remote_config_is_byte_preserved_and_local_path_refused(self):
        self.config.parent.mkdir()
        original = b'# Custom\n\n## Issue tracker: GitLab\nDomain docs: docs/terms.md\n'
        self.config.write_bytes(original)
        self.assertEqual(self.cli("setup")["action"], "preserved-existing")
        self.assertEqual(self.config.read_bytes(), original)
        self.cli("path", "--kind", "ticket", "--topic", "feature", ok=False)

    def test_ticket_path_is_lazy_and_confined_to_selected_effort(self):
        self.cli("setup")
        result = self.cli("path", "--kind", "ticket", "--topic", "feature", "--name", "01-first.md")
        expected = self.root / "Tasks/app/feature/issues/01-first.md"
        self.assertEqual(result["output_path"], str(expected))
        self.assertFalse(expected.parent.exists())
        expected.parent.mkdir(parents=True)
        expected.write_text('# 01: First\n**Blocked by:** None\n**Status:** ready-for-agent\n')
        self.assertEqual(self.cli("path", "--kind", "ticket", "--topic", "feature", "--name", "01-first.md")["output_path"], str(expected))
        self.assertFalse((self.project / ".scratch").exists())

    def test_ticket_requires_setup_and_matching_declared_root(self):
        self.cli("path", "--kind", "ticket", "--topic", "feature", ok=False)
        self.cli("setup")
        self.config.write_text(self.config.read_text().replace('Tasks/app', 'Tasks/other'))
        self.cli("path", "--kind", "ticket", "--topic", "feature", ok=False)

    def test_worktree_reuses_primary_config_and_storage(self):
        worktree = self.base / "random-worktree-name"
        self.git(self.project, "worktree", "add", "--quiet", "--detach", str(worktree))
        result = self.cli("setup", "--workspace", str(self.root), cwd=worktree)
        self.assertEqual(result["source_root"], str(worktree))
        self.assertEqual(result["paths"]["config"], str(self.config))
        self.assertFalse((self.root / "Local/mattskills/random-worktree-name.md").exists())
        result = self.cli("locate", "--project", "app", "--checkout", str(worktree), cwd=self.root)
        self.assertEqual(result["source_root"], str(worktree))

    def test_unrelated_checkout_is_rejected(self):
        other = self.base / "other"
        other.mkdir()
        self.git(other, "init", "--quiet")
        self.cli("locate", "--project", "app", "--checkout", str(other), cwd=self.root, ok=False)
        self.cli("locate", "--workspace", str(self.root), cwd=other, ok=False)

    def test_no_ordinary_repository_fallback(self):
        outside = self.base / "ordinary"
        outside.mkdir()
        self.cli(cwd=outside, ok=False)
        self.assertFalse((outside / ".scratch").exists())

    def test_incomplete_or_invalid_workspace_markers_stop(self):
        (self.root / "Config/layout.md").unlink()
        self.cli(ok=False)
        (self.root / "Config/layout.md").write_text('# Layout')
        (self.root / "repos.toml").write_text('schema_version = 3\nworkspace_id = "fixture"\n')
        self.cli(ok=False)

    def test_symlinked_config_and_ticket_roots_are_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "Local/mattskills").symlink_to(outside, target_is_directory=True)
        self.cli("setup", ok=False)
        self.assertEqual(list(outside.iterdir()), [])
        (self.root / "Local/mattskills").unlink()
        self.cli("setup")
        (self.root / "Tasks").symlink_to(outside, target_is_directory=True)
        self.cli("path", "--kind", "ticket", "--topic", "feature", ok=False)

    def test_escaping_components_and_invalid_ticket_names_are_rejected(self):
        self.cli("setup")
        for topic in ("../other", "/tmp", "a/b", "..", "a\\b"):
            self.cli("path", "--kind", "ticket", "--topic", topic, ok=False)
        self.cli("path", "--kind", "ticket", "--topic", "feature", "--name", "notes.txt", ok=False)

    def test_output_categories_are_retained_outside_project(self):
        for kind, expected in (("html", 'Local/Documents/workflow/app'),
                               ("scratch", 'Temporary/Scratch/workflow/app'),
                               ("teaching", 'Local/Documents/Teaching/app'),
                               ("build", 'Local/Builds/app/workflow')):
            result = self.cli("path", "--kind", kind, "--topic", "topic")
            target = Path(result["output_path"])
            self.assertTrue(target.is_relative_to(self.root / expected))
            self.assertFalse(target.exists())
            self.assertFalse(target.is_relative_to(self.project))

    def test_repository_name_collision_cannot_share_configuration(self):
        second = self.root / "Projects/Company/app"
        second.mkdir(parents=True)
        self.rows.append({"id": "second", "kind": "registration", "status": "available", "vcs": "none", "resolved_path": str(second)})
        self.save_rows()
        self.cli(ok=False)

    def test_non_git_registered_project_is_supported(self):
        plain = self.root / "Projects/plain"
        plain.mkdir()
        self.rows.append({"id": "plain", "kind": "registration", "status": "available", "vcs": "none", "resolved_path": str(plain)})
        self.save_rows()
        result = self.cli("setup", cwd=plain)
        self.assertEqual(result["source_root"], str(plain))

    def test_bad_query_contract_is_rejected(self):
        script = self.root / "Scripts/projects.py"
        script.write_text(script.read_text().replace('query_schema_version=1', 'query_schema_version=9'))
        self.cli(ok=False)

    def test_query_from_another_workspace_is_rejected(self):
        script = self.root / "Scripts/projects.py"
        script.write_text(script.read_text().replace("workspace_id='fixture'", "workspace_id='other'"))
        self.cli(ok=False)

    def test_unavailable_project_is_not_initialized(self):
        self.rows[0]["status"] = "missing"
        self.save_rows()
        self.cli("setup", "--project", "app", cwd=self.root, ok=False)
        self.assertFalse(self.config.exists())

    def test_two_html_outputs_do_not_reuse_a_filename(self):
        first = self.cli("path", "--kind", "html", "--topic", "review")
        second = self.cli("path", "--kind", "html", "--topic", "review")
        self.assertNotEqual(first["output_path"], second["output_path"])


if __name__ == "__main__":
    unittest.main()
