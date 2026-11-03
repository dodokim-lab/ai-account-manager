# 설치와 처음 설정

이 문서는 `install.sh` 와 `acm setup` 이 무엇을 바꾸는지, 터미널 밖에서 띄우는 세션을 acm 으로 보내는 법을 적는다. 설치만 하려면 README 의 빠른 시작으로 충분하다.

## install.sh 는 네 가지를 한다

```bash
./install.sh              # CLI 와 statusline 래퍼, 메뉴바 앱까지
./install.sh --no-app     # 메뉴바 앱 없이 CLI 만
./install.sh --uninstall  # statusline 을 되돌리고 CLI 와 앱을 지운다
```

- 첫째, `bin/acm` 과 `bin/acm-statusline` 을 `~/.local/bin` 에 복사한다. 심링크가 아니라 복사라서 저장소를 옮기거나 worktree 를 지워도 acm 은 계속 돈다. 소스를 고친 뒤에는 `install.sh` 를 다시 돌려야 반영된다. 어느 저장소의 어느 커밋을 깔았는지는 `~/.acm/install.json` 에 남긴다.
- 둘째, `~/.claude/settings.json` 의 `statusLine` 을 `acm-statusline '<원래 명령>'` 으로 감싼다. 원래 명령은 래퍼의 인자로 남아 그대로 실행되므로 화면은 달라지지 않는다. 원래 명령을 acm 이 따로 두는 파일로 옮기지 않는 것은, 그런 파일은 Claude Code 가 보호하지 않아서다. 세션이 묻지 않고 그 파일을 고치면 모든 세션의 statusline 에서 코드가 돈다. `settings.json` 이 아직 없는 새 설치면 만든다. 바꾸기 전 settings 는 `settings.json.acm-bak-<시각>` 으로 남긴다.
- 셋째, `app/` 의 메뉴바 앱을 빌드해 `/Applications/ACM.app` 에 넣고 띄운다.
- 넷째, `acm setup` 을 불러 나머지 설정을 하나씩 묻고 맞춘다. 다음 절에 있다.

필요한 것은 `python3` 와 `jq`, `claude`, 앱을 빌드할 때의 `swiftc` 다. 하나라도 없으면 설치 방법을 알리고 멈춘다. `codex` 는 Codex 계정을 쓸 때만 있으면 된다. `~/.local/bin` 이 `PATH` 에 없으면 `acm setup` 이 셸 함수와 함께 넣는다.

`--uninstall` 은 `acm setup` 이 넣은 셸 줄과 IDE 플러그인 설정을 되돌리고, 계정 디렉터리와 `~/.acm` 은 남긴다. 로그인 정보가 들어 있어서 지우는 것은 사람이 판단해야 하기 때문이다.

## 처음 설정은 acm setup 이 묻고 맞춘다

`acm setup` 은 아래 일곱 가지를 차례로 점검하고, 안 된 것만 물어서 맞춘다. 이미 된 것은 건드리지 않으니 몇 번을 돌려도 된다.

| 점검 | 안 돼 있으면 하는 일 |
|---|---|
| 터미널 | 로그인 셸의 rc 파일에 `PATH` 와 `claude`, `codex` 셸 함수를 넣는다. zsh 는 `~/.zshrc`, bash 는 `~/.bash_profile` 이다 |
| 발행 세션 실행 | tmux 가 없으면 `brew install tmux` 로 설치한다 |
| IDE | Claude Code 플러그인이 깔린 JetBrains IDE 마다 가장 새 판의 Claude 명령을 `~/.local/bin/acm` 으로 바꾼다. Claude Code 확장이 깔린 VS Code 와 Cursor, Windsurf, VSCodium 은 사용자 `settings.json` 에 `claudeCode.claudeProcessWrapper` 를 넣는다 |
| 계정 | 로그인 안 된 Claude 계정을 로그인시키고, 계정이 하나뿐이면 추가할지 묻는다. 추가 계정이 있으면 `projects` 와 `skills`, `hooks` 를 `~/.acm/shared` 로 옮긴다 |
| Codex 계정 | `codex` 와 `~/.codex` 가 있으면 기본 계정 `cx1` 을 등록할지 묻는다. 등록한 Codex 계정마다 로그인과 공유 링크를 본다 |
| 아티팩트 모으기 | 계정이 둘 이상이면 발행 세션 승인 범위를 기본 문안으로 쓰고, 대표 계정을 고른 뒤 발행 모으기를 켠다. 대표 계정은 브라우저로 claude.ai 에 로그인해 둔 계정이어야 아티팩트를 열어 볼 수 있다 |
| 한도 이어 가기 | 계정이 둘 이상이면 `~/.claude/settings.json` 에 `rate_limit` 매처의 `StopFailure` 훅을 더한다. 있던 훅은 그대로 두고, `--undo` 는 acm 훅만 뺀다 |

