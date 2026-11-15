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
    static readonly StringName WorldName = "world_time", WorldWasName = "world_time_was";
    static double time, world, rollover = 3600;

    /// <summary>The world's rate for the world materials' clock (shaders/world_clock.gdshaderinc):
    /// FlareFx.WorldRate in a Flare, 1 outside one; set each frame by the world (WorldScene).
    /// In the stop the world's ground, grass, water and fire truly hold, she and the marks alive.</summary>
    public static double WorldRate = 1;
    static int frame;
    static Node? clockOf;

    /// <summary>Followed from now: called before the game's first frame is drawn.</summary>
    public static void Start(Node node)
    {
        // (a scene loaded afresh, the look viewer's replay: the clock follows the new game's frames; it was left on
        // the freed one and stopped)
        if (clockOf != null && GodotObject.IsInstanceValid(clockOf)) return;
        bool first = clockOf == null;
        clockOf = node;
        if (!first) return;
        rollover = (double)ProjectSettings.GetSetting("rendering/limits/time/time_rollover_secs", 3600.0);
        RenderingServer.FramePreDraw += Draw;
    }

    /// <summary>(the look viewer) Back to the game's start: TIME, the world's clock and the frame count at 0, as the
    /// renderer's TIME is put back to 0 for the same draw (LookViewer, from a frame_pre_draw after this clock's own).</summary>
    public static void Restart()
    {
        time = 0; world = 0; frame = 0; WorldRate = 1;
        RenderingServer.GlobalShaderParameterSet(Then, -1e9f);
        RenderingServer.GlobalShaderParameterSet(WorldWasName, 0f);
        RenderingServer.GlobalShaderParameterSet(WorldName, 0f);
        RenderingServer.GlobalShaderParameterSet(FrameName, 0f);
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
        // The world's clock: last draw's for the look back, then this draw's step at the world's rate.
        RenderingServer.GlobalShaderParameterSet(WorldWasName, (float)world);
        world = (world + step * Mathf.Clamp(WorldRate, 0, 1)) % rollover;
        RenderingServer.GlobalShaderParameterSet(WorldName, (float)world);
        // The frames drawn (wrapping), for what is cut by a threshold moved every frame
        // (shaders/coverage.gdshaderinc).
        frame = (frame + 1) % 256;
        RenderingServer.GlobalShaderParameterSet(FrameName, (float)frame);
    }
}
