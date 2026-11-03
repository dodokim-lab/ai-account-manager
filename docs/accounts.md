# 계정 관리

이 문서는 계정 디렉터리가 무엇을 따로 두고 무엇을 같이 쓰는지, 로그인 토큰을 acm 이 어떻게 다루는지 적는다. Codex 계정은 마지막 절에 따로 적었다. 계정을 더하는 명령만 필요하면 README 로 충분하다.

## 계정은 add 하고 로그인한다

계정 id 는 도구 약자에 번호를 붙여 짓는다. Claude 계정은 `cl1`, `cl2`, Codex 계정은 `cx1`, `cx2` 처럼 쓰고, 추가 계정 폴더 이름도 이 id 를 따른다. 새 번호는 그 도구의 계정 수 다음부터 매겨서, 옛 id `acc1`, `acc2` 가 남은 설치에서는 세 번째 계정이 `cl3` 이 된다.

기본 계정 `cl1` 은 지금 쓰는 `~/.claude` 이고 따로 할 일이 없다. 두 번째 계정부터 추가하는데, `acm setup` 이 묻는 대로 답해도 되고 아래처럼 직접 해도 된다.

```bash
acm add cl2                 # ~/.claude-cl2 를 만든다
acm -a cl2 auth login       # 그 계정으로 로그인
acm label cl2 personal      # 화면에 보일 이름. 기본은 이메일 앞부분
acm status                   # 로그인과 사용량 확인
```

`auth login` 은 브라우저에서 승인하는데, 브라우저가 claude.ai 에 이미 다른 계정으로 로그인돼 있으면 그 계정으로 승인된다.[3] 그러면 두 acm 계정이 같은 Claude 계정이 되고, 나눠 띄워도 한도가 늘지 않는 데다 대표 계정의 여유를 다른 이름으로 쓰게 된다. 그래서 acm 은 같은 계정으로 로그인한 acm 계정 가운데 하나만 자동 배정에 남기고, 묶음에 대표 계정이 있으면 대표 계정을 남긴다. `acm status` 와 `acm setup` 이 이 일을 알리면, 시크릿 창처럼 그 계정으로 claude.ai 에 로그인한 브라우저에서 인증 주소를 열어 다시 로그인한다. 같은 계정인지는 `.claude.json` 의 계정 UUID 로 가르고, UUID 가 없으면 이메일로 가른다.

서로 다른 Claude 계정이 한 조직에 묶여 있으면 `acm status` 가 알린다. 개인 구독은 계정마다 자기 조직이 따로 있어서, 묶였다면 Team 이나 Enterprise 처럼 조직 한도를 나눠 쓰는 계정일 수 있다. 조직 계정끼리 한도를 나눠 쓴다는 보고는 Anthropic 이 확인하지 않아서, 알리기만 하고 배정에서는 빼지 않는다.[4] 조직은 `.claude.json` 의 `organizationUuid` 로 견준다.

## 계정 디렉터리에는 계정마다 달라야 하는 것만 둔다

계정 디렉터리에는 계정마다 달라야 하는 것만 실제 파일로 둔다. `.claude.json` 과 `.credentials.json`, `backups`, `jobs`, `telemetry`, `statsig`, `daemon*` 가 그것이고, 나머지는 전부 `~/.claude` 를 가리키는 링크다. `.claude.json` 에는 기본 계정의 `mcpServers` 와 개인 설정, 프로젝트 신뢰 정보를 복사해 넣는다. 개인 설정은 자동 업데이트와 테마, 편집기 모드 같은 값이고, 맞출 때마다 기본 계정 값으로 덮어서 기본 계정에 없는 값은 지운다. 그래서 추가 계정에서 `/config` 로 바꾼 개인 설정은 다음에 띄울 때 돌아가니, 설정은 기본 계정에서 바꾼다. 추가 계정의 `.claude.json` 을 읽지 못하면 그 계정 세션이 쓰는 중이거나 깨진 파일이라서, 덮어쓰지 않고 그때는 건너뛴다. 덮어쓰면 로그인 정보와 프로젝트 기록이 지워진다. acm 은 세션을 띄울 때마다 그 계정을 이렇게 맞추고, 링크가 어긋났을 때만 `acm sync --fix` 로 다시 맞추면 된다.

