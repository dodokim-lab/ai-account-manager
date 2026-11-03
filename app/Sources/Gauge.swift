import SwiftUI

// 사용량만큼 차오르는 게이지. 처음 나타날 때와 값이 바뀔 때 채워지는 애니메이션을 한다.
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
