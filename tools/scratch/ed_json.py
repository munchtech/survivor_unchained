import json
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\ui_assets.json'
d = json.load(open(p, encoding='utf-8'))
A = {a["id"]: a for a in d["assets"]}
A["plate"].update(margins=[64, 64, 64, 64], out=12, clear=21, tile=True)
for k in ("paper", "tooltip", "tooltip_worn", "button", "button_hover", "button_pressed", "button_disabled", "button_primary",
          "button_primary_hover", "button_primary_pressed", "row_on", "toast", "prompt", "bar_track", "map_frame"):
    A[k]["tile"] = True
A["hint"].update(margins=[40, 40, 40, 40], clear=14, tile=True)
A["map_frame"]["out"] = 8
for k in ("card_0", "card_1", "card_2", "card_3", "card_4", "card_evolve"):
    A[k].update(size=[736, 1000], margins=[64, 80, 64, 64], out=24)
A["medal_level"]["size"] = [116, 116]
A["ring_art"]["size"] = [220, 220]
for a in d["assets"]:
    a["made_by"] = "tools/uiforge/build.py"
d["assets"].append({"id": "bar_casing", "file": "bars/casing.png", "size": [128, 48], "margins": [16, 8, 16, 8], "out": 6, "tile": True,
                    "kind": "frame", "made_by": "tools/uiforge/build.py",
                    "prompt": "Forged iron round a bar's groove, hollow, the twisted wire along it, a rivet at each end (GameHud.Casing)."})
d["assets"].append({"id": "bar_casing_boss", "file": "bars/casing_boss.png", "size": [640, 128], "margins": [64, 24, 64, 24], "out": 64,
                    "out_y": 24, "tile": True, "kind": "frame", "made_by": "tools/uiforge/build.py",
                    "prompt": "The boss's bar: a channel of black iron with red-gold trim, a horned ram's skull at each end."})
d["_"] += (" Since the art pass: every asset is made by tools/uiforge/build.py (see docs/UI_ART_BRIEF.md 2.6); "
           "'out' is how far a frame reaches past its control (UiArt.Slice Out), 'clear' how far content keeps from the edge, "
           "'tile' that its edges and middle repeat.")
json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(d["assets"]))
