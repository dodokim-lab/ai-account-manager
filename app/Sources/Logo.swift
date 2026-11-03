import AppKit
import SwiftUI

// Tool logo. Trademarked images are not kept in the repo. It borrows the icon of the tool's app installed on this Mac.
// Without the app, it shows a symbol on the tool color
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
    // The Claude desktop app icon for Claude, and the Codex app or ChatGPT app icon for Codex
    private static let bundles = ["claude": ["com.anthropic.claudefordesktop"],
                                  "codex": ["com.openai.codex", "com.openai.chat"]]
    // Keep the first lookup so the app is not searched on every redraw. Call only from the main thread
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

// Menu bar icon. Only the mark and bars of the acm logo are drawn as a template image, so the system sets the color for a light or dark menu bar
enum MenuIcon {
    static let image: NSImage = {
        // The drawn part of the logo spans x 72 to 440 and y 148 to 352 of 512
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

// acm logo. Same drawing as docs/logo.svg: the next-pick mark and two usage bars
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
