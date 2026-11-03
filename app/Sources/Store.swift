import Foundation
import SwiftUI

// `acm status --json` 출력과 같은 모양
struct Snapshot: Decodable {
    struct Window: Decodable {
        let pct: Double
        let resetsAt: Double?
        // 창 이름. Claude 는 Week, Codex 는 요금제에 따라 Week 나 30d. 예전 acm 은 내지 않는다
        var name: String? = nil
    }

    // Codex 처럼 긴 창이 여럿인 계정의 나머지 창. 배정에도 견준다
    struct Extra: Decodable, Identifiable {
        let name: String
        let pct: Double
        let resetsAt: Double?

        var id: String { name }
        var window: Window { Window(pct: pct, resetsAt: resetsAt, name: name) }
    }

    // 모델별 주간 한도 (Fable, Sonnet only 같은 것). applies 는 이번 배정에 견주는 모델의 한도인지
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
        // claude 나 codex. 예전 acm 은 내지 않아서 nil 이면 claude 다
        let tool: String?
        let label: String
        let email: String?
        let plan: String?
        // 5시간 한도가 없는 계정(Ultra 인증 계정)은 nil
        let fiveHour: Window?
        let sevenDay: Window
        // 예전 acm 은 이 필드를 내지 않는다
        let scoped: [Scoped]?
        let exhausted: Bool
        let updatedAt: Double?
        let source: String?
        let pollNote: String?
        let sessions: Int
        // 대표 계정이면 true. 예비 기준을 넘어 자동 배정에서 빠졌으면 reserveHeld 도 true
        let reserved: Bool?
        let reserveHeld: Bool?
        // Codex 가 지금은 쓸 수 없다고 알린 계정
        let denied: Bool?
        let extra: [Extra]?

        var toolKey: String { tool ?? "claude" }
        var isDenied: Bool { denied ?? false }
        var loggedIn: Bool { email != nil }
        var isReserved: Bool { reserved ?? false }
        var isHeld: Bool { reserveHeld ?? false }
        // 둘 중 더 빡빡한 창이 실제 한도를 정한다
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
    // Claude 의 다음 배정. 도구마다의 다음 배정은 nextByTool 에 있다
    let next: Next?
    let accounts: [Account]
    let sessions: [Session]
    // 계정이 있는 도구. 예전 acm 은 내지 않는다
    let tools: [String]?
    let nextByTool: [String: Next?]?

    var toolList: [String] { tools ?? ["claude"] }

    func accounts(of tool: String) -> [Account] { accounts.filter { $0.toolKey == tool } }

    func next(for tool: String) -> Next? {
        if let found = nextByTool?[tool] { return found }
        return tool == "claude" ? next : nil
    }

    // 위젯이 보일 도구. 메뉴바 창과 같은 순서이고, 고른 도구가 모두 없어졌으면 첫 도구를 보인다
    func widgetList(_ chosen: Set<String>) -> [String] {
        let list = toolList.filter(chosen.contains)
        return list.isEmpty ? [toolList.first ?? "claude"] : list
    }

    // 그 도구의 로그인한 계정 중 하나라도 5시간 한도가 있으면 5h 를 보인다. 모두 없으면(전부 Ultra 인증 계정) 5h 열을 뺀다
    func showsFiveHour(of tool: String) -> Bool { accounts(of: tool).contains { $0.loggedIn && $0.fiveHour != nil } }

    // 위젯에 열로 세울 모델별 주간 한도. 로그인한 계정 중 하나라도 가진 한도를 처음 나온 순서대로 모은다
    func scopeColumns(of tool: String) -> [Scoped] {
        var seen = Set<String>()
        return accounts(of: tool).filter(\.loggedIn).flatMap { $0.scoped ?? [] }.filter { seen.insert($0.name).inserted }
    }

