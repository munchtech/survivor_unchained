using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The renderer's clock, followed for the shaders: the frames drawn (for cut-outs moved
/// every frame, shaders/coverage.gdshaderinc), and which of a material's two runs of its
/// vertex stage is drawing: this frame's, or the motion vectors' look back at last frame. To know how each point moved (for
/// the temporal smoothing, TAA or FSR 2), Godot runs a vertex stage again with last
/// frame's TIME, transform and skinning (scene_forward_clustered.glsl), but with
/// this frame's uniforms. So a shape that code moves each frame (her hair's swing,
/// HairSway) gives its last frame's values beside this frame's, and the stage picks
/// by its TIME: the look back runs at this frame's TIME less the frame's step
/// (render_scene_data_rd.cpp), and `motion_then` (shaders/motion.gdshaderinc) is
/// set between the two.
///
/// TIME is the renderer's own clock: each draw adds the frame's (scaled) step and
/// wraps at the rollover (renderer_compositor_rd.cpp). It is followed here draw by
/// draw (RenderingServer's frame_pre_draw comes once before each, with the step the
/// draw adds), so a frame not drawn (a window minimised) is not counted. (A draw
/// forced from code, RenderingServer.ForceDraw, adds its own step and would put it
/// out: the game never forces one.)
/// Wrong by a frame, a swing would only lose its motion vectors (as before) or be
/// drawn a frame late; neither shows.
/// </summary>
public static class MotionClock
{
    static readonly StringName Then = "motion_then", FrameName = "motion_frame";
    static double time, rollover = 3600;
    static int frame;
    static Node? clockOf;

    /// <summary>Followed from now: called before the game's first frame is drawn.</summary>
    public static void Start(Node node)
    {
        if (clockOf != null) return;
        clockOf = node;
        rollover = (double)ProjectSettings.GetSetting("rendering/limits/time/time_rollover_secs", 3600.0);
        RenderingServer.FramePreDraw += Draw;
    }

    static void Draw()
    {
        if (clockOf == null || !GodotObject.IsInstanceValid(clockOf)) return;
        // The step this draw adds to TIME: the frame's process step, scaled (main.cpp).
        double step = clockOf.GetProcessDeltaTime();
        time = (time + step) % rollover;
        // Halfway back to the look back's TIME; with no step there is no telling them apart
        // (and nothing moved), so every run is this frame's.
        RenderingServer.GlobalShaderParameterSet(Then, step > 0 ? (float)(time - step * 0.5) : -1e9f);
        // The frames drawn (wrapping), for what is cut by a threshold moved every frame
        // (shaders/coverage.gdshaderinc).
        frame = (frame + 1) % 256;
        RenderingServer.GlobalShaderParameterSet(FrameName, (float)frame);
    }
}
