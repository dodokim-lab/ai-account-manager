# ai-account-manager

English | [한국어](README.ko.md)

If you pay for more than one Claude Code or Codex subscription, the accounts do not work together. A session runs on whichever account you signed in to last, so one account hits its limit while another sits unused. Each account also keeps its own memory, history, settings, and skills, so moving to another account means starting from an empty context.

acm is a launcher that makes those accounts work as one. Keep typing `claude` and `codex` as usual. acm starts each session on the account of that tool with the most headroom left, and every account reads the same `~/.claude` or `~/.codex`, so your context comes along. It also runs behind [Orca](https://github.com/stablyai/orca), so the sessions Orca starts on your desktop and shows on your phone get the same pick and the same context.

![On the left, typing claude and codex in a terminal prints the account acm picked. On the right, the acm menu bar window lists three Claude accounts and two Codex accounts with 5-hour and weekly usage gauges, and the picked account of each tool is outlined. Below the terminal, the Claude accounts cl1 to cl3 point to one ~/.claude and the Codex accounts cx1 and cx2 to one ~/.codex.](docs/readme/hero.svg)

## What sets acm apart

- The account is picked for each session. A new session starts on the account with the most headroom, with nothing to switch.
- Every account shares one context. Memory, history, settings, and skills are one `~/.claude` or `~/.codex`.
- Login tokens are never read or moved. Each account stays signed in through the tool's own login.
- Claude Code and Codex are handled by one tool, with one status table and one menu bar window.
- Claude artifacts are collected in one account, so they are edited and deleted from one place.
- It runs behind Orca. Orca's own account switcher changes the active account when you click it. Behind Orca, acm picks the account for each session, and the accounts share one context.

[How acm differs from similar tools](docs/comparison.md) has the details and a comparison with claude-swap, CCS account pools, claude-limits, and Orca's account switcher. [Using acm with Orca](docs/orca.md) has the Orca setup.

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

The [guide](GUIDE.md) covers adding Claude and Codex accounts, starting sessions, collecting artifacts, checking after a Claude Code update, uninstalling, and troubleshooting. It ends with the list of detailed docs for each feature.

## Use it only with accounts you own

acm is an unofficial tool and is not affiliated with Anthropic or OpenAI. Anthropic notes that [advertised usage limits assume ordinary, individual usage](https://code.claude.com/docs/en/legal-and-compliance). acm is built for one person who holds several subscriptions, not for sharing accounts between people.

## Contributing and reporting vulnerabilities

See [CONTRIBUTING.md](CONTRIBUTING.md) for the checks to run and the rules to keep before you open a pull request. Report security vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a public issue.

## License

Released under the MIT License. See `LICENSE`.
