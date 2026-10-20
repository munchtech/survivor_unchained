TWO_HANDS = False
FWD = {3: (-0.16, 0.48, 0.70, 30.0, -22.0), 6: (-0.16, 0.48, 0.70, 30.0, -22.0), 9: (-0.16, 0.50, 0.68, 30.0, -22.0)}
FWD_BODY = {"clav_r": (20, 14), "spine": (-2, -10, 0), "neck": (4, -4, 0), "head": (8, -6, 0)}
LFREE = {2: ((0.04, 0.02, 0.40), (0.6, -0.4, -0.4), "spread"), 3: ((0.26, -0.30, 0.06), (0.6, -0.6, -0.5), "spread"),
         6: ((0.27, -0.32, 0.04), (0.6, -0.6, -0.5), "spread")}
_orig_keys = _strike_keys
def _strike_keys():
    out = []
    for fr, pose, e in _orig_keys():
        if fr in LFREE:
            v, pole, fing = LFREE[fr]
            pose = {**pose, "hand_l": {"arc": arc_of(v), "pole": pole, "frame": "chest", "twist": 0.3}, "fingers_l": fing}
        out.append((fr, pose, e))
    return out
def chain_strike(rig):
    keys = _strike_keys()
    meta = {"layer": "full", "contact": 3 / 30, "weapon": "axe", "note": "keyed: the haul's landing blow"}
    first = build("chain_strike", rig, keys, meta=meta, post=_left_clear)
    fwd = _forward(rig, first)
    return build("chain_strike", rig, keys, meta=meta, post=lambda fr, pose: _left_clear(fr, fwd(fr, pose)))
FWD_POLES = {"hand_r": None, "hand_l": None}
