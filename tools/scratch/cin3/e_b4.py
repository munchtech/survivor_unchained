def edit(shots, f):
    # B4: over Rook's right shoulder, low, her head and shoulder the left third; the
    # survivor right of centre, and the tower with its lamp above and behind her (Rook's
    # look to the tower is a lift of the head along the same line).
    s = shots["B4"]
    s["cam"] = {"pos": [-11.1, 1.5, 13.1], "at": [-1.64, 1.6, 5.71], "lens": 35, "focus": 1.1, "fstop": 2.8,
                "move": {"focus": 12.5, "start": 0.8, "end": 2.2, "ease": "inout"}}
    s["note"] = ("Over Rook's right shoulder at the inn door, low, her head and folded arms soft in the left third: focus "
                 "pulls from her to the survivor stopping at the square's edge, right of centre, looking round at the "
                 "faces. Behind the survivor and above, the toll tower. Rook looks at her; then lifts her head to the "
                 "tower. (Hunter: the look holds a beat longer, and her arms tighten.)")
    # B4b: the reverse, on the same side of the line: Rook's single, her eyeline just
    # off the lens to the right, where the survivor is. She brings her eyes down from the
    # tower to the survivor, and unfolds her arms.
    s = shots["B4b"]
    s["cam"] = {"pos": [-8.4, 1.3, 11.8], "at": {"actor": "rook", "bone": "chest", "off": [0, 0.12, 0]}, "lens": 50,
                "focus": {"actor": "rook", "bone": "head"}, "fstop": 2.8}
    s["note"] = ("Reverse: Rook's single from the square, her eyeline just off the lens to the right. Her eyes come down "
                 "from the tower to the survivor, and she unfolds her arms.")
