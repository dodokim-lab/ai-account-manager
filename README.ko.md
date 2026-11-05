# ai-account-manager

[English](README.md) | 한국어

Claude Code 나 Codex 구독을 여러 개 가져도 한 계정이 한도에 닿는 동안 다른 계정은 남는다. 맥락도 계정마다 따로다.

acm 은 이 계정들을 하나처럼 쓰게 하는 런처다. `claude` 와 `codex` 를 평소대로 치면 남은 여유가 가장 큰 계정으로 세션이 뜬다. 모든 계정이 같은 맥락을 쓴다. [Orca](https://github.com/stablyai/orca) 뒤에서도 돈다.

![왼쪽 터미널에서 claude 와 codex 를 치면 acm 이 고른 계정이 찍힌다. 오른쪽 acm 메뉴바 창에는 Claude 계정 세 개와 Codex 계정 두 개가 5시간과 주간 사용량 게이지로 보인다. 도구마다 고른 계정에는 테두리가 쳐져 있다. 터미널 아래에는 Claude 계정 cl1 과 cl2, cl3 이 ~/.claude 한 곳을 가리킨다. Codex 계정 cx1 과 cx2 는 ~/.codex 한 곳을 가리킨다.](docs/readme/hero.svg)

## acm 은 이런 점이 다르다

- 계정을 바꾸지 않아도 세션마다 여유가 가장 큰 계정으로 뜬다.
- 모든 계정이 메모리와 히스토리, 설정, 스킬을 같이 쓴다.
- 로그인 토큰을 읽지도 옮기지도 않는다.
- Claude Code 와 Codex 를 한 도구로 다룬다.
- Claude 아티팩트를 한 계정에 모은다.
- [Orca 뒤에서 돌아서](docs/orca.md) Orca 가 띄우는 세션도 같은 방식으로 계정과 맥락을 받는다.

자세한 설명과 다른 도구와 견준 표는 [비슷한 도구와 무엇이 다른가](docs/comparison.md) 에 있다.

## 빠른 시작

macOS 와 Linux 에서 돌고 Linux 지원은 새로 넣었다. `python3` 와 `jq`, `claude` 가 있어야 한다. Codex 계정에는 `codex` 가, macOS 메뉴바 앱에는 `swiftc` 가 더 필요하다. 자세한 것은 사용 안내의 [Install](GUIDE.md#install) 에 있다.

1. JetBrains IDE 와 떠 있는 claude 세션을 모두 닫는다. 떠 있으면 setup 이 일부 설정을 뒤로 미룬다.
2. 저장소를 받아 `install.sh` 를 돌린다. acm 을 깔고 `acm setup` 을 부른다.

   ```bash
   git clone https://github.com/dodokim-lab/ai-account-manager.git
   cd ai-account-manager
   ./install.sh
   ```

3. setup 이 물으면 계정을 추가하고 로그인한다. 지금 쓰는 `~/.claude` 는 첫 계정 `cl1` 이 된다.
4. 새 터미널을 열고 `claude` 를 친다.
5. `acm status` 로 계정마다 로그인과 사용량을 확인한다.

## 자세히 쓰려면

[사용 안내](GUIDE.md) 에 계정과 세션, 아티팩트 모으기, 제거, 문제 해결을 절마다 적었다. 기능별 상세 문서의 목록도 거기 있다. 사용 안내와 상세 문서는 영어다.

## 본인 계정에만 쓴다

acm 은 Anthropic 이나 OpenAI 와 관계없는 비공식 도구다. Anthropic 은 [구독 요금제의 사용 한도가 평범한 개인 사용을 전제한다](https://code.claude.com/docs/en/legal-and-compliance)고 적는다. 그래서 acm 은 한 사람이 자기 계정에만 쓰고 여러 사람이 계정을 나눠 쓰는 데는 쓰지 않는다.

## 기여하거나 취약점을 알리려면

PR 을 올리기 전에 [CONTRIBUTING.md](CONTRIBUTING.md) 를 읽는다. 보안 취약점은 [SECURITY.md](SECURITY.md) 에 적힌 대로 비공개로 신고한다.

## 라이선스

MIT 라이선스다. 전문은 `LICENSE` 파일에 있다.
