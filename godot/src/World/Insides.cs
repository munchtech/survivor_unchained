using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (E9c3) The pieces of a house's inside (OwnWalls.Furnish) that are not the kit's: our own props ("own:bed",
/// "own:log_short"), the hearth (Campfire's stone ring, ash bed, logs and embers, no flame, and a low ember light that
/// lights the cauldron's rim), a wool rug ("rug") and strewn rushes ("straw"), the last two flat cards of
/// shaders/floor_cloth.gdshader sized by their transform's scale (half sizes). HouseFade brings each in with its house's
/// cutaway (their "inside" meta): the rugs and rushes by the shader's own scatter (its "unit"), the rest by their
/// transparency; out of view while the house stands whole.
/// </summary>
public static class Insides
{
    static ShaderMaterial? rug, straw;
    static PlaneMesh? card;

    public static Node3D? Node(string id, Transform3D at)
    {
        if (id.StartsWith("own:"))
        {
            if (OwnProps.Piece(id[4..]) is not Node3D p) return null;
            p.Transform = at;
            // (E9d) inside, as the kit's inside pieces: no shadows
            foreach (var n in p.FindChildren("*", "GeometryInstance3D", true, false)) if (n is GeometryInstance3D g) g.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            return p;
        }
        if (id == "hearth")
        {
            var f = Campfire.Build(Vector3.Zero, 0.78f, true, "coals");
            f.Name = "Hearth";
            f.Transform = at;
            f.AddChild(new OmniLight3D
            {
                Name = "hearth_glow", Position = new Vector3(0, 0.35f, 0), LightColor = new Color(1.0f, 0.55f, 0.25f),
                LightEnergy = 1.4f, OmniRange = 2.6f, OmniAttenuation = 1.6f, ShadowEnabled = false, Visible = false,
            });
            return f;
        }
        if (id is "rug" or "straw")
        {
            card ??= new PlaneMesh { Size = new Vector2(2, 2), SubdivideWidth = 0, SubdivideDepth = 0 };
            var m = id == "rug" ? rug ??= Look(true) : straw ??= Look(false);
            var mi = new MeshInstance3D { Name = id, Mesh = card, MaterialOverride = m, Transform = at, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            mi.SetInstanceShaderParameter("seed", (at.Origin.X * 7.31f + at.Origin.Z * 3.17f) % 97f);
            return mi;
        }
        return null;
    }

    static ShaderMaterial Look(bool isRug)
    {
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/floor_cloth.gdshader") };
        m.SetShaderParameter("rug", isRug);
        return m;
    }
}
