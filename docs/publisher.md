# 아티팩트 모으기와 화면 제어

이 문서는 여러 계정 세션이 아티팩트를 한 계정으로 모아 발행하는 방식과, 대표 계정이 아닌 세션이 브라우저를 다루는 방식을 적는다. 발행 세션의 권한을 바꾸거나 발행이 막혔을 때 읽는다.

## 아티팩트는 한 계정으로 모은다

아티팩트는 그 세션이 붙은 계정 소유로 발행된다. 그래서 계정을 옮겨 가며 쓰면 아티팩트가 계정마다 흩어지고, 브라우저에 로그인한 계정과 다른 쪽 것은 열리지 않는다. `acm publisher on` 을 켜면 다른 계정 세션은 아티팩트를 대표 계정의 발행 전용 세션에 맡겨 발행한다. 켜는 것은 맡기는 방식을 정할 뿐이고, 발행 세션은 맡길 때만 뜬다. 아티팩트는 Claude 기능이라 대표 계정은 Claude 계정만 고를 수 있고 Codex 세션에는 이 규칙을 붙이지 않는다.

```bash
acm publisher on              # 켠다. 발행 세션은 맡길 때 뜬다
acm publisher status          # 켜짐 여부와 대표 계정, 세션 상태
acm publisher check           # 지금 발행을 맡길 수 있는지. 발행 세션이 없으면 띄운다
acm publisher account cl1    # 모을 계정. 기본은 첫 Claude 계정
acm publisher model claude-sonnet-5-5 high  # 발행 세션 모델과 effort
acm publisher stop            # 떠 있는 발행 세션만 끈다. 켜짐은 그대로다
acm publisher off             # 끄고 각 세션이 자기 계정으로 발행하게 되돌린다
```

켜 두면 acm 이 다른 계정 세션을 띄울 때 두 가지를 붙인다. 하나는 그 세션에서 Artifact 도구를 빼는 `--disallowedTools Artifact` 이고, 다른 하나는 아티팩트를 SendMessage 로 `acm-publisher` 세션에 맡기라는 운영 규칙을 담은 `--append-system-prompt` 다. 세션은 HTML 파일을 쓰고 `acm publisher check <파일>` 로 올린 뒤 올린 경로를 보내며, 발행 세션이 돌려준 URL 을 사용자에게 전한다.

## 발행 세션은 tmux 에서 좁은 권한으로 돈다

발행 세션은 tmux 의 `acm-publisher` 에서 `claude-sonnet-5-5`, effort high 로 돈다. tmux 는 발행 세션을 화면 없이 뒤에 띄워 두는 데만 쓰고, 쓰는 터미널이 tmux 일 필요는 없다. iTerm 이나 IDE 터미널, 다른 claude 세션의 Bash 어디서 `check` 를 불러도 tmux 서버가 없으면 그 자리에서 뜬다. 들여다볼 때는 아무 터미널에서 `tmux attach -t acm-publisher` 를 친다. Artifact 도구 규칙을 판단하고 기존 아티팩트를 갱신하는 자리라 작은 모델로 내리지 않는다. 모델은 alias 가 아니라 정확한 ID 로 고정한다. 이 값을 대신 점검해 주는 감사가 없으니, 쓰던 모델이 은퇴하거나 같은 계열에 새 세대가 나오면 `bin/acm` 의 `PUBLISHER_MODEL` 을 직접 바꾼다. 쓸 수 있는 도구는 Read 와 Artifact, SendMessage, ListAgents 뿐이고 MCP 서버는 하나도 붙이지 않는다. Artifact 에만 허용 규칙을 걸어 확인 없이 발행한다. 다른 세션의 메시지를 받고 움직이는 세션이라 할 수 있는 일을 이 범위로 좁혀 두었다.

## 발행 세션은 inbox 에 올린 파일만 읽는다

발행 세션은 다른 세션의 요청을 묻지 않고 처리한다. 그래서 프롬프트 인젝션을 당한 세션이 `~/.ssh` 같은 파일을 발행해 달라고 보낼 수 있다. 이를 막으려고 발행 세션이 읽고 발행하는 로컬 파일을 `~/.acm/publisher/inbox` 아래와 그 세션의 scratchpad 아래로 묶는다.

