"""Draws the warden's quarter of the Lamps as an SVG (docs/design/classes_warden_lamps.svg).
Hand-laid on a grid so no label meets another: two roads as columns, the bridge between,
the hearth below, the crossings leaving at the sides."""
import math, sys

W, H = 1900, 1110
CX = 950
out = []
add = out.append

BG = "#0f0d0b"; ROAD = "#463d31"; LIT_ROAD = "#c08f42"; INK = "#e8dcc4"; DIM = "#9a8d78"
GOLD = "#e0a94a"; BLUE = "#7ab6ff"; UNLIT = "#2a251f"; UNLIT_STROKE = "#7d6c52"

nodes = {}
edges = []

def node(i, x, y, kind, label="", lit=False, lp="r", size=None):
    nodes[i] = dict(x=x, y=y, kind=kind, label=label, lit=lit, lp=lp, size=size)

def edge(a, b): edges.append((a, b))

SY0, STEP = 820, 58
def sy(i): return SY0 - STEP * i

strikes = []
gates = []

def road(p, side, spine_x, skills, notables, blues, ults, lit_spine, lit_extra):
    s = side                       # -1: the left road, +1: the right
    outer, inner = ("l", "r") if s < 0 else ("r", "l")
    for i in range(12):
        nid = f"{p}s{i}"
        if i == 0:
            node(nid, spine_x, sy(i), "notable", notables[0], i in lit_spine, outer)
        elif i in (3, 6, 9):
            node(nid, spine_x, sy(i), "notable", notables[(3, 6, 9).index(i) + 1], i in lit_spine, inner)
        elif i == 11:
            node(nid, spine_x, sy(i), "blue", blues[0], False, inner)
        else:
            node(nid, spine_x, sy(i), "small", "", i in lit_spine)
        if i: edge(f"{p}s{i-1}", nid)
    for a_, t_ in ((2, "6 lit"), (8, "12 lit")):
        gates.append((spine_x, (sy(a_) + sy(a_ + 1)) / 2, s, t_))
    # skill clusters on the outer side
    for k, at in enumerate((1, 4, 7)):
        name, lamps = skills[k]
        kx, ky = spine_x + s * 140, sy(at)
        kid = f"{p}k{k}"
        node(kid, kx, ky, "skill", name, f"k{k}" in lit_extra, "t")
        edge(f"{p}s{at}", kid)
        for j, lname in enumerate(lamps):
            jid = f"{kid}_{j}"
            node(jid, kx + s * 95, ky - 26 + 26 * j, "small", lname, f"k{k}_{j}" in lit_extra, outer, 12)
            edge(kid, jid)
    # two more notables on the inner side
    for k, at in enumerate((5, 8)):
        nid = f"{p}n{k}"
        node(nid, spine_x - s * 110, sy(at) + 0, "notable", notables[4 + k], False, inner)
        edge(f"{p}s{at}", nid)
    # the second blue lamp, outer, off spine 10
    node(f"{p}b1", spine_x + s * 140, sy(10), "blue", blues[1], False, outer)
    edge(f"{p}s10", f"{p}b1")
    # ultimates on the inner side: the Strike at depth 3 (spine 2), the Stand at depth 12 (spine 10)
    for k, at in enumerate((2, 10)):
        name, mods = ults[k]
        ux, uy = spine_x - s * 150, sy(at)
        uid = f"{p}u{k}"
        node(uid, ux, uy, "ult", name, f"u{k}" in lit_extra, "ul" if s < 0 else "ur")
        edge(f"{p}s{at}", uid)
        if k == 0: strikes.append((ux + (-24 if s < 0 else 24), uy + 42, "end" if s < 0 else "start"))
        for j, m in enumerate(mods):
            mid = f"{uid}_{j}"
            node(mid, ux - s * 62, uy - 30 + 30 * j, "mod", m, False, inner)
            edge(uid, mid)

