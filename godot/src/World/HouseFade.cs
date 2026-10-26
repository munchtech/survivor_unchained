using System.Collections.Generic;
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

    /// <summary>What hangs on a unit's walls (kit lanterns, torches: OwnWalls.FadeUnits): one copy of a MultiMesh, put out
    /// of view while its unit is more than half faded (too small to want a fade of its own).</summary>
    public readonly List<(MultiMesh Mm, int I, Transform3D At, int Unit)> Hung = new();
    bool[] hidden = System.Array.Empty<bool>();
    // (the lanterns' glow balls, landmarks.glb's "glow-*" nodes within 0.8 m of a hung lantern: shrunk away with it, not
    // hidden, as ZoneView shows and hides them by the light's hours)
    readonly List<(Node3D N, Vector3 Scale, int Hung)> glows = new();
    int frames;

    const float Ease = 0.3f;
    static readonly StringName IdsA = "house_fade_ids", IdsB = "house_fade_ids2", AmtA = "house_fade", AmtB = "house_fade2";
    float[] fade = System.Array.Empty<float>();
    readonly float hold = float.TryParse(SurvivorUnchained.Args.Get("house-fade-hold"), System.Globalization.NumberStyles.Float,
        System.Globalization.CultureInfo.InvariantCulture, out var h) ? Mathf.Clamp(h, 0, 1) : -1;
    readonly float[] ids = new float[8], amt = new float[8];
    readonly Vector3[] pts = new Vector3[5];
    // (-1: set on the first frame, so a zone left faded is cleared)
    Vector4 lastA = -Vector4.One, lastB = -Vector4.One, lastC = -Vector4.One, lastD = -Vector4.One;

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
            float to = hit ? (hold >= 0 ? hold : 1) : 0;
            fade[i] = hold >= 0 ? to : Mathf.MoveToward(fade[i], to, step);
        }
        if (hidden.Length != Hung.Count) hidden = new bool[Hung.Count];
        if (++frames == 3 && Hung.Count > 0)
            foreach (var n in GetTree().Root.FindChildren("glow-*", "Node3D", true, false))
                if (n is Node3D g)
                    for (int i = 0; i < Hung.Count; i++)
                        if (g.GlobalPosition.DistanceTo(Hung[i].At.Origin) < 0.8f) { glows.Add((g, g.Scale, i)); break; }
        for (int i = 0; i < Hung.Count; i++)
        {
            var (mm, ix, at, unit) = Hung[i];
            bool hide = fade[unit] > 0.5f;
            if (hide == hidden[i]) continue;
            hidden[i] = hide;
            mm.SetInstanceTransform(ix, hide ? new Transform3D(new Basis().Scaled(Vector3.Zero), at.Origin) : at);
            foreach (var (g, sc, hi) in glows) if (hi == i && IsInstanceValid(g)) g.Scale = hide ? sc * 1e-4f : sc;
        }
        // the 8 most faded, eased (smoothstep) as the shader takes them
        System.Array.Clear(ids); System.Array.Clear(amt);
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
            ids[at] = i + 1; amt[at] = f;
        }
        Set(IdsA, new Vector4(ids[0], ids[1], ids[2], ids[3]), ref lastA);
        Set(IdsB, new Vector4(ids[4], ids[5], ids[6], ids[7]), ref lastB);
        Set(AmtA, new Vector4(amt[0], amt[1], amt[2], amt[3]), ref lastC);
        Set(AmtB, new Vector4(amt[4], amt[5], amt[6], amt[7]), ref lastD);
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
