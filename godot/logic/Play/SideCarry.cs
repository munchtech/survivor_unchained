using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>(warden-move, max judge r3 option c; screen-aware, solver 15) The side carry: a layer over a held piece's grip
/// for when the hand that holds it faces the camera. At the den's steep camera (pitch 62) a long piece hanging along her
/// side reads as a cane, a still bar near vertical; and one 3D tip-back reads differently by heading: on the away
/// diagonals her back points toward the camera, so tipping the blade back turns it toward screen-down (still a stick), on
/// the toward diagonals away from it (too flat). So the layer works on screen. Each drawn pose it turns the piece in her
/// fist about her LEFT axis (level, through the fist's fitted pocket; + = tip behind her) by the tilt that puts the
/// blade's on-screen angle (from straight down, + toward her screen-back: the side of the screen behind her facing) at a
/// target: <see cref="RunAngle"/> at a run, <see cref="StandAngle"/> standing (never a cane), less on a strafe
/// (<see cref="StrafeCut"/>), and never past what the clamp on the blade's own 3D tip-back from her vertical
/// (<see cref="BackMin"/>..<see cref="BackMax"/>) allows less <see cref="CapRoom"/>; plus a swing in screen degrees, so it
/// is alike on every heading: a damped spring the fist's acceleration along her facing drives (the blade's inertia: the
/// fist pulled forward leaves the tip behind), so the blade swings each stride a few frames after the fist. It also turns
/// the tip in toward her body (<see cref="Splay"/>, more on the away diagonals: <see cref="SplayAway"/>) and out on a
/// strafe (<see cref="SplayStrafe"/>: clear of her crossing calf). The weight is how much her holding side faces the camera
/// (<see cref="Target"/>: none with the piece on the far side or squarely toward or away, so there the grip is exactly the
/// clips'), eased over <see cref="Ease"/>; the tilt changes at most <see cref="MaxRate"/> a second. Pure (no Godot):
/// PlayerView feeds it each drawn pose (the clip's blade, her axes, the camera's screen map at the grip) and turns the
/// piece by <see cref="Tilt"/> about her left, then <see cref="Inward"/> about her facing.</summary>
public sealed class SideCarry
{
    /// <summary>The blade's on-screen angle wanted at a run and standing (deg from straight down, toward her screen-back).</summary>
    public float RunAngle = 41f, StandAngle = 22f;
    /// <summary>Degrees less of it on a strafe (full sideways travel).</summary>
    public float StrafeCut = 14f;
    /// <summary>The swing: screen degrees per m/s² of the fist's acceleration along her facing (forward pull, tip back).</summary>
    public float Gain = 0.7f;
    /// <summary>The swing's spring: natural frequency (Hz) and damping ratio.</summary>
    public float Hz = 3f, Damping = 0.7f;
    /// <summary>How far the swing may go (screen deg), tip back and tip forward (less: a stop's swing forward never stands
    /// the blade straight down).</summary>
    public float Loose = 15f, LooseFwd = 8f;
    /// <summary>The largest acceleration the spring takes (m/s²): the arm's swing is about 20; a stop or a start, more, is cut to it.</summary>
    public float MaxAccel = 24f;
    /// <summary>The weight's ease, a time constant (s).</summary>
    public float Ease = 0.1f;
    /// <summary>The fastest the added tilt may change (deg/s; 150 is 5 a frame at 30 fps).</summary>
    public float MaxRate = 200f;
    /// <summary>The tip turned in toward her body at full weight (deg), more by <see cref="SplayAway"/> heading away from
    /// the camera (her back to it), less by <see cref="SplayStrafe"/> on a strafe.</summary>
    public float Splay = 3f, SplayAway = 10f, SplayStrafe = 18f;
    /// <summary>The clamp on the blade's own tip-back from her vertical (deg; the clip's and the layer's together).</summary>
    public float BackMin = 0f, BackMax = 50f;
    /// <summary>Screen degrees the target keeps under the clamp's angle (room for the back swing where the clamp binds).</summary>
    public float CapRoom = 6f;
    /// <summary>The weight's ramp: none at or under `side` Side0, full at Side1 (smooth between).</summary>
    public float Side0 = 0.15f, Side1 = 0.6f;

    /// <summary>The eased weight (0..1).</summary>
    public float Weight { get; private set; }
    /// <summary>The swing now (screen deg, + = tip back).</summary>
    public float Spring { get; private set; }
    /// <summary>The tilt the layer adds now (deg about her left, + = tip back): Weight * <see cref="Raw"/>, rate-limited.</summary>
    public float Tilt { get; private set; }
    /// <summary>The turn in toward her body it adds now (deg about her facing).</summary>
    public float Inward { get; private set; }
    /// <summary>The on-screen angle wanted now (deg, toward her screen-back) and the full-weight tilt that gives it (deg).</summary>
    public float Want { get; private set; }
    public float Raw { get; private set; }
    /// <summary>The screen side behind her (-1 = screen left, +1 = right).</summary>
    public float Sigma { get; private set; } = -1f;
    float springV;

