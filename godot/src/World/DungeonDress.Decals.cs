using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's floor decals (godot/art/dungeon/den/decals.png, painted by tools/look/den_decals.py), scattered by rule over
/// the walkable field and by room kind: roots, fur, twigs and pebbles at the walls' feet; bones, leaves, fur and old blood
/// in the open; the boss room's kills (hides, rib cages, a deer skull) toward its back. Every decal is a small grid draped
/// on the ground's height, all in one mesh on one material (shaders/dungeon_decal.gdshader). A decal's painted light comes
/// from its cell's top, so each is turned or mirrored to keep that side toward the rig's light (ground.json "light").
/// </summary>
public static partial class DungeonDress
{
    sealed record Decal(string Kind, Rect2 Uv, Vector2 Metres, float Weight);

    static List<Decal>? decals;
    static Vector2 decalLight = new(-0.45f, -0.89f);

    static List<Decal> Decals()
    {
        if (decals != null) return decals;
        decals = new();
        using var f = FileAccess.Open("res://art/dungeon/den/decals.json", FileAccess.ModeFlags.Read);
        var doc = JsonDocument.Parse(f.GetAsText());
        var size = doc.RootElement.GetProperty("size");
        float W = size[0].GetSingle(), Hh = size[1].GetSingle();
        var l = doc.RootElement.GetProperty("light");
        decalLight = new Vector2(l[0].GetSingle(), l[1].GetSingle()).Normalized();
        foreach (var d in doc.RootElement.GetProperty("decals").EnumerateArray())
        {
            var r = d.GetProperty("rect");
            var m = d.GetProperty("metres");
            decals.Add(new Decal(d.GetProperty("kind").GetString()!,
                new Rect2(r[0].GetSingle() / W, r[1].GetSingle() / Hh, r[2].GetSingle() / W, r[3].GetSingle() / Hh),
                new Vector2(m[0].GetSingle(), m[1].GetSingle()), d.GetProperty("weight").GetSingle()));
        }
        return decals;
    }

    // Kind weights by where a decal lies: at a wall's foot, in the open, in the boss room's back half.
    static readonly Dictionary<string, float> AtFoot = new() { ["root"] = 3.0f, ["fur"] = 0.8f, ["twigs"] = 1.2f, ["pebbles"] = 1.0f, ["leaves"] = 1.0f, ["bone"] = 0.5f };
    static readonly Dictionary<string, float> InOpen = new() { ["bone"] = 1.4f, ["fur"] = 0.9f, ["leaves"] = 1.0f, ["twigs"] = 0.5f, ["pebbles"] = 0.5f, ["blood"] = 0.35f, ["ribcage"] = 0.25f, ["wolf_skull"] = 0.15f };
    static readonly Dictionary<string, float> BossBack = new() { ["hide"] = 1.2f, ["ribcage"] = 1.2f, ["bone"] = 2.0f, ["fur"] = 1.2f, ["blood"] = 0.8f, ["deer_skull"] = 0.3f, ["wolf_skull"] = 0.4f };

    static Decal PickDecal(Dictionary<string, float> by, float u)
    {
        var all = Decals();
        float sum = 0;
        foreach (var d in all) sum += by.GetValueOrDefault(d.Kind) * d.Weight;
        float t = u * sum;
        foreach (var d in all)
        {
            float w = by.GetValueOrDefault(d.Kind) * d.Weight;
            if (w <= 0) continue;
            if (t < w) return d;
            t -= w;
        }
        return all[0];
    }

    sealed class DecalBuf
    {
        public readonly List<Vector3> V = new();
        public readonly List<Vector2> U = new();
        public readonly List<int> I = new();
        public int Count;
        public readonly Dictionary<string, int> Kinds = new();
    }

