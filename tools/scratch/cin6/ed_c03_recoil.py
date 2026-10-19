def edit(shots, f):
    c = shots["9"]["cues"]
    # The burst: she flinches, and her reaching hand pulls back as he snatches the heart
    # (she held the reach frozen through s9-s12 before).
    c.append({"at": 0.05, "do": "anim", "actor": "her", "clip": "her/flinch", "from": 0, "speed": 1, "blend": 0.05})
    c.append({"at": 0.45, "do": "anim", "actor": "her", "clip": "@idle", "from": 0, "speed": 1, "blend": 0.6})
