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
    // (den r17 D3, R16 item: the lit decal bones rendered cream-yellow, L .82 C .10, den_room's L .69-.75 C .06-.07) the cause:
    // dungeon_decal.gdshader's bone_k branch gates on luminance .3-.6 and saturation under .25-.5 measured on the LINEAR
    // atlas (a source_color sampler), where the bones' body sits at L .17, sat .42: it fired on about a tenth of their
    // pixels, so --den-bone / --den-bone-sat did nothing visible. Now the bone kinds are marked per vertex (COLOR.r) and
    // graded in Oklab there: x the L scale, y the chroma scale, z a hue turn (degrees), w on (0 = the old branch alone).
    static readonly Vector4 BoneGrade = new(SurvivorUnchained.Args.Num("den-bone-l", 0.95f), SurvivorUnchained.Args.Num("den-bone-c", 0.38f), SurvivorUnchained.Args.Num("den-bone-h", -12f), SurvivorUnchained.Args.Num("den-bone-grade", 1f));
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

    // Kind weights by where a decal lies: in a pile (a kill's leavings), a wall's foot, the open between, the lair's floor.
    // (round 8) bones a third of a pile, not two thirds: a kill reads by its rib cage, skull and fur, the long bones were white noise
    static readonly Dictionary<string, float> InPile = new() { ["bone"] = 1.0f, ["ribcage"] = 0.8f, ["fur"] = 0.5f, ["wolf_skull"] = 0.35f, ["leaves"] = 0.5f, ["twigs"] = 0.35f, ["pebbles"] = 0.2f };
    static readonly Dictionary<string, float> InBossPile = new() { ["bone"] = 1.0f, ["ribcage"] = 1.0f, ["fur"] = 0.5f, ["hide"] = 0.45f, ["wolf_skull"] = 0.35f, ["deer_skull"] = 0.12f, ["leaves"] = 0.45f };
    static readonly Dictionary<string, float> AtFoot = new() { ["root"] = 2.0f, ["twigs"] = 1.2f, ["pebbles"] = 1.0f, ["leaves"] = 1.0f, ["fur"] = 0.4f, ["moss"] = 0.5f };
    static readonly Dictionary<string, float> InOpen = new() { ["leaves"] = 1.4f, ["pebbles"] = 0.8f, ["twigs"] = 0.6f, ["root"] = 2.4f, ["fur"] = 0.2f, ["blood"] = SurvivorUnchained.Args.Num("den-open-blood", 0f), ["bone"] = SurvivorUnchained.Args.Num("den-open-bone", 0f) };   // (den r17 D2, lead item 1: bones only inside the clusters, none alone in the open; .6 = d7e)   // (den r15 S: no lone floor blood: a puddle with no kill read as paint)   // (den r14 item 8: the open floor was empty: thin roots, flat leaves, pebbles)
    static readonly Dictionary<string, float> Under = new() { ["blood"] = 1.0f, ["drift"] = SurvivorUnchained.Args.Num("den-drift", 0f) };   // (den r15 Q, judge r15 item 4: still the orange bean clumps at 0.08, now cut)   // (den r15 D: the leaf drifts read as orange bean clumps at the camera; kept rare)

    static readonly float OpenLitter = SurvivorUnchained.Args.Num("den-open-litter", 6f);   // (den r15 D) the open floor's litter density, x
    static Vector2? lairC; static float lairR;
    static readonly float LairLeaves = SurvivorUnchained.Args.Num("den-lair-leaves", 0f);
    static readonly int LairDeerCap = (int)SurvivorUnchained.Args.Num("den-lair-deer", 3f);
    static int lairDeer;
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
        public readonly List<Color> K = new();   // (den r17 D3) per vertex: r 1 on the pale bone kinds (dungeon_decal.gdshader's bone grade); empty = none
        public int Count;
        public readonly Dictionary<string, int> Kinds = new();
    }

    /// <summary>The den's litter by rule: the kills' leavings in PILES (round 6: an even scatter read as noise) round the
    /// pits' lips, at the banks' feet and beside the boulders, the boss room's open floor piled on a jittered 4.5 m grid
    /// with drag marks, moss and leaf drifts between; the open floor between piles sparse, the walls' feet busier.</summary>
    static void DenDecals(Ctx c)
    {
        var z = c.Z;
        var b = new DecalBuf(); lairDeer = 0;
        var pits = DenPits(c);
        var hollows = DenHollows(c);
        bool Ok(float x, float zz, float wmin, float hmin)
        {
            if (Wall(c, x, zz) < wmin || Hole(c, x, zz) < hmin) return false;
            foreach (var (hp, hr, _) in hollows) if (hp.DistanceSquaredTo(new Vector2(x, zz)) < (hr + 0.2f) * (hr + 0.2f)) return false;
            return true;
        }
        int boss = -1;
        for (int k = 0; k < z.Rooms.Count; k++) if (z.Rooms[k].Kind == "Boss") boss = k;
        bool InBoss(Vector2 p) => boss >= 0 && p.DistanceTo(new Vector2(z.Rooms[boss].X, z.Rooms[boss].Z)) < z.Rooms[boss].R * 1.05f;
        lairC = boss >= 0 ? new Vector2(z.Rooms[boss].X, z.Rooms[boss].Z) : null; lairR = boss >= 0 ? z.Rooms[boss].R * 1.05f : 0f;   // (den r15 Q) for AddDecal's lair leaf cut
        Vector2 Inward(float x, float zz)
        {
            var g = new Vector2(Wall(c, x + 0.5f, zz) - Wall(c, x - 0.5f, zz), Wall(c, x, zz + 0.5f) - Wall(c, x, zz - 0.5f));
            return g.LengthSquared() < 1e-8f ? Vector2.Right : g.Normalized();
        }

        // ---- the piles' seeds: (where, size, the boss room's) ----
        var seeds = new List<(Vector2 p, float size, bool boss)>();
        int pi = 0;
        foreach (var (pc, pr, _) in pits)
        {
            pi++;
            int m = 2 + (pr > 2.6f ? 1 : 0);
            float a0 = Hash(pi, 1, 931) * Mathf.Tau;
            for (int k = 0; k < m; k++)
            {
                float a = a0 + k * Mathf.Tau / m + (Hash(pi, k, 932) - 0.5f) * 1.2f;
                var p = pc + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * (pr + 0.9f + 0.6f * Hash(pi, k, 933));
                if (Ok(p.X, p.Y, 0.6f, 0.6f)) seeds.Add((p, 0.9f, InBoss(p)));
            }
        }
        int ri = 0;
        foreach (var (rp, bh) in c.Boulders)   // (the boulders Den() set down: they stay where they sit)
        {
            ri++;
            var dir = Inward(rp.X, rp.Y).Rotated((Hash(ri, 2, 934) - 0.5f) * 1.6f);
            float dd = bh + 0.6f + 0.4f * Hash(ri, 3, 934);
            var p = rp + dir * dd;
            if (Ok(p.X, p.Y, 0.4f, 0.8f)) seeds.Add((p, 0.8f, InBoss(p)));
        }
        foreach (var (hp, hr, _) in DenHollows(c))   // (and the lair's hollows: bones heaped at their lips)
        {
            ri++;
            float a = Hash(ri, 4, 934) * Mathf.Tau;
            var p = hp + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * (hr + 0.7f);
            if (Ok(p.X, p.Y, 0.6f, 0.8f)) seeds.Add((p, 0.8f, InBoss(p)));
        }
        {
            const float scan = 0.5f;
            int n = (int)(z.Size / scan);
            var taken = new List<Vector2>();
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    float x = -z.Half + (i + 0.5f) * scan, zz = -z.Half + (j + 0.5f) * scan;
                    float w = Wall(c, x, zz);
                    if (Mathf.Abs(w - 1.1f) > 0.26f || Hole(c, x, zz) < 1.5f) continue;
                    var p = new Vector2(x, zz);
                    float gap = 5f + 2.5f * Hash(i, j, 935);
                    bool near = false;
                    foreach (var t in taken) if (t.DistanceSquaredTo(p) < gap * gap) { near = true; break; }
                    foreach (var s in seeds) if (s.p.DistanceSquaredTo(p) < 9f) { near = true; break; }
                    if (near) continue;
                    taken.Add(p);
                    if (Hash(i, j, 936) < 0.5f) seeds.Add((p, 0.7f, InBoss(p)));
                }
        }
        if (boss >= 0)
        {
            var r = z.Rooms[boss];
            const float g = 4.5f;
            int m = (int)(r.R / g) + 1;
            for (int j = -m; j <= m; j++)
                for (int i = -m; i <= m; i++)
                {
                    var p = new Vector2(r.X + (i + (Hash(i, j, 937) - 0.5f) * 0.7f) * g, r.Z + (j + (Hash(i, j, 938) - 0.5f) * 0.7f) * g);
                    if (p.DistanceTo(new Vector2(r.X, r.Z)) > r.R * 0.95f || !Ok(p.X, p.Y, 1.0f, 1.2f)) continue;
                    bool near = false;
                    foreach (var s in seeds) if (s.p.DistanceSquaredTo(p) < 6.25f) { near = true; break; }
                    if (!near && Hash(i, j, 939) < 0.4f) seeds.Add((p, 1.15f, true));   // (round 8: 0.8 laid a pile every 4.5 m, an even sprinkle)
                }
        }

        // ---- the piles: a ground layer (old blood or a leaf drift), then 4-10 pieces round the seed ----
        int si = 0;
        foreach (var (sp, size, inBoss) in seeds)
        {
            si++;
            if (SetMode > 0 && SetIn(sp.X, sp.Y)) SetLitter(c, sp, si, Wall(c, sp.X, sp.Y));   // (round 10b: painted O3 / O2)
            if (Hash(si, 0, 941) < (inBoss ? 0.9f : 0.8f))
                AddDecal(c, b, PickDecal(Under, Hash(si, 0, 942)), sp.X + (Hash(si, 0, 943) - 0.5f), sp.Y + (Hash(si, 0, 944) - 0.5f), Hash(si, 0, 945) * Mathf.Tau, 0.9f + 0.3f * Hash(si, 0, 946));
            int n = 3 + (int)(4f * size * Hash(si, 0, 947));
            float sig = 0.45f + 0.35f * size;
            for (int k = 1; k <= n; k++)
            {
                float u1 = Mathf.Max(Hash(si, k, 948), 1e-4f), u2 = Hash(si, k, 949);
                float rad = sig * Mathf.Sqrt(-2f * Mathf.Log(u1));
                float x = sp.X + rad * Mathf.Cos(Mathf.Tau * u2), zz = sp.Y + rad * Mathf.Sin(Mathf.Tau * u2);
                if (!Ok(x, zz, 0.25f, 0.5f)) continue;
                var pd = PickDecal(inBoss ? InBossPile : InPile, Hash(si, k, 950));
                // (den r13 rooms) at most --den-lair-deer deer skulls in a lair, the rest small scatter (a bone)
                if (inBoss && pd.Kind == "deer_skull") { if (++lairDeer > LairDeerCap) { lairDeer--; pd = PickDecal(InPile, Hash(si, k, 957)); } else GD.Print($"[den-lair] deer skull {lairDeer}"); }
                AddDecal(c, b, pd, x, zz, Hash(si, k, 951) * Mathf.Tau, 0.9f + 0.25f * Hash(si, k, 952));
            }
        }

        DenOpen(c, b, Ok, boss);   // (den r17 D, R16 item 4) runners, debris clusters and the lair's rib arc (DungeonDress.Open.cs)

        // ---- the walls' feet and the open between: thinner, and no bones heaped there ----
        const float cell = 1.6f;
        int nc = (int)(z.Size / cell);
        for (int j = 0; j < nc; j++)
            for (int i = 0; i < nc; i++)
            {
                float u0 = Hash(i, j, 901), u1 = Hash(i, j, 902), u2 = Hash(i, j, 903), u3 = Hash(i, j, 904);
                float x = -z.Half + (i + u0) * cell, zz = -z.Half + (j + u1) * cell;
                float w = Wall(c, x, zz), h = Hole(c, x, zz);
                if (w < 0.15f || h < 0.5f || !Ok(x, zz, 0.15f, 0.5f)) continue;
                bool foot = w < 1.8f;
                float keep = (foot ? 0.3f : w > 5f ? 0.07f : 0.09f) * (foot ? 1f : OpenLitter);   // (round 8: the open scatter cut by more than half; den r15 D: the open floor was empty, x --den-open-litter)
                if (!foot) keep *= OpenKeep(x, zz);   // (den r17 D, R16 item 4) the open sprinkle thinned between the clusters (--den-open-between)
                if (u2 > keep) continue;
                var d = PickDecal(foot ? AtFoot : InOpen, u3);
                if (d.Kind == "bone" && !DenCaps.Take("openbone", new Vector2(x, zz), 2, 12f)) d = PickDecal(InOpen, Hash(i, j, 908));
                if (d.Metres.X * 0.5f > w + 0.4f && d.Kind != "root") continue;
                // (den r15 S) open-floor sticks read as cables: none within --den-stick-clear m of her spawn or the lair's middle, one per --den-stick-gap m
                if (d.Kind == "root" && !foot)
                {
                    var rp = new Vector2(x, zz);
                    float clr = SurvivorUnchained.Args.Num("den-stick-clear", 3.6f);
                    // (den r16 E, R15f item 9) a stick longer than --den-stick-max m (as laid: x its scale) is cut, and the clear radius counts from its nearest end (a long stick began 3.6 m out and reached her); 0 = as r15
                    float stickMax = SurvivorUnchained.Args.Num("den-stick-max", 2.4f);
                    float stickLen = d.Metres.X * (0.9f + 0.25f * Hash(i, j, 907) + (w > 3f ? 0.35f : 0f));
                    if (stickMax > 0f) { if (stickLen > stickMax) continue; clr += stickLen * 0.5f; }
                    if (z.Rooms.Count > 0 && rp.DistanceTo(new Vector2(z.Rooms[0].X, z.Rooms[0].Z)) < clr) continue;
                    if (boss >= 0 && rp.DistanceTo(new Vector2(z.Rooms[boss].X, z.Rooms[boss].Z)) < clr) continue;
                    if (!DenCaps.Take("openroot", rp, 1, SurvivorUnchained.Args.Num("den-stick-gap", 7f))) continue;
                }
                float yaw;
                if (d.Kind == "root")
                {
                    // a root crawls out from the wall: its long axis along the field's rise, its far end into the room
                    var g = Inward(x, zz);
                    yaw = Mathf.Atan2(g.Y, g.X) + (Hash(i, j, 905) - 0.5f) * 0.9f;
                }
                else yaw = Hash(i, j, 906) * Mathf.Tau;
                if (d.Kind == "root" && w > 3f) yaw = Hash(i, j, 909) * Mathf.Pi;   // (den r15 D: a root across the open floor lies any way)
                if (d.Kind == "root") yaw = StickYawFold(yaw);   // (den r17 D, R16 item 8) laid down the camera's depth a stick read as a standing rod: near level on screen
                AddDecal(c, b, d, x, zz, yaw, 0.9f + 0.25f * Hash(i, j, 907) + (d.Kind == "root" && w > 3f ? 0.35f : 0f), d.Kind == "bone");
            }

        // ---- the lair's floor: drag marks out from its piles, moss in the damp by the banks, drifts against them ----
        if (boss >= 0)
        {
            var r = z.Rooms[boss];
            var ctr = new Vector2(r.X, r.Z);
            int nd = 0, k = 0;
            foreach (var (sp, size, inBoss) in seeds)
            {
                k++;
                if (nd >= (int)SurvivorUnchained.Args.Num("den-drags", 0f) || Hash(k, 5, 953) < (inBoss ? 0.45f : 0.65f)) continue;   // (round 8: kills dragged in every room, not the lair only)
                var dir = (ctr - sp).LengthSquared() > 1f ? (ctr - sp).Normalized() : Vector2.Right;
                dir = dir.Rotated((Hash(k, 5, 954) - 0.5f) * 1.4f);
                var mid = sp + dir * 1.6f;
                if (!Ok(mid.X, mid.Y, 0.6f, 0.8f) || !Ok(sp.X + dir.X * 2.6f, sp.Y + dir.Y * 2.6f, 0.4f, 0.6f)) continue;
                AddDecal(c, b, PickDecal(new() { ["drag"] = 1f }, Hash(k, 5, 955)), mid.X, mid.Y, Mathf.Atan2(dir.Y, dir.X), 0.95f + 0.2f * Hash(k, 5, 956));
                nd++;
            }
            for (int q = 0; q < 26; q++)
            {
                float a = Hash(q, 9, 957) * Mathf.Tau, dd = Mathf.Sqrt(Hash(q, 9, 958)) * r.R * 0.98f;
                float x = r.X + Mathf.Cos(a) * dd, zz = r.Z + Mathf.Sin(a) * dd;
                float w = Wall(c, x, zz);
                if (!Ok(x, zz, 0.5f, 0.8f)) continue;
                string kind = w < 3.2f ? (Hash(q, 9, 959) < 0.55f ? "moss" : "leaves") : "leaves";   // (r11 judge: no moss alone on the open lair floor: it read as stickers)
                AddDecal(c, b, PickDecal(new() { [kind] = 1f }, Hash(q, 9, 960)), x, zz, Hash(q, 9, 961) * Mathf.Tau, 0.95f + 0.35f * Hash(q, 9, 962));
            }
        }
        c.Count["decal piles"] = seeds.Count;
        if (b.Count == 0) return;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        var nrm = new Vector3[b.V.Count];
        System.Array.Fill(nrm, Vector3.Up);
        arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = nrm;
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        if (b.K.Count == b.V.Count && b.K.Count > 0) arr[(int)Mesh.ArrayType.Color] = b.K.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_decal.gdshader") };
        mat.SetShaderParameter("atlas", GD.Load<Texture2D>("res://art/dungeon/den/decals.png"));
        mat.SetShaderParameter("field", DungeonFloor.Field(z));
        mat.SetShaderParameter("half_size", z.Half);
        mat.SetShaderParameter("step", z.Step);
        mat.SetShaderParameter("res", (float)z.Res);
        mat.SetShaderParameter("bone_k", SurvivorUnchained.Args.Num("den-bone", 0.3f));   // (den r17 D2, lead item 1) the decal bones down to den_room's lit bone value (.62 = d7e)
        mat.SetShaderParameter("bone_sat", SurvivorUnchained.Args.Num("den-bone-sat", 0.7f));
        mat.SetShaderParameter("bone_grade", BoneGrade);
        mat.SetShaderParameter("bone_knee", new Vector2(SurvivorUnchained.Args.Num("den-bone-knee", 0.55f), SurvivorUnchained.Args.Num("den-bone-share", 0.3f)));   // (den r17 D3) the bones' highlights rolled off above Oklab L .55 to 30 % of their rise (1 = none)
        if (SurvivorUnchained.Args.Num("den-bone-patch", 0f) > 0f) { var sh = (Shader)mat.Shader.Duplicate(); sh.Code = sh.Code.Replace("uniform float bone_k = 0.62;", "uniform float bone_k = 0.62; uniform float bone_sat = 1.0;").Replace("col *= mix(1.0, bone_k, smoothstep(0.3, 0.6, l) * (1.0 - smoothstep(0.25, 0.5, sat)));", "col *= mix(1.0, bone_k, smoothstep(0.3, 0.6, l) * (1.0 - smoothstep(0.25, 0.5, sat))); col = mix(col, mix(vec3(dot(col, vec3(0.299, 0.587, 0.114))), col, bone_sat), smoothstep(0.3, 0.6, l) * (1.0 - smoothstep(0.25, 0.5, sat)));"); mat.Shader = sh; GD.Print("TESTPATCH bone_sat " + sh.Code.Contains("bone_sat")); }
        c.Root.AddChild(new MeshInstance3D { Name = "Decals", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        foreach (var kv in b.Kinds) c.Count["decal " + kv.Key] = kv.Value;
    }

    /// <summary>One decal draped on the ground: its long axis at yaw, mirrored across it when that keeps the painted lit
    /// side (the cell's top) toward the light.</summary>
    static void AddDecal(Ctx c, DecalBuf b, Decal d, float x, float zz, float yaw, float scale, bool litterBone = false)
    {
        if (SetMode > 0 && SetDrops(d.Kind) && !(litterBone && d.Kind == "bone") && SetIn(x, zz)) return;   // (round 10b: the set's paintings carry the kills; den r15 D: a lone floor bone is litter, kept)
        // (den r15 D) the orange "bean" clumps were leaves in a pile: at most 3 within 1.5 m, each one then a flat leaf (scaled, turned)
        if (d.Kind == "leaves" && LairLeaves <= 0f && lairC is Vector2 lc && lc.DistanceTo(new Vector2(x, zz)) < lairR) return;   // (den r15 Q, judge r15 item 4) the lair's leaf decals read as orange bean clumps: none (the rooms' flat litter stays)
        if (d.Kind == "leaves") { if (!DenCaps.Take("leaf", new Vector2(x, zz), 3, 1.5f)) return; scale *= 1.25f; }
        // (den r14 floor, judge r13 item 4) per camera footprint at most 2 deer skulls and 3 rib cages (DenCaps, radius 9 m);
        // a refused one is small litter instead (a single bone, a leaf, a fur tuft), scaled .8-1.2 and turned by its hash
        // (den r16 E2, R15f item 7) an antlered skull is a large piece too (BigSkull) and the skull cap counts within SkullR, not 9 m
        if (d.Kind is "deer_skull" or "ribcage" && !((d.Kind == "deer_skull" && !BigSkull || DenCaps.Take("bigbone", new Vector2(x, zz), BigBoneCap, BigBoneR)) && DenCaps.Take(d.Kind == "deer_skull" ? "skull" : d.Kind, new Vector2(x, zz), d.Kind == "deer_skull" ? SkullCap : 3, d.Kind == "deer_skull" ? SkullR : 9f)))
        {
            float hu = Hash((int)(x * 10), (int)(zz * 10), 977);
            d = PickDecal(new() { ["bone"] = 1f, ["leaves"] = 1.2f, ["fur"] = 0.3f, ["pebbles"] = 0.3f }, hu);
            scale = 0.8f + 0.4f * Hash((int)(x * 10), (int)(zz * 10), 978);
        }
        var ax = new Vector2(Mathf.Cos(yaw), Mathf.Sin(yaw));
        var up = new Vector2(ax.Y, -ax.X);  // (the cell's top, before any mirror)
        if (up.Dot(decalLight) < 0) up = -up;
        // (the targets draw the den's litter larger than life, so it reads from the play camera: bones and kills x1.5)
        if (d.Kind is "bone" or "ribcage" or "wolf_skull" or "deer_skull" or "fur" or "hide") scale *= 1.5f;
        float W = d.Metres.X * scale, Hh = d.Metres.Y * scale;
        int nx = Mathf.Max(2, Mathf.CeilToInt(W / 0.4f) + 1), ny = Mathf.Max(2, Mathf.CeilToInt(Hh / 0.4f) + 1);
        int base0 = b.V.Count;
        // (the ground layers, blood, drags, drifts and moss, under the pieces laid on them)
        float lift = d.Kind is "blood" or "drag" or "drift" or "moss" ? 0.012f + 0.001f * (b.Count % 4) : 0.022f + 0.0015f * (b.Count % 8);
        for (int q = 0; q < ny; q++)
            for (int p = 0; p < nx; p++)
            {
                float s = (float)p / (nx - 1), t = (float)q / (ny - 1);  // (t 0 = the cell's top, the lit side)
                var w = new Vector2(x, zz) + ax * ((s - 0.5f) * W) + up * ((0.5f - t) * Hh);
                b.V.Add(new Vector3(w.X, H(c, w.X, w.Y) + lift, w.Y));
                if (BoneGrade.W > 0f) b.K.Add(new Color(d.Kind is "bone" or "arctusk" or "ribcage" or "wolf_skull" or "deer_skull" ? 1f : 0f, 0f, 0f, 1f));
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
