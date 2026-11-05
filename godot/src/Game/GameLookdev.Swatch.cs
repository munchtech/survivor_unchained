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
/// </summary>
public partial class Game
{
    static readonly bool LookSwatchesOn = Args.Has("lookdev-swatches");
    bool lookSwatchesBuilt;

    void LookSwatches()
    {
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
            var mat = new StandardMaterial3D { AlbedoColor = new Color(CelLib.Lib.Classes[cls].Mid!), Roughness = RoughFor(cls), Metallic = cls is "iron" or "bronze" or "gold" ? 1f : 0f };
            var mi = new MeshInstance3D { Name = "Swatch_" + cls, Mesh = mesh, MaterialOverride = mat };
            root.AddChild(mi);
            mi.GlobalPosition = W(0, 0.25f);
            if (CelLib.On) CelLib.Bind(mat, cls);
            var lab = new Label3D { Name = "SwatchLabel_" + cls, Text = cls, PixelSize = 0.0035f, FontSize = 40, Modulate = new Color(1, 0.95f, 0.8f), OutlineSize = 10, OutlineModulate = Colors.Black, Billboard = BaseMaterial3D.BillboardModeEnum.FixedY, NoDepthTest = true };
            root.AddChild(lab);
            lab.GlobalPosition = W(-0.38f, 0.07f);
        }
        GD.Print($"lookdev: {classes.Count} swatches in 2 rows of {perRow}");
    }

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
                bool flip = (v[1].P - v[0].P).Cross(v[2].P - v[0].P).Dot(N) < 0;
                var order = flip ? new[] { 0, 2, 1, 3, 5, 4 } : new[] { 0, 1, 2, 3, 4, 5 };
                foreach (int k in order) { st.SetNormal(v[k].Nr); st.AddVertex(v[k].P); }
            }
        return st.Commit();
    }

    static float Ease(float t) => Mathf.Sin((t * 2 - 1) * Mathf.Pi / 2);
}
