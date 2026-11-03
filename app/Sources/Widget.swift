import AppKit
import SwiftUI

// A small usage window that floats on top. A header for each chosen tool and one row per account.
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
        // SwiftUI draws the shadow along the rounded shape. The window shadow is rectangular, so turn it off
        panel.hasShadow = false

        let host = AutoSizingHost(rootView: WidgetView(store: Store.shared))
        panel.contentView = host

        // Top right of the screen at first, then wherever it was last dragged. The size follows the content
        if !panel.setFrameUsingName("ACMWidget"), let screen = NSScreen.main {
            let frame = screen.visibleFrame
            panel.setFrameTopLeftPoint(NSPoint(x: frame.maxX - 520, y: frame.maxY - 4))
        }
        panel.setFrameAutosaveName("ACMWidget")
        host.fitWindow()
        return panel
    }
}

// Fit the window when the content changes size. Keep the top left corner in place
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
        // If it grows past the screen edge, push it back inside
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
                // If a new read fails, dim the last numbers and report the failure below
                Group {
                    ForEach(tools, id: \.self) { tool in
                        let showsFiveHour = snap.showsFiveHour(of: tool)
                        let scopes = snap.scopeColumns(of: tool)
                        // Window lengths and per-model limits differ by tool, so each tool gets its own header
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
                        Text("Could not read acm. Showing the last values")
                    }
                    .font(.system(size: 10))
                    .help(error)
                }
            } else {
                Text(store.error ?? "Reading acm…").font(.caption)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background {
            ZStack {
                // An NSView does not take a SwiftUI shadow, so lay a plate of the same shape underneath and shadow that
                RoundedRectangle(cornerRadius: Self.radius)
                    .fill(.black.opacity(0.2))
                    .shadow(color: .black.opacity(0.35), radius: 10, y: 4)
                VisualEffect(cornerRadius: Self.radius)
                // Lighten the top a little for a glassy look
                RoundedRectangle(cornerRadius: Self.radius)
                    .fill(LinearGradient(colors: [.white.opacity(0.10), .clear], startPoint: .top, endPoint: .bottom))
                RoundedRectangle(cornerRadius: Self.radius)
                    .strokeBorder(.white.opacity(0.18), lineWidth: 0.5)
            }
        }
        .fixedSize()
        // Inner window margin so the shadow is not clipped
        .padding(14)
        .contextMenu {
            Button("Refresh") { store.refresh() }
            if let snap = store.snapshot, snap.toolList.count > 1 {
                let shown = snap.widgetList(store.widgetTools)
                Divider()
                ForEach(snap.toolList, id: \.self) { tool in
                    Button((shown.contains(tool) ? "✓ " : "    ") + "Show \(Tools.name(tool))") {
                        store.setWidget(tool, !shown.contains(tool), in: snap)
                    }
                    .disabled(shown == [tool])
                }
                Divider()
            }
            Button("Hide widget") { FloatingWidget.shared.isVisible = false }
        }
    }
}

// Column widths. The header and the rows use the same values so the columns line up
enum WidgetColumn {
    // Fits a nine-character name, the plan badge, and the Primary tag. Longer names get cut short
    static let name: CGFloat = 142
    static let gauge: CGFloat = 48
    // Fits "100%" on one line
    static let pct: CGFloat = 36
    // When the Week reset is less than a day away, it takes six characters, like "13h53m"
    static let reset: CGFloat = 46
    static let inner: CGFloat = 4
    static let outer: CGFloat = 12
}

// The 5h, Week, and model name labels appear once in the header, not on every row. With several tools, the name cell shows the tool logo and name
struct WidgetHeader: View {
    // nil leaves the name cell empty. That happens when there is only one tool
    let tool: String?
    let showsFiveHour: Bool
    // Long window column name. Week for Claude, 30d for the Codex free plan
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
            Text("Reset").frame(width: WidgetColumn.reset, alignment: .leading)
        }
    }
}

