# Roadmap

This doc collects the work deferred for acm and the reasons. The choices were made after comparing acm with other multi-account tools. It is split into gaps to close, work not planned for now, and assumptions not yet verified.

## The next steps go in this order

1. Verify the items in "Some assumptions are still unverified" below. If an assumption in the current code is wrong, fix it before anything else.
2. Collect Codex Sites publishing in the primary account too.
3. Support Linux, Claude Desktop, and Windows in that order, as planned in [Platform support plan](platforms.md).

## Some gaps still need closing

### Codex Sites should be collected in the primary account too

The value of artifact collection is managing documents published from other accounts in one primary account. A share link only opens a document. Editing or deleting it works only from the owning account. So Codex's ChatGPT Sites has the same problem.

The Codex CLI on a Plus account came with the `sites` plugin installed.[1] Publishing creates a site with `sites.create_site` and gets a short-lived git token with `sites.create_source_repository_write_credential`. Then it pushes the `dist` built by the plugin script to the Sites git server. The default visibility is owner only. The push step has not been tested end to end yet, so whether another session can update the same site by pushing again is also unverified.

In Claude, one Artifact tool call finishes a publish. A Codex publisher session needs a shell, git, node, and network access. So the current approach of limiting the publisher session to a few tools does not carry over, and the publishing layer must be split into per-tool adapters. Sites is not available on the free and Go plans, so the primary Codex account must be on Plus or higher.[2]

## Some work is not planned for now

The two items below seem unnecessary for now, so they are not planned. They come back if they are missed in use.

- Storing usage as a time series to predict when it runs out and alert at thresholds. Menu bar apps such as claude-limits and Claudius feature this.[3]
- A list of sessions stopped by a limit, with a continue button, in the menu bar window. For now, `acm resume` and the iTerm notification are enough.

## Some assumptions are still unverified

The current code relies on assumptions for the four items below. As each is verified, the code or docs will be fixed. The last one is on the Codex side, so it will be verified when two Codex accounts can be used together.

- Whether VS Code-based extensions pass the bundled claude path as the first argument to `claudeProcessWrapper`. This has not been run with the real extension.
- Whether `claude -p /usage` refreshes an expired token by itself. Leave an account with no session for a day with the menu bar app running. If `refresh_at` never appears in `~/.acm/poll/<account>.json`, it refreshes by itself. In that case, drop the token refresh that starts haiku.
- Whether `/usage` shows the Current session line on an account with a 5h limit that has not been used for more than a day. If not, that account looks like it has no limit until its next use.
- Whether continuing with `acm codex resume` on another Codex account keeps the earlier reasoning history. There may be a limit similar to Claude not being able to use thinking from another organization.

## Footnotes

[1] 2026-11-03, codex-cli 0.166.0. On the account upgraded to Plus, `codex plugin list` showed `sites@openai-curated-remote` 1.1.2 installed and enabled. Creating a site from a test page and getting a git token worked.

[2] OpenAI help article "Creating and managing ChatGPT Sites". https://help.openai.com/en/articles/20001339

[3] https://github.com/figueiredouc/claude-limits , https://github.com/Abd-K/claudius-claude-code-usage
