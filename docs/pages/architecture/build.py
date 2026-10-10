"""Builds the qa-factory architecture page: diagrams as inline SVG, laid out on a grid.

    python3 docs/pages/architecture/build.py [OUT]

Writes the page (default `.artifacts/pages/qa-factory-architecture.html`, gitignored) from
`template.html` and the first run's `summary.json`. Published at
https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa; a later session republishes the built file with
that URL so the link stays the same. The text of the page lives in the template; the diagrams and
charts are drawn here.
"""
import html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".artifacts" / "pages" / "qa-factory-architecture.html"
SUM = json.load(open(ROOT / "docs/runs/2026-10-08-linkding-sort-by-modified/summary.json"))

def esc(s): return html.escape(s, quote=True)

def text(x, y, s, cls="", anchor="middle", extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'

def box(x, y, w, h, kind, rx=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="box {kind}"/>'

def arrow(x1, y1, x2, y2, cls="edge", marker="ah"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#{marker})"/>'

def defs(prefix):
    return (f'<defs>'
            f'<marker id="{prefix}ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah"/></marker>'
            f'<marker id="{prefix}ahd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah-dim"/></marker>'
            f'<marker id="{prefix}ahf" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah-fail"/></marker>'
            f'<marker id="{prefix}ahp" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ah-pass"/></marker>'
            f'</defs>')

def badge(cx, cy, letter):
    return f'<circle cx="{cx}" cy="{cy}" r="9" class="badge"/>' + text(cx, cy + 4, letter, "t-badge")

def label_bg(cx, cy, s, size=10.5):
    w = len(s) * size * 0.54 + 12
    return (f'<rect x="{cx - w/2:.1f}" y="{cy - size - 2:.1f}" width="{w:.1f}" height="{size + 8:.1f}" rx="4" class="label-bg"/>'
            + text(cx, cy, s, "t-edge"))

# ---------------------------------------------------------------- 1. the flow
def flow_svg():
    W, H = 1168, 330
    nw, gap, y, nh = 112, 16, 96, 76
    nodes = [
        ("Ticket", ["from upstream", "PR 1363"], "io", "→ ticket.json", None, "A"),
        ("Frame", ["Sonnet 5.5", "13 s · 0.03 USD"], "ai", "→ criteria", None, None),
        ("Plan", ["Sonnet 5.5", "14 s · 0.07 USD"], "ai", "→ test placement", None, None),
        ("Implement", ["the developers'", "real commit"], "det", "→ diff, file lists", None, "G"),
        ("Verify", ["6 stages", "800 s · 4.90 USD"], "mixed", "→ tests + cases", None, "CD"),
        ("You", ["approve", "or decline"], "person", "→ answer.json", None, "E"),
        ("Review", ["Opus 5.5", "by hand: 53 s"], "ai", "→ findings", "not yet run as a step", None),
        ("Ship", ["git commit", "+ full suite"], "det", "→ a commit", "not yet run as a step", None),
        ("App's suite", ["linkding's own", "test folders"], "io", "tests join here", None, "F"),
    ]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="The flow: a ticket passes Frame, Plan, Implement and Verify, stops for your approval, then Review and Ship add the tests to the application\'s own suite. The loops back to Implement are planned and not built." class="dia">', defs("f")]
    xs = [16 + i * (nw + gap) for i in range(len(nodes))]
    cx = [x + nw / 2 for x in xs]
    p.append(f'<path d="M{cx[4]} 96 C{cx[4]} 40, {cx[3]+10} 40, {cx[3]+10} 92" class="edge-dash" marker-end="url(#fahd)"/>')
    p.append(f'<path d="M{cx[6]} 96 C{cx[6]} -10, {cx[3]-10} -10, {cx[3]-10} 92" class="edge-dash" marker-end="url(#fahd)"/>')
    p.append(label_bg((cx[4] + cx[3]) / 2 + 5, 52, "fail → fix (planned)"))
    p.append(label_bg((cx[6] + cx[3]) / 2 + 20, 22, "findings → fix (planned)"))
    for i, (name, subs, kind, hands, warn, letters) in enumerate(nodes):
        x = xs[i]; c = cx[i]
        p.append(box(x, y, nw, nh, kind))
        if warn:
            p.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="8" class="box-notyet"/>')
        p.append(text(c, y + 26, name, "t-title"))
        p.append(text(c, y + 46, subs[0], "t-sub"))
        p.append(text(c, y + 62, subs[1], "t-sub"))
        p.append(text(c, y + nh + 20, hands, "t-hand"))
        if warn:
            p.append(text(c, y + nh + 36, warn, "t-warn"))
        if i < len(nodes) - 1:
            p.append(arrow(x + nw + 1, y + nh / 2, x + nw + gap - 2, y + nh / 2, "edge", "fah"))
        if letters:
            for j, ch in enumerate(letters):
                p.append(badge(x + 10 + j * 20, y - 2, ch))
    p.append(text(cx[5], 80, "run parked here", "t-park"))
    p.append(f'<rect x="{xs[1]}" y="226" width="{xs[-1] + nw - xs[1]}" height="30" rx="6" class="band"/>')
    p.append(badge(xs[1] + 16, 241, "B"))
    p.append(text(xs[1] + 34, 245, "Application recipe: app.json, strategy.md, fetch.py, tickets. One set per application; linkding is the only one today.", "t-band", "start"))
    p.append(f'<rect x="16" y="264" width="{xs[-1] + nw - 16}" height="30" rx="6" class="band"/>')
    p.append(badge(32, 279, "H"))
    p.append(text(50, 283, "Driver: one Python process runs the steps in order, one ticket at a time, one run folder per ticket; a re-run resumes.", "t-band", "start"))
    lx = 16; ly = 318
    items = [("ai", "AI, Claude Code headless"), ("det", "deterministic: git, pytest, mutmut"), ("mixed", "AI writes, tools check"), ("person", "a person decides"), ("io", "input or destination")]
    for kind, lab in items:
        p.append(f'<rect x="{lx}" y="{ly - 10}" width="18" height="12" rx="3" class="box {kind}"/>')
        p.append(text(lx + 24, ly, lab, "t-legend", "start"))
        lx += 24 + len(lab) * 6.1 + 22
    p.append(f'<line x1="{lx:.0f}" y1="{ly - 4}" x2="{lx + 28:.0f}" y2="{ly - 4}" class="edge-dash"/>')
    p.append(text(round(lx + 34), ly, "planned, not built", "t-legend", "start"))
    p.append("</svg>")
    return "\n".join(p)

# ---------------------------------------------------------------- 2. inside Verify
def verify_svg():
    W, H = 1204, 300
    bw, gap, y, bh = 152, 18, 40, 84
    st = [
        ("1  Write tests", "Claude Code, Opus", "414 s · 3.62 USD", "ai", ["it edits app code,", "edits an existing test,", "or writes no API test"]),
        ("2  Lint", "ruff + AST check", "0.1 s", "det", ["any ruff finding, a test", "without an assertion,", "a sleep, a mock of app code"]),
        ("3  Revert check", "pytest + plugin", "18 s", "det", ["a test crashes or misses", "a name on the old code,", "or none proves behaviour"]),
        ("4  Mutation", "mutmut 3.8.0", "159 s, two runs", "det", ["no mutant is checked,", "or none is killed on", "the changed lines"]),
        ("5  App's suite", "pytest, Playwright", "93 s", "det", ["any test is red", "(1294 API and unit,", "83 browser)"]),
        ("6  Test cases", "Claude Code, Opus", "116 s · 1.28 USD", "ai", ["the case linter still", "finds issues after", "one repair"]),
        ("Question to you", "question.md", "the run exits 2", "person", None),
    ]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Inside Verify: six stages in order, each able to stop the run, then a question to you." class="dia">', defs("v")]
    xs = [16 + i * (bw + gap) for i in range(len(st))]
    p.append(text(16, 22, "what moves:", "t-cap", "start"))
    moves = ["2 test files", "clean files", "verdict per test", "scores", "green suite", "6 cases"]
    for i, (title, tool, meas, kind, stop) in enumerate(st):
        x = xs[i]; cx = x + bw / 2
        p.append(box(x, y, bw, bh, kind))
        p.append(text(cx, y + 26, title, "t-title"))
        p.append(text(cx, y + 47, tool, "t-mono"))
        p.append(text(cx, y + 67, meas, "t-sub"))
        if i < len(st) - 1:
            p.append(arrow(x + bw + 1, y + bh / 2, x + bw + gap - 2, y + bh / 2, "edge", "vah"))
            p.append(text(x + bw + gap / 2, y - 8, moves[i], "t-move"))
        if stop:
            p.append(text(cx, y + bh + 22, "STOPS THE RUN IF", "t-cap"))
            for j, line in enumerate(stop):
                p.append(text(cx, y + bh + 40 + j * 15, line, "t-stop"))
            p.append(arrow(cx, y + bh + 82, cx, 238, "edge-fail", "vahf"))
        else:
            p.append(text(cx, y + bh + 22, "WAITS FOR", "t-cap"))
            p.append(text(cx, y + bh + 40, "answer.json", "t-stop"))
    p.append(f'<line x1="{xs[0] + bw/2}" y1="242" x2="{xs[5] + bw/2}" y2="242" class="rail"/>')
    p.append(text((xs[0] + xs[5] + bw) / 2, 268, "The run stops with a fail record and exit 1. Nothing loops back to the writer yet; a retry is a fresh run of Verify.", "t-railtext"))
    p.append("</svg>")
    return "\n".join(p)

# ---------------------------------------------------------------- 3. the revert check
def revert_svg():
    W, H = 1000, 286
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="The revert check: the new tests run on the new code, where all six pass, and on the old code with the same tests, where five fail on an assertion and one still passes." class="dia">', defs("r")]
    p.append(box(16, 40, 200, 58, "det")); p.append(text(116, 64, "Base commit 0837b51", "t-title")); p.append(text(116, 84, "the code before the change", "t-sub"))
    p.append(box(16, 196, 200, 58, "det")); p.append(text(116, 220, "Head commit 0490013", "t-title")); p.append(text(116, 240, "the change, plus the new tests", "t-sub"))
    p.append(box(320, 40, 210, 58, "mixed")); p.append(text(425, 64, "Reverted tree", "t-title")); p.append(text(425, 84, "old code + the new tests", "t-sub"))
    p.append(box(320, 196, 210, 58, "mixed")); p.append(text(425, 220, "Head tree", "t-title")); p.append(text(425, 240, "new code + the new tests", "t-sub"))
    p.append(arrow(217, 69, 318, 69, "edge", "rah")); p.append(label_bg(268, 60, "3 source files"))
    p.append(arrow(217, 225, 318, 225, "edge", "rah")); p.append(label_bg(268, 216, "as committed"))
    p.append(arrow(217, 206, 318, 92, "edge", "rah")); p.append(label_bg(262, 152, "6 new tests"))
    # head outcome
    p.append(box(640, 196, 344, 58, "pass-box")); p.append(text(812, 220, "6 of 6 pass", "t-title")); p.append(text(812, 240, "required before anything else counts", "t-sub"))
    p.append(arrow(531, 225, 638, 225, "edge", "rah")); p.append(label_bg(585, 216, "pytest"))
    rows = [
        ("Fails on an assertion in the test or a helper", "proves behaviour", "5", "pass-row"),
        ("Still passes on the old code", "regression guard, allowed", "1", "dim-row"),
        ("Fails because a name is missing", "rejected", "0", "fail-row"),
        ("Fails with any other exception", "rejected as a crash", "0", "fail-row"),
    ]
    for i, (what, verdict, n, cls) in enumerate(rows):
        ry = 14 + i * 40
        p.append(f'<rect x="640" y="{ry}" width="344" height="32" rx="6" class="{cls}"/>')
        p.append(text(652, ry + 14, what, "t-row", "start"))
        p.append(text(652, ry + 27, verdict, "t-rowsub", "start"))
        p.append(text(970, ry + 22, n, "t-count", "end"))
        p.append(f'<path d="M531 69 C590 69, 590 {ry + 16}, 636 {ry + 16}" class="edge-thin" marker-end="url(#rah)"/>')
    p.append(text(425, 122, "pytest, each failure sorted", "t-edge"))
    p.append("</svg>")
    return "\n".join(p)

# ---------------------------------------------------------------- 4. where everything lives
def lives_svg():
    W, H = 1000, 462
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Where everything lives: the factory repository, the run folders, the application cache and Claude Code on this laptop; the Anthropic API and two GitHub repositories outside it." class="dia">', defs("w")]
    p.append(f'<rect x="10" y="40" width="742" height="410" rx="12" class="frame"/>')
    p.append(text(26, 62, "THIS LAPTOP", "t-cap", "start"))
    def panel(x, y, w, h, title, lines, kind="det", note=None):
        out = [box(x, y, w, h, kind), text(x + 14, y + 24, title, "t-title", "start")]
        for j, (a, b) in enumerate(lines):
            out.append(text(x + 14, y + 46 + j * 19, a, "t-mono", "start"))
            if b: out.append(text(x + w - 14, y + 46 + j * 19, b, "t-sub", "end"))
        if note: out.append(text(x + 14, y + h - 12, note, "t-warn", "start"))
        return "\n".join(out)
    p.append(panel(30, 76, 286, 150, "Factory repository", [
        ("~/dev/qa-factory", ""), ("factory/", "driver, steps, checks"), ("targets/linkding/", "recipe, tickets"),
        ("tests/", "100 factory tests"), ("docs/", "status, log, decisions, runs")]))
    p.append(panel(30, 268, 286, 166, "Run folders", [
        (".artifacts/runs/<ticket>/", ""), ("steps/", "one record per step"), ("verify/ and the rest", "each step's files"),
        ("question.md", "the gate's question"), ("answer.json", "your answer, used once")],
        note="local only, gitignored · 48 MB per run"))
    p.append(panel(386, 76, 352, 178, "Application cache", [
        ("~/Library/Caches/qa-factory/linkding", ""), ("repo/", "release 1.47.0 · 7 MB"), (".venv/", "Python 3.13.15 · 294 MB"),
        ("", "Django 6.0.7, pytest 9.0.3, mutmut 3.8.0"), ("wt/<ticket>/base", "6 MB"),
        ("wt/<ticket>/head", "61 MB, 47 MB node_modules"), ("~/Library/Caches/ms-playwright", "Chromium · 1.1 GB")]))
    p.append(panel(386, 300, 352, 90, "Claude Code 2.1.295", [
        ("claude -p", "a fresh session per call"), ("working directory", "the ticket's head worktree")], kind="ai"))
    p.append(panel(790, 76, 196, 76, "GitHub", [("OlegKonyk/qa-factory", ""), ("", "private · pull requests")]))
    p.append(panel(790, 186, 196, 76, "GitHub", [("sissbruecker/linkding", ""), ("", "upstream · read only")]))
    p.append(panel(790, 300, 196, 76, "Anthropic API", [("Sonnet 5.5, Opus 5.5", ""), ("", "billed per call")], kind="ai"))
    p.append(arrow(173, 227, 173, 266, "edge", "wah")); p.append(label_bg(248, 250, "driver writes records"))
    p.append(arrow(317, 150, 384, 150, "edge", "wah")); p.append(label_bg(351, 140, "checks run"))
    p.append('<path d="M317 205 C352 205, 352 345, 384 345" class="edge" marker-end="url(#wah)"/>'); p.append(label_bg(351, 296, "steps call"))
    p.append(arrow(562, 299, 562, 256, "edge", "wah")); p.append(label_bg(630, 282, "writes the tests"))
    p.append(arrow(739, 345, 788, 345, "edge", "wah")); p.append(label_bg(764, 333, "calls"))
    p.append(arrow(788, 224, 740, 224, "edge", "wah")); p.append(label_bg(764, 212, "clone"))
    p.append('<path d="M173 76 V24 H888 V74" class="edge" marker-end="url(#wah)"/>'); p.append(label_bg(540, 28, "sessions push branches and merge pull requests"))
    p.append("</svg>")
    return "\n".join(p)

# ---------------------------------------------------------------- charts
def bars_svg(rows, unit, fmt, label, maxv, aria):
    W, rowh, top, left, right = 760, 30, 10, 170, 80
    H = top + rowh * len(rows) + 30
    plot = W - left - right
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(aria)}" class="chart">']
    ticks = [maxv * k / 4 for k in range(5)]
    for t in ticks:
        x = left + plot * t / maxv
        p.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + rowh * len(rows)}" class="grid"/>')
        p.append(text(round(x, 1), top + rowh * len(rows) + 18, fmt(t), "t-tick"))
    for i, (name, v, note) in enumerate(rows):
        y = top + i * rowh + 8; h = 14
        w = max(plot * v / maxv, 1.5)
        p.append(f'<g class="bar"><title>{esc(name)}: {esc(fmt(v))}{esc(" · " + note if note else "")}</title>')
        p.append(f'<rect x="{left - 160}" y="{y - 8}" width="{W - 20}" height="{rowh}" class="hit"/>')
        if w > 5:
            p.append(f'<path d="M{left} {y} h{w - 4:.1f} a4 4 0 0 1 4 4 v{h - 8} a4 4 0 0 1 -4 4 h-{w - 4:.1f} z" class="barfill"/>')
        else:
            p.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{h}" class="barfill"/>')
        p.append(text(left - 12, y + 11, name, "t-barlabel", "end"))
        p.append(text(round(left + w + 8, 1), y + 11, fmt(v) + (f"  {note}" if note else ""), "t-barval", "start"))
        p.append("</g>")
    p.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + rowh * len(rows)}" class="axis"/>')
    p.append("</svg>")
    return "\n".join(p)

