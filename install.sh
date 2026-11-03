#!/bin/sh
# acm 설치. 다시 돌리면 이 소스로 덮어쓴다.
#   ./install.sh              CLI 복사, statusline 래퍼 설치, 메뉴바 앱 빌드
#   ./install.sh --no-app     메뉴바 앱은 빼고 CLI 만
#   ./install.sh --uninstall  statusline 원복, setup 이 넣은 셸 줄과 IDE 설정 원복, CLI 와 앱 삭제
#                             (계정 디렉터리와 ~/.acm 은 남긴다)
#
# 설치 뒤 acm setup 이 셸 함수, tmux, IDE 플러그인, Claude 와 Codex 계정, 아티팩트 모으기, 한도 이어 가기를
# 하나씩 묻고 맞춘다.
# 터미널이 아니면 묻지 않고 남은 일만 보인다. 묻지 않고 기본값대로 하려면 ACM_SETUP=--yes ./install.sh
#
# CLI 는 심링크가 아니라 ~/.local/bin 에 복사한다. 저장소를 옮기거나 지워도 acm 은 계속 돈다.
# 어느 저장소의 어느 커밋을 깔았는지 ~/.acm/install.json 에 남긴다. acm version 이 보이고 acm upgrade 가 이 저장소를 당긴다.
set -eu
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
APP="/Applications/ACM.app"
MODE="${1:-}"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "필요: $1 — $2" >&2; exit 1; }
}

if [ "$MODE" = "--uninstall" ]; then
  [ -x "$BIN/acm" ] && "$BIN/acm" setup --undo || true
  [ -x "$BIN/acm" ] && "$BIN/acm" uninstall-statusline || true
  osascript -e 'tell application "ACM" to quit' >/dev/null 2>&1 || true
  rm -f "$BIN/acm" "$BIN/acm-statusline"
  rm -rf "$APP"
  echo "지웠습니다. 계정 디렉터리(~/.claude-<id>)와 상태(~/.acm)는 남겨 두었습니다."
  exit 0
fi

need python3 "xcode-select --install"
need jq "brew install jq"
need claude "Claude Code 를 먼저 설치하세요"

mkdir -p "$BIN"
for f in acm acm-statusline; do
  rm -f "$BIN/$f"            # 예전 심링크가 있으면 링크만 지운다
  cp "$DIR/bin/$f" "$BIN/$f"
  chmod 755 "$BIN/$f"
done
echo "CLI: $BIN/acm"

STATE="${ACM_HOME:-$HOME/.acm}"
# 상태 폴더에는 이메일과 사용량이 든다. 같은 Mac 의 다른 사용자가 읽지 못하게 처음부터 나만 연다
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
  *) echo "주의: PATH 에 $BIN 이 없습니다. ~/.zshrc 에 export PATH=\"\$HOME/.local/bin:\$PATH\" 를 넣으세요" ;;
esac

"$BIN/acm" install-statusline

if [ "$MODE" != "--no-app" ]; then
  need swiftc "xcode-select --install"
  "$DIR/app/build.sh"
  open "$APP"
fi

echo
"$BIN/acm" setup ${ACM_SETUP:-}

echo
"$BIN/acm" status
