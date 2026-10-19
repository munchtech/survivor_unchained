# k12a4 variants on the edited c01: X = s8a globes black behind brighter halos; L = s3's moon from above her brow, in front.
def X(shots, f):
    for c in shots["8a"]["cues"]:
        if c.get("do") == "globe": c["level"] = 0.0
        if c.get("do") == "glow": c.update({"size": 0.09, "energy": 6, "spread": 18, "halo": 0.6})
def L(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("name") == "moon": c.update({"from": {"actor": "her", "bone": "head", "off": [-0.35, 1.3, 0.05]}, "energy": 0.5})
VARIANTS = {"X": X, "L": L}
