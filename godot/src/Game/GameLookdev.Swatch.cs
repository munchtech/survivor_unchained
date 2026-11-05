using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>
/// --lookdev-swatches (L1 B2): on the lookdev stage, one 0.5 m rounded block per class of the material library (file order,
/// classes without a measured albedo skipped) in two rows in front of the sphere row. Each is a StandardMaterial3D of the class's
/// board-measured albedo (its middle color with the board's light divided out) put on the model in its class by CelLib.Bind; a Label3D names it. Without the flag nothing is built.
/// --lookdev-swatch-y Y (2.8), --lookdev-swatch-gap G (1.0): the front row's depth and the row spacing, in stage meters.
/// --b3-white (L1 B3 round 2, tools/look/calib.py): every swatch at albedo 1 (white), so a frame measures each class's response
/// to the rig (its lit and shade faces); each swatch's middle and the row's frame are printed ("b3-swatch" lines).
/// --b3-albedo FILE.json ({"class": "#rrggbb ROUGH"}): the swatches in those colors instead, drawn as B3's painted maps are
/// (metallic 0, roughness ROUGH; tools/look/calib.py: "#ffffff" for the response, the solved albedo for the relit check).
/// </summary>
public partial class Game
{
    static readonly bool LookSwatchesOn = Args.Has("lookdev-swatches");
    bool lookSwatchesBuilt;

    void LookSwatches()
    {
        LookItems();   // (B3r2: --b3-cams, GameLookdev.Items.cs)
        if (!LookSwatchesOn || lookSwatchesBuilt || lookBuiltAt < 0 || scene == null) return;
        var root = scene.GetNodeOrNull<Node3D>("Lookdev");
        if (root == null) return;
        lookSwatchesBuilt = true;
        var classes = CelLib.Lib.Classes.Where(kv => kv.Value.Mid != null).Select(kv => kv.Key).ToList();
        int perRow = (classes.Count + 1) / 2;
        float step = 0.66f, y0 = -(float)Args.Num("lookdev-swatch-y", 2.8f), gap = (float)Args.Num("lookdev-swatch-gap", 1.0f);
        var mesh = RoundedBox(0.5f, 0.07f, 6);
        var basis = new Basis(lookR, Vector3.Up, -lookF);
        for (int i = 0; i < classes.Count; i++)
        {
            string cls = classes[i];
            int row = i / perRow, col = i % perRow;
            float x = 0.8f + (col - (perRow - 1) / 2f) * step, y = y0 - row * gap;
            Vector3 W(float dy, float lift)
            {
                var w = lookP + lookR * x + lookF * (y + dy);
                w.Y = (float)scene.HeightAt(w.X, w.Z) + lift;
                return w;
            }
            // (B3r2: a class given in --b3-albedo is drawn as B3's painted maps draw it (B3Maps.Mat): metallic 0, its roughness)
            var b3 = B3Albedo.TryGetValue(cls, out var bh) ? bh.Split(' ') : null;
            var tint = Args.Has("b3-white") ? Colors.White : b3 != null ? new Color(b3[0]) : new Color(CelLib.Lib.Classes[cls].Mid!);
            var mat = new StandardMaterial3D { AlbedoColor = tint, Roughness = RoughFor(cls), Metallic = cls is "iron" or "bronze" or "gold" ? 1f : 0f };
            if (b3 is { Length: > 1 }) { mat.Roughness = float.Parse(b3[1], System.Globalization.CultureInfo.InvariantCulture); mat.Metallic = 0; }
            var mi = new MeshInstance3D { Name = "Swatch_" + cls, Mesh = mesh, MaterialOverride = mat };
            root.AddChild(mi);
            mi.GlobalPosition = W(0, 0.25f);
            if (CelLib.On) CelLib.Bind(mat, cls);
            var lab = new Label3D { Name = "SwatchLabel_" + cls, Text = cls, PixelSize = 0.0035f, FontSize = 40, Modulate = new Color(1, 0.95f, 0.8f), OutlineSize = 10, OutlineModulate = Colors.Black, Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true };
            root.AddChild(lab);
            lab.GlobalPosition = W(-0.38f, 0.07f);
            var sp = mi.GlobalPosition;
            GD.Print($"b3-swatch {cls} {sp.X:0.0000} {sp.Y:0.0000} {sp.Z:0.0000} {tint.ToHtml(false)}");
        }
        GD.Print($"b3-swatch-frame {lookR.X:0.0000} {lookR.Z:0.0000} {lookF.X:0.0000} {lookF.Z:0.0000} 0.5");
        // (B2r2) No wolf in front of the rows: a held wolf standing within 1.5 m of a row's depth is moved behind the others
        // (the stage holds each at its BoundX/BoundZ every frame).
        foreach (var w in lookWolves)
        {
            var d = new Vector3((float)w.BoundX, 0, (float)w.BoundZ) - lookP;
            float wy = d.Dot(lookF), wx = d.Dot(lookR);
            if (wy > y0 + 1.5f || wy < y0 - gap - 1.5f) continue;
            var to = lookP + lookR * wx + lookF * 3.6f;
            w.BoundX = to.X; w.BoundZ = to.Z;
        }
        GD.Print($"lookdev: {classes.Count} swatches in 2 rows of {perRow}");
    }