    // 긴 창 열의 이름. 계정마다 창 길이가 다르면(Codex 무료와 유료) 한도라고 쓴다
    func longWindowName(of tool: String) -> String {
        let names = Set(accounts(of: tool).filter(\.loggedIn).compactMap { $0.sevenDay.name })
        return names.count == 1 ? names.first! : names.isEmpty ? Windows.week : "한도"
    }
}

enum Tools {
    static func name(_ tool: String) -> String {
        ["claude": "Claude", "codex": "Codex"][tool] ?? tool.capitalized
    }

    // 메뉴바 창에서 도구 묶음의 테두리 색. Claude 는 acm 로고와 같은 주황이다
    static func color(_ tool: String) -> Color {
        tool == "codex" ? Color(red: 0.29, green: 0.53, blue: 0.96) : Color(red: 0xD9 / 255, green: 0x77 / 255, blue: 0x57 / 255)
    }

    static func loginHint(_ account: Snapshot.Account) -> String {
        account.toolKey == "codex" ? "acm -a \(account.id) login --device-auth" : "acm -a \(account.id) auth login"
    }
}

@MainActor
final class Store: ObservableObject {
    // 메뉴바 창과 떠 있는 위젯이 같은 데이터를 본다
    static let shared = Store()

    @Published var snapshot: Snapshot?
    @Published var error: String?
    @Published var loading = false
    // 떠 있는 위젯에 보일 도구. 처음에는 예전 판에서 위젯에 보이던 도구(shownTool) 하나다
    @Published var widgetTools = Set(UserDefaults.standard.stringArray(forKey: "widgetTools")
                                     ?? [UserDefaults.standard.string(forKey: "shownTool") ?? "claude"]) {
        didSet { UserDefaults.standard.set(widgetTools.sorted(), forKey: "widgetTools") }
    }

    // 위젯에서 도구를 켜고 끈다. 위젯이 비지 않게 마지막 하나는 끄지 않는다. 위젯을 통째로 숨기려면 "떠 있는 위젯" 을 끈다
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
                        self.error = "acm 출력 해석 실패: \(error.localizedDescription)"
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

    // 시간 초과로 끊었는지. 타이머 스레드가 쓰고 run 이 읽는다
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
        // 메뉴바 앱은 셸 PATH 를 물려받지 않는다
        env["PATH"] = "\(NSHomeDirectory())/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        env.removeValue(forKey: "CLAUDE_CONFIG_DIR")
        process.environment = env
        let out = Pipe(), err = Pipe()
        process.standardOutput = out
        process.standardError = err
        do {
            try process.run()
        } catch {
            return .failure(Failure(text: "acm 을 실행하지 못했습니다: \(acmPath)"))
        }
        // acm 이 멈추면 loading 이 풀리지 않아 다음 새로고침이 영영 오지 않는다. 시간이 지나면 끊는다
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
            return .failure(Failure(text: "acm \(args.joined(separator: " ")) 가 \(Int(timeout))초 안에 끝나지 않아 끊었습니다"))
        }
        if process.terminationStatus != 0 {
            let text = String(data: errData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return .failure(Failure(text: text.isEmpty ? "acm 종료 코드 \(process.terminationStatus)" : text))
        }
        return .success(data)
    }
}

enum Fmt {
    static func duration(_ seconds: Double) -> String {
        let s = max(0, Int(seconds))
        let d = s / 86400, h = (s % 86400) / 3600, m = (s % 3600) / 60
        if d > 0 { return "\(d)일 \(h)시간" }
        if h > 0 { return "\(h)시간 \(m)분" }
        return "\(m)분"
    }

    static func resetIn(_ ts: Double?) -> String {
        guard let ts else { return "" }
        let left = ts - Date().timeIntervalSince1970
        return left <= 0 ? "리셋됨" : "\(duration(left)) 후 리셋"
    }

    // Claude 는 "Ultra" 처럼, Codex 는 "plus" 처럼 소문자로 와서 첫 글자만 대문자로 맞춘다
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
