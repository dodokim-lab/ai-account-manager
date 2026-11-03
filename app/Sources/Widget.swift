import AppKit
import SwiftUI

// 항상 위에 떠 있는 작은 사용량 창. 고른 도구마다 머리글을 두고 계정마다 한 줄.
@MainActor
final class FloatingWidget {
    static let shared = FloatingWidget()
    private static let visibleKey = "widgetVisible"

    private var panel: NSPanel?

    var isVisible: Bool {
        get { UserDefaults.standard.object(forKey: Self.visibleKey) as? Bool ?? true }
        set {
            UserDefaults.standard.set(newValue, forKey: Self.visibleKey)
            newValue ? show() : panel?.orderOut(nil)
        }
    }

    func showIfEnabled() {
        if isVisible { show() }
    }

    private func show() {
        if panel == nil { panel = makePanel() }
        panel?.orderFrontRegardless()
    }

    private func makePanel() -> NSPanel {
        let panel = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 300, height: 48),
                            styleMask: [.nonactivatingPanel, .borderless],
                            backing: .buffered, defer: false)
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        panel.isMovableByWindowBackground = true
        panel.hidesOnDeactivate = false
        panel.backgroundColor = .clear
        panel.isOpaque = false
        // 그림자는 SwiftUI 가 둥근 모양을 따라 그린다. 창 그림자는 사각형이라 끈다
        panel.hasShadow = false

        let host = AutoSizingHost(rootView: WidgetView(store: Store.shared))
        panel.contentView = host

        // 처음에는 화면 오른쪽 위, 그다음부터는 마지막으로 끌어다 둔 자리. 크기는 내용을 따른다
        if !panel.setFrameUsingName("ACMWidget"), let screen = NSScreen.main {
            let frame = screen.visibleFrame
            panel.setFrameTopLeftPoint(NSPoint(x: frame.maxX - 520, y: frame.maxY - 4))
        }
        panel.setFrameAutosaveName("ACMWidget")
        host.fitWindow()
        return panel
    }
}

// 내용이 바뀌어 크기가 달라지면 창을 맞춘다. 왼쪽 위 모서리는 그대로 둔다
final class AutoSizingHost: NSHostingView<WidgetView> {
    override func invalidateIntrinsicContentSize() {
        super.invalidateIntrinsicContentSize()
        DispatchQueue.main.async { [weak self] in self?.fitWindow() }
    }

    func fitWindow() {
        guard let window else { return }
        let size = fittingSize
        guard size.width > 0, size.height > 0, size != window.frame.size else { return }
        var frame = NSRect(x: window.frame.minX, y: window.frame.maxY - size.height, width: size.width, height: size.height)
        // 커지면서 화면 밖으로 나가면 안쪽으로 민다
        if let visible = (window.screen ?? NSScreen.main)?.visibleFrame {
            frame.origin.x = min(max(frame.minX, visible.minX), visible.maxX - frame.width)
            frame.origin.y = min(max(frame.minY, visible.minY), visible.maxY - frame.height)
        }
        window.setFrame(frame, display: true)
    }
}

struct WidgetView: View {
    @ObservedObject var store: Store
    static let radius: CGFloat = 14

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            if let snap = store.snapshot {
                let tools = snap.widgetList(store.widgetTools)
                // 새로 읽지 못했으면 마지막으로 읽은 숫자를 흐리게 두고, 아래에 실패를 알린다
                Group {
                    ForEach(tools, id: \.self) { tool in
                        let showsFiveHour = snap.showsFiveHour(of: tool)
                        let scopes = snap.scopeColumns(of: tool)
                        // 도구마다 창 길이와 모델별 한도가 달라서 머리글을 따로 둔다
                        WidgetHeader(tool: snap.toolList.count > 1 ? tool : nil, showsFiveHour: showsFiveHour,
                                     longName: snap.longWindowName(of: tool), scopes: scopes)
                            .padding(.top, tool == tools.first ? 0 : 5)
                        ForEach(snap.accounts(of: tool).filter(\.loggedIn)) {
                            WidgetRow(account: $0, isNext: snap.next(for: tool)?.id == $0.id, showsFiveHour: showsFiveHour,
                                      scopes: scopes)
                        }
                    }
                }
                .opacity(store.error == nil ? 1 : 0.45)
                if let error = store.error {
                    HStack(spacing: 4) {
                        Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.orange)
                        Text("acm 을 읽지 못해 마지막 값을 보이는 중")
                    }
                    .font(.system(size: 10))
                    .help(error)
                }
            } else {
                Text(store.error ?? "acm 읽는 중…").font(.caption)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background {
            ZStack {
                // NSView 는 SwiftUI 그림자를 받지 않아서, 같은 모양의 판을 아래에 깔고 그 판에 그림자를 준다
                RoundedRectangle(cornerRadius: Self.radius)
                    .fill(.black.opacity(0.2))
                    .shadow(color: .black.opacity(0.35), radius: 10, y: 4)
                VisualEffect(cornerRadius: Self.radius)
                // 위쪽을 살짝 밝혀 유리처럼 보이게
                RoundedRectangle(cornerRadius: Self.radius)
                    .fill(LinearGradient(colors: [.white.opacity(0.10), .clear], startPoint: .top, endPoint: .bottom))
                RoundedRectangle(cornerRadius: Self.radius)
                    .strokeBorder(.white.opacity(0.18), lineWidth: 0.5)
            }
        }
        .fixedSize()
        // 그림자가 잘리지 않게 창 안쪽 여백
        .padding(14)
        .contextMenu {
            Button("새로고침") { store.refresh() }
            if let snap = store.snapshot, snap.toolList.count > 1 {
                let shown = snap.widgetList(store.widgetTools)
                Divider()
                ForEach(snap.toolList, id: \.self) { tool in
                    Button((shown.contains(tool) ? "✓ " : "    ") + "\(Tools.name(tool)) 보기") {
                        store.setWidget(tool, !shown.contains(tool), in: snap)
                    }
                    .disabled(shown == [tool])
                }
                Divider()
            }
            Button("위젯 숨기기") { FloatingWidget.shared.isVisible = false }
        }
    }
}