## projects 와 skills, hooks 는 공유 폴더에 둔다

`projects` 와 `skills`, `hooks` 는 실체를 `~/.acm/shared` 에 두고 `~/.claude` 쪽에는 그곳을 가리키는 링크를 둔다. 세션 기록과 자동 메모리, 개인 스킬, 훅 스크립트가 이 안에 있어서 세션이 직접 고치는 일이 잦다. Claude Code 는 링크를 따라간 실제 경로로 쓰기를 판정한다. 그 경로가 세션 자기 설정 폴더가 아닌 `.claude` 폴더 안이면 민감 파일로 보고 auto 모드에서도 확인을 묻는다.[1][2] 그래서 실체가 `~/.claude` 안에 있으면 추가 계정 세션은 이 세 폴더를 고칠 때마다 확인을 묻고, 허용 규칙이나 `--add-dir` 로는 풀리지 않는다.[2]

`CLAUDE.md` 나 `settings.json` 같은 파일은 옮기지 않는다. `Write` 와 `Edit` 는 링크 파일에 쓰지 않고 실제 경로로 다시 쓰라고 돌려보내서, 파일까지 옮기면 기본 계정에서 고칠 때도 이 왕복이 생긴다.[2]

계정을 처음 추가한 뒤 한 번, claude 세션을 모두 닫고 `acm sync --fix` 를 돌리면 옮긴다. 옮길 폴더가 늘어난 판으로 바꾼 뒤에도 같은 방법으로 한 번 더 돌린다. 떠 있는 claude 프로세스가 있거나 `~/.acm/shared` 에 같은 이름이 이미 있으면 옮기지 않고 알린다. 옮기기 전에는 세션을 띄울 때마다 한 줄로 알린다.

## 로그인 토큰은 Claude Code 만 다룬다

로그인 토큰은 macOS 키체인에 계정 디렉터리마다 다른 이름으로 들어가고, acm 은 이 토큰을 읽지 않는다. 사용량은 그 계정의 Claude Code 에 `claude -p /usage` 를 시켜 읽어서, 토큰은 Claude Code 안에서만 쓰인다. 메뉴바 창에 남은 조회 실패 사유는 그 계정 세션이 statusline 으로 사용량을 새로 기록하면 지운다.

세션이 없는 계정은 토큰이 8시간쯤 뒤 만료된다. `/usage` 가 만료된 토큰을 스스로 갱신하는지는 미확인이라, `/usage` 가 429 가 아닌 이유로 실패하면 acm 이 그 계정으로 `claude -p` 를 뒤에서 한 번 띄운다. 이때 훅과 플러그인, MCP, 도구를 모두 끈 채 haiku 에 짧은 요청 하나만 보내고 세션 기록은 남기지 않는다. 한 번에 드는 양은 실측으로 입력 2,973 토큰이었다. 토큰은 acm 이 아니라 Claude Code 가 평소처럼 갱신하고, 같은 계정 세션이 떠 있어도 잠금을 잡고 갱신하므로 꼬이지 않는다.

갱신을 띄우면 메뉴바 창에 "토큰 갱신을 띄움" 이 뜨고 acm 은 90초 뒤에 다시 읽는다. 갱신은 30분에 한 번까지만 띄우고, 그 사이에 또 실패하면 창에 `acm -a <계정> auth login` 안내와 다음 갱신 시각이 뜬다. 안내가 이어지면 그 계정으로 다시 로그인한다.

갱신을 띄운 뒤에도 조회가 실패하면 acm 은 그 계정의 로그인이 풀린 것으로 본다. `acm status` 와 `acm setup` 이 다시 로그인하라고 알리고, 한도에 걸린 세션을 이어 갈 때도 그 계정으로는 보내지 않는다. 다시 로그인하면 `.claude.json` 이 바뀌니, 다음 조회를 기다리지 않고 바로 풀린 것으로 보지 않는다.

## 안 쓰는 계정은 rm 으로 뺀다

