using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (E9c) The house fade (look bible 08, "The trick" 1): the part of a house that stands between the survivor and the
/// play camera (OwnWalls' fade units: a house, or a 12 m length of a long one) fades out with a screen-door cut
/// (kit.gdshader's house_fade_of, a threshold moved every frame that the temporal smoothing sums), easing in and out
/// over 0.3 s; its shadow stays (the cut is made only in the camera's view). A unit is in her way when the line from
/// the camera to any of five points on her (chest, head, knees, and the chest 35 cm either side across the
/// screen) passes through its box. At most 8 units fade at once (the nearest-faded kept).
/// --house-fade-hold F: every fade in her way held at F (0..1), for the mid-fade frames.
/// </summary>
public sealed partial class HouseFade : Node
{
    /// <summary>Her chest (xyz) and 1 in w while she is in the world (WorldScene sets it each frame).</summary>
    public static Vector4 Her;

    /// <summary>A volume a unit fills: a box in its own frame (To: world to that frame), or, Ridge 1 or 2, the prism under
    /// a roof's two slopes (its ridge along the box's x or z, at the box's top in the middle, its eaves at the box's foot).</summary>
    public readonly record struct Vol(Transform3D To, Aabb Box, int Ridge);

    /// <summary>Each unit's volumes (OwnWalls.FadeUnits).</summary>
    public readonly List<Vol[]> Units = new();

    /// <summary>(E9c2) Each unit's cut, world height: above it the unit fades (0.9 m over its floor), below it stands
    /// (the cutaway: the house cut down to its footing, never gone). Roofs fade whole.</summary>
    public readonly List<float> Cut = new();

    /// <summary>What hangs on a unit's walls (kit lanterns, torches: OwnWalls.FadeUnits): one copy of a MultiMesh, faded
    /// with its unit by the kit shader (its custom data r: the unit + 1).</summary>
    public readonly List<(MultiMesh Mm, int I, Transform3D At, int Unit)> Hung = new();
    // (E9c2) what else goes with a unit, on its curve (found once, on the third frame): the glow balls, flames and glass
    // by its hung lanterns and inside it (made transparent as it fades), its lights (their colour dimmed, as the
    // flicker drives their energy), its chimney smoke (transparent, and no new puffs past half)
    readonly List<(GeometryInstance3D G, int Unit)> faders = new();
    // (the glow balls also shrink on the curve: their additive material takes no instance transparency)
    readonly List<(Node3D N, Vector3 Scale, int Unit)> balls = new();
    readonly List<(Light3D L, Color Base, int Unit)> lamps = new();
    readonly List<(GpuParticles3D P, int Unit)> smokes = new();
    float[] shown = System.Array.Empty<float>();
    int frames;

    const float Ease = 0.3f;
    // (E9c3) once in her way a unit stays cut until she has been clear of it this long: its fade runs to 0 or 1 and
    // rests only there, never held part way by her standing at its edge
    const float Linger = 0.4f;
    float[] away = System.Array.Empty<float>();
    // (E9c3) what furnishes the insides (Insides.cs, meta "inside"): our props and the hearths, in view only while
    // their house is cut, coming in on its curve (their transparency); the hearths' lights with them
    readonly List<(GeometryInstance3D G, int Unit)> ins = new();
    readonly List<(Light3D L, float E, int Unit)> inLights = new();
    // (E9c2 perf) the inside MultiMeshInstance3Ds: no shadows, and out of the draw while no unit is cut
    readonly List<MultiMeshInstance3D> inMmis = new();
    static readonly StringName IdsA = "house_fade_ids", IdsB = "house_fade_ids2", AmtA = "house_fade", AmtB = "house_fade2", CutA = "house_cut", CutB = "house_cut2";
    float[] fade = System.Array.Empty<float>();
    readonly float hold = float.TryParse(SurvivorUnchained.Args.Get("house-fade-hold"), System.Globalization.NumberStyles.Float,
        System.Globalization.CultureInfo.InvariantCulture, out var h) ? Mathf.Clamp(h, 0, 1) : -1;
    readonly float[] ids = new float[8], amt = new float[8], cut = new float[8];
    readonly Vector3[] pts = new Vector3[5];
    // (-1: set on the first frame, so a zone left faded is cleared)
    Vector4 lastA = -Vector4.One, lastB = -Vector4.One, lastC = -Vector4.One, lastD = -Vector4.One, lastE = -Vector4.One, lastF = -Vector4.One;

