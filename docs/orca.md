# Using acm with Orca

[Orca](https://github.com/stablyai/orca) is a desktop app that runs coding agents in git worktrees and pairs with a phone app. acm has no view across devices. This doc puts Orca in front of acm. Orca starts and shows the sessions, and acm still picks the account for each one. Read it if you use acm and want to reach your sessions from a phone.

Everything here was observed on one macOS setup.[1] Orca changes often, so a step may differ in your version.

## Quick start

1. Install acm and add your accounts as in the [guide](../GUIDE.md). `acm status` must list them before you go on.
2. Install Orca. The plain `orca` cask is a different app, so name the tap.

   ```sh
   brew install --cask stablyai/orca/orca
   ```

3. Open Orca and add a repository. The first run adds Orca's hooks to your Claude Code and Codex settings, listed in [What Orca changes on your machine](#what-orca-changes-on-your-machine).
4. In Settings → Agents, set the Command of Claude Code to the full path of acm followed by `claude`. A bare `acm` asks which tool to start, and that question swallows the first prompt Orca sends.

   ```
   <home>/.local/bin/acm claude
   ```

5. Start Claude Code from the agent menu of a worktree.
6. Run `acm status --json` in any terminal. The session is listed under the account acm picked, with `"via": "acm"`.

From here every Claude Code session Orca starts goes through acm.

## To start a session on a chosen account

Open a terminal in the worktree and run acm yourself. Orca shows the session like one started from the agent menu.

```sh
acm -a <account>
```

## To reach your sessions from a phone

1. Sign in to an Orca account on the desktop. Without it Orca offers only the desktop's local address, and a phone on mobile data fails with `direct websocket closed 1006`.
2. Open the pairing screen from the account menu on the desktop.
3. Install the Orca app on the phone, choose Pair, and enter the code.

The sessions still run on the desktop, on the account acm picked there.

## What works under Orca

| acm feature | Under Orca | Notes |
|---|---|---|
| Picking an account per session | Works | Seen for the automatic pick and for `acm -a <account>` |
| Shared history, memory, and skills | Works | Sessions on two accounts in an Orca worktree read the memory folder of the main repository |
| Usage from the statusline | Works | Orca leaves `statusLine` in the settings as it is. The tag in front of the statusline lists every Claude account's usage, on the desktop and in the phone's terminal view |
| Collecting artifacts in one account | Starts clean, publish not yet tried | The rule to hand off is attached to sessions on other accounts. The publisher session drops Orca's variables. See [Artifact collection](publisher.md) |
| Continuing a session that hit its limit | Not yet tried | The StopFailure hook still runs. Run `acm resume` in a terminal of the same worktree |
| Menu bar app and widget | Works, with one gap | They count Orca's sessions too. "New Session…" opens iTerm, not Orca |
| Codex accounts | Not yet tried | Set the Command of Codex to `<home>/.local/bin/acm codex` |

## What Orca does not know about acm

Orca treats every session as the default account. It names a config folder first, and acm sets the real one afterwards. Three things follow.

- Orca's status bar and the phone's usage screen show the default account and its usage, whatever account the session runs on. Read usage from the tag in front of each session's statusline, such as `[work · cl1 62% · cl2 66%]`, or with `acm status` or the menu bar app.[6]
- Orca reads Claude usage by calling the usage API with that account's login token.[2] acm still never reads a token. Orca does it on its own.
- Do not add accounts in Orca's account switcher. Accounts added there live in Orca's data, where acm cannot see them.

## What Orca changes on your machine

On first run Orca added one hook entry to each of 15 hook events in `~/.claude/settings.json`. It added 9 hooks to `~/.codex/hooks.json` with trust records in `~/.codex/config.toml`, and a hooks file under `~/.gemini`. It kept the existing entries and left `.bak` copies. acm shares these files between accounts, so the hooks run in every account's sessions. In a session Orca did not start, the hook exits in about 0.03 seconds. `orca agent hooks status` shows whether they are installed, and Orca's docs give `orca agent hooks off` to remove them.[3]

While it runs, Orca listens on port 6768 on every network interface. The pairing setting offers `automatic` and `local-only`, and neither limits pairing to Relay.

Each session Orca starts carries more than twenty `ORCA_*` variables and `CLAUDE_CODE_PLUGIN_DIRS`. acm passes them to the session, because Orca's status display needs them, but not to the publisher session.

## Troubleshooting

| Symptom | Fix |
|---|---|
| A new session shows acm's question about which tool to start, and the first prompt is gone | End the Command with `claude`, as in step 4 |
| The phone fails to pair with `direct websocket closed 1006` | Sign in to an Orca account on the desktop, then pair again |
| Sign-in or Relay fails on a network that re-signs HTTPS, with `SELF_SIGNED_CERT_IN_CHAIN` in a Node fetch | Start Orca with the network's CA, as below |

Orca's main process is Node, and it did not trust a CA that the macOS keychain trusts. Give it a PEM file that holds that CA.

```sh
open --env NODE_EXTRA_CA_CERTS=<bundle.pem> -a Orca
```

For a start from the Dock, set the variable for the login session. It lasts until you log out and reaches every Node and Electron app started afterwards.

```sh
launchctl setenv NODE_EXTRA_CA_CERTS <bundle.pem>
```

## Still to check

- A real publish handed off from a session Orca started on an account other than the primary one.
- Whether Orca's terminal shows the notification acm sends when a session hits its limit.
- Codex through `acm codex`. Orca's docs warn that a wrapper which sets `CODEX_HOME` reads a home Orca did not set up.[4] acm links each extra Codex account's `hooks.json` and `config.toml` to those in `~/.codex`, so the hooks should be found.
- Agent hibernation, which is off by default. Orca reopens a paused session with the same launch command and `--resume`.[5] Through acm the pick runs again, so the session may continue on another account.
- A phone on mobile data while the desktop is behind a VPN, and a Relay connection held for a long time.
- Whether an Orca started from the Dock receives the variable set with `launchctl setenv`.

## Footnotes

[1] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, acm 0.3.0, macOS 15.7.1. Two Claude accounts and two Codex accounts. Sessions started from Orca's agent menu and with `acm -a` in an Orca terminal were listed with `"via": "acm"`. The phone was paired through Orca Relay after signing in on the desktop.

[2] Usage & rate-limit tracking in the Orca docs. "For Claude, Orca requests `https://api.anthropic.com/api/oauth/usage` with the token from your existing Claude Code login; it does not ask for extra credentials." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/usage-tracking.mdx

[3] Settings in the Orca docs, the Agents section, lists Agent status hooks with the CLI `orca agent hooks on|off|status`. On this setup `orca agent hooks status` reported the Claude and Codex hooks as installed. `off` was not run. https://github.com/stablyai/orca/blob/main/docs/site/content/docs/settings.mdx

[4] Codex in the Orca docs, the section "Wrapper scripts that set `CODEX_HOME`". https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/codex.mdx

[5] Agent hibernation in the Orca docs. It says Orca relaunches the agent CLI with resume flags such as `claude --resume <id>`, and "Resume also reuses the launch command, arguments, and private environment captured when Orca first opened the agent." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/hibernation.mdx

[6] 2026-11-05, Orca 1.4.249 and its phone app, Claude Code 2.1.318. The statusline of a session showed on the phone in the terminal view. The phone's usage screen listed one account. How the tag is built is in [Account selection and usage](selection.md#the-statusline-tag-lists-every-claude-accounts-usage).
