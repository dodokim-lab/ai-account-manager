# Setup

This doc covers what `install.sh` and `acm setup` change, and how to send sessions started outside the terminal through acm. If you only want to install, the quick start in the README is enough.

## install.sh does four things

```bash
./install.sh              # CLI, statusline wrapper, and menu bar app
./install.sh --no-app     # CLI only, no menu bar app
./install.sh --uninstall  # restore the statusline and remove the CLI and the app
```

- First, it copies `bin/acm` and `bin/acm-statusline` to `~/.local/bin`. They are copies, not symlinks, so acm keeps running if you move the repository or delete the worktree. After you edit the source, rerun `install.sh` to apply the change. It records which commit of which repository it installed in `~/.acm/install.json`.
- Second, it wraps `statusLine` in `~/.claude/settings.json` as `acm-statusline '<original command>'`. The original command stays as the wrapper's argument and runs as before, so the display does not change. acm does not move the original command into a file of its own, because Claude Code does not protect such a file. If a session edited that file without asking, code would run in every session's statusline. On a new install with no `settings.json` yet, it creates one. It keeps the settings from before the change as `settings.json.acm-bak-<time>`.
- Third, it builds the menu bar app in `app/`, puts it in `/Applications/ACM.app`, and launches it.
- Fourth, it runs `acm setup`, which asks about the remaining settings one by one and applies them. The next section covers it.

It needs `python3`, `jq`, and `claude`. If any of them is missing, it tells you how to install it and stops. It also stops when `swiftc` is missing, unless you pass `--no-app`. `codex` and `tmux` are optional. You need `codex` only for Codex accounts. If `~/.local/bin` is not on `PATH`, `acm setup` adds it along with the shell function.

`--uninstall` reverts the shell lines and IDE plugin settings that `acm setup` added. It keeps the account folders and `~/.acm`. They hold login data, so deleting them is your call.

## acm setup asks about first-time settings and applies them

`acm setup` checks the seven items below in order. It asks only about the ones not done yet and applies them. It leaves finished items alone, so you can run it any number of times.

| Check | If not done |
|---|---|
| Terminal | Adds `PATH` and the `claude` and `codex` shell functions to the login shell's rc file. That is `~/.zshrc` for zsh. For bash it is `~/.bash_profile` on macOS and `~/.bashrc` on Linux |
| Publisher session runtime | If tmux is missing, installs it with `brew install tmux`. On Linux it names the package manager command, such as `sudo apt install tmux`, and leaves it to you |
| IDE | For each JetBrains IDE with the Claude Code plugin, changes the Claude command of the newest version to `~/.local/bin/acm`. For VS Code, Cursor, Windsurf, and VSCodium with the Claude Code extension, adds `claudeCode.claudeProcessWrapper` to the user `settings.json` |
| Accounts | Signs in Claude accounts that are not signed in. If there is only one account, asks whether to add one. If there are extra accounts, moves `projects`, `skills`, and `hooks` to `~/.acm/shared` |
| Codex accounts | If `codex` and `~/.codex` exist, asks whether to register the default account `cx1`. Checks sign-in and shared links for each registered Codex account |
| Artifact collection | With two or more accounts, writes the default text for the publisher session's scope, asks you to pick the primary account, and turns on artifact collection. Pick the account you are signed in to on claude.ai in your browser as the primary account. Otherwise you cannot open the artifacts |
| Limit handoff | With two or more accounts, adds a `StopFailure` hook with the `rate_limit` matcher to `~/.claude/settings.json`. Existing hooks stay as they are, and `--undo` removes only the acm hook |

If a JetBrains IDE is running, setup does not change the plugin settings and lists them as a remaining step. The IDE may overwrite the file with the settings it holds in memory when it quits. VS Code-based editors do not overwrite `settings.json` when they quit, so setup changes it even while they run. The change applies after you reload the window (Developer: Reload Window). Setup does not rewrite `settings.json`. It inserts one line after the first `{`, so comments and formatting stay as they are, and `--undo` removes only that line. If a different `claudeProcessWrapper` is already set, setup leaves it alone and lists it as a remaining step. For the same reason, setup does not move the shared folder while a claude session is running. macOS asks for the menu bar app's permission to control iTerm the first time the app uses it, so setup cannot grant it for you.

```bash
acm setup            # asks and applies one by one. Outside a terminal, it only shows, like --check
acm setup --yes      # uses the defaults without asking. Skips steps that need you to sign in, such as adding an account
acm setup --check    # changes nothing and shows only the remaining steps
acm setup --undo     # reverts the shell lines and IDE plugin settings it added. Leaves accounts and publisher settings as they are
```

