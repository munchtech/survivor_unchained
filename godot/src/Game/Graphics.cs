using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>
/// The picture's quality (Settings.Quality) and its resolution
/// (Settings.Scale), applied to the renderer, the air and the place on show.
/// High is the game as it was made, and the default; each step down gives up
/// what costs most for what it shows from the game's camera (each measured:
/// docs/PERF_AUDIT.md, "The graphics settings"). A step gives up the world,
/// never the heroine's own detail (the owner's rule): her meshes have no
/// LODs, her textures keep every mip, her skin its scattering. (FXAA is off
/// at every step: TAA and MSAA already smooth the edges, and it only blurred
/// her and the world a second time.) The resolution's steps draw
/// the world at fewer pixels and let FSR 2.2 bring it back up to the screen
/// (its own temporal smoothing in place of TAA and MSAA); the interface is
/// always drawn at the screen's own.
/// </summary>
public static class Graphics
{
    /// <summary>One step of quality: what each part of the picture is drawn with.</summary>
    public sealed record Tier(
        bool Ssao, RenderingServer.EnvironmentSsaoQuality SsaoQuality, bool VolumetricFog,
        int SunShadowSize, RenderingServer.ShadowQuality SunFilter, bool SunFourSplits, float SunSplit,
        bool LampShadows, RenderingServer.ShadowQuality LampFilter,
        Viewport.Msaa Msaa, RenderingServer.SubSurfaceScatteringQuality Skin,
        float GrassCell, float Effects, bool CrowdShadows, int Corpses, float LodThreshold);

    /// <summary>The game as made (the project's own settings: soft shadows at
    /// medium, positional at low, SSAO at medium, skin at low, MSAA 4x: the
    /// project's msaa_3d=2 is 4x in Godot's count, not 2x).</summary>
    public static readonly Tier High = new(
        true, RenderingServer.EnvironmentSsaoQuality.Medium, true,
        4096, RenderingServer.ShadowQuality.SoftMedium, true, 0.1f,
        true, RenderingServer.ShadowQuality.SoftLow,
        Viewport.Msaa.Msaa4X, RenderingServer.SubSurfaceScatteringQuality.Low,
        0.3f, 1f, true, 160, 1f);

    public static readonly Tier Medium = High with
    {
        SsaoQuality = RenderingServer.EnvironmentSsaoQuality.Low, VolumetricFog = false,
        SunFilter = RenderingServer.ShadowQuality.SoftLow, LampFilter = RenderingServer.ShadowQuality.SoftVeryLow,
        Msaa = Viewport.Msaa.Disabled, GrassCell = 0.36f, Effects = 0.75f, Corpses = 110, LodThreshold = 1.5f,
    };

    public static readonly Tier Low = Medium with
    {
        // Two cascades, not four, with the first reaching 35 m (half the 70 m the
        // sun's shadows reach): she stands 12.5 to 31 m from the camera at every
        // zoom short of the farthest, so she stays in a cascade as fine as High's
        // (the atlas kept at 4096) and only the world beyond goes coarser. With
        // the split at 7 m and a 2048 atlas she sat in a 7-70 m cascade, her own
        // shadows four times coarser.
        Ssao = false, SunFilter = RenderingServer.ShadowQuality.SoftVeryLow, SunFourSplits = false, SunSplit = 0.5f,
        // (Skin keeps its scattering: it is her own, and costs only the pixels she covers.)
        LampShadows = false,
        GrassCell = 0.45f, Effects = 0.5f, CrowdShadows = false, Corpses = 60, LodThreshold = 2.5f,
    };

    public static Tier Of(string quality) => quality switch { "low" => Low, "medium" => Medium, _ => High };

    /// <summary>The resolution's steps: the share of the screen's width the world is drawn at.</summary>
    public static float ScaleOf(string scale) => scale switch
    {
        "quality" => 1 / 1.5f, "balanced" => 1 / 1.7f, "performance" => 0.5f, _ => 1f,
    };

    /// <summary>What the quality and resolution say, applied now (cheap when nothing changed).</summary>
    public static void Apply(Settings s, Atmosphere air, Viewport vp, WorldScene? scene)
    {
        var t = Of(s.Quality);
        Current = t;
        var env = air.Env;
        env.SsaoEnabled = t.Ssao;
        RenderingServer.EnvironmentSetSsaoQuality(t.SsaoQuality, true, 0.5f, 2, 50, 300);
        env.VolumetricFogEnabled = t.VolumetricFog;
        RenderingServer.DirectionalShadowAtlasSetSize(t.SunShadowSize, true);
        RenderingServer.DirectionalSoftShadowFilterSetQuality(t.SunFilter);
        RenderingServer.PositionalSoftShadowFilterSetQuality(t.LampFilter);
        air.Key.DirectionalShadowMode = t.SunFourSplits ? DirectionalLight3D.ShadowMode.Parallel4Splits : DirectionalLight3D.ShadowMode.Parallel2Splits;
        air.Key.DirectionalShadowSplit1 = t.SunSplit;
        RenderingServer.SubSurfaceScatteringSetQuality(t.Skin);
        vp.MeshLodThreshold = t.LodThreshold;

        // The resolution: FSR 2.2 below the screen's own, which brings its own
        // temporal smoothing (TAA and MSAA would only blur it twice).
        float scale = ScaleOf(s.Scale);
        bool fsr = scale < 0.999f;
        vp.Scaling3DMode = fsr ? Viewport.Scaling3DModeEnum.Fsr2 : Viewport.Scaling3DModeEnum.Bilinear;
        vp.Scaling3DScale = scale;
        vp.UseTaa = !fsr;
        vp.Msaa3D = fsr ? Viewport.Msaa.Disabled : t.Msaa;

        Sparks.Density = t.Effects;
        if (scene == null) return;
        scene.View.LampShadows(t.LampShadows);
        scene.View.GrassCell(t.GrassCell);
        scene.Crowd.Shadows = t.CrowdShadows;
        scene.Crowd.CorpseMax = t.Corpses;
    }

    /// <summary>The quality in force (for what is built later: a lamp lit in play).</summary>
    public static Tier Current { get; private set; } = High;
}
