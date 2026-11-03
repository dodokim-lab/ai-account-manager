# 나중에 할 것

이 문서는 acm 에 더할 일 가운데 미뤄 둔 것과 그 이유를 모은다. 다른 다중 계정 도구와 견줘 보고 정했다. 남은 약점을 메우는 일과 지금은 하지 않는 일, 아직 확인하지 못한 것으로 나눠 적는다.

## 다음에 할 순서

1. 아래 "아직 확인하지 못한 것" 을 확인한다. 지금 코드의 가정이 틀렸으면 다른 일보다 먼저 고친다.
2. Antigravity 는 계정을 나누지 않고 사용량만 보이게 붙인다.
3. Codex 의 Sites 발행도 대표 계정으로 모은다.
4. Linux 와 Claude Desktop 은 쓸 사람이 생기거나 Claude Code 쪽 지원이 바뀌면 한다.

## 남은 약점을 메우는 일

### Linux 에서도 돌게 한다

acm 은 이제 키체인을 읽지 않는다. Linux 의 Claude Code 가 토큰을 두는 `.credentials.json` 도 이미 계정마다 따로 둔다. 남은 일은 세 군데 있는데, Linux 에서 시험해 보지 못해서 미뤘다.

- 세션의 작업 폴더를 `lsof` 로 읽는 부분은 `/proc/<pid>/cwd` 로 바꾼다. 환경변수는 이미 `/proc/<pid>/environ` 을 읽는다.
- JetBrains 와 VS Code 계열의 설정 폴더는 `~/Library/Application Support` 대신 `~/.config` 아래에서 찾는다.
- 메뉴바 앱은 Linux 용으로 만들지 않고 `acm status` 로 대신한다.

### Claude Desktop 은 지원이 생길 때까지 기다린다

Claude Desktop 의 Code 탭은 `CLAUDE_CONFIG_DIR` 를 따르지 않는다는 보고가 있어서 acm 이 계정을 골라 붙일 수 없다. Claude Code 에 다중 계정 기능을 요청한 이슈도 아직 열려 있으니, 둘 중 하나가 바뀌면 다시 본다.[1]

### Antigravity 는 사용량만 보이게 붙인다

Antigravity CLI `agy` 는 계정을 하나밖에 둘 수 없어서 런처로는 붙이지 않는다. 설정 폴더를 바꾸는 환경변수가 없고 `GEMINI_DIR` 을 줘도 `~/.gemini` 를 그대로 썼다. `HOME` 을 바꾸면 새로 로그인해야 하는데, 로그인 정보는 macOS 키체인의 `antigravity` 항목 하나에 들어간다.[3] 두 번째 계정으로 로그인하면 이 항목을 덮을 것으로 보여 시험하지 않았다.

계정이 하나면 배정과 맥락 공유가 할 일이 없어서 남는 쓸모는 사용량을 한곳에서 보는 것뿐이다. `agy -p "/usage" --output-format json` 이 주간 창마다 남은 비율과 리셋 시각을 돌려주므로, 이 값을 메뉴바와 `acm status` 에 보기 전용 한 줄로 둔다. 계정을 나눠 둘 방법이 생기면 그때 Codex 와 같은 방식으로 붙인다.

### Codex 의 Sites 도 대표 계정으로 모은다

아티팩트 모으기의 쓸모는 다른 계정에서 발행한 문서를 대표 계정 하나에서 관리하는 데 있다. 공유 링크로는 문서를 열 수만 있고 고치거나 지우는 일은 소유 계정에서만 되므로, Codex 의 ChatGPT Sites 에도 같은 문제가 생긴다.

Plus 계정의 Codex CLI 에는 `sites` 플러그인이 기본으로 깔려 있었다.[4] 발행은 `sites.create_site` 로 사이트를 만들고 `sites.create_source_repository_write_credential` 로 잠깐 쓰는 git 토큰을 받은 뒤, 플러그인 스크립트가 만든 `dist` 를 Sites 의 git 서버로 push 하는 흐름이다. 기본 공개 범위는 소유자만이다. push 단계는 아직 끝까지 시험하지 못해서, 같은 사이트를 다른 세션에서 다시 push 해 갱신할 수 있는지도 미확인이다.

