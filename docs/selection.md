# Account selection and usage

This doc covers which account acm picks for each session and where it collects the usage behind that choice. Read it when you change thresholds or a pick is not what you expected. Picks and usage for Codex accounts have their own section at the end.

## Quick start

1. Run `acm poll --force` to read usage for every account now.
2. Run `acm status` to see each account's usage and per-model weekly limits.
3. Run `acm pick` to see the account it would pick and its score. To start with a different model, add the model, as in `acm pick --model fable`.

## acm picks the account with the highest score

The default selection mode `usage` scores each account and picks the highest. The score is the 5h headroom times the weekly pace ratio. For an account with no 5h limit, the 5h part counts as 100. The weekly pace ratio is the remaining weekly headroom divided by the fraction of time left until the reset. A ratio of 1 means enough is left to use at an even pace until the reset.

An account with a lot left close to its reset gets a ratio above 1 and is used first. That share is lost if it is not used before the reset. An account at Week 70% that resets in two hours is used before an account at Week 40% with six days left. Even right before a reset, the ratio counts at most 10 times. An account that used a lot ahead of pace gets a ratio below 1 and moves back.

Among accounts within 5 points of the top score, acm picks the one with fewer running sessions. If the session counts are equal too, it picks the higher score. Accounts at 5h usage of 95% or more, or Week usage of 98% or more, are left out of picks. If every account is left out, acm compares what is really left up to 100% instead, picks the account with the most, and warns. An account that Codex reports it cannot use now, or one already at 100%, is picked only when no account has anything left. Then acm picks the one whose limit resets first, so a session started there works once that window resets. `acm pick` shows the picked account like `Week 3% · score 124 · running 4`. Running sessions count only top-level claude processes started by your user. The account is told by that process's `CLAUDE_CONFIG_DIR`. acm reads environment variables from the kernel, separate from the arguments, instead of from `ps` output. So a `KEY=value` inside an argument does not confuse it.

`acm mode rr` switches to round robin, which picks in turn regardless of usage. Environment variables change the thresholds.

| Environment variable | Default | Meaning |
|---|---|---|
| `ACM_FIVE_HOUR_CAP` | 95 | Leave an account out of picks at this 5h usage or more |
| `ACM_SEVEN_DAY_CAP` | 98 | Leave an account out of picks at this Week usage or per-model weekly usage or more |
| `ACM_USAGE_BAND` | 5 | Within this many points of the top score, pick the account with fewer running sessions |
| `ACM_POLL_INTERVAL` | 300 | How often to read usage for each account, in seconds. Codex accounts use it too |
| `ACM_RESERVE_FIVE_HOUR_CAP` | 70 | 5h usage at which the primary account leaves automatic picks |
| `ACM_RESERVE_SEVEN_DAY_CAP` | 85 | Week usage at which the primary account leaves automatic picks |

The separate rules for the primary account are in [Artifact collection and screen control](publisher.md).

## A per-model weekly limit counts only for sessions on that model

Besides Week, `/usage` lists weekly limits that apply to one model only, such as `Current week (Fable)` or `Current week (Sonnet only)`. acm guesses the model this session will use and checks that model's limit along with Week. The tighter of the two sets the weekly pace ratio. If that limit is at 98% or more, the account is left out of picks. Limits for other models are only shown.

acm guesses the model in the same order Claude Code uses to choose it.

- `--model` passed as in `acm --model fable`
- The environment variable `ANTHROPIC_MODEL`
- `model` in `.claude/settings.local.json` and `.claude/settings.json` in the working folder, then in `~/.claude/settings.json`
- If none of these is set, the model of the session the statusline saw last

A model changed with `/model` inside a session cannot be known at launch. The last line of `acm status` shows which model acm compares against now.

## acm collects usage from the statusline and /usage

For an account with a running session, Claude Code passes `rate_limits` to the statusline, and `acm-statusline` writes it to `~/.acm/usage/<account>.json`. For every signed-in account, acm runs `claude -p /usage` in the background with that account's Claude Code every 5 minutes and writes the result to `~/.acm/poll/<account>.json`. This command does not call a model, so it used 0 input and 0 output tokens and cost $0. Each run took 3.8 seconds.[1] For each window, acm uses the more recent value. Per-model weekly limits come only from `/usage`.

