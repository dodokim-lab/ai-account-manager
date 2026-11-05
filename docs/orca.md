# Using acm with Orca

[Orca](https://github.com/stablyai/orca) is a desktop app that runs coding agents in git worktrees and pairs with a phone app. acm has no view across devices. This doc puts Orca in front of acm. Orca starts and shows the sessions, and acm still picks the account for each one. Read it if you use acm and want to reach your sessions from a phone.

Everything here was observed on one macOS setup.[1] Orca changes often, so a step may differ in your version.

## Who does what

| Job | Done by | How |
|---|---|---|
| Starting a session and showing its terminal | Orca | It runs the Command you set for the agent |
| Picking the account | acm | The Command is `acm claude`, so every start goes through the pick |
| History, memory, skills, settings | acm | Every account links to the same shared folders |
| Showing sessions on the phone | Orca | The phone app pairs with the desktop through Orca Relay |
| Showing every account's usage | acm | The tag in front of each session's statusline |
| Collecting artifacts in one account | acm | The publisher session, started outside Orca in tmux |

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

From here every Claude Code session Orca starts goes through acm. The first line of a new session shows the account acm picked, and the statusline starts with its tag.

```
[work · cl1 62% · cl2 66%] <your statusline>
```

## To start a session on a chosen account

Open a terminal in the worktree and run acm yourself. Orca shows the session like one started from the agent menu.

```sh
acm -a <account>
```

## To move a running session into Orca

A session started in another terminal keeps its history in the shared folder, so Orca can reopen it.

1. Copy the session ID. Claude Code prints it with `claude --resume <id>` when the session exits.
2. Close the session where it runs. Two processes on one session write to the same record.
3. Open a terminal in Orca in the workspace of that repository.
4. Go to the folder the session was started in, and resume. That folder is what was tried. A worktree folder Orca made was not.

   ```sh
   cd <folder the session ran in> && acm -a <account> --resume <session id>
   ```

Without `-a <account>`, use `acm claude --resume <session id>` and acm picks the account again. The tab belongs to the workspace whose terminal you opened, not to the folder you moved to, so the phone lists it under that workspace.

## To reach your sessions from a phone

1. Sign in to an Orca account on the desktop. Without it Orca offers only the desktop's local address, and a phone on mobile data fails with `direct websocket closed 1006`.
2. Open the pairing screen from the account menu on the desktop.
3. Install the Orca app on the phone, choose Pair, and enter the code.

The sessions still run on the desktop, on the account acm picked there.

## To use the phone

- Open a workspace to see its session tabs. A tab opens in the terminal view or the chat view. Orca's docs say a long-press on a tab switches that tab between the two.[7]
- Read every account's usage from the tag at the bottom of a session. It was seen in the terminal view. The chat view was not checked.[6]
- Do not rely on the phone's usage screen. It lists the accounts Orca manages, which is the default account only.
- To see the full table, add a Quick Command with the command `acm status`. The list syncs between the desktop and the phone, and running it opens a new tab.[7]

## Ways to show usage in Orca

Three ways were tried. The statusline tag is the one that needs nothing opened and shows on the phone.

| Way | Desktop | Phone | Cost |
|---|---|---|---|
| The statusline tag | Shows in every session | Shows in the terminal view | Built into acm. `acm statusline-usage off` turns it off |
| A terminal tab running `acm status` | Shows the full table | Shows, as one more tab to open | None. Save it as a Quick Command |
| An Orca plugin with a status bar item and a sidebar panel | Both showed, fed by `acm status --json` every 30 seconds | Not expected. Orca's docs call status bar items desktop only, and the phone app's source has no code that draws a plugin panel. Not checked on a phone | A plugin to keep, on an API Orca marks as alpha[8] |

## What works under Orca

| acm feature | Under Orca | Notes |
|---|---|---|
| Picking an account per session | Works | Seen for the automatic pick and for `acm -a <account>` |
| Shared history, memory, and skills | Works | Sessions on two accounts in an Orca worktree read the memory folder of the main repository |
| Usage from the statusline | Works | Orca leaves `statusLine` in the settings as it is. The tag in front of the statusline lists every Claude account's usage, on the desktop and in the phone's terminal view |
| Collecting artifacts in one account | Works | A session on another account in an Orca tab handed off a publish, and the artifact landed in the primary account. The publisher session drops Orca's variables.[9] See [Artifact collection](publisher.md) |
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
| A tab you just made does not show on the phone | Open the workspace the tab belongs to. `orca terminal create` makes the tab in the workspace of the folder it was run from |

Orca's main process is Node, and it did not trust a CA that the macOS keychain trusts. Give it a PEM file that holds that CA.

```sh
open --env NODE_EXTRA_CA_CERTS=<bundle.pem> -a Orca
```

For a start from the Dock, set the variable for the login session. It lasts until you log out and reaches every Node and Electron app started afterwards. An Orca started again without `--env` received it.[10]

```sh
launchctl setenv NODE_EXTRA_CA_CERTS <bundle.pem>
```

## Still to check

- Whether Orca's terminal shows the notification acm sends when a session hits its limit.
- Codex through `acm codex`. Orca's docs warn that a wrapper which sets `CODEX_HOME` reads a home Orca did not set up.[4] acm links each extra Codex account's `hooks.json` and `config.toml` to those in `~/.codex`, so the hooks should be found.
- Agent hibernation, which is off by default. Orca reopens a paused session with the same launch command and `--resume`.[5] Through acm the pick runs again, so the session may continue on another account.
- A phone on mobile data while the desktop is behind a VPN, and a Relay connection held for a long time.
- The Quick Command for `acm status`. A tab that ran `acm status` showed on the phone, but the command was not saved as a Quick Command.

## Footnotes

[1] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, acm 0.3.0, macOS 15.7.1. Two Claude accounts and two Codex accounts. Sessions started from Orca's agent menu and with `acm -a` in an Orca terminal were listed with `"via": "acm"`. The phone was paired through Orca Relay after signing in on the desktop.

[2] Usage & rate-limit tracking in the Orca docs. "For Claude, Orca requests `https://api.anthropic.com/api/oauth/usage` with the token from your existing Claude Code login; it does not ask for extra credentials." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/usage-tracking.mdx

[3] Settings in the Orca docs, the Agents section, lists Agent status hooks with the CLI `orca agent hooks on|off|status`. On this setup `orca agent hooks status` reported the Claude and Codex hooks as installed. `off` was not run. https://github.com/stablyai/orca/blob/main/docs/site/content/docs/settings.mdx

[4] Codex in the Orca docs, the section "Wrapper scripts that set `CODEX_HOME`". https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/codex.mdx

[5] Agent hibernation in the Orca docs. It says Orca relaunches the agent CLI with resume flags such as `claude --resume <id>`, and "Resume also reuses the launch command, arguments, and private environment captured when Orca first opened the agent." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/hibernation.mdx

[6] 2026-11-05, Orca 1.4.249 and its phone app, Claude Code 2.1.318. The statusline of a session showed on the phone in the terminal view. The phone's usage screen listed one account. How the tag is built is in [Account selection and usage](selection.md#the-statusline-tag-lists-every-claude-accounts-usage).

[7] Terminal and Mobile in the Orca docs. Quick Commands are created under Settings → Quick Commands, run from the tab bar, and "sync both ways" with the phone. https://github.com/stablyai/orca/blob/main/docs/site/content/docs/mobile.mdx

[8] 2026-11-05, Orca 1.4.249. A development plugin with a worker, one status bar item, and one panel was loaded with `orca plugin dev load`. The status bar showed `cl1 62% · cl2 66%` and the panel drew a card per account. The Orca docs say of `statusBar.update` "Desktop app only", and Settings lists the plugin system as alpha. The plugin was unloaded after the test. https://github.com/stablyai/orca/blob/main/docs/reference/plugin-host-api.md

[9] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, tmux 3.8. A session started with `acm -a` on the second Claude account in an Orca terminal tab wrote an HTML file, staged it with `acm publisher check`, and sent the staged path to the publisher session. `check` started the publisher session, which returned a URL, and the artifact was listed under the primary account. The requesting claude process carried 25 `ORCA_*` variables. The publisher session's process carried none, and no `CLAUDE_CODE_PLUGIN_DIRS`.

[10] 2026-11-05, Orca 1.4.249, macOS 15.7.1. With the variable set by `launchctl setenv`, Orca was quit and started again with `open` from an empty environment, without `--env`. The new main process had launchd as its parent and carried the variable. The Dock icon itself was not clicked. A test app that only records its environment gave the same result. The sessions running in Orca's terminals kept running through the restart.
