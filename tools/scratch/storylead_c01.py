"""Two placeholder shots in C01 for the call up the road, inserted as text in
the file's own hand layout (the cinematics lead frames them properly)."""
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\cinematics\c01.json"
raw = open(P, "rb").read().decode("utf-8")
anchor = '    {\r\n      "id": "9",\r\n'
assert raw.count(anchor) == 1
block = '''    {
      "id": "8a",
      "type": "ELS",
      "dur": 5.0,
      "fit": ["cin_drowned_fire.lamp"],
      "tail": 0.6,
      "still": 3.0,
      "note": "PLACEHOLDER (story lead; the cinematics lead frames it): over her shoulder, north, past the ford's three blue points, far up the road: one lamp, high in the dark (the toll tower). Hold on it. N-lamp.",
      "cam": {"pos": {"actor": "her", "bone": "head", "off": [-0.62, 0.38, 1.35]}, "at": [-6.6, 1.2, 72.0], "lens": 50, "focus": {"abs": [-6.6, 1.2, 72.0]}, "fstop": 4.0},
      "cues": [
        {"do": "gaze", "look": [0, 0.9]},
        {"at": 0.6, "do": "line", "id": "cin_drowned_fire.lamp"}
      ]
    },
    {
      "id": "8b",
      "type": "CU",
      "dur": 4.5,
      "fit": ["cin_drowned_fire.call"],
      "tail": 0.8,
      "still": 2.5,
      "note": "PLACEHOLDER (story lead): as shot 8. The voice comes as if from her shoulder; she does not turn. Unnamed: the subtitle says only 'A voice up the road'. Vonnra's voice, far off and thinned by the cold.",
      "cam": {"pos": {"actor": "her", "bone": "head", "off": [0.05, 0.04, -1.15]}, "at": {"actor": "her", "bone": "eyes"}, "lens": 85, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0},
      "cues": [
        {"do": "gaze", "look": [0, 0.9]},
        {"at": 0.4, "do": "line", "id": "cin_drowned_fire.call"}
      ]
    },
'''.replace("\n", "\r\n")
open(P, "wb").write(raw.replace(anchor, block + anchor).encode("utf-8"))
print("ok")
