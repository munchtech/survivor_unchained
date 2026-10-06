V = {
    "5": [
        {"id": "5B", "cam": {"pos": [-11.75, 0.38, 90.75], "at": {"actor": "her", "bone": "chest", "off": [0, 0.12, 0]}, "lens": 35, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.8}},
        {"id": "5C", "cam": {"pos": [-11.6, 0.5, 91.05], "at": {"actor": "her", "bone": "chest", "off": [0, 0.1, 0]}, "lens": 45, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.4}},
    ],
    "6a": [
        {"id": "6aC", "cam": {"pos": [-9.95, 0.75, 91.35], "at": [-10.2, 0.28, 90.6], "lens": 40, "focus": {"actor": "her", "bone": "hand_r"}, "fstop": 2.8}},
        # As C, the flames put out entirely (the rest of the run then has none).
        {"id": "6aD", "cam": {"pos": [-9.95, 0.75, 91.35], "at": [-10.2, 0.28, 90.6], "lens": 40, "focus": {"actor": "her", "bone": "hand_r"}, "fstop": 2.8},
         "cues": [{"do": "fire", "light": 0, "flames": 0}, {"do": "anim", "clip": "her/reach_coals", "from": 0, "speed": 1.0, "blend": 0}]},
    ],
}
