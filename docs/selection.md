# 계정 배정과 사용량

이 문서는 acm 이 세션마다 어느 계정을 고르는지, 그 판단에 쓰는 사용량을 어디서 모으는지 적는다. 기준값을 바꾸거나 배정이 예상과 다를 때 읽는다. Codex 계정의 배정과 사용량은 마지막 절에 따로 적었다.

## 빠른 시작

1. `acm poll --force` 로 모든 계정의 사용량을 지금 읽는다.
2. `acm status` 로 계정마다 사용률과 모델별 주간 한도를 본다.
3. `acm pick` 으로 고를 계정과 점수를 본다. 다른 모델로 띄울 때는 `acm pick --model fable` 처럼 모델을 붙인다.

## 계정은 점수가 가장 높은 순으로 고른다

기본 분배 방식 `usage` 는 계정마다 점수를 매겨 가장 높은 계정을 고른다. 점수는 5h 남은 여유에 주간 속도 비율을 곱한 값이고, 5h 한도가 없는 계정은 5h 자리를 100 으로 본다. 주간 속도 비율은 남은 주간 여유를 리셋까지 남은 시간 비율로 나눈 값이라, 1 이면 리셋까지 고른 속도로 쓸 만큼 남았다는 뜻이다.

리셋이 가까운데 많이 남은 계정은 비율이 1 보다 커져서 먼저 쓰인다. 리셋 전에 안 쓰면 사라지는 몫이기 때문이다. Week 70% 에 두 시간 뒤 리셋되는 계정은 Week 40% 에 엿새 남은 계정보다 먼저 쓰이고, 리셋 직전이어도 최대 10배까지만 크게 친다. 반대로 앞당겨 많이 쓴 계정은 비율이 1 보다 작아져 뒤로 밀린다.

가장 높은 점수와 5점 안쪽인 계정끼리는 실행 중 세션이 적은 계정을 고르고, 세션 수도 같으면 점수가 높은 쪽을 고른다. 5h 사용률이 95% 이상이거나 Week 사용률이 98% 이상인 계정은 배정에서 뺀다. 모든 계정이 빠지면 점수가 가장 높은 계정을 고르고 경고한다. `acm pick` 은 고른 계정을 `Week 3% · 점수 124 · 실행 중 4` 처럼 보인다. 실행 중 세션은 내 macOS 계정으로 띄운 최상위 claude 프로세스만 세고, 계정은 그 프로세스의 `CLAUDE_CONFIG_DIR` 로 가른다. 환경변수는 `ps` 출력 대신 커널에서 인자와 나뉜 채로 읽어서, 인자에 `KEY=값` 이 들어 있어도 헷갈리지 않는다.

`acm mode rr` 로 바꾸면 사용량과 상관없이 돌아가며 고른다. 기준값은 환경변수로 바꾼다.

| 환경변수 | 기본값 | 뜻 |
|---|---|---|
| `ACM_FIVE_HOUR_CAP` | 95 | 이 5h 사용률 이상이면 배정에서 뺀다 |
| `ACM_SEVEN_DAY_CAP` | 98 | 이 Week 사용률이나 모델별 주간 사용률 이상이면 배정에서 뺀다 |
| `ACM_USAGE_BAND` | 5 | 가장 높은 점수와 이만큼 안쪽이면 실행 중 세션이 적은 계정을 고른다 |
| `ACM_POLL_INTERVAL` | 300 | 계정마다 사용량을 읽는 간격. 초 단위이고 Codex 계정에도 같이 쓴다 |
| `ACM_RESERVE_FIVE_HOUR_CAP` | 70 | 대표 계정을 자동 배정에서 빼는 5h 사용률 |
| `ACM_RESERVE_SEVEN_DAY_CAP` | 85 | 대표 계정을 자동 배정에서 빼는 Week 사용률 |

대표 계정을 따로 다루는 기준은 [아티팩트 모으기와 화면 제어](publisher.md) 에 있다.

## 모델별 주간 한도는 그 모델 세션에만 견준다

`/usage` 에는 Week 말고도 `Current week (Fable)` 이나 `Current week (Sonnet only)` 처럼 모델 하나에만 걸리는 주간 한도가 따로 나온다. acm 은 이번 세션이 쓸 모델을 짐작해서, 그 모델에 걸리는 한도를 Week 와 함께 본다. 둘 중 더 빠듯한 쪽이 주간 속도 비율을 정하고, 그 한도가 98% 이상이면 배정에서 뺀다. 다른 모델의 한도는 화면에 보이기만 한다.

모델은 Claude Code 가 모델을 정하는 순서를 따라 짐작한다.

