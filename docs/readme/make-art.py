r"""Draw the README image and the GitHub social preview for acm.

    python3 docs/readme/make-art.py docs/readme/hero.svg /tmp/social-preview.svg
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
      --force-device-scale-factor=1 --window-size=1280,640 \
      --screenshot=docs/readme/social-preview.png file:///tmp/social-preview.svg

The accounts are made up and use example.com. The cards copy the menu bar window in app/Sources/Panel.swift,
so redraw them when the window changes. GitHub has no API for the social preview. Upload the PNG under
Settings, General, Social preview.
"""
import sys
from xml.sax.saxutils import escape

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
INK = "#1F1E1D"
CREAM = "#F5F0E8"
CLAUDE = "#D97757"
CODEX = "#4A87F5"
GRAY = "#6B6862"
GREEN, ORANGE, RED = "#34C759", "#FF9500", "#FF3B30"


def gauge_color(p):
    return RED if p >= 90 else ORANGE if p >= 70 else GREEN


def t(x, y, s, size=12, fill=INK, weight="normal", family=SANS, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')


def logo(x, y, size):
    k = size / 512
    return (f'<g transform="translate({x},{y}) scale({k})">'
            f'<rect width="512" height="512" rx="96" fill="{CLAUDE}"/>'
            f'<path d="M72 148 L144 196 L72 244 Z" fill="{INK}"/>'
            f'<rect x="172" y="160" width="268" height="72" rx="36" fill="{CREAM}" fill-opacity="0.4"/>'
            f'<rect x="172" y="160" width="184" height="72" rx="36" fill="{CREAM}"/>'
            f'<rect x="172" y="280" width="268" height="72" rx="36" fill="{CREAM}" fill-opacity="0.4"/>'
            f'<rect x="172" y="280" width="104" height="72" rx="36" fill="{CREAM}"/></g>')


def usage_bar(x, y, w, title, pct, reset):
    """One gauge row like UsageBar in the app: title 42, gauge, percent 36, reset 96, gaps 6."""
    gw = w - 42 - 36 - 96 - 18
    gx = x + 48
    c = gauge_color(pct)
    return "".join([
        t(x, y + 4, title, 11, INK),
        f'<rect x="{gx}" y="{y - 4}" width="{gw}" height="8" rx="4" fill="{INK}" fill-opacity="0.12"/>',
        f'<rect x="{gx}" y="{y - 4}" width="{gw * pct / 100:.1f}" height="8" rx="4" fill="{c}"/>',
        t(gx + gw + 6 + 36, y + 4, f"{pct}%", 11, c, "600", anchor="end"),
        t(x + w, y + 4, reset, 10, GRAY, anchor="end"),
    ])


def card(x, y, w, a, color=None):
    h = 62
    ring = f' stroke="{color}" stroke-width="2"' if a.get("picked") else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{INK}" fill-opacity="0.05"{ring}/>']
    ix, iw = x + 8, w - 16
    out.append(t(ix, y + 18, a["label"], 12.5, INK, "bold"))
    # Bold label widths measured in the rendered image, since SVG cannot flow a pill after text
    lw = {"home": 36, "work": 34, "spare": 38, "main": 33, "side": 29}[a["label"]] + 7
    out.append(t(ix + lw, y + 18, a["email"], 11, GRAY))
    pw = len(a["plan"]) * 6.4 + 8
    px = ix + lw + len(a["email"]) * 6.75 + 6
    out.append(f'<rect x="{px:.1f}" y="{y + 8}" width="{pw:.1f}" height="14" rx="7" fill="{INK}" fill-opacity="0.08"/>')
    out.append(t(px + pw / 2, y + 18.5, a["plan"], 10, GRAY, anchor="middle"))
    right = ix + iw
    sess = f'{a["sessions"]} session{"" if a["sessions"] == 1 else "s"}'
    out.append(t(right, y + 18, sess, 11, GRAY, anchor="end"))
    if a.get("near"):
        nx = right - len(sess) * 6.2 - 8 - 62
        out.append(f'<rect x="{nx:.1f}" y="{y + 7.5}" width="62" height="15" rx="7.5" fill="{RED}"/>')
        out.append(t(nx + 31, y + 18.5, "Near limit", 10, "#FFFFFF", "bold", anchor="middle"))
    out.append(usage_bar(ix, y + 36, iw, "5h", a["five"], a["five_reset"]))
    out.append(usage_bar(ix, y + 52, iw, "Week", a["week"], a["week_reset"]))
    return "".join(out), h


def tool_box(x, y, w, name, color, next_line, accounts, mark):
    inner = []
    cy = y + 50
    for a in accounts:
        svg, h = card(x + 10, cy, w - 20, a, color)
        inner.append(svg)
        cy += h + 6
    h = cy - y + 4
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{color}" fill-opacity="0.08" '
           f'stroke="{color}" stroke-opacity="0.6"/>']
    out.append(mark(x + 10, y + 9))
    out.append(t(x + 38, y + 25, name, 13.5, INK, "bold"))
    out.append(t(x + 10, y + 43, next_line, 10.5, GRAY))
    return "".join(out + inner), h


