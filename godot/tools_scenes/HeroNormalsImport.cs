#if TOOLS
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Tools;

/// <summary>(L1 lead 25, CACHE) The import step for her kit (heroine.glb, her outfits, armor, weapons: import_script/path in
/// their .import): every mesh's smooth shading normals baked into the imported mesh (CUSTOM0, the runtime's exact bake,
/// HeroNormals.BakeMesh) with the key as meta ("hash params"), so her spawn reads no arrays back and uploads no copy.
/// The radius is every rigs.json hero_pool value 60 (the first non-zero one). A re-import rebuilds it; the image
/// mipmaps step (import_mipmaps.gd) runs first, as before.</summary>
[Tool]
public partial class HeroNormalsImport : EditorScenePostImport
{
    public override GodotObject _PostImport(Node scene)
    {
        if (GD.Load<GDScript>("res://tools_scenes/import_mipmaps.gd")?.New().AsGodotObject() is { } mip) mip.Call("_post_import", scene);
        float r = 0f;
        var set = SurvivorUnchained.Look.RigSet.Parse(FileAccess.GetFileAsString("res://data/look/rigs.json"));
        foreach (var rig in set.Rigs.Values) { var hs = SurvivorUnchained.Look.Rigs.HeroSmooth(rig.HeroPool); if (hs[1] > 0) { r = (float)hs[1]; break; } }
        if (r <= 0f) { GD.Print("hero normals import: no radius in rigs.json, nothing baked"); return scene; }
        var done = new Dictionary<ulong, ArrayMesh?>(); int nm = 0, nv = 0; var sw = System.Diagnostics.Stopwatch.StartNew();
        void Walk(Node n)
        {
            if (n is MeshInstance3D { Mesh: ArrayMesh am } mi)
            {
                if (!done.TryGetValue(am.GetInstanceId(), out var copy)) { copy = SurvivorUnchained.View.HeroNormals.BakeMesh(am, r, out int v); done[am.GetInstanceId()] = copy; if (copy != null) { nm++; nv += v; } }
                if (copy != null) mi.Mesh = copy;
            }
            foreach (var c in n.GetChildren()) Walk(c);
        }
        Walk(scene);
        GD.Print($"hero normals import: {nm} meshes, {nv} verts baked at radius {r:0.###} m in {sw.ElapsedMilliseconds} ms ({SurvivorUnchained.View.HeroNormals.Params(r)})");
        return scene;
    }
}
#endif
