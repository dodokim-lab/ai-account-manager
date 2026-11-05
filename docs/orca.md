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
| Passing work between Claude and Codex | Orca | Orchestration workers. acm picks the account of each worker |

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

## To continue a session that hit its limit

The steps are those of [Account selection and usage](selection.md#a-session-that-hits-a-limit-continues-on-another-account-with-acm-resume), typed in the session's own tab. They were tried with a limit record made by hand, not with a real limit.[11]

1. Do not wait for acm's notification. It is a terminal sequence that iTerm2 shows as a desktop notification, and Orca's terminal has no handler for it. The session shows Claude Code's own limit message, and `acm status` reports the stopped session.
2. Close the session with `/exit`. The tab drops to its shell.
3. Run `acm resume` there. acm picks another account and reopens the session in the same tab, and Orca lists the tab as a Claude agent again.

## To pass work between Claude and Codex

Orca's orchestration lets one agent start another as a worker and get its report back, such as Claude asking Codex for a review. Agent hibernation is a different feature. It pauses idle sessions and is covered under [Still to check](#still-to-check).

1. Install the two skills that teach an agent the commands. They link into the shared skills folder, so sessions on every account get them.

   ```sh
   orca skills install --skill orca-cli --skill orchestration --agent claude,codex
   ```

2. Let a Codex worker report without a prompt. Codex's sandbox blocks the connection to Orca that the report needs, so without a rule the worker stops and asks to run the command outside the sandbox. Save this rule as `~/.codex/rules/orca.rules`.[15]

   ```
   prefix_rule(
       pattern = ["orca", "orchestration", ["send", "ask", "reply", "check"]],
       decision = "allow",
       justification = "Orca worker messaging needs Orca's local socket, which the sandbox blocks",
       match = [
           "orca orchestration send --type worker_done --subject done --body ok --outcome succeeded",
           "orca orchestration ask --question why",
       ],
       not_match = [
           "orca orchestration worker-start --agent codex --spec x",
           "orca terminal send --text x",
           "orca worktree rm --worktree x",
       ],
   )
   ```

3. Run `acm sync`. It links the new `rules` folder into every extra Codex account.
4. In a session Orca started, ask for the other agent by name and say that you want the result back. The skill tells the session to start the worker with `orca orchestration worker-start --agent codex`. In the tests the command was run directly, not through the skill.[13]
5. The worker opens in a new tab. A Codex worker goes through acm like any other Codex session, so it runs on the account acm picks.[13]
6. Wait for the report. Orca types a line into the starting session when a message arrives, and the session reads it with `orca orchestration check`.[15]

The rule allows the four messaging commands and nothing else. They run outside Codex's sandbox with no prompt, in every Codex session on these accounts. The rule does not cover starting a worker, typing into a terminal, or removing a worktree.

Without the rule, the session that started the worker gets a message that the worker is waiting. Approve the prompt in the worker's tab, and the report goes through.[13]

The worker runs in the workspace that the starting session's tab belongs to, which is not always the folder that session is in.

## To reach your sessions from a phone

1. Sign in to an Orca account on the desktop. Without it Orca offers only the desktop's local address, and a phone on mobile data fails with `direct websocket closed 1006`.
2. Open the pairing screen from the account menu on the desktop.
3. Install the Orca app on the phone, choose Pair, and enter the code.

The sessions still run on the desktop, on the account acm picked there.

## To use the phone

- Open a workspace to see its session tabs. A tab opens in the terminal view or the chat view. Orca's docs say a long-press on a tab switches that tab between the two.[7]
- Read every account's usage from the tag at the bottom of a session's terminal. While the phone is attached, Orca sizes the terminal to the phone, and Claude Code cuts a statusline line that is wider than the terminal. acm folds such a line onto more rows, so the items after the tag stay. The fold shows at the session's next statusline update.[6]
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
| Usage from the statusline | Works | Orca leaves `statusLine` in the settings as it is. The tag in front of the statusline lists every Claude account's usage, on the desktop and in the phone's terminal view. A line too wide for the terminal is folded onto more rows |
| Collecting artifacts in one account | Works | A session on another account in an Orca tab handed off a publish, and the artifact landed in the primary account. The publisher session drops Orca's variables.[9] See [Artifact collection](publisher.md) |
| Continuing a session that hit its limit | Works, without the notification | Tried with a limit record made by hand. See [To continue a session that hit its limit](#to-continue-a-session-that-hit-its-limit) |
| Menu bar app and widget | Works, with one gap | They count Orca's sessions too. "New Session…" opens iTerm, not Orca |
| Codex accounts | Works | Orca types `codex` into the tab's shell, and the shell function that `acm setup` added sends it through acm. The Command of Codex was left as it is.[12] |
| Claude and Codex passing work to each other | Works from Claude to a Codex worker | The worker ran on the Codex account acm picked, and its report came back. With a Codex rule the report needs no prompt.[13][15] |

## What Orca does not know about acm

Orca treats every session as the default account. It names a config folder first, and acm sets the real one afterwards. Three things follow.

- Orca's status bar and the phone's usage screen show the default account and its usage, whatever account the session runs on. Read usage from the tag in front of each session's statusline, such as `[work · cl1 62% · cl2 66%]`, or with `acm status` or the menu bar app.[6]
- Orca reads Claude usage by calling the usage API with that account's login token.[2] acm still never reads a token. Orca does it on its own. No setting turns this off for Claude. Orca reads while its window is visible and focused, and when the phone connects.[14]
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

- A real limit in an Orca session. Orca's code treats that stop as the end of a failed turn, so Orca may send its own notification to the desktop and the phone. This was not seen.[11]
- An agent that Orca starts as a chat instead of a terminal. Nothing is typed into a shell then, so the session may skip acm and run on the default account.
- The Command of Codex set to `<home>/.local/bin/acm codex`, for a shell without acm's function. Orca's docs warn that a wrapper which sets `CODEX_HOME` reads a home Orca did not set up.[4] With the shell function, the hooks were found, because acm links each extra Codex account's `hooks.json` and `config.toml` to those in `~/.codex`.[12]
- A Claude session that starts a worker on its own from the installed skills, and a Codex session that starts a Claude worker. The Codex rule does not cover `worker-start`, so that session would stop at a prompt.
- The fold on a phone. It was seen in a desktop terminal 48 columns wide, and the cut it replaces was reported from a phone.[6]
- Agent hibernation, which is off by default. Orca reopens a paused session with the same launch command and `--resume`.[5] Through acm the pick runs again, so the session may continue on another account.
- Whether Orca's usage reads make the API answer `429` to acm's `/usage` poll on the default account. Both call the same API, and a menu bar plugin that called it every 2 minutes did that. See footnote 2 of [Account selection and usage](selection.md).
- A phone on mobile data while the desktop is behind a VPN, and a Relay connection held for a long time.
- Quick Commands for `acm status` and `acm resume`. A tab that ran `acm status` showed on the phone, but neither command was saved as a Quick Command.

## Footnotes

[1] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, acm 0.3.0, macOS 15.7.1. Two Claude accounts and two Codex accounts. Sessions started from Orca's agent menu and with `acm -a` in an Orca terminal were listed with `"via": "acm"`. The phone was paired through Orca Relay after signing in on the desktop.

[2] Usage & rate-limit tracking in the Orca docs. "For Claude, Orca requests `https://api.anthropic.com/api/oauth/usage` with the token from your existing Claude Code login; it does not ask for extra credentials." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/usage-tracking.mdx

[3] Settings in the Orca docs, the Agents section, lists Agent status hooks with the CLI `orca agent hooks on|off|status`. On this setup `orca agent hooks status` reported the Claude and Codex hooks as installed. `off` was not run. https://github.com/stablyai/orca/blob/main/docs/site/content/docs/settings.mdx

[4] Codex in the Orca docs, the section "Wrapper scripts that set `CODEX_HOME`". https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/codex.mdx

[5] Agent hibernation in the Orca docs. It says Orca relaunches the agent CLI with resume flags such as `claude --resume <id>`, and "Resume also reuses the launch command, arguments, and private environment captured when Orca first opened the agent." https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/hibernation.mdx

[6] 2026-11-05, Orca 1.4.249 and its phone app, Claude Code 2.1.318. The statusline of a session showed on the phone in the terminal view. Before acm folded wide lines, the tag showed on the phone and the items after it were cut off. That was reported for the chat view, and which view it was has not been checked again. Orca's docs describe the chat view as a transcript.[7] The app's terminal contract, in `terminal-viewport-schemas-params.js`, describes the display mode `auto` as the phone setting the terminal's size while it is attached, and `desktop` as no resize. In a desktop terminal 48 columns wide, the statusline ended in `…` a few characters after the tag. With the fold it showed on four rows with nothing cut. The fold was not seen on a phone. The phone's usage screen listed one account. How the tag is built and folded is in [Account selection and usage](selection.md#the-statusline-tag-lists-every-claude-accounts-usage).

[7] Terminal and Mobile in the Orca docs. Quick Commands are created under Settings → Quick Commands, run from the tab bar, and "sync both ways" with the phone. https://github.com/stablyai/orca/blob/main/docs/site/content/docs/mobile.mdx

[8] 2026-11-05, Orca 1.4.249. A development plugin with a worker, one status bar item, and one panel was loaded with `orca plugin dev load`. The status bar showed `cl1 62% · cl2 66%` and the panel drew a card per account. The Orca docs say of `statusBar.update` "Desktop app only", and Settings lists the plugin system as alpha. The plugin was unloaded after the test. https://github.com/stablyai/orca/blob/main/docs/reference/plugin-host-api.md

[9] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, tmux 3.8. A session started with `acm -a` on the second Claude account in an Orca terminal tab wrote an HTML file, staged it with `acm publisher check`, and sent the staged path to the publisher session. `check` started the publisher session, which returned a URL, and the artifact was listed under the primary account. The requesting claude process carried 25 `ORCA_*` variables. The publisher session's process carried none, and no `CLAUDE_CODE_PLUGIN_DIRS`.

[10] 2026-11-05, Orca 1.4.249, macOS 15.7.1. With the variable set by `launchctl setenv`, Orca was quit and started again with `open` from an empty environment, without `--env`. The new main process had launchd as its parent and carried the variable. The Dock icon itself was not clicked. A test app that only records its environment gave the same result. The sessions running in Orca's terminals kept running through the restart.

[11] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318. No real limit was hit. A session started with `acm -a` on the second Claude account in an Orca tab answered one prompt. acm's `StopFailure` hook was then run by hand in that session's environment with a `rate_limit` event, and it recorded the second account. `acm resume` refused while the session was open. After `/exit`, `acm resume` typed in the same tab picked the first account and reopened the session. Asked there for the word from the first turn, it answered correctly, and `orca worktree ps` listed the tab as a Claude agent in state `done`. The notification sequence (OSC 9) written to the tab's terminal did not change the screen, and the desktop was not watched for a notification. The app's terminal code registers handlers for OSC 0, 1, 2, 4, 7, 8, 10 to 12, 52, 104, 110 to 112, 133, 1337, and 7501, and none for 9. Its hook listener, in `claude-events.js`, gives a `StopFailure` event the outcome `failure` at the end of a turn. The same event sent to Orca's hook by hand was not taken, so Orca's reaction was not seen.

[12] 2026-11-05, Orca 1.4.249, codex-cli 0.166.0. `orca agent launch --agent codex --surface terminal` started a session whose parent process was the tab's login shell. acm printed the account it picked, `acm status --json` listed the session under the second Codex account with `"via": "acm"`, and the process carried that account's `CODEX_HOME`. `orca worktree ps` listed the tab as a Codex agent in state `done` with its last message, so Orca's status hooks ran in that account's home.

[13] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, codex-cli 0.166.0, with Orca's agent permissions not set to Yolo. Neither skill was installed yet, so a Claude session on the first Claude account ran `orca orchestration worker-start --agent codex --worktree current --spec ...` by hand. The worker opened in a terminal on the second Codex account with `"via": "acm"`, read a file, and finished the task. Its `orca orchestration send --type worker_done` failed with `runtime_access_denied: The Codex sandbox blocked this command from connecting to Orca (EPERM)`, and Codex asked to run the command again outside the sandbox. Orca typed "You have 1 orchestration message" into the starting session, and `orca orchestration check` returned an escalation with the stop reason `needs-input`. The prompt was approved later the same day, and `orca orchestration check` then returned the worker's `worker_done` with the outcome `succeeded`. The install afterwards added two folders under `~/.agents/skills` and two links in the shared skills folder, and a Claude session that was already running listed both skills.

[14] 2026-11-05, Orca 1.4.249. Orca's docs list display choices only, which are the status bar items and percent used or remaining.[2] In the app's main code the usage service starts with the window and has no switch for Claude. It skips the Claude read only while a retry time from the API is in effect, and only the Antigravity read depends on its status bar item. `shouldBackgroundPoll` is true when the window is visible, not minimized, and focused. Orca's docs name more triggers, among them the phone connecting.[2]

[15] 2026-11-05, Orca 1.4.249, codex-cli 0.166.0. The rule file was saved in `~/.codex/rules`, and `acm sync` linked that folder into the second Codex account's home. `codex execpolicy check --rules <file>` matched `orca orchestration send` with the decision `allow`, and matched neither `orca orchestration worker-start` nor `orca terminal send`. A second worker, started the same way as the first, ran on the second Codex account and sent `worker_done` with no prompt. Orca typed "You have 1 orchestration message" into the starting session, and `orca orchestration check` returned the report with the outcome `succeeded`. Without the rule the same command had failed inside the sandbox, so the allowed command ran outside it.
