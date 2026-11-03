import AppKit
import ServiceManagement
import SwiftUI

struct PanelView: View {
    @ObservedObject var store: Store
    @State private var loginItem = SMAppService.mainApp.status == .enabled
    @State private var widget = FloatingWidget.shared.isVisible

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header
            if let error = store.error {
                Text(error).font(.caption).foregroundStyle(.red).fixedSize(horizontal: false, vertical: true)
            }
            if let snap = store.snapshot {
                // 도구마다 색이 다른 테두리로 묶는다. 위젯 체크박스는 도구가 여럿일 때만 둔다
                let widgetTools = snap.widgetList(store.widgetTools)
                ForEach(snap.toolList, id: \.self) { tool in
                    ToolGroup(tool: tool, next: snap.next(for: tool),
                              widget: snap.toolList.count > 1 ? Binding(get: { widgetTools.contains(tool) },
                                                                        set: { store.setWidget(tool, $0, in: snap) }) : nil,
                              lastInWidget: widgetTools == [tool]) {
                        ForEach(snap.accounts(of: tool)) { AccountCard(account: $0, showsFiveHour: snap.showsFiveHour(of: tool)) }
                    }
                }
                Divider()
                sessions(snap)
                Divider()
                footer(snap)
            } else if store.error == nil {
                ProgressView().frame(maxWidth: .infinity)
            }
        }
        .padding(14)
        .frame(width: 400)
        .onAppear { store.refresh() }
    }

    private var header: some View {
        HStack(spacing: 8) {
            AppLogo(size: 22)
            Text("AI Account Manager").font(.headline)
            Spacer()
            Button {
                store.refresh()
            } label: {
                Image(systemName: store.loading ? "hourglass" : "arrow.clockwise")
            }
            .buttonStyle(.borderless)
            .help("새로고침")
        }
    }

    private func sessions(_ snap: Snapshot) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("실행 중인 세션 \(snap.sessions.count)개").font(.subheadline.bold())
            ScrollView {
                VStack(alignment: .leading, spacing: Self.sessionSpacing) {
                    ForEach(snap.sessions) { s in
                        HStack(spacing: 6) {
                            if snap.toolList.count > 1 {
                                Text(Tools.name(s.tool ?? "claude")).font(.caption2).foregroundStyle(.secondary)
                                    .frame(width: 38, alignment: .leading)
                            }
                            Text(s.label ?? "?")
                                .font(.caption2.monospaced())
                                .padding(.horizontal, 4)
                                .background(RoundedRectangle(cornerRadius: 3).fill(.quaternary))
                            Text(Fmt.folder(s.cwd)).font(.caption).lineLimit(1).truncationMode(.middle)
                            Spacer()
                            // via 는 acm 으로 띄웠으면 acm, 아니면 claude 나 codex 다
                            if s.via != "acm" {
                                Text(s.via).font(.caption2).foregroundStyle(.orange).help("acm 을 거치지 않고 띄운 세션")
                            }
                            Text(Fmt.duration(Double(s.elapsedS))).font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                }
            }
            // 메뉴바 창은 내용의 이상적인 크기로 열리는데 ScrollView 는 그 높이가 0 이라 목록이 사라진다. 줄 수로 높이를 정한다
            .frame(height: min(220, CGFloat(snap.sessions.count) * (Self.sessionRow + Self.sessionSpacing)))
        }
    }

    private static let sessionRow: CGFloat = 16
    private static let sessionSpacing: CGFloat = 3

    private func footer(_ snap: Snapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("분배").font(.caption)
                Picker("", selection: Binding(get: { snap.mode }, set: { store.setMode($0) })) {
                    Text("사용량").tag("usage")
                    Text("라운드로빈").tag("rr")
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .frame(width: 170)
                Spacer()
                if snap.toolList.count > 1 {
                    Menu("새 세션…") {
                        ForEach(snap.toolList, id: \.self) { tool in
                            Button("\(Tools.name(tool)) 세션…") { NewSession.openInITerm(tool: tool) }
                        }
                    }
                    .fixedSize()
                } else {
                    Button("새 세션…") { NewSession.openInITerm(tool: snap.toolList.first ?? "claude") }
                }
            }
            HStack {
                Toggle("로그인 시 실행", isOn: $loginItem)
                    .toggleStyle(.checkbox)
                    .font(.caption)
                    .onChange(of: loginItem) { _, on in
                        do {
                            if on { try SMAppService.mainApp.register() } else { try SMAppService.mainApp.unregister() }
                        } catch {
                            store.error = "로그인 항목 변경 실패: \(error.localizedDescription)"
                            loginItem = SMAppService.mainApp.status == .enabled
                        }
                    }
                Toggle("떠 있는 위젯", isOn: $widget)
                    .toggleStyle(.checkbox)
                    .font(.caption)
                    .onChange(of: widget) { _, on in FloatingWidget.shared.isVisible = on }
                Spacer()
                Text("갱신 \(Date(timeIntervalSince1970: snap.generatedAt).formatted(date: .omitted, time: .shortened))")
                    .font(.caption2).foregroundStyle(.secondary)
                Button("종료") { NSApp.terminate(nil) }.font(.caption)
            }
        }
    }
}