    public override void _Process(double delta)
    {
        if (fade.Length != Units.Count) fade = new float[Units.Count];
        var cam = GetViewport()?.GetCamera3D();
        bool on = Her.W > 0 && cam != null;
        if (on)
        {
            var her = new Vector3(Her.X, Her.Y, Her.Z);
            var side = cam!.GlobalBasis.X with { Y = 0 };
            side = side.LengthSquared() > 1e-6f ? side.Normalized() * 0.35f : Vector3.Zero;
            pts[0] = her; pts[1] = her + new Vector3(0, 0.7f, 0); pts[2] = her - new Vector3(0, 0.7f, 0); pts[3] = her + side; pts[4] = her - side;
        }
        float step = (float)delta / Ease;
        for (int i = 0; i < Units.Count; i++)
        {
            bool hit = on && InWay(Units[i], cam!.GlobalPosition);
            if (away.Length != Units.Count) away = new float[Units.Count];
            away[i] = hit ? 0 : away[i] + (float)delta;
            bool want = hit || fade[i] > 0 && away[i] < Linger;
            float to = want ? (hold >= 0 ? hold : 1) : 0;
            fade[i] = hold >= 0 ? to : Mathf.MoveToward(fade[i], to, step);
        }
        if (++frames == 3) Attach();
        if (shown.Length != Units.Count) shown = new float[Units.Count];
        Follow();
        // the 8 most faded, eased (smoothstep) as the shader takes them
        System.Array.Clear(ids); System.Array.Clear(amt); System.Array.Clear(cut);
        int used = 0;
        for (int i = 0; i < fade.Length; i++)
        {
            if (fade[i] <= 0) continue;
            float f = hold >= 0 ? fade[i] : fade[i] * fade[i] * (3 - 2 * fade[i]);
            int at = used < 8 ? used++ : -1;
            if (at < 0)
            {
                // (more than 8: the least faded gives way)
                int m = 0;
                for (int j = 1; j < 8; j++) if (amt[j] < amt[m]) m = j;
                if (amt[m] >= f) continue;
                at = m;
            }
            ids[at] = i + 1; amt[at] = f; cut[at] = i < Cut.Count ? Cut[i] : -1e4f;
        }
        Set(IdsA, new Vector4(ids[0], ids[1], ids[2], ids[3]), ref lastA);
        Set(IdsB, new Vector4(ids[4], ids[5], ids[6], ids[7]), ref lastB);
        Set(AmtA, new Vector4(amt[0], amt[1], amt[2], amt[3]), ref lastC);
        Set(AmtB, new Vector4(amt[4], amt[5], amt[6], amt[7]), ref lastD);
        Set(CutA, new Vector4(cut[0], cut[1], cut[2], cut[3]), ref lastE);
        Set(CutB, new Vector4(cut[4], cut[5], cut[6], cut[7]), ref lastF);
    }

    /// <summary>The unit whose walls' box, grown by g (in x and z; y from its foot to its top plus up), holds p, or -1.</summary>
    int UnitAt(Vector3 p, float g, float up)
    {
        for (int u = 0; u < Units.Count; u++)
            foreach (var v in Units[u])
            {
                if (v.Ridge != 3) continue;
                var q = v.To * p;
                var b = v.Box;
                if (q.X > b.Position.X - g && q.X < b.End.X + g && q.Z > b.Position.Z - g && q.Z < b.End.Z + g && q.Y > b.Position.Y - 0.5f && q.Y < b.End.Y + up) return u;
            }
        return -1;
    }

    int SmokeUnit(Vector3 p)
    {
        foreach (var g in new[] { 0f, 0.3f, 0.75f, 1.5f })
            if (UnitAt(p, g, 7f) is int u && u >= 0) return u;
        return -1;
    }

