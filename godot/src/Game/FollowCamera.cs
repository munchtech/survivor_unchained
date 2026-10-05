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
    /// <summary>Where the survivor should stand across the screen, in pixels from its middle at
    /// 1080 high (a side panel open: they step aside so they stay in view beside it).</summary>
    public float ScreenShift;
    /// <summary>How near the camera comes while a side panel is open (1: as it was): the panel took
    /// the room her large figure had, so the world frames her nearer instead.</summary>
    public float ScreenNear = 1;
    float near = 1;
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

    public void Snap(float x, float y, float z)
    {
        look = new Vector3(x, y, z);
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
        var t = new Vector3(x + leadX, y + 0.8f, z + leadZ);
        overrideBlend = Damp(overrideBlend, FocusOverride.HasValue ? 1 : 0, 2.5f, dt);
        var f = FocusOverride is Vector3 o ? t.Lerp(o, overrideBlend) : t;
        look = new Vector3(Damp(look.X, f.X, 7, dt), Damp(look.Y, f.Y, 4, dt), Damp(look.Z, f.Z, 7, dt));
        Distance = Damp(Distance, TargetDistance, 1.6f, dt);
        Trauma = Mathf.Max(0, Trauma - dt * 1.4f);
        kickT += dt;
        // The view slides sideways, the angle unchanged: pixels to metres at the survivor's distance.
        near = Damp(near, ScreenNear, 5, dt);
        float perPx = 2 * Distance * near * Mathf.Tan(Mathf.DegToRad(Camera.Fov) / 2) / 1080;
        Camera.HOffset = Damp(Camera.HOffset, -ScreenShift * perPx, 6, dt);
        shakeT += dt;
        Place();
    }

    void Place()
    {
        float cp = Mathf.Cos(Pitch), sp = Mathf.Sin(Pitch);
        float d = Distance * near;
        var pos = new Vector3(look.X + Mathf.Sin(Yaw) * cp * d, look.Y + sp * d, look.Z + Mathf.Cos(Yaw) * cp * d);
        float s = Trauma * Trauma, t = shakeT * 22;
        float N(float a) => Mathf.Sin(t + a) * 0.5f + Mathf.Sin(t * 2.3f + a * 1.7f) * 0.3f + Mathf.Sin(t * 4.1f + a * 3.1f) * 0.2f;
        var lean = Kicked();
        var at = pos + lean + new Vector3(N(1) * s * 0.7f, N(2) * s * 0.5f, N(3) * s * 0.7f);
        var target = new Vector3(look.X + N(4) * s * 0.25f, look.Y, look.Z + N(5) * s * 0.25f) + lean * 1.3f;
        var basis = Basis.LookingAt(target - at, Vector3.Up);
        Camera.GlobalTransform = new Transform3D(basis.Rotated(basis.Z, N(6) * s * 0.025f), at);
    }
}
