import Foundation
import SwiftUI

// Same shape as the `acm status --json` output
struct Snapshot: Decodable {
    struct Window: Decodable {
        let pct: Double
        let resetsAt: Double?
        // Window name. Week for Claude. Week or 30d for Codex, depending on the plan. Older acm versions do not send it
        var name: String? = nil
    }

    // The other windows of an account with several long windows, like Codex. Picks count them too
    struct Extra: Decodable, Identifiable {
        let name: String
        let pct: Double
        let resetsAt: Double?

        var id: String { name }
        var window: Window { Window(pct: pct, resetsAt: resetsAt, name: name) }
    }

    // Per-model weekly limits (such as Fable or Sonnet only). applies tells whether the limit is for the model this pick counts
    struct Scoped: Decodable, Identifiable {
        let name: String
        let short: String
        let pct: Double
        let resetsAt: Double?
        let applies: Bool?

        var id: String { name }
        var window: Window { Window(pct: pct, resetsAt: resetsAt) }
    }

    struct Account: Decodable, Identifiable {
        let id: String
        // claude or codex. Older acm versions do not send it, so nil means claude
        let tool: String?
        let label: String
        let email: String?
        let plan: String?
        // nil for an account with no 5-hour limit (a verified Ultra account)
        let fiveHour: Window?
        let sevenDay: Window
        // Older acm versions do not send this field
        let scoped: [Scoped]?
        let exhausted: Bool
        let updatedAt: Double?
        let source: String?
        let pollNote: String?
        let sessions: Int
        // true for the primary account. reserveHeld is also true when it passed the reserve threshold and was left out of automatic picks
        let reserved: Bool?
        let reserveHeld: Bool?
        // An account that Codex reported as unavailable for now
        let denied: Bool?
        let extra: [Extra]?

        var toolKey: String { tool ?? "claude" }
        var isDenied: Bool { denied ?? false }
        var loggedIn: Bool { email != nil }
        var isReserved: Bool { reserved ?? false }
        var isHeld: Bool { reserveHeld ?? false }
        // The tighter of the two windows sets the real limit
        var binding: Double { max(fiveHour?.pct ?? 0, sevenDay.pct) }
    }

    struct Session: Decodable, Identifiable {
        let pid: Int
        let tool: String?
        let account: String?
        let label: String?
        let cwd: String?
        let elapsedS: Int
        let via: String

        var id: Int { pid }
    }

    struct Next: Decodable {
        let id: String
        let label: String
        let why: String
    }

    let generatedAt: Double
    let mode: String
    // The next pick for Claude. The next pick for each tool is in nextByTool
    let next: Next?
    let accounts: [Account]
    let sessions: [Session]
    // Tools that have accounts. Older acm versions do not send it
    let tools: [String]?
    let nextByTool: [String: Next?]?

    var toolList: [String] { tools ?? ["claude"] }

    func accounts(of tool: String) -> [Account] { accounts.filter { $0.toolKey == tool } }

    func next(for tool: String) -> Next? {
        if let found = nextByTool?[tool] { return found }
        return tool == "claude" ? next : nil
    }

    // Tools the widget shows, in menu bar window order. If all chosen tools are gone, show the first tool
    func widgetList(_ chosen: Set<String>) -> [String] {
        let list = toolList.filter(chosen.contains)
        return list.isEmpty ? [toolList.first ?? "claude"] : list
    }

    // Show 5h if any signed-in account of the tool has a 5-hour limit. If none has one (all verified Ultra accounts), drop the 5h column
    func showsFiveHour(of tool: String) -> Bool { accounts(of: tool).contains { $0.loggedIn && $0.fiveHour != nil } }

    // Per-model weekly limits to show as widget columns. Collect each limit any signed-in account has, in order of first appearance
    func scopeColumns(of tool: String) -> [Scoped] {
        var seen = Set<String>()
        return accounts(of: tool).filter(\.loggedIn).flatMap { $0.scoped ?? [] }.filter { seen.insert($0.name).inserted }
    }

    // Name of the long window column. If window lengths differ across accounts (Codex free and paid), use Limit
    func longWindowName(of tool: String) -> String {
        let names = Set(accounts(of: tool).filter(\.loggedIn).compactMap { $0.sevenDay.name })
        return names.count == 1 ? names.first! : names.isEmpty ? Windows.week : "Limit"
    }
}

enum Tools {
    static func name(_ tool: String) -> String {
        ["claude": "Claude", "codex": "Codex"][tool] ?? tool.capitalized
    }

    // Border color of a tool group in the menu bar window. Claude uses the same orange as the acm logo
    static func color(_ tool: String) -> Color {
        tool == "codex" ? Color(red: 0.29, green: 0.53, blue: 0.96) : Color(red: 0xD9 / 255, green: 0x77 / 255, blue: 0x57 / 255)
    }

    static func loginHint(_ account: Snapshot.Account) -> String {
        account.toolKey == "codex" ? "acm -a \(account.id) login --device-auth" : "acm -a \(account.id) auth login"
    }
}

@MainActor
final class Store: ObservableObject {
    // The menu bar window and the floating widget share the same data
    static let shared = Store()

