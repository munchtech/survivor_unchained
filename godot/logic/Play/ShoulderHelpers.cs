using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her shoulder's muscle helpers (Body 6 S2; tools/anim/helpers.py SPEC "shoulder", its twin
/// <c>helpers.shoulder_helper</c>): per side delt (the deltoid bunching on the upper arm's outer side), trap (the outer
/// trapezius top lifted 15 mm), pec (the pec's lower-lateral band turned and stretched toward the arm) and lat (the lat
/// band below the armpit turned in toward the arm's line). Each is a bone built into her body (shoulder_rig_post.py), a
/// child of the bone whose weight it takes, with its global rest at its pivot. Below <see cref="A0"/> degrees of the
/// upper arm's angle it moves exactly as its parent (her idles and the Look keep their shoulders); past it, g (a
/// smoothstep to <see cref="A1"/>) of a turn toward its aim, a stretch and a move. Continuous in A, no keys. Engine-free
/// (System.Numerics types, the math in double, skeleton space); View/HerShoulder runs it after HerScap, only where the
/// bones are.
/// </summary>
public static class ShoulderHelpers
{
    public const float A0 = 60f, A1 = 120f;

    /// <summary>One helper's numbers (SPEC shoulder bones). <c>Pivot</c>: her left rest space, the right mirrored in x;
    /// <c>HumPivot</c> (if not negative) instead that many meters down the humerus from the joint. <c>Aim</c> (null for
    /// trap): meters down the humerus, plus <c>AimOff</c> (x negated on the right).</summary>
    public sealed record Kind(string Name, string Parent, Vector3 Pivot, float HumPivot, float[]? Aim, Vector3 AimOff, string On,
        float Follow, float Ka, float Kp, float Sa, float Sp, Vector3 Off);

    public static readonly Kind Delt = new("delt", "upperarm_twist_02_{s}", default, 0.05f, new[] { 0.30f }, Vector3.Zero, "upperarm_{s}",
        0f, 0f, 0f, -0.10f, 0.45f, Vector3.Zero);
    public static readonly Kind Trap = new("trap", "clavicle_{s}", new(0.10f, 1.535f, -0.04f), -1f, null, Vector3.Zero, "upperarm_{s}",
        0f, 0f, 0f, 0f, 0f, new(0f, 0.015f, 0f));
    public static readonly Kind Pec = new("pec", "spine_03", new(0.05f, 1.42f, 0.05f), -1f, new[] { 0.08f }, new(0f, 0f, 0.025f), "upperarm_{s}",
        0.2f, 0.5f, 0f, 0f, 0f, Vector3.Zero);
    public static readonly Kind Lat = new("lat", "spine_03", new(0.09f, 1.20f, -0.05f), -1f, new[] { 0.07f }, new(-0.01f, 0f, 0.01f), "upperarm_{s}",
        0.15f, 0f, 0f, 0f, 0f, Vector3.Zero);

    public static readonly Kind[] All = { Delt, Trap, Pec, Lat };

    /// <summary>How far the helpers act (0-1) for an upper arm at <paramref name="a"/> degrees: a smoothstep over A0..A1.</summary>
    public static float G(float a) => (float)GD(a);

    static double GD(double a)
    {
        double t = Math.Clamp((a - A0) / (A1 - A0), 0.0, 1.0);
        return t * t * (3 - 2 * t);
    }

    static Vector3 Mirror(Vector3 v, bool left) => left ? v : new Vector3(-v.X, v.Y, v.Z);

    /// <summary>The pivot (her rest space) from the upper arm's and forearm's rest origins.</summary>
    public static Vector3 Pivot(Kind k, bool left, Vector3 upperRest, Vector3 lowerRest)
    {
        if (k.HumPivot < 0) return Mirror(k.Pivot, left);
        return upperRest + Vector3.Normalize(lowerRest - upperRest) * k.HumPivot;
    }

    /// <summary>The move (her rest axes) for a side: x negated on the right.</summary>
    public static Vector3 Off(Kind k, bool left) => Mirror(k.Off, left);

    /// <summary>The aim point T0 (a point on her humerus carried by the upper arm; null for trap) and the pivot-to-aim
    /// length L0 (1 if none) from the rest origins and the pivot.</summary>
    public static (Vector3? T0, float L0) RestAim(Kind k, bool left, Vector3 upperRest, Vector3 lowerRest, Vector3 pivot)
    {
        if (k.Aim == null) return (null, 1f);
        var h = Vector3.Normalize(lowerRest - upperRest);
        var t0 = upperRest + k.Aim[0] * h + Mirror(k.AimOff, left);
        return (t0, (t0 - pivot).Length());
    }

