using Godot;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Play;

/// <summary>
/// The game camera (src/render/camera.ts): a steep three-quarter view that
/// follows the survivor.
///   - it leads a little in the direction of travel, so you see more of what
///     you are running into than what you are running from;
///   - it eases to a new distance when the game asks (in close for a
///     conversation: TargetDistance);
///   - shake uses a trauma model (shake = trauma²) with smooth noise, so a big
///     hit is felt and a stream of small ones is not a blur;
///   - FocusOverride lets a cutscene or a boss intro frame something else.
/// </summary>
public sealed class FollowCamera
{
    public readonly Camera3D Camera;
    public float Pitch = Mathf.DegToRad(56);
    public float Yaw;
    public float Distance = 23, TargetDistance = 23;
    public float Lead = 2.2f;
    public float Trauma;
    /// <summary>How much of the shake the player wants (settings: 0..1).</summary>
    public float ShakeScale = 1;
    public Vector3? FocusOverride;
    /// <summary>Metres the view's aim is raised (negative: lowered) for someone not her height: GameNpcShot's swap, a
    /// package NPC in her place, frames the close-up on its own head (0: her own framing).</summary>
    public float AimLift;
    /// <summary>What the view keeps in frame with her (a story night's boss): the look leans a third of the
    /// way toward it, never more than four and a half metres. Followed on her alone, the boss stood under the
    /// HUD's bar at the screen's foot for a fight's length.</summary>
    public Vector3? Toward;
    /// <summary>The share of the way the look leans toward it, and its most metres (a giant boss: the Ford-Warden).</summary>
    public float TowardShare = 0.33f, TowardMax = 4.5f;
    float towardX, towardZ;
    /// <summary>Where the survivor should stand across the screen, in pixels from its middle at
    /// 1080 high (a side panel open: they step aside so they stay in view beside it).</summary>
    public float ScreenShift;
    /// <summary>How near the camera comes while a side panel is open (1: as it was): the panel took
    /// the room her large figure had, so the world frames her nearer instead.</summary>
    public float ScreenNear = 1;
    float near = 1;
    /// <summary>A side panel's own view of her (the book: Pack, Self, Arts): the view comes down from
    /// play's steep angle to this pitch (degrees) and distance (metres), looking at this height on her,
    /// so her face reads beside the panel. From play's own height and distance her face was a few
    /// pixels of the top of her head. Null: play's view (ScreenNear still brings it nearer).</summary>
    public (float Pitch, float Distance, float Height)? ScreenFrame;
    (float Pitch, float Distance, float Height) frame = (56, 23, 0.8f);
    float framed;
    /// <summary>How near the close view is asked to come (CloseUp: 0 play's own distance, 1 her from the hips up),
    /// and how fast it goes there (per second). The pitch comes down as it nears, so it shows her, not the top
    /// of her head: play's view, then her whole figure filling the frame (CloseMid), then CloseNear.</summary>
    public float Close, CloseRate = 4;
    /// <summary>A slow turn of the view around her (radians, the idle view's drift), eased in at CloseRate.</summary>
    public float Orbit;
    /// <summary>How much of the way from where it looks to where it would stand is clear (0..1; the ground's walls
    /// and houses): a near view comes in front of a wall rather than through it. Null: always clear.</summary>
    public System.Func<Vector3, Vector3, float>? Room;
    /// <summary>The ground's height at a point (a near, low view never goes under a rise).</summary>
    public System.Func<float, float, float>? Ground;
    /// <summary>The close view's two framings (pitch in degrees, distance and the height on her it looks at, in
    /// metres): her whole figure filling the frame, and her from the hips up. --close-mid / --close-near P,D,H.
    /// The nearest looks 3 degrees down from about her eye height (the owner, 22 Oct: at 9 degrees it looked down on
    /// her crown and her hair read as a helmet).</summary>
    public static readonly (float Pitch, float Distance, float Height) CloseMid = Frame("close-mid", (15, 4.2f, 1.0f)),
        CloseNear = Frame("close-near", (3, 1.95f, 1.6f));
    float closeNow, orbitNow, room = 1;
    /// <summary>How near the close view is now (eased).</summary>
    public float CloseShown => closeNow;