- `acm --model fable` 처럼 넘긴 `--model`
- 환경변수 `ANTHROPIC_MODEL`
- 작업 폴더의 `.claude/settings.local.json` 과 `.claude/settings.json`, 그다음 `~/.claude/settings.json` 의 `model`
- 앞의 것이 모두 없으면 statusline 이 마지막으로 본 세션의 모델

세션 안에서 `/model` 로 바꾼 모델은 띄울 때 알 수 없다. `acm status` 의 마지막 줄이 지금 어느 모델 기준으로 견주는지 보인다.

## 사용량은 statusline 과 /usage 두 곳에서 모은다

세션이 떠 있는 계정은 Claude Code 가 statusline 에 넘기는 `rate_limits` 를 `acm-statusline` 이 받아 `~/.acm/usage/<계정>.json` 에 적는다. 로그인한 계정은 모두 5분마다 그 계정의 Claude Code 로 `claude -p /usage` 를 뒤에서 돌려 `~/.acm/poll/<계정>.json` 에 적는다. 이 명령은 모델을 부르지 않아서 입력과 출력 모두 0 토큰, 비용 $0 이었고, 한 번에 3.8초가 걸렸다.[1] 창마다 더 최근에 받은 값을 쓰고, 모델별 주간 한도는 `/usage` 에만 있다.

조회는 기다리지 않는다. 세션을 띄우거나 메뉴바 앱이 현황을 부를 때 조회할 때가 된 계정이 있으면, acm 은 `acm poll` 을 뒤에 띄우고 지금 가진 값으로 바로 고른다. 세션이 없는 계정은 이 Mac 밖에서 쓰지 않는 한 사용량이 늘지 않아서, 몇 분 묵은 값으로 골라도 결과가 같다.

`/usage` 가 실패하면 7분 30초를 쉬고, 다시 실패할 때마다 대기를 1.5배씩 늘려 최대 30분까지 쉰다. 429 가 아닌 실패는 토큰 만료일 수 있어서 [계정 관리](accounts.md) 에 적은 토큰 갱신을 띄운다. 사용량을 보는 다른 도구가 같은 사용량 API 를 자주 부르면 호출 한도를 나눠 쓰게 돼 429 가 나니, 그런 도구는 하나만 켠다.[2] `/usage` 출력은 사람이 읽는 문장이라 형식이 바뀌면 acm 이 읽지 못하니, Claude Code 를 올린 뒤에는 `acm doctor` 를 돌린다.

## Ultra 인증 계정의 5h 는 한도 없음으로 보인다

인증된 Ultra 계정에는 5시간 한도가 없어서, acm 은 그 계정의 5h 를 0% 가 아니라 한도 없음으로 다룬다. 2026-10-30 에 Max 20x 요금제가 Ultra 로 바뀌면서, Anthropic 은 계정과 결제 이력으로 Ultra 계정을 자동 인증하고 인증된 계정의 5시간 한도를 없앴다.[3] Settings > Usage 와 `/usage` 출력에 Current session 줄이 없으면 인증된 계정이다.[4]

acm 은 statusline 과 `/usage` 어디에서도 5h 창이 하루 넘게 보이지 않으면 5시간 한도가 없는 계정으로 본다. 한도가 있는 계정도 창이 리셋되면 statusline 입력에서 5h 가 빠지기 때문에, 한 번 빠졌다고 한도 없음으로 보지 않고, 리셋 시각이 지난 그 창을 0% 로 읽는다.[5]

한도가 있는 계정을 하루 넘게 쓰지 않을 때 `/usage` 가 5h 줄을 보이는지는 미확인인데, 보이지 않아도 그동안 5h 사용률은 0% 라 배정은 거의 같다. 한도 없는 계정은 배정 제외와 대표 계정 예비 기준도 Week 만 본다. 화면에서 5h 자리를 어떻게 비우는지는 [메뉴바와 위젯](app.md) 에 있다.

## 한도에 걸린 세션은 acm resume 으로 다른 계정에서 이어 간다

세션이 한도로 멈추면 `StopFailure` 훅이 그 세션을 `~/.acm/limited/` 에 적고, iTerm 알림으로 `acm resume` 을 알린다. 훅의 출력은 세션에 들어가지 않아서 acm 이 세션을 대신 옮길 수는 없다.[6] 그래서 그 세션을 닫고 아무 터미널에서 `acm resume` 을 치면, 가장 최근에 걸린 세션을 다른 계정으로 다시 연다. 세션 기록은 모든 계정이 같이 쓰는 공유 폴더에 있어서 맥락이 그대로 이어진다.[7] 훅은 `acm setup` 이 `~/.claude/settings.json` 에 `rate_limit` 매처로 넣는다.

