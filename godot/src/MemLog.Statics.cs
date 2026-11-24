using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Godot;

namespace SurvivorUnchained;

/// <summary>(dev, --mem-statics with --mem-strip; the tester lane, 24 Nov: town's texture monitor said 2318 MB, the tree reached
/// 1093) Once the place is taken apart and collected: every static field of the game's own types walked (its collections,
/// tuples, our own classes' fields, Godot objects' properties, a PackedScene's bundled resources), the textures each reaches
/// (unique per field; a texture two fields share is counted in both lines, once in the total), then what the tree still
/// reaches and the resource cache holds besides. What is left of the monitor is held by the engine or by no field we keep.</summary>
public partial class MemLog
{
    static void Statics(Node root)
    {
        var (tree, _) = Reach(root);
        var union = new Dictionary<Rid, long>();
        var rows = new List<(string F, long B, int N)>();
        foreach (var t in typeof(MemLog).Assembly.GetTypes())
        {
            if (t.ContainsGenericParameters) continue;
            foreach (var f in t.GetFields(BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly))
            {
                if (f.IsLiteral) continue;
                object? v; try { v = f.GetValue(null); } catch { continue; }
                if (v == null) continue;
                var mine = new Dictionary<Rid, long>();
                var seen = new HashSet<object>(ReferenceEqualityComparer.Instance);
                try { Hold(v, mine, seen, 0); } catch (Exception e) { GD.Print($"mem statics: {t.Name}.{f.Name} walk failed: {e.GetType().Name}"); }
                if (mine.Count == 0) continue;
                rows.Add(($"{t.FullName}.{f.Name}", mine.Values.Sum(), mine.Count));
                foreach (var kv in mine) union.TryAdd(kv.Key, kv.Value);
            }
        }
        static string Mb(long b) => $"{b / 1048576.0:0.0} MB";
        long treeOnly = tree.Where(kv => !union.ContainsKey(kv.Key)).Sum(kv => kv.Value.B);
        var known = union.Keys.Concat(tree.Keys).ToHashSet();
        var cache = new Dictionary<Rid, (long B, string What, string Where)>();
        CachedOnly(known, cache);
        GD.Print($"mem statics: the monitor says {Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576.0:0} MB; statics reach {union.Count} textures {Mb(union.Values.Sum())}; " +
                 $"the tree besides {Mb(treeOnly)}; the resource cache besides {cache.Count} {Mb(cache.Values.Sum(v => v.B))} (mips assumed)");
        foreach (var r in rows.OrderByDescending(r => r.B).Take(30)) GD.Print($"mem statics field: {Mb(r.B)} {r.N} {r.F}");
        foreach (var g in cache.Values.GroupBy(v => string.Join("/", v.Where[12..].Split('/')[..^1].Take(4))).OrderByDescending(g => g.Sum(v => v.B)).Take(15))
            GD.Print($"mem statics cache dir: {Mb(g.Sum(v => v.B))} {g.Count()} {g.Key}");
    }

    /// <summary>The textures an object reaches (bytes by RID, mips assumed), depth-capped.</summary>
    static void Hold(object? o, Dictionary<Rid, long> into, HashSet<object> seen, int depth)
    {
        if (o == null || depth > 8 || o is string || o.GetType().IsPrimitive || o.GetType().IsEnum) return;
        if (o is Variant vr) { if (vr.VariantType == Variant.Type.Object) Hold(vr.AsGodotObject(), into, seen, depth); return; }
        if (!o.GetType().IsValueType && !seen.Add(o)) return;
        if (o is GodotObject go)
        {
            if (!GodotObject.IsInstanceValid(go)) return;
            if (go is Node n) { foreach (var kv in Reach(n).Tex) into.TryAdd(kv.Key, kv.Value.B); return; }
            if (go is Texture tx) { AddTex(tx, into); return; }
            if (go is PackedScene ps && ps.Get("_bundled").AsGodotDictionary() is { } b && b.TryGetValue("variants", out var vs))
                foreach (var x in vs.AsGodotArray()) Hold(x, into, seen, depth + 1);
            foreach (var pr in go.GetPropertyList())
            {
                if ((Variant.Type)pr["type"].AsInt32() != Variant.Type.Object) continue;
                var name = pr["name"].AsString();
                if (name is "script" or "owner") continue;
                GodotObject? v; try { v = go.Get(name).AsGodotObject(); } catch { continue; }
                if (v is Resource) Hold(v, into, seen, depth + 1);
            }
            return;
        }
        if (o is IDictionary d) { foreach (DictionaryEntry e in d) { Hold(e.Key, into, seen, depth + 1); Hold(e.Value, into, seen, depth + 1); } return; }
        if (o is IEnumerable en) { foreach (var x in en) Hold(x, into, seen, depth + 1); return; }
        // our own classes and structs (and tuples): their instance fields
        var ty = o.GetType();
        string tn = ty.FullName ?? "";
        if (ty.Assembly != typeof(MemLog).Assembly && !new[] { "System.ValueTuple", "System.Tuple", "System.Lazy", "System.Collections.Generic.KeyValuePair" }.Any(tn.StartsWith)) return;
        for (var c = ty; c != null && c != typeof(object); c = c.BaseType)
            foreach (var f in c.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly))
            { object? v; try { v = f.GetValue(o); } catch { continue; } Hold(v, into, seen, depth + 1); }
    }

    static void AddTex(Texture t, Dictionary<Rid, long> into)
    {
        var rid = t.GetRid();
        if (!rid.IsValid || into.ContainsKey(rid)) return;
        int w = 0, h = 0, layers = 1; var fm = Image.Format.Rgba8;
        if (t is Texture2D t2) { w = t2.GetWidth(); h = t2.GetHeight(); }
        if (t is TextureLayered tl) { w = tl.GetWidth(); h = tl.GetHeight(); layers = tl.GetLayers(); fm = tl.GetFormat(); }
        if (t is Texture3D t3) { w = t3.GetWidth(); h = t3.GetHeight(); layers = t3.GetDepth(); fm = t3.GetFormat(); }
        try { fm = RenderingServer.TextureGetFormat(rid); } catch { }
        into[rid] = (long)(w * (double)h * layers * Bpp(fm) * 1.333);
    }
}