    static (float, float, float) Frame(string arg, (float, float, float) or)
    {
        if (Args.Get(arg) is not string f || f.Split(',') is not [var p, var d, var h]) return or;
        static float N(string s) => float.Parse(s, System.Globalization.CultureInfo.InvariantCulture);
        return (N(p), N(d), N(h));
    }

    /// <summary>The close view straight to where it is asked (a cinematic takes the camera, a new place).</summary>
    public void SnapClose() { closeNow = Close; orbitNow = Orbit; room = 1; }

    /// <summary>Play's view brought so near (0..1): its pitch (radians), distance and height on her, from play's
    /// own pitch and distance. The distance goes down evenly in proportion (each notch the same step to the eye),
    /// the pitch and height with it through the two framings.</summary>
    /// <summary>The lens at the nearest (vertical degrees; play's is 34): longer, as a portrait's, so her figure is
    /// not drawn wide by a near wide lens. The distance grows with it to keep CloseNear's framing. --close-lens.</summary>
    public static readonly float CloseLens = Args.Has("close-lens") ? Args.Num("close-lens", 24) : 24;

    /// <summary>The lens (vertical degrees) the close view wants at this nearness.</summary>
    public static float Lens(float c, float pitch, float dist)
    {
        var (_, d, _) = Closed(c, pitch, dist);
        float mid = CloseMid.Distance, n = CloseNear.Distance;
        if (d >= mid) return 34;
        float u = Mathf.Clamp((Mathf.Log(mid) - Mathf.Log(d)) / (Mathf.Log(mid) - Mathf.Log(n)), 0, 1);
        return Mathf.Lerp(34, CloseLens, u);
    }

    public static (float Pitch, float Distance, float Height) Closed(float c, float pitch, float dist)
    {
        if (c <= 0) return (pitch, dist, 0.8f);
        var m = CloseMid; var n = CloseNear;
        float far = Mathf.Log(Mathf.Max(dist, m.Distance + 0.01f)), mid = Mathf.Log(m.Distance), nearL = Mathf.Log(n.Distance);
        float lnD = Mathf.Lerp(far, nearL, Mathf.Clamp(c, 0, 1));
        float d = Mathf.Exp(lnD);
        if (lnD >= mid)
        {
            float t = (far - lnD) / (far - mid);
            return (Mathf.Lerp(pitch, Mathf.DegToRad(m.Pitch), t), d, Mathf.Lerp(0.8f, m.Height, t));
        }
        float u = (mid - lnD) / (mid - nearL);
        return (Mathf.DegToRad(Mathf.Lerp(m.Pitch, n.Pitch, u)), d, Mathf.Lerp(m.Height, n.Height, u));
    }

    float overrideBlend, leadX, leadZ, shakeT;
    Vector3 look;
    bool initialised;
    float lastDt;
    static readonly bool CamLog = Args.Has("camlog");
    float logFree = 1;
    /// <summary>(--camlog: a line a frame of the near view's closeness, room, lens and distance) what its room ray last hit.</summary>
    public string? RoomHit;

    public FollowCamera(Camera3D camera) { Camera = camera; }

    /// <summary>Where the camera is looking (for shadows, grass and sound).</summary>
    public Vector3 Focus => look;

    public void AddTrauma(float v) => Trauma = Mathf.Clamp(Trauma + v * ShakeScale, 0, 1);

    /// <summary>The Flare's envelope (Fx/Flare/FlareFx.cs, FLARE_LOOK §1.4): the push in (a share of the distance; below
    /// 0 pulls out) and the pitch (radians added; below 0 lifts the view toward the sky).</summary>
    public float FlarePush, FlarePitch;
    Vector3 joltAxis;
    float joltAmt, joltT = 9;

    /// <summary>One shake along a blow (vertical for a slam, across for a sweep), decaying: the Flare's (trauma 0..1).</summary>
    public void Jolt(Vector3 axis, float amount)
    {
        if (axis.LengthSquared() < 1e-6f || ShakeScale <= 0) return;
        joltAmt = Mathf.Max(joltAmt * Mathf.Exp(-joltT * 7), amount * ShakeScale);
        joltAxis = axis.Normalized();
        joltT = 0;
    }

    Vector3 kick;
    float kickT = 1;

