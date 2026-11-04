#!/bin/sh
# Install acm. Running it again overwrites the install with this source.
#   ./install.sh              Copy the CLI, install the statusline wrapper, build the menu bar app
#   ./install.sh --no-app     CLI only, without the menu bar app. Linux always installs this way, since the app is macOS only
#   ./install.sh --uninstall  Restore the statusline, revert the shell lines and IDE settings that setup added,
#                             remove the CLI and the app (account folders and ~/.acm are kept)
#
# After install, acm setup asks about the shell function, tmux, IDE plugins, Claude and Codex accounts,
# artifact collection, and limit handoff, one at a time, and sets them up.
# Outside a terminal it does not ask and only shows the remaining steps. To skip the questions and take the defaults, run ACM_SETUP=--yes ./install.sh
#
# The CLI is copied to ~/.local/bin, not symlinked. acm keeps working if you move or delete the repo.
# ~/.acm/install.json records which repo and commit were installed. acm version shows it, and acm upgrade pulls this repo.
set -eu
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
APP="/Applications/ACM.app"
MODE="${1:-}"
OS="$(uname -s)"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing $1. $2" >&2; exit 1; }
}

if [ "$MODE" = "--uninstall" ]; then
  [ -x "$BIN/acm" ] && "$BIN/acm" setup --undo || true
  [ -x "$BIN/acm" ] && "$BIN/acm" uninstall-statusline || true
  rm -f "$BIN/acm" "$BIN/acm-statusline"
  if [ "$OS" = Darwin ]; then
    osascript -e 'tell application "ACM" to quit' >/dev/null 2>&1 || true
    rm -rf "$APP"
  fi
  echo "Removed. Account folders (~/.claude-<id>) and the state folder (~/.acm) were kept."
  exit 0
fi

if [ "$OS" = Darwin ]; then
  need python3 "Run xcode-select --install"
  need jq "Run brew install jq"
else
  need python3 "Install it with your package manager, such as sudo apt install python3"
  need jq "Install it with your package manager, such as sudo apt install jq"
  if [ "$MODE" != "--no-app" ]; then
    echo "The menu bar app is macOS only, so it is skipped. acm status shows the same accounts"
    MODE=--no-app
  fi
fi
need claude "Install Claude Code first"
# Check before installing anything, so a missing swiftc does not leave a half-finished install
if [ "$MODE" != "--no-app" ]; then
  need swiftc "Run xcode-select --install"
fi

mkdir -p "$BIN"
for f in acm acm-statusline; do
  rm -f "$BIN/$f"            # If an old symlink exists, remove only the link
  cp "$DIR/bin/$f" "$BIN/$f"
  chmod 755 "$BIN/$f"
done
echo "CLI: $BIN/acm"

STATE="${ACM_HOME:-$HOME/.acm}"
# The state folder holds emails and usage. Make it owner-only from the start so other users on this Mac cannot read it
mkdir -p "$STATE"
chmod 700 "$STATE"
commit=$(git -C "$DIR" rev-parse --short HEAD 2>/dev/null || true)
dirty=false
if [ -n "$commit" ] && [ -n "$(git -C "$DIR" status --porcelain 2>/dev/null)" ]; then dirty=true; fi
no_app=false
[ "$MODE" = "--no-app" ] && no_app=true
jq -n --arg source "$DIR" --arg commit "$commit" --argjson dirty "$dirty" --argjson no_app "$no_app" \
  --arg at "$(date '+%Y-%m-%d %H:%M')" \
  '{source: $source, commit: $commit, dirty: $dirty, no_app: $no_app, installed_at: $at}' > "$STATE/install.json"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    case "$(basename "${SHELL:-zsh}")" in
      bash) if [ "$OS" = Darwin ]; then rc="~/.bash_profile"; else rc="~/.bashrc"; fi ;;
      *) rc="~/.zshrc" ;;
    esac
    echo "Warning: $BIN is not on PATH. Add export PATH=\"\$HOME/.local/bin:\$PATH\" to $rc" ;;
esac

"$BIN/acm" install-statusline

if [ "$MODE" != "--no-app" ]; then
  "$DIR/app/build.sh"
  open "$APP"
fi

echo
"$BIN/acm" setup ${ACM_SETUP:-}

echo
"$BIN/acm" status