갱신할 때는 Artifact read 가 저장한 라이브 판 사본도 읽는다. Artifact 도구는 라이브 판을 끝까지 읽은 세션에만 갱신을 허용하는데, 발행 세션은 요청마다 새로 떠서 라이브 판을 본 적이 없다. 그래서 이 사본을 읽지 못하면 내용이 바뀐 갱신은 모두 거절된다.[4] 사본을 끝까지 읽은 뒤에는 요청에 온 파일을 그대로 발행한다. 발행 세션에는 파일을 고치는 도구가 없으니 라이브 판과 합치는 일은 요청한 세션이 맡는다.

다른 세션은 `acm publisher check <HTML 파일> [추가 파일...]` 로 파일을 inbox 에 올리고, 출력에 나온 올린 경로를 발행 세션에 보낸다. 올릴 때 아래 파일은 거절한다.

- 숨은 파일과, `~/.ssh` 나 `~/.claude`, `~/.acm` 처럼 홈 바로 아래 숨은 폴더에 든 파일
- `~/Library` 아래 파일
- 웹 파일이 아닌 확장자. html 과 md, css, js, json, 이미지, 글꼴, 동영상, pdf, txt, csv 만 받는다
- 16MB 를 넘는 파일

링크는 가리키는 파일로 판단한다. 홈은 경로 문자열이 아니라 폴더 자체로 알아봐서, `/users/<이름>` 처럼 대소문자를 바꾸거나 `/System/Volumes/Data` 로 시작하는 경로로 써도 거절된다. 검사한 파일은 한 번만 열어서, 연 파일의 실제 경로로 다시 검사한 뒤 그 파일에서 복사한다. 검사와 복사 사이에 경로가 다른 파일을 가리키게 바뀌어도 바뀐 파일은 올라가지 않는다. 올린 파일은 나만 읽게 0600 으로 두고, inbox 는 0700 이다. 추가 파일은 첫 파일과 같은 폴더 아래에 있어야 하고, 올린 폴더에서도 같은 상대 위치에 놓여 페이지의 상대 링크가 그대로 맞는다. 올린 폴더는 하루가 지나면 다음에 올릴 때 지운다.

범위는 PreToolUse 훅이 지킨다. acm 은 발행 세션을 띄울 때 `--settings` 로 `acm publisher guard` 훅을 더하고, 이 훅이 모든 도구 호출을 본다. 훅이 지키는 범위는 아래와 같다.

- 통과하는 도구는 Read 와 Artifact, SendMessage, ListAgents, ToolSearch 뿐이다. ToolSearch 로 불러온 ArtifactData 같은 다른 도구도 막는다.
- Read 와 Artifact 의 로컬 경로는 inbox 나 그 세션의 scratchpad 안이어야 한다. `..` 가 든 경로는 받지 않고, 상대 경로는 작업 폴더와 `root` 어느 쪽 기준으로 풀어도 범위 안이어야 한다.
- Read 는 그 세션의 라이브 판 사본도 받는다. 사본 폴더는 훅 입력의 `transcript_path` 옆 `<세션 ID>/tool-results/` 로 정하고, 그 폴더 바로 아래에서 이름이 `artifact-` 로 시작하는 파일만 통과시킨다. 다른 세션의 사본과 하위 폴더, 밖을 가리키는 링크는 막는다. 사본을 발행 경로로 쓰는 것도 막는다.
- Artifact 는 publish 와 read 만 쓴다. force 와 capabilities, read 의 out_dir 도 막는다.
- inbox 가 링크로 바뀌어 있으면 아무 파일도 통과시키지 않는다.

훅이 2 가 아닌 종료 코드로 끝나면 Claude Code 는 도구를 그대로 실행한다. 그래서 훅은 입력을 읽다 실패해도 막고, 명령 끝에 `|| exit 2` 를 붙여 acm 이 import 단계에서 죽어도 막힌다. 다른 설정의 `disableAllHooks` 가 이 훅을 끄지 못하게 같은 `--settings` 에서 false 로 둔다. 시스템 프롬프트에도 같은 범위를 ROLE.md 뒤에 붙인다.

Claude Code 의 `--restricted` 도 파일 도구를 작업 폴더로 묶지만 쓰지 않았다. 이 모드로 띄운 세션은 메시지 소켓을 열지 않아서 SendMessage 를 받지 못한다.[3]