    /// <summary>One drawn pose, in the world (y up): the clip's blade (grip to tip, before the layer), her left and her
    /// facing (level), the camera's screen map at the grip (rows: screen x and screen y, y down, per metre), the camera's
    /// back (its basis Z), how much she moves (0 standing .. 1 at a run) and how much of her travel is sideways (0..1).</summary>
    public readonly record struct Frame(Vector3 Blade, Vector3 Left, Vector3 Ahead, Vector3 Jx, Vector3 Jy, Vector3 CamBack,
        float Moving, float Strafe);

    /// <summary>The weight wanted for a side facing: `side` is the cosine between the holding hand's side (out from her,
    /// level) and the way back to the camera (level): full from <see cref="Side1"/> (the diagonals, 0.71, are full), none
    /// at or under <see cref="Side0"/> (facing toward, away, the piece on the far side).</summary>
    public float Target(float side)
    {
        if (side <= Side0) return 0f;
        if (side >= Side1 || Side1 <= Side0) return 1f;
        float t = (side - Side0) / (Side1 - Side0);
        return t * t * (3f - 2f * t);
    }

    /// <summary>`side` for a figure turned `faceRad` about up (Godot's yaw: she faces +Z at 0) with the camera's back (its
    /// basis Z, level) along `camBackX`, `camBackZ`, the piece in her right hand (`right`) or left. Her right is -X at yaw 0.</summary>
    public static float Side(float faceRad, float camBackX, float camBackZ, bool right = true)
    {
        float len = MathF.Sqrt(camBackX * camBackX + camBackZ * camBackZ);
        if (len < 1e-6f) return 0f;
        float sx = -MathF.Cos(faceRad), sz = MathF.Sin(faceRad);
        if (!right) { sx = -sx; sz = -sz; }
        return (sx * camBackX + sz * camBackZ) / len;
    }

    const float D2R = MathF.PI / 180f, R2D = 180f / MathF.PI;

    /// <summary>`v` turned `deg` about the unit `axis` (right hand: + about her left tips a hanging blade back).</summary>
    public static Vector3 Rot(Vector3 axis, float deg, Vector3 v)
    {
        float r = deg * D2R, c = MathF.Cos(r), s = MathF.Sin(r);
        return v * c + Vector3.Cross(axis, v) * s + axis * (Vector3.Dot(axis, v) * (1f - c));
    }

    /// <summary>The blade `b` turned `back` about her `left`, then `inward` about her `ahead` (as PersonView turns the piece).</summary>
    public static Vector3 Turned(Vector3 b, Vector3 left, float back, Vector3 ahead, float inward) => Rot(ahead, inward, Rot(left, back, b));

    /// <summary>A world direction's angle on screen through the rows `jx`, `jy` (deg from straight down; + toward the screen
    /// side `sigma`, -1 left or +1 right).</summary>
    public static float ScreenAngle(Vector3 d, Vector3 jx, Vector3 jy, float sigma)
        => MathF.Atan2(sigma * Vector3.Dot(jx, d), Vector3.Dot(jy, d)) * R2D;

    /// <summary>The blade's own tip-back from her vertical (deg; + = tip behind her facing).</summary>
    public static float BackOf(Vector3 b, Vector3 ahead) => MathF.Atan2(-Vector3.Dot(b, ahead), -b.Y) * R2D;

    static float Wrap(float d) { d %= 360f; return d > 180f ? d - 360f : d < -180f ? d + 360f : d; }

    /// <summary>The tilt in [lo, hi] (deg about `left`) that shows the blade `b` (turned `inward` after) on screen at `want`
    /// (deg toward `sigma`), solved exactly (the turned blade's screen image is a cos + b sin + c in the tilt), the root
    /// pointing the wanted way nearest `prev`; with none in range, the end nearer on screen.</summary>
    public static float Solve(Vector3 b, Vector3 left, Vector3 ahead, float inward, Vector3 jx, Vector3 jy, float sigma,
        float want, float lo, float hi, float prev)
    {
        if (hi < lo) hi = lo;
        // The screen rows seen through the inward turn after the tilt (its transpose: the turn back).
        var ix = Rot(ahead, -inward, jx);
        var iy = Rot(ahead, -inward, jy);
        float wr = want * D2R, dx = sigma * MathF.Sin(wr), dy = MathF.Cos(wr);
        var bl = left * Vector3.Dot(left, b);
        var bp = b - bl;
        var bq = Vector3.Cross(left, b);
        float Cr(Vector3 v) => Vector3.Dot(ix, v) * dy - Vector3.Dot(iy, v) * dx;   // the image's cross with the wanted way
        float Dp(Vector3 v) => Vector3.Dot(ix, v) * dx + Vector3.Dot(iy, v) * dy;   // and its share along it
        float a = Cr(bp), bb = Cr(bq), c = Cr(bl), r = MathF.Sqrt(a * a + bb * bb);
        float best = float.NaN, bestD = float.MaxValue, lr = lo * D2R, hr = hi * D2R;
        if (r > 1e-9f && MathF.Abs(c) <= r)
        {
            float ph = MathF.Atan2(bb, a), ac = MathF.Acos(Math.Clamp(-c / r, -1f, 1f));
            for (int i = 0; i < 2; i++)
                for (int k = -1; k <= 1; k++)
                {
                    float x = ph + (i == 0 ? ac : -ac) + k * 2f * MathF.PI;
                    if (x < lr - 1e-5f || x > hr + 1e-5f) continue;
                    if (Dp(bp) * MathF.Cos(x) + Dp(bq) * MathF.Sin(x) + Dp(bl) <= 0f) continue;   // the opposite way
                    float deg = Math.Clamp(x * R2D, lo, hi), dd = MathF.Abs(deg - prev);
                    if (dd < bestD) { bestD = dd; best = deg; }
                }
        }
        if (!float.IsNaN(best)) return best;
        float Err(float t) => MathF.Abs(Wrap(ScreenAngle(Turned(b, left, t, ahead, inward), jx, jy, sigma) - want));
        return Err(lo) <= Err(hi) ? lo : hi;
    }