    /// <summary>The den's decals over the whole walkable floor (a jittered 1.6 m scan) and the boss room's kills.</summary>
    static void DenDecals(Ctx c)
    {
        var z = c.Z;
        var b = new DecalBuf();
        const float cell = 1.6f;
        int n = (int)(z.Size / cell);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float u0 = Hash(i, j, 901), u1 = Hash(i, j, 902), u2 = Hash(i, j, 903), u3 = Hash(i, j, 904);
                float x = -z.Half + (i + u0) * cell, zz = -z.Half + (j + u1) * cell;
                float w = Wall(c, x, zz), h = Hole(c, x, zz);
                if (w < 0.15f || h < 0.5f) continue;
                bool foot = w < 1.8f;
                // (density: the foot busier than the open, and the open thinner in the rooms' trodden middles)
                float keep = foot ? 0.55f : w > 5f ? 0.2f : 0.32f;
                if (u2 > keep) continue;
                var d = PickDecal(foot ? AtFoot : InOpen, u3);
                if (d.Metres.X * 0.5f > w + 0.4f && d.Kind != "root") continue;
                float yaw;
                if (d.Kind == "root")
                {
                    // a root crawls out from the wall: its long axis along the field's rise, its far end into the room
                    float gx = Wall(c, x + 0.5f, zz) - Wall(c, x - 0.5f, zz), gz = Wall(c, x, zz + 0.5f) - Wall(c, x, zz - 0.5f);
                    yaw = Mathf.Atan2(gz, gx) + (Hash(i, j, 905) - 0.5f) * 0.9f;
                }
                else yaw = Hash(i, j, 906) * Mathf.Tau;
                AddDecal(c, b, d, x, zz, yaw, 0.9f + 0.25f * Hash(i, j, 907));
            }
        // The boss room: its kills strewn over the back (north) half, away from the pits.
        foreach (var r in z.Rooms)
        {
            if (r.Kind != "Boss") continue;
            for (int k = 0; k < 22; k++)
            {
                float a = Mathf.Pi + Hash(k, 77, 1) * Mathf.Pi;  // (north half: -z)
                float dd = Mathf.Sqrt(Hash(k, 77, 2)) * 0.85f * r.R;
                float x = r.X + Mathf.Cos(a) * dd, zz = r.Z + Mathf.Sin(a) * dd;
                if (Wall(c, x, zz) < 0.8f || Hole(c, x, zz) < 1.0f) continue;
                AddDecal(c, b, PickDecal(BossBack, Hash(k, 77, 3)), x, zz, Hash(k, 77, 4) * Mathf.Tau, 0.95f + 0.2f * Hash(k, 77, 5));
            }
        }
        if (b.Count == 0) return;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        var nrm = new Vector3[b.V.Count];
        System.Array.Fill(nrm, Vector3.Up);
        arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = nrm;
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_decal.gdshader") };
        mat.SetShaderParameter("atlas", GD.Load<Texture2D>("res://art/dungeon/den/decals.png"));
        mat.SetShaderParameter("field", DungeonFloor.Field(z));
        mat.SetShaderParameter("half_size", z.Half);
        mat.SetShaderParameter("step", z.Step);
        mat.SetShaderParameter("res", (float)z.Res);
        c.Root.AddChild(new MeshInstance3D { Name = "Decals", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        foreach (var kv in b.Kinds) c.Count["decal " + kv.Key] = kv.Value;
    }

    /// <summary>One decal draped on the ground: its long axis at yaw, mirrored across it when that keeps the painted lit
    /// side (the cell's top) toward the light.</summary>
    static void AddDecal(Ctx c, DecalBuf b, Decal d, float x, float zz, float yaw, float scale)
    {
        var ax = new Vector2(Mathf.Cos(yaw), Mathf.Sin(yaw));
        var up = new Vector2(ax.Y, -ax.X);  // (the cell's top, before any mirror)
        if (up.Dot(decalLight) < 0) up = -up;
        // (the targets draw the den's litter larger than life, so it reads from the play camera: bones and kills x1.5)
        if (d.Kind is "bone" or "ribcage" or "wolf_skull" or "deer_skull" or "fur" or "hide") scale *= 1.5f;
        float W = d.Metres.X * scale, Hh = d.Metres.Y * scale;
        int nx = Mathf.Max(2, Mathf.CeilToInt(W / 0.4f) + 1), ny = Mathf.Max(2, Mathf.CeilToInt(Hh / 0.4f) + 1);
        int base0 = b.V.Count;
        float lift = 0.02f + 0.0015f * (b.Count % 8);
        for (int q = 0; q < ny; q++)
            for (int p = 0; p < nx; p++)
            {
                float s = (float)p / (nx - 1), t = (float)q / (ny - 1);  // (t 0 = the cell's top, the lit side)
                var w = new Vector2(x, zz) + ax * ((s - 0.5f) * W) + up * ((0.5f - t) * Hh);
                b.V.Add(new Vector3(w.X, H(c, w.X, w.Y) + lift, w.Y));
                b.U.Add(new Vector2(d.Uv.Position.X + s * d.Uv.Size.X, d.Uv.Position.Y + t * d.Uv.Size.Y));
            }
        // (winding by the mirror, so every decal faces up)
        bool flip = ax.X * up.Y - ax.Y * up.X > 0;
        for (int q = 0; q < ny - 1; q++)
            for (int p = 0; p < nx - 1; p++)
            {
                int a = base0 + q * nx + p, e = a + 1, f = a + nx, g = f + 1;
                if (flip) { b.I.Add(a); b.I.Add(e); b.I.Add(f); b.I.Add(e); b.I.Add(g); b.I.Add(f); }
                else { b.I.Add(a); b.I.Add(f); b.I.Add(e); b.I.Add(e); b.I.Add(f); b.I.Add(g); }
            }
        b.Count++;
        b.Kinds[d.Kind] = b.Kinds.GetValueOrDefault(d.Kind) + 1;
    }
}
