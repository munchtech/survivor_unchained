# --------------------------------------------------------------------- the slam --
# Where the blow meets the ground, in seconds into the clip (CrowdView.SlamImpact
# plays the windup to land there as the sim's blow lands).
SLAM_IMPACT = 29


def slam(name, rig: Rig, armed=False) -> Clip:
    """A heavy's slam, the cast it makes before the ground breaks round it
    (combat's SlamSpec: a windup of 1.0 to 1.1 s, the blow landing at its
    end). The lead foot planted as it sinks to gather, the fists (armed:
    the axe, cocked behind the head) swept up overhead and the back arched
    under them, a hang at the top for the player to read; then it
    jack-knifes, and the fists (the axe head) go into the ground in front
    with the knees, at frame 29. It stays down a beat, glaring up, then
    shoves itself up off the ground."""
    P, H = _kit(rig)
    planted = {"foot_l": {"pos": P(0.20, 0, 0.18), "rot": (16, 0, 0), "pole": (0.35, 0, 1)},
               "foot_r": {"pos": P(-0.20, 0, -0.13), "rot": (-18, 0, 0), "pole": (-0.35, 0, 1)}}
    feet = {0: {"foot_l": {"pos": P(0.14, 0, 0.05), "rot": (10, 0, 0)}, "foot_r": planted["foot_r"]},
            3: {"foot_l": {"pos": P(0.17, 0.07, 0.12), "rot": (14, -6, 0)}, "foot_r": planted["foot_r"]}}

    def hips(y, pitch, z=-0.05, yaw=0.0, x=0.0):
        return {"pos": H(x, y, z), "rot": (yaw, pitch, 0)}

    def hand(side, at, pole, knuckles=None, blade=None):
        h = {"pos": P(*at), "pole": pole, "frame": "char"}
        if knuckles is not None:
            h["knuckles"] = knuckles
        if blade is not None:
            h["blade"] = blade
        return {f"hand_{side}": h}

    def fists(x, y, z, pole_out=(0.7, -0.2, -0.6), knuckles=(0.0, -1.0, 0.2)):
        """Both fists, mirrored about the middle."""
        (px, py, pz), (kx, ky, kz) = pole_out, knuckles
        return {**hand("l", (x, y, z), (px, py, pz), (kx, ky, kz)), **hand("r", (-x, y, z), (-px, py, pz), (-kx, ky, kz)),
                "fingers_l": "fist", "fingers_r": "fist"}

    def axe(at, blade, shield, pole=(-0.7, -0.3, -0.6), shield_pole=(0.7, -0.4, -0.5)):
        """The axe in the right fist (blade: the way the haft leaves it), the shield arm's hand at `shield`."""
        return {**hand("r", at, pole, blade=blade), **hand("l", shield, shield_pole), "fingers_l": "fist", "fingers_r": "grip"}

    # (frame, body, unarmed hands, armed hands, ease)
    beats = [
        # Settled, the fists (the axe) low.
        (0, dict(hips=hips(0.93, 4, -0.04), spine=(0, 4, 0)),
         fists(0.24, 0.90, 0.04),
         axe((-0.24, 0.92, 0.08), (0.0, -0.45, 0.9), (0.20, 0.98, 0.16)), "ease"),
        # The gather: the lead foot planted as it sinks into its knees, the
        # chest down over the fists (the axe drawn back low, the shield up).
        (6, dict(hips=hips(0.78, 24, -0.06, yaw=-8), spine=(-8, 20, 0), neck=(0, -6, 0), head=(4, -18, 0)),
         fists(0.13, 0.82, 0.42, knuckles=(0.0, -0.9, 0.4)),
         axe((-0.32, 0.84, -0.16), (0.0, -0.55, -0.83), (0.10, 1.10, 0.36)), "auto"),
        # Rising: the fists swept up past the face (the axe up over the shoulder).
        (13, dict(hips=hips(0.90, 6, -0.05), spine=(0, -2, 0), neck=(0, -4, 0), head=(0, -8, 0), clav_l=(10, 4), clav_r=(10, 4)),
         fists(0.17, 1.56, 0.30, (0.8, -0.3, -0.5), (0.0, 0.4, 0.9)),
         axe((-0.28, 1.58, 0.04), (0.0, 0.95, -0.3), (0.42, 1.22, 0.10), shield_pole=(0.5, -0.6, -0.6)), "auto"),
        # The top: the fists flung up and wide (the axe cocked behind the
        # head), the back arched under them, the head up.
        (19, dict(hips=hips(0.93, -8, -0.08, yaw=4), spine=(4, -20, 0), neck=(0, -6, 0), head=(0, -10, 0), clav_l=(26, -6), clav_r=(26, -6)),
         fists(0.33, 1.90, -0.12, (1.0, 0.0, -0.2), (0.0, 0.5, -0.85)),
         axe((-0.18, 1.90, -0.14), (0.0, -0.55, -0.83), (0.46, 1.26, 0.02), (-0.9, 0.1, -0.3), (0.5, -0.6, -0.6)), "auto"),
        # The hang: drawn a little further back.
        (24, dict(hips=hips(0.92, -10, -0.10, yaw=4), spine=(4, -24, 0), neck=(0, -6, 0), head=(0, -12, 0), clav_l=(28, -8), clav_r=(28, -8)),
         fists(0.32, 1.89, -0.21, (1.0, 0.0, -0.2), (0.0, 0.4, -0.9)),
         axe((-0.17, 1.88, -0.22), (0.0, -0.72, -0.7), (0.46, 1.24, -0.02), (-0.9, 0.1, -0.3), (0.5, -0.6, -0.6)), "linear"),
        # Down: it jack-knifes, the fists over the head and coming down in front.
        (26, dict(hips=hips(0.84, 16, -0.03), spine=(0, 10, 0), neck=(0, -4, 0), head=(0, -14, 0), clav_l=(18, 8), clav_r=(18, 8)),
         fists(0.24, 1.72, 0.30, (1.0, 0.2, -0.3), (0.0, 0.6, 0.8)),
         axe((-0.14, 1.78, 0.26), (0.0, 1.0, -0.1), (0.36, 1.10, 0.20), (-0.9, 0.2, -0.3)), "linear"),
        (28, dict(hips=hips(0.62, 38, -0.01), spine=(0, 24, 0), neck=(0, -2, 0), head=(0, -16, 0), clav_l=(4, 14), clav_r=(4, 14)),
         fists(0.18, 0.96, 0.64, (0.8, 0.4, -0.4), (0.0, -0.3, 0.95)),
         axe((-0.10, 1.02, 0.64), (0.0, 0.55, 0.83), (0.30, 0.72, 0.34), (-0.8, 0.4, -0.4)), "linear"),
        # The blow: the fists (the axe head) into the ground before the feet.
        (SLAM_IMPACT, dict(hips=hips(0.47, 46, -0.03), spine=(0, 28, 0), neck=(0, 2, 0), head=(0, -14, 0), clav_l=(-4, 16), clav_r=(-4, 16)),
         fists(0.16, 0.11, 0.58, (0.8, 0.5, -0.3), (0.0, -1.0, 0.3)),
         axe((-0.10, 0.36, 0.62), (0.0, -0.6, 0.8), (0.26, 0.58, 0.40), (-0.8, 0.5, -0.3)), "fast"),
        # Driven on into it, the knees and shoulders taking the shock.
        (32, dict(hips=hips(0.40, 52, -0.05), spine=(0, 32, 0), neck=(0, 4, 0), head=(0, -10, 0), clav_l=(-8, 18), clav_r=(-8, 18)),
         fists(0.17, 0.09, 0.56, (0.8, 0.5, -0.3), (0.0, -1.0, 0.3)),
         axe((-0.10, 0.30, 0.58), (0.0, -0.66, 0.75), (0.26, 0.52, 0.38), (-0.8, 0.5, -0.3)), "ease"),
        # Held down a beat, the head coming up to glare.
        (36, dict(hips=hips(0.42, 50, -0.05), spine=(0, 28, 0), neck=(0, -4, 0), head=(0, -24, 0), clav_l=(-4, 16), clav_r=(-4, 16)),
         fists(0.17, 0.10, 0.55, (0.8, 0.5, -0.3), (0.0, -1.0, 0.3)),
         axe((-0.10, 0.31, 0.57), (0.0, -0.66, 0.75), (0.26, 0.53, 0.38), (-0.8, 0.5, -0.3)), "ease"),
        # Shoved up off the ground (the axe wrenched out).
        (43, dict(hips=hips(0.70, 28, -0.05), spine=(0, 14, 0), neck=(0, -2, 0), head=(0, -10, 0), clav_l=(4, 8), clav_r=(4, 8)),
         fists(0.22, 0.56, 0.32, (0.7, 0.2, -0.6), (0.0, -0.9, 0.3)),
         axe((-0.22, 0.70, 0.40), (0.0, 0.2, 0.98), (0.22, 0.80, 0.30)), "auto"),
        # Up, and settled.
        (49, dict(hips=hips(0.90, 6, -0.05), spine=(0, 4, 0), neck=(0, 0, 0), head=(0, -2, 0), clav_l=(6, 0), clav_r=(6, 0)),
         fists(0.24, 0.88, 0.06),
         axe((-0.24, 0.92, 0.12), (0.0, -0.3, 0.95), (0.20, 0.98, 0.18)), "auto"),
        (53, dict(hips=hips(0.92, 4, -0.05), spine=(0, 4, 0)),
         fists(0.24, 0.90, 0.04),
         axe((-0.24, 0.92, 0.10), (0.0, -0.45, 0.9), (0.20, 0.98, 0.16)), "ease"),
    ]
    keys = []
    for fr, pose, bare, held, ease in beats:
        legs = feet.get(fr, planted)
        keys.append((fr, {**legs, **pose, **(held if armed else bare)}, ease))
    return build(name, rig, keys, meta={"layer": "full", "impact": SLAM_IMPACT / 30.0, "source": "keyed (tools/anim/crowd.py)",
                                        "note": "a heavy's slam: up overhead, down onto the ground, and up again" + (", armed" if armed else "")})


