using Godot;

namespace SurvivorUnchained.View;

/// <summary>(L1 lead 19, SH2) The fire's shadow of a body that is not one of the crowd (shaders/crowd_blob_cast.gdshader:
/// one shader and one rule for all three users; the crowd's quads are Actors/Vat.cs's blobs). A MultiMesh of flat quads,
/// one per body: the instance's origin is the feet, its color r the body's height m, g its width at the feet m, b zero
/// (the trail's length is the rule's: where the top of the body's shadow falls from her light) or a fixed length m (the
/// light's own bearer: PlayerView), a how much it shows. The shader places and shapes the trail itself, every frame, from
/// her light's foot: a standing piece's quad is set once. One draw call per MultiMesh.</summary>
public static class FireCast
{
    static Mesh? mesh;
    static ShaderMaterial? mat;
    /// <summary>A hand over the ground, as the crowd's blobs are.</summary>
    const float Lift = 0.06f;

    /// <summary>(the frame's cost, on request) --cast-count: every two seconds, how many cast quads stand inside the
    /// fire's reach (the others are drawn as nothing: the shader leaves their four corners on the feet).</summary>
    public static readonly bool Count = SurvivorUnchained.Args.Has("cast-count");
    static Vector3 foot;
    static float reach;
    static int crowd, crowdAll, crowdMeshes, frames;
    static readonly System.Collections.Generic.List<Vector3> stands = new();

    /// <summary>A crowd's blobs this frame (Vat.cs: transform 12, color 4; alpha how much it shows).</summary>
    public static void Tally(float[] buf, int n, int stride)
    {
        if (n > 0) crowdMeshes++;
        for (int i = 0; i < n; i++)
        {
            int q = i * stride;
            if (buf[q + 15] <= 0) continue;
            crowdAll++;
            float dx = buf[q + 3] - foot.X, dz = buf[q + 11] - foot.Z;
            if (dx * dx + dz * dz < reach * reach) crowd++;
        }
    }

    /// <summary>Her place this frame; the count goes to the log every 120 frames.</summary>
    public static void Report(Vector3 her)
    {
        if (++frames % 120 == 0)
        {
            int near = 0;
            foreach (var s in stands) if (new Vector2(s.X - foot.X, s.Z - foot.Z).Length() < reach) near++;
            GD.Print($"fire casts drawn: crowd {crowd} of {crowdAll} (in {crowdMeshes} MultiMeshes, the blobs' second pass), standing {near} of {stands.Count} (one MultiMesh), her 1 (one MultiMesh); reach {reach:0.0} m");
        }
        crowd = crowdAll = crowdMeshes = 0;
        foot = her;
        reach = RenderingServer.GlobalShaderParameterGet("cel_floor_band").AsVector4().X;
    }

    /// <summary>A MultiMesh of n cast quads, none showing until Set.</summary>
    public static MultiMeshInstance3D Make(string name, int n)
    {
        mesh ??= new PlaneMesh { Size = Vector2.One };
        mat ??= new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/crowd_blob_cast.gdshader") };
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, InstanceCount = n, Mesh = mesh };
        for (int i = 0; i < n; i++) mm.SetInstanceColor(i, new Color(0, 0, 0, 0));
        return new MultiMeshInstance3D
        {
            // (on the crowd's blobs' layer, out of the ground decals' cull mask; never culled as a whole: the shader moves the quad)
            Name = name, Multimesh = mm, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, TopLevel = true, Layers = 2,
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
        };
    }

    /// <summary>One body's cast: its feet (world), height and width at the feet (m), how much it shows; fixedLen over 0
    /// with a direction (world x, z) for the light's own bearer.</summary>
    public static void Set(MultiMesh mm, int i, Vector3 feet, float height, float width, float show = 1, float fixedLen = 0, Vector2 dir = default)
    {
        var z = fixedLen > 0 && dir.LengthSquared() > 1e-8f ? new Vector3(dir.X, 0, dir.Y).Normalized() : Vector3.Back;
        var x = Vector3.Up.Cross(z);
        mm.SetInstanceTransform(i, new Transform3D(new Basis(x, Vector3.Up, z), feet + new Vector3(0, Lift, 0)));
        mm.SetInstanceColor(i, new Color(height, width, fixedLen, show));
        if (Count && fixedLen <= 0) stands.Add(feet);
    }
}