```bash
acm resume                # 가장 최근에 한도로 멈춘 세션을 다른 계정으로
acm resume 9e8ce742       # 세션 ID 로 고른다. 한도 기록이 있는 세션은 앞부분만 써도 된다
acm resume -a cl1        # 이어 갈 계정을 직접 지정
```

이어 갈 계정은 새 세션과 같은 점수로 고르되, 아래 계정은 고르지 않는다.

- 한도에 걸린 그 계정과, 그 계정과 같은 Claude 계정으로 로그인한 acm 계정
- 한도 근처인 계정
- 대표 계정이 예비 기준 5h 70% 나 Week 85% 를 넘었으면 대표 계정
- 사용량 조회가 실패하고 토큰 갱신 뒤에도 성공하지 못해 로그인이 풀린 계정

새 세션 배정은 모든 계정이 막혀도 한도 근처 계정으로 띄우지만, 이어 가기는 갈 곳이 없으면 띄우지 않고 계정마다 사용률과 리셋 시각을 알린다. 이어 간 세션이 바로 다시 멈추면 소용이 없어서다. 대표 계정은 아티팩트 발행에 Week 15% 를 남겨 두려고 85% 에서 멈춘다. 85% 전에 떠 있던 대표 계정 세션이 남은 15% 를 다 쓰는 일은 드물어서, 그 세션들을 미리 옮기라고 알리지는 않는다.

주간 한도에 걸리면 Claude Code 가 세 가지 중에 고르라고 묻는다. 기다렸다가 멈추기와 리셋 때 이어서 하기, 사용량 크레딧으로 바꾸기인데, 이어 가려면 첫째를 고르고 세션을 닫는다. 셋째는 구독 밖에서 따로 요금을 낸다.[8]

다른 계정이 다른 조직이면, 이어 간 세션은 앞서 쓴 thinking 을 쓰지 못한다. Claude Code 는 "Claude can't use thinking from another organization" 을 띄운다. 다음 응답은 세션을 다시 읽느라 느려지고 토큰을 더 쓴다. thinking 은 지워지지 않아서 원래 계정으로 다시 열면 다시 쓴다.[7] 대화 캐시도 계정마다 따로라 처음부터 다시 만든다.[9] 그래도 이어 갈 때를 사람이 고르니 세션 도중에 갑자기 느려지지는 않는다.

`acm resume` 은 세션을 열었던 폴더로 옮겨서 `claude --resume` 을 띄운다. 같은 세션이 아직 열려 있으면 기록이 섞이니 띄우지 않는다. 한도에 걸린 뒤에도 2분 넘게 기록이 이어진 세션은 리셋 뒤 그 계정에서 계속 쓴 것으로 보고 이어 갈 목록에서 뺀다. `acm status` 는 이어 가지 않은 세션이 있으면 그 수를 알린다.

## Codex 는 Codex 계정끼리 같은 점수로 고른다

배정은 같은 도구의 계정끼리만 한다. `acm codex` 는 Codex 계정 가운데서, `acm claude` 와 도구 이름 없는 `acm` 은 Claude 계정 가운데서 고른다. 점수와 배정 제외 기준, 세션 수로 가르는 규칙은 Claude 와 같다. 라운드로빈의 직전 계정도 도구마다 따로 기억한다. 대표 계정 예비 기준은 아티팩트 발행 몫이라 Codex 에는 없다. `acm pick codex` 로 고를 계정을 미리 본다.

Codex 사용량은 5분마다 그 계정의 `CODEX_HOME` 으로 `codex app-server` 를 띄워 묻는다. JSON-RPC 로 `account/read` 와 `account/rateLimits/read` 를 보내고 답을 받으면 바로 끈다. 모델을 부르지 않고 한 번에 0.5~2.0초가 걸렸다.[10] statusline 같은 다른 경로가 없어서 이 조회 값만 쓴다. 실패하면 Claude 와 같은 간격으로 쉬었다가 다시 읽는다.

창은 요금제마다 다르다. 무료 요금제 계정에서는 30일 창 하나만 왔다.[10] acm 은 5시간 이하 창을 5h 자리에 두고 긴 창 가운데 가장 많이 쓴 창을 Week 자리에 둔다. 나머지 긴 창도 점수에 견주고 주간 속도 비율은 창마다 제 길이로 잰다. 30일 창은 리셋까지 남은 시간을 30일에 견준다. 화면과 `acm status` 는 이 창을 `30d 100%` 처럼 창 길이로 부른다. Plus 계정에서는 5시간 창과 7일 창이 와서 각각 5h 와 Week 자리에 들어갔다.[11]

