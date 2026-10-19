# k12a pass 2 (C01): s3 back on k12a3V's lens (13 cm up, aimed at her head: the flung arm stays under the frame);
# s8a's globes black behind brighter halos (k12a4X: three small blue lamps, no eggs).
def edit(shots, f):
    shots["3"]["cam"] = {"pos": [-10.07, 0.13, 90.5], "at": [-9.45, 0.17, 90.45], "lens": 60,
                         "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0, "move": {"push": 0.02, "ease": "linear"}}
    for c in shots["8a"]["cues"]:
        if c.get("do") == "globe": c["level"] = 0.0
        if c.get("do") == "glow" and c.get("name", "").startswith("ford"): c.update({"size": 0.09, "energy": 6, "spread": 18, "halo": 0.6})