    void Attach()
    {
        var root = GetTree().Root;
        var near = new List<(Vector3 At, int Unit)>();
        foreach (var (_, _, at, u) in Hung) near.Add((at.Origin, u));
        int Near(Vector3 p) { foreach (var (a, u) in near) if (a.DistanceTo(p) < 1.3f) return u; return -1; }
        var seen = new HashSet<ulong>();
        // (glow balls, landmarks.glb's "glow-*": by a hung lantern, or inside the house)
        foreach (var n in root.FindChildren("glow-*", "Node3D", true, false))
        {
            if (n is not Node3D g) continue;
            int u = Near(g.GlobalPosition);
            // (or on its wall: a lamp's ball within a metre of it, over its cut; or inside it)
            if (u < 0 && UnitAt(g.GlobalPosition, 1.0f, 0) is int w && w >= 0 && (g.GlobalPosition.Y > Cut[w] || UnitAt(g.GlobalPosition, -0.1f, 0) >= 0)) u = w;
            if (SurvivorUnchained.Args.Has("house-fade-debug")) GD.Print($"house fade glow {g.Name} at {g.GlobalPosition} unit {u} near {UnitAt(g.GlobalPosition, 3f, 3f)}");
            if (u < 0) continue;
            balls.Add((g, g.Scale, u));
            foreach (var gi in g.FindChildren("*", "GeometryInstance3D", true, false).Append(g).OfType<GeometryInstance3D>())
                if (seen.Add(gi.GetInstanceId())) faders.Add((gi, u));
        }
        // (the road's lamps the landmarks hang on our walls (Landmarks.Holders, their "lamp" meta): within a metre of its walls, over its cut,
        // and what is in them)
        foreach (var hn in root.FindChildren("*", "Node3D", true, false).OfType<Node3D>().Where(x => x.HasMeta("lamp")).ToList())
        {
            var hp = hn.GlobalPosition;
            int u = UnitAt(hp, 1.0f, 0);
            if (u < 0 || hp.Y < Cut[u]) continue;
            near.Add((hp, u));
            foreach (var gi in hn.FindChildren("*", "GeometryInstance3D", true, false).OfType<GeometryInstance3D>())
                if (seen.Add(gi.GetInstanceId())) faders.Add((gi, u));
        }
        // (the flames and glass in a hung lantern: small pieces, not the kit's MultiMeshes)
        if (near.Count > 0)
            foreach (var n in root.FindChildren("*", "GeometryInstance3D", true, false))
                if (n is GeometryInstance3D gi && gi is not MultiMeshInstance3D && Near(gi.GlobalPosition) is int u && u >= 0
                    && (gi.GlobalTransform * gi.GetAabb()).Size.Length() < 1.6f && seen.Add(gi.GetInstanceId()))
                    faders.Add((gi, u));
        foreach (var n in root.FindChildren("*", "Light3D", true, false))
            if (n is OmniLight3D or SpotLight3D && n is Light3D l)
            {
                int u = Near(l.GlobalPosition);
                if (u < 0) u = UnitAt(l.GlobalPosition, 0.8f, 0);
                if (u >= 0) lamps.Add((l, l.LightColor, u));
            }
        if (SurvivorUnchained.Args.Has("house-fade-debug"))
            foreach (var n in root.FindChildren("Chimney*", "", true, false)) GD.Print($"house fade smoke {n.Name} {n.GetClass()} at {(n as Node3D)?.GlobalPosition} unit {UnitAt(((Node3D)n).GlobalPosition, 3f, 6f)}");
        foreach (var n in root.FindChildren("Chimney*", "GPUParticles3D", true, false))
            // (E9d r3: the house the stack stands in first, then the nearest within 1.5 m: at 1.5 m first-found, a stack by a
            // party wall was tied to its cut neighbour, and the uncut house's plume went with that one)
            if (n is GpuParticles3D p && SmokeUnit(p.GlobalPosition) is int u && u >= 0) smokes.Add((p, u));
        foreach (var n in root.FindChildren("*", "Node3D", true, false).OfType<Node3D>().Where(x => x.HasMeta("inside") && x is not MultiMeshInstance3D).ToList())
        {
            int u = UnitAt(n.GlobalPosition + new Vector3(0, 0.3f, 0), 0.05f, 0);
            if (u < 0) continue;
            if (n is MeshInstance3D card && card.MaterialOverride is ShaderMaterial) { card.SetInstanceShaderParameter("unit", (float)(u + 1)); continue; }
            foreach (var gi in n.FindChildren("*", "GeometryInstance3D", true, false).OfType<GeometryInstance3D>()) { ins.Add((gi, u)); gi.Visible = false; gi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; }
            foreach (var l in n.FindChildren("*", "Light3D", true, false).OfType<Light3D>()) inLights.Add((l, l.LightEnergy, u));
        }
        foreach (var m in root.FindChildren("*", "MultiMeshInstance3D", true, false).OfType<MultiMeshInstance3D>().Where(x => x.HasMeta("inside"))) { m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; m.Visible = false; inMmis.Add(m); }
        GD.Print($"house fade: {faders.Count} faders, {lamps.Count} lights, {smokes.Count} smokes with their houses; {ins.Count} inside pieces, {inLights.Count} hearth lights");
    }

    float Eased(int u) => u >= fade.Length ? 0 : hold >= 0 ? fade[u] : fade[u] * fade[u] * (3 - 2 * fade[u]);