// 열 너비. 머리글과 줄이 같은 값을 써서 세로로 맞는다
enum WidgetColumn {
    // 아홉 글자 이름과 요금제 표시가 잘리지 않는 너비. 더 길면 이름이 줄어든다
    static let name: CGFloat = 124
    static let gauge: CGFloat = 48
    // "100%" 가 한 줄에 들어가는 너비
    static let pct: CGFloat = 36
    // Week 리셋이 하루 안으로 들어오면 "13h53m" 처럼 여섯 글자가 된다
    static let reset: CGFloat = 46
    static let inner: CGFloat = 4
    static let outer: CGFloat = 12
}

// 5h, Week, 모델 이름 라벨은 줄마다 쓰지 않고 머리글에 한 번만 쓴다. 도구가 여럿이면 이름 칸에 로고와 도구 이름을 쓴다
struct WidgetHeader: View {
    // nil 이면 이름 칸을 비운다. 도구가 하나뿐일 때다
    let tool: String?
    let showsFiveHour: Bool
    // 긴 창 열 이름. Claude 는 Week, Codex 무료 요금제는 30d
    let longName: String
    let scopes: [Snapshot.Scoped]

    var body: some View {
        HStack(spacing: WidgetColumn.outer) {
            HStack(spacing: 4) {
                if let tool {
                    ToolLogo(tool: tool, size: 12)
                    Text(Tools.name(tool)).fontWeight(.semibold)
                }
            }
            .frame(width: WidgetColumn.name, alignment: .leading)
            if showsFiveHour {
                column(Windows.fiveHour)
            }
            column(longName)
            ForEach(scopes) { column($0.short) }
        }
        .font(.system(size: 10, weight: .medium))
        .foregroundStyle(.secondary)
    }

    private func column(_ title: String) -> some View {
        HStack(spacing: WidgetColumn.inner) {
            Text(title).frame(width: WidgetColumn.gauge + WidgetColumn.inner + WidgetColumn.pct, alignment: .leading)
            Text("리셋").frame(width: WidgetColumn.reset, alignment: .leading)
        }
    }
}

struct WidgetRow: View {
    let account: Snapshot.Account
    let isNext: Bool
    // false 면 5h 열이 없다. true 인데 이 계정에 5시간 한도가 없으면 5h 칸에 "한도 없음" 을 둔다
    let showsFiveHour: Bool
    // 머리글의 모델별 열. 이 계정에 그 한도가 없으면 칸에 "–" 를 둔다
    let scopes: [Snapshot.Scoped]

    var body: some View {
        HStack(spacing: WidgetColumn.outer) {
            HStack(spacing: 4) {
                Text((isNext ? "▸ " : "  ") + account.label)
                    .font(.system(size: 11, weight: .semibold))
                    .lineLimit(1)
                if let plan = account.plan {
                    PlanBadge(plan: plan)
                }
                if account.isReserved {
                    ReserveTag(held: account.isHeld, compact: true)
                }
                // 사용량 조회에 걸린 일이 있으면 점으로 알린다. 내용은 마우스를 올리면 보인다
                if let note = account.pollNote {
                    Circle().fill(.orange).frame(width: 6, height: 6).help(note)
                }
            }
            .frame(width: WidgetColumn.name, alignment: .leading)
            if showsFiveHour {
                if account.updatedAt == nil {
                    cell(account.fiveHour, empty: "–", emptyHelp: "사용량을 아직 읽지 못했다")
                } else if account.toolKey == "codex" {
                    cell(account.fiveHour, empty: "–", emptyHelp: "이 요금제에는 5시간 창이 없다")
                } else {
                    cell(account.fiveHour, empty: "한도 없음", emptyHelp: "5시간 한도가 없는 계정 (Ultra 인증 계정). Week 한도만 걸린다")
                }
            }
            cell(account.sevenDay, help: account.isDenied ? "Codex 가 지금은 쓸 수 없다고 알렸다" : (account.sevenDay.name ?? ""))
            ForEach(scopes) { column in
                let scoped = account.scoped?.first { $0.name == column.name }
                cell(scoped?.window, help: scoped.map(Self.scopeHelp) ?? "",
                     empty: "–", emptyHelp: "이 계정에는 \(column.name) 주간 한도가 없다")
            }
        }
    }

