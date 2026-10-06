"""C02: animation's Kimodo clips for the Warden (judged by animation at these cameras)."""


def edit(shots, f):
    for c in shots["5"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c.update({"clip": "folk/m_rise_stiff", "from": 0, "speed": 1, "blend": 0})
    for c in shots["7"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c.clear()
            c.update({"do": "anim", "actor": "warden", "clip": "folk/m_bend_lift", "from": 0, "speed": 1, "blend": 0.4})