Picks do not wait for polls. When you start a session or the menu bar app asks for status and an account is due for a poll, acm starts `acm poll` in the background and picks right away with the values it has. An account with no session does not gain usage unless it is used outside this Mac. So picking with values a few minutes old gives the same result.

If `/usage` fails, acm waits 7 minutes 30 seconds. Each further failure multiplies the wait by 1.5, up to 30 minutes. A failure other than 429 may be an expired token, so acm starts the token refresh described in [Accounts](accounts.md). If another usage tool calls the same usage API often, the two share its request limit and you get 429s. Keep only one such tool on.[2] `/usage` output is text for people, so acm cannot read it if the format changes. Run `acm doctor` after you update Claude Code.

## The statusline tag lists every Claude account's usage

`acm-statusline` puts a tag with the account's label in front of your statusline. With two or more Claude accounts, the tag also lists the usage of each one, so any session shows where the other accounts stand.

```
[work · cl1 62% · cl2 5/66%] <your statusline>
```

One number is the weekly usage. Two numbers are 5h and Week. A `?` after the number means the newest record of that account is over an hour old. The numbers follow the same rules as `acm status`: the more recent of the statusline record and the `/usage` poll wins for each window, a window past its reset counts as 0, and a 5h window not seen for a day is left out. Per-model weekly limits and Codex accounts are not in the tag. The list adds about 0.1 seconds to each statusline run.[14]

`acm statusline-usage off` leaves only the label, and `acm statusline-usage on` brings the list back.

## A verified Ultra account shows no 5h limit

A verified Ultra account has no 5-hour limit, so acm treats its 5h as no limit, not as 0%. When the Max 20x plan became Ultra on 2026-10-30, Anthropic started verifying Ultra accounts automatically from account and billing history and removed the 5-hour limit for verified accounts.[3] If Settings > Usage and the `/usage` output have no Current session line, the account is verified.[4]

If neither the statusline nor `/usage` has shown a 5h window for more than a day, acm treats the account as having no 5-hour limit. Accounts with a limit also lose 5h from the statusline input when the window resets. So one missing window does not mean no limit. acm reads a window past its reset time as 0%.[5]

It is unverified whether `/usage` shows the 5h line for an account with a limit that has not been used for more than a day. Even if it does not, 5h usage is 0% during that time, so picks stay nearly the same. For accounts with no limit, the pick exclusion and the primary account reserve thresholds also look only at Week. How the display leaves the 5h spot empty is in [Menu bar and widget](app.md).

## A session that hits a limit continues on another account with acm resume

When a session stops at a limit, the `StopFailure` hook records it in `~/.acm/limited/` and suggests `acm resume` in an iTerm notification. Hook output does not reach the session, so acm cannot move the session for you.[6] Instead, close that session and type `acm resume` in any terminal. It reopens the most recently limited session on another account. Session history is in the shared folder that every account uses, so the context carries over.[7] `acm setup` adds the hook to `~/.claude/settings.json` with the `rate_limit` matcher.

```bash
acm resume                # the most recent session stopped by a limit, on another account
acm resume 9e8ce742       # pick by session ID. For sessions with a limit record, a prefix is enough
acm resume -a cl1        # choose the account to continue on
```

acm picks the account to continue on with the same score as a new session, but skips the accounts below.

- The limited account itself, and acm accounts signed in to the same Claude account as it
- Accounts near a limit
- The primary account, if it is past the reserve thresholds of 5h 70% or Week 85%
- Accounts signed out because polling failed and still failed after a token refresh

For a new session, acm starts on an account near its limit even when every account is blocked. Limit handoff does not. If there is nowhere to go, it starts nothing and reports each account's usage and reset time. A continued session that stops again right away is no use. The primary account stops at 85% to keep Week 15% for publishing artifacts. Primary account sessions started before 85% rarely use up the remaining 15%, so acm does not tell you to move them ahead of time.

When you hit the weekly limit, Claude Code asks you to choose one of three options: stop and wait, continue when the limit resets, or switch to usage credits. To continue the session, choose the first and close it. The third is billed separately, outside your subscription.[8]