    @Published var snapshot: Snapshot?
    @Published var error: String?
    @Published var loading = false
    // Tools shown in the floating widget. At first, the one tool (shownTool) the widget showed in older versions
    @Published var widgetTools = Set(UserDefaults.standard.stringArray(forKey: "widgetTools")
                                     ?? [UserDefaults.standard.string(forKey: "shownTool") ?? "claude"]) {
        didSet { UserDefaults.standard.set(widgetTools.sorted(), forKey: "widgetTools") }
    }

    // Turn a tool on or off in the widget. The last one stays on so the widget is never empty. To hide the whole widget, turn off "Floating widget"
    func setWidget(_ tool: String, _ on: Bool, in snap: Snapshot) {
        var tools = Set(snap.widgetList(widgetTools))
        if on { tools.insert(tool) } else { tools.remove(tool) }
        if !tools.isEmpty { widgetTools = tools }
    }

    nonisolated static let acmPath = NSString(string: "~/.local/bin/acm").expandingTildeInPath
    private var timer: Timer?

    init() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.refresh() }
        }
    }

    func refresh() {
        guard !loading else { return }
        loading = true
        Task.detached {
            let result = Store.run(["status", "--json"])
            await MainActor.run {
                self.loading = false
                switch result {
                case .success(let data):
                    let decoder = JSONDecoder()
                    decoder.keyDecodingStrategy = .convertFromSnakeCase
                    do {
                        self.snapshot = try decoder.decode(Snapshot.self, from: data)
                        self.error = nil
                    } catch {
                        self.error = "Could not parse acm output: \(error.localizedDescription)"
                    }
                case .failure(let message):
                    self.error = message.text
                }
            }
        }
    }

    func setMode(_ mode: String) {
        Task.detached {
            _ = Store.run(["mode", mode])
            await MainActor.run { self.refresh() }
        }
    }

    struct Failure: Error { let text: String }

    // Whether the process was stopped on timeout. The timer thread writes it and run reads it
    final class TimeoutFlag: @unchecked Sendable {
        private let lock = NSLock()
        private var value = false
        func set() { lock.lock(); value = true; lock.unlock() }
        var isSet: Bool { lock.lock(); defer { lock.unlock() }; return value }
    }

    nonisolated static func run(_ args: [String], timeout: Double = 60) -> Result<Data, Failure> {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: acmPath)
        process.arguments = args
        var env = ProcessInfo.processInfo.environment
        // The menu bar app does not inherit the shell PATH
        env["PATH"] = "\(NSHomeDirectory())/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        env.removeValue(forKey: "CLAUDE_CONFIG_DIR")
        process.environment = env
        let out = Pipe(), err = Pipe()
        process.standardOutput = out
        process.standardError = err
        do {
            try process.run()
        } catch {
            return .failure(Failure(text: "Could not run acm: \(acmPath)"))
        }
        // If acm hangs, loading never clears and the next refresh never comes. Stop it after the timeout
        let timedOut = TimeoutFlag()
        DispatchQueue.global().asyncAfter(deadline: .now() + timeout) {
            if process.isRunning {
                timedOut.set()
                process.terminate()
            }
        }
        let data = out.fileHandleForReading.readDataToEndOfFile()
        let errData = err.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        if timedOut.isSet {
            return .failure(Failure(text: "acm \(args.joined(separator: " ")) did not finish within \(Int(timeout))s and was stopped"))
        }
        if process.terminationStatus != 0 {
            let text = String(data: errData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return .failure(Failure(text: text.isEmpty ? "acm exited with code \(process.terminationStatus)" : text))
        }
        return .success(data)
    }
}

enum Fmt {
    // Clamp the range so a huge value from a corrupt usage file cannot crash the app in the Int conversion
    static func whole(_ x: Double, limit: Double = 1e9) -> Int {
        x.isFinite ? Int(min(max(x.rounded(), -limit), limit)) : 0
    }

    static func duration(_ seconds: Double) -> String {
        let s = max(0, whole(seconds))
        let d = s / 86400, h = (s % 86400) / 3600, m = (s % 3600) / 60
        if d > 0 { return "\(d)d \(h)h" }
        if h > 0 { return "\(h)h \(m)m" }
        return "\(m)m"
    }

    static func resetIn(_ ts: Double?) -> String {
        guard let ts else { return "" }
        let left = ts - Date().timeIntervalSince1970
        return left <= 0 ? "Already reset" : "Resets in \(duration(left))"
    }

    // Claude sends names like "Ultra" and Codex sends lowercase ones like "plus", so capitalize only the first letter
    static func plan(_ plan: String) -> String {
        plan.prefix(1).uppercased() + plan.dropFirst()
    }

    static func folder(_ path: String?) -> String {
        guard let path else { return "?" }
        let home = NSHomeDirectory()
        let short = path.hasPrefix(home) ? "~" + path.dropFirst(home.count) : path
        let parts = short.split(separator: "/")
        return parts.count > 2 ? "…/" + parts.suffix(2).joined(separator: "/") : short
    }
}
