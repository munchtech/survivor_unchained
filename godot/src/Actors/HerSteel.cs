using Godot;

namespace SurvivorUnchained.View;

/// <summary>(demo-look r2 her, 16 Nov; judge 1: "her sword is a 1 px black stick") Her held steel in the den. A metal surface in
/// a dark room reflects the dark, so at the play camera her blade read as a black stick. While the rig's hero_den row asks for
/// it (HeroDen.SteelOn) the piece in her sword hand wears shaders/hero_steel.gdshader in place of each surface's own material:
/// its metal at the row's lit and shade tones by the key, one painted glint across the blade, its grip at its own albedo. A
/// surface override, not the mesh's override, so CelLib's line still goes round it. Off: each surface's own material back.</summary>
public static class HerSteel
{
    const string Tag = "hero_steel", Was = "hero_steel_was";
    static Shader? shader;

    /// <summary>Each frame from PlayerView: the meshes under her hand's mount (null: nothing held) wear the den's steel while
    /// on, their own again when not. Only a change touches a material.</summary>
    public static void Wear(Node? mount, bool on)
    {
        if (mount == null) return;
        foreach (var c in mount.GetChildren())
        {
            if (c is MeshInstance3D { Mesh: { } mesh } mi && mi.MaterialOverride == null)
                for (int s = 0; s < mesh.GetSurfaceCount(); s++)
                {
                    var cur = mi.GetSurfaceOverrideMaterial(s);
                    bool mine = cur is ShaderMaterial { ResourceName: Tag };
                    if (on == mine) continue;
                    if (on)
                    {
                        if (mesh.SurfaceGetMaterial(s) is not BaseMaterial3D own) continue;
                        var m = Make(own, mesh.GetAabb());
                        if (cur != null) m.SetMeta(Was, cur);
                        mi.SetSurfaceOverrideMaterial(s, m);
                    }
                    else mi.SetSurfaceOverrideMaterial(s, cur!.HasMeta(Was) ? cur.GetMeta(Was).AsGodotObject() as Material : null);
                }
            Wear(c, on);
        }
    }

    static ShaderMaterial Make(BaseMaterial3D own, Aabb box)
    {
        shader ??= GD.Load<Shader>("res://shaders/hero_steel.gdshader");
        var m = new ShaderMaterial { Shader = shader, ResourceName = Tag };
        if (own.AlbedoTexture != null) m.SetShaderParameter("albedo_tex", own.AlbedoTexture);
        m.SetShaderParameter("albedo", own.AlbedoColor);
        if (own.MetallicTexture != null) m.SetShaderParameter("metal_tex", own.MetallicTexture);
        m.SetShaderParameter("metal_channel", own.MetallicTextureChannel switch
        {
            BaseMaterial3D.TextureChannel.Red => new Vector4(1, 0, 0, 0),
            BaseMaterial3D.TextureChannel.Green => new Vector4(0, 1, 0, 0),
            BaseMaterial3D.TextureChannel.Alpha => new Vector4(0, 0, 0, 1),
            BaseMaterial3D.TextureChannel.Grayscale => new Vector4(1, 1, 1, 0) / 3f,
            _ => new Vector4(0, 0, 1, 0),
        });
        m.SetShaderParameter("metallic", own.Metallic);
        // (the long axis: the box's longest side through its middle, from its low end to its high end)
        var size = box.Size; int ax = size.X >= size.Y && size.X >= size.Z ? 0 : size.Y >= size.Z ? 1 : 2;
        Vector3 lo = box.GetCenter(), hi = lo;
        lo[ax] = box.Position[ax]; hi[ax] = box.End[ax];
        m.SetShaderParameter("axis_lo", lo);
        m.SetShaderParameter("axis_hi", hi);
        return m;
    }
}
