# Working in this repository

These are the rules for coding agents and people changing acm. [CONTRIBUTING.md](CONTRIBUTING.md) has the checks to run before a pull request and the rules every change keeps, such as English only, the Python standard library only, and no login tokens. This file adds what is easy to get wrong while working: acm installs into real places on the Mac, so a careless test can break the setup you are using.

## Test without touching the real setup

acm writes to your home folder, your shell rc file, Claude Code settings, and `/Applications`. Try changes in a fake home, not on your own install.

- The unit tests already run in a temporary home with fake `claude` and `codex` commands. Run `python3 -m unittest discover -s tests` first.
- To try `install.sh` and `acm setup` by hand, run them under `env -i` with `HOME` set to an empty folder. Put a fake `claude` that only answers `--version` first on `PATH`, and set `TMUX_TMPDIR` inside the fake home so a publisher session cannot land in your own tmux server. `ACM_SETUP=--yes` takes the defaults without asking. For a fake `codex`, reuse `FAKE_CODEX` from `tests/test_acm.py`.
- Always install with `./install.sh --no-app` there. `app/build.sh` writes to the fixed path `/Applications/ACM.app`, so building the app replaces the one you use.
- Never run `./install.sh --uninstall` in a fake home. It quits the running ACM app and deletes `/Applications/ACM.app` whatever `HOME` is. Delete the fake home folder instead.
- To try `acm upgrade`, clone this repository into a temporary folder, reset the clone to an older commit, install from it, and run `acm upgrade`. The clone's origin is your local repository, so the pull behaves like a real one.
- `ps` still sees your real processes in a fake home, so session counts there include your own sessions.

Do not edit your real `~/.claude/settings.json`, `~/.codex`, or `~/.acm` to experiment. Do not read, print, or copy login tokens, keychain items, or credential files, even while debugging.

## Claude Code and Codex internals change without notice

acm relies on behavior that is not documented, such as the output of `/usage`, the statusline input, and session records. Check a claim against the installed version before you build on it.

- After a Claude Code update, run `acm doctor`. If it passes, raise `VERIFIED_CLAUDE` in `bin/acm` to that version.
- The publisher session's model is pinned in `PUBLISHER_MODEL`. Change it when the model is retired or a newer one of the same family comes out.
- When a doc states observed behavior, add a footnote with the date and the Claude Code or Codex version, like the footnotes already in `docs/`.

## The publisher session is a security boundary

Any session can send messages to the publisher session, so its limits are enforced in code, not only by its prompt. The sections of [docs/publisher.md](docs/publisher.md) on staging and the hook list every rule. When you change `acm publisher check`, the `acm publisher guard` hook, or the session rules, keep each of those rules, add a test for each new case, and update that doc in the same commit.

Both checks are allow lists. A file, tool, or input shape they do not recognize is rejected, not passed, because a new shape may carry a local path. Keep it that way when Claude Code adds a new field or tool.