JetBrains IDE 가 떠 있으면 플러그인 설정은 바꾸지 않고 남은 일로 알린다. IDE 가 끌 때 메모리에 있던 설정으로 파일을 덮어쓸 수 있어서다. VS Code 계열은 끌 때 `settings.json` 을 덮어쓰지 않아서 떠 있어도 바꾸고, 창을 다시 불러오면(Developer: Reload Window) 적용된다. `settings.json` 은 다시 쓰지 않고 첫 `{` 뒤에 한 줄만 넣으니 주석과 서식이 그대로 남고, `--undo` 는 그 줄만 뺀다. 이미 다른 `claudeProcessWrapper` 가 있으면 건드리지 않고 남은 일로 알린다. 같은 이유로 claude 세션이 떠 있으면 공유 폴더를 옮기지 않는다. 메뉴바 앱이 iTerm 을 제어하는 권한은 macOS 가 처음 쓸 때 묻는 것이라 setup 이 대신할 수 없다.

```bash
acm setup            # 하나씩 묻고 맞춘다. 터미널이 아니면 --check 처럼 보기만 한다
acm setup --yes      # 묻지 않고 기본값대로. 계정 추가처럼 사람이 로그인해야 하는 일은 건너뛴다
acm setup --check    # 바꾸지 않고 남은 일만 보인다
acm setup --undo     # 넣은 셸 줄과 IDE 플러그인 설정을 되돌린다. 계정과 발행 설정은 그대로 둔다
```

`install.sh` 가 터미널에서 돌면 `acm setup` 이 묻고, 스크립트 안에서 돌면 보기만 한다. 묻지 않고 기본값대로 하려면 `ACM_SETUP=--yes ./install.sh` 로 돌린다. IDE 설정을 바꾸기 전의 값은 `~/.acm/setup.json` 에 남겨 `--undo` 가 되돌릴 때 쓴다. acm 이 새로 만든 설정 파일은 지운다.

## 터미널 밖에서 띄우는 세션도 acm 으로 보낸다

`claude` 를 직접 실행하면 acm 을 거치지 않아 기본 계정으로 뜨고, 기본 계정 사용량은 대부분 여기서 나온다. 그래서 사람이 터미널에 친 `claude` 와 `codex` 만 acm 으로 보내는 셸 함수를 `~/.zshrc` 에 건다. `claude` 는 `acm claude` 로, `codex` 는 `acm codex` 로 보내서 각각 그 도구의 계정 가운데서 고른다. `acm setup` 이 넣어 주고, 직접 넣는다면 아래 한 줄이다.

```bash
if command -v acm >/dev/null 2>&1; then eval "$(acm shell-init)"; fi
```

이 함수는 터미널에서 직접 친 경우에만 acm 을 거치고, 파이프나 스크립트 안에서는 원래 `claude` 와 `codex` 를 부른다. `mcp` 와 `auth`, `update` 같은 하위 명령도 계정을 고를 일이 아니라서 그대로 보낸다. Codex 는 `login` 과 `logout`, `mcp`, `update` 같은 하위 명령이 그렇다. 실행 파일 자체를 바꾸지 않으니 다른 도구가 부르는 `claude` 와 `codex` 는 영향을 받지 않는다. 원래대로 띄우려면 `command claude` 나 `command codex` 를 친다.

`acm` 만 치면 어느 도구로 열지 묻고 그냥 Enter 를 치면 Claude 로 연다. Codex 계정을 등록하지 않았고 `codex` 나 `~/.codex` 가 없으면 묻지 않는다. JetBrains 플러그인처럼 IDE 가 띄운 터미널에서는 묻지 않고 Claude 로 연다. 이 판으로 올리기 전에 열어 둔 셸에는 예전 함수가 남아 있다. 인자 없이 친 `claude` 가 도구를 묻거나 `codex` 가 acm 을 거치지 않아 기본 계정 `cx1` 로 뜬다. 새 셸을 열거나 그 셸에서 `exec zsh -l` 을 치면 새 함수를 쓴다.