## 발행 세션은 필요할 때만 떠 있다

다른 계정 세션이 발행을 맡기기 전에 부르는 `acm publisher check` 가 발행 세션이 없으면 띄우고, Claude Code 세션 목록에 올라와 메시지를 받을 수 있을 때까지 기다린다. 같은 tmux 창에서 도는 감시가 5초마다 `~/.claude/sessions/<pid>.json` 의 `status` 와 `statusUpdatedAt` 을 읽어 쉬는 시간을 잰다. 일을 마치고 30초 동안 새 요청이 없으면 세션을 끄고, 띄운 뒤 일을 한 번도 받지 않으면 5분에 끈다.[1] `check` 는 부를 때마다 시각을 남겨서, `check` 와 그 뒤의 SendMessage 사이에 세션이 꺼지지 않게 한다. 기준은 `ACM_PUBLISHER_IDLE` 과 `ACM_PUBLISHER_IDLE_MAX` 로 바꾸고, 끈 기록은 `~/.acm/publisher/watch.log` 에 남는다. 한 번만 돌고 끝나는 `claude -p` 로 발행하지 않는 것은 그 모드에 Artifact 도구가 없어서다.[1]

tmux 서버를 처음 띄운 프로세스의 환경변수는 서버에 남는다. 그래서 다른 claude 세션이 `check` 를 부르면 그 세션의 세션 ID 와 메시지 소켓이 발행 세션에 그대로 넘어갔다.[2] 부른 세션이 끝나면 이 값은 없는 소켓을 가리키게 된다. 지금은 tmux 를 부를 때와 창 안의 명령 양쪽에서 claude 세션에 묶인 값을 빼고 띄운다. 토큰 갱신용 `claude -p` 도 같은 값을 빼고 띄운다.

## 승인 범위는 ROLE.md 에 둔다

발행 세션의 역할과 승인 범위는 `~/.acm/publisher/ROLE.md` 에 둔다. 다른 세션의 요청으로 외부에 발행하는 상시 승인이라서 본인이 범위를 정해야 하고, 이 파일이 없으면 acm 은 발행 세션을 띄우지 않는다. `acm setup` 이 기본 문안을 보여 주고 동의를 받아 쓰며, 범위를 바꾸려면 이 파일을 고친다. 기본 문안은 아래를 담는다.

- 같은 Mac 의 다른 Claude 세션이 SendMessage 로 요청한 발행과 갱신은 묻지 않고 진행한다는 승인
- 범위는 요청한 세션이 inbox 에 올린 파일을 읽어 새로 발행하거나 지정한 url 을 갱신하고, 결과 URL 을 요청한 세션에 답하는 데까지라는 것
- 아티팩트 삭제와 공유 범위 변경, 파일 수정은 하지 않고, Artifact 도구 규칙에 걸리는 내용은 발행하지 않는다는 것

예전 기본 문안으로 쓴 ROLE.md 는 고치지 않아도 된다. 파일 범위는 acm 이 ROLE.md 뒤에 따로 붙이고 훅이 지킨다.

## 대표 계정에는 발행에 쓸 여유를 남긴다

발행 모으기가 켜져 있으면 acm 은 대표 계정을 5h 70% 또는 Week 85% 부터 자동 배정에서 뺀다. 아티팩트 발행에는 Week 15% 면 충분하다고 보고 정한 값이다. 그 아래에서는 대표 계정도 다른 계정과 똑같이 견줘서 세션을 계정마다 고르게 나눈다. 모든 계정이 막혀도 대표 계정은 마지막까지 남긴다. `acm -a` 로 직접 지정하면 기준과 상관없이 뜬다. 한도에 걸린 세션을 이어 갈 때도 같은 기준을 지킨다. 기준은 `ACM_RESERVE_FIVE_HOUR_CAP` 과 `ACM_RESERVE_SEVEN_DAY_CAP` 으로 바꾼다. 메뉴바 창과 위젯은 대표 계정에 `대표` 태그를 달고, 자동 배정에서 빠지면 태그가 주황으로 바뀐다. 발행 모으기를 끄면 여유를 남기지 않으니 태그도 사라진다.

