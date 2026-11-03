# Menu bar and widget

This doc covers what the menu bar app and the floating widget show. `install.sh` builds the app and puts it in `/Applications/ACM.app`.

## The menu bar shows only the logo

The menu bar shows only the acm logo, not usage. Usage means something only when you open the window and see it with the account cards. The logo is a template image, so the system matches its color to a light or dark menu bar. On a MacBook with a notch, if the menu bar item hides behind the notch, hold Command and drag it.

## The menu bar window groups accounts in a box with a different color per tool

Click the logo to open the window. At the top are the acm logo and the name AI Account Manager. Below them are the account cards and the list of running sessions. Account cards are grouped in a box per tool. The Claude box has an orange border, and the Codex box a blue one. The box header shows the tool's logo and its next pick. The logos borrow the icons of the Claude, Codex, and ChatGPT apps installed on this Mac, and fall back to a symbol if the app is missing.

- An account card shows 5h and Week gauges, usage, and the time left until reset, such as `Resets in 1d 5h`. Gauges are green below 70%, orange below 90%, and red at 90% or more.
- The plan, such as `Ultra` or `free`, appears next to the email. The Claude plan is the display name Claude Code received at sign-in. The Codex plan is the value app-server reported.
- An account with a per-model weekly limit shows one more gauge named after the model, such as `Fable` or `Sonnet`. Which limit counts toward picks is in [Account selection and usage](selection.md).
- Codex cards name the long window gauge by its length, such as `30d`. An account that Codex reported as unusable right now gets a red `Unavailable`.
- An orange `claude` or `codex` mark in the session list means a session started without acm. With more than one tool, each line starts with the tool name.
- At the bottom are switches for the selection mode, launch at login, and the floating widget. If you have a Codex account, "New Session…" becomes a menu for choosing the tool.

A verified Ultra account with no 5-hour limit leaves its 5h spot empty. Mixed with accounts that have a limit, the widget shows `No limit` in the 5h cell, and `acm status` shows `none`. If no signed-in account has a 5h limit, the widget, the account cards, and `acm status` drop the 5h column. An account whose usage has never been read is not assumed to have no limit. The widget and `acm status` put `–` in that cell, and the account card shows `Not read yet`.

## The widget floats on top in every Space

The floating widget is a small window that stays on top in every Space. Choose the tools it shows with "Show in widget" in each tool box of the menu bar window. You can also turn them on and off from the widget's right-click menu. At first it shows only Claude. With both on, each tool gets its own header, one after the other. The last tool cannot be turned off, so the widget is never empty. To hide the whole widget, turn off "Floating widget" at the bottom of the menu bar window.

A one-line header holds the column names `5h Reset Week Reset`. Each account gets one line with gauges, usage, and the time left until reset. With more than one tool, the header shows the logo and tool name on the left. If the long window is 30 days, as on the Codex free plan, the column is named `30d` instead of Week. If any account has a per-model weekly limit, a model column such as `Fable Reset` is added after Week. Accounts without that limit get `–` in the cell. Hover over a per-model cell to see whether that limit counts toward the current pick. The account marked `▸` is the next pick. Drag the widget to move it, and it remembers the spot. Right-click to refresh or hide it.

## The app only calls acm status

The app only calls `acm status --json` every 30 seconds. It never reads usage itself. If an account is due for a poll, acm starts the `/usage` or `codex app-server` poll in the background, and the app gets the new values on the next call. If acm does not finish within 60 seconds, the app cuts it off, dims the last values, and waits for the next call. The menu bar app does not inherit the shell's PATH, so it adds `~/.local/bin` and `/opt/homebrew/bin` to PATH before calling acm. If you changed only the app, rebuild it with `app/build.sh`.