    /// <summary>The view leans toward a blow of hers for a breath (S-17): out over 90 ms, back
    /// over 160 ms, along the ground toward where it landed and a little down into it, so the
    /// weight is hers and it reads which way it went. Not a shake: it never wobbles.</summary>
    public void Kick(Vector3 toward, float metres)
    {
        toward.Y = 0;
        if (toward.LengthSquared() < 1e-4f || ShakeScale <= 0) return;
        kick = (toward.Normalized() + Vector3.Down * 0.35f) * metres * ShakeScale;
        kickT = 0;
    }

    Vector3 Kicked()
    {
        if (kickT >= 0.25f) return Vector3.Zero;
        float k = kickT < 0.09f ? Mathf.SmoothStep(0, 1, kickT / 0.09f) : 1 - Mathf.SmoothStep(0, 1, (kickT - 0.09f) / 0.16f);
        return kick * k;
    }

    /// <summary>Straight to where it settles over someone standing at this
    /// point on the ground (as PoseFor: a cinematic's blend lands on it).</summary>
    public void Snap(float x, float y, float z)
    {
        look = new Vector3(x, y + 0.8f, z);
        Distance = TargetDistance;
        initialised = true;
        Place();
    }

    static float Damp(float a, float b, float lambda, float dt) => (float)MathX.Damp(a, b, lambda, dt);

    /// <summary>Where the camera settles over someone standing still at this
    /// point (no lead, no shake): what a cinematic hands back into.</summary>
    public (Vector3 Pos, Vector3 Look) PoseFor(Vector3 at)
    {
        var l = at + new Vector3(0, 0.8f, 0);
        float cp = Mathf.Cos(Pitch), sp = Mathf.Sin(Pitch);
        return (new Vector3(l.X + Mathf.Sin(Yaw) * cp * TargetDistance, l.Y + sp * TargetDistance, l.Z + Mathf.Cos(Yaw) * cp * TargetDistance), l);
    }

    public void Update(float dt, float x, float y, float z, float vx, float vz)
    {
        if (!initialised) Snap(x, y, z);
        closeNow = Damp(closeNow, Close, CloseRate, dt);
        orbitNow = Damp(orbitNow, Orbit, CloseRate, dt);
        // (near, the lead is the street ahead in a smaller frame: a quarter of it keeps her in view)
        float leadK = 1 - 0.75f * Mathf.Clamp(closeNow / 0.6f, 0, 1);
        leadX = Damp(leadX, vx * Lead * 0.2f * leadK, 3, dt);
        leadZ = Damp(leadZ, vz * Lead * 0.2f * leadK, 3, dt);
        float wx = 0, wz = 0;
        if (Toward is Vector3 tw)
        {
            float dx = tw.X - x, dz = tw.Z - z, dl = Mathf.Sqrt(dx * dx + dz * dz);
            if (dl > 0.01f) { float k = Mathf.Min(dl * TowardShare, TowardMax) / dl; wx = dx * k; wz = dz * k; }
        }
        towardX = Damp(towardX, wx, 1.5f, dt);
        towardZ = Damp(towardZ, wz, 1.5f, dt);
        var t = new Vector3(x + leadX + towardX, y + 0.8f, z + leadZ + towardZ);
        overrideBlend = Damp(overrideBlend, FocusOverride.HasValue ? 1 : 0, 2.5f, dt);
        var f = FocusOverride is Vector3 o ? t.Lerp(o, overrideBlend) : t;
        look = new Vector3(Damp(look.X, f.X, 7, dt), Damp(look.Y, f.Y, 4, dt), Damp(look.Z, f.Z, 7, dt));
        Distance = Damp(Distance, TargetDistance, 1.6f, dt);
        Trauma = Mathf.Max(0, Trauma - dt * 1.4f);
        kickT += dt;
        joltT += dt;
        // The view slides sideways, the angle unchanged: pixels to metres at the survivor's distance.
        near = Damp(near, ScreenNear, 5, dt);
        if (ScreenFrame is { } sf) frame = sf;
        framed = Damp(framed, ScreenFrame != null ? 1 : 0, 3.5f, dt);
        float perPx = 2 * Reach() * Mathf.Tan(Mathf.DegToRad(Camera.Fov) / 2) / 1080;
        Camera.HOffset = Damp(Camera.HOffset, -ScreenShift * perPx, 6, dt);
        shakeT += dt;
        lastDt = dt;
        Place();
    }

