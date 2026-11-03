# Platform support plan

acm runs on macOS only. This doc plans support for Linux, Claude Desktop, and Windows, in that order. For each one it lists what has to change, how to test it, and when it counts as done. None of this work has started. The code locations below were taken from `bin/acm`, `bin/acm-statusline`, and `install.sh` on 2026-11-03.

## The order follows cost and what blocks each step

Linux comes first because it costs the least. Claude Code on Linux keeps its token in `.credentials.json` inside the config folder, so each account folder already holds its own. acm uses only the Python standard library and POSIX calls, and two of the macOS-only spots already have a Linux branch. Linux also covers Windows users who run Claude Code inside WSL 2, before native Windows support exists.

Claude Desktop comes second, but it is blocked upstream. Reports say the Code tab of Claude Desktop does not follow `CLAUDE_CONFIG_DIR`, so acm has no way to start it on a picked account.[1] The step starts by checking whether that has changed. If it has not, the step stays blocked and Windows goes ahead without waiting.

Windows comes last because it changes the most. The shared folder is built from symbolic links, session lookup reads other processes, the statusline wrapper is a shell script, and the publisher session runs in tmux. Each of these needs a Windows version.

## Linux is mostly a matter of finding things in other places

### What already works

- `proc_info` reads a session's environment from `/proc/<pid>/environ`. On macOS it uses `sysctl`, and that branch only runs on macOS.
- `fd_path` reads the real path of an open file from `/proc/self/fd`. On macOS it uses `F_GETPATH`.
- Each account's Claude Code keeps `.credentials.json` in its own folder, such as `~/.claude-cl2`. acm never reads it.
- `bin/acm` needs only Python 3.9 and its standard library.

### What has to change

| Where | macOS today | Linux plan |
|---|---|---|
| `running_sessions` | Reads each session's working folder with `lsof -d cwd` | Read the link `/proc/<pid>/cwd`. Keep `lsof` on macOS |
| `running_sessions`, `claude_pids`, setup's IDE check | `ps -axo pid=,ppid=,uid=,etime=,comm=` | Check that procps `ps` accepts these options. If not, read `/proc/<pid>/stat` and `/proc/<pid>/status` directly. Check that `comm` shows `claude` for a native install, since Linux cuts it to 15 characters |
| `JETBRAINS_DIR`, `VSCODE_APP_SUPPORT` | `~/Library/Application Support` | `~/.config` for JetBrains, Code, Cursor, and Windsurf. Remote and WSL editors keep settings in `~/.vscode-server` instead, which needs its own check |
| `shell_rc` | `.zshrc`, or `.bash_profile` for bash because macOS Terminal opens a login shell | `.bashrc` for bash, since most Linux terminals open a non-login shell |
| claude and codex lookup | Falls back to `/opt/homebrew/bin` and `/usr/local/bin` | Add `~/.local/bin`, where the native installer puts claude, and `/usr/bin` |
| `setup_tmux`, publisher messages | Offers `brew install tmux` | Name the system package manager, such as `apt install tmux`, and do not run it. Installing system packages needs root |
| `install.sh` | Builds `/Applications/ACM.app`, quits it with `osascript`, suggests `brew install jq` | Skip the app and `osascript` on Linux as if `--no-app` were given. Suggest the package manager for jq |
| Setup's closing note | Mentions macOS asking to control iTerm | Show only on macOS |
| Limit notification | iTerm shows OSC 9 as a notification | Leave as is. Terminals that ignore OSC 9 show nothing, which is the current behavior in other macOS terminals too |
| `acm rm` help and docs | "keeps the folder and the keychain entry" | Say the token stays in the folder on Linux |

The menu bar app is not built for Linux. `acm status` shows the same accounts, and `acm status --json` gives the same data the app reads.

### How to test

1. Make the unit tests platform aware. Tests that fake `lsof` or `sysctl` output should fake `/proc` on Linux instead.
2. Add an `ubuntu-latest` job to `.github/workflows/check.yml`. It runs the syntax check and the unit tests, but not the Swift build. The comment in that file already marks the spot.
3. Run `install.sh --no-app` and `acm setup` in a fake home on Linux, the same way [AGENTS.md](../AGENTS.md) describes for macOS.
4. On a real Linux machine or VM, sign in to two Claude accounts and two Codex accounts. Run `acm doctor`, start sessions with `claude` and `codex` through the shell function, check `acm status`, and publish one artifact through the publisher session.

### Done when

- The ubuntu CI job passes.
- Step 4 above works end to end on a real Linux machine, and the result is noted with the date and versions in a footnote.
- The README says acm runs on macOS and Linux, and the Quick start names what to install on Linux.
- WSL 2 is tried once. If it works, the README says so. If it does not, this doc records what broke.

