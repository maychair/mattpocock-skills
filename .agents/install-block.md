# Canonical Workspace install block

This fork supports registered Workspace projects through the whole Codex plugin. Keep README installation commands identical to this block. Standalone copies of skill folders are unsupported because shared Workspace resources belong to the plugin root.

```sh
codex plugin marketplace add maychair/mattpocock-skills
codex plugin add workspace-mattpocock-skills@maychair-workspace
```

For a feature branch, add `--ref <branch>` to marketplace add. For local development, add the checkout path instead of the GitHub shorthand. Version changes must be synchronized across package.json and both plugin manifests; run `npm run check-plugin-version` and `npm run check:workspace` before installing. Local source installs need reinstalling after edits. Existing chats may retain old skills; verify the native catalog in a new chat.

Use one installed provider for these workflows to avoid duplicate skill names. This fork preserves the original author credit and MIT license.
