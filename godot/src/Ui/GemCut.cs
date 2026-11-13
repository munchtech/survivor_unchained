using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>A support gem as a 16-fold round brilliant (bd-ui W16): the table, 8 star, 8 kite (bezel) and 16 upper-girdle
/// facets, the girdle, 16 lower-girdle facets and 8 pavilion mains to the culet. Every facet is flat, with its own normal;
/// gem_cut.gdshader gives each the look of a jewel (near-black / body / bright / white strip). One model for the photograph,
/// the panel and the ground. About 1 unit across, the culet at -0.5 and the table at +0.25.</summary>
public static class GemCut
{
    // The deep body colours, their lights, and the near-black of the dark facets (the judge's, bd-ui round 1).
    static readonly Dictionary<string, (string Body, string Bright, string Dark)> Colours = new()
    {
        ["garnet"] = ("#5E0B16", "#E33244", "#12020A"),
        ["sapphire"] = ("#0E2A80", "#5A93FF", "#030A22"),
        ["clear"] = ("#AEBBCD", "#F4F8FF", "#3A4656"),
    };

    // The ground stone's own values (the judge's, round 2): garnet #9E1626 with lights #FF5A6A, sapphire #1D4FD0 with lights #8AB8FF,
    // and an inner glow so it reads lit from inside on the grass.
    static readonly Dictionary<string, (string Body, string Bright, string Dark)> GroundColours = new()
    {
        ["garnet"] = ("#9E1626", "#FF5A6A", "#5E0B16"),
        ["sapphire"] = ("#1D4FD0", "#8AB8FF", "#0A1C66"),
        ["clear"] = ("#AEBBCD", "#F4F8FF", "#5C6878"),
    };

    static ArrayMesh? mesh;
    static Shader? shader, glint;

    /// <summary>The stone for a family ("garnet", "sapphire", "clear", "bicolor"); `withGlint` adds the one four-point glint
    /// the photograph carries (the ground's is its own light).</summary>
    public static Node3D Make(string family, bool withGlint, bool ground = false)
    {
        mesh ??= BuildMesh();
        shader ??= GD.Load<Shader>("res://shaders/gem_cut.gdshader");
        var mat = new ShaderMaterial { Shader = shader };
        var set = ground ? GroundColours : Colours;
        var a = set[family == "bicolor" ? "garnet" : family];
        if (ground) { mat.SetShaderParameter("glow", family is "garnet" or "bicolor" ? 0.9f : 0.6f); if (family == "bicolor") mat.SetShaderParameter("glow_b", 0.6f); if (family is "garnet" or "bicolor") { mat.SetShaderParameter("floor_k", 0.55f); mat.SetShaderParameter("lit_min", 0.2f); mat.SetShaderParameter("bright_share", 0.5f); mat.SetShaderParameter("tab_lo", 0.57f); } }
        mat.SetShaderParameter("body", new Color(a.Body));
        mat.SetShaderParameter("bright", new Color(a.Bright));
        mat.SetShaderParameter("dark", new Color(a.Dark));
        if (family == "clear") mat.SetShaderParameter("alt", 1.0f);
        if (family == "bicolor")
        {
            if (withGlint) mat.SetShaderParameter("split_turn", 0.4f);
            else mat.SetShaderParameter("split_view", true);
            var b = set["sapphire"];
            mat.SetShaderParameter("split", true);
            mat.SetShaderParameter("body_b", new Color(b.Body));
            mat.SetShaderParameter("bright_b", new Color(b.Bright));
            mat.SetShaderParameter("dark_b", new Color(b.Dark));
        }
        var root = new Node3D();
        root.AddChild(new MeshInstance3D { Mesh = mesh, MaterialOverride = mat });
        if (withGlint)
        {
            glint ??= GD.Load<Shader>("res://shaders/gem_glint.gdshader");
            root.AddChild(new MeshInstance3D
            {
                Mesh = new QuadMesh { Size = new Vector2(0.35f, 0.35f) }, MaterialOverride = new ShaderMaterial { Shader = glint },
                Position = new Vector3(0.006f, 0.290f, 0.466f), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            });
        }
        return root;
    }

