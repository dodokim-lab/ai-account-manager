# Roadmap

This doc collects the work deferred for acm and the reasons. The choices were made after comparing acm with other multi-account tools. It is split into gaps to close, work not planned for now, and assumptions not yet verified.

## The next steps go in this order

1. Verify the items in "Some assumptions are still unverified" below. If an assumption in the current code is wrong, fix it before anything else.
2. Add Antigravity for usage display only, without splitting accounts.
3. Collect Codex Sites publishing in the primary account too.
4. Do Linux and Claude Desktop when someone needs them or Claude Code's support changes.

## Some gaps still need closing

### acm should run on Linux too

acm no longer reads the keychain. `.credentials.json`, where Claude Code on Linux keeps its token, is already kept per account. Three places remain. They are deferred because they could not be tested on Linux.

- Read a session's working folder from `/proc/<pid>/cwd` instead of with `lsof`. Environment variables already come from `/proc/<pid>/environ`.
- Look for the JetBrains and VS Code-based editor settings folders under `~/.config` instead of `~/Library/Application Support`.
- Do not build the menu bar app for Linux. Use `acm status` instead.

### Claude Desktop waits until support arrives

Reports say the Code tab of Claude Desktop does not follow `CLAUDE_CONFIG_DIR`, so acm cannot pick an account for it. The issue requesting multi-account support in Claude Code is also still open. If either changes, this will be revisited.[1]

### Antigravity gets usage display only

The Antigravity CLI `agy` can hold only one account, so acm does not add it as a launcher. It has no environment variable to change its config folder, and it kept using `~/.gemini` even with `GEMINI_DIR` set. Changing `HOME` requires a new sign-in, and the login data goes into a single `antigravity` entry in the macOS keychain.[3] Signing in with a second account seems likely to overwrite this entry, so it was not tested.

With one account, picks and context sharing have nothing to do, so the only use left is seeing usage in one place. `agy -p "/usage" --output-format json` returns the remaining percentage and reset time for each weekly window. acm will show these as one view-only line in the menu bar and `acm status`. If a way to keep separate accounts appears, it will be added the same way as Codex.

### Codex Sites should be collected in the primary account too

The value of artifact collection is managing documents published from other accounts in one primary account. A share link only opens a document. Editing or deleting it works only from the owning account. So Codex's ChatGPT Sites has the same problem.

The Codex CLI on a Plus account came with the `sites` plugin installed.[4] Publishing creates a site with `sites.create_site` and gets a short-lived git token with `sites.create_source_repository_write_credential`. Then it pushes the `dist` built by the plugin script to the Sites git server. The default visibility is owner only. The push step has not been tested end to end yet, so whether another session can update the same site by pushing again is also unverified.

In Claude, one Artifact tool call finishes a publish. A Codex publisher session needs a shell, git, node, and network access. So the current approach of limiting the publisher session to a few tools does not carry over, and the publishing layer must be split into per-tool adapters. Sites is not available on the free and Go plans, so the primary Codex account must be on Plus or higher.[5]

## Some work is not planned for now

The two items below seem unnecessary for now, so they are not planned. They come back if they are missed in use.

- Storing usage as a time series to predict when it runs out and alert at thresholds. Menu bar apps such as claude-limits and Claudius feature this.[2]
- A list of sessions stopped by a limit, with a continue button, in the menu bar window. For now, `acm resume` and the iTerm notification are enough.

## Some assumptions are still unverified

The current code relies on assumptions for the four items below. As each is verified, the code or docs will be fixed. The last one is on the Codex side, so it will be verified when two Codex accounts can be used together.

- Whether VS Code-based extensions pass the bundled claude path as the first argument to `claudeProcessWrapper`. This has not been run with the real extension.
- Whether `claude -p /usage` refreshes an expired token by itself. Leave an account with no session for a day with the menu bar app running. If `refresh_at` never appears in `~/.acm/poll/<account>.json`, it refreshes by itself. In that case, drop the token refresh that starts haiku.
- Whether `/usage` shows the Current session line on an account with a 5h limit that has not been used for more than a day. If not, that account looks like it has no limit until its next use.
- Whether continuing with `acm codex resume` on another Codex account keeps the earlier reasoning history. There may be a limit similar to Claude not being able to use thinking from another organization.

## Footnotes

[1] anthropics/claude-code issue #30031 and its comments. It was still open as of the 2026-10-27 comment. https://github.com/anthropics/claude-code/issues/30031

[2] https://github.com/figueiredouc/claude-limits , https://github.com/Abd-K/claudius-claude-code-usage

[3] 2026-11-03, agy 1.4.8. Even with `GEMINI_DIR` changed, it read `~/.gemini`. Changing `HOME` to a temp folder made it ask for sign-in again. The keychain entry name was checked, but its contents were not opened. The changelog of 1.4.12, released the same day, also said nothing about accounts or config folders. The `AGY_ACCOUNT` in the executable is a variable that picks the account of a CLI attached as a plugin. It is unrelated to agy sign-in.

[4] 2026-11-03, codex-cli 0.166.0. On the account upgraded to Plus, `codex plugin list` showed `sites@openai-curated-remote` 1.1.2 installed and enabled. Creating a site from a test page and getting a git token worked.

[5] OpenAI help article "Creating and managing ChatGPT Sites". https://help.openai.com/en/articles/20001339
