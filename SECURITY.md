# Security policy

Please report security vulnerabilities in acm privately through GitHub, not in public issues. If the details go public before a fix, everyone who uses acm is exposed through that gap in the meantime.

## Report privately

Open the Security tab of this repository and click "Report a vulnerability". The direct link is https://github.com/dodokim-lab/ai-account-manager/security/advisories/new . Only the maintainer and you can see the report.

These details help us confirm it quickly.
- Which part is affected, and what the gap lets someone do
- Steps to reproduce, with the commands you ran and the files you used
- The output of `acm version`, and your macOS version

## Only the latest main gets fixes

Fixes go into `main`. Past commits and tagged versions do not get separate fixed versions. Run `acm upgrade` to get the latest `main`.

## What is in scope

In scope:
- How `bin/acm` and `bin/acm-statusline` read and write the state folder `~/.acm`, the account folders, Claude Code and Codex settings files, and the shell lines in your rc file
- `install.sh` and `acm upgrade`
- The publisher session: staging files with `acm publisher check`, the `acm publisher guard` hook, and anything that lets another session make the publisher session do more than its scope in [docs/publisher.md](docs/publisher.md)
- The menu bar app under `app/`
- Any path that makes acm read, copy, or send login tokens, or lets another user on the same Mac read your account data

Out of scope:
- Claude Code, Codex CLI, and the services behind them. Report those to Anthropic or OpenAI
- Changes made by someone who already controls your user account on the computer, such as editing `~/.acm` or the installed scripts
- Whether running several accounts fits a provider's terms. That is up to each user, as the README notes

## When you will hear back

acm is maintained by one person, so these timelines are best effort.
- An acknowledgement within 7 days
- An assessment and a plan for a fix within 30 days
- After the fix is in `main`, a security advisory is published, with your name if you want it credited