    static readonly System.Collections.Generic.Dictionary<string, string> B3Albedo = Args.Get("b3-albedo") is string bf && System.IO.File.Exists(bf)
        ? System.Text.Json.JsonSerializer.Deserialize<System.Collections.Generic.Dictionary<string, string>>(System.IO.File.ReadAllText(bf)) ?? new() : new();

    static float RoughFor(string cls) => cls switch
    {
        "iron" or "bronze" or "gold" => 0.35f,
        "gloss" or "glass" => 0.2f,
        "satin" => 0.4f,
        "skin" or "folk_skin" or "leather" => 0.5f,
        "hair" => 0.45f,
        _ => 0.9f,
    };

    /// <summary>A cube of the given edge with bevelled (rounded) edges: each face's grid pushed onto an inner box grown by r, smooth normals.</summary>
    static ArrayMesh RoundedBox(float size, float r, int seg)
    {
        float H = size / 2, h = H - r;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        int n = seg * 3;
        var faces = new (Vector3 N, Vector3 U, Vector3 V)[]
        {
            (Vector3.Right, Vector3.Back, Vector3.Up), (Vector3.Left, Vector3.Forward, Vector3.Up),
            (Vector3.Up, Vector3.Right, Vector3.Back), (Vector3.Down, Vector3.Right, Vector3.Forward),
            (Vector3.Back, Vector3.Left, Vector3.Up), (Vector3.Forward, Vector3.Right, Vector3.Up),
        };
        foreach (var (N, U, V) in faces)
            for (int a = 0; a < n; a++) for (int b = 0; b < n; b++)
            {
                (Vector3 P, Vector3 Nr) Pt(int i, int j)
                {
                    var q = (N + U * Ease(i / (float)n) + V * Ease(j / (float)n)) * H;
                    var c = new Vector3(Mathf.Clamp(q.X, -h, h), Mathf.Clamp(q.Y, -h, h), Mathf.Clamp(q.Z, -h, h));
                    var d = q - c; d = d.LengthSquared() < 1e-10f ? N : d.Normalized();
                    return (c + d * r, d);
                }
                var v = new[] { Pt(a, b), Pt(a + 1, b), Pt(a + 1, b + 1), Pt(a, b), Pt(a + 1, b + 1), Pt(a, b + 1) };
                // (Godot draws clockwise triangles as front faces: wound counter-clockwise, the swatches were drawn inside out,
                // the row showing each box's inner floor and walls in their own shadow; B3r2)
                bool flip = (v[1].P - v[0].P).Cross(v[2].P - v[0].P).Dot(N) > 0;
                var order = flip ? new[] { 0, 2, 1, 3, 5, 4 } : new[] { 0, 1, 2, 3, 4, 5 };
                foreach (int k in order) { st.SetNormal(v[k].Nr); st.AddVertex(v[k].P); }
            }
        return st.Commit();
    }

    static float Ease(float t) => Mathf.Sin((t * 2 - 1) * Mathf.Pi / 2);
}
