using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The camp on the Low Ford road (Lowford's fire), where the title, the
/// making of a survivor and C01 are shot: the first place anyone sees close.
/// The web game blocked it out in primitives, two octagonal logs and a
/// tripod of sticks over a black ball. Here the logs are pine, sawn to
/// length and left out a season, their bark furrowed and their ends greyed
/// and checked; the tripod and its pot are gone. It is one traveller's fire,
/// and C01's low cameras round her on the ground see her, not a leg of it.
/// </summary>
public static class Camp
{
    /// <summary>The web game's pieces it replaces, by where their middles
    /// stand: the seat log (trunk, end rings, end cores, a stub), the north
    /// log (the same), and the tripod's legs, chain, pot and stew.</summary>
    static readonly Vector3[] Crude =
    {
        new(-8.49f, 0.24f, 90.3f), new(-8.25f, 0.24f, 89.18f), new(-8.25f, 0.23f, 89.18f), new(-8.75f, 0.24f, 91.42f), new(-8.75f, 0.23f, 91.42f), new(-8.58f, 0.47f, 90.64f),
        new(-10.9f, 0.24f, 88.21f), new(-10.1f, 0.24f, 88.12f), new(-10.1f, 0.23f, 88.12f), new(-11.7f, 0.24f, 88.28f), new(-11.7f, 0.23f, 88.28f), new(-11.14f, 0.43f, 88.22f),
        new(-10.1f, 0.79f, 90.5f), new(-10.7f, 0.79f, 90.84f), new(-10.7f, 0.79f, 90.16f), new(-10.5f, 1.28f, 90.5f), new(-10.5f, 0.94f, 90.5f), new(-10.5f, 1.08f, 90.5f),
    };

    /// <summary>Hides the blocked-out camp among the landmarks (not yet in
    /// the tree) and returns the made one, to add beside them.</summary>
    public static Node3D Dress(Node3D landmarks)
    {
        foreach (var n in landmarks.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi) continue;
            var t = Transform3D.Identity;
            for (Node? p = mi; p != null && p != landmarks; p = p.GetParent()) if (p is Node3D p3) t = p3.Transform * t;
            var c = (t * mi.GetAabb()).GetCenter();
            foreach (var k in Crude) if (c.DistanceTo(k) < 0.06f) { mi.Visible = false; break; }
        }
        var bark = new Sheet();
        var ends = new Sheet();
        // The seat, east of the fire, north to south: the title's stranger
        // sits on its middle and C01's weapon leans at its south end. Its
        // collider is the web game's (2.3 by 0.54 m), so it keeps that size.
        var seat = Log(bark, ends, new Vector3(-8.25f, 0.215f, 89.18f), new Vector3(-8.75f, 0.215f, 91.42f), 0.265f, 1);
        // A limb lopped close on its east side, away from the fire and the sitter.
        Vector3 root = seat(0.78f, -0.18f, 0.5f), skin = seat(0.78f, -0.18f, 1f);
        Log(bark, ends, root, skin + (skin - root).Normalized() * 0.11f + Vector3.Up * 0.03f, 0.05f, 3, inner: true);
        // The north log, lower and thinner, a second seat nobody took.
        Log(bark, ends, new Vector3(-10.1f, 0.19f, 88.12f), new Vector3(-11.7f, 0.19f, 88.28f), 0.215f, 2);
        var camp = new Node3D { Name = "Camp" };
        camp.AddChild(new MeshInstance3D { Name = "Bark", Mesh = bark.Mesh(), MaterialOverride = Bark() });
        camp.AddChild(new MeshInstance3D { Name = "Ends", Mesh = ends.Mesh(), MaterialOverride = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/endgrain.gdshader") } });
        return camp;
    }

    /// <summary>The pine bark (Poly Haven's, 2 m to its sheet), a little
    /// greyed: the tree has been dead a while.</summary>
    static StandardMaterial3D Bark()
    {
        const string dir = "res://art/materials/pine_bark";
        var arm = GD.Load<Texture2D>($"{dir}/arm.jpg");
        return new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>($"{dir}/albedo.jpg"), AlbedoColor = new Color(0.86f, 0.82f, 0.78f),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>($"{dir}/normal.jpg"), NormalScale = 1.3f,
            Roughness = 1, RoughnessTexture = arm, RoughnessTextureChannel = BaseMaterial3D.TextureChannel.Green,
            AOEnabled = true, AOTexture = arm, AOTextureChannel = BaseMaterial3D.TextureChannel.Red,
        };
    }

    /// <summary>A log from a to b, sawn at both ends a little out of square:
    /// out of round, bowed, knotted, a little thinner toward b. The bark's
    /// sheet wraps round it a whole number of times with its grain along the
    /// log, and each end has its own pith and pattern. `inner` leaves off the
    /// end at a (a limb's, inside the trunk). Returns a point of it: (along,
    /// 0 to 1; round, in turns from the top; out, 0 at the axis to 1 at the
    /// bark).</summary>
    static Func<float, float, float, Vector3> Log(Sheet bark, Sheet ends, Vector3 a, Vector3 b, float r, int seed, bool inner = false)
    {
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 7919 + 13) };
        float len = a.DistanceTo(b);
        var T = (b - a) / len;
        var S = T.Cross(Mathf.Abs(T.Y) < 0.9f ? Vector3.Up : Vector3.Right).Normalized();
        var U = S.Cross(T).Normalized();
        if (U.Y < 0) { U = -U; S = -S; }
        var ph = new float[6];
        for (int i = 0; i < ph.Length; i++) ph[i] = rng.Randf() * Mathf.Tau;
        // Two knots, swellings where limbs were.
        var knots = new[] { (T: 0.2f + 0.2f * rng.Randf(), Th: rng.Randf() * Mathf.Tau), (T: 0.55f + 0.3f * rng.Randf(), Th: rng.Randf() * Mathf.Tau) };
        float Rad(float t, float th)
        {
            float k = 1 - 0.07f * t
                + 0.035f * Mathf.Cos(2 * th + ph[0]) + 0.025f * Mathf.Sin(3 * th + ph[1] + 4 * t)
                + 0.015f * Mathf.Sin(5 * th + ph[2] - 7 * t) + 0.02f * Mathf.Sin(9 * t + ph[3]) * Mathf.Cos(th + ph[4]);
            foreach (var kn in knots)
            {
                float dt = (t - kn.T) * len / (r * 0.45f), da = Mathf.AngleDifference(th, kn.Th) / 0.45f;
                k += 0.07f * Mathf.Exp(-dt * dt - da * da);
            }
            return r * k;
        }
        float bow = Mathf.Min(0.018f, len * 0.05f);
        Vector3 Axis(float t) => a + T * (len * t) + (U * 0.018f * Mathf.Sin(Mathf.Pi * t) + S * 0.012f * Mathf.Sin(Mathf.Pi * 1.3f * t + ph[5])) * (bow / 0.018f);
        Vector3 Dir(float th) => U * Mathf.Cos(th) + S * Mathf.Sin(th);
        // The saw ran a few degrees off square at each end.
        float tilt0 = Mathf.Tan(Mathf.DegToRad(2 + 5 * rng.Randf())), tilt1 = Mathf.Tan(Mathf.DegToRad(2 + 5 * rng.Randf()));
        Vector3 cut0 = Dir(rng.Randf() * Mathf.Tau), cut1 = Dir(rng.Randf() * Mathf.Tau);
        Vector3 At(float t, float th, float out_ = 1)
        {
            var d = Dir(th) * Rad(t, th) * out_;
            var p = Axis(t) + d;
            if (t <= 0) p += T * (tilt0 * d.Dot(cut0));
            if (t >= 1) p -= T * (tilt1 * d.Dot(cut1));
            return p;
        }
        int rings = Mathf.Max(6, Mathf.CeilToInt(len / 0.04f)) + 1, sides = r > 0.1f ? 48 : 16;
        // Whole turns of the sheet round it, drawn at about 1.2 m, and the same scale along.
        float around = Mathf.Max(1, Mathf.Round(Mathf.Tau * r / 1.2f)), tile = Mathf.Tau * r / around;
        var P = new Vector3[rings, sides + 1];
        for (int i = 0; i < rings; i++)
            for (int s = 0; s <= sides; s++)
                P[i, s] = At((float)i / (rings - 1), Mathf.Tau * s / sides);
        int v0 = bark.P.Count;
        for (int i = 0; i < rings; i++)
            for (int s = 0; s <= sides; s++)
            {
                var du = P[i, (s + 1) % sides] - P[i, (s - 1 + sides) % sides];
                var dv = P[Mathf.Min(rings - 1, i + 1), s % sides] - P[Mathf.Max(0, i - 1), s % sides];
                var n = du.Cross(dv).Normalized();
                if (n.Dot(P[i, s] - Axis((float)i / (rings - 1))) < 0) n = -n;
                bark.V(P[i, s], n, new Vector2(around * s / sides, len * i / (rings - 1) / tile));
            }
        for (int i = 0; i < rings - 1; i++)
            for (int s = 0; s < sides; s++)
            {
                int q0 = v0 + i * (sides + 1) + s, q2 = q0 + sides + 1;
                bark.Quad(q0, q0 + 1, q2 + 1, q2, P[i, s] - Axis((float)i / (rings - 1)));
            }
        // The sawn ends: a fan of loops, each face with its pith a little off the axis.
        float[] loops = { 0, 0.2f, 0.4f, 0.6f, 0.8f, 0.92f, 1 };
        foreach (var (t, sd) in new[] { (0f, seed * 2.1f), (1f, seed * 2.1f + 1) })
        {
            if (inner && t <= 0) continue;
            var pith = (U * (rng.Randf() - 0.5f) + S * (rng.Randf() - 0.5f)) * (r * 0.2f);
            var nrm = t <= 0 ? (-T + cut0 * tilt0).Normalized() : (T - cut1 * tilt1).Normalized();
            int e0 = ends.P.Count;
            foreach (var f in loops)
                for (int s = 0; s <= sides; s++)
                {
                    var p = At(t, Mathf.Tau * s / sides, f);
                    var off = p - Axis(t) - pith;
                    ends.V(p, nrm, new Vector2(off.Dot(S), off.Dot(U)), new Vector2(f, sd));
                }
            for (int l = 0; l < loops.Length - 1; l++)
                for (int s = 0; s < sides; s++)
                {
                    int q0 = e0 + l * (sides + 1) + s, q2 = q0 + sides + 1;
                    ends.Quad(q0, q0 + 1, q2 + 1, q2, nrm);
                }
        }
        return (t, round, out_) => At(t, round * Mathf.Tau, out_);
    }

    /// <summary>A mesh built up: points, normals, two UV sets, triangles.</summary>
    sealed class Sheet
    {
        public readonly List<Vector3> P = new(), N = new();
        readonly List<Vector2> uv = new(), uv2 = new();
        readonly List<int> idx = new();

        public void V(Vector3 p, Vector3 n, Vector2 u, Vector2 u2 = default) { P.Add(p); N.Add(n); uv.Add(u); uv2.Add(u2); }

        /// <summary>Two triangles, wound to face `toward` (Godot's front faces wind clockwise).</summary>
        public void Quad(int a, int b, int c, int d, Vector3 toward)
        {
            Tri(a, b, c, toward);
            Tri(a, c, d, toward);
        }

        void Tri(int a, int b, int c, Vector3 toward)
        {
            if ((P[c] - P[a]).Cross(P[b] - P[a]).Dot(toward) < 0) (b, c) = (c, b);
            idx.Add(a); idx.Add(b); idx.Add(c);
        }

        public ArrayMesh Mesh()
        {
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Godot.Mesh.ArrayType.Max);
            arr[(int)Godot.Mesh.ArrayType.Vertex] = P.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Normal] = N.ToArray();
            arr[(int)Godot.Mesh.ArrayType.TexUV] = uv.ToArray();
            arr[(int)Godot.Mesh.ArrayType.TexUV2] = uv2.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Index] = idx.ToArray();
            var m = new ArrayMesh();
            m.AddSurfaceFromArrays(Godot.Mesh.PrimitiveType.Triangles, arr);
            var st = new SurfaceTool();
            st.CreateFrom(m, 0);
            st.GenerateTangents();
            return st.Commit();
        }
    }
}
