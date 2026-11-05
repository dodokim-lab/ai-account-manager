# ai-account-manager

[English](README.md) | 한국어

Claude Code 나 Codex 구독을 여러 개 가져도 계정들은 서로 따로 논다. 세션은 마지막으로 로그인한 계정으로 뜨므로 한 계정이 한도에 닿는 동안 다른 계정은 쓰이지 않고 남는다. 메모리와 히스토리, 설정, 스킬도 계정마다 따로라서 다른 계정으로 옮기면 빈 맥락에서 다시 시작해야 한다.

acm 은 이 계정들을 하나처럼 쓰게 하는 런처다. `claude` 와 `codex` 를 평소대로 치면 acm 이 그 도구의 계정 가운데 남은 여유가 가장 큰 계정으로 세션을 띄운다. 모든 계정이 같은 `~/.claude` 나 `~/.codex` 를 읽어서 어느 계정으로 떠도 하던 일의 맥락이 따라온다. [Orca](https://github.com/stablyai/orca) 뒤에서도 돈다. Orca 가 데스크톱에서 띄우고 폰에 보여 주는 세션도 같은 방식으로 계정을 받고 같은 맥락을 쓴다.

![왼쪽 터미널에서 claude 와 codex 를 치면 acm 이 고른 계정이 찍힌다. 오른쪽 acm 메뉴바 창에는 Claude 계정 세 개와 Codex 계정 두 개가 5시간과 주간 사용량 게이지로 보인다. 도구마다 고른 계정에는 테두리가 쳐져 있다. 터미널 아래에는 Claude 계정 cl1 과 cl2, cl3 이 ~/.claude 한 곳을 가리킨다. Codex 계정 cx1 과 cx2 는 ~/.codex 한 곳을 가리킨다.](docs/readme/hero.svg)

## acm 은 이런 점이 다르다

- 세션마다 계정이 정해진다. 새 세션은 남은 여유가 가장 큰 계정에서 뜨므로 계정을 바꿀 일이 없다.
- 모든 계정이 맥락 하나를 같이 쓴다. 메모리와 히스토리, 설정, 스킬이 `~/.claude` 나 `~/.codex` 한 곳에 있다.
- 로그인 토큰을 읽지도 옮기지도 않는다. 계정마다 그 도구의 로그인 흐름으로 로그인한 채로 있다.
- Claude Code 와 Codex 를 한 도구로 다룬다. 두 도구의 계정이 같은 상태 표와 같은 메뉴바 창에 보인다.
- Claude 아티팩트를 한 계정에 모아서 한 곳에서 고치고 지운다.
- Orca 뒤에서 돈다. Orca 의 계정 전환은 누를 때 활성 계정을 바꾼다. acm 을 뒤에 두면 Orca 가 띄우는 세션마다 계정이 정해지고 계정들이 맥락 하나를 같이 쓴다.

자세한 설명과 다른 도구와 견준 표는 [비슷한 도구와 무엇이 다른가](docs/comparison.md) 에 있다. 견준 도구는 claude-swap 과 CCS 계정 풀, claude-limits, Orca 의 계정 전환이다. Orca 설정은 [Orca 와 함께 쓰기](docs/orca.md) 에 있다.

## 빠른 시작

macOS 와 Linux 에서 돈다. Linux 지원은 새로 넣은 것이라 실제 로그인한 계정으로는 아직 돌려 보지 않았다. Windows 지원은 [플랫폼 지원 계획](docs/platforms.md) 에 적어 두었다. `python3` 와 `jq`, `claude` 가 있어야 하고 Codex 계정을 쓰려면 `codex` 도 있어야 한다. 메뉴바 앱은 macOS 전용이다. `swiftc` 로 빌드하며 Apple silicon 의 macOS 14 이상에서 돈다.

1. JetBrains IDE 와 떠 있는 claude 세션을 모두 닫는다. 떠 있으면 setup 이 IDE 플러그인 설정과 공유 폴더를 남은 일로 미룬다.
2. 저장소를 받아 `install.sh` 를 돌린다. CLI 와 statusline 래퍼, 메뉴바 앱을 깐 뒤 `acm setup` 을 부른다.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ./install.sh
   ```

3. setup 이 계정을 추가할지 물으면 추가하고 그 계정으로 로그인한다. 지금 쓰는 `~/.claude` 는 그대로 첫 계정 `cl1` 이 된다.
4. 새 터미널을 열고 `claude` 를 친다. 남은 여유가 가장 큰 Claude 계정으로 뜬다.
5. `acm status` 로 계정마다 로그인과 사용량을 확인한다.

## 자세히 쓰려면

[사용 안내](GUIDE.md) 에 Claude 와 Codex 계정 더하기, 세션 띄우기, 아티팩트 모으기, Claude Code 업데이트 뒤 점검, 제거, 문제 해결을 절마다 하나씩 적었다. 기능마다 있는 상세 문서의 목록도 그 끝에 있다. 사용 안내와 상세 문서는 영어로 쓰여 있다.

## 본인 계정에만 쓴다

acm 은 Anthropic 이나 OpenAI 와 관계없는 비공식 도구다. Anthropic 은 [구독 요금제의 사용 한도가 평범한 개인 사용을 전제한다](https://code.claude.com/docs/en/legal-and-compliance)고 적고 있다. acm 은 구독을 여러 개 가진 한 사람이 쓰려고 만든 도구라서 여러 사람이 계정을 나눠 쓰는 데는 쓰지 않는다.

## 기여하거나 취약점을 알리려면

PR 을 올리기 전에 돌릴 검사와 지킬 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md) 에 영어로 있다. 보안 취약점은 공개 이슈 대신 [SECURITY.md](SECURITY.md) 에 적힌 대로 비공개로 신고한다.

## 라이선스

MIT 라이선스로 배포한다. 전문은 `LICENSE` 파일에 있다.
