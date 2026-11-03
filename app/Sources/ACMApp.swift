import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        MainActor.assumeIsolated { FloatingWidget.shared.showIfEnabled() }
    }
}

@main
struct ACMApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @StateObject private var store = Store.shared

    var body: some Scene {
        MenuBarExtra {
            PanelView(store: store)
        } label: {
            // 사용량은 창을 열어야 뜻이 있어서 메뉴바에는 로고만 둔다
            Image(nsImage: MenuIcon.image).accessibilityLabel("AI Account Manager")
        }
        .menuBarExtraStyle(.window)
    }
}
