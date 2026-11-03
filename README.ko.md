# ai-account-manager

[English](README.md) | 한국어

<img src="docs/logo.svg" alt="다음 배정 표시와 사용량 막대 두 개를 그린 acm 로고" width="96">

acm 은 한 사람이 가진 Claude Code 와 Codex CLI 계정 여러 개에 세션을 나눠 띄우는 런처다. 이 문서는 구독 계정을 두 개 이상 가진 개발자가 acm 을 처음 깔고 쓸 때 읽는다. acm 은 세션을 띄울 때마다 그 도구의 계정 가운데 남은 여유가 가장 큰 계정을 골라 붙여서 가진 계정의 사용량이 고르게 줄어든다. 메모리와 히스토리, 설정, 스킬은 도구마다 `~/.claude` 나 `~/.codex` 하나를 모든 계정이 같이 쓴다. 그래서 어느 계정으로 떠도 하던 일의 맥락이 이어진다.

발행 모으기를 켜면 어느 계정 세션에서 발행한 Claude 아티팩트든 대표 계정 하나에 모인다.

acm 은 Anthropic 이나 OpenAI 와 관계없는 비공식 도구다. 로그인 토큰은 읽지도 옮기지도 않는다. 로그인은 계정마다 Claude Code 와 Codex 가 자기 로그인 흐름으로 직접 한다. 사용량은 statusline 과 그 계정으로 돌린 `claude -p /usage`, `codex app-server` 에서 읽는다. Anthropic 은 [구독 요금제의 사용 한도가 평범한 개인 사용을 전제한다](https://code.claude.com/docs/en/legal-and-compliance)고 적고 있어서 acm 은 본인이 가진 계정에만 쓴다.

## 빠른 시작

지금은 macOS 에서만 돈다. 설치 전에 아래 도구가 있어야 한다.

| 도구 | 필요한 때 |
|---|---|
| `python3`, `jq`, `claude` | 늘 |
| `swiftc` | 메뉴바 앱을 빌드할 때. 앱은 Apple silicon 의 macOS 14 이상에서 돈다. 앱 없이 깔려면 `./install.sh --no-app` 을 쓴다 |
| `codex` | Codex 계정을 쓸 때 |
| `tmux` | 아티팩트 모으기를 켤 때. 없으면 `acm setup` 이 brew 로 설치할지 묻는다 |

`python3` 와 `jq`, `claude` 가 없으면 `install.sh` 가 설치 방법을 알리고 멈춘다. 앱까지 깔 때는 `swiftc` 가 없어도 멈춘다.

1. 저장소를 받는다.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ```

2. JetBrains IDE 와 떠 있는 claude 세션을 모두 닫는다. 떠 있으면 `acm setup` 이 IDE 플러그인 설정과 공유 폴더를 건드리지 않고 남은 일로 미룬다.
3. `./install.sh` 를 돌린다. CLI 와 statusline 래퍼, 메뉴바 앱을 깐 뒤 `acm setup` 을 불러 남은 설정을 하나씩 묻는다.
4. setup 이 계정을 추가할지 물으면 추가하고 그 계정으로 로그인한다. 기본 계정 `cl1` 은 지금 쓰는 `~/.claude` 라서 따로 할 일이 없다.
5. 새 터미널을 열고 `claude` 를 친다. setup 이 셸 rc 파일에 넣은 함수가 `acm claude` 로 보내서 남은 여유가 가장 큰 Claude 계정으로 뜬다.
6. `acm status` 로 계정마다 로그인과 사용량을 확인한다.

## 계정을 더하려면

```bash
acm add cl2                 # ~/.claude-cl2 를 만든다
acm -a cl2 auth login       # 그 계정으로 로그인
acm rm cl2                  # 목록에서 뺀다. 디렉터리와 키체인 항목은 남긴다
```

`acm add` 로 직접 더했으면 로그인한 뒤 `acm setup` 을 돌린다. 계정이 하나일 때 건너뛴 아티팩트 모으기와 한도 이어 가기를 이때 맞춘다.

## Codex 계정을 붙이려면

처음 `acm add --codex` 를 치면 지금 쓰는 `~/.codex` 를 기본 계정 `cx1` 로 등록한다. 브라우저가 다른 ChatGPT 계정에 로그인돼 있으면 로그인 주소를 시크릿 창에서 연다.

```bash
acm add --codex cx2              # ~/.codex-cx2 를 만든다
acm -a cx2 login --device-auth   # 화면의 주소를 열고 코드를 넣는다
```

## 세션을 띄우려면

```bash
acm                      # 어느 도구로 열지 묻는다
acm claude               # 남은 여유가 가장 큰 Claude 계정으로
acm -c                   # 도구 이름이 없으면 claude 인자로 넘긴다
acm codex                # 남은 여유가 가장 큰 Codex 계정으로
acm -a personal          # 계정을 지정. 그 계정의 도구로 뜬다
acm pick [codex]         # 띄우지 않고 어느 계정이 될지만 본다
acm resume               # 한도로 멈춘 Claude 세션을 다른 계정에서 이어 간다
acm codex resume <ID>    # Codex 세션은 어느 Codex 계정에서든 연다
```

배정은 같은 도구의 계정끼리만 한다. `-a` 와 이번만 라운드로빈으로 고르는 `--rr` 은 맨 앞에 둔다. 계정 자리에는 id 와 표시 이름, 이메일, 이메일 앞부분 중 아무것이나 쓴다. acm 을 거치지 않고 띄우려면 `command claude`, `command codex` 를 친다.

IDE 와 메뉴바 앱에서 띄우는 법은 [설치와 처음 설정](docs/setup.md) 에 있다. 계정을 고르는 점수와 한도에 걸린 세션을 이어 가는 법은 [계정 배정과 사용량](docs/selection.md) 에 있다.

## 아티팩트를 한 계정으로 모으려면

아티팩트는 세션이 붙은 계정 소유로 발행돼서 계정을 옮겨 가며 쓰면 계정마다 흩어진다. 발행 모으기를 켜면 다른 계정 세션은 대표 계정의 발행 전용 세션에 아티팩트를 맡긴다. 계정이 둘 이상이면 `acm setup` 이 승인 범위를 보여 주고 대표 계정을 고르게 한 뒤 켠다.

```bash
acm publisher on         # 켠다. 발행 세션은 맡길 때 뜬다
acm publisher status     # 켜짐 여부와 대표 계정, 세션 상태
acm publisher off        # 끄고 각 세션이 자기 계정으로 발행하게 되돌린다
```

대표 계정은 브라우저로 claude.ai 에 로그인해 둔 계정이어야 아티팩트를 열어 볼 수 있다. 지금은 Claude 아티팩트만 모은다. Codex 의 Sites 를 모으는 일은 [나중에 할 것](docs/roadmap.md) 에 있다.

## Claude Code 를 올린 뒤 점검하려면

acm 은 `/usage` 출력 형식처럼 문서에 없는 Claude Code 구조에 기댄다. Claude Code 를 올린 뒤 `acm doctor` 를 돌리면 그 구조가 기대대로인지 계정마다 실제로 읽어 보고 알린다. 문제가 있으면 종료 코드 1 로 끝난다.

```bash
acm doctor              # Claude Code 구조 점검
acm upgrade             # 설치한 저장소를 git pull 하고 install.sh 를 다시 돌린다
```

## 되돌리거나 지우려면

```bash
acm setup --undo           # 넣은 셸 줄과 IDE 플러그인 설정을 되돌린다
./install.sh --uninstall   # 위에 더해 statusline 을 되돌리고 CLI 와 앱을 지운다
```

둘 다 계정 디렉터리와 `~/.acm` 은 남긴다. 로그인 정보가 들어 있어서 지우는 것은 사람이 판단해야 하기 때문이다.

## 문제 해결

설치하고 처음 쓸 때 자주 막히는 곳과 푸는 법이다.

| 증상 | 해결 |
|---|---|
| `acm setup` 이 IDE 플러그인 설정을 남은 일로 미뤘다 | JetBrains IDE 를 닫고 `acm setup` 을 다시 돌린다 |
| 공유 폴더를 `~/.acm/shared` 로 옮기지 못했다고 나온다 | claude 세션을 모두 닫고 `acm sync --fix` 를 돌린다 |
| `claude` 나 `codex` 를 쳐도 acm 을 거치지 않는다 | setup 전에 열어 둔 터미널이다. 새 터미널을 열거나 `exec zsh -l` 을 친다 |
| 메뉴바 앱의 "New Session…" 이 창을 열지 않는다 | 처음 누를 때 macOS 가 ACM 의 iTerm 제어를 묻는다. 허용해야 창이 열린다 |

## 더 읽을 문서

| 문서 | 다루는 것 |
|---|---|
| [설치와 처음 설정](docs/setup.md) | `acm setup` 이 바꾸는 것, 셸 함수, IDE 에서 띄우기 |
| [계정 관리](docs/accounts.md) | 계정 디렉터리 구성, 공유 폴더, 로그인 토큰 갱신, Codex 계정 |
| [계정 배정과 사용량](docs/selection.md) | 배정 기준과 환경변수, 사용량 수집, Ultra 계정, Codex 사용량 |
| [아티팩트 모으기와 화면 제어](docs/publisher.md) | 발행 세션과 승인 범위, 대표 계정 여유, aside |
| [메뉴바와 위젯](docs/app.md) | 메뉴바 창의 도구별 계정 카드, 떠 있는 위젯 |
| [나중에 할 것](docs/roadmap.md) | 미뤄 둔 기능과 그 이유 |

## 파일 구성

| 경로 | 내용 |
|---|---|
| `bin/acm` | CLI. Python 3.9 표준 라이브러리만 쓴다 |
| `bin/acm-statusline` | statusline 래퍼. 사용량을 적고 원래 statusline 을 실행한다 |
| `app/` | 메뉴바 앱 SwiftUI 소스와 `build.sh`. Apple silicon 의 macOS 14 이상용으로 빌드한다. ad-hoc 서명이라 빌드한 Mac 에서만 돈다 |
| `docs/` | 기능별 자세한 설명과 로고 `logo.svg` |
| `tests/` | 가짜 홈 폴더에서 도는 테스트. `python3 -m unittest discover -s tests` |
| `install.sh` | 설치와 제거 |
| `~/.acm/` | 상태. `accounts.json` 과 계정별 사용량, 조회와 세션 기록, 발행 세션 폴더. 소유자만 여는 0700 으로 맞춘다 |

## 기여하거나 취약점을 알리려면

PR 을 올리기 전에 돌릴 검사와 지킬 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md) 에 영어로 있다. 보안 취약점은 공개 이슈 대신 [SECURITY.md](SECURITY.md) 에 적힌 대로 비공개로 신고한다.

## 라이선스

MIT 라이선스로 배포한다. 전문은 `LICENSE` 파일에 있다.
