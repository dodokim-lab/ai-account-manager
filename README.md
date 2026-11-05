# ai-account-manager

English | [한국어](README.ko.md)

With more than one Claude Code or Codex subscription, one account hits its limit while another sits unused. Each account also keeps its own context.

acm is a launcher that makes those accounts work as one. Keep typing `claude` and `codex`. Each session starts on the account with the most headroom, and every account shares one context. It also runs behind [Orca](https://github.com/stablyai/orca).

![On the left, typing claude and codex in a terminal prints the account acm picked. On the right, the acm menu bar window lists three Claude accounts and two Codex accounts with 5-hour and weekly usage gauges, and the picked account of each tool is outlined. Below the terminal, the Claude accounts cl1 to cl3 point to one ~/.claude and the Codex accounts cx1 and cx2 to one ~/.codex.](docs/readme/hero.svg)

## What sets acm apart

- Picks the account for each session, with nothing to switch
- Shares memory, history, settings, and skills across every account
- Never reads or moves a login token
- Handles Claude Code and Codex in one tool
- Collects Claude artifacts in one account
- Runs [behind Orca](docs/orca.md), so the sessions Orca starts get the same pick and context

[How acm differs from similar tools](docs/comparison.md) has the details and a comparison with other tools.

## Quick start

acm runs on macOS and Linux, and Linux support is new. It needs `python3`, `jq`, and `claude`. Codex accounts need `codex`, and the macOS menu bar app needs `swiftc`. [Install](GUIDE.md#install) in the guide has the details.

1. Quit JetBrains IDEs and running claude sessions. While they run, setup puts off some settings.
2. Clone the repository and run `install.sh`. It installs acm and runs `acm setup`.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ./install.sh
   ```

3. Add an account when setup asks, and sign in. Your current `~/.claude` becomes the first account, `cl1`.
4. Open a new terminal and type `claude`.
5. Run `acm status` to see each account's sign-in and usage.

## Using acm

The [guide](GUIDE.md) covers accounts, sessions, artifact collection, uninstalling, and troubleshooting. It also lists the docs for each feature.

## Use it only with accounts you own

acm is unofficial and not affiliated with Anthropic or OpenAI. Anthropic notes that [advertised usage limits assume ordinary, individual usage](https://code.claude.com/docs/en/legal-and-compliance), so acm is for one person's own accounts, not for sharing accounts between people.

## Contributing and reporting vulnerabilities

Read [CONTRIBUTING.md](CONTRIBUTING.md) before you open a pull request. Report security vulnerabilities privately as [SECURITY.md](SECURITY.md) describes.

## License

MIT. See `LICENSE`.
