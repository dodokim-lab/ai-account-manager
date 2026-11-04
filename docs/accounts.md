# Accounts

This doc covers what each account folder keeps on its own and what it shares, and how acm handles login tokens. Codex accounts have their own section at the end. If you only need the commands to add accounts, the [guide](../GUIDE.md) is enough.

## You add an account, then sign in with it

An account id is the tool's short name plus a number. Claude accounts are `cl1`, `cl2`, and Codex accounts are `cx1`, `cx2`. Extra account folders are named after these ids too. A new number follows the count of that tool's accounts, so in an install that still has the old ids `acc1` and `acc2`, the third account becomes `cl3`.

The default account `cl1` is your current `~/.claude` and needs nothing. You add accounts from the second one on. Answer `acm setup` when it asks, or do it yourself as below.

```bash
acm add cl2                 # creates ~/.claude-cl2
acm -a cl2 auth login       # sign in with that account
acm label cl2 personal      # display name. Defaults to the part of the email before @
acm status                   # check sign-in and usage
```

`auth login` asks you to approve in the browser. If the browser is already signed in to claude.ai with another account, the approval goes to that account.[3] Then two acm accounts become the same Claude account. Splitting sessions between them does not raise your limit, and you spend the primary account's headroom under another name. So among acm accounts signed in to the same account, acm keeps only one in automatic picks. If the group includes the primary account, it keeps the primary account. When `acm status` or `acm setup` reports this, sign in again. Open the auth URL in a browser signed in to claude.ai with the right account, such as a private window. acm tells accounts apart by the account UUID in `.claude.json`, or by email if there is no UUID.

If different Claude accounts belong to one organization, `acm status` reports it. Each personal subscription has its own organization. Accounts in one organization may share an organization limit, as on Team or Enterprise. Anthropic has not confirmed reports that organization accounts share limits, so acm only reports this and does not leave the accounts out of picks.[4] It compares organizations by `organizationUuid` in `.claude.json`.

## An account folder holds only what must differ per account

An account folder keeps real files only for what must differ per account. Those are `.claude.json`, `.credentials.json`, `backups`, `jobs`, `telemetry`, `statsig`, and `daemon*`. Everything else is a link to `~/.claude`. acm copies the default account's `mcpServers`, personal settings, and project trust data into `.claude.json`. Personal settings are values such as auto-update, theme, and editor mode. Each sync overwrites them with the default account's values and removes values the default account lacks. So personal settings changed with `/config` on an extra account revert at the next launch. Change settings on the default account. If acm cannot read an extra account's `.claude.json`, a session on that account is writing it or the file is broken. acm then skips it instead of overwriting. Overwriting would erase the login data and project history. acm syncs the account this way every time it starts a session. Run `acm sync --fix` only when links get out of place.

## projects, skills, and hooks live in the shared folder

The real `projects`, `skills`, and `hooks` folders are in `~/.acm/shared`, and `~/.claude` holds links to them. They contain session history, auto memory, personal skills, and hook scripts, so sessions edit them often. Claude Code judges a write by the real path after following links. If that path is inside a `.claude` folder other than the session's own config folder, Claude Code treats it as a sensitive file and asks for confirmation even in auto mode.[1][2] So if the real folders were inside `~/.claude`, extra account sessions would ask for confirmation every time they edited these three folders. Allow rules and `--add-dir` do not lift this.[2]

Files such as `CLAUDE.md` and `settings.json` are not moved. `Write` and `Edit` refuse to write to a linked file and send the session back to write to the real path. If these files were moved too, edits on the default account would also need this round trip.[2]

After you first add an account, quit all claude sessions and run `acm sync --fix` once to move the folders. After upgrading to a version that moves more folders, run it once more the same way. If a claude process is running or `~/.acm/shared` already has the same name, acm does not move anything and reports it. Until the move is done, acm reports it in one line every time it starts a session.

## Only Claude Code handles login tokens

On macOS, login tokens are stored in the keychain under a different name for each account folder. On Linux, Claude Code keeps the token in `.credentials.json` inside each account folder. acm does not read them in either case. acm reads usage by having that account's Claude Code run `claude -p /usage`, so the token is used only inside Claude Code. A poll failure reason shown in the menu bar window is cleared when a session on that account records new usage through the statusline.

On an account with no session, the token expires after about 8 hours. Whether `/usage` refreshes an expired token by itself is unverified. So if `/usage` fails for a reason other than 429, acm starts `claude -p` once in the background on that account. This run turns off hooks, plugins, MCP, and tools, sends haiku one short request, and keeps no session history. The measured cost per run was 2,973 input tokens. Claude Code, not acm, refreshes the token as it normally does. It takes a lock to refresh, so nothing breaks even when a session on the same account is running.

When acm starts a refresh, the menu bar window shows "started a token refresh", and acm reads again after 90 seconds. acm starts a refresh at most once every 30 minutes. If polling fails again in between, the window shows an `acm -a <account> auth login` hint and the time of the next refresh. If the hint keeps showing, sign in again with that account.

If polling still fails after the refresh, acm treats the account as signed out. `acm status` and `acm setup` tell you to sign in again, and limit handoff does not send sessions to that account. Signing in again changes `.claude.json`, so acm stops treating the account as signed out right away, without waiting for the next poll.

## Remove unused accounts with rm

`acm rm <account>` removes an unused account from the list. It refuses if a session is running on that account, and the Claude default account `cl1` cannot be removed. If the removed account was the primary account that collects artifacts, acm clears that setting and collects in the first account from then on. It keeps the folder and the keychain entry and shows the commands to delete them for good.