steps = SUM["steps"]; vt = SUM["verify"]["timings_s"]; costs = SUM["verify"]["costs"]
time_rows = [
    ("Frame", steps["frame"]["duration_s"], ""), ("Plan", steps["plan"]["duration_s"], ""),
    ("Implement", steps["implement"]["duration_s"], ""), ("Write tests", vt["write_tests"], ""),
    ("Lint", vt["lint"], ""), ("Revert check", vt["revert"], ""), ("Mutation", vt["mutation"], "two runs"),
    ("App's suite", vt["suite"], ""), ("Test cases", vt["test_cases"], ""),
]
total_s = sum(r[1] for r in time_rows)
cost_rows = [
    ("Write tests", costs["write_tests"]["cost_usd"], "Opus"), ("Test cases", costs["test_cases"]["cost_usd"], "Opus"),
    ("Review", SUM["review_dry_run"]["metrics"]["cost_usd"], "Opus, by hand"),
    ("Plan", steps["plan"]["metrics"]["cost_usd"], "Sonnet"), ("Frame", steps["frame"]["metrics"]["cost_usd"], "Sonnet"),
]
total_usd = sum(r[1] for r in cost_rows)
def fmt_s(v): return "0 s" if v == 0 else (f"{v:.0f} s" if v >= 1 else f"{v:.2f} s")
def fmt_usd(v): return f"{v:.2f} USD"
chart_time = bars_svg(time_rows, "s", fmt_s, "seconds", 480, f"Time per stage, Frame through Verify: {total_s/60:.1f} minutes in all, the test writer {vt['write_tests']:.0f} seconds of it.")
chart_cost = bars_svg(cost_rows, "USD", fmt_usd, "USD", 4, f"Model spend per call: {total_usd:.2f} USD in all, the test writer {costs['write_tests']['cost_usd']:.2f} of it.")

