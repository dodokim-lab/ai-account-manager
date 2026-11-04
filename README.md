# ai-account-manager

English | [한국어](README.ko.md)

If you pay for more than one Claude Code or Codex subscription, the accounts do not work together. A session runs on whichever account you signed in to last, so one account hits its limit while another sits unused. Each account also keeps its own memory, history, settings, and skills, so moving to another account means starting from an empty context.

acm is a launcher that makes those accounts work as one. Keep typing `claude` and `codex` as usual. acm starts each session on the account of that tool with the most headroom left, and every account reads the same `~/.claude` or `~/.codex`, so your context comes along.

![On the left, typing claude and codex in a terminal prints the account acm picked. On the right, the acm menu bar window lists three Claude accounts and two Codex accounts with 5-hour and weekly usage gauges, and the picked account of each tool is outlined. Below the terminal, the Claude accounts cl1 to cl3 point to one ~/.claude and the Codex accounts cx1 and cx2 to one ~/.codex.](docs/readme/hero.svg)

## What acm does

acm picks an account each time a session starts. It weighs the 5-hour headroom against how fast the weekly limit is being used, so an account that would lose unused quota at its reset goes first. Accounts close to a limit are left out, and among accounts with close scores, the one running fewer sessions wins. The rules are in [Account selection and usage](docs/selection.md).

All accounts of a tool share one context. Memory, history, settings, and skills live in one `~/.claude` or `~/.codex`, and each account folder links to it. A Claude session stopped by a limit continues on another account with `acm resume`, and `acm codex resume` opens a Codex session from any Codex account.

The menu bar window shows every account's 5-hour and weekly usage with its reset time, and a floating widget keeps the same numbers on screen. In a terminal, `acm status` prints them. If the Antigravity CLI `agy` is installed, its weekly usage shows there too, though acm does not start or pick it.

Claude artifacts can be collected in one account. An artifact belongs to the account that published it, and only that account can edit or delete it. With artifact collection on, sessions on other accounts hand their artifacts to a publisher session on the primary account, so every artifact is managed from one place.

acm never reads or moves login tokens. Each account signs in through Claude Code's or Codex's own login flow. Usage comes from the statusline and from `claude -p /usage` and `codex app-server` run under that account.

## How acm differs from similar tools

Other tools solve parts of the same problem. The descriptions follow each project's docs as of November 2026.

| Tool | What it does | How acm differs |
|---|---|---|
| [claude-swap](https://github.com/realiti4/claude-swap) | Switches the signed-in Claude Code account by swapping its stored credentials, and can rotate automatically when usage passes a threshold. Chat history stays per account unless you opt in. Runs on macOS, Linux, and Windows | acm never moves credentials. Every account stays signed in to its own folder, history is shared from the start, and Codex accounts are covered too. acm does not run on Windows yet |
| [CCS account pools](https://docs.ccs.kaitran.ca/features/pool) | Puts several Claude accounts behind a local proxy and uses one account fully before moving to the next | acm starts each session directly on one account with no proxy, and spreads usage by headroom instead of using accounts in order |
| [claude-limits](https://github.com/figueiredouc/claude-limits) | Shows Claude Code usage in the macOS menu bar by calling the usage API with Claude Code's token | acm shows every Claude and Codex account in one window and reads usage without touching the token |

## Quick start

acm runs on macOS and Linux. Linux support is new and has not yet been tried with real signed-in accounts. Windows is planned in [Platform support plan](docs/platforms.md). You need `python3`, `jq`, and `claude`, plus `codex` for Codex accounts. The menu bar app is macOS only. It needs `swiftc` and runs on Apple silicon with macOS 14 or later.

1. Quit JetBrains IDEs and any running claude sessions. If they are running, setup leaves the IDE plugin settings and the shared folder as remaining steps.
2. Clone the repository and run `install.sh`. It installs the CLI, the statusline wrapper, and the menu bar app, then runs `acm setup`.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ./install.sh
   ```

3. When setup asks whether to add an account, add one and sign in with it. Your current `~/.claude` becomes the first account `cl1` as it is.
4. Open a new terminal and type `claude`. It starts on the Claude account with the most headroom.
5. Run `acm status` to check sign-in and usage for each account.

## Using acm

The [guide](GUIDE.md) covers adding Claude and Codex accounts, starting sessions, collecting artifacts, checking after a Claude Code update, uninstalling, and troubleshooting. Each feature also has a detailed doc.

| Doc | Covers |
|---|---|
| [Setup](docs/setup.md) | What `acm setup` changes, the shell function, starting from IDEs |
| [Accounts](docs/accounts.md) | Account folder layout, the shared folder, login token refresh, Codex accounts |
| [Account selection and usage](docs/selection.md) | Selection rules and environment variables, usage collection, Ultra accounts, Codex usage, Antigravity usage |
| [Artifact collection and screen control](docs/publisher.md) | The publisher session and its scope, primary account headroom, screen control through Aside Browser |
| [Menu bar and widget](docs/app.md) | Per-tool account cards in the menu bar window, the floating widget |
| [Platform support plan](docs/platforms.md) | What Linux, Claude Desktop, and Windows support needs, in that order |
| [Roadmap](docs/roadmap.md) | Deferred features and why they were deferred |

## Use it only with accounts you own

acm is an unofficial tool and is not affiliated with Anthropic or OpenAI. Anthropic notes that [advertised usage limits assume ordinary, individual usage](https://code.claude.com/docs/en/legal-and-compliance). acm is built for one person who holds several subscriptions, not for sharing accounts between people.

## Contributing and reporting vulnerabilities

See [CONTRIBUTING.md](CONTRIBUTING.md) for the checks to run and the rules to keep before you open a pull request. Report security vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a public issue.

## License

Released under the MIT License. See `LICENSE`.
