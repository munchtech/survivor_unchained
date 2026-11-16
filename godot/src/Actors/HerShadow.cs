using Godot;

namespace SurvivorUnchained.View;

/// <summary>(demo-look r2 her, 16 Nov) Her cast shadow in the den (shaders/hero_cast.gdshader; its shape and tone are the rig's
/// hero_den row, View/HeroDen.cs): one ground quad, world-placed at her feet every frame, shown only while the row is on.</summary>
public partial class HerShadow : MeshInstance3D
{
    readonly ShaderMaterial mat = new() { Shader = GD.Load<Shader>("res://shaders/hero_cast.gdshader") };

    public HerShadow()
    {
        Name = "HerShadow"; Mesh = new PlaneMesh { Size = Vector2.One }; MaterialOverride = mat; TopLevel = true; Layers = 2;
        CastShadow = ShadowCastingSetting.Off; Visible = false;
    }

    /// <summary>Her feet (world) this frame; shown is false while she is hidden.</summary>
    public void Place(Vector3 feet, bool shown)
    {
        Visible = shown && HeroDen.CastOn;
        if (!Visible) return;
        float s = 2f * (3f + 0.2f);   // (covers the longest trail the row is likely to ask; the shader discards the rest)
        GlobalTransform = new Transform3D(Basis.Identity.Scaled(new Vector3(s, 1, s)), feet + new Vector3(0, 0.03f, 0));
        mat.SetShaderParameter("dir", HeroDen.CastDir);
    }
}