If the other account is in a different organization, the continued session cannot use its earlier thinking. Claude Code shows "Claude can't use thinking from another organization". The next response is slower and uses more tokens because it rereads the session. The thinking is not deleted, so reopening on the original account uses it again.[7] The conversation cache is also per account, so it is rebuilt from scratch.[9] Still, you choose when to continue, so the session does not slow down suddenly in the middle.

`acm resume` changes to the folder where the session was opened and starts `claude --resume`. If the same session is still open, it does not start, because the histories would mix. If the model answered in a session more than 2 minutes after the limit, acm assumes it continued on that account after the reset and drops it from the list to continue. A change to the history alone does not count, because closing a session writes to it too, and a limit message is not an answer.[15] So a session closed long after it stopped can still be continued. If there are sessions not yet continued, `acm status` reports how many.

## Codex picks among Codex accounts with the same score

acm picks only among accounts of the same tool. `acm codex` picks among Codex accounts. `acm claude` and `acm` without a tool name pick among Claude accounts. The score, the exclusion thresholds, and the session count rule are the same as for Claude. Round robin also remembers the last account per tool. The primary account reserve exists for artifact publishing, so Codex has none. `acm pick codex` previews the account it would pick.

acm polls Codex usage every 5 minutes by starting `codex app-server` with that account's `CODEX_HOME`. It sends `account/read` and `account/rateLimits/read` over JSON-RPC and shuts the server down as soon as it gets the answers. It does not call a model, and each run took 0.5 to 2.0 seconds.[10] There is no other source such as the statusline, so acm uses only these poll values. On failure, it waits with the same intervals as for Claude, then reads again.

Windows differ by plan. A free plan account returned only one 30-day window.[10] acm puts a window of 5 hours or less in the 5h spot, and the most used of the longer windows in the Week spot. The other long windows also count toward the score, and the pace ratio is measured against each window's own length. For a 30-day window, the time left until reset is compared with 30 days. The display and `acm status` name this window by its length, as in `30d 100%`. A Plus account returned a 5-hour window and a 7-day window, which went into the 5h and Week spots.[11]

If Codex reports that the account cannot be used right now, acm leaves it out of picks regardless of usage. This is when `ordinaryUsageAllowed` in the response is false. Once the reset time of the window seen then passes, acm compares the account again. If the response has limit entries other than `codex`, `acm status` shows them but picks do not use them.

Running sessions count top-level `codex` processes started by your user. The account is told by that process's `CODEX_HOME`. A process without `CODEX_HOME` belongs to the default account. The app server daemon that Codex keeps in the background is not a session, so it is not counted. This was verified with codex installed by Homebrew. With an npm install, where the process name shows as `node`, sessions may not be counted.

`acm resume` continues only Claude sessions. Codex session history is shared by every account. Close the limited session and type `acm codex resume <session ID>`, and it opens on the account with the most headroom. Whether the earlier reasoning history carries over when continuing on another account is unverified.

## Antigravity usage is shown but never picked

The Antigravity CLI `agy` can hold only one account. It has no environment variable to change its config folder, and it kept using `~/.gemini` even with `GEMINI_DIR` set. Changing `HOME` requires a new sign-in, and the login data goes into a single `antigravity` entry in the macOS keychain.[12] So acm does not start agy, split it into accounts, or pick for it. It only shows agy's usage next to the other tools.

When `agy` is installed, acm reads `agy -p /usage --output-format json` every 5 minutes. The response lists groups of models that share a weekly limit, such as Gemini and Claude and GPT, with the remaining fraction and the reset time of each. acm shows the used percentage per group in the menu bar window and in `acm status`. It does not call a model, and each run took 4 to 7 seconds.[13] Nothing shows until the first read succeeds.

Signed out, agy prints a sign-in URL, opens it in the browser with the `open` command it finds on PATH, and waits.[13] A background poll must not open a browser, so acm puts an `open` and an `xdg-open` that do nothing in `~/.acm/agy-shim` first on PATH. It stops agy as soon as the sign-in message appears and tries again after 6 hours. Run `agy` once yourself to sign in.