// 도구 묶음. 로고와 이름, 그 도구의 다음 배정, 위젯에 보일지를 머리에 두고 계정 카드를 도구 색 테두리로 감싼다
struct ToolGroup<Content: View>: View {
    let tool: String
    let next: Snapshot.Next?
    // nil 이면 체크박스를 두지 않는다. 도구가 하나뿐이면 위젯은 늘 그 도구다
    let widget: Binding<Bool>?
    // 위젯에 남은 마지막 도구라 끌 수 없다
    let lastInWidget: Bool
    @ViewBuilder let content: Content

    var body: some View {
        let color = Tools.color(tool)
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                ToolLogo(tool: tool, size: 22)
                Text(Tools.name(tool)).font(.subheadline.bold())
                Spacer()
                if let widget {
                    Toggle("위젯에 표시", isOn: widget)
                        .toggleStyle(.checkbox)
                        .font(.caption)
                        .disabled(lastInWidget)
                        .help(lastInWidget ? "위젯에는 도구가 하나 이상 있어야 한다. 위젯을 숨기려면 아래 떠 있는 위젯을 끈다"
                                           : "떠 있는 위젯에 \(Tools.name(tool)) 계정을 보인다")
                }
            }
            // 체크박스와 한 줄에 두면 좁아서 잘린다. 상자 너비를 다 쓰게 아래 줄에 둔다
            if let next {
                Text("다음 세션 → \(next.label)  (\(next.why))").font(.caption2).foregroundStyle(.secondary)
                    .lineLimit(2).fixedSize(horizontal: false, vertical: true)
                    .padding(.top, -4)
            }
            content
        }
        .padding(10)
        .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(color.opacity(0.08)))
        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(color.opacity(0.6), lineWidth: 1))
    }
}