road("L", -1, 520,
     [("Sunder", ["Wide Swing", "Third Blow", "Burning Edge"]),
      ("Groundbreaker", ["Twin Cracks", "Fault Line", "Upheaval"]),
      ("Dawnpulse", ["Dawn Rhythm", "Wider Morning", "Searing Light"])],
     ["Two Hands", "Breaking Point", "Sundered", "Rooted Stance", "Momentum of the Blade", "Morning in the Steel"],
     ["Weight of the Oath", "The Unbroken Line"],
     [("The Long Cut", ["Second Cut", "Line of Morning", "Through the Wall"]),
      ("Dawn in the Steel", ["High Morning", "Crescents Through", "Mending Light"])],
     lit_spine={0, 1, 2, 3, 4}, lit_extra={"k0", "k0_0", "k0_1", "u0"})
road("R", 1, 1380,
     [("Oathblade", ["Shield and Edge", "Reaching Oath", "Morning Edge"]),
      ("Rebuke", ["Wider Rebuke", "Rebuke the Strong", "Answering Light"]),
      ("Watch Bell", ["Loud Bell", "Iron Bell", "Bell and Barrier"])],
     ["Shield Arm", "Mortar", "Planted", "Turned Arrows", "Heavy Shield", "Faith in the Wall"],
     ["The Wall Holds", "Bearer of Blows"],
     [("Bell of the Morning", ["Fourth Toll", "Bell for the Dead", "Healing Peal"]),
      ("Sixty on the Wall", ["Shield-Brothers", "The Wall Walks", "Night Watch"])],
     lit_spine=set(), lit_extra=set())

# the bridge, between the roads' inner notables
node("brA", CX - 55, 545, "small", "Might", False, "b", 12)
node("brB", CX + 55, 545, "small", "Resolve", False, "b", 12)
node("brC", CX - 55, 478, "notable", "Shield Swing", False, "l")
node("brD", CX + 55, 478, "notable", "Oath and Bell", False, "r")
node("brE", CX, 418, "blue", "Sword-and-Board", False, "t")
edge("Ln0", "brA"); edge("Rn0", "brB"); edge("brA", "brB")
edge("brA", "brC"); edge("brB", "brD"); edge("brC", "brE"); edge("brD", "brE")

# the hearth
HX, HY = CX, 900
node("start", HX, HY, "start", "The Warden's Oath: the dash is Bull Rush", True, "b")
node("d1", HX - 95, 975, "dash", "Iron Hide", False, "b", 12)
node("d2", HX - 185, 975, "dash", "Pile Driver", False, "b", 12)
node("d3", HX - 275, 975, "dash", "Unbroken", False, "b", 12)
node("d4", HX - 365, 975, "dash", "Gore", False, "b", 12)
edge("start", "d1"); edge("d1", "d2"); edge("d2", "d3"); edge("d3", "d4")
node("r1", HX + 95, 975, "reflex", "Shield Bash", False, "b", 12)
node("r1a", HX + 185, 975, "small", "Concussion", False, "b", 12)
node("r1b", HX + 275, 975, "small", "Shield Wall", False, "b", 12)
node("r2", HX + 95, 1040, "reflex", "Braced", False, "b", 12)
node("r2a", HX + 205, 1040, "small", "Rallying Stand", False, "b", 12)
edge("start", "r1"); edge("r1", "r1a"); edge("r1a", "r1b"); edge("r1", "r2"); edge("r2", "r2a")
node("f1", HX - 85, 835, "small", "Kindled Oath", False, "l", 12)
node("f2", HX + 85, 835, "small", "Last at the Crossing", False, "r", 12)
edge("start", "f1"); edge("start", "f2")
node("hb1", CX - 160, 790, "blue", "Hold Fast", False, "t")
node("hb2", CX + 160, 790, "blue", "Banked Flame", False, "t")
edge("f1", "hb1"); edge("f2", "hb2")
edge("start", "Ls0"); edge("start", "Rs0")

