using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// --her-draws: her share of the frame's draw calls (armor.md's play-draw budget). From 4 s it averages the viewport's
/// draws over 30 frames with her shown, then 30 with her skeleton hidden, prints the difference and what of hers is
/// visible (meshes and surfaces drawn, and those casting shadows), and shows her again. Not for pictures.
/// </summary>
public partial class HerDraws : Node
{
    Skeleton3D skel = null!;
    int frame;
    double t, a, ash, b, bsh;
    string seen = "";

    public static void Watch(People.Person p)
    {
        if (!Args.Has("her-draws") || p.Skeleton.GetNodeOrNull("HerDraws") != null) return;
        p.Skeleton.AddChild(new HerDraws { Name = "HerDraws", skel = p.Skeleton });
    }

    public override void _Process(double delta)
    {
        t += delta;
        if (t < 4 || frame > 62) return;
        var vp = GetViewport().GetViewportRid();
        double d = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Visible, RenderingServer.ViewportRenderInfo.DrawCallsInFrame);
        double sh = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Shadow, RenderingServer.ViewportRenderInfo.DrawCallsInFrame);
        // (the info is the last drawn frame's: skip the frame after each switch)
        if (frame >= 1 && frame <= 30) { a += d; ash += sh; }
        if (frame >= 33 && frame <= 62) { b += d; bsh += sh; }
        if (frame == 30)
        {
            var list = new System.Collections.Generic.List<string>();
            int meshes = 0, surf = 0, cast = 0, shadowOnly = 0;
            foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>().Where(m => m.Visible && m.Mesh != null))
            {
                int n = mi.Mesh.GetSurfaceCount();
                if (mi.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly) { shadowOnly += n; continue; }
                meshes++;
                list.Add($"{mi.Name}[{string.Join(",", Enumerable.Range(0, n).Select(i => (mi.GetSurfaceOverrideMaterial(i) ?? mi.Mesh.SurfaceGetMaterial(i))?.ResourceName is { Length: > 0 } r ? r : mi.Mesh.SurfaceGetMaterial(i)?.ResourceName ?? "-"))}]{(mi.CastShadow == GeometryInstance3D.ShadowCastingSetting.Off ? "" : "*")}");
                for (int s = 0; s < n; s++)
                {
                    // (a material's next passes draw again: fur shells)
                    var m = mi.MaterialOverride ?? mi.GetSurfaceOverrideMaterial(s) ?? mi.Mesh.SurfaceGetMaterial(s);
                    for (; m != null; m = m.NextPass) surf++;
                    if (mi.MaterialOverlay != null) surf++;
                }
                if (mi.CastShadow != GeometryInstance3D.ShadowCastingSetting.Off) cast += n;
            }
            seen = $"{meshes} meshes, {surf} surface passes, {cast} casting surfaces, {shadowOnly} shadow-only surfaces: " + string.Join(" ", list);
            skel.Visible = false;
        }
        if (frame == 62)
        {
            skel.Visible = true;
            GD.Print($"her draws: {(a - b) / 30:0.0} visible + {(ash - bsh) / 30:0.0} shadow (frame {a / 30:0} + {ash / 30:0}sh without her {b / 30:0} + {bsh / 30:0}sh); {seen}");
        }
        frame++;
    }
}
