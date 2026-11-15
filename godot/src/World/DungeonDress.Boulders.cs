using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's boulders (dungeon lead 6's helper, 15 Nov): PAINTINGS of each boulder as the fixed play camera sees it
/// (tools/look/den_boulders.py: art/dungeon/den/boulders_paint.png, boulders_form.png, boulders.json), drawn on a card in
/// the boulder facing that camera, which writes the painting's own depth (shaders/den_boulder.gdshader); a shadow-only hull
/// of the painted form casts the key's shadow, and a soft dark blob under it sits it on the floor. Placed at yaw 0: the
/// painting is the boulder from the one view the dungeon camera has.
/// </summary>
public static partial class DungeonDress
{
    const string BoulderJson = "res://art/dungeon/den/boulders.json";

    sealed record Boulder(Vector4 Uv, Vector4 Card, Vector3 Pivot, Vector4 Foot, Vector3[] Hull, int[] Tri);

    static List<Boulder>? boulders;
    static Shader? boulderShader;
    static Texture2D? bPaint, bForm;
    static float bDmax;
    static Vector3 bRight, bUp, bView;
    static GradientTexture2D? blob;

    static List<Boulder> Boulders()
    {
        if (boulders != null) return boulders;
        boulders = new();
        if (!FileAccess.FileExists(BoulderJson)) return boulders;
        using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(BoulderJson));
        var r = doc.RootElement;
        static Vector3 V3(JsonElement e) => new(e[0].GetSingle(), e[1].GetSingle(), e[2].GetSingle());
        var atlas = r.GetProperty("atlas");
        float aw = atlas[0].GetSingle(), ah = atlas[1].GetSingle();
        bDmax = r.GetProperty("dmax").GetSingle();
        var basis = r.GetProperty("basis");
        bRight = V3(basis.GetProperty("right")); bUp = V3(basis.GetProperty("up")); bView = V3(basis.GetProperty("view"));
        foreach (var b in r.GetProperty("boulders").EnumerateArray())
        {
            var rc = b.GetProperty("rect"); var cd = b.GetProperty("card"); var ft = b.GetProperty("foot");
            var hv = b.GetProperty("hull").GetProperty("v"); var hi = b.GetProperty("hull").GetProperty("i");
            var hull = new Vector3[hv.GetArrayLength() / 3];
            for (int k = 0; k < hull.Length; k++) hull[k] = new Vector3(hv[3 * k].GetSingle(), hv[3 * k + 1].GetSingle(), hv[3 * k + 2].GetSingle());
            var tri = new int[hi.GetArrayLength()];
            for (int k = 0; k < tri.Length; k++) tri[k] = hi[k].GetInt32();
            boulders.Add(new Boulder(
                new Vector4(rc[0].GetSingle() / aw, rc[1].GetSingle() / ah, rc[2].GetSingle() / aw, rc[3].GetSingle() / ah),
                new Vector4(cd[0].GetSingle(), cd[1].GetSingle(), cd[2].GetSingle(), cd[3].GetSingle()),
                V3(b.GetProperty("pivot")),
                new Vector4(ft[0].GetSingle(), ft[1].GetSingle(), ft[2].GetSingle(), ft[3].GetSingle()),
                hull, tri));
        }
        bPaint = GD.Load<Texture2D>("res://art/dungeon/den/boulders_paint.png");
        bForm = GD.Load<Texture2D>("res://art/dungeon/den/boulders_form.png");
        boulderShader = GD.Load<Shader>("res://shaders/den_boulder.gdshader");
        return boulders;
    }

    // One painted boulder at (x, zz) on the floor, kind by the hash, at yaw 0 (the painting's view).
    static void PlaceBoulder(Ctx c, int pick, float x, float zz, float scale)
    {
        var all = Boulders();
        if (all.Count == 0 || boulderShader == null) return;
        var b = all[pick % all.Count];
        var n = new Node3D { Name = "Boulder", Position = new Vector3(x, H(c, x, zz), zz), Scale = Vector3.One * scale };
        // the card: the plane through the pivot across the view, spanned by the camera's right and up
        Vector3 o = bView * b.Pivot.Dot(bView);
        Vector3 P(float u, float v) => o + bRight * (b.Card.X + u * b.Card.Z) + bUp * (b.Card.Y + v * b.Card.W);
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        foreach (var (u, v) in new[] { (0f, 0f), (1f, 0f), (1f, 1f), (0f, 0f), (1f, 1f), (0f, 1f) })
        {
            st.SetUV(new Vector2(u, 1f - v));
            st.SetNormal(-bView);
            st.AddVertex(P(u, v));
        }
        var hullBox = new Aabb(b.Hull[0], Vector3.Zero);
        foreach (var hp in b.Hull) hullBox = hullBox.Expand(hp);
        var card = st.Commit();
        card.CustomAabb = hullBox.Merge(new Aabb(P(0, 0), Vector3.Zero).Expand(P(1, 1)));
        var mat = new ShaderMaterial { Shader = boulderShader };
        mat.SetShaderParameter("paint_tex", bPaint);
        mat.SetShaderParameter("form_tex", bForm);
        mat.SetShaderParameter("rect", b.Uv);
        mat.SetShaderParameter("dmax", bDmax);
        mat.SetShaderParameter("right_dir", bRight);
        mat.SetShaderParameter("up_dir", bUp);
        mat.SetShaderParameter("view_dir", bView);
        n.AddChild(new MeshInstance3D { Name = "Painting", Mesh = card, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        // the shadow: the painted form's hull, shadow only
        var hs = new SurfaceTool();
        hs.Begin(Mesh.PrimitiveType.Triangles);
        foreach (int i in b.Tri) hs.AddVertex(b.Hull[i]);
        hs.GenerateNormals();
        n.AddChild(new MeshInstance3D
        {
            Name = "Shadow", Mesh = hs.Commit(), CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly,
            MaterialOverride = new StandardMaterial3D { CullMode = BaseMaterial3D.CullModeEnum.Disabled },
        });
        // the contact: a soft dark blob on the floor under its foot
        blob ??= new GradientTexture2D
        {
            Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
            Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 1f }, Colors = new[] { new Color(0, 0, 0, 1), new Color(0, 0, 0, 0.7f), new Color(0, 0, 0, 0) } },
        };
        float fw = b.Foot.Y - b.Foot.X, fd = b.Foot.W - b.Foot.Z;
        n.AddChild(new Decal
        {
            Name = "Contact", TextureAlbedo = blob, Modulate = new Color(1, 1, 1, 0.6f), AlbedoMix = 1f,
            Size = new Vector3(fw * 1.25f, 1.2f, fd * 1.25f),
            Position = new Vector3(0.5f * (b.Foot.X + b.Foot.Y), 0f, 0.5f * (b.Foot.Z + b.Foot.W)),
        });
        c.Root.AddChild(n);
        c.Tick("rocks");
    }
}