# the crossings, leaving at the sides from spine 8
def crossing(p, from_id, x_end, labels):
    fx, fy = nodes[from_id]["x"], nodes[from_id]["y"]
    prev = from_id
    n = len(labels)
    for i, lab in enumerate(labels):
        x = fx + (x_end - fx) * (i + 1) / n
        nid = f"{p}{i}"
        node(nid, x, fy, "notable" if lab else "small", lab, False, "t", 12)
        edge(prev, nid); prev = nid

crossing("CL", "Ls8", 90, ["", "Opened Up", "", "Cleaver's Weight", "", ""])
crossing("CR", "Rs8", 1810, ["", "Parry", "", "Return Cut", "", ""])

# ---------------------------------------------------------------- draw
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Georgia, \'Times New Roman\', serif">')
add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
add('<defs><radialGradient id="glow"><stop offset="0" stop-color="#ffcf7a" stop-opacity="0.5"/><stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/></radialGradient>'
    '<radialGradient id="bglow"><stop offset="0" stop-color="#8cc4ff" stop-opacity="0.45"/><stop offset="1" stop-color="#8cc4ff" stop-opacity="0"/></radialGradient></defs>')
add(f'<text x="40" y="50" fill="{INK}" font-size="30">The Lamps: the warden\'s quarter</text>')
add(f'<text x="40" y="76" fill="{DIM}" font-size="15">A diagram, not the screen. Lit as a new player who follows the glow has it at about level 6; the glowing lamp is the next suggestion. Gates count lamps lit on that road.</text>')

for a, b in edges:
    A, B = nodes[a], nodes[b]
    lit = A["lit"] and B["lit"]
    add(f'<line x1="{A["x"]:.0f}" y1="{A["y"]:.0f}" x2="{B["x"]:.0f}" y2="{B["y"]:.0f}" stroke="{LIT_ROAD if lit else ROAD}" stroke-width="{3.5 if lit else 2}" stroke-linecap="round"/>')

nx = nodes["Ls5"]
add(f'<circle cx="{nx["x"]}" cy="{nx["y"]}" r="30" fill="url(#glow)"/>')
add(f'<text x="{nx["x"] - 18}" y="{nx["y"] + 4}" fill="{GOLD}" font-size="12" font-style="italic" text-anchor="end">next</text>')

def label(x, y, text, lp, size, colour):
    if not text: return
    dx, dy, anchor = {"r": (17, 4, "start"), "l": (-17, 4, "end"), "b": (0, 28, "middle"), "t": (0, -19, "middle"), "ul": (-24, 26, "end"), "ur": (24, 26, "start")}[lp]
    add(f'<text x="{x + dx:.0f}" y="{y + dy:.0f}" fill="{colour}" font-size="{size}" text-anchor="{anchor}">{text}</text>')

def star(x, y, r1, r2):
    return " ".join(f"{x + (r1 if k % 2 == 0 else r2) * math.cos(math.radians(-90 + 36 * k)):.1f},{y + (r1 if k % 2 == 0 else r2) * math.sin(math.radians(-90 + 36 * k)):.1f}" for k in range(10))

def hexa(x, y, r):
    return " ".join(f"{x + r * math.cos(math.radians(60 * k)):.1f},{y + r * math.sin(math.radians(60 * k)):.1f}" for k in range(6))