터미널 밖에서 띄우는 곳은 각각 바꿔 준다.

| 띄우는 곳 | 바꿀 것 |
|---|---|
| iTerm, herdr | 셸에서 `acm` 으로 실행 |
| JetBrains Claude Code 플러그인 | 설정의 Claude 명령을 `~/.local/bin/acm` 의 절대 경로로. `acm setup` 이 IDE 가 꺼져 있을 때 `options/claude-code-plugin-settings.xml` 의 `claudeCommand` 를 바꾸고, IDE 를 다시 띄우면 적용된다 |
| VS Code 계열 Claude Code 확장 | 사용자 설정의 `claudeCode.claudeProcessWrapper` 를 `~/.local/bin/acm` 의 절대 경로로. `acm setup` 이 넣는다 |
| 메뉴바 앱 | "새 세션…" 이 도구와 폴더를 묻고 iTerm 새 창에서 `acm claude` 나 `acm codex` 를 실행 |

처음 "새 세션…" 을 누르면 macOS 가 ACM 이 iTerm 을 제어해도 되는지 묻는다. 허용해야 창이 열린다.

VS Code 계열 확장은 `claudeProcessWrapper` 로 acm 을 부를 때 확장에 든 claude 의 경로를 인자로 넘긴다.[1] acm 은 첫 인자가 `anthropic.claude-code-<버전>` 확장 폴더 안의 claude 실행 파일이면 계정을 고른 뒤 그 claude 를 띄우고, `auth` 나 `--version` 같은 하위 명령은 계정을 고르지 않고 그대로 넘긴다. 확장 폴더 밖의 실행 파일은 `claude ./claude-setup.sh` 처럼 프롬프트로 넘긴 경로일 수 있어서 실행하지 않는다. 경로가 첫 인자로 온다고 보고 만들었고, 실제 확장으로는 아직 확인하지 않았다.

셸 함수와 IDE 확장은 claude 를 acm 으로 보내서, acm 이 멈추면 claude 도 뜨지 않는다. 그래서 acm 은 계정을 고르다 예상하지 못한 오류가 나면 계정을 고르지 않고 claude 를 그대로 띄우고, 오류는 한 줄로 알린다. 로그인된 계정이 하나도 없으면 첫 계정으로 띄워 Claude Code 의 로그인 화면을 보인다. 확장이 `--append-system-prompt` 나 `--disallowedTools` 를 함께 넘기면 acm 의 운영 규칙을 그 값 뒤에 이어 붙여서, 확장이 넣은 값이 지워지지 않는다. Claude Desktop 은 `CLAUDE_CONFIG_DIR` 를 따르지 않아 acm 으로 보낼 수 없다.

## acm 을 새 판으로 올리려면

`acm upgrade` 는 `~/.acm/install.json` 에 남은 저장소를 `git pull --ff-only` 로 당기고 그 저장소의 `install.sh` 를 다시 돌린다. 메뉴바 앱 없이 깔았으면 다시 깔 때도 앱을 빼고, 저장소를 직접 고쳤으면 `acm upgrade --no-pull` 로 당기지 않고 다시 깐다. `acm version` 은 acm 과 claude 의 판, 설치한 커밋을 보인다. 이 기록은 이 판의 `install.sh` 부터 남기니, 그 전에 깔았으면 한 번은 저장소에서 `./install.sh` 를 직접 돌린다.

0.2.0 에서 0.3.0 으로 올려도 Claude 계정 id 는 `acc1`, `acc2` 그대로라 다시 로그인할 일이 없다. 새로 더하는 계정만 `cl3` 처럼 새 규칙을 따른다. id 까지 `cl` 로 바꾸려면 추가 계정 폴더 이름이 바뀌는 셈이라 그 계정은 다시 로그인해야 한다. 올리기 전에 열어 둔 터미널에서는 `codex` 가 acm 을 거치지 않으니, 새로 열거나 `exec zsh -l` 을 친다.

## 각주

[1] Claude Code VS Code 문서의 Extension settings 표. "Executable used to launch the Claude process. The bundled binary path is passed as an argument when present." https://code.claude.com/docs/en/vs-code
