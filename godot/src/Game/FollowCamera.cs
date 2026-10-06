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
    /// <summary>What the view keeps in frame with her (a story night's boss): the look leans a third of the
    /// way toward it, never more than four and a half metres. Followed on her alone, the boss stood under the
    /// HUD's bar at the screen's foot for a fight's length.</summary>
    public Vector3? Toward;
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
    float overrideBlend, leadX, leadZ, shakeT;
    Vector3 look;
    bool initialised;

    public FollowCamera(Camera3D camera) { Camera = camera; }

    /// <summary>Where the camera is looking (for shadows, grass and sound).</summary>
    public Vector3 Focus => look;

    public void AddTrauma(float v) => Trauma = Mathf.Clamp(Trauma + v * ShakeScale, 0, 1);

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
        leadX = Damp(leadX, vx * Lead * 0.2f, 3, dt);
        leadZ = Damp(leadZ, vz * Lead * 0.2f, 3, dt);
        float wx = 0, wz = 0;
        if (Toward is Vector3 tw)
        {
            float dx = tw.X - x, dz = tw.Z - z, dl = Mathf.Sqrt(dx * dx + dz * dz);
            if (dl > 0.01f) { float k = Mathf.Min(dl * 0.33f, 4.5f) / dl; wx = dx * k; wz = dz * k; }
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
        // The view slides sideways, the angle unchanged: pixels to metres at the survivor's distance.
        near = Damp(near, ScreenNear, 5, dt);
        if (ScreenFrame is { } sf) frame = sf;
        framed = Damp(framed, ScreenFrame != null ? 1 : 0, 3.5f, dt);
        float perPx = 2 * Reach() * Mathf.Tan(Mathf.DegToRad(Camera.Fov) / 2) / 1080;
        Camera.HOffset = Damp(Camera.HOffset, -ScreenShift * perPx, 6, dt);
        shakeT += dt;
        Place();
    }

    /// <summary>How far the camera stands from where it looks: play's distance, or a panel's framing
    /// eased in (smoothed, so the view glides down to her rather than swinging).</summary>
    float Reach() => Mathf.Lerp(Distance * near, frame.Distance, Mathf.SmoothStep(0, 1, framed));

    void Place()
    {
        float k = Mathf.SmoothStep(0, 1, framed);
        float pitch = Mathf.Lerp(Pitch, Mathf.DegToRad(frame.Pitch), k);
        float cp = Mathf.Cos(pitch), sp = Mathf.Sin(pitch);
        float d = Reach();
        var aim = look + new Vector3(0, (frame.Height - 0.8f) * k, 0);
        var pos = new Vector3(aim.X + Mathf.Sin(Yaw) * cp * d, aim.Y + sp * d, aim.Z + Mathf.Cos(Yaw) * cp * d);
        float s = Trauma * Trauma, t = shakeT * 22;
        float N(float a) => Mathf.Sin(t + a) * 0.5f + Mathf.Sin(t * 2.3f + a * 1.7f) * 0.3f + Mathf.Sin(t * 4.1f + a * 3.1f) * 0.2f;
        var lean = Kicked();
        var at = pos + lean + new Vector3(N(1) * s * 0.7f, N(2) * s * 0.5f, N(3) * s * 0.7f);
        var target = new Vector3(aim.X + N(4) * s * 0.25f, aim.Y, aim.Z + N(5) * s * 0.25f) + lean * 1.3f;
        var basis = Basis.LookingAt(target - at, Vector3.Up);
        Camera.GlobalTransform = new Transform3D(basis.Rotated(basis.Z, N(6) * s * 0.025f), at);
    }
}
