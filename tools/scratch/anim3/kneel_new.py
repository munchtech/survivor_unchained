# ---------------------------------------------------------------- the kneel --
# A crossbow's aim (combat's RangedSpec.Aim: 0.55 s, planted on its line, then
# the shot, then planted 0.7 s more): down onto the right knee, the left foot
# out in front and the left elbow on the knee under the fore-end, the stock at
# the right shoulder and the cheek on it, the body side-on to the mark so the
# bolt's line reads from above. The crossbow in the right fist pistol-fashion
# (Arms.Hold): its stock runs along the fingers, its top out of the thumb.
def _kneel_parts(rig: Rig):
    P, H = _kit(rig)

    def hips(y, pitch, z=-0.02, yaw=0.0, roll=0.0, x=0.0):
        return {"pos": H(x, y, z), "rot": (yaw, pitch, roll)}

    def bow(at, aim, left, pole=(-0.6, -0.7, -0.3), left_pole=(0.3, -0.9, -0.2), left_knuckles=(-0.7, 0.0, 0.7)):
        """The crossbow's grip at `at`, its line along `aim` (its top kept up),
        the left hand at `left` under the fore-end."""
        aim = np.array(aim, float) / np.linalg.norm(aim)
        top = np.array([0.0, 1.0, 0.0]) - aim * aim[1]
        top = top / np.linalg.norm(top)
        return {"hand_r": {"pos": P(*at), "pole": pole, "knuckles": tuple(aim), "blade": tuple(top), "frame": "char"},
                "hand_l": {"pos": P(*left), "pole": left_pole, "knuckles": left_knuckles, "frame": "char"},
                "fingers_r": "grip", "fingers_l": {"curl": 0.45, "thumb": 0.3}}

    stand = {"foot_l": {"pos": P(0.13, 0, 0.06), "rot": (8, 0, 0)}, "foot_r": {"pos": P(-0.14, 0, -0.06), "rot": (-10, 0, 0)}}
    # Down: the right knee on the ground under the hip, the shin back along
    # it, the toes tucked under; the left foot out in front, its shin upright.
    kneel = {"foot_l": {"pos": P(0.15, 0, 0.36), "rot": (6, 0, 0), "pole": (0.25, 0.3, 1.0)},
             "foot_r": {"pos": P(-0.12, 0.085, -0.50), "rot": (-6, 68, 0), "toe": 66, "pole": (-0.05, -0.75, 1.0)}}
    return P, H, hips, bow, stand, kneel


def kneel_aim(name, rig: Rig) -> Clip:
    """Down onto one knee and the crossbow up to the eye inside the aim's
    0.55 s; held there, steady, until it looses (kneel_shot)."""
    P, H, hips, bow, stand, kneel = _kneel_parts(rig)
    aimed = dict(hips=hips(0.475, 4, yaw=-22), spine=(-16, 2, 0), neck=(14, 4, -4), head=(16, 8, -10), clav_r=(6, 6), clav_l=(0, 10),
                 **bow((-0.09, 1.10, 0.08), (0.0, 0.0, 1.0), (-0.06, 1.05, 0.33)))
    keys = [
        # Standing, the crossbow low before it.
        (0, {**stand, **dict(hips=hips(0.93, 4, -0.04), spine=(0, 4, 0)),
             **bow((-0.17, 0.92, 0.22), (0.0, -0.40, 0.92), (-0.04, 0.88, 0.40))}, "ease"),
        # The left foot out as it drops, the right heel coming up behind.
        (3, {"foot_l": {"pos": P(0.15, 0.07, 0.22), "rot": (8, -8, 0)}, "foot_r": {"pos": P(-0.14, 0.02, -0.14), "rot": (-10, 20, 0), "toe": 20},
             **dict(hips=hips(0.84, 6, -0.03, yaw=-6), spine=(-4, 6, 0)),
             **bow((-0.16, 0.96, 0.22), (0.0, -0.25, 0.97), (-0.04, 0.92, 0.42))}, "auto"),
        (6, {"foot_l": kneel["foot_l"], "foot_r": {"pos": P(-0.13, 0.05, -0.34), "rot": (-8, 45, 0), "toe": 40, "pole": (-0.05, -0.5, 1.0)},
             **dict(hips=hips(0.70, 8, -0.02, yaw=-12), spine=(-8, 6, 0), neck=(4, 0, 0), head=(6, 0, 0)),
             **bow((-0.14, 1.00, 0.20), (0.0, -0.10, 1.0), (-0.04, 0.96, 0.42))}, "auto"),
        # The knee meets the ground, a touch low as the weight lands on it.
        (10, {**kneel, **dict(hips=hips(0.46, 6, yaw=-18), spine=(-12, 4, 0), neck=(10, 2, 0), head=(12, 4, -4), clav_r=(4, 4)),
              **bow((-0.12, 1.04, 0.14), (0.0, -0.02, 1.0), (-0.05, 1.00, 0.38))}, "auto"),
        # Up to the eye: the stock in the shoulder, the cheek down on it.
        (14, {**kneel, **dict(aimed, hips=hips(0.48, 4, yaw=-22))}, "auto"),
        (17, {**kneel, **aimed}, "ease"),
        # Held on the line, breathing.
        (21, {**kneel, **dict(aimed, spine=(-16, 3, 0))}, "ease"),
    ]
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/crowd.py)",
                                        "note": "a crossbow's kneel and aim"})