def claude_mark(x, y):
    return f'<rect x="{x}" y="{y}" width="22" height="22" rx="6" fill="{CLAUDE}"/>' + \
           t(x + 11, y + 16, "C", 13, "#FFFFFF", "bold", anchor="middle")


def codex_mark(x, y):
    return f'<rect x="{x}" y="{y}" width="22" height="22" rx="6" fill="{CODEX}"/>' + \
           t(x + 11, y + 16, ">_", 11, "#FFFFFF", "bold", family=MONO, anchor="middle")


CLAUDE_ACCOUNTS = [
    dict(label="home", email="home@example.com", plan="Max", sessions=1, five=64, five_reset="Resets in 1h 40m",
         week=35, week_reset="Resets in 2d 3h"),
    dict(label="work", email="work@example.com", plan="Max", sessions=2, picked=True, five=12, five_reset="Resets in 4h 5m",
         week=31, week_reset="Resets in 3d 10h"),
    dict(label="spare", email="spare@example.com", plan="Pro", sessions=0, five=97, five_reset="Resets in 25m",
         week=58, week_reset="Resets in 5d 1h", near=True),
]
CODEX_ACCOUNTS = [
    dict(label="main", email="home@example.com", plan="Plus", sessions=1, five=48, five_reset="Resets in 2h 50m",
         week=74, week_reset="Resets in 1d 6h"),
    dict(label="side", email="side@example.com", plan="Plus", sessions=0, picked=True, five=5, five_reset="Resets in 4h 30m",
         week=12, week_reset="Resets in 4d 5h"),
]
CLAUDE_NEXT = "Next session → work  (5h 12% · Week 31% · score 124 · running 2)"
CODEX_NEXT = "Next session → side  (5h 5% · Week 12% · score 140 · running 0)"


def panel(x, y, w=420):
    """The menu bar window with fake accounts. Returns svg, height, and the y of the two picked cards."""
    out = []
    body = []
    body.append(logo(x + 14, y + 13, 22))
    body.append(t(x + 44, y + 29, "AI Account Manager", 14, INK, "bold"))
    cy = y + 48
    box, h1 = tool_box(x + 14, cy, w - 28, "Claude", CLAUDE, CLAUDE_NEXT, CLAUDE_ACCOUNTS, claude_mark)
    body.append(box)
    work_y = cy + 50 + 68 + 31
    cy += h1 + 10
    box, h2 = tool_box(x + 14, cy, w - 28, "Codex", CODEX, CODEX_NEXT, CODEX_ACCOUNTS, codex_mark)
    body.append(box)
    side_y = cy + 50 + 68 + 31
    cy += h2 + 10
    h = cy + 4 - y
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#FFFFFF" stroke="{INK}" '
               f'stroke-opacity="0.14"/>')
    return "".join(out + body), h, work_y, side_y


def terminal(x, y, w, h, lines):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{INK}"/>']
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        out.append(f'<circle cx="{x + 18 + i * 18}" cy="{y + 16}" r="5.5" fill="{c}"/>')
    ly = y + 50
    for kind, s in lines:
        if kind == "gap":
            ly += 12
            continue
        if kind == "cmd":
            prompt, cmd = s
            out.append(f'<text x="{x + 18}" y="{ly}" font-family="{MONO}" font-size="13">'
                       f'<tspan fill="#9C9A92">{escape(prompt)}</tspan><tspan fill="{CREAM}" font-weight="bold">'
                       f' {escape(cmd)}</tspan></text>')
        else:
            out.append(t(x + 18, ly, s, 13, kind, family=MONO))
        ly += 21
    return "".join(out)