    void Follow()
    {
        foreach (var (g, u) in faders)
        {
            if (!IsInstanceValid(g)) continue;
            float f = Eased(u);
            if (Mathf.IsEqualApprox(g.Transparency, f)) continue;
            g.Transparency = f;
        }
        foreach (var (n, sc, u) in balls)
        {
            if (!IsInstanceValid(n)) continue;
            float f = Eased(u);
            if (f <= 0 && shown[u] <= 0) continue;
            n.Scale = sc * Mathf.Max(1e-4f, 1 - f);
        }
        for (int i = 0; i < lamps.Count; i++)
        {
            var (l, c, u) = lamps[i];
            if (!IsInstanceValid(l)) continue;
            float f = Eased(u), was = shown[u];
            // (its colour as the zone set it taken while the house stands, given back when it stands again)
            if (f <= 0) { if (was > 0) l.LightColor = c; else if (l.LightColor != c) lamps[i] = (l, l.LightColor, u); continue; }
            l.LightColor = new Color(c.R * (1 - f), c.G * (1 - f), c.B * (1 - f), c.A);
        }
        foreach (var (p, u) in smokes)
        {
            if (!IsInstanceValid(p)) continue;
            float f = Eased(u);
            if (f <= 0 && shown[u] <= 0) continue;
            p.Transparency = f;
            p.Emitting = f < 0.5f;
        }
        foreach (var (g, u) in ins)
        {
            if (!IsInstanceValid(g)) continue;
            float f = Eased(u);
            if (g.Visible != f > 0) g.Visible = f > 0;
            if (f > 0 && !Mathf.IsEqualApprox(g.Transparency, 1 - f)) g.Transparency = 1 - f;
        }
        bool anyCut = false;
        for (int u = 0; u < fade.Length && !anyCut; u++) anyCut = Eased(u) > 0 || shown[u] > 0;
        foreach (var m in inMmis) if (IsInstanceValid(m) && m.Visible != anyCut) m.Visible = anyCut;
        foreach (var (l, e, u) in inLights)
        {
            if (!IsInstanceValid(l)) continue;
            float f = Eased(u);
            l.Visible = f > 0;
            l.LightEnergy = e * f;
        }
        for (int u = 0; u < shown.Length; u++) shown[u] = fade[u];
    }

    static void Set(StringName name, Vector4 v, ref Vector4 last)
    {
        if (v == last) return;
        last = v;
        RenderingServer.GlobalShaderParameterSet(name, v);
    }

    bool InWay(Vol[] u, Vector3 cam)
    {
        foreach (var v in u)
        {
            var c = v.To * cam;
            foreach (var p in pts)
                if (Crosses(c, v.To * p, v.Box, v.Ridge)) return true;
        }
        return false;
    }

    /// <summary>Whether the segment a..b passes through the box, or with ridge 1 or 2 the roof prism in it (each plane clipped in turn).</summary>
    public static bool Crosses(Vector3 a, Vector3 b, Aabb box, int ridge = 0)
    {
        float t0 = 0, t1 = 1;
        var d = b - a;
        Vector3 min = box.Position, max = box.End;
        for (int k = 0; k < 3; k++)
        {
            float o = a[k], dk = d[k], lo = min[k], hi = max[k];
            if (Mathf.Abs(dk) < 1e-6f) { if (o < lo || o > hi) return false; continue; }
            float ta = (lo - o) / dk, tb = (hi - o) / dk;
            if (ta > tb) (ta, tb) = (tb, ta);
            t0 = Mathf.Max(t0, ta); t1 = Mathf.Min(t1, tb);
            if (t0 > t1) return false;
        }
        if (ridge is not (1 or 2)) return true;
        // the slopes: y + s (q - mid) * height / half <= top for s = -1, 1, q across the ridge (x for a ridge along z)
        int ac = ridge == 1 ? 2 : 0;
        float mid = (min[ac] + max[ac]) / 2, half = Mathf.Max((max[ac] - min[ac]) / 2, 1e-3f), k2 = (max.Y - min.Y) / half;
        for (int s = -1; s <= 1; s += 2)
        {
            float fa = a.Y + s * k2 * (a[ac] - mid) - max.Y, fb = b.Y + s * k2 * (b[ac] - mid) - max.Y;
            if (fa > 0 && fb > 0) return false;
            if (fa > 0) t0 = Mathf.Max(t0, fa / (fa - fb));
            else if (fb > 0) t1 = Mathf.Min(t1, fa / (fa - fb));
            if (t0 > t1) return false;
        }
        return true;
    }
}