struct WidgetRow: View {
    let account: Snapshot.Account
    let isNext: Bool
    // false means there is no 5h column. If true and this account has no 5-hour limit, the 5h cell shows "No limit"
    let showsFiveHour: Bool
    // Per-model columns from the header. If this account lacks that limit, the cell shows "–"
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
                // A dot flags a problem with the usage poll. Hover to see the details
                if let note = account.pollNote {
                    Circle().fill(.orange).frame(width: 6, height: 6).help(note)
                }
            }
            .frame(width: WidgetColumn.name, alignment: .leading)
            if showsFiveHour {
                if account.updatedAt == nil {
                    cell(account.fiveHour, empty: "–", emptyHelp: "Usage not read yet")
                } else if account.toolKey == "codex" {
                    cell(account.fiveHour, empty: "–", emptyHelp: "This plan has no 5-hour window")
                } else {
                    cell(account.fiveHour, empty: "No limit",
                         emptyHelp: "This account has no 5-hour limit (verified Ultra account). Only the Week limit applies.")
                }
            }
            cell(account.sevenDay, help: account.isDenied ? "Codex reported it as unavailable for now" : (account.sevenDay.name ?? ""))
            ForEach(scopes) { column in
                let scoped = account.scoped?.first { $0.name == column.name }
                cell(scoped?.window, help: scoped.map(Self.scopeHelp) ?? "",
                     empty: "–", emptyHelp: "This account has no \(column.name) weekly limit")
            }
        }
    }

    // Whether a per-model limit counts for this pick is less visible here than on the account card, so hovering explains it
    private static func scopeHelp(_ scoped: Snapshot.Scoped) -> String {
        (scoped.applies ?? false)
            ? "\(scoped.name) weekly limit. This pick counts it."
            : "\(scoped.name) weekly limit. Picks do not count it, because it is for another model."
    }

    // A nil window means the account lacks that limit, so show empty instead of a gauge
    private func cell(_ window: Snapshot.Window?, help: String = "",
                      empty: String = "", emptyHelp: String = "") -> some View {
        HStack(spacing: WidgetColumn.inner) {
            if let window {
                HStack(spacing: WidgetColumn.inner) {
                    GaugeBar(pct: window.pct).frame(width: WidgetColumn.gauge)
                    Text("\(Fmt.whole(window.pct, limit: 999))%")
                        .foregroundStyle(GaugeBar.color(window.pct)).fontWeight(.semibold)
                        .lineLimit(1)
                        .frame(width: WidgetColumn.pct, alignment: .trailing)
                }
                .help(help)
                // Time until reset
                Text(short(window.resetsAt))
                    .foregroundStyle(.secondary).frame(width: WidgetColumn.reset, alignment: .leading)
                    .help("Time until reset")
            } else {
                // Takes the full width of the gauge, %, and reset cells so it lines up with the rows above and below
                Text(empty)
                    .foregroundStyle(.secondary)
                    .frame(width: WidgetColumn.gauge + WidgetColumn.pct + WidgetColumn.reset + WidgetColumn.inner * 2,
                           alignment: .leading)
                    .help(emptyHelp)
            }
        }
        .font(.system(size: 11).monospacedDigit())
    }

    // Shorter than Fmt.duration: "1d7h" instead of "1d 7h"
    private func short(_ ts: Double?) -> String {
        guard let ts else { return "" }
        let s = max(0, Fmt.whole(ts - Date().timeIntervalSince1970))
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

// Plan badge on a widget row. Outline only, so it is not mistaken for the filled Primary tag
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
            .help("Plan: \(Fmt.plan(plan))")
    }
}

// Primary account tag. Turns orange when the account passed the reserve threshold and was left out of automatic picks
struct ReserveTag: View {
    let held: Bool
    var compact = false

    var body: some View {
        Text(compact ? "Primary" : (held ? "Primary · not picked" : "Primary account"))
            .font(.system(size: compact ? 9 : 10, weight: .semibold))
            .lineLimit(1)
            .fixedSize()
            .foregroundStyle(held ? Color.white : Color.secondary)
            .padding(.horizontal, 4)
            .padding(.vertical, 1)
            .background(Capsule().fill(held ? Color.orange : Color.primary.opacity(0.12)))
            .help(held ? "Left out of automatic picks for new sessions to keep headroom for publishing artifacts"
                       : "This primary account collects and publishes artifacts, so other accounts are picked first")
    }
}
