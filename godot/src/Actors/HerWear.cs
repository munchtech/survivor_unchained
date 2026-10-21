using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.View;

/// <summary>
/// What she wears, piece by piece (docs/handoff/armor.md items 2 and 7): each visual slot's piece (Rpg.Wear.Look) from
/// its file onto her skeleton, as People.HerOutfit lays a whole outfit, her hold (HerJiggle) from the top she wears,
/// and her skin's tuck under them all: the largest of the worn pieces' tucks (armor_tuck/ID.bin, by her bind-pose
/// points), written a value a vertex into a float texture each body surface's skin reads by VERTEX_ID
/// (heroine_skin.gdshader, tuck_channel -2). Her gameplay model (HerLod): one calling's full set uses
/// its outfit file; a mixed look uses the gameplay and shadow meshes inside each piece's own file, if it has them.
/// --wear a.slot,b.slot,...: those pieces over her equipment, for a shot.
/// </summary>
public static class HerWear
{
    /// <summary>--wear: the pieces a shot puts on her over her equipment (none: her equipment's own).</summary>
    public static readonly string[]? Override = Args.Get("wear") is string w && w != "1"
        ? w.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries) : null;

    /// <summary>--helm 0|1: her show-helm toggle for the run (over CharacterData.Headgear).</summary>
    public static readonly bool? HelmOverride = Args.Get("helm") is string hm ? hm != "0" : null;

    /// <summary>--dye zone=#hex,zone=#hex: a dye on every piece she wears, over her items' own (zones: metal, trim, leather, cloth, thread).</summary>
    public static readonly Dictionary<string, string>? DyeOverride = Args.Get("dye") is string dy && dy != "1"
        ? dy.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).Select(x => x.Split('=', 2)).Where(x => x.Length == 2).ToDictionary(x => x[0].Trim(), x => x[1].Trim()) : null;

    const string Meta = "her_wear";
    static readonly Dictionary<string, PackedScene> scenes = new();
    static readonly Dictionary<string, (long Key, float T)[]> tucks = new();
    /// <summary>A body mesh's vertices, a surface's at a time, by their quantized bind position (Key).</summary>
    static readonly Dictionary<ulong, long[][]> bodyKeys = new();

    /// <summary>Her look from her equipment's pieces and --wear, over her calling's own (null: neither wears a piece).</summary>
    public static Dictionary<string, string>? LookFor(string calling, IReadOnlyDictionary<string, string>? worn, IReadOnlyCollection<string>? hide = null)
    {
        var ix = ArmorIndex.Shared;
        var w = new Dictionary<string, string>(worn ?? new Dictionary<string, string>());
        if (Override != null) foreach (var id in Override) w[ix.SlotOf(id)] = id;
        // (her show-helm toggle off: "head" stays empty, which needs the piece path even with nothing worn)
        if (HelmOverride is bool shown) hide = shown ? null : new[] { "head" };
        if (w.Count == 0 && Override == null && (hide == null || hide.Count == 0)) return null;
        var notes = new List<string>();
        var look = Wear.Look(w, calling, ix, notes, hide);
        foreach (var n in notes) GD.PushWarning(n);
        return look;
    }

    /// <summary>Key of a bind position (glTF metres x 1e5, rounded half to even as heroine_outfits.py's numpy does).</summary>
    static long Key(long x, long y, long z) => ((x + (1 << 20)) << 42) | ((y + (1 << 20)) << 21) | (z + (1 << 20));
    internal static long Key(Vector3 v) => Key((long)Math.Round(v.X * 1e5), (long)Math.Round(v.Y * 1e5), (long)Math.Round(v.Z * 1e5));

    /// <summary>The worn piece that hides her hair (its row says "hair": "hide"), or null.</summary>
    public static string? HairHider(IReadOnlyDictionary<string, string>? look)
    {
        if (look == null || !look.TryGetValue("head", out var id)) return null;
        return ArmorIndex.Shared.Find(id) is { Hair: "hide" } ? id : null;
    }

    /// <summary>A piece's dye: its item's (piece id -> zone -> hex), then --dye over it.</summary>
    static Dictionary<string, string>? DyeFor(string id, IReadOnlyDictionary<string, Dictionary<string, string>>? dyes)
    {
        Dictionary<string, string>? d = null;
        if (dyes != null && dyes.TryGetValue(id, out var own)) d = new Dictionary<string, string>(own);
        if (DyeOverride != null) { d ??= new(); foreach (var (z, h) in DyeOverride) d[z] = h; }
        return d;
    }

    /// <summary>Sets a dye on a mesh's material surfaces by their zone (People.OutfitMaterials tags each ShaderMaterial with its
    /// zone and kind): shaders/heroine_outfit.gdshaderinc recolors keeping the texture's variation; leather's "thread" zone sets
    /// its stitch thread; fur and sheer (zone cloth) take the dye on their tint, keeping its luma.</summary>
    internal static void DyeMesh(MeshInstance3D mi, IReadOnlyDictionary<string, string> dye)
    {
        for (int s = 0; s < mi.GetSurfaceOverrideMaterialCount(); s++)
        {
            if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m || !m.HasMeta("zone")) continue;
            var zone = (string)m.GetMeta("zone");
            bool outfit = m.HasMeta("kind");
            if (outfit && (int)m.GetMeta("kind") == 0 && dye.TryGetValue("thread", out var th)) m.SetShaderParameter("thread", new Color(th));
            if (!dye.TryGetValue(zone, out var hex)) continue;
            var c = new Color(hex);
            if (outfit)
            {
                m.SetShaderParameter("dye", c);
                m.SetShaderParameter("dye_amount", 1.0f);
                continue;
            }
            // (fur's shells and sheer: the tint toward the dye, at its own luma)
            var lin = c.SrgbToLinear();
            float ld = Math.Max(Luma(lin), 1e-3f);
            for (var pass = m; pass != null; pass = pass.NextPass as ShaderMaterial)
            {
                var old = pass.GetShaderParameter("tint");
                var t = old.VariantType == Variant.Type.Color ? old.AsColor() : Colors.White;
                float k = Luma(t.SrgbToLinear()) / ld;
                pass.SetShaderParameter("tint", new Color(Math.Min(lin.R * k, 1f), Math.Min(lin.G * k, 1f), Math.Min(lin.B * k, 1f), t.A).LinearToSrgb());
            }
        }
    }

    static float Luma(Color c) => 0.2126f * c.R + 0.7152f * c.G + 0.0722f * c.B;

    public static void Apply(People.Person p, string calling, IReadOnlyDictionary<string, string> look, IReadOnlyDictionary<string, Dictionary<string, string>>? dyes = null)
    {
        var ix = ArmorIndex.Shared;
        var rows = look.Values.Select(id => ix.Find(id)).Where(r => r != null).Select(r => r!).OrderBy(r => r.Layer).ToList();

        // What she wore before: every piece any index names (HerOutfit's too) and every one laid here.
        var names = new HashSet<string>(ix.Pieces.Values.SelectMany(r => r.Meshes).Select(m => m.Replace('.', '_')));
        p.Skeleton.GetNodeOrNull<HerLod>("HerLod")?.Remove();
        foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>().ToList())
        {
            if (!mi.HasMeta(Meta) && !names.Contains(mi.Name.ToString())) continue;
            p.Meshes.Remove(mi);
            p.Skeleton.RemoveChild(mi);
            mi.QueueFree();
        }

        var lodPairs = new List<(MeshInstance3D Full, MeshInstance3D Lod)>();
        var lodShadows = new List<(MeshInstance3D Shadow, MeshInstance3D Like)>();
        var laid = new List<MeshInstance3D>();

        // Each piece's meshes from its file (its outfit's, or its own), a file opened once.
        foreach (var g in rows.GroupBy(r => r.File ?? $"res://art/people/heroine_outfit_{r.Outfit}.gltf"))
        {
            if (!ResourceLoader.Exists(g.Key)) { GD.PushWarning($"wear: {g.Key} is not there ({string.Join(", ", g.Select(r => r.Id))})"); continue; }
            if (!scenes.TryGetValue(g.Key, out var ps)) scenes[g.Key] = ps = GD.Load<PackedScene>(g.Key);
            var scene = ps.Instantiate<Node3D>();
            var found = scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>()
                .GroupBy(m => m.Name.ToString()).ToDictionary(x => x.Key, x => x.First());
            foreach (var r in g)
            {
                MeshInstance3D? anyFull = null;
                foreach (var mn in r.Meshes)
                {
                    if (!found.TryGetValue(mn.Replace('.', '_'), out var mi) && !found.TryGetValue(mn, out mi))
                    {
                        GD.PushWarning($"wear: {r.Id}'s mesh {mn} is not in {g.Key}");
                        continue;
                    }
                    WearPiece(p, mi, r.Id);
                    anyFull ??= mi;
                    laid.Add(mi);
                    var dye = DyeFor(r.Id, dyes);
                    if (dye != null) DyeMesh(mi, dye);
                    var mat = mn[(mn.LastIndexOf('.') + 1)..];
                    if (found.TryGetValue($"{r.Id}_lod1_{mat}", out var lm) && lm != mi && lm.GetParent() != null)
                    {
                        Lay(p, lm, r.Id);
                        People.OutfitMaterials(lm);
                        if (dye != null) DyeMesh(lm, dye);
                        lodPairs.Add((mi, lm));
                    }
                }
                if (anyFull != null && found.TryGetValue($"{r.Id}_shadow", out var sm) && sm.GetParent() != null)
                {
                    Lay(p, sm, r.Id);
                    lodShadows.Add((sm, anyFull));
                }
            }
            scene.Free();
        }

        // Her hold, from the top she wears (plate holds her: People.HerOutfit).
        var hold = look.TryGetValue("top", out var top) ? ix.Find(top)?.Hold : null;
        if (p.Skeleton.GetNodeOrNull<HerJiggle>("HerJiggle") is HerJiggle jig)
        {
            jig.Amount = (float)(hold?.Amount ?? 1);
            jig.Squash = (float)(hold?.Squash ?? 1);
        }

        bool full = Wear.IsCallingSet(look, calling, ix);
        bool lodFile = full && ResourceLoader.Exists($"res://art/people/heroine_outfit_{calling}_lod.gltf");
        if (lodFile)
        {
            // (her gameplay body shares her skin's materials and its own vertices have no tuck map: one calling's
            // full set keeps that calling's channel, as HerOutfit does)
            int ch = People.OutfitChannel(calling);
            foreach (var mi in p.Skeleton.GetChildren().OfType<MeshInstance3D>().Where(People.TuckBody))
                for (int s = 0; s < mi.GetSurfaceOverrideMaterialCount(); s++)
                    if (People.IsSkin(mi.GetSurfaceOverrideMaterial(s))) ((ShaderMaterial)mi.GetSurfaceOverrideMaterial(s)).SetShaderParameter("tuck_channel", ch);
        }
        else TuckMap(p, rows);
        if (full) HerLod.Attach(p, calling);
        if (lodPairs.Count > 0 || lodShadows.Count > 0)
        {
            var lod = HerLod.For(p);
            if (lod == null)
            {
                foreach (var (_, l) in lodPairs) l.QueueFree();
                foreach (var (s, _) in lodShadows) s.QueueFree();
            }
            else
            {
                foreach (var (f, l) in lodPairs) lod.AddPiece(f, l);
                foreach (var (s, like) in lodShadows) lod.AddShadow(s, like);
            }
        }
        // What draws of it at the play camera, one mesh a material (HerLod.Merge).
        HerLod.For(p)?.Merge(laid);
        GD.Print($"her wear: {calling}, {string.Join(" ", look.OrderBy(kv => kv.Key).Select(kv => kv.Value))}" + (full ? " (her calling's set)" : " (no gameplay model: mixed)"));
    }

    /// <summary>A piece's full mesh onto a person's skeleton, drawn as what it is made of (her pieces, and a Marionette
    /// package's: NpcPackage).</summary>
    internal static void WearPiece(People.Person p, MeshInstance3D mi, string id)
    {
        Lay(p, mi, id);
        p.Meshes.Add(mi);
        People.Fur(mi);
        People.OutfitMaterials(mi);
    }

    /// <summary>A piece's gameplay or shadow mesh, onto her skeleton like its full meshes (but not in her mesh list).</summary>
    internal static void Lay(People.Person p, MeshInstance3D mi, string id)
    {
        mi.GetParent().RemoveChild(mi);
        mi.Owner = null;
        p.Skeleton.AddChild(mi);
        mi.Skeleton = "..";
        mi.Layers = 2;
        mi.SetMeta(Meta, id);
    }

    /// <summary>The worn pieces' tuck of her skin, the largest at each of her points, into each body surface's tuck_map.</summary>
    static void TuckMap(People.Person p, List<ArmorPiece> rows)
    {
        var at = new Dictionary<long, float>();
        foreach (var r in rows)
        {
            if (r.Tuck == null) continue;
            foreach (var (k, t) in Records($"res://art/{r.Dir}/{r.Tuck}"))
                if (!at.TryGetValue(k, out var o) || t > o) at[k] = t;
        }
        var bodies = p.Skeleton.GetChildren().OfType<MeshInstance3D>().Where(People.TuckBody).ToList();
        var seen = new HashSet<long>();
        foreach (var mi in bodies)
        {
            var keys = KeysOf(mi.Mesh);
            for (int s = 0; s < keys.Length && s < mi.GetSurfaceOverrideMaterialCount(); s++)
            {
                if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m || !People.IsSkin(m)) continue;
                var ks = keys[s];
                var v = new float[ks.Length];
                bool any = false;
                for (int i = 0; i < ks.Length; i++)
                    if (at.TryGetValue(ks[i], out var t))
                    {
                        // (as her vertex colours hold a channel's mark: eight bits)
                        v[i] = MathF.Round(Math.Clamp(t, 0f, 1f) * 255f) / 255f;
                        any |= v[i] > 0;
                        seen.Add(ks[i]);
                    }
                if (!any) { m.SetShaderParameter("tuck_channel", -1); continue; }
                int w = Math.Min(ks.Length, 4096), h = (ks.Length + w - 1) / w;
                var bytes = new byte[w * h * 4];
                Buffer.BlockCopy(v, 0, bytes, 0, v.Length * 4);
                var img = Image.CreateFromData(w, h, false, Image.Format.Rf, bytes);
                m.SetShaderParameter("tuck_map", ImageTexture.CreateFromImage(img));
                m.SetShaderParameter("tuck_map_width", w);
                m.SetShaderParameter("tuck_channel", -2);
            }
        }
        int miss = at.Keys.Count(k => !seen.Contains(k));
        if (miss > 0) GD.PushWarning($"wear: {miss} of {at.Count} tuck points are on none of her body's vertices (a stale tuck: rebuild the pieces against her body)");
    }

    /// <summary>The bind positions a tuck-format record file lists (NpcPackage's hidden skin).</summary>
    internal static IEnumerable<long> Points(string path) => Records(path).Select(r => r.Item1);

    static (long, float)[] Records(string path)
    {
        if (tucks.TryGetValue(path, out var r)) return r;
        var b = FileAccess.GetFileAsBytes(path);
        if (b.Length < 4) { GD.PushWarning($"wear: no tuck at {path}"); return tucks[path] = Array.Empty<(long, float)>(); }
        int n = BitConverter.ToInt32(b, 0);
        r = new (long, float)[n];
        for (int i = 0; i < n; i++)
        {
            int o = 4 + i * 16;
            r[i] = (Key(BitConverter.ToInt32(b, o), BitConverter.ToInt32(b, o + 4), BitConverter.ToInt32(b, o + 8)), BitConverter.ToSingle(b, o + 12));
        }
        return tucks[path] = r;
    }

    static long[][] KeysOf(Mesh mesh)
    {
        if (bodyKeys.TryGetValue(mesh.GetInstanceId(), out var k)) return k;
        k = new long[mesh.GetSurfaceCount()][];
        for (int s = 0; s < k.Length; s++)
        {
            var vs = mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            k[s] = vs.Select(Key).ToArray();
        }
        return bodyKeys[mesh.GetInstanceId()] = k;
    }
}
