# How acm differs from similar tools

This doc lists what sets acm apart and compares it with the tools that solve parts of the same problem. Read it to decide whether acm fits the way you use your accounts.

## What sets acm apart

Other tools switch the signed-in account, pool accounts behind a proxy, or show usage. acm differs from them in six ways.

| What sets acm apart | How |
|---|---|
| The account is picked for each session, with nothing to switch | Each new session starts on the account with the most headroom, so usage spreads across accounts and does not fill one first. acm weighs the 5-hour headroom against how fast the weekly limit is being used, so an account that would lose unused quota at its reset goes first. Accounts close to a limit are left out, and among accounts with close scores, the one running fewer sessions wins. The rules are in [Account selection and usage](selection.md) |
| Every account shares one context | Memory, history, settings, and skills live in one `~/.claude` or `~/.codex`, and each account folder links to it. A Claude session stopped by a limit moves to another account in the same terminal, and `acm codex resume` opens a Codex session from any Codex account. The folders are in [Accounts](accounts.md) |
| Login tokens are never read or moved | Each account signs in through Claude Code's or Codex's own login flow and stays signed in to its own folder. Usage comes from the statusline and from `claude -p /usage` and `codex app-server` run under that account. No credential is swapped or copied, and there is no proxy |
| Claude Code and Codex in one tool | The pick, `acm status`, and the menu bar window cover both tools. Accounts are picked among those of the same tool |
| Claude artifacts are collected in one account | An artifact belongs to the account that published it, and only that account can edit or delete it. With artifact collection on, sessions on other accounts hand their artifacts to a publisher session on the primary account, so every artifact is managed from one place. See [Artifact collection and screen control](publisher.md) |
| It runs behind Orca | [Orca](https://github.com/stablyai/orca) starts sessions in git worktrees and shows them on a phone. Its own account switcher changes the active account when you click it. Behind Orca, acm gives each session the pick and the shared context, and the session's statusline shows every Claude account's usage. See [Using acm with Orca](orca.md) |

The menu bar window shows every account's 5-hour and weekly usage with its reset time, and a floating widget keeps the same numbers on screen. In a terminal, `acm status` prints them. If the Antigravity CLI `agy` is installed, its weekly usage shows there too, though acm does not start or pick it. See [Menu bar and widget](app.md).

## Compared with each tool

Other tools solve parts of the same problem. The descriptions follow each project's docs as of November 2026.

| Tool | What it does | How acm differs |
|---|---|---|
| [claude-swap](https://github.com/realiti4/claude-swap) | Switches the signed-in Claude Code account by swapping its stored credentials, and can rotate automatically when usage passes a threshold. Chat history stays per account unless you opt in. Runs on macOS, Linux, and Windows | acm never moves credentials. Every account stays signed in to its own folder, history is shared from the start, and Codex accounts are covered too. acm does not run on Windows yet |
| [CCS account pools](https://docs.ccs.kaitran.ca/features/pool) | Puts several Claude accounts behind a local proxy and uses one account fully before moving to the next | acm starts each session directly on one account with no proxy, and spreads usage by headroom instead of using accounts in order |
| [claude-limits](https://github.com/figueiredouc/claude-limits) | Shows Claude Code usage in the macOS menu bar by calling the usage API with Claude Code's token | acm shows every Claude and Codex account in one window and reads usage without touching the token |
| [Orca's account switcher](https://github.com/stablyai/orca/blob/main/docs/site/content/docs/agents/codex-hot-swap.mdx) | Keeps several Claude Code and Codex accounts in the Orca desktop app and makes one of them active with a click. New sessions use the active account, and each extra account runs in an isolated home. Usage is read with each tool's login | acm picks an account for each session by headroom with no click, shares one context between the accounts, and reads usage without the token. acm runs behind Orca, so the two are used together |
