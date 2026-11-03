import SwiftUI

// A gauge that fills up to the usage. The fill animates when it first appears and when the value changes.
struct GaugeBar: View {
    let pct: Double
    var height: CGFloat = 6
    @State private var shown: Double = 0

    static func color(_ pct: Double) -> Color {
        pct >= 90 ? .red : pct >= 70 ? .orange : .green
    }

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(Color.primary.opacity(0.12))
                Capsule()
                    .fill(Self.color(pct).gradient)
                    .frame(width: geo.size.width * min(max(shown, 0), 100) / 100)
            }
        }
        .frame(height: height)
        .onAppear { withAnimation(.easeOut(duration: 0.8)) { shown = pct } }
        .onChange(of: pct) { _, value in withAnimation(.easeOut(duration: 0.6)) { shown = value } }
    }
}

enum Windows {
    static let fiveHour = "5h"
    static let week = "Week"
}
