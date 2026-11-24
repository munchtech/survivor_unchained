using Godot;

namespace SurvivorUnchained;

/// <summary>--keep-pipelines (dev, the tester lane's pipeline A/B, 24 Nov: the owner asked whether the den loop's native RAM
/// steps come from the ~258 mesh pipelines compiled again at each den load). What compiles them (read in Godot 4.7.2's source,
/// measured on the den loop): a mesh RESOURCE loaded from disk (ArrayMesh._set_surfaces -> RenderingServer
/// mesh_create_from_surfaces -> mesh_generate_pipelines, counted as PIPELINE_SOURCE_MESH) compiles the ubershader pipelines of
/// its surfaces' own materials, unless that material's shader already holds them (PipelineHashMapRD, one per shader; dropped
/// when the shader is freed, and a built-in material's shader is freed with the last material of its kind). FxWarm's library
/// (res://data/fx_warm/warm.scn, 349 stand-ins) is loaded again from disk at every place's warm-up once the GC has taken the
/// last one: the 215 stand-ins not tagged for the den are never warmed, so their materials are never held (FxWarm.Hold), and
/// each load compiles their pipelines anew, which are freed with the library a few seconds later. In the control every den
/// load's 258 mesh pipelines fall inside the warm-up's window (its line: mesh 258, everything already warmed, 0 drawn).
/// This holds the library's PackedScene for the session once it is cached (its stand-ins' tiny meshes, 4x4 textures,
/// materials, shaders, and the pipelines compiled for them at the first load); the warm-up's GD.Load then finds it cached
/// and instantiates it without making a mesh. A test, not the fix: a fixed hold, it does not grow.</summary>
public partial class PipeKeep : Node
{
    static PackedScene? library;
    public PipeKeep() { ProcessMode = ProcessModeEnum.Always; Name = "PipeKeep"; }

    public override void _Process(double delta)
    {
        if (library != null) { SetProcess(false); return; }
        if (!ResourceLoader.HasCached(Fx.FxWarm.Library)) return;
        library = ResourceLoader.Load<PackedScene>(Fx.FxWarm.Library, "", ResourceLoader.CacheMode.Reuse);
        var k = Perf.PipesKinds();
        GD.Print($"pipe keep: the fx warm library held from {Time.GetTicksMsec() / 1000.0:0.0} s (frame {Engine.GetFramesDrawn()}), {library?.GetState().GetNodeCount() ?? 0} nodes; pipelines so far c/m/s/d/sp {string.Join("/", System.Array.ConvertAll(k, v => (int)v))}");
        SetProcess(false);
    }
}