    /// <summary>Back to no weight and no tilt, the spring at rest (a new body, a cut).</summary>
    public void Reset() { Weight = 0f; Spring = 0f; springV = 0f; Tilt = 0f; Inward = 0f; Raw = 0f; Want = 0f; }

    /// <summary>One step of `dt` seconds on the drawn pose `f`: the weight eased toward <see cref="Target"/> of her holding
    /// side's facing to the camera (none unless `on`), the swing driven by the grip's acceleration `accel` along her facing
    /// (m/s², + forward), the full-weight tilt solved for the target angle plus the swing, and the tilt moved toward
    /// Weight times it at most MaxRate.</summary>
    public void Step(float dt, bool on, float accel, in Frame f)
    {
        if (!(dt > 0f)) return;
        var cb = new Vector3(f.CamBack.X, 0f, f.CamBack.Z);
        float side = cb.LengthSquared() > 1e-8f ? Vector3.Dot(-f.Left, Vector3.Normalize(cb)) : 0f;
        float target = on && float.IsFinite(side) ? Target(side) : 0f;
        Weight = Ease > 0f ? Weight + (target - Weight) * (1f - MathF.Exp(-dt / Ease)) : target;
        if (Weight < 1e-4f && target == 0f) Weight = 0f;
        // The swing: a damped spring toward 0, pushed tip-back by a forward pull (fixed sub-steps for any frame rate).
        float k = MathF.Pow(2f * MathF.PI * Hz, 2f), cd = 2f * Damping * 2f * MathF.PI * Hz;
        int n = Math.Max(1, (int)MathF.Ceiling(dt / (1f / 240f)));
        float h = dt / n, drive = k * Gain * Math.Clamp(float.IsFinite(accel) ? accel : 0f, -MaxAccel, MaxAccel);
        for (int i = 0; i < n; i++)
        {
            float acc = drive - k * Spring - cd * springV;
            springV += acc * h;
            Spring += springV * h;
            if (Spring > Loose) { Spring = Loose; if (springV > 0f) springV = 0f; }
            if (Spring < -LooseFwd) { Spring = -LooseFwd; if (springV < 0f) springV = 0f; }
        }
        float step = MaxRate * dt;
        var b = f.Blade;
        if (Weight == 0f || b.LengthSquared() < 1e-8f || f.Left.LengthSquared() < 1e-8f || f.Ahead.LengthSquared() < 1e-8f)
        {
            Tilt += Math.Clamp(-Tilt, -step, step);
            if (MathF.Abs(Tilt) < 1e-3f) Tilt = 0f;
            Inward = Weight == 0f ? 0f : Inward;
            return;
        }
        b = Vector3.Normalize(b);
        var left = Vector3.Normalize(f.Left);
        var ahead = Vector3.Normalize(f.Ahead);
        // Her screen-back: the screen side her facing is not on (kept when she faces squarely up or down the screen).
        float fx = Vector3.Dot(ahead, f.Jx);
        if (MathF.Abs(fx) > 1e-4f * (f.Jx.Length() + 1e-6f)) Sigma = fx > 0f ? -1f : 1f;
        float away = cb.LengthSquared() > 1e-8f ? Math.Clamp(-Vector3.Dot(ahead, Vector3.Normalize(cb)), 0f, 1f) : 0f;
        float strafe = Math.Clamp(f.Strafe, 0f, 1f), moving = Math.Clamp(f.Moving, 0f, 1f);
        float psi = Splay + SplayAway * away - SplayStrafe * strafe;
        float back = BackOf(b, ahead), lo = BackMin - back, hi = BackMax - back;
        float aim = StandAngle + (RunAngle - StandAngle) * moving - StrafeCut * strafe;
        float cap = ScreenAngle(Turned(b, left, hi, ahead, psi), f.Jx, f.Jy, Sigma) - CapRoom;
        if (cap > -90f && cap < aim) aim = cap;
        Want = aim + Spring;
        Raw = Solve(b, left, ahead, psi, f.Jx, f.Jy, Sigma, Want, lo, hi, Raw);
        Tilt += Math.Clamp(Weight * Raw - Tilt, -step, step);
        Inward = Weight * psi;
    }
}