## Claude Desktop waits until the Code tab follows a config folder

The Code tab of Claude Desktop runs Claude Code sessions, but reports say it ignores `CLAUDE_CONFIG_DIR`.[1] acm picks an account by choosing the config folder a session starts with. It never swaps login tokens, so there is no workaround that keeps that rule.

### Check first

1. Read issue #30031 and the Claude Desktop release notes for news on config folders or multiple accounts.
2. Start Claude Desktop with `CLAUDE_CONFIG_DIR` set, for example with `open --env CLAUDE_CONFIG_DIR=$HOME/.claude-cl2 -a Claude`. Start a session in the Code tab and see which account and which `projects` folder it uses.

If neither shows a change, record the date and the Desktop version here and move on to Windows.

### If the Code tab follows the variable

- Add `acm desktop`, which picks a Claude account and starts Claude Desktop with that account's `CLAUDE_CONFIG_DIR`. Add the same choice to "New Session…" in the menu bar app.
- Desktop sessions get no statusline, so their usage comes only from the `/usage` poll. Check that the poll interval is short enough for an account used only from Desktop.
- Count Desktop sessions as running sessions. Check which process holds `CLAUDE_CONFIG_DIR` and whether `running_sessions` can tell it apart from the CLI.
- Only one Desktop app can run at a time, so a second account cannot run beside the first. Write down how switching works, or whether it needs a restart.

### Done when

A session started with `acm desktop` runs on the picked account, shares `~/.claude` with CLI sessions, and shows up in `acm status`.

## Windows starts with WSL and then goes native

### WSL 2 comes with Linux

Inside WSL 2, Claude Code and Codex are Linux programs, so the Linux step already covers them. The only Windows-specific work there is the editor case. VS Code with the WSL extension keeps settings in `~/.vscode-server`, and JetBrains IDEs on Windows keep settings on the Windows side. Setup should report these as remaining steps instead of guessing.

### Native Windows needs a new version of five parts

| Part | Today | Windows plan |
|---|---|---|
| Shared folder | 18 places create or read symbolic links from account folders to `~/.claude` and `~/.acm/shared` | Use directory junctions for folders, which need no admin rights. For single files, check whether Developer Mode symbolic links are acceptable, or change the layout so only folders are linked |
| Session lookup | `ps`, `lsof`, `sysctl`, and `/proc` read other processes' environment and working folder | Reading another process's environment on Windows needs `NtQueryInformationProcess` and `ReadProcessMemory` through `ctypes`. This is fragile, so first try recording the pid and account when acm starts a session, and only check that the pid is alive. Sessions started without acm then show with an unknown account |
| Statusline wrapper | `bin/acm-statusline` is a `/bin/sh` script that needs `jq` | Move it into Python as `acm statusline`, so one wrapper runs everywhere. This also drops the `jq` requirement on macOS and Linux. Measure the startup time first, because the statusline runs often |
| Shell function | `acm shell-init` writes a zsh and bash function | Write a PowerShell function and add it to `$PROFILE`. cmd is not supported |
| Publisher session | Runs claude inside a detached tmux session | Windows has no tmux. Leave artifact collection off on native Windows at first, and point users who need it to WSL 2 |

Smaller changes:

- `os.getuid` is used in four places. Two keep only this user's processes, one builds Claude Code's temp folder path `/tmp/claude-<uid>`, and one checks who owns a folder. Windows has no uid, so each needs its own answer: skip the process filter, find where Claude Code keeps temp files on Windows, and check the owner through the file's security info.
- `fcntl` is used in four places for file locks and in one for `F_GETPATH`. Use `msvcrt.locking` and `GetFinalPathNameByHandleW` instead.
- `install.sh` needs an `install.ps1` counterpart. State stays in `%USERPROFILE%\.acm`, and account folders stay as `%USERPROFILE%\.claude-<id>`.
- IDE settings live in `%APPDATA%\JetBrains` and `%APPDATA%\Code\User`.
- Check that `CLAUDE_CONFIG_DIR` and `CODEX_HOME` keep each account's sign-in separate on Windows, and that `claude -p /usage` and `codex app-server` behave the same there.
- No menu bar or tray app. `acm status` covers it.

### How to test

Add a `windows-latest` job to CI that runs the unit tests. Then, on a real Windows machine, repeat the Linux end-to-end test without the publisher session.

### Done when

- On native Windows, `claude` and `codex` typed in PowerShell start on the picked account, the accounts share one `~/.claude` or `~/.codex`, and `acm status` shows usage.
- The README says which features native Windows lacks and that WSL 2 has them.

## Footnotes

[1] anthropics/claude-code issue #30031 and its comments. It was still open as of the 2026-10-27 comment. https://github.com/anthropics/claude-code/issues/30031