    // ---- double 3x3 helpers (row-major m[r*3+c]) ----
    static double[] Mat(Quaternion q)
    {
        double n = Math.Sqrt((double)q.X * q.X + (double)q.Y * q.Y + (double)q.Z * q.Z + (double)q.W * q.W);
        double x = q.X / n, y = q.Y / n, z = q.Z / n, w = q.W / n;
        return new[] { 1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
                       2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
                       2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y) };
    }

    static double[] Mul(double[] a, double[] b)
    {
        var r = new double[9];
        for (int i = 0; i < 3; i++)
            for (int j = 0; j < 3; j++)
                r[i * 3 + j] = a[i * 3] * b[j] + a[i * 3 + 1] * b[3 + j] + a[i * 3 + 2] * b[6 + j];
        return r;
    }

    static double[] T(double[] a) => new[] { a[0], a[3], a[6], a[1], a[4], a[7], a[2], a[5], a[8] };
    static double[] Vec(Vector3 v) => new double[] { v.X, v.Y, v.Z };
    static double[] Apply(double[] m, double[] v) => new[] { m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2], m[6] * v[0] + m[7] * v[1] + m[8] * v[2] };
    static double[] Sub(double[] a, double[] b) => new[] { a[0] - b[0], a[1] - b[1], a[2] - b[2] };
    static double[] Add(double[] a, double[] b) => new[] { a[0] + b[0], a[1] + b[1], a[2] + b[2] };
    static double Dot(double[] a, double[] b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    static double Len(double[] a) => Math.Sqrt(Dot(a, a));
    static double[] Cross(double[] a, double[] b) => new[] { a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0] };
    static double[] Col(double[] m, int c) => new[] { m[c], m[3 + c], m[6 + c] };

    static double[] Turn(double[] ax, double ang)
    {
        double s = Math.Sin(ang), c = Math.Cos(ang), x = ax[0], y = ax[1], z = ax[2];
        double[] k = { 0, -z, y, z, 0, -x, -y, x, 0 };
        var kk = Mul(k, k);
        var r = new double[9];
        for (int i = 0; i < 9; i++) r[i] = (i % 4 == 0 ? 1 : 0) + s * k[i] + (1 - c) * kk[i];
        return r;
    }

    static Quaternion ToQuat(double[] m)
    {
        double tr = m[0] + m[4] + m[8], x, y, z, w;
        if (tr > 0) { double s = Math.Sqrt(tr + 1) * 2; w = 0.25 * s; x = (m[7] - m[5]) / s; y = (m[2] - m[6]) / s; z = (m[3] - m[1]) / s; }
        else if (m[0] > m[4] && m[0] > m[8]) { double s = Math.Sqrt(1 + m[0] - m[4] - m[8]) * 2; w = (m[7] - m[5]) / s; x = 0.25 * s; y = (m[1] + m[3]) / s; z = (m[2] + m[6]) / s; }
        else if (m[4] > m[8]) { double s = Math.Sqrt(1 + m[4] - m[0] - m[8]) * 2; w = (m[2] - m[6]) / s; x = (m[1] + m[3]) / s; y = 0.25 * s; z = (m[5] + m[7]) / s; }
        else { double s = Math.Sqrt(1 + m[8] - m[0] - m[4]) * 2; w = (m[3] - m[1]) / s; x = (m[2] + m[6]) / s; y = (m[5] + m[7]) / s; z = 0.25 * s; }
        double n = Math.Sqrt(x * x + y * y + z * z + w * w);
        return new Quaternion((float)(x / n), (float)(y / n), (float)(z / n), (float)(w / n));
    }

    /// <summary>One helper's local pose under its parent's posed global (Godot: pose = T*R*S, scale in its own axes).
    /// Parent posed (<paramref name="rp"/>, <paramref name="op"/>) and rest (<paramref name="rp0"/>, <paramref name="op0"/>)
    /// globals; the helper's rest global (<paramref name="rh0"/>, <paramref name="oh0"/> = its pivot); the aim's carrier
    /// (the upper arm) posed and rest globals; <paramref name="t0"/> (null: no aim), <paramref name="l0"/>,
    /// <paramref name="off"/> (already mirrored) and <paramref name="a"/> (degrees). Below A0 the result is exactly the
    /// parent-following rest local pose (scale 1).</summary>
    public static (Quaternion Rotation, Vector3 Scale, Vector3 Position) Pose(Kind k,
        Quaternion rp, Vector3 op, Quaternion rp0, Vector3 op0, Quaternion rh0, Vector3 oh0,
        Quaternion ron, Vector3 oon, Quaternion ron0, Vector3 oon0, Vector3? t0, float l0, Vector3 off, float a)
    {
        double g = GD(a);
        var Rp = Mat(rp);
        var rrel = Mul(Rp, T(Mat(rp0)));
        var rf = Mul(rrel, Mat(rh0));
        var opd = Vec(op);
        var o = Add(opd, Apply(rrel, Sub(Vec(oh0), Vec(op0))));
        double sa = 1, sp = 1;
        if (t0 is Vector3 tt && g > 0)
        {
            var t = Add(Vec(oon), Apply(Mul(Mat(ron), T(Mat(ron0))), Sub(Vec(tt), Vec(oon0))));
            var d = Sub(t, o);
            double r = Len(d) / l0;
            var y = Col(rf, 1);
            var ax = Cross(y, d);
            double sn = Len(ax);
            if (k.Follow > 0 && sn > 1e-9)
                rf = Mul(Turn(new[] { ax[0] / sn, ax[1] / sn, ax[2] / sn }, Math.Atan2(sn, Dot(y, d)) * k.Follow * g), rf);
            sa *= 1 + g * (Math.Pow(r, k.Ka) - 1);
            sp *= 1 + g * (Math.Pow(r, -k.Kp) - 1);
        }
        sa *= 1 + g * k.Sa;
        sp *= 1 + g * k.Sp;
        var mv = Apply(rrel, Vec(off));
        o = new[] { o[0] + g * mv[0], o[1] + g * mv[1], o[2] + g * mv[2] };
        var rpt = T(Rp);
        var pos = Apply(rpt, Sub(o, opd));
        return (ToQuat(Mul(rpt, rf)), new Vector3((float)sp, (float)sa, (float)sp), new Vector3((float)pos[0], (float)pos[1], (float)pos[2]));
    }
}