## Codex accounts use ~/.codex as the root

The Codex default account `cx1` is your current `~/.codex`. Extra accounts start with `CODEX_HOME` set to `~/.codex-<id>`. Codex uses the folder that `CODEX_HOME` points to as its config folder. The first `acm add --codex` registers `cx1`. The first `acm codex` launch also registers it first if it is not registered yet.

```bash
acm add --codex cx2              # creates ~/.codex-cx2
acm -a cx2 login --device-auth   # sign in with that account
acm rm cx2                       # removes it from the list, keeps the folder and the login data
```

An extra account folder keeps real files only for what must differ per account.

- `auth.json` is the login data.
- `app-server-daemon` and `app-server-control` belong to the app server daemon started on that account. If they were shared, a session on another account would attach to that daemon and run as that account.
- `models_cache.json` is kept separate because the available models differ by plan.
- `installation_id`, `log`, `cache`, `tmp`, and `.tmp` are traces of that account's runs.

Everything else is a link to `~/.codex`. That includes the session history `sessions`, the state DB, `config.toml`, skills, hooks, and plugins, so every Codex account sees the same session list and settings. When Codex edits a linked `config.toml`, it follows the link and writes to the original file, so the link does not turn into a real file.[5] SQLite creates the WAL file next to the original DB the link points to, so sharing the DB through a link is safe.[6] So nothing needs to move to a shared folder as with Claude accounts.

Hook trust records are kept per account. Codex records a trusted hook in `config.toml` under a key such as `<hooks.json path>:session_start:0:0`. On an extra account this path is the unresolved `~/.codex-cx2/hooks.json`, so the same hook looks untrusted. The trust hash depends only on the hook's content, not on the path.[7] So when acm syncs an account's links, it copies the record under the `~/.codex` key to the extra account's key. This trusts only the same content you already trusted. If the hook content changes, both accounts ask again. If the account key already has a record, acm leaves it alone even if the hash differs. Writing the same table twice breaks `config.toml`, and Codex will not start.

With `login --device-auth`, you open the URL shown in a browser and enter the code. If the browser is signed in to a different ChatGPT account, the login binds to that account, so open it in a private window. Among acm accounts signed in to the same ChatGPT account, acm keeps only one in automatic picks, by the same rule as for Claude. To tell whether accounts are the same, acm compares both the email and the ChatGPT account ID, because members of a team workspace share an account ID.

If you already signed in to a folder with `CODEX_HOME=~/.codex-<id> codex login`, plain `acm add --codex` registers it as an account. This works when exactly one unregistered `~/.codex-*` folder has an `auth.json`. If Codex already created session history or a DB in that folder, acm moves them to `.acm-drift` and puts links to `~/.codex` in their place. When it moves a DB, it also moves the WAL file that holds records not yet merged.

acm does not read `auth.json`. It only checks that the file exists. It gets the email, plan, and ChatGPT account ID from `codex app-server` started on that account and writes them to `accounts.json`. The first `acm status` right after sign-in waits for this poll before showing them. When you sign out and `auth.json` disappears, acm clears these three values. If the token of an account left without sessions expires, the app-server poll refreshes it by itself.[8] Removing the Codex default account from the list leaves `~/.codex` untouched.

## Footnotes

[1] 2026-10-30. In a cl2 session, all 8 memory `Edit` and `Write` calls asked for confirmation with `reasonCode: safetyCheck`, while Bash and Read in the same session did not ask (session history `permissionDecision`). The docs do not say the exception is based on the session's own config folder. That is inferred from this measurement. Protected paths and link handling are documented in these pages. https://code.claude.com/docs/en/permission-modes.md#protected-paths , https://code.claude.com/docs/en/permissions.md#symlinks

[2] 2026-10-31, Claude Code 2.1.314. Writes were measured with auto mode `-p` sessions. The default account wrote to `~/.claude/state` and `~/.claude/skills` without asking. When cl2 wrote to the same folders through links, both were denied as sensitive files. Writes in `backups` in cl2's own config folder and in the moved `projects` passed, both inside and outside the memory folder. Allowing `~/.claude/**` writes with `--allowedTools` or adding `--add-dir ~/.claude` was still denied for the same reason. A write to a linked file was sent back with "it is a symbolic link" and a request to use the real path. Creating a new file inside a linked folder worked.

[3] 2026-11-03. In a browser signed in to claude.ai with the default account, approving `acm -a cl2 auth login` put the default account's email and account UUID into cl2's `.claude.json`.

[4] anthropics/claude-code issue #41886. It was closed automatically with no staff reply. https://github.com/anthropics/claude-code/issues/41886

[5] 2026-11-03, codex-cli 0.165.0. In a temp folder, `codex features enable` was run with a `CODEX_HOME` whose `config.toml` was a link. The link stayed in place, and the feature setting was written to the original file the link pointed to.

[6] 2026-11-03, SQLite 3.43.2. Writing to a WAL mode DB opened through a link created the `-wal` and `-shm` files only next to the original DB. Connections opened through the two paths read the same rows.

[7] 2026-11-03, codex-cli 0.165.0. Trust state was read with the app-server's `hooks/list`. On cx2 both hooks were untrusted. In a temp folder, writing the `~/.codex` hash under a different path key made them trusted. Changing the hook command turned them to modified.

[8] 2026-11-03, codex-cli 0.166.0. On cx2 left without sessions, `codex plugin list` failed with `token_expired`. Then the app-server poll of `acm poll --force` succeeded. After that, the same `codex plugin list` passed.