그래도 대표 계정이 한도에 닿으면 발행을 멈춘다. 다른 계정으로 발행하면 아티팩트가 다시 흩어지기 때문이다. 다른 계정 세션은 발행을 맡기기 전에 `acm publisher check` 를 돌리고, 실패하면 맡기지 않고 리셋 시각을 사용자에게 전한다. `check` 는 대표 계정의 사용량을 그 자리에서 새로 읽고, 발행 세션 모델인 `claude-sonnet-5-5` 에 걸리는 Sonnet only 주간 한도도 함께 본다. 발행 세션은 실행 중 세션 수에 넣지 않아서 배정에는 영향이 없다.

## 다른 계정 세션의 화면 제어는 aside 로 돌린다

Claude in Chrome 은 claude.ai 계정 단위로 붙는데, Chrome 확장은 한 번에 한 계정에만 로그인한다. 확장을 대표 계정으로 두면 다른 계정 세션은 Chrome 에 연결되지 않는다.

그래서 acm 은 대표 계정이 아닌 세션에 화면 제어는 aside MCP 로 하라는 운영 규칙을 함께 붙인다. aside 는 Aside 자체 계정으로 돌아서 어느 Claude 계정 세션에서든 같은 브라우저를 쓴다. 기본 계정의 MCP 목록에 `aside` 가 없으면 이 규칙은 붙지 않는다.

Aside Browser 에 로그인되지 않은 사이트는 세션이 비밀번호를 대신 넣지 않고 사용자에게 직접 로그인해 달라고 한다. 한 번 로그인해 두면 모든 계정 세션이 그 로그인을 같이 쓴다.

## 각주

[1] 2026-10-31, Claude Code 2.1.314. `claude -p` 의 도구 목록에는 haiku 와 sonnet 모두 Artifact 가 없었다. 기준을 15초와 40초로 줄인 시험용 발행 세션은 `check` 1초 안에 떴고, 일 없이 40초에 꺼졌다. 메시지 한 건을 처리한 뒤에는 15초 기준에 꺼졌고, 일을 마치고 11초에 `check` 를 부르자 그로부터 20초 뒤에 꺼졌다. 감시가 5초 간격이라 기준보다 최대 5초 늦게 끈다.

[2] 2026-11-02, tmux 3.8. tmux 서버가 없는 상태에서 claude 세션의 Bash 로 `acm publisher check` 를 불렀다. 발행 세션은 자기 세션 ID 와 소켓으로 따로 등록됐지만, 프로세스 환경에는 부른 세션의 `CLAUDE_CODE_SESSION_ID` 와 `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_CHILD_SESSION=1`, `CLAUDECODE=1` 이 남아 있었다. 고친 뒤 같은 방법으로 띄우면 `ACM_ACCOUNT` 와 `ACM_LABEL`, `ACM_ROLE` 만 남는다.

[3] 2026-11-02, Claude Code 2.1.316. `--restricted` 로 띄운 haiku 세션은 작업 폴더 밖 파일의 Read 와 Artifact publish 를 모두 막았다. 하지만 세션 기록에 `messagingSocketPath` 가 없어 ListAgents 에 보이지 않았고, SendMessage 도 닿지 않았다. 같은 명령에서 `--restricted` 만 빼면 소켓이 생겼다. 훅을 붙인 발행 세션은 inbox 파일을 읽었고, `~/.acm/accounts.json` 은 범위 밖이라며 호출하지 않았다. 그 세션의 훅 명령에 같은 입력을 넣으면 `accounts.json` 은 종료 코드 2 로 막혔다.

[4] 2026-11-03, Claude Code 2.1.316. 발행 세션이 기존 덱을 갱신하려 하자 Artifact 도구는 라이브 판을 본 적이 없다며 발행을 거절했다. 같은 응답이 라이브 판 전체를 `~/.claude/projects/<작업 폴더>/<세션 ID>/tool-results/artifact-<id>-<판>.html` 에 저장했다고 알렸지만, 훅이 그 파일의 Read 를 inbox 밖이라며 막았다. 같은 판에서 PreToolUse 훅 입력에는 `transcript_path` 가 `<세션 ID>.jsonl` 경로로 들어왔다. 고친 훅에 막혔던 입력을 다시 넣으면 종료 코드 0 으로 통과하고, 다른 세션의 기록 경로를 넣으면 2 로 막힌다.