def shape(kind, x, y, lit, scale=1.0):
    fill = GOLD if lit else UNLIT
    stroke = "#f6d796" if lit else UNLIT_STROKE
    if kind == "small":
        add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6*scale:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    elif kind in ("notable", "start"):
        r = (14 if kind == "start" else 10) * scale
        add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
    elif kind == "skill":
        h = 10 * scale
        add(f'<rect x="{x - h:.0f}" y="{y - h:.0f}" width="{2*h:.0f}" height="{2*h:.0f}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    elif kind == "blue":
        if scale == 1.0: add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="24" fill="url(#bglow)"/>')
        a, b = 14 * scale, 10 * scale
        add(f'<path d="M{x:.0f},{y - a:.0f} L{x + b:.0f},{y:.0f} L{x:.0f},{y + a:.0f} L{x - b:.0f},{y:.0f} Z" fill="#1d3550" stroke="{BLUE}" stroke-width="2.5"/>')
    elif kind == "ult":
        add(f'<polygon points="{star(x, y, 18*scale, 8*scale)}" fill="{GOLD if lit else "#3a2410"}" stroke="{"#f6d796" if lit else GOLD}" stroke-width="2"/>')
    elif kind == "mod":
        add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{5*scale:.1f}" fill="#3a2410" stroke="{GOLD}" stroke-width="1.5"/>')
    elif kind == "reflex":
        add(f'<polygon points="{hexa(x, y, 11*scale)}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    elif kind == "dash":
        a = 10 * scale
        add(f'<path d="M{x - a:.0f},{y + a*0.7:.0f} L{x:.0f},{y - a:.0f} L{x + a:.0f},{y + a*0.7:.0f} Z" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

for n in nodes.values():
    x, y, kind, lit = n["x"], n["y"], n["kind"], n["lit"]
    if lit: add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="18" fill="url(#glow)"/>')
    shape(kind, x, y, lit)
    size = n["size"] or {"small": 12, "notable": 14, "start": 15, "skill": 15, "blue": 14, "ult": 15, "mod": 11, "reflex": 13, "dash": 12}[kind]
    colour = {"blue": BLUE, "ult": GOLD, "mod": DIM, "small": INK if lit else DIM, "skill": GOLD if lit else INK}.get(kind, INK)
    label(x, y, n["label"], n["lp"], size, colour)

for gx, gy, gs, gt in gates:
    add(f'<line x1="{gx}" y1="{gy:.0f}" x2="{gx + gs * 30}" y2="{gy:.0f}" stroke="#6f6350" stroke-width="2" stroke-dasharray="5 4"/>')
    add(f'<text x="{gx + gs * 36}" y="{gy + 4:.0f}" fill="#8a7e6a" font-size="11" font-style="italic" text-anchor="{"end" if gs < 0 else "start"}">{gt}</text>')
for sx, sy_, sa in strikes:
    add(f'<text x="{sx}" y="{sy_}" fill="#8a7e6a" font-size="11" font-style="italic" text-anchor="{sa}">3 lit</text>')

def title(x, y, big, small):
    add(f'<text x="{x}" y="{y}" fill="{GOLD}" font-size="22" text-anchor="middle">{big}</text>')
    add(f'<text x="{x}" y="{y + 20}" fill="{DIM}" font-size="13" text-anchor="middle">{small}</text>')

title(520, 118, "Road of the Sunderer", "greatsword: heavy blows, stagger, holy fire")
title(1380, 118, "Road of the Bulwark", "sword and shield: block, Ward, retaliation")
title(CX, 612, "The bridge: Sword and Board", "for carrying both")
title(CX, 1075, "The hearth", "dash form, reflexes, the Flare")
add(f'<text x="90" y="312" fill="{DIM}" font-size="14" font-style="italic">the Shambles, on to the Butcher</text>')
add(f'<text x="1810" y="312" fill="{DIM}" font-size="14" font-style="italic" text-anchor="end">the Duelist\'s Road, on to the Skirmisher</text>')

# legend, bottom left
lx, ly = 70, 880
items = [("small", "small lamp"), ("skill", "skill, with its three lamps"), ("notable", "notable"),
         ("blue", "blue lamp: a rule with a price"), ("ult", "ultimate (Flare), three modifiers"),
         ("reflex", "reflex: an art that fires itself"), ("dash", "dash form")]
add(f'<rect x="{lx - 25}" y="{ly - 25}" width="300" height="{len(items) * 26 + 22}" fill="#16130f" stroke="#3a3226" rx="6"/>')
for k, (kind, text) in enumerate(items):
    y = ly + k * 26
    shape(kind, lx, y, False, 0.8)
    add(f'<text x="{lx + 22}" y="{y + 5}" fill="{INK}" font-size="13">{text}</text>')

add('</svg>')
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
print(len(nodes), "nodes", len(edges), "edges")