Claude 는 Artifact 도구를 한 번 부르면 발행이 끝나지만 Codex 발행 세션에는 셸과 git, node, 네트워크가 필요하다. 그래서 발행 세션을 좁은 도구로 묶는 지금 방식은 그대로 쓸 수 없어서 발행 계층을 도구별 어댑터로 나눠야 한다. 무료와 Go 요금제에서는 Sites 를 쓸 수 없으므로 대표 Codex 계정은 Plus 이상이어야 한다.[5]

## 지금은 하지 않는 일

아래 두 가지는 지금은 필요 없다고 봐서 하지 않는다. 쓰다가 아쉬워지면 다시 꺼낸다.

- 사용량을 시계열로 쌓아 소진 시점을 예측하고 임계값에서 알리는 일. claude-limits 와 Claudius 같은 메뉴바 앱이 이 기능을 내세운다.[2]
- 메뉴바 창에 한도로 멈춘 세션 목록과 이어 가기 버튼을 두는 일. 지금은 `acm resume` 과 iTerm 알림으로 충분하다.

## 아직 확인하지 못한 것

아래 네 가지는 지금 코드가 가정에 기대고 있어서, 확인하는 대로 코드나 문서를 고친다. 마지막 한 가지는 Codex 쪽이라 Codex 계정 두 개를 함께 쓸 수 있을 때 확인한다.

- VS Code 계열 확장이 `claudeProcessWrapper` 에 번들 claude 경로를 첫 인자로 넘기는지. 실제 확장으로는 돌려 보지 못했다.
- 만료된 토큰에서 `claude -p /usage` 가 토큰을 스스로 갱신하는지. 세션 없는 계정을 메뉴바 앱을 켠 채 하루 두고 `~/.acm/poll/<계정>.json` 에 `refresh_at` 이 한 번도 생기지 않으면 스스로 갱신하는 것이다. 그러면 haiku 로 띄우는 토큰 갱신을 뺀다.
- 하루 넘게 쓰지 않은 5h 한도 계정에서 `/usage` 가 Current session 줄을 보이는지. 보이지 않으면 그 계정이 다음에 쓸 때까지 한도 없음으로 보인다.
- 다른 Codex 계정에서 `acm codex resume` 으로 이어 갈 때 앞서 쓴 추론 기록을 그대로 쓰는지. Claude 가 다른 조직의 thinking 을 쓰지 못하는 것과 비슷한 제약이 있을 수 있다.

## 각주

[1] anthropics/claude-code 이슈 #30031 과 그 댓글. 2026-10-27 댓글까지 열려 있었다. https://github.com/anthropics/claude-code/issues/30031

[2] https://github.com/figueiredouc/claude-limits , https://github.com/Abd-K/claudius-claude-code-usage

[3] 2026-11-03, agy 1.4.8. `GEMINI_DIR` 을 바꿔도 `~/.gemini` 를 읽었다. `HOME` 을 임시 폴더로 바꾸자 로그인을 다시 요구했다. 키체인 항목 이름은 확인했지만 내용은 열어 보지 않았다. 같은 날 올라온 1.4.12 의 변경 기록에도 계정이나 설정 폴더 이야기는 없었다. 실행 파일에 든 `AGY_ACCOUNT` 는 플러그인으로 붙인 CLI 의 계정을 고르는 변수라 agy 로그인과는 상관없다.

[4] 2026-11-03, codex-cli 0.166.0. Plus 로 올린 계정에서 `codex plugin list` 에 `sites@openai-curated-remote` 1.1.2 가 설치되고 켜진 채로 나왔다. 시험 페이지로 사이트를 만들고 git 토큰을 받는 데까지 됐다.

[5] OpenAI 도움말 "Creating and managing ChatGPT Sites". https://help.openai.com/en/articles/20001339
