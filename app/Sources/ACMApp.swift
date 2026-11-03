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
            // Usage only makes sense with the window open, so the menu bar shows just the logo
            Image(nsImage: MenuIcon.image).accessibilityLabel("AI Account Manager")
        }
        .menuBarExtraStyle(.window)
    }
}
