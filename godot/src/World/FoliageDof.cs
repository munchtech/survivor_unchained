using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Our own trees under the depth of field (foliage-dof, 13 Nov: "foliage shows hard triangles under the depth of field").
/// The spruce's and the alder's branch sprays are solid painted cards (their atlases carry no alpha): in focus they read
/// as painted clumps, but Godot's blur (a few pixels across) only rounds their straight edges, so a blurred crown read
/// as flat triangles. Each frame this hands the current camera's depth of field to kit.gdshader (OWN_FOLIAGE) as two
/// global uniforms, and there a needle fragment as far out of focus as the blur makes it is broken into clumps
/// (world-anchored lumps eaten away, a little mottle, no ink line), which the blur then melts into soft foliage.
/// In focus (no depth of field, the play camera, or nearer than the blur's start) nothing changes.
///   dof_far  = (far start m, far transition m, lump size m, strength; 0 = off)
///   dof_near = (near distance m, near transition m, lump size m, strength; 0 = off)
/// --fol-dof K: the strength (1 by default; 0 turns it off, for A|B pictures).
/// </summary>
public static class FoliageDof
{
    static bool hooked;
    static readonly StringName Far = "dof_far", Near = "dof_near";
    static Vector4 farWas = new(-1, 0, 0, 0), nearWas = new(-1, 0, 0, 0);
    /// <summary>The breakup's strength (--fol-dof K).</summary>
    public static readonly float Strength = SurvivorUnchained.Args.Has("fol-dof") ? SurvivorUnchained.Args.Num("fol-dof", 1f) : 1f;
    /// <summary>The lump, in blur widths: about two of Godot's blur radii, so the blur melts its edge but not its shape.</summary>
    const float Lump = 4f;

    /// <summary>Starts the per-frame hand-over once (KitLook calls it when it makes our trees' material).</summary>
    public static void Ensure()
    {
        if (hooked) return;
        hooked = true;
        RenderingServer.FramePreDraw += Frame;
    }

    static void Frame()
    {
        var cam = (Engine.GetMainLoop() as SceneTree)?.Root?.GetCamera3D();
        Vector4 far = Vector4.Zero, near = Vector4.Zero;
        if (Strength > 0 && cam?.Attributes is CameraAttributesPractical a && (a.DofBlurFarEnabled || a.DofBlurNearEnabled) && a.DofBlurAmount > 0)
        {
            // (Godot's bokeh: its size in pixels at 1080p is about the amount x 64; the lump is sized so it spans
            // about Lump of those at the depth where the blur is whole, and stays that size in the world beyond)
            float px = a.DofBlurAmount * 64f;
            float k = Mathf.Tan(Mathf.DegToRad(cam.Fov) * 0.5f) / 540f;   // metres per 1080p pixel per metre of depth
            if (a.DofBlurFarEnabled)
            {
                float t = Mathf.Max(a.DofBlurFarTransition, 0.001f);
                float lump = Mathf.Clamp(px * Lump * (a.DofBlurFarDistance + t) * k, 0.06f, 1.5f);
                far = new Vector4(a.DofBlurFarDistance, t, lump, Strength);
            }
            if (a.DofBlurNearEnabled)
            {
                float t = Mathf.Max(a.DofBlurNearTransition, 0.001f);
                float lump = Mathf.Clamp(px * Lump * Mathf.Max(a.DofBlurNearDistance - t, 0.05f) * k, 0.01f, 1.5f);
                near = new Vector4(a.DofBlurNearDistance, t, lump, Strength);
            }
        }
        if (far != farWas) { RenderingServer.GlobalShaderParameterSet(Far, far); farWas = far; }
        if (near != nearWas) { RenderingServer.GlobalShaderParameterSet(Near, near); nearWas = near; }
    }
}