When `install.sh` runs in a terminal, `acm setup` asks. When it runs inside a script, setup only shows. To apply the defaults without asking, run `ACM_SETUP=--yes ./install.sh`. Setup keeps the IDE settings from before the change in `~/.acm/setup.json`, and `--undo` uses them to revert. `--undo` deletes settings files that acm created.

## Sessions started outside the terminal also go through acm

If you run `claude` directly, it skips acm and starts on the default account. Most of the default account's usage comes from this. So setup adds a shell function to `~/.zshrc` that sends only the `claude` and `codex` you type in a terminal to acm. `claude` goes to `acm claude` and `codex` goes to `acm codex`, and each picks among that tool's accounts. `acm setup` adds it. To add it yourself, it is this one line.

```bash
if command -v acm >/dev/null 2>&1; then eval "$(acm shell-init)"; fi
```

The function goes through acm only when you type the command in a terminal. In pipes and scripts it calls the original `claude` and `codex`. Subcommands such as `mcp`, `auth`, and `update` do not need an account pick, so they pass straight through. For Codex, the same goes for subcommands such as `login`, `logout`, `mcp`, and `update`. The executables themselves stay unchanged, so `claude` and `codex` called by other tools are not affected. To start them the original way, type `command claude` or `command codex`.

Type `acm` alone and it asks which tool to open. Press Enter to open Claude. It does not ask if no Codex account is registered and `codex` or `~/.codex` is missing. In a terminal started by an IDE, such as the JetBrains plugin, it opens Claude without asking. Shells opened before you upgraded to this version still have the old function. In them, `claude` without arguments asks for a tool, or `codex` skips acm and starts on the default account `cx1`. Open a new shell or run `exec zsh -l` in that shell to use the new function.

Each place that starts sessions outside the terminal needs its own change.

| Where sessions start | What to change |
|---|---|
| iTerm, herdr | Run through `acm` in the shell |
| JetBrains Claude Code plugin | Set the Claude command in the settings to the absolute path of `~/.local/bin/acm`. `acm setup` changes `claudeCommand` in `options/claude-code-plugin-settings.xml` while the IDE is closed. The change applies when you start the IDE again |
| Claude Code extension for VS Code-based editors | Set `claudeCode.claudeProcessWrapper` in the user settings to the absolute path of `~/.local/bin/acm`. `acm setup` adds it |
| Menu bar app | "New Session…" asks for a tool and a folder, then runs `acm claude` or `acm codex` in a new iTerm window |

The first time you click "New Session…", macOS asks whether ACM may control iTerm. The window opens only after you allow it.

When a VS Code-based extension calls acm through `claudeProcessWrapper`, it passes the path of its bundled claude as an argument.[1] If the first argument is a claude executable inside an `anthropic.claude-code-<version>` extension folder, acm picks an account and starts that claude. Subcommands such as `auth` or `--version` pass through without an account pick. acm does not run executables outside the extension folder, because such a path may be a prompt argument, as in `claude ./claude-setup.sh`. This design assumes the path comes as the first argument. It is unverified with the real extension.

The shell function and the IDE extensions send claude through acm, so if acm fails, claude does not start either. For this reason, when acm hits an unexpected error while picking an account, it skips the pick, starts claude as is, and reports the error in one line. If no account is signed in, it starts on the first account so Claude Code shows its login screen. If the extension also passes `--append-system-prompt` or `--disallowedTools`, acm appends its session rules after those values, so the extension's values are kept. Claude Desktop does not follow `CLAUDE_CONFIG_DIR`, so it cannot go through acm.

## How do I upgrade acm to a new version?

`acm upgrade` runs `git pull --ff-only` on the repository recorded in `~/.acm/install.json`, then reruns that repository's `install.sh`. If you installed without the menu bar app, the reinstall also leaves the app out. If you edited the repository yourself, `acm upgrade --no-pull` reinstalls without pulling. `acm version` shows the acm and claude versions and the installed commit. The `install.sh` of this version is the first to write this record. If you installed an earlier version, run `./install.sh` from the repository yourself once.

When you upgrade from 0.2.0 to 0.3.0, Claude account ids stay `acc1` and `acc2`, so you do not need to sign in again. Only newly added accounts follow the new scheme, such as `cl3`. Changing the ids to `cl` as well means renaming the extra account folders, so those accounts must sign in again. In terminals opened before the upgrade, `codex` does not go through acm. Open a new one or run `exec zsh -l`.

## Footnotes

[1] The Extension settings table in the Claude Code VS Code docs. "Executable used to launch the Claude process. The bundled binary path is passed as an argument when present." https://code.claude.com/docs/en/vs-code