mut = SUM["verify"]["mutation"]
gen, both = mut["generated"], mut["generated_and_developers"]

page = pathlib.Path(__file__).with_name("template.html").read_text()
page = (page.replace("{{FLOW}}", flow_svg()).replace("{{VERIFY}}", verify_svg()).replace("{{REVERT}}", revert_svg())
        .replace("{{LIVES}}", lives_svg()).replace("{{CHART_TIME}}", chart_time).replace("{{CHART_COST}}", chart_cost)
        .replace("{{TOTAL_MIN}}", f"{total_s/60:.1f}").replace("{{TOTAL_USD}}", f"{total_usd:.2f}")
        .replace("{{WRITER_SHARE}}", f"{100*costs['write_tests']['cost_usd']/total_usd:.0f}")
        .replace("{{GEN_KILLED}}", str(gen["killed"])).replace("{{CHECKED}}", str(gen["checked"]))
        .replace("{{BOTH_KILLED}}", str(both["killed"])).replace("{{CL_KILLED}}", str(gen["on_changed_lines"]["killed"]))
        .replace("{{CL_CHECKED}}", str(gen["on_changed_lines"]["checked"])))
assert "{{" not in page, [l for l in page.splitlines() if "{{" in l][:3]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print("wrote", OUT, len(page), "bytes;", f"total {total_s:.1f} s, {total_usd:.4f} USD")