    static Vector3 Ring(float r, float y, int step, float offset = 0)
    {
        float a = Mathf.Pi / 4 * step + offset;
        return new Vector3(Mathf.Cos(a) * r, y, Mathf.Sin(a) * r);
    }

    static ArrayMesh BuildMesh()
    {
        const float half = Mathf.Pi / 8;
        const float girdleTop = 0.03f, girdleBottom = 0f;
        var P = new List<Vector3>(); var N = new List<Vector3>(); var I = new List<int>();
        void Poly(params Vector3[] v)
        {
            // Flat: one normal (Newell), turned to point out of the stone; a fan of triangles, each wound as Godot faces front
            // (clockwise seen from outside: (c - a) x (b - a) points out, as Build.Faceted has it).
            var n = Vector3.Zero;
            for (int i = 0; i < v.Length; i++) { var c = v[i]; var d = v[(i + 1) % v.Length]; n += new Vector3((c.Y - d.Y) * (c.Z + d.Z), (c.Z - d.Z) * (c.X + d.X), (c.X - d.X) * (c.Y + d.Y)); }
            n = n.Normalized();
            var mid = Vector3.Zero; foreach (var c in v) mid += c; mid /= v.Length;
            if (n.Dot(mid - new Vector3(0, -0.1f, 0)) < 0) n = -n;
            int b = P.Count;
            foreach (var c in v) { P.Add(c); N.Add(n); }
            for (int i = 1; i < v.Length - 1; i++)
            {
                var ta = v[0]; var tb = v[i]; var tc = v[i + 1];
                bool front = (tc - ta).Cross(tb - ta).Dot(n) > 0;
                I.Add(b); I.Add(front ? b + i : b + i + 1); I.Add(front ? b + i + 1 : b + i);
            }
        }
        for (int k = 0; k < 8; k++)
        {
            Vector3 T(int j) => Ring(0.27f, 0.25f, j);                 // table corners at 45k
            Vector3 S(int j) => Ring(0.38f, 0.19f, j, half);           // star tips between them
            Vector3 G(int j) => Ring(0.5f, girdleTop, j);              // girdle points under the corners
            Vector3 H(int j) => Ring(0.5f, girdleTop, j, half);        // girdle points under the star tips
            Vector3 Gl(int j) => Ring(0.5f, girdleBottom, j);
            Vector3 Hl(int j) => Ring(0.5f, girdleBottom, j, half);
            Vector3 U(int j) => Ring(0.31f, -0.2f, j, half);           // pavilion mid points
            var culet = new Vector3(0, -0.5f, 0);
            int k1 = k + 1, km = k - 1;
            // Crown.
            Poly(T(k), T(k1), S(k));                                   // star
            Poly(T(k), S(k), G(k), S(km));                             // kite
            Poly(S(k), G(k1), H(k));                                   // upper girdle, two to a star tip
            Poly(S(k), H(k), G(k));
            // Girdle band: two flat faces per step.
            Poly(G(k), H(k), Hl(k), Gl(k));
            Poly(H(k), G(k1), Gl(k1), Hl(k));
            // Pavilion.
            Poly(culet, U(km), Gl(k), U(k));                           // main
            Poly(U(k), Gl(k1), Hl(k));                                 // lower girdle
            Poly(U(k), Hl(k), Gl(k));
        }
        // The table.
        var table = new Vector3[8];
        for (int k = 0; k < 8; k++) table[k] = Ring(0.27f, 0.25f, k);
        Poly(table);
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = P.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = N.ToArray();
        arr[(int)Mesh.ArrayType.Index] = I.ToArray();
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        return m;
    }
}