안 쓰는 계정은 `acm rm <계정>` 으로 목록에서 뺀다. 그 계정으로 돌고 있는 세션이 있으면 거부하고, Claude 기본 계정 `cl1` 은 뺄 수 없다. 뺀 계정이 아티팩트를 모으는 대표 계정이었으면 대표 지정도 지우고, 그 뒤로는 첫 계정으로 모은다. 디렉터리와 키체인 항목은 남기고 완전히 지우는 명령을 알려 준다.

## Codex 계정은 ~/.codex 를 root 로 둔다

Codex 기본 계정 `cx1` 은 지금 쓰는 `~/.codex` 이고 추가 계정은 `CODEX_HOME` 을 `~/.codex-<id>` 로 두고 띄운다. Codex 는 `CODEX_HOME` 이 가리키는 폴더를 자기 설정 폴더로 쓴다. 처음 `acm add --codex` 를 치면 `cx1` 을 등록하고 `acm codex` 로 처음 띄울 때도 등록돼 있지 않으면 먼저 등록한다.

```bash
acm add --codex cx2              # ~/.codex-cx2 를 만든다
acm -a cx2 login --device-auth   # 그 계정으로 로그인
acm rm cx2                       # 목록에서 뺀다. 폴더와 로그인 정보는 남긴다
```

추가 계정 폴더에는 계정마다 달라야 하는 것만 실제 파일로 둔다.

- `auth.json` 은 로그인 정보다.
- `app-server-daemon` 과 `app-server-control` 은 그 계정으로 뜬 앱 서버 데몬의 자리다. 같이 쓰면 다른 계정 세션이 그 데몬에 붙어 그 계정으로 돈다.
- `models_cache.json` 은 요금제마다 쓸 수 있는 모델이 달라서 따로 둔다.
- `installation_id` 와 `log`, `cache`, `tmp`, `.tmp` 는 그 계정의 실행 흔적이다.

나머지는 모두 `~/.codex` 를 가리키는 링크다. 세션 기록 `sessions` 와 상태 DB, `config.toml`, 스킬, 훅, 플러그인이 여기 들어서, 어느 Codex 계정으로 떠도 같은 세션 목록과 설정을 본다. Codex 는 링크한 `config.toml` 을 고칠 때 링크를 따라가 원래 파일에 써서 링크가 실제 파일로 바뀌지 않는다.[5] SQLite 는 링크를 따라간 원래 DB 옆에 WAL 파일을 만들어서, DB 를 링크로 같이 써도 된다.[6] 그래서 Claude 계정처럼 공유 폴더로 옮기는 일은 없다.

훅 신뢰 기록은 계정마다 따로 생긴다. Codex 는 신뢰한 훅을 `config.toml` 에 `<hooks.json 경로>:session_start:0:0` 같은 키로 적는다. 추가 계정에서는 이 경로가 링크를 풀지 않은 `~/.codex-cx2/hooks.json` 이라 같은 훅이 신뢰 전으로 보인다. 신뢰 해시는 경로와 상관없이 훅 내용으로만 정해진다.[7] 그래서 acm 은 계정 링크를 맞출 때 `~/.codex` 키의 기록을 추가 계정 키로 옮겨 적는다. 이미 신뢰한 같은 내용만 신뢰하는 셈이고, 훅 내용이 바뀌면 양쪽 모두 다시 묻는다. 계정 키의 기록이 이미 있으면 해시가 달라도 건드리지 않는다. 같은 표를 두 번 적으면 `config.toml` 이 깨져 Codex 가 뜨지 않기 때문이다.

`login --device-auth` 는 화면에 나온 주소를 브라우저에서 열고 코드를 넣는다. 브라우저가 다른 ChatGPT 계정에 로그인돼 있으면 그 계정으로 묶이니 시크릿 창에서 연다. 같은 ChatGPT 계정으로 로그인한 acm 계정은 Claude 와 같은 규칙으로 하나만 자동 배정에 남긴다. 같은 계정인지는 이메일과 ChatGPT 계정 ID 를 함께 견준다. 팀 워크스페이스는 구성원이 계정 ID 를 같이 쓰기 때문이다.