    /// <summary>How far the camera stands from where it looks: play's distance, or a panel's framing
    /// eased in (smoothed, so the view glides down to her rather than swinging).</summary>
    float Reach() => Mathf.Lerp(Closed(closeNow, Pitch, Distance * near).Distance * LensStep() * room, frame.Distance, Mathf.SmoothStep(0, 1, framed));

    /// <summary>The distance's stretch for the longer lens (1 at play's own), so the framing holds.</summary>
    float LensStep() => closeNow <= 0.0005f ? 1 : Mathf.Tan(Mathf.DegToRad(17)) / Mathf.Tan(Mathf.DegToRad(Lens(closeNow, Pitch, Distance * near) / 2));

    void Place()
    {
        float k = Mathf.SmoothStep(0, 1, framed);
        var c = Closed(closeNow, Pitch, Distance * near);
        float pitch = Mathf.Lerp(c.Pitch, Mathf.DegToRad(frame.Pitch), k) + FlarePitch;
        float cp = Mathf.Cos(pitch), sp = Mathf.Sin(pitch);
        float yaw = Yaw + orbitNow * (1 - k);
        var aim = look + new Vector3(0, Mathf.Lerp(c.Height, frame.Height, k) - 0.8f + AimLift, 0);
        // A near view comes in front of a wall, never through it (gliding: CameraRoom; a post or a cart is no wall).
        if (closeNow > 0.02f && Room != null)
        {
            float cd = c.Distance * LensStep();
            var want = new Vector3(aim.X + Mathf.Sin(yaw) * cp * cd, aim.Y + sp * cd, aim.Z + Mathf.Cos(yaw) * cp * cd);
            float free = Mathf.Clamp(Room(aim, want), 0, 1);
            logFree = free;
            // (no nearer than a metre and a half: inside that a wall wins and the view stays on her)
            free = Mathf.Max(free, Mathf.Min(1, 1.5f / cd));
            room = SurvivorUnchained.Play.CameraRoom.Step(room, free, lastDt);
        }
        else room = 1;
        float d = Reach() * (1 - FlarePush);
        // (the game puts play's lens back each frame; the close view lengthens it after)
        if (closeNow > 0.0005f) Camera.Fov = Mathf.Lerp(Lens(closeNow, Pitch, Distance * near), Camera.Fov, k);
        var pos = new Vector3(aim.X + Mathf.Sin(yaw) * cp * d, aim.Y + sp * d, aim.Z + Mathf.Cos(yaw) * cp * d);
        if (closeNow > 0.02f && Ground != null) pos.Y = Mathf.Max(pos.Y, Ground(pos.X, pos.Z) + 0.45f);
        float s = Trauma * Trauma, t = shakeT * 22;
        float N(float a) => Mathf.Sin(t + a) * 0.5f + Mathf.Sin(t * 2.3f + a * 1.7f) * 0.3f + Mathf.Sin(t * 4.1f + a * 3.1f) * 0.2f;
        var lean = Kicked();
        // (The Flare's jolt: a damped swing along its blow, about 13 a second.)
        var jolt = joltT < 1.2f ? joltAxis * joltAmt * 0.55f * Mathf.Exp(-joltT * 7) * Mathf.Sin(joltT * Mathf.Tau * 13) : Vector3.Zero;
        var at = pos + lean + jolt + new Vector3(N(1) * s * 0.7f, N(2) * s * 0.5f, N(3) * s * 0.7f);
        var target = new Vector3(aim.X + N(4) * s * 0.25f, aim.Y, aim.Z + N(5) * s * 0.25f) + lean * 1.3f;
        if (CamLog) GD.Print($"CAMLOG t={shakeT:F3} close={closeNow:F3} room={room:F3} free={logFree:F3} hit={RoomHit ?? "-"} fov={Camera.Fov:F2} d={d:F3} pos={at.X:F2},{at.Y:F2},{at.Z:F2} aim={aim.X:F2},{aim.Y:F2},{aim.Z:F2}");
        var basis = Basis.LookingAt(target - at, Vector3.Up);
        Camera.GlobalTransform = new Transform3D(basis.Rotated(basis.Z, N(6) * s * 0.025f), at);
    }
}