## Footnotes

[1] 2026-11-02, Claude Code 2.1.316. On two accounts, `claude -p "/usage" --output-format json` reported `usage` tokens of 0 and `total_cost_usd` of 0. The output format was checked in the `/usage` code of the same version.

[2] 2026-10-30. Removing a menu bar plugin that called the same API every 2 minutes stopped the 429s on the default account.

[3] Anthropic help article "What is the Ultra plan?" https://support.claude.com/en/articles/17728952-what-is-the-ultra-plan

[4] On 2026-11-01, the usage API response for the default account had `five_hour` as null. On 2026-11-02, the `/usage` output of both accounts had no Current session line.

[5] The Claude Code statusline docs say "Claude Code drops a window once its resets_at time passes". https://code.claude.com/docs/en/statusline

[6] The `StopFailure` section of the Claude Code hooks docs. The input has `session_id`, `cwd`, `transcript_path`, and `error`, and the output is not used except for `terminalSequence`. https://code.claude.com/docs/en/hooks

[7] 2026-11-03, Claude Code 2.1.316. A haiku session on the default account was told to remember a code word, then recorded as limited. `acm resume` refused while the session was open. After the session was closed, `acm resume` picked the second account and opened it there. Asked for the code word there, it answered correctly, and the other-organization thinking notice appeared before the answer.

[8] 2026-11-03, Claude Code 2.1.316. Only one session on the second account had `ANTHROPIC_BASE_URL` pointed at a local fake server. The fake server answered with a `rate_limit_error` 429 and a weekly limit `rejected` header. The session showed "You've hit your weekly limit" and three options, and the hook left a record in `~/.acm/limited/`. From the record, `acm resume` reopened the session on the default account. It ran inside tmux, so the iTerm notification was not seen. Whether a real limit behaves the same is unverified.

[9] Other tools that switch accounts mid-session also say they rebuild the conversation cache on the first request after the switch. See the Limitations section of the claude-swap README and the CCS Account Pools docs. https://github.com/realiti4/claude-swap , https://docs.ccs.kaitran.ca/features/pool

[10] 2026-11-03, codex-cli 0.165.0. On a free plan default account, `initialize` through the `account/rateLimits/read` response took 0.5 to 2.0 seconds. In the response, `primary` had `windowDurationMins` 43200 and `usedPercent` 100, `secondary` was null, and `ordinaryUsageAllowed` was false.

[11] 2026-11-03, codex-cli 0.166.0. On an account upgraded from free to Plus, `acm status` showed 5h and Week. The 5h reset was five hours away, and the Week reset seven days away.

[12] 2026-11-03, agy 1.4.8. Even with `GEMINI_DIR` changed, it read `~/.gemini`. Changing `HOME` to a temp folder made it ask for sign-in again. The keychain entry name was checked, but its contents were not opened. The changelog of 1.4.12, released the same day, also said nothing about accounts or config folders. The `AGY_ACCOUNT` in the executable is a variable that picks the account of a CLI attached as a plugin. It is unrelated to agy sign-in.

[13] 2026-11-04, agy 1.4.12. `/usage` reported 0 input and output tokens and took 4.1 to 7.2 seconds. With `HOME` pointed at an empty folder, agy printed "Authentication required" and the sign-in URL, and a fake `open` placed first on PATH received that URL.

[14] 2026-11-05, Claude Code 2.1.318, jq 1.8.2, macOS 15.7.1. Five runs of the wrapper with two Claude accounts took 1.008 seconds with the list and 0.470 seconds with the wrapper from before it.

[15] 2026-11-05, Claude Code 2.1.318. A session was recorded as limited and closed with `/exit` 137 seconds later. Closing appended `cost-state`, `file-history-snapshot`, and `last-prompt` entries, which carry no time, and changed the file's modified time. Before this fix acm compared only that time, so `acm status` and `acm resume` no longer listed the session. Histories written by 2.1.296 and 2.1.316 hold a limit message as an `assistant` entry with the model `<synthetic>`, `isApiErrorMessage` true, and `error` `rate_limit`. acm reads the last 256 KB of the history and counts only an `assistant` entry from a real model.
