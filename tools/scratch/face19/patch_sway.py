"""Hair swing faults (animation judge 20): gravity wins when her chain's rest no longer hangs down, frame-rate-free
substeps, her arms as colliders (and a forearm pushout in the shader), no mirroring to her back from her sides, the floor."""
import sys
ROOT = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/"

def patch(path, pairs):
    raw = open(ROOT + path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    s = raw.decode("utf-8-sig").replace("\r\n", "\n")
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            sys.exit(f"{path}: {n} matches for {old[:60]!r}")
        s = s.replace(old, new)
    out = s.replace("\n", "\r\n").encode("utf-8")
    open(ROOT + path, "wb").write((b"\xef\xbb\xbf" if bom else b"") + out)

CS = [
("""    sealed class Ball { public int Bone; public Vector3 At; public float R; public bool Behind; }
""", """    sealed class Ball { public int Bone; public Vector3 At; public float R; public bool Behind; }

    // Her forearms, from the elbow to past the fist, in the skeleton's space at rest: the shader pushes her hair out of
    // them (a lock by her ear as her throwing arm comes past her head, animation judge 20), and balls along them and her
    // upper arms keep the chain out (a braid falling beside her as she lies face down). The balls' radii are her limb's
    // with its pauldron or bracer and half a braid; the shader's her forearm's with its bracer, as her hair is its surface.
    int[] foreBone = [], fistBone = [];
    Vector3[] elbowRest = [], fistRest = [];
    const float ForearmR = 0.05f;
    Vector3[] arms = new Vector3[4], armsThen = new Vector3[4];
"""),
("""    Vector3[] rest = [], x = [], xp = [];
    float[] link = [];
""", """    Vector3[] rest = [], x = [], xp = [];
    float[] link = [];
    // Each point's share of the chain's stiffness that stays when its rest no longer hangs down: its rest shape is how
    // it hangs as she stands, gravity's shape, so lying face down or folding forward that shape is let go from the root
    // out, and gravity wins (judge 20: a braid stood off her back as a stick; tails rigid as rods as she folded).
    float[] keep = [];
"""),
("""        link = new float[rest.Length];
        for (int i = 1; i < rest.Length; i++) link[i] = rest[i].DistanceTo(rest[i - 1]);
        var bs = d["spheres"].AsGodotArray();
        balls = new Ball[bs.Count];
        for (int i = 0; i < balls.Length; i++)
        {
            var b = bs[i].AsGodotDictionary();
            var name = (string)b["bone"];
            balls[i] = new Ball { Bone = sk.FindBone(name), At = Vec(b["at"]), R = (float)b["r"], Behind = name.StartsWith("neck") || name.StartsWith("spine") };
        }
    }
""", """        link = new float[rest.Length];
        for (int i = 1; i < rest.Length; i++) link[i] = rest[i].DistanceTo(rest[i - 1]);
        keep = new float[rest.Length];
        for (int i = 0; i < rest.Length; i++) keep[i] = Mathf.Pow(1f - i / (rest.Length - 1f), 3);
        var bs = d["spheres"].AsGodotArray();
        var list = new System.Collections.Generic.List<Ball>();
        for (int i = 0; i < bs.Count; i++)
        {
            var b = bs[i].AsGodotDictionary();
            var name = (string)b["bone"];
            list.Add(new Ball { Bone = sk.FindBone(name), At = Vec(b["at"]), R = (float)b["r"], Behind = name.StartsWith("neck") || name.StartsWith("spine") });
        }
        foreach (var (shoulder, elbow, fist) in Limbs())
        {
            Vector3 s = sk.GetBoneGlobalRest(shoulder).Origin, e = sk.GetBoneGlobalRest(elbow).Origin, f = sk.GetBoneGlobalRest(fist).Origin;
            list.Add(new Ball { Bone = shoulder, At = s, R = 0.08f });
            list.Add(new Ball { Bone = shoulder, At = s.Lerp(e, 0.5f), R = 0.065f });
            list.Add(new Ball { Bone = elbow, At = e, R = 0.06f });
            list.Add(new Ball { Bone = elbow, At = e.Lerp(f, 0.5f), R = 0.055f });
            list.Add(new Ball { Bone = fist, At = f + (f - e).Normalized() * 0.04f, R = 0.055f });
        }
        balls = list.ToArray();
    }

    /// <summary>Her arms' bones (shoulder, elbow, hand), each side that has them.</summary>
    System.Collections.Generic.IEnumerable<(int, int, int)> Limbs()
    {
        foreach (var s in new[] { "l", "r" })
        {
            int u = sk!.FindBone("upperarm_" + s), l = sk.FindBone("lowerarm_" + s), h = sk.FindBone("hand_" + s);
            if (u >= 0 && l >= 0 && h >= 0) yield return (u, l, h);
        }
    }

    void FindForearms()
    {
        var f = new System.Collections.Generic.List<(int, int, Vector3, Vector3)>();
        foreach (var (_, elbow, fist) in Limbs())
        {
            Vector3 e = sk!.GetBoneGlobalRest(elbow).Origin, h = sk.GetBoneGlobalRest(fist).Origin;
            f.Add((elbow, fist, e, h + (h - e).Normalized() * 0.05f));
        }
        foreBone = f.ConvertAll(a => a.Item1).ToArray();
        fistBone = f.ConvertAll(a => a.Item2).ToArray();
        elbowRest = f.ConvertAll(a => a.Item3).ToArray();
        fistRest = f.ConvertAll(a => a.Item4).ToArray();
    }
"""),
("""        head = sk.FindBone("Head");
""", """        head = sk.FindBone("Head");
        FindForearms();
"""),
("""            if (at.Length != balls.Length) { at = new Vector3[balls.Length]; back = new Vector3[balls.Length]; }
            for (int i = 0; i < balls.Length; i++)
            {
                var mv = Moved(balls[i].Bone);
                at[i] = world * (mv * balls[i].At);
                back[i] = (world.Basis * mv.Basis * Vector3.Forward).Normalized();   // (her back: -z at rest)
            }
            if (!live || dt <= 0) { x = (Vector3[])target.Clone(); xp = (Vector3[])target.Clone(); live = true; }
            const int steps = 4;
            float h = dt / steps;
            var fall = new Vector3(0, -9.8f, 0) * h * h;
""", """            if (at.Length != balls.Length) { at = new Vector3[balls.Length]; back = new Vector3[balls.Length]; across = new Vector3[balls.Length]; }
            for (int i = 0; i < balls.Length; i++)
            {
                var mv = Moved(balls[i].Bone);
                at[i] = world * (mv * balls[i].At);
                back[i] = (world.Basis * mv.Basis * Vector3.Forward).Normalized();   // (her back: -z at rest)
                across[i] = (world.Basis * mv.Basis * Vector3.Right).Normalized();
            }
            // How stiff each point is held to its rest: all of it while its rest hangs down from the root, the root's
            // share only (keep) as that rest turns level or up.
            for (int i = 1; i < 8; i++)
            {
                float u = Mathf.Clamp((target[i] - target[0]).Normalized().Dot(Vector3.Down), 0f, 1f);
                hold[i] = stiff * (keep[i] + (1f - keep[i]) * u * u * u * u);
            }
            if (!live || dt <= 0) { x = (Vector3[])target.Clone(); xp = (Vector3[])target.Clone(); live = true; }
            // Steps of about 1/120 s whatever the frame rate (four at 30 fps, as it was tuned and judged): the
            // stiffness and the damping are per step, so at 60 fps four steps held it twice as stiff.
            int steps = Mathf.Max(1, Mathf.CeilToInt(dt * 120f - 1e-3f));
            float h = dt / steps;
            var fall = new Vector3(0, -9.8f, 0) * h * h;
            // (the ground she stands or lies on: her skeleton's own floor)
            float floor = world.Origin.Y + 0.015f;
"""),
("""                        x[i] += (target[i] - x[i]) * stiff;
""", """                        x[i] += (target[i] - x[i]) * hold[i];
"""),
("""                            // (in front of a ball down her back: mirrored behind it, then out)
                            if (balls[b].Behind && off.Dot(back[b]) < 0) off -= 2 * off.Dot(back[b]) * back[b];
                            x[i] = at[b] + (off.LengthSquared() > 1e-10f ? off.Normalized() : back[b]) * r;
                        }
""", """                            // (in front of a ball down her back and near her middle, inside her chest: mirrored behind
                            // it, then out; off to her side, out the nearest way, as a braid falls beside her lying down)
                            if (balls[b].Behind && off.Dot(back[b]) < 0 && Mathf.Abs(off.Dot(across[b])) < 0.6f * r)
                                off -= 2 * off.Dot(back[b]) * back[b];
                            x[i] = at[b] + (off.LengthSquared() > 1e-10f ? off.Normalized() : back[b]) * r;
                        }
                        if (x[i].Y < floor) x[i].Y = floor;
"""),
("""        headAt = local * (world * pose.Origin);
""", """        headAt = local * (world * pose.Origin);
        (armsThen, arms) = (arms, armsThen);
        for (int a = 0; a < 2; a++)
        {
            bool has = a < foreBone.Length;
            arms[2 * a] = has ? local * (world * (Moved(foreBone[a]) * elbowRest[a])) : Vector3.Zero;
            arms[2 * a + 1] = has ? local * (world * (Moved(fistBone[a]) * fistRest[a])) : Vector3.Zero;
        }
"""),
("""        if (!drawn) { swayThen = sway; headThen = headAt; System.Array.Copy(swung, swungThen, 8); drawn = true; }
""", """        if (!drawn) { swayThen = sway; headThen = headAt; System.Array.Copy(swung, swungThen, 8); System.Array.Copy(arms, armsThen, 4); drawn = true; }
"""),
("""                    m.SetShaderParameter(ChainThenName, swungThen);
""", """                    m.SetShaderParameter(ChainThenName, swungThen);
                    m.SetShaderParameter(ArmsName, arms);
                    m.SetShaderParameter(ArmsThenName, armsThen);
                    m.SetShaderParameter(ArmRName, foreBone.Length > 0 ? ForearmR : 0f);
"""),
("""        SwayThenName = "sway_then", HeadThenName = "head_then", ChainThenName = "chain_then";
""", """        SwayThenName = "sway_then", HeadThenName = "head_then", ChainThenName = "chain_then",
        ArmsName = "arms", ArmsThenName = "arms_then", ArmRName = "arm_r";
"""),
("""    Vector3[] target = new Vector3[8], at = [], back = [];
""", """    Vector3[] target = new Vector3[8], at = [], back = [], across = [];
    float[] hold = new float[8];
"""),
]

SH = [
("""uniform vec3 chain_then[8];
""", """uniform vec3 chain_then[8];
// Her forearms (elbow, past the fist; left then right, in the mesh's own space) and their radius: her hair is
// pushed out of them (a lock by her ear as her throwing arm comes past her head). 0: none.
uniform vec3 arms[4];
uniform vec3 arms_then[4];
uniform float arm_r = 0.0;
"""),
("""		VERTEX += ((past ? sway_then : sway) + air) * hang * hang * tip * moves;
	}
""", """		VERTEX += ((past ? sway_then : sway) + air) * hang * hang * tip * moves;
	}
	if (arm_r > 0.0 && moves > 0.0) {
		for (int k = 0; k < 2; k++) {
			vec3 a = past ? arms_then[2 * k] : arms[2 * k];
			vec3 ab = (past ? arms_then[2 * k + 1] : arms[2 * k + 1]) - a;
			vec3 c = a + ab * clamp(dot(VERTEX - a, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
			vec3 o = VERTEX - c;
			float d = length(o);
			if (d < arm_r && d > 1e-5) VERTEX = c + o * (arm_r / d);
		}
	}
"""),
]

patch("src/Actors/HairSway.cs", CS)
patch("shaders/heroine_hair.gdshaderinc", SH)
print("patched")