def shared_rows(x, y):
    """Account tags joined to the one folder every account of that tool reads."""
    out = []
    rows = [("Claude", CLAUDE, ["cl1", "cl2", "cl3"], "~/.claude"), ("Codex", CODEX, ["cx1", "cx2"], "~/.codex")]
    for i, (name, color, ids, folder) in enumerate(rows):
        ry = y + i * 46
        tx = x
        for acc in ids:
            out.append(f'<rect x="{tx}" y="{ry}" width="44" height="26" rx="13" fill="{color}" fill-opacity="0.14" '
                       f'stroke="{color}" stroke-opacity="0.6"/>')
            out.append(t(tx + 22, ry + 17.5, acc, 12, INK, "600", family=MONO, anchor="middle"))
            tx += 50
        ax = x + 3 * 50 + 4
        out.append(f'<path d="M{ax} {ry + 13} H{ax + 40}" stroke="{color}" stroke-width="2"/>')
        out.append(f'<path d="M{ax + 40} {ry + 8} L{ax + 48} {ry + 13} L{ax + 40} {ry + 18} Z" fill="{color}"/>')
        bx = ax + 56
        out.append(f'<rect x="{bx}" y="{ry - 2}" width="352" height="30" rx="8" fill="#FFFFFF" stroke="{INK}" '
                   f'stroke-opacity="0.14"/>')
        out.append(f'<text x="{bx + 12}" y="{ry + 18}" font-size="12.5" font-family="{SANS}">'
                   f'<tspan font-family="{MONO}" font-weight="bold" fill="{INK}">{escape(folder)}</tspan>'
                   f'<tspan fill="{GRAY}" dx="10">memory · history · settings · skills</tspan></text>')
    return "".join(out)


def connector(x1, y1, x2, y2, color):
    mx = (x1 + x2) / 2
    return (f'<path d="M{x1} {y1} C {mx} {y1}, {mx} {y2}, {x2 - 8} {y2}" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-dasharray="5 4"/>'
            f'<path d="M{x2 - 9} {y2 - 5} L{x2} {y2} L{x2 - 9} {y2 + 5} Z" fill="{color}"/>')


def hero(path):
    W, H = 1120, 572
    p_x, p_y = 670, 24
    psvg, ph, work_y, side_y = panel(p_x, p_y)
    tx, ty, tw, th = 32, 84, 560, 196
    lines = [
        ("cmd", ("~/work/shop $", "claude")),
        ("#E8B4A2", "acm: work [cl2] (work@example.com) \u00b7 5h 12% \u00b7"),
        ("#E8B4A2", "Week 31% \u00b7 score 124 \u00b7 running 2"),
        ("gap", None),
        ("cmd", ("~/side/app $", "codex")),
        ("#A9C5FA", "acm: Codex side [cx2] (side@example.com, plus) \u00b7"),
        ("#A9C5FA", "5h 5% \u00b7 Week 12% \u00b7 score 140 \u00b7 running 0"),
    ]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" rx="18" fill="{CREAM}"/>',
           t(tx, 48, "Type claude or codex as usual.", 22, INK, "bold"),
           t(tx + 1, 70, "acm starts the session on the account with the most headroom.", 14, GRAY),
           terminal(tx, ty, tw, th, lines)]
    sy = ty + th + 52
    out.append(t(tx, sy, "Whichever account it lands on, your context is the same.", 16, INK, "bold"))
    out.append(t(tx, sy + 21, "Every account of a tool shares one folder.", 13.5, GRAY))
    out.append(shared_rows(tx, sy + 44))
    out.append(psvg)
    # From each launch message to the card it picked, drawn over the panel
    out.append(connector(tx + tw, ty + 78, p_x + 24, work_y, CLAUDE))
    out.append(connector(tx + tw, ty + 153, p_x + 24, side_y, CODEX))
    out.append("</svg>")
    open(path, "w").write("\n".join(out) + "\n")
    return ph


def social(path):
    W, H = 1280, 640
    psvg, ph, work_y, side_y = panel(0, 0)
    scale = 1.18
    px = W - 420 * scale - 64
    py = (H - ph * scale) / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="{CREAM}"/>',
           logo(72, 92, 96),
           t(72, 250, "ai-account-manager", 46, INK, "bold"),
           t(72, 304, "One launcher for several Claude Code", 25, INK),
           t(72, 338, "and Codex CLI accounts.", 25, INK),
           t(72, 400, "Each session starts on the account", 19, GRAY),
           t(72, 428, "with the most headroom, and every", 19, GRAY),
           t(72, 456, "account shares one ~/.claude.", 19, GRAY),
           t(72, 548, "github.com/dodokim-lab/ai-account-manager", 17, GRAY, family=MONO),
           f'<g transform="translate({px:.1f},{py:.1f}) scale({scale})">{psvg}</g>',
           "</svg>"]
    open(path, "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    hero(sys.argv[1])
    social(sys.argv[2])
