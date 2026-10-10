#!/usr/bin/env node
// Synchronizes both Codex and compatibility plugin versions with package.json.
// Runs as part of `npm run version`, immediately after `changeset version`.
// With --check it changes nothing and exits 1 if the two versions differ.

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repo = join(dirname(fileURLToPath(import.meta.url)), "..");
const pluginPaths = [".claude-plugin", ".codex-plugin"].map(dir => join(repo, dir, "plugin.json"));

const { version } = JSON.parse(readFileSync(join(repo, "package.json"), "utf8"));
let failed = false;
for (const pluginPath of pluginPaths) {
  const source = readFileSync(pluginPath, "utf8");
  const plugin = JSON.parse(source);

  if (plugin.version === version) {
    console.log(`plugin.json version is ${version} (already in sync)`);
    continue;
  }

  if (process.argv.includes("--check")) {
    console.error(
      `plugin.json version is ${plugin.version}, package.json is ${version}. Run \`node scripts/sync-plugin-version.mjs\`.`,
    );
    failed = true;
    continue;
  }

  // Rewrite only the version line, to keep the key order and the formatting.
  const updated = source.replace(
    /("version"\s*:\s*")[^"]*(")/,
    `$1${version}$2`,
  );

  if (JSON.parse(updated).version !== version) {
    console.error(`Could not find a version field to replace in ${pluginPath}.`);
    process.exit(1);
  }

  writeFileSync(pluginPath, updated);
  console.log(`plugin.json version ${plugin.version} -> ${version}`);
}
if (failed) process.exit(1);
