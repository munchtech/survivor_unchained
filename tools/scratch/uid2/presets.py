import json, sys, os
D = os.path.dirname(os.path.abspath(__file__))
P = {
    "1_own": {},
    "2_highborn": {"nose_width": -0.5, "nose_bridge": 0.3, "cheekbones": 0.3, "cheeks": -0.4, "jaw": -0.5, "chin_width": -0.5, "eyes_tilt": 0.4, "brows_arch": 0.3, "lips_upper": -0.2},
    "3_vixen": {"eyes_tilt": 0.8, "eyes_open": -0.5, "lips_upper": 0.6, "lips_lower": 0.7, "cupids_bow": 0.6, "nose_tip": 0.4, "nose_width": -0.3, "chin_width": -0.6, "cheeks": -0.3, "brows_arch": 0.4, "mouth_corners": 0.2},
    "4_doe": {"eyes_size": 0.6, "eyes_open": 0.3, "eyes_tilt": -0.2, "nose_width": -0.4, "nose_length": -0.4, "cheeks": 0.2, "cheekbones": -0.3, "jaw": -0.4, "lips_lower": 0.5, "chin_length": -0.3, "brows_arch": 0.2},
    "5_hardwon": {"jaw": 0.8, "chin_width": 0.3, "chin_forward": 0.5, "brows_height": -0.6, "brows_arch": -0.4, "nose_bridge": 0.6, "nose_width": 0.3, "lips_upper": -0.4, "eyes_open": -0.3, "cheekbones": 0.2, "cheeks": -0.6},
    "6_fey": {"ears_pointed": 1, "ears_size": 0.4, "eyes_spacing": 0.4, "eyes_size": 0.4, "eyes_tilt": 0.6, "brows_arch": 0.5, "brows_height": 0.4, "nose_width": -0.6, "nose_tip": 0.3, "chin_width": -0.8, "jaw": -0.6, "cheekbones": 0.3, "cheeks": -0.5},
    "7_wildling": {"mouth_width": 0.6, "lips_lower": 0.6, "lips_upper": 0.4, "nose_width": 0.4, "nose_tip": 0.2, "cheekbones": 0.3, "jaw": 0.3, "eyes_tilt": 0.3, "brows_height": -0.3},
}
if len(sys.argv) > 1 and sys.argv[1] == "load":
    P = json.load(open(os.path.join(D, "presets.json")))
hair = sys.argv[2] if len(sys.argv) > 2 else "bob"
json.dump([{"name": k, "hair": hair, "face": v} for k, v in P.items()], open(os.path.join(D, "sheet_presets.json"), "w"), indent=1)
json.dump(P, open(os.path.join(D, "presets.json"), "w"), indent=1)