def kneel_shot(name, rig: Rig) -> Clip:
    """The release from the kneel: the kick up through the arms and the
    shoulder, a beat on the knee as the bolt goes, then up off it, the back
    foot brought under, the crossbow lowered. Standing by 0.63 s, inside
    the 0.7 s the shooter stays planted after it looses."""
    P, H, hips, bow, stand, kneel = _kneel_parts(rig)
    aimed = dict(hips=hips(0.475, 4, yaw=-22), spine=(-16, 3, 0), neck=(14, 4, -4), head=(16, 8, -10), clav_r=(6, 6), clav_l=(0, 10))
    keys = [
        (0, {**kneel, **aimed, **bow((-0.09, 1.10, 0.08), (0.0, 0.0, 1.0), (-0.06, 1.05, 0.33))}, "fast"),
        # The kick: the crossbow thrown up, the shoulder and the head knocked back.
        (2, {**kneel, **dict(aimed, spine=(-16, -4, 0), neck=(14, -2, -4), head=(16, 0, -8), clav_r=(12, 0)),
             **bow((-0.09, 1.15, 0.03), (0.0, 0.38, 0.92), (-0.06, 1.12, 0.30))}, "auto"),
        (5, {**kneel, **dict(aimed, spine=(-15, 1, 0)), **bow((-0.10, 1.10, 0.07), (0.0, 0.08, 1.0), (-0.06, 1.05, 0.32))}, "ease"),
        # Lowered, the head up off the stock, the weight going forward over the front foot.
        (9, {**kneel, **dict(hips=hips(0.50, 14, yaw=-14), spine=(-8, 8, 0), neck=(6, 2, 0), head=(8, -2, 0)),
             **bow((-0.15, 0.94, 0.22), (0.0, -0.30, 0.95), (-0.04, 0.92, 0.42))}, "auto"),
        # Up off the knee on the front leg, the back foot drawn under.
        (13, {"foot_l": kneel["foot_l"], "foot_r": {"pos": P(-0.13, 0.04, -0.40), "rot": (-8, 30, 0), "toe": 30, "pole": (-0.05, -0.3, 1.0)},
              **dict(hips=hips(0.72, 16, 0.02, yaw=-8), spine=(-4, 8, 0), neck=(2, 0, 0), head=(4, -2, 0)),
              **bow((-0.16, 0.92, 0.26), (0.0, -0.38, 0.92), (-0.04, 0.88, 0.44))}, "auto"),
        (16, {"foot_l": kneel["foot_l"], "foot_r": {"pos": P(-0.14, 0.08, -0.20), "rot": (-10, 10, 0), "toe": 10},
              **dict(hips=hips(0.86, 8, 0.06, yaw=-4), spine=(-2, 4, 0)),
              **bow((-0.17, 0.92, 0.26), (0.0, -0.40, 0.92), (-0.04, 0.88, 0.42))}, "auto"),
        (19, {"foot_l": kneel["foot_l"], "foot_r": {"pos": P(-0.14, 0, -0.08), "rot": (-10, 0, 0)},
              **dict(hips=hips(0.91, 4, 0.08), spine=(0, 4, 0)),
              **bow((-0.17, 0.92, 0.24), (0.0, -0.40, 0.92), (-0.04, 0.88, 0.40))}, "ease"),
        (21, {"foot_l": kneel["foot_l"], "foot_r": {"pos": P(-0.14, 0, -0.08), "rot": (-10, 0, 0)},
              **dict(hips=hips(0.92, 4, 0.08), spine=(0, 4, 0)),
              **bow((-0.17, 0.92, 0.23), (0.0, -0.40, 0.92), (-0.04, 0.88, 0.40))}, "ease"),
    ]
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/crowd.py)",
                                        "note": "a crossbow's shot from the kneel, and the rise"})