`CODEX_HOME=~/.codex-<id> codex login` 으로 먼저 로그인해 둔 폴더는 `acm add --codex` 만 쳐도 계정으로 등록한다. 등록하지 않은 `~/.codex-*` 폴더 가운데 `auth.json` 이 있는 폴더가 하나뿐일 때다. 그 폴더에 Codex 가 이미 만든 세션 기록이나 DB 가 있으면 `.acm-drift` 로 옮기고 그 자리를 `~/.codex` 로 링크한다. DB 를 옮길 때는 아직 합치지 않은 기록이 든 WAL 파일도 함께 옮긴다.

acm 은 `auth.json` 을 읽지 않고 있는지만 본다. 이메일과 요금제, ChatGPT 계정 ID 는 그 계정으로 띄운 `codex app-server` 에 물어 받고 `accounts.json` 에 적는다. 로그인 직후 처음 `acm status` 를 치면 이 조회를 기다렸다가 보인다. 로그아웃해서 `auth.json` 이 없어지면 이 세 값을 지운다. 세션 없이 둔 계정의 토큰이 만료돼도 app-server 조회가 토큰을 스스로 갱신한다.[8] Codex 기본 계정은 목록에서 빼도 `~/.codex` 를 건드리지 않는다.

## 각주

[1] 2026-10-30. cl2 세션의 메모리 `Edit`·`Write` 8건이 모두 `reasonCode: safetyCheck` 로 확인을 물었고, 같은 세션의 Bash·Read 는 묻지 않았다(세션 기록 `permissionDecision`). 보호 경로와 링크 판정은 https://code.claude.com/docs/en/permission-modes.md#protected-paths 와 https://code.claude.com/docs/en/permissions.md#symlinks 에 있다. 예외가 세션 자기 설정 폴더 기준이라는 것은 문서에 없고 이 실측에서 추론했다.

[2] 2026-10-31, Claude Code 2.1.314. auto 모드 `-p` 세션으로 쓰기를 쟀다. 기본 계정은 `~/.claude/state` 와 `~/.claude/skills` 에 묻지 않고 썼고, cl2 가 같은 폴더에 링크로 쓰면 둘 다 민감 파일로 거부됐다. cl2 자기 설정 폴더의 `backups` 와 실체를 옮긴 `projects` 안은 메모리 폴더 안팎 모두 통과했다. `--allowedTools` 로 `~/.claude/**` 쓰기를 허용하거나 `--add-dir ~/.claude` 를 붙여도 같은 이유로 거부됐다. 링크 파일에 쓰면 "it is a symbolic link" 라며 실제 경로를 쓰라고 돌려보냈고, 링크 폴더 안에 새 파일을 만드는 것은 그대로 됐다.

[3] 2026-11-03. claude.ai 에 기본 계정으로 로그인한 브라우저에서 `acm -a cl2 auth login` 을 승인하자, cl2 의 `.claude.json` 에 기본 계정과 같은 이메일과 계정 UUID 가 들어갔다.

[4] anthropics/claude-code 이슈 #41886. 직원 답 없이 자동으로 닫혔다. https://github.com/anthropics/claude-code/issues/41886

[5] 2026-11-03, codex-cli 0.165.0. 임시 폴더에서 `config.toml` 을 링크로 둔 `CODEX_HOME` 으로 `codex features enable` 을 돌리자, 링크는 그대로 남고 링크가 가리키는 원래 파일에 기능 설정이 적혔다.

[6] 2026-11-03, SQLite 3.43.2. 링크로 연 WAL 모드 DB 에 쓰자 `-wal` 과 `-shm` 파일이 원래 DB 옆에만 생겼고, 두 경로로 연 연결이 같은 행을 읽었다.

[7] 2026-11-03, codex-cli 0.165.0. app-server 의 `hooks/list` 로 신뢰 상태를 읽었다. cx2 에서는 두 훅 모두 untrusted 였다. 임시 폴더에 `~/.codex` 의 해시를 다른 경로 키로 적자 trusted 가 됐고, 훅 명령을 바꾸자 modified 로 바뀌었다.

[8] 2026-11-03, codex-cli 0.166.0. 세션 없이 둔 cx2 에서 `codex plugin list` 가 `token_expired` 로 실패했다. 이어서 `acm poll --force` 의 app-server 조회가 성공했다. 그 뒤로는 같은 `codex plugin list` 가 통과했다.
