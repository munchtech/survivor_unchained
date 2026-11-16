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
    public float RunAngle = 41f, StandAngle = 30f;
    /// <summary>Degrees less of it on a strafe (full sideways travel).</summary>
    public float StrafeCut = 4f;
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
    /// <summary>The fastest the added tilt may change (deg/s; a safety only: the on-screen limit is <see cref="ScreenRate"/>).</summary>
    public float MaxRate = 900f;
    /// <summary>The tip turned in toward her body at full weight (deg), more by <see cref="SplayAway"/> heading away from
    /// the camera (her back to it), less by <see cref="SplayStrafe"/> on a strafe.</summary>
    public float Splay = 3f, SplayAway = 30f, SplayStrafe = 18f;
    /// <summary>The clamp on the blade's own tip-back from her vertical (deg; the clip's and the layer's together).</summary>
    public float BackMin = 0f, BackMax = 50f;
    /// <summary>Screen degrees the target keeps under the clamp's angle (room for the back swing where the clamp binds).</summary>
    public float CapRoom = 6f;
    /// <summary>The weight's ramp: none at or under `side` Side0, full at Side1 (smooth between).</summary>
    public float Side0 = 0.15f, Side1 = 0.6f;
    /// <summary>(judge r4) The weight falls at most from full to none in this long (s; 0.27 is 8 frames at 30 fps): a fade
    /// out of a sword-side stand never flicks.</summary>
    public float FadeOut = 0.27f;
    /// <summary>(judge r4) The layer's own on-screen turn of the blade (its shift over the clip's blade) changes at most this
    /// fast (deg/s; 150 is 5 a frame): the drawn blade turns at most that much faster than the body turns it.</summary>
    public float ScreenRate = 150f;
    /// <summary>(judge r4) The layer never turns the blade past this from straight down on screen (deg), nor further out than
    /// the clip's own blade where that is already past it.</summary>
    public float Edge = 65f;
    /// <summary>(judge r4) The most out-splay (deg, tip out from her holding side) the blade may have with the layer's turn:
    /// on a strafe the out-turn foreshortens it toward the camera.</summary>
    public float SplayOutMax = 18f;
    /// <summary>(judge r4) Standing, the swing settles with this time constant (s) and takes no stride drive: a static stand.</summary>
    public float StandSettle = 0.08f;
    /// <summary>(judge r4) The wanted angle never under this (deg toward her screen-back) where the clamp allows it.</summary>
    public float Floor = 20f;
    /// <summary>(judge r4, solver 17) Standing, the most extra turn in toward her body (deg) the layer takes where the stand's
    /// angle is out of the tilt's reach (the away diagonals, where the stop clip throws the blade out): just enough to reach it,
    /// so the stand holds still on screen while the clip's idle moves; none at a run (scaled by 1 - moving).</summary>
    public float InMax = 20f;
    /// <summary>(judge r4, solver 18) Blade-calf clearance: while a calf (the capsule <see cref="CalfKnee"/> at the knee to
    /// <see cref="CalfAnkle"/> at the ankle, m) nears the drawn blade (from 0.10 m along it to the tip), the tip turns out
    /// from her body (<see cref="OutTurn"/>) by the least that keeps it <see cref="Clear"/> (m) off, or as far as the clip's own
    /// blade is where that is nearer; at most <see cref="OutMax"/> (deg) times the weight. Moving, it starts early on the
    /// calves' paths extrapolated <see cref="ClearLook"/> frames (rising at most <see cref="ClearAtk"/> deg/s past this frame's
    /// need, a need j frames out taken less j times <see cref="ClearRate"/>), and eases back at <see cref="ClearDown"/> deg/s.
    /// Clear 0: off. Needs the frame's grip, length and calves.</summary>
    public float Clear = 0.055f, OutMax = 15f, ClearRate = 90f, ClearAtk = 100f, ClearDown = 90f, CalfKnee = 0.074f, CalfAnkle = 0.046f;
    public int ClearLook = 4;
    /// <summary>The out-turn for the calf's clearance now (deg; taken off <see cref="Inward"/>).</summary>
    public float OutTurn { get; private set; }
    readonly Vector3[] calfHist = new Vector3[12];   // the last three frames' knee L, ankle L, knee R, ankle R (from the grip)
    int calfN;

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
    /// <summary>The layer's own turn of the blade on screen now (deg, screen right +): the drawn blade's angle less the clip's.</summary>
    public float Shift { get; private set; }
    float springV, clipPrev = float.NaN;

    /// <summary>One drawn pose, in the world (y up): the clip's blade (grip to tip, before the layer), her left and her
    /// facing (level), the camera's screen map at the grip (rows: screen x and screen y, y down, per metre), the camera's
    /// back (its basis Z), how much she moves (0 standing .. 1 at a run) and how much of her travel is sideways (0..1).</summary>
    public readonly record struct Frame(Vector3 Blade, Vector3 Left, Vector3 Ahead, Vector3 Jx, Vector3 Jy, Vector3 CamBack,
        float Moving, float Strafe, Vector3 Grip = default, float Length = 0f, Vector3 KneeL = default, Vector3 AnkleL = default,
        Vector3 KneeR = default, Vector3 AnkleR = default);

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
    public void Reset() { Weight = 0f; Spring = 0f; springV = 0f; Tilt = 0f; Inward = 0f; Raw = 0f; Want = 0f; Shift = 0f; clipPrev = float.NaN; OutTurn = 0f; calfN = 0; }

    /// <summary>The closest points of segments p0p1 and q0q1: the distance and the share along q (0..1).</summary>
    static (float d, float u) SegDist(Vector3 p0, Vector3 p1, Vector3 q0, Vector3 q1)
    {
        Vector3 d1 = p1 - p0, d2 = q1 - q0, r = p0 - q0;
        float a = Vector3.Dot(d1, d1), e = Vector3.Dot(d2, d2), f = Vector3.Dot(d2, r), c = Vector3.Dot(d1, r), b = Vector3.Dot(d1, d2);
        if (a < 1e-12f || e < 1e-12f) return ((p0 - q0).Length(), 0f);
        float den = a * e - b * b, s = den > 1e-12f ? Math.Clamp((b * f - c * e) / den, 0f, 1f) : 0f, u = (b * s + f) / e;
        if (u < 0f) { u = 0f; s = Math.Clamp(-c / a, 0f, 1f); }
        else if (u > 1f) { u = 1f; s = Math.Clamp((b - c) / a, 0f, 1f); }
        return ((p0 + d1 * s - (q0 + d2 * u)).Length(), u);
    }

    /// <summary>The blade along unit `d` (from the grip, 0.10 m out to `len`) clear of the calves `c` (knee L, ankle L, knee R,
    /// ankle R from the grip): the least gap to their capsules (m).</summary>
    public float ClearOf(Vector3 d, float len, ReadOnlySpan<Vector3> c)
    {
        float best = 9f;
        for (int s = 0; s < 2; s++)
        {
            var (dd, u) = SegDist(d * 0.10f, d * len, c[2 * s], c[2 * s + 1]);
            best = MathF.Min(best, dd - (CalfKnee + (CalfAnkle - CalfKnee) * u));
        }
        return best;
    }

    /// <summary>The least out-turn (deg, 0.5 steps, to OutMax times the weight) that keeps the drawn blade `Clear` off the
    /// calves `c`, or as far as the clip's blade `b` is where that is nearer.</summary>
    float OutNeed(Vector3 b, Vector3 left, Vector3 ahead, float len, ReadOnlySpan<Vector3> c)
    {
        float want = MathF.Min(Clear, ClearOf(b, len, c)), top = OutMax * Weight;
        for (float p = 0f; p <= top + 0.01f; p += 0.5f)
            if (ClearOf(Turned(b, left, Tilt, ahead, Inward - p), len, c) >= want) return p;
        return top;
    }

    /// <summary>The calf clearance's out-turn (see <see cref="Clear"/>), taken off Inward; the calves' history kept.</summary>
    void ClearCalves(float dt, in Frame f, Vector3 b, Vector3 left, Vector3 ahead, float moving)
    {
        if (!(Clear > 0f) || !(f.Length > 0.1f)) { OutTurn = 0f; calfN = 0; return; }
        Span<Vector3> cur = stackalloc Vector3[4] { f.KneeL - f.Grip, f.AnkleL - f.Grip, f.KneeR - f.Grip, f.AnkleR - f.Grip };
        for (int i = 0; i < 8; i++) calfHist[i] = calfHist[i + 4];
        for (int i = 0; i < 4; i++) calfHist[8 + i] = cur[i];
        calfN = Math.Min(calfN + 1, 3);
        if (Weight == 0f && Tilt == 0f) { OutTurn = 0f; return; }
        float n0 = OutNeed(b, left, ahead, f.Length, cur), tg = n0, up = ClearRate * dt;
        if (moving >= 0.5f && calfN >= 2)
        {
            Span<Vector3> p = stackalloc Vector3[4];
            for (int j = 1; j <= ClearLook; j++)
            {
                for (int i = 0; i < 4; i++)
                {
                    Vector3 p2 = calfHist[8 + i], p1 = calfHist[4 + i];
                    p[i] = p2 + j * (p2 - p1);
                    if (calfN >= 3) p[i] += 0.5f * j * (j + 1) * (p2 - 2f * p1 + calfHist[i]);
                }
                tg = MathF.Max(tg, OutNeed(b, left, ahead, f.Length, p) - j * up);
            }
        }
        if (ClearAtk > 0f) tg = MathF.Max(n0, MathF.Min(tg, OutTurn + ClearAtk * dt));
        OutTurn = MathF.Max(tg, OutTurn - ClearDown * dt);
        Inward -= OutTurn;
    }

    /// <summary>One step of `dt` seconds on the drawn pose `f`: the weight eased toward <see cref="Target"/> of her holding
    /// side's facing to the camera (none unless `on`; falling no faster than <see cref="FadeOut"/>), the swing driven by the
    /// grip's acceleration `accel` along her facing (m/s², + forward) while she moves and settled out standing, the
    /// full-weight tilt solved for the target angle plus the swing; then the layer's on-screen shift of the blade moved
    /// toward Weight times that at most <see cref="ScreenRate"/>, kept inside <see cref="Edge"/>, and the tilt solved for it.</summary>
    public void Step(float dt, bool on, float accel, in Frame f)
    {
        if (!(dt > 0f)) return;
        var cb = new Vector3(f.CamBack.X, 0f, f.CamBack.Z);
        float side = cb.LengthSquared() > 1e-8f ? Vector3.Dot(-f.Left, Vector3.Normalize(cb)) : 0f;
        float target = on && float.IsFinite(side) ? Target(side) : 0f;
        float wn = Ease > 0f ? Weight + (target - Weight) * (1f - MathF.Exp(-dt / Ease)) : target;
        if (wn < Weight && FadeOut > 0f) wn = MathF.Max(wn, Weight - dt / FadeOut);
        Weight = wn < 1e-4f && target == 0f ? 0f : wn;
        float moving = Math.Clamp(float.IsFinite(f.Moving) ? f.Moving : 0f, 0f, 1f);
        // The swing: a damped spring toward 0, pushed tip-back by a forward pull while she moves (fixed sub-steps).
        float k = MathF.Pow(2f * MathF.PI * Hz, 2f), cd = 2f * Damping * 2f * MathF.PI * Hz;
        int n = Math.Max(1, (int)MathF.Ceiling(dt / (1f / 240f)));
        float h = dt / n, drive = moving * k * Gain * Math.Clamp(float.IsFinite(accel) ? accel : 0f, -MaxAccel, MaxAccel);
        for (int i = 0; i < n; i++)
        {
            float acc = drive - k * Spring - cd * springV;
            springV += acc * h;
            Spring += springV * h;
            if (Spring > Loose) { Spring = Loose; if (springV > 0f) springV = 0f; }
            if (Spring < -LooseFwd) { Spring = -LooseFwd; if (springV < 0f) springV = 0f; }
        }
        if (moving < 1f && StandSettle > 0f) { float g = MathF.Exp(-dt * (1f - moving) / StandSettle); Spring *= g; springV *= g; }
        float step = MaxRate * dt;
        var b = f.Blade;
        bool idle = Weight == 0f && Tilt == 0f && MathF.Abs(Shift) < 1e-3f;
        if (idle || b.LengthSquared() < 1e-8f || f.Left.LengthSquared() < 1e-8f || f.Ahead.LengthSquared() < 1e-8f
            || f.Jx.LengthSquared() < 1e-12f || f.Jy.LengthSquared() < 1e-12f)
        {
            Tilt += Math.Clamp(-Tilt, -step, step);
            if (MathF.Abs(Tilt) < 1e-3f) Tilt = 0f;
            Inward = Weight == 0f ? 0f : Inward;
            if (Tilt == 0f && Weight == 0f) { Shift = 0f; clipPrev = float.NaN; }
            OutTurn = 0f; calfN = 0;
            return;
        }
        b = Vector3.Normalize(b);
        var left = Vector3.Normalize(f.Left);
        var ahead = Vector3.Normalize(f.Ahead);
        // Her screen-back: the screen side her facing is not on (kept when she faces squarely up or down the screen).
        float fx = Vector3.Dot(ahead, f.Jx);
        if (MathF.Abs(fx) > 1e-4f * (f.Jx.Length() + 1e-6f)) Sigma = fx > 0f ? -1f : 1f;
        float away = cb.LengthSquared() > 1e-8f ? Math.Clamp(-Vector3.Dot(ahead, Vector3.Normalize(cb)), 0f, 1f) : 0f;
        float strafe = Math.Clamp(f.Strafe, 0f, 1f);
        float psi = Splay + SplayAway * away - SplayStrafe * strafe;
        // The out-splay cap: the clip's own (tip out to her holding side, + ) less the turn in stays under SplayOutMax.
        float own = MathF.Asin(Math.Clamp(-Vector3.Dot(b, left), -1f, 1f)) * R2D;
        if (own - psi > SplayOutMax) psi = own - SplayOutMax;
        float back = BackOf(b, ahead), lo = BackMin - back, hi = BackMax - back;
        float aim = StandAngle + (RunAngle - StandAngle) * moving - StrafeCut * strafe;
        // The room under the clamp is for the run's back swing: none standing (no swing), so the stand reaches its angle.
        float room = CapRoom * moving, sg = Sigma;
        Vector3 jx = f.Jx, jy = f.Jy, bc = b;
        float CapAt(float p) => ScreenAngle(Turned(bc, left, hi, ahead, p), jx, jy, sg);
        float cap = CapAt(psi) - room;
        // Standing, where the aim is past the clamp's reach: the tip turned in just enough more (up to InMax) to reach it.
        float im = InMax * (1f - moving);
        if (im > 0f && cap > -90f && cap < aim)
        {
            if (CapAt(psi + im) - room >= aim)
            {
                float l0 = psi, l1 = psi + im;
                for (int i = 0; i < 10; i++) { float m = 0.5f * (l0 + l1); if (CapAt(m) - room >= aim) l1 = m; else l0 = m; }
                psi = l1;
            }
            else psi += im;
            cap = CapAt(psi) - room;
        }
        if (cap > -90f && cap < aim) aim = cap;
        Want = MathF.Max(aim + Spring, MathF.Min(Floor, cap + room));
        Raw = Weight > 0f ? Solve(b, left, ahead, psi, f.Jx, f.Jy, Sigma, Want, lo, hi, Raw) : Raw;
        // The drawn blade on screen (deg, screen right +): toward the weighted tilt's, turning at most ScreenRate faster than
        // the clip's own blade turns (holding still is always allowed), inside the Edge.
        float tilt = Weight * Raw, inward = Weight * psi;
        float a0 = ScreenAngle(b, f.Jx, f.Jy, 1f), aT = ScreenAngle(Turned(b, left, tilt, ahead, inward), f.Jx, f.Jy, 1f);
        float c0 = float.IsNaN(clipPrev) ? a0 : clipPrev, lim = ScreenRate * dt + MathF.Abs(Wrap(a0 - c0)), was = c0 + Shift;
        float aW = was + Math.Clamp(Wrap(aT - was), -lim, lim);
        if (MathF.Abs(a0) <= Edge) aW = Math.Clamp(aW, -Edge, Edge);
        else if (MathF.Abs(aW) > MathF.Abs(a0) && MathF.Sign(aW) == MathF.Sign(a0)) aW = a0;
        if (MathF.Abs(Wrap(aW - aT)) > 0.05f)
            tilt = Solve(b, left, ahead, inward, f.Jx, f.Jy, 1f, aW, MathF.Min(0f, MathF.Min(lo, hi)), MathF.Max(0f, hi), Tilt);
        Tilt += Math.Clamp(tilt - Tilt, -step, step);
        Inward = inward;
        Shift = Wrap(ScreenAngle(Turned(b, left, Tilt, ahead, Inward), f.Jx, f.Jy, 1f) - a0);
        clipPrev = a0;
        ClearCalves(dt, f, b, left, ahead, moving);
    }
}
