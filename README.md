# ai-account-manager

English | [한국어](README.ko.md)

<img src="docs/logo.svg" alt="acm logo: a next-pick marker above two usage bars" width="96">

acm is a launcher for one person who has several Claude Code and Codex CLI subscription accounts. Each time you start a session, acm picks the account of that tool with the most headroom left, so usage drains evenly across your accounts. Memory, history, settings, and skills live in one `~/.claude` or `~/.codex` per tool that every account shares. Your context carries over no matter which account a session lands on.

Turn on artifact collection and Claude artifacts published from any account's session end up under one primary account.

acm is an unofficial tool and is not affiliated with Anthropic or OpenAI. It never reads or moves login tokens. Each account signs in through Claude Code's or Codex's own login flow. Usage comes from the statusline and from `claude -p /usage` and `codex app-server` run under that account. Anthropic notes that [advertised usage limits assume ordinary, individual usage](https://code.claude.com/docs/en/legal-and-compliance), so use acm only with accounts you own.

## Quick start

acm runs on macOS only for now. Install these tools first.

| Tool | Needed |
|---|---|
| `python3`, `jq`, `claude` | Always |
| `swiftc` | To build the menu bar app. The app runs on Apple silicon with macOS 14 or later. Run `./install.sh --no-app` to skip it |
| `codex` | For Codex accounts |
| `tmux` | For artifact collection. If it is missing, `acm setup` offers to install it with Homebrew |

If `python3`, `jq`, or `claude` is missing, `install.sh` stops and tells you how to install it. It also stops without `swiftc` when you install the app.

1. Clone the repository.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ```

2. Quit JetBrains IDEs and any running claude sessions. If they are running, `acm setup` leaves the IDE plugin settings and the shared folder alone and lists them as remaining steps.
3. Run `./install.sh`. It installs the CLI, the statusline wrapper, and the menu bar app, then runs `acm setup` to walk you through the rest.
4. When setup asks whether to add an account, add one and sign in with it. The default account `cl1` is your current `~/.claude`, so it needs nothing.
5. Open a new terminal and type `claude`. The shell function that setup added to your rc file sends it to `acm claude`, which starts on the Claude account with the most headroom.
6. Run `acm status` to check sign-in and usage for each account.

## Adding accounts

```bash
acm add cl2                 # creates ~/.claude-cl2
acm -a cl2 auth login       # sign in with that account
acm rm cl2                  # removes it from the list, keeps the folder and the keychain entry
```

Account ids use letters, digits, `-`, and `_`, up to 32 characters.

If you added an account with `acm add` directly, run `acm setup` after signing in. It sets up artifact collection and limit handoff, which it skipped while you had only one account.

## Adding Codex accounts

The first `acm add --codex` registers your current `~/.codex` as the default account `cx1`. If your browser is signed in to a different ChatGPT account, open the login URL in a private window.

```bash
acm add --codex cx2              # creates ~/.codex-cx2
acm -a cx2 login --device-auth   # open the URL shown and enter the code
```

## Starting sessions

```bash
acm                      # asks which tool to open
acm claude               # Claude account with the most headroom
acm -c                   # without a tool name, arguments go to claude
acm codex                # Codex account with the most headroom
acm -a personal          # pick the account yourself; starts that account's tool
acm pick [codex]         # show which account would be picked without starting
acm resume               # continue a Claude session stopped by a limit on another account
acm codex resume <ID>    # open a Codex session from any Codex account
```

acm picks only among accounts of the same tool. Put `-a` and `--rr`, which picks round robin for this launch only, before everything else. For the account you can give its id, display name, email, or the part of the email before `@`. To skip acm, type `command claude` or `command codex`.

Starting sessions from IDEs and the menu bar app is covered in [Setup](docs/setup.md). How accounts are scored and how to continue a session that hit a limit are in [Account selection and usage](docs/selection.md).

## Collecting artifacts in one account

An artifact belongs to the account its session is attached to, so artifacts scatter across accounts as you move between them. With artifact collection on, sessions on other accounts hand their artifacts to a publisher session on the primary account. When you have two or more accounts, `acm setup` shows what the publisher session is allowed to do, asks you to pick the primary account, and turns collection on.

```bash
acm publisher on         # turn on; the publisher session starts when it is needed
acm publisher status     # whether it is on, the primary account, and the session state
acm publisher off        # turn off; each session publishes under its own account again
```

Pick the account you are signed in to on claude.ai in your browser as the primary account. Otherwise you cannot open the collected artifacts. Only Claude artifacts are collected for now. Collecting Codex Sites is on the [roadmap](docs/roadmap.md).

## Checking after a Claude Code update

acm depends on undocumented Claude Code behavior such as the output format of `/usage`. After you update Claude Code, run `acm doctor`. It reads every account for real and reports whether that behavior still matches. It exits with code 1 when something is off.

```bash
acm doctor              # check the Claude Code behavior acm relies on
acm upgrade             # git pull the installed repository and rerun install.sh
```

## Undoing and uninstalling

```bash
acm setup --undo           # revert the shell lines and the IDE plugin settings
./install.sh --uninstall   # also restore the statusline and remove the CLI and the app
```

Both keep the account folders and `~/.acm`. They hold login data, so deleting them is your call.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `acm setup` left the IDE plugin settings as a remaining step | Quit JetBrains IDEs and run `acm setup` again |
| It says it could not move the shared folder to `~/.acm/shared` | Quit all claude sessions and run `acm sync --fix` |
| `claude` or `codex` does not go through acm | The terminal was opened before setup. Open a new one or run `exec zsh -l` |
| New Session… in the menu bar app opens no window | The first time you click it, macOS asks whether ACM may control iTerm. Allow it |

## More docs

| Doc | Covers |
|---|---|
| [Setup](docs/setup.md) | What `acm setup` changes, the shell function, starting from IDEs |
| [Accounts](docs/accounts.md) | Account folder layout, the shared folder, login token refresh, Codex accounts |
| [Account selection and usage](docs/selection.md) | Selection rules and environment variables, usage collection, Ultra accounts, Codex usage |
| [Artifact collection and screen control](docs/publisher.md) | The publisher session and its scope, primary account headroom, screen control through Aside Browser |
| [Menu bar and widget](docs/app.md) | Per-tool account cards in the menu bar window, the floating widget |
| [Roadmap](docs/roadmap.md) | Deferred features and why they were deferred |

## Files

| Path | Contents |
|---|---|
| `bin/acm` | The CLI. Uses only the Python 3.9 standard library |
| `bin/acm-statusline` | Statusline wrapper. Records usage, then runs your original statusline |
| `app/` | SwiftUI sources of the menu bar app and `build.sh`. Built for macOS 14 or later on Apple silicon. It is ad-hoc signed, so it runs only on the Mac that built it |
| `docs/` | Detailed docs per feature and the logo `logo.svg` |
| `tests/` | Tests that run in a fake home folder. `python3 -m unittest discover -s tests` |
| `install.sh` | Install and uninstall |
| `~/.acm/` | State: `accounts.json`, usage per account, poll and session records, the publisher session folder. Kept at 0700 so only you can open it |

## License

Released under the MIT License. See `LICENSE`.
