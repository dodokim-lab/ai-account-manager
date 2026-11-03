import AppKit
import SwiftUI

// 도구 로고. 상표 이미지를 저장소에 두지 않고, 이 Mac 에 깔린 그 도구의 앱 아이콘을 빌려 쓴다.
// 앱이 없으면 도구 색 바탕에 기호를 둔다
struct ToolLogo: View {
    let tool: String
    var size: CGFloat = 16

    var body: some View {
        if let icon = ToolIcon.image(tool) {
            Image(nsImage: icon).resizable().interpolation(.high).frame(width: size, height: size)
        } else {
            Text(tool == "codex" ? ">_" : "✳︎")
                .font(.system(size: size * 0.5, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)
                .frame(width: size, height: size)
                .background(RoundedRectangle(cornerRadius: size * 0.24, style: .continuous)
                    .fill(tool == "codex" ? Color.black : Tools.color(tool)))
        }
    }
}

enum ToolIcon {
    // Claude 는 데스크톱 앱, Codex 는 Codex 앱이나 ChatGPT 앱의 아이콘
    private static let bundles = ["claude": ["com.anthropic.claudefordesktop"],
                                  "codex": ["com.openai.codex", "com.openai.chat"]]
    // 창이 그려질 때마다 앱을 찾지 않게 한 번 찾은 결과를 둔다. 메인 스레드에서만 부른다
    nonisolated(unsafe) private static var cache: [String: NSImage?] = [:]

    static func image(_ tool: String) -> NSImage? {
        if let hit = cache[tool] { return hit }
        let found = (bundles[tool] ?? []).lazy
            .compactMap { NSWorkspace.shared.urlForApplication(withBundleIdentifier: $0) }
            .first
            .map { NSWorkspace.shared.icon(forFile: $0.path) }
        cache[tool] = .some(found)
        return found
    }
}

// 메뉴바 아이콘. acm 로고의 표시와 막대만 템플릿 이미지로 그려서, 메뉴바가 밝든 어둡든 시스템이 색을 맞춘다
enum MenuIcon {
    static let image: NSImage = {
        // 로고의 그림 부분은 512 칸 중 x 72~440, y 148~352 다
        let size = NSSize(width: 22, height: 16)
        let image = NSImage(size: size, flipped: true) { _ in
            let k: CGFloat = 20 / 368
            let dx = (size.width - 368 * k) / 2 - 72 * k, dy = (size.height - 204 * k) / 2 - 148 * k
            func rect(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> NSRect {
                NSRect(x: dx + x * k, y: dy + y * k, width: w * k, height: h * k)
            }
            NSColor.black.setFill()
            let mark = NSBezierPath()
            mark.move(to: NSPoint(x: dx + 72 * k, y: dy + 148 * k))
            mark.line(to: NSPoint(x: dx + 144 * k, y: dy + 196 * k))
            mark.line(to: NSPoint(x: dx + 72 * k, y: dy + 244 * k))
            mark.close()
            mark.fill()
            for (y, used) in [(160.0, 184.0), (280.0, 104.0)] {
                NSColor.black.withAlphaComponent(0.35).setFill()
                NSBezierPath(roundedRect: rect(172, y, 268, 72), xRadius: 36 * k, yRadius: 36 * k).fill()
                NSColor.black.setFill()
                NSBezierPath(roundedRect: rect(172, y, used, 72), xRadius: 36 * k, yRadius: 36 * k).fill()
            }
            return true
        }
        image.isTemplate = true
        return image
    }()
}

// acm 로고. docs/logo.svg 와 같은 그림이다: 다음 배정 표시와 사용량 막대 두 개
struct AppLogo: View {
    var size: CGFloat = 22

    var body: some View {
        Canvas { ctx, area in
            let k = area.width / 512
            func rect(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect {
                CGRect(x: x * k, y: y * k, width: w * k, height: h * k)
            }
            ctx.fill(Path(rect(0, 0, 512, 512)), with: .color(Tools.color("claude")))
            var mark = Path()
            mark.move(to: CGPoint(x: 72 * k, y: 148 * k))
            mark.addLine(to: CGPoint(x: 144 * k, y: 196 * k))
            mark.addLine(to: CGPoint(x: 72 * k, y: 244 * k))
            mark.closeSubpath()
            ctx.fill(mark, with: .color(Color(red: 0x1F / 255, green: 0x1E / 255, blue: 0x1D / 255)))
            let cream = Color(red: 0xF5 / 255, green: 0xF0 / 255, blue: 0xE8 / 255)
            for (y, used) in [(160.0, 184.0), (280.0, 104.0)] {
                ctx.fill(Path(roundedRect: rect(172, y, 268, 72), cornerRadius: 36 * k), with: .color(cream.opacity(0.4)))
                ctx.fill(Path(roundedRect: rect(172, y, used, 72), cornerRadius: 36 * k), with: .color(cream))
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: size * 0.22, style: .continuous))
    }
}