Codex 가 지금은 쓸 수 없다고 알리면 사용률과 상관없이 배정에서 뺀다. 응답의 `ordinaryUsageAllowed` 가 false 인 경우이고 그때 본 창의 리셋 시각이 지나면 다시 견준다. 응답에 `codex` 말고 다른 한도 항목이 오면 `acm status` 에 보이기만 하고 배정에는 쓰지 않는다.

실행 중 세션은 내 macOS 계정으로 띄운 최상위 `codex` 프로세스를 세고 계정은 그 프로세스의 `CODEX_HOME` 으로 가른다. `CODEX_HOME` 이 없으면 기본 계정이다. Codex 가 뒤에 띄워 두는 앱 서버 데몬은 세션이 아니라서 세지 않는다. Homebrew 로 깐 codex 에서 확인했다. npm 으로 깔아 프로세스 이름이 `node` 로 보이는 설치에서는 세지 못할 수 있다.

`acm resume` 은 Claude 세션만 이어 간다. Codex 는 세션 기록을 모든 계정이 같이 쓰니, 한도에 걸린 세션은 닫고 `acm codex resume <세션 ID>` 를 치면 남은 여유가 가장 큰 계정에서 연다. 다른 계정에서 이어 갈 때 앞서 쓴 추론 기록을 그대로 쓰는지는 미확인이다.

## 각주

[1] 2026-11-02, Claude Code 2.1.316. 두 계정에서 `claude -p "/usage" --output-format json` 의 `usage` 토큰이 모두 0, `total_cost_usd` 가 0 이었다. 출력 형식은 같은 판의 `/usage` 코드에서 확인했다.

[2] 2026-10-30. 2분마다 같은 API 를 부르는 메뉴바 플러그인을 지우자 기본 계정의 429 가 멈췄다.

[3] Anthropic 도움말 "What is the Ultra plan?" https://support.claude.com/en/articles/17728952-what-is-the-ultra-plan

[4] 2026-11-01 기본 계정의 사용량 API 응답에서 `five_hour` 가 null 이었고, 2026-11-02 두 계정의 `/usage` 출력에 Current session 줄이 없었다.

[5] Claude Code statusline 문서는 "Claude Code drops a window once its resets_at time passes" 라고 적는다. https://code.claude.com/docs/en/statusline

[6] Claude Code hooks 문서의 `StopFailure` 절. 입력에 `session_id` 와 `cwd`, `transcript_path`, `error` 가 오고, 출력은 `terminalSequence` 말고는 쓰지 않는다. https://code.claude.com/docs/en/hooks

[7] 2026-11-03, Claude Code 2.1.316. 기본 계정 haiku 세션에 코드 단어를 기억하라고 한 뒤 한도에 걸린 것으로 적었다. 세션을 열어 둔 채 `acm resume` 을 치자 거부했고, 닫은 뒤 치자 두 번째 계정을 골라 열었다. 거기서 코드 단어를 묻자 맞게 답했고, 그 답 앞에 다른 조직 thinking 안내가 떴다.

[8] 2026-11-03, Claude Code 2.1.316. 두 번째 계정 세션 하나만 `ANTHROPIC_BASE_URL` 을 로컬 가짜 서버로 돌렸다. 가짜 서버는 `rate_limit_error` 429 와 주간 한도 `rejected` 헤더로 답했다. 세션은 "You've hit your weekly limit" 와 세 가지 선택지를 띄웠고, 훅이 `~/.acm/limited/` 에 기록을 남겼다. 기록을 보고 `acm resume` 이 기본 계정으로 다시 열었다. tmux 안이라 iTerm 알림은 보지 못했고, 진짜 한도에서 같은지는 미확인이다.

[9] 세션 도중 계정을 바꾸는 다른 도구도 넘어간 뒤 첫 요청에서 대화 캐시를 다시 만든다고 적는다. claude-swap README 의 Limitations 절과 CCS Account Pools 문서. https://github.com/realiti4/claude-swap , https://docs.ccs.kaitran.ca/features/pool

[10] 2026-11-03, codex-cli 0.165.0. 무료 요금제 기본 계정에서 `initialize` 부터 `account/rateLimits/read` 응답까지 0.5~2.0초였다. 응답의 `primary` 는 `windowDurationMins` 43200, `usedPercent` 100 이었고 `secondary` 는 null, `ordinaryUsageAllowed` 는 false 였다.

[11] 2026-11-03, codex-cli 0.166.0. 무료에서 Plus 로 올린 계정의 `acm status` 가 5h 와 Week 를 보였다. 리셋 시각은 5h 가 다섯 시간 뒤, Week 가 이레 뒤였다.
