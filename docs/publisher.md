# Artifact collection and screen control

This doc covers how sessions on several accounts publish artifacts under one account, and how sessions not on the primary account control the browser. Read it when you change the publisher session's permissions or publishing is blocked.

## Artifacts are collected in one account

An artifact is published as owned by the account its session is attached to. So as you move between accounts, artifacts scatter across them, and ones owned by an account other than the one signed in to your browser do not open. With `acm publisher on`, sessions on other accounts hand their artifacts to a publisher session on the primary account, which publishes them. Turning it on only sets how artifacts are handed off. The publisher session starts only when an artifact is handed to it. Artifacts are a Claude feature, so only a Claude account can be the primary account, and Codex sessions do not get these rules.

```bash
acm publisher on              # turn on; the publisher session starts when it is needed
acm publisher status          # whether it is on, the primary account, and the session state
acm publisher check           # whether publishing can be handed off now. Starts the publisher session if none is running
acm publisher account cl1    # the account to collect in. Defaults to the first Claude account
acm publisher model claude-sonnet-5-5 high  # publisher session model and effort
acm publisher stop            # stops only the running publisher session. Collection stays on
acm publisher off             # turn off; each session publishes under its own account again
```

While it is on, acm adds two things when it starts a session on another account. One is `--disallowedTools Artifact`, which removes the Artifact tool from that session. The other is `--append-system-prompt` with session rules that tell it to hand artifacts to the `acm-publisher` session with SendMessage. The session writes an HTML file, stages it with `acm publisher check <file>`, and sends the staged path. Then it passes the URL the publisher session returns to the user. A delete is handed off the same way and waits for your confirmation. See [A delete goes through the publisher session and waits for you](#a-delete-goes-through-the-publisher-session-and-waits-for-you).

## The publisher session runs in tmux with narrow permissions

The publisher session runs in the tmux session `acm-publisher` on `claude-sonnet-5-5` with effort high. tmux only keeps the publisher session running in the background without a window. Your own terminal does not need to be tmux. Whether you call `check` from iTerm, an IDE terminal, or another claude session's Bash, the tmux server starts on the spot if it is not running. To look in, run `tmux attach -t acm-publisher` in any terminal. The session judges the Artifact tool rules and updates existing artifacts, so it does not drop to a smaller model. The model is pinned to an exact ID, not an alias. No audit checks this value for you. When the model is retired or a newer generation of the same family comes out, change `PUBLISHER_MODEL` in `bin/acm` yourself. Its only tools are Read, Artifact, SendMessage, and ListAgents, and no MCP server is attached. Only Artifact has an allow rule, so it publishes without confirmation. The session acts on messages from other sessions, so what it can do is narrowed to this scope.

## The publisher session reads only files staged in the inbox

The publisher session handles requests from other sessions without asking. So a session hit by prompt injection could ask it to publish a file such as `~/.ssh`. To prevent this, the local files the publisher session reads and publishes are limited to `~/.acm/publisher/inbox` and that session's scratchpad.

For an update, it also reads the copy of the live version that Artifact read saved. The Artifact tool allows an update only from a session that has read the live version to the end. The publisher session starts fresh for each request and has never seen the live version. So if it cannot read this copy, every update with changed content is rejected.[4] After reading the copy to the end, it publishes the file from the request as is. The publisher session has no tool to edit files, so merging with the live version is the requesting session's job.

When the same file is sent again, the Artifact tool rejects it once more. The rejection comes with a note: if the file does include the live version's changes, send it once more as is. Sending it a third time as told goes through.[5] The publisher session cannot tell by itself whether the file reflects the live version. So it sends a third time only when the requesting session wrote that overwriting is allowed. Without that, it reports the number of lines found only in the live version and asks whether to overwrite. The session rules added to other sessions also tell them to state this decision in the request.

Other sessions stage files in the inbox with `acm publisher check <HTML file> [extra files...]` and send the staged path from the output to the publisher session. Staging rejects the files below.

- Hidden files and files in hidden folders. Not only `~/.ssh`, `~/.claude`, and `~/.acm` right under home, but also `.git` or `.secrets` inside a project are rejected
- Hard-linked files. From the name alone, you cannot tell where the original is
- Files under `~/Library`
- Extensions that are not web files. Only html, md, css, js, json, images, fonts, videos, pdf, txt, and csv are accepted
- Files over 16MB

A link is judged by the file it points to. Home is recognized by the folder itself, not by the path string. So a path with changed case such as `/users/<name>`, or one starting with `/System/Volumes/Data`, is still rejected. A checked file is opened only once. acm checks it again by the real path of the opened file, then copies from that same file. If the path is changed to point to another file between the check and the copy, the changed file is not staged. Staged files are set to 0600 so only you can read them, and the inbox is 0700. Extra files must be under the same folder as the first file. They keep the same relative positions in the staged folder, so the page's relative links still work. A staged folder older than a day is deleted at the next staging.

A PreToolUse hook enforces the scope. When acm starts the publisher session, it adds the `acm publisher guard` hook with `--settings`, and this hook sees every tool call. The hook enforces the rules below.

- Only Read, Artifact, SendMessage, ListAgents, and ToolSearch pass. Other tools loaded with ToolSearch, such as ArtifactData, are blocked too.
- Local paths for Read and Artifact must be inside the inbox or that session's scratchpad. Paths with `..` are refused. A relative path must stay in scope whether it is resolved against the working folder or `root`.
- Read also accepts that session's copies of live versions. The copy folder is `<session ID>/tool-results/` next to `transcript_path` from the hook input. Only files directly in that folder whose names start with `artifact-` pass. Copies from other sessions, subfolders, and links pointing outside are blocked. Using a copy as a publish path is blocked too.
- Artifact may use only publish, read, list, and delete. force, capabilities, and read's out_dir are blocked too.
- list shows only this account's own artifacts and the files of one of them. What others shared and the type catalog are blocked.
- delete takes the url of the artifact and nothing else, so one asset cannot be removed. The hook does not allow it outright. It answers `ask`, so the question to the user shows whatever allow rule is set.
- Artifact `files` accepts only known shapes. Those are a local path, `{from}`, `{artifact, path}` that copies on the server, and null that deletes. An unknown shape might contain a local path, so it is blocked.
- If the inbox has been replaced with a link, no file passes.

If the hook exits with a code other than 2, Claude Code runs the tool anyway. So the hook also blocks when it fails to read its input. The command ends with `|| exit 2`, so calls are blocked even if acm dies at the import step. The same `--settings` sets `disableAllHooks` to false, so other settings cannot turn this hook off. The system prompt also gets the same scope, appended after ROLE.md.

Claude Code's `--restricted` also limits file tools to the working folder, but acm does not use it. A session started in this mode does not open a messaging socket, so it cannot receive SendMessage.[3]

## The publisher session runs only when needed

Sessions on other accounts call `acm publisher check` before handing off a publish. If no publisher session is running, `check` starts one and waits until it appears in the Claude Code session list and can receive messages. A watcher in the same tmux window reads `status` and `statusUpdatedAt` from `~/.claude/sessions/<pid>.json` every 5 seconds to measure idle time. It stops the session after 30 seconds with no new request once work is done. If the session never gets any work after it starts, it stops it after 5 minutes.[1] Each `check` call records the time, so the session does not stop between `check` and the SendMessage that follows. Change the thresholds with `ACM_PUBLISHER_IDLE` and `ACM_PUBLISHER_IDLE_MAX`. Stops are logged in `~/.acm/publisher/watch.log`. acm does not publish with a one-shot `claude -p`, because that mode has no Artifact tool.[1]

The tmux server keeps the environment variables of the process that first started it. So when another claude session called `check`, that session's session ID and messaging socket passed straight to the publisher session.[2] When the calling session ends, these values point to a socket that no longer exists. A session started by a tool that wraps claude carries more. Orca adds a plugin folder, a hook address with its token, and a pane id to every session it starts.[6] Passed on, they would load that tool's plugin in the publisher session and report the publisher session's tool calls as the other pane's.

So the environment the publisher session starts with is an allow list, like the staging check and the hook. acm starts tmux with only the allowed variables. Inside the window, claude starts through `acm publisher exec`, which keeps only the allowed variables of that window and adds the primary account's config folder and acm's own markers. The second step is needed because a tmux server that was already running gives the window the environment it was started with. The allowed names are `PUBLISHER_ENV` in `bin/acm`: the home folder, user, shell, and `PATH`, the locale and time zone, the terminal and tmux variables, the XDG folders, and the proxy and CA certificate variables a network may need to reach claude.ai. Every other name is dropped, including `ANTHROPIC_*`, `CLAUDE_CODE_*`, and `PYTHONPATH`. The `claude -p` runs for usage polls and token refresh still start from the calling environment, with only the values tied to a claude session removed.

## The scope lives in ROLE.md

The publisher session's role and scope are in `~/.acm/publisher/ROLE.md`. It is a standing approval to publish externally at other sessions' request, so you must set the scope yourself. Without this file, acm does not start the publisher session. `acm setup` shows the default text and writes it after you agree. To change the scope, edit this file. The default text covers the points below.

- Approval to proceed without asking on publishes and updates that other Claude sessions on the same Mac request with SendMessage
- The scope ends at reading files the requesting session staged in the inbox, publishing them new or updating the given url, and replying to the requesting session with the resulting URL
- A delete is not part of the standing approval. The session calls Artifact delete so that you are asked in its window, and a message from another session never counts as your answer
- No changing sharing or editing files, and no publishing content that breaks the Artifact tool rules

A ROLE.md written with the old default text does not need edits. acm appends the file scope after ROLE.md separately, and the hook enforces it. The appended scope also covers the delete, so a ROLE.md that still lists deleting as out of scope works.[7]

## A delete goes through the publisher session and waits for you

An artifact belongs to the primary account, so deleting it goes the same way as publishing it. A session on another account runs `acm publisher check` and sends the publisher session a delete request with the artifact's url. If it does not know the url, it asks for a list of the account's artifacts first.

The publisher session does not delete on that request alone. A delete cannot be undone, and any session can send the request. So the hook answers `ask` for a delete, and Claude Code shows its own question in the publisher session's window: `Permanently delete "<title>"?`. The choice starts on No. The artifact is deleted only after you choose Yes there.[7]

The question shows in the publisher session's window, not in the session you asked. That session tells you so, and it opens a terminal on the window when it can, such as a new tab under Orca. From any terminal, `tmux attach -t acm-publisher` shows the window, and Ctrl-b d leaves it. `acm publisher status` says when the session is waiting for your answer.

While the question waits, the publisher session takes no other request, so publishing waits behind it. The watcher stops the session after 15 minutes without an answer, and nothing is deleted. Change the time with `ACM_PUBLISHER_CONFIRM`.

The confirmation is only as strong as the window. A process that can type into your tmux sessions can answer it, which is true of any claude session you run in tmux. What the hook rules out is a delete on a message alone.

You can still delete an artifact yourself in a session on the primary account, with `d` in the `/artifacts` list, or from the artifact's own menu on claude.ai.[7]

## The primary account keeps headroom for publishing

With artifact collection on, acm leaves the primary account out of automatic picks from 5h 70% or Week 85%. These values assume Week 15% is enough for publishing artifacts. Below them, the primary account is compared like any other account, so sessions spread evenly across accounts. Even when every account is blocked, acm keeps the primary account for last among the accounts that have anything left below 100%. So once every other account is at 100%, a new session starts on the primary account. If you choose it with `acm -a`, it starts regardless of the thresholds. Limit handoff follows the same thresholds. Change them with `ACM_RESERVE_FIVE_HOUR_CAP` and `ACM_RESERVE_SEVEN_DAY_CAP`. The menu bar window and the widget put a `Primary` tag on the primary account, and the tag turns orange when it leaves automatic picks. With artifact collection off, no headroom is kept, so the tag disappears too.

If the primary account still reaches its limit, publishing stops. Publishing under another account would scatter artifacts again. Sessions on other accounts run `acm publisher check` before handing off a publish. If it fails, they do not hand it off and tell the user the reset time. `check` reads the primary account's usage fresh on the spot. It also checks the Sonnet only weekly limit, which applies to the publisher session model `claude-sonnet-5-5`. The publisher session is not counted among running sessions, so it does not affect picks.

## Screen control from other accounts' sessions goes through aside

Claude in Chrome connects per claude.ai account, and the Chrome extension signs in to only one account at a time. If the extension is on the primary account, sessions on other accounts cannot connect to Chrome.

So acm also adds a session rule to sessions not on the primary account. The rule says to use the aside MCP for screen control. aside runs on its own Aside account, so sessions on any Claude account use the same browser. If `aside` is not in the default account's MCP list, this rule is not added.

For a site not signed in on Aside Browser, the session does not enter a password for you. It asks you to sign in yourself. Once you sign in, sessions on every account share that login.

## Footnotes

[1] 2026-10-31, Claude Code 2.1.314. The tool list of `claude -p` had no Artifact for either haiku or sonnet. A test publisher session with thresholds cut to 15 and 40 seconds started within 1 second of `check` and stopped at 40 seconds with no work. After handling one message, it stopped at the 15-second threshold. When `check` was called 11 seconds after work finished, it stopped 20 seconds after that call. The watcher runs every 5 seconds, so it stops up to 5 seconds later than the threshold.

[2] 2026-11-02, tmux 3.8. With no tmux server running, `acm publisher check` was called from a claude session's Bash. The publisher session registered with its own session ID and socket. But its process environment still had the calling session's `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_CHILD_SESSION=1`, and `CLAUDECODE=1`. After the fix, starting it the same way leaves only `ACM_ACCOUNT`, `ACM_LABEL`, and `ACM_ROLE`.

[3] 2026-11-02, Claude Code 2.1.316. A haiku session started with `--restricted` blocked both Read of files outside the working folder and Artifact publish. But its session record had no `messagingSocketPath`, so it did not appear in ListAgents, and SendMessage did not reach it. Removing only `--restricted` from the same command created the socket. The publisher session with the hook read the inbox file. It did not make the call for `~/.acm/accounts.json`, saying it was out of scope. Feeding the same input to that session's hook command blocked `accounts.json` with exit code 2.

[4] 2026-11-03, Claude Code 2.1.316. When the publisher session tried to update an existing deck, the Artifact tool rejected the publish because the session had never seen the live version. The same response said it had saved the whole live version to `~/.claude/projects/<working folder>/<session ID>/tool-results/artifact-<id>-<version>.html`. But the hook blocked Read of that file as outside the inbox. In the same version, the PreToolUse hook input had `transcript_path` as a `<session ID>.jsonl` path. Feeding the blocked input to the fixed hook passes with exit code 0. Feeding another session's transcript path blocks with 2.

[5] 2026-11-03, Claude Code 2.1.316. While updating the same deck with the fixed hook, the session ran publish three times without force. The first was rejected because the session had never seen the live version. The second was sent after reading all 1499 lines of the copy, and was rejected as the same content already rejected. The third sent the same file and updated the deck to version 1793686083-48ad. The publisher session sent the third only after the requesting session reported that it had compared the live version with the first version and nothing would be lost.

[6] 2026-11-05, Orca 1.4.249, Claude Code 2.1.318, tmux 3.8. A claude session started from Orca had `CLAUDE_CODE_PLUGIN_DIRS`, `ORCA_AGENT_HOOK_PORT`, `ORCA_AGENT_HOOK_TOKEN`, `ORCA_PANE_KEY`, and about twenty more `ORCA_*` names in its environment. None of them was in the list of names acm removed at the time. With the allow list, a publisher session started in a fake home from an environment holding these names, `CLAUDE_CODE_SESSION_ID`, and `PYTHONPATH` received none of them, and neither did the tmux server it started.

[7] 2026-11-05, Claude Code 2.1.318, Orca 1.4.249, tmux 3.8. Before this change the hook blocked every delete. A session on the second Claude account, asked to delete an artifact, sent the publisher session two requests, was refused twice, and searched for a delete action of its own until the user deleted the artifact by hand. With the change, a session on the second account was asked to delete an artifact that an earlier publisher session had published. `acm publisher check` started a new publisher session, and the request reached it. The hook's output was the `ask` decision, the window showed `Permanently delete "acm delete route test 2"?` with No selected, and `acm publisher status` reported the session as waiting. The question waited 7 minutes 44 seconds, and nothing was deleted in that time. Then the user chose Yes in the window, the artifact was deleted, and the publisher session's reply reached the requesting session. In the run before it, the requesting session opened an Orca tab on the window, and the artifact was deleted 11 seconds after the question appeared. Who answered there was not recorded. The publisher session ran in auto mode in both runs. The primary account's ROLE.md still had the earlier default text, which lists deleting as out of scope. The watcher's 15 minute stop was not waited for. The installed Claude Code lists `delete` among the actions that a whole-tool allow rule does not cover, and holds the text "in the Claude Code terminal `/artifacts` lists their Artifacts (press d to delete the selected one), or on claude.ai from the Artifact's own menu". These were read from the program, and the two ways in that text were not tried.
