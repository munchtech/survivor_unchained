using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (E9c) The house fade (look bible 08, "The trick" 1): the part of a house that stands between the survivor and the
/// play camera (OwnWalls' fade units: a house, or a 12 m length of a long one) fades out with a screen-door cut
/// (kit.gdshader's house_fade_of, a threshold moved every frame that the temporal smoothing sums), easing in and out
/// over 0.3 s; its shadow stays (the cut is made only in the camera's view). A unit is in her way when the line from
/// the camera to any of five points on her (chest, head, knees, and the chest half a metre either side across the
/// screen) passes through its box. At most 8 units fade at once (the nearest-faded kept).
/// --house-fade-hold F: every fade in her way held at F (0..1), for the mid-fade frames.
/// </summary>
public sealed partial class HouseFade : Node
{
    /// <summary>Her chest (xyz) and 1 in w while she is in the world (WorldScene sets it each frame).</summary>
    public static Vector4 Her;

    /// <summary>Each unit's frame (its house's cos and sin of yaw) and its box in that frame (x along, y up, z across).</summary>
    public readonly List<(float C, float S, Vector3 Min, Vector3 Max)> Units = new();

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
            side = side.LengthSquared() > 1e-6f ? side.Normalized() * 0.5f : Vector3.Zero;
            pts[0] = her; pts[1] = her + new Vector3(0, 0.7f, 0); pts[2] = her - new Vector3(0, 0.7f, 0); pts[3] = her + side; pts[4] = her - side;
        }
        float step = (float)delta / Ease;
        for (int i = 0; i < Units.Count; i++)
        {
            bool hit = on && InWay(Units[i], cam!.GlobalPosition);
            float to = hit ? (hold >= 0 ? hold : 1) : 0;
            fade[i] = hold >= 0 ? to : Mathf.MoveToward(fade[i], to, step);
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

    bool InWay((float C, float S, Vector3 Min, Vector3 Max) u, Vector3 cam)
    {
        if (u.Max.X <= u.Min.X) return false;
        foreach (var p in pts)
            if (Crosses(Local(u, cam), Local(u, p), u.Min, u.Max)) return true;
        return false;
    }

    static Vector3 Local((float C, float S, Vector3 Min, Vector3 Max) u, Vector3 p) => new(p.X * u.C + p.Z * u.S, p.Y, -p.X * u.S + p.Z * u.C);

    /// <summary>Whether the segment a..b passes through the box (slabs).</summary>
    public static bool Crosses(Vector3 a, Vector3 b, Vector3 min, Vector3 max)
    {
        float t0 = 0, t1 = 1;
        var d = b - a;
        for (int k = 0; k < 3; k++)
        {
            float o = a[k], dk = d[k], lo = min[k], hi = max[k];
            if (Mathf.Abs(dk) < 1e-6f) { if (o < lo || o > hi) return false; continue; }
            float ta = (lo - o) / dk, tb = (hi - o) / dk;
            if (ta > tb) (ta, tb) = (tb, ta);
            t0 = Mathf.Max(t0, ta); t1 = Mathf.Min(t1, tb);
            if (t0 > t1) return false;
        }
        return true;
    }
}
