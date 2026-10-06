def self2(cv: Canvas, src="kit", chain=True):
    """Self as the approved greybox lays it (UI design, 644fb432): no dead space, the page
    ending at its contents and fading into the world; the head band the one frame, and on its
    rail the chain, broken under her name."""
    backdrop(cv, src, taper=(880, 1010))
    ink, ink_dim, gold, gold_hi, ember = "#e8dcc8", "#a89c8c", "#c9a256", "#f0d9a0", "#ff9a4a"
    hd = load("frames/header.png", src)
    cv.nine(hd, -4, -4, 1928, 100, 0, 0, 0, 12, True)
    if chain:
        ch = load("frames/chain_band.png", src)
        if ch is not None:
            cv.over(resize(ch, 1920 * cv.s, 40 * cv.s), 0, 76 * cv.s)
    x = 60
    for i, t in enumerate(["Pack", "Self", "Arts", "Journal", "Map"]):
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 17)
        tw = fnt.getlength(t)
        if i == 1:
            piece(cv, "tab_on", x - 12, 22, tw + 48, 34, src)
        cv.text(x, 42, t, "alegreya-sans-700", 17, gold_hi if i == 1 else ink_dim, "ls")
        piece(cv, "keycap", x + tw + 8, 27, 20, 20, src)
        cv.text(x + tw + 18, 42, "ICKJM"[i], "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        x += tw + 62
    cv.text(960, 50, "WREN", "cinzel-700", 38, gold_hi, "ms")
    cv.text(960, 69, "Level 4  ·  Warden  ·  Hunter, who knows Beastlore", "alegreya-400-italic", 15, ink_dim, "ms")
    piece(cv, "rule_h", 857, 72, 206, 6, src)
    cv.fill(860, 74, 112, 2, (0.53, 0.69, 0.85), 0.9)
    cv.text(1068, 79, "340 / 600", "alegreya-sans-500", 11, ink_dim, "ls")
    piece(cv, "button", 1784, 26, 100, 36, src)
    piece(cv, "keycap", 1796, 34, 26, 20, src)
    cv.text(1809, 49, "Esc", "alegreya-sans-700", 11, ink_dim, "ms", shadow=False)
    cv.text(1830, 50, "Close", "alegreya-sans-700", 15, gold_hi, "ls")
    cv.text(290, 520, "her figure, live 3D", "alegreya-400-italic", 15, "#4a423c", "ms", shadow=False)
    # Attributes: a tight row of four.
    cv.text(560, 124, "ATTRIBUTES", "alegreya-sans-800", 13, gold, "ls")
    cv.text(644, 127, "more with each level", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 765, 117, 1005, 6, src)
    cv.text(1880, 124, "2 points to spend", "alegreya-sans-700", 13, ember, "rs")
    attrs = [("MIGHT", "6", "+2.5% damage, +4 health a point"), ("FINESSE", "3", "+0.6% critical chance, +1% speed"),
             ("WITS", "3", "+1% weapon speed, +2% area and ember"), ("RESOLVE", "6", "+3 health, +0.5 armour, +0.08 regeneration")]
    for i, (nm, n, dsc) in enumerate(attrs):
        px = 560 + i * 334
        piece(cv, "panel", px, 140, 318, 120, src)
        cv.text(px + 22, 196, n, "cinzel-700", 48, gold_hi, "ls")
        if i == 0:
            cv.text(px + 62, 194, "»", "alegreya-sans-700", 26, "#7fd07a", "ls")
            cv.text(px + 92, 196, "7", "cinzel-700", 36, "#7fd07a", "ls")
            node(cv, "round", px + 242, 169, 34, src)
            cv.text(px + 242, 175, "−", "alegreya-sans-700", 18, ink_dim, "ms", shadow=False)
        node(cv, "round_spend", px + 282, 169, 38, src)
        cv.text(px + 282, 176, "+", "alegreya-sans-700", 20, ember, "ms", shadow=False)
        cv.text(px + 22, 223, nm, "cinzel-700", 19, gold, "ls")
        cv.text(px + 22, 244, dsc, "alegreya-sans-500", 13, ink_dim, "ls")
    cv.text(560, 294, "Spending shows every number it changes, green where it rises, until you confirm.", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "button", 1626, 270, 110, 36, src)
    cv.text(1644, 294, "Undo", "alegreya-sans-700", 15, gold_hi, "ls")
    piece(cv, "button_primary", 1748, 270, 132, 36, src)
    cv.text(1766, 294, "Confirm", "alegreya-sans-700", 15, "#ffe4b0", "ls")
    # Traits: the track.
    cv.text(560, 346, "TRAITS", "alegreya-sans-800", 13, gold, "ls")
    cv.text(612, 349, "one of three at every second level, and some given for what you do", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 970, 339, 910, 6, src)
    piece(cv, "rule_h", 590, 391, 870, 6, src)
    node(cv, "taken", 590, 394, 44, src)
    cv.text(590, 400, "ic", "alegreya-sans-700", 13, ink_dim, "ms", shadow=False)
    node(cv, "next", 687, 394, 50, src)
    cv.text(687, 403, "4", "cinzel-700", 20, ember, "ms")
    for k, lv in enumerate(range(6, 21, 2)):
        nx = 783 + k * 96.7
        node(cv, "later", nx, 394, 14, src)
        cv.text(nx, 422, str(lv), "alegreya-sans-500", 12, ink_dim, "ms", shadow=False)
    cv.text(590, 436, "Steady Hand", "alegreya-sans-700", 14, ink, "ms")
    cv.text(687, 436, "Next: one of three", "alegreya-sans-700", 14, ember, "ms")
    cv.text(1520, 377, "GIVEN FOR DEEDS", "alegreya-sans-800", 12, gold, "ls")
    for cx0, w, t in ((1520, 84, "Wolfsbane"), (1612, 70, "Lamp-lit")):
        piece(cv, "chip", cx0, 387, w, 26, src)
        cv.text(cx0 + w / 2, 405, t, "alegreya-sans-500", 14, ink, "ms", shadow=False)
    # Standing: four aligned columns.
    cv.text(560, 474, "STANDING", "alegreya-sans-800", 13, gold, "ls")
    cv.text(634, 477, "hover a number: where it comes from", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 840, 467, 1040, 6, src)
    cols = [(560, [("STAYING ALIVE", [("Health", "212", "+4"), ("Armour", "8 · 29%", ""), ("Regeneration", "0.7/s", ""), ("Healing", "+18%", ""), ("Dodge", "0%", "")])]),
            (899, [("DEALING DEATH", [("Damage", "+15%", "+2.5%"), ("Critical chance", "6%", ""), ("Critical damage", "×1.5", ""), ("Weapon speed", "+3%", ""), ("Area", "+6%", "")])]),
            (1238, [("WARDING", [("Fire", "12%", ""), ("Frost", "22%", ""), ("Storm", "0%", ""), ("Venom", "0%", "")]),
                    ("FORTUNE", [("Experience", "+6%", ""), ("Gold found", "0%", "")])]),
            (1577, [("MOVING", [("Speed", "5.2", ""), ("Dashes", "2", ""), ("Reach", "2.4 m", "")]),
                    ("THE ART IN HAND", [("Shield Bash", "rank II", ""), ("Strength", "+6%", ""), ("Wait", "7 s", "")])])]
    for cx0, groups in cols:
        y = 507
        for head, rows in groups:
            cv.text(cx0, y, head, "alegreya-sans-800", 12, gold, "ls")
            y += 26
            for a, b, d in rows:
                cv.text(cx0, y, a, "alegreya-sans-500", 16, ink, "ls")
                cv.text(cx0 + 252, y, b, "alegreya-sans-700", 15, ink, "rs")
                if d:
                    cv.text(cx0 + 304, y, d, "alegreya-sans-700", 13, "#7fd07a", "rs")
                piece(cv, "rule_h", cx0 - 4, y + 8, 312, 6, src)
                y += 31
            y += 16
    cv.text(560, 780, "CALLING AND ORIGIN", "alegreya-sans-800", 13, gold, "ls")
    piece(cv, "rule_h", 695, 773, 1185, 6, src)
    origin = [("CALLING", "Warden", "Hold the line."), ("ORIGIN", "Hunter", "You read the ground and the animals on it."),
              ("KNOWS", "Beastlore", "It opens words and ways others miss."), ("RENOWN", "A stranger", "The Waystation has not decided about you.")]
    for i, (h_, n_, d_) in enumerate(origin):
        cx0 = 560 + i * 339
        cv.text(cx0, 811, h_, "alegreya-sans-800", 12, gold, "ls")
        cv.text(cx0, 841, n_, "alegreya-700", 19, ink, "ls")
        cv.text(cx0, 866, d_, "alegreya-400-italic", 14, ink_dim, "ls")
    prompts = [("Arrows", "Move"), ("Enter", "Spend a point"), ("Bksp", "Take it back"), ("[ ]", "Turn the page"), ("Esc", "Close")]
    for i, (k_, t) in enumerate(prompts):
        bx = 646 + [0, 120, 278, 422, 560][i]
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 12)
        kw = fnt.getlength(k_) + 14
        piece(cv, "keycap", bx, 1040, kw, 22, src)
        cv.text(bx + kw / 2, 1056, k_, "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        cv.text(bx + kw + 10, 1056, t, "alegreya-sans-500", 14, ink_dim, "ls")
    return cv