struct AccountCard: View {
    let account: Snapshot.Account
    // 위젯과 같은 규칙. 모든 계정에 5시간 한도가 없으면 5h 줄을 뺀다
    let showsFiveHour: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(account.label).font(.subheadline.bold())
                Text(account.email ?? "로그인 안 됨").font(.caption).foregroundStyle(.secondary).lineLimit(1)
                if let plan = account.plan {
                    Text(Fmt.plan(plan)).font(.caption2).foregroundStyle(.secondary)
                        .padding(.horizontal, 4).background(Capsule().fill(Color.primary.opacity(0.08)))
                }
                if account.isReserved {
                    ReserveTag(held: account.isHeld)
                }
                Spacer()
                if account.exhausted {
                    Text(account.isDenied ? "쓸 수 없음" : "한도 근처").font(.caption2.bold()).foregroundStyle(.white)
                        .padding(.horizontal, 5).background(Capsule().fill(.red))
                        .help(account.isDenied ? "Codex 가 지금은 쓸 수 없다고 알려 자동 배정에서 뺐다" : "한도 기준을 넘어 자동 배정에서 뺐다")
                }
                Text("세션 \(account.sessions)").font(.caption).foregroundStyle(.secondary)
            }
            if account.loggedIn {
                if showsFiveHour {
                    // 사용량을 아직 읽지 못한 계정은 5h 창이 없는 까닭을 알 수 없어서 Ultra 로 단정하지 않는다
                    UsageBar(title: Windows.fiveHour, window: account.fiveHour,
                             empty: account.updatedAt == nil ? "아직 읽지 못함"
                                 : account.toolKey == "codex" ? "이 요금제에는 5시간 창이 없음" : UsageBar.ultra)
                }
                UsageBar(title: account.sevenDay.name ?? Windows.week, window: account.sevenDay)
                ForEach(account.extra ?? []) { extra in
                    UsageBar(title: extra.name, window: extra.window)
                }
                ForEach(account.scoped ?? []) { scoped in
                    UsageBar(title: scoped.short, window: scoped.window)
                }
                HStack(spacing: 4) {
                    if let at = account.updatedAt {
                        Text("\(Fmt.duration(Date().timeIntervalSince1970 - at)) 전 · \(account.source ?? "")")
                    }
                    if let note = account.pollNote {
                        Text("· \(note)").foregroundStyle(.orange)
                    }
                }
                .font(.caption2).foregroundStyle(.secondary)
            } else {
                Text(Tools.loginHint(account)).font(.caption.monospaced()).foregroundStyle(.secondary)
            }
        }
        .padding(8)
        .background(RoundedRectangle(cornerRadius: 8).fill(.quaternary.opacity(0.5)))
        .opacity(account.loggedIn ? 1 : 0.6)
    }
}

struct UsageBar: View {
    static let ultra = "한도 없음 · Ultra 인증 계정"
    let title: String
    // nil 이면 그 창의 한도가 없는 계정이다 (Ultra 인증 계정의 5h)
    let window: Snapshot.Window?
    var empty = UsageBar.ultra

    var body: some View {
        HStack(spacing: 6) {
            Text(title).font(.caption).lineLimit(1).frame(width: 42, alignment: .leading)
            if let window {
                GaugeBar(pct: window.pct, height: 8)
                Text("\(Fmt.whole(window.pct, limit: 999))%")
                    .font(.caption.monospacedDigit().weight(.semibold))
                    .foregroundStyle(GaugeBar.color(window.pct))
                    .frame(width: 36, alignment: .trailing)
                Text(Fmt.resetIn(window.resetsAt)).font(.caption2).foregroundStyle(.secondary).frame(width: 96, alignment: .trailing)
            } else {
                Text(empty).font(.caption).foregroundStyle(.secondary)
                Spacer()
            }
        }
    }
}

enum NewSession {
    // 폴더를 고르면 iTerm 새 창에서 그 도구로 acm 을 띄운다
    @MainActor
    static func openInITerm(tool: String) {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.prompt = "여기서 세션 열기"
        panel.directoryURL = URL(fileURLWithPath: NSHomeDirectory() + "/workspace")
        NSApp.activate(ignoringOtherApps: true)
        guard panel.runModal() == .OK, let dir = panel.url?.path else { return }
        // 경로는 iTerm 에 글자로 입력된다. 제어 문자가 섞이면 따옴표 밖에서 줄이 끝나거나 지워질 수 있어 띄우지 않는다.
        // fish 는 작은따옴표 안의 \' 를 이스케이프로 읽어서, 역슬래시가 든 경로도 띄우지 않는다
        if dir.contains("\\") || dir.unicodeScalars.contains(where: { CharacterSet.controlCharacters.contains($0) }) {
            NSSound.beep()
            return
        }
        let quoted = "'" + dir.replacingOccurrences(of: "'", with: "'\\''") + "'"
        // 도구 이름은 이 앱이 정한 값만 쓴다. 터미널에 글자로 들어가서다
        let command = "cd \(quoted) && acm \(tool == "codex" ? "codex" : "claude")"
        let script = """
        tell application "iTerm"
            activate
            set w to (create window with default profile)
            tell current session of w to write text "\(command.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\""))"
        end tell
        """
        var error: NSDictionary?
        NSAppleScript(source: script)?.executeAndReturnError(&error)
    }
}
