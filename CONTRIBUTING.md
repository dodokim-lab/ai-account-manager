# Contributing

acm welcomes pull requests that fix bugs, clarify the docs, or make acm work with a new Claude Code or Codex CLI version. One maintainer reviews every pull request by hand, so it may take a few days. For a new feature or a large change, open an issue first so we can agree on the direction before you write the code. [docs/roadmap.md](docs/roadmap.md) lists features that were deferred and why.

Report security vulnerabilities privately as described in [SECURITY.md](SECURITY.md), not in a pull request or issue.

## Before you open a pull request

Run the same checks CI runs. They need macOS with Xcode command line tools.

```sh
sh -n install.sh && sh -n bin/acm-statusline && sh -n app/build.sh
python3 -m py_compile bin/acm
python3 -m unittest discover -s tests
swiftc -parse-as-library -swift-version 5 -target arm64-apple-macos14.0 -o /tmp/ACM app/Sources/*.swift
```

The tests run in a fake home folder with fake `claude` and `codex` commands, so they do not touch your accounts. To try an install by hand without touching your real setup, run `./install.sh --no-app` with `HOME` set to an empty folder. `app/build.sh` always installs into `/Applications/ACM.app`, so it replaces the app you use.

In the pull request description, say what you changed and why in a line or two. If the change depends on how Claude Code or Codex CLI behaves, add the version you checked it with.

## Keep these the same

- `bin/acm` uses only the Python 3.9 standard library. Do not add packages.
- Code, comments, CLI messages, docs, and commit messages are in English. `README.ko.md` is the only Korean file. If you change `README.md`, change it too, or say in the pull request that it needs a Korean update.
- acm never reads, copies, or sends login tokens. Usage comes from the statusline, `claude -p /usage`, and `codex app-server`. Pull requests that read the keychain or call private APIs with a token are not accepted.
- When behavior changes, update `acm help`, the comments at the top of `install.sh`, the `acm setup` questions, and the docs in the same pull request.
- Docs state what was observed with a footnote that gives the date and the Claude Code or Codex version, like the existing ones in `docs/`.
- Tests, examples, and docs use made-up accounts at reserved domains such as `example.com` or `.test`. Do not include real emails, account names, tokens, or company names. This is a public repository, and a merged commit is hard to remove from the history.

## Commit messages

Write the subject as a plain sentence that says what the change does, with no prefix, for example "Keep publisher status working without tmux". Keep unrelated changes in separate commits.
