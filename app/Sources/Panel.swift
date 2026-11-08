import AppKit
import ServiceManagement
import SwiftUI

struct PanelView: View {
    @ObservedObject var store: Store
    @State private var loginItem = SMAppService.mainApp.status == .enabled

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header
            if let error = store.error {
                Text(error).font(.caption).foregroundStyle(.red).fixedSize(horizontal: false, vertical: true)
            }
            if let snap = store.snapshot {
                // Group each tool in a border of its own color. The widget checkbox appears only when there is more than one tool
                let widgetTools = snap.widgetList(store.widgetTools)
                ForEach(snap.toolList, id: \.self) { tool in
                    ToolGroup(tool: tool, next: snap.next(for: tool),
                              widget: snap.toolList.count > 1 ? Binding(get: { widgetTools.contains(tool) },
                                                                        set: { store.setWidget(tool, $0, in: snap) }) : nil,
                              lastInWidget: widgetTools == [tool]) {
                        ForEach(snap.accounts(of: tool)) { AccountCard(account: $0, showsFiveHour: snap.showsFiveHour(of: tool)) }
                    }
                }
                if let agy = snap.antigravity, !agy.groups.isEmpty {
                    ToolGroup(tool: "antigravity", next: nil, widget: nil, lastInWidget: false) {
                        AntigravityCard(usage: agy)
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
            .help("Refresh")
        }
    }

    private func sessions(_ snap: Snapshot) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("\(snap.sessions.count) running session\(snap.sessions.count == 1 ? "" : "s")").font(.subheadline.bold())
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
                            // via is acm if the session was started through acm, otherwise claude or codex
                            if s.via != "acm" {
                                Text(s.via).font(.caption2).foregroundStyle(.orange).help("Session started without acm")
                            }
                            Text(Fmt.duration(Double(s.elapsedS))).font(.caption2).foregroundStyle(.secondary)
                        }
                    }
                }
            }
            // The menu bar window opens at the ideal size of its content, but a ScrollView's ideal height is 0, so the list would vanish. Set the height from the row count
            .frame(height: min(220, CGFloat(snap.sessions.count) * (Self.sessionRow + Self.sessionSpacing)))
        }
    }

    private static let sessionRow: CGFloat = 16
    private static let sessionSpacing: CGFloat = 3

    private func footer(_ snap: Snapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Mode").font(.caption)
                Picker("", selection: Binding(get: { snap.mode }, set: { store.setMode($0) })) {
                    Text("Usage").tag("usage")
                    Text("Round robin").tag("rr")
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .frame(width: 170)
                Spacer()
                if snap.toolList.count > 1 {
                    Menu("New Session…") {
                        ForEach(snap.toolList, id: \.self) { tool in
                            Button("\(Tools.name(tool)) session…") { NewSession.openInITerm(tool: tool) }
                        }
                    }
                    .fixedSize()
                } else {
                    Button("New Session…") { NewSession.openInITerm(tool: snap.toolList.first ?? "claude") }
                }
            }
            HStack {
                Toggle("Launch at login", isOn: $loginItem)
                    .toggleStyle(.checkbox)
                    .font(.caption)
                    .onChange(of: loginItem) { _, on in
                        do {
                            if on { try SMAppService.mainApp.register() } else { try SMAppService.mainApp.unregister() }
                        } catch {
                            store.error = "Could not change the login item: \(error.localizedDescription)"
                            loginItem = SMAppService.mainApp.status == .enabled
                        }
                    }
                Toggle("Floating widget", isOn: $store.widgetVisible)
                    .toggleStyle(.checkbox)
                    .font(.caption)
                Spacer()
                Text("Updated \(Date(timeIntervalSince1970: snap.generatedAt).formatted(date: .omitted, time: .shortened))")
                    .font(.caption2).foregroundStyle(.secondary)
                Button("Quit") { NSApp.terminate(nil) }.font(.caption)
            }
        }
    }
}

