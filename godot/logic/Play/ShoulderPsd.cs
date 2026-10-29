using System;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her shoulder and armpit pose-space correctives (tools/assets/shoulder_psd_post.py, armor 17 C1): morphs
/// authored at sample raises of one upper arm (A 117 and 140 sideways and forward, 175 overhead; C2: 117, where the close-range clips live, was 110), weighted here
/// from the arm's direction in her torso frame. A is the angle from her torso's down axis (neck_01 to pelvis):
/// 90 level with the shoulder, 180 overhead; the azimuth is 0 out to her side, 90 forward, negative back.
/// Nothing up to <see cref="EaseFrom"/> (rest and arms-down poses are untouched), the level sample
/// (shoulder_lvl80, Body 9: tools/assets/shoulder_sculpt_post.py's lowered key) eased in to <see cref="Level"/>
/// and handed (eased) to the first samples by <see cref="First"/> (their weights as before), then linear between
/// them. Python's twin: shoulder_psd_post.psd_weights.
/// </summary>
public static class ShoulderPsd
{
    public const float EaseFrom = 60f;   // (Body 9, was 90: the level sample eases in from here; the Look's arms reach ~55)

    /// <summary>The level sample's raise (A degrees): whole here.</summary>
    public const float Level = 80f;

    /// <summary>The shapes (each with _l or _r), in the order <see cref="Weights"/> fills.</summary>
    public static readonly string[] Shapes =
    {
        "shoulder_abd117", "shoulder_abd140", "shoulder_flex117", "shoulder_flex140", "shoulder_up175",
        "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s", "shoulder_lvl80",
    };

    /// <summary>The first samples' raise (A degrees).</summary>
    public const float First = 117f;

    /// <summary>Her clavicle's rise past <see cref="ClavicleLift.Target"/> (degrees) at which the 140 and 175 samples are
    /// wholly their shrugged twins (the plain samples are authored with the clavicle lift HerShrug gives, the twins
    /// this much higher, as leap raises it).</summary>
    public const float Shrug = 30f;

    static float Ramp(float x, float a, float b) => Math.Clamp((x - a) / (b - a), 0f, 1f);

    /// <summary>The shapes' weights for an upper arm at (a, azimuth) degrees with its clavicle risen
    /// <paramref name="rise"/> degrees above rest (HerShrug's lift in), into <paramref name="w"/> (Shapes' order).</summary>
    public static void Weights(float a, float azimuth, float rise, Span<float> w)
    {
        float e90 = Ramp(a, EaseFrom, Level);
        e90 = e90 * e90 * (3 - 2 * e90);
        float e = Ramp(a, Level, First);
        e = e * e * (3 - 2 * e);
        float t110 = e * (1 - Ramp(a, First, 140f));
        float t140 = Ramp(a, First, 140f) * (1 - Ramp(a, 140f, 175f));
        float t175 = Ramp(a, 140f, 175f);
        float s = MathF.Sin(Math.Clamp(azimuth, 0f, 90f) * MathF.PI / 180f);
        float wf = s * s, wa = 1 - wf;
        float r = Math.Clamp((rise - ClavicleLift.Target(a)) / Shrug, 0f, 1f);
        w[0] = wa * t110; w[1] = wa * t140 * (1 - r); w[2] = wf * t110; w[3] = wf * t140 * (1 - r); w[4] = t175 * (1 - r);
        w[5] = wa * t140 * r; w[6] = wf * t140 * r; w[7] = t175 * r;
        w[8] = e90 * (1 - e);
    }

    /// <summary>A line's elevation in degrees above the plane square to <paramref name="down"/>.</summary>
    public static float Elevation((float X, float Y, float Z) v, (float X, float Y, float Z) down)
    {
        float n = MathF.Sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) * MathF.Sqrt(down.X * down.X + down.Y * down.Y + down.Z * down.Z);
        if (n < 1e-9f) return 0;
        return MathF.Asin(Math.Clamp(-(v.X * down.X + v.Y * down.Y + v.Z * down.Z) / n, -1f, 1f)) * 180f / MathF.PI;
    }

    /// <summary>(A, azimuth) in degrees of an upper arm direction, given her torso's down axis and the lateral axis
    /// out to that arm's side (both unit; lateral need not be square to down) and her forward. Plain floats so the
    /// logic needs no engine.</summary>
    public static (float A, float Azimuth) Angles(
        (float X, float Y, float Z) arm, (float X, float Y, float Z) down, (float X, float Y, float Z) lateral,
        (float X, float Y, float Z) forward)
    {
        static float Dot((float X, float Y, float Z) p, (float X, float Y, float Z) q) => p.X * q.X + p.Y * q.Y + p.Z * q.Z;
        static (float, float, float) Unit((float X, float Y, float Z) p)
        {
            float n = MathF.Sqrt(Dot(p, p));
            return n < 1e-9f ? (0, 0, 0) : (p.X / n, p.Y / n, p.Z / n);
        }
        var d = Unit(arm);
        var dn = Unit(down);
        float k = Dot(lateral, dn);
        var lat = Unit((lateral.X - k * dn.Item1, lateral.Y - k * dn.Item2, lateral.Z - k * dn.Item3));
        k = Dot(forward, dn);
        var f0 = (forward.X - k * dn.Item1, forward.Y - k * dn.Item2, forward.Z - k * dn.Item3);
        k = Dot(f0, lat);
        var fwd = Unit((f0.Item1 - k * lat.Item1, f0.Item2 - k * lat.Item2, f0.Item3 - k * lat.Item3));
        float a = MathF.Acos(Math.Clamp(Dot(d, dn), -1f, 1f)) * 180f / MathF.PI;
        float az = MathF.Atan2(Dot(d, fwd), Dot(d, lat)) * 180f / MathF.PI;
        return (a, az);
    }
}
