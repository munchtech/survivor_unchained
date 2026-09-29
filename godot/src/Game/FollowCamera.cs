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
    float overrideBlend, leadX, leadZ, shakeT;
    Vector3 look;
    bool initialised;

    public FollowCamera(Camera3D camera) { Camera = camera; }

    /// <summary>Where the camera is looking (for shadows, grass and sound).</summary>
    public Vector3 Focus => look;

    public void AddTrauma(float v) => Trauma = Mathf.Clamp(Trauma + v * ShakeScale, 0, 1);

    public void Snap(float x, float y, float z)
    {
        look = new Vector3(x, y, z);
        Distance = TargetDistance;
        initialised = true;
        Place();
    }

    static float Damp(float a, float b, float lambda, float dt) => (float)MathX.Damp(a, b, lambda, dt);

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
        shakeT += dt;
        Place();
    }

    void Place()
    {
        float cp = Mathf.Cos(Pitch), sp = Mathf.Sin(Pitch);
        var pos = new Vector3(look.X + Mathf.Sin(Yaw) * cp * Distance, look.Y + sp * Distance, look.Z + Mathf.Cos(Yaw) * cp * Distance);
        float s = Trauma * Trauma, t = shakeT * 22;
        float N(float a) => Mathf.Sin(t + a) * 0.5f + Mathf.Sin(t * 2.3f + a * 1.7f) * 0.3f + Mathf.Sin(t * 4.1f + a * 3.1f) * 0.2f;
        var at = pos + new Vector3(N(1) * s * 0.7f, N(2) * s * 0.5f, N(3) * s * 0.7f);
        var target = new Vector3(look.X + N(4) * s * 0.25f, look.Y, look.Z + N(5) * s * 0.25f);
        var basis = Basis.LookingAt(target - at, Vector3.Up);
        Camera.GlobalTransform = new Transform3D(basis.Rotated(basis.Z, N(6) * s * 0.025f), at);
    }
}