// A tool group. The top row has the logo and name, the tool's next pick, and whether it shows in the widget.
// The account cards sit inside a border in the tool's color
struct ToolGroup<Content: View>: View {
    let tool: String
    let next: Snapshot.Next?
    // nil means no checkbox. With only one tool, the widget always shows that tool
    let widget: Binding<Bool>?
    // The last tool left in the widget, so it cannot be turned off
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
                    Toggle("Show in widget", isOn: widget)
                        .toggleStyle(.checkbox)
                        .font(.caption)
                        .disabled(lastInWidget)
                        .help(lastInWidget ? "The widget needs at least one tool. To hide the widget, turn off Floating widget below."
                                           : "Show \(Tools.name(tool)) accounts in the floating widget")
                }
            }
            // On the checkbox row it would be cut off. Put it on the next row so it can use the full box width
            if let next {
                Text("Next session → \(next.label)  (\(next.why))").font(.caption2).foregroundStyle(.secondary)
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
    // Same rule as the widget. If no account has a 5-hour limit, drop the 5h row
    let showsFiveHour: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(account.label).font(.subheadline.bold())
                Text(account.email ?? "Not signed in").font(.caption).foregroundStyle(.secondary).lineLimit(1)
                if let plan = account.plan {
                    Text(Fmt.plan(plan)).font(.caption2).foregroundStyle(.secondary)
                        .padding(.horizontal, 4).background(Capsule().fill(Color.primary.opacity(0.08)))
                }
                if account.isReserved {
                    ReserveTag(held: account.isHeld)
                }
                Spacer()
                if account.exhausted {
                    Text(account.isDenied ? "Unavailable" : "Near limit").font(.caption2.bold()).foregroundStyle(.white)
                        .padding(.horizontal, 5).background(Capsule().fill(.red))
                        .help(account.isDenied ? "Codex reported it as unavailable for now, so it is left out of automatic picks"
                                                : "Over the limit threshold, so it is left out of automatic picks")
                }
                Text("\(account.sessions) session\(account.sessions == 1 ? "" : "s")").font(.caption).foregroundStyle(.secondary)
            }
            if account.loggedIn {
                if showsFiveHour {
                    // If usage has not been read yet, the reason for a missing 5h window is unknown, so do not assume Ultra
                    UsageBar(title: Windows.fiveHour, window: account.fiveHour,
                             empty: account.updatedAt == nil ? "Not read yet"
                                 : account.toolKey == "codex" ? "No 5-hour window on this plan" : UsageBar.ultra)
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
                        Text("\(Fmt.duration(Date().timeIntervalSince1970 - at)) ago · \(account.source ?? "")")
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

// Antigravity usage. agy holds one account, so there is no email, session count, or pick
struct AntigravityCard: View {
    let usage: Snapshot.Antigravity

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Usage only · acm does not start or pick it").font(.caption).foregroundStyle(.secondary)
            ForEach(usage.groups) { group in
                UsageBar(title: group.name, window: group.window, titleWidth: 92)
            }
            HStack(spacing: 4) {
                if let at = usage.updatedAt {
                    Text("\(Fmt.duration(Date().timeIntervalSince1970 - at)) ago · agy")
                }
                if let note = usage.pollNote {
                    Text("· \(note)").foregroundStyle(.orange)
                }
            }
            .font(.caption2).foregroundStyle(.secondary)
        }
        .padding(8)
        .background(RoundedRectangle(cornerRadius: 8).fill(.quaternary.opacity(0.5)))
    }
}

struct UsageBar: View {
    static let ultra = "No limit · verified Ultra account"
    let title: String
    // nil means the account has no limit for this window (the 5h of a verified Ultra account)
    let window: Snapshot.Window?
    var empty = UsageBar.ultra
    // Antigravity group names such as "Claude and GPT" need more room than 5h or Week
    var titleWidth: CGFloat = 42

    var body: some View {
        HStack(spacing: 6) {
            Text(title).font(.caption).lineLimit(1).frame(width: titleWidth, alignment: .leading)
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
    // Once a folder is picked, start acm with that tool in a new iTerm window
    @MainActor
    static func openInITerm(tool: String) {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.prompt = "Open session here"
        panel.directoryURL = URL(fileURLWithPath: NSHomeDirectory() + "/workspace")
        NSApp.activate(ignoringOtherApps: true)
        guard panel.runModal() == .OK, let dir = panel.url?.path else { return }
        // The path is typed into iTerm as text. A control character could end or erase the line outside the quotes,
        // so no session is started. fish reads \' inside single quotes as an escape, so a path with a backslash is refused too
        if dir.contains("\\") || dir.unicodeScalars.contains(where: { CharacterSet.controlCharacters.contains($0) }) {
            NSSound.beep()
            return
        }
        let quoted = "'" + dir.replacingOccurrences(of: "'", with: "'\\''") + "'"
        // Use only tool names this app defines, because they are typed into the terminal
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