    // 모델별 한도는 이번 배정에 견주는지가 계정 카드보다 덜 드러나서, 마우스를 올리면 알린다
    private static func scopeHelp(_ scoped: Snapshot.Scoped) -> String {
        (scoped.applies ?? false)
            ? "\(scoped.name) 주간 한도. 이번 배정에 견준다"
            : "\(scoped.name) 주간 한도. 다른 모델 한도라 배정에 견주지 않는다"
    }

    // window 가 nil 이면 그 한도가 없는 계정이라 게이지 대신 empty 를 둔다
    private func cell(_ window: Snapshot.Window?, help: String = "",
                      empty: String = "", emptyHelp: String = "") -> some View {
        HStack(spacing: WidgetColumn.inner) {
            if let window {
                HStack(spacing: WidgetColumn.inner) {
                    GaugeBar(pct: window.pct).frame(width: WidgetColumn.gauge)
                    Text("\(Int(window.pct.rounded()))%")
                        .foregroundStyle(GaugeBar.color(window.pct)).fontWeight(.semibold)
                        .lineLimit(1)
                        .frame(width: WidgetColumn.pct, alignment: .trailing)
                }
                .help(help)
                // 리셋까지 남은 시간
                Text(short(window.resetsAt))
                    .foregroundStyle(.secondary).frame(width: WidgetColumn.reset, alignment: .leading)
                    .help("리셋까지 남은 시간")
            } else {
                // 게이지, %, 리셋 세 칸 너비를 그대로 차지해서 아래위 줄과 열이 맞는다
                Text(empty)
                    .foregroundStyle(.secondary)
                    .frame(width: WidgetColumn.gauge + WidgetColumn.pct + WidgetColumn.reset + WidgetColumn.inner * 2,
                           alignment: .leading)
                    .help(emptyHelp)
            }
        }
        .font(.system(size: 11).monospacedDigit())
    }

    // "1일 7시간" 대신 "1d7h" 처럼 짧게
    private func short(_ ts: Double?) -> String {
        guard let ts else { return "" }
        let s = max(0, Int(ts - Date().timeIntervalSince1970))
        let d = s / 86400, h = (s % 86400) / 3600, m = (s % 3600) / 60
        if d > 0 { return "\(d)d\(h)h" }
        if h > 0 { return "\(h)h\(m)m" }
        return "\(m)m"
    }
}

struct VisualEffect: NSViewRepresentable {
    var cornerRadius: CGFloat = 0

    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = .hudWindow
        view.blendingMode = .behindWindow
        view.state = .active
        view.wantsLayer = true
        view.layer?.cornerRadius = cornerRadius
        view.layer?.cornerCurve = .continuous
        view.layer?.masksToBounds = true
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {}
}

// 위젯 줄의 요금제 표시. 속을 채운 대표 표시와 헷갈리지 않게 테두리만 긋는다
struct PlanBadge: View {
    let plan: String

    var body: some View {
        Text(Fmt.plan(plan))
            .font(.system(size: 8, weight: .medium))
            .lineLimit(1)
            .fixedSize()
            .foregroundStyle(.secondary)
            .padding(.horizontal, 3)
            .overlay(Capsule().strokeBorder(Color.secondary.opacity(0.5), lineWidth: 0.5))
            .help("요금제 \(Fmt.plan(plan))")
    }
}

// 대표 계정 표시. 예비 기준을 넘어 자동 배정에서 빠졌으면 주황으로 바꾼다
struct ReserveTag: View {
    let held: Bool
    var compact = false

    var body: some View {
        Text(compact ? "대표" : (held ? "대표 · 배정 제외" : "대표 계정"))
            .font(.system(size: compact ? 9 : 10, weight: .semibold))
            .lineLimit(1)
            .fixedSize()
            .foregroundStyle(held ? Color.white : Color.secondary)
            .padding(.horizontal, 4)
            .padding(.vertical, 1)
            .background(Capsule().fill(held ? Color.orange : Color.primary.opacity(0.12)))
            .help(held ? "아티팩트 발행에 쓸 여유를 남기려고 새 세션 자동 배정에서 뺐다" : "아티팩트를 모아 발행하는 대표 계정이라 다른 계정을 먼저 배정한다")
    }
}
