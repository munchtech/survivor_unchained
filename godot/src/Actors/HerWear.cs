using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.View;

/// <summary>
/// What she wears, piece by piece (docs/handoff/armor.md items 2 and 7): each visual slot's piece (Rpg.Wear.Look) from
/// its file onto her skeleton, as People.HerOutfit lays a whole outfit, her hold (HerJiggle) from the top she wears,
/// and her skin's tuck under them all: the largest of the worn pieces' tucks (armor_tuck/ID.bin, by her bind-pose
/// points), written a value a vertex into a float texture each body surface's skin reads by VERTEX_ID
/// (heroine_skin.gdshader, tuck_channel -2). And each piece's garment tuck (Rpg.GarmentTuck, docs/armor/PIECE_SCHEMA.md
/// "Garment tuck"): laid down under the pieces of other outfits outside it, new meshes before her gameplay model
/// and her play-camera merge take them. Her gameplay model (HerLod): one calling's full set uses
/// its outfit file; a mixed look uses the gameplay and shadow meshes inside each piece's own file, if it has them.
/// --wear a.slot,b.slot,...: those pieces over her equipment, for a shot.
/// </summary>
public static class HerWear
{
    /// <summary>--wear: the pieces a shot puts on her over her equipment (none: her equipment's own).</summary>
    public static readonly string[]? Override = Args.Get("wear") is string w && w != "1"
        ? w.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries) : null;

    /// <summary>--helm 0|1: her show-helm toggle for the run (over CharacterData.Headgear).</summary>
    static readonly string[]? HideSlots = Args.Get("hide-slots") is string hs && hs != "1"
        ? (hs == "all" ? Wear.VisualSlots : hs.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)) : null;
    public static readonly bool? HelmOverride = Args.Get("helm") is string hm ? hm != "0" : null;

    /// <summary>--dye zone=#hex,zone=#hex: a dye on every piece she wears, over her items' own (zones: metal, trim, leather, cloth, thread).</summary>
    public static readonly Dictionary<string, string>? DyeOverride = Args.Get("dye") is string dy && dy != "1"
        ? dy.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).Select(x => x.Split('=', 2)).Where(x => x.Length == 2).ToDictionary(x => x[0].Trim(), x => x[1].Trim()) : null;
    /// <summary>--tuck-scale K: every worn piece's tuck of her skin times K (0: none), for pictures that test what the
    /// tuck does at her skin's visible edges (face 32, her left neck's step under the arcanist's collar).</summary>
    static readonly float TuckScale = Args.Has("tuck-scale") ? (float)Args.Num("tuck-scale", 1f) : 1f;

    const string Meta = "her_wear";
    static readonly bool Prof = Args.Get("tuck-prof") != null;
    /// <summary>--tuck-dump PATH: each laid mesh's vertices, bones, weights and index (and its skin's binds) into PATH, an
    /// Apply after another (a check that a change to the tuck lays the same).</summary>
    static readonly string? DumpPath = Args.Get("tuck-dump") is string dp && dp != "1" ? dp : null;
    static System.IO.BinaryWriter? dump;
    static int dumpApply;
    static readonly Dictionary<string, PackedScene> scenes = new();
    static readonly Dictionary<string, (long Key, float T)[]> tucks = new();
    /// <summary>A body mesh's vertices, a surface's at a time, by their quantized bind position (Key).</summary>
    static readonly Dictionary<ulong, long[][]> bodyKeys = new();
    /// <summary>Her body's points for the garment tuck, by her body meshes.</summary>
    static readonly Dictionary<string, SkinPoints> skinPoints = new();
    /// <summary>A piece mesh laid under what covers it (by the source mesh and the pieces over it), and her points it
    /// lies on with their values (her skin is tucked under it as much).</summary>
    static readonly Dictionary<(ulong, string), (ArrayMesh Mesh, (int Point, float T)[] Under, Skin? Skin)> laidMeshes = new();

    /// <summary>--standin 0: a calling's stood-in rows ignored at load (her outfit file as before; for an ABAB).</summary>
    static readonly bool StandIns = Args.Get("standin") != "0";

    /// <summary>Her look from her equipment's pieces and --wear, over her calling's own (null: neither wears a piece).</summary>
    public static Dictionary<string, string>? LookFor(string calling, IReadOnlyDictionary<string, string>? worn, IReadOnlyCollection<string>? hide = null)
    {
        var ix = ArmorIndex.Shared;
        var w = new Dictionary<string, string>(worn ?? new Dictionary<string, string>());
        if (Override != null) foreach (var id in Override) w[ix.SlotOf(id)] = id;
        // (her show-helm toggle off: "head" stays empty, which needs the piece path even with nothing worn)
        if (HelmOverride is bool shown) hide = shown ? null : new[] { "head" };
        // (--hide-slots a,b|all: those slots empty for the run: pictures of her bare body under a garment, same camera)
        if (HideSlots != null) hide = HideSlots;
        // (a calling whose index row is stood in for (a row's "replaces") takes the piece path too, or her outfit file would
        // draw the replaced piece; --standin 0: the outfit file as before, for an ABAB)
        bool standIn = StandIns && ix.Calling(calling).Any(kv => ix.Find(kv.Value) is { } r && r.Outfit != calling);
        if (w.Count == 0 && Override == null && (hide == null || hide.Count == 0) && !standIn) return null;
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
        // (a gold plate dye would swallow the gold trim: Wear.TrimUnderGold darkens the trim to bronze; env GOLD_TRIM="#rrggbb:metal" tries another)
        dye = Wear.TrimUnderGold(dye);
        if (dye.TryGetValue("trim", out var gt) && gt == Wear.GoldTrimBronze && System.Environment.GetEnvironmentVariable("GOLD_TRIM") is { Length: > 0 } trial)
            dye = new Dictionary<string, string>(dye) { ["trim"] = trial };
        for (int s = 0; s < mi.GetSurfaceOverrideMaterialCount(); s++)
        {
            if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m || !m.HasMeta("zone")) continue;
            var zone = (string)m.GetMeta("zone");
            bool outfit = m.HasMeta("kind");
            if (outfit && (int)m.GetMeta("kind") == 0 && dye.TryGetValue("thread", out var th)) m.SetShaderParameter("thread", new Color(Wear.DyeFinish(th).Hex));
            if (!dye.TryGetValue(zone, out var hex))
            {
                // (no dye in this zone: back to the built finish)
                if (outfit && (int)m.GetMeta("kind") == 1 && m.HasMeta("finish0")) m.SetShaderParameter("finish", (int)m.GetMeta("finish0"));
                continue;
            }
            var (dyeHex, isMetal) = Wear.DyeFinish(hex);
            var c = new Color(dyeHex);
            if (outfit)
            {
                // enamel and dye_paint metal (meta finish0 = the built finish): a metal dye gives dyed metal (finish 3: brushed, no oxide); a colour dye paints it (finish 2)
                if ((int)m.GetMeta("kind") == 1)
                {
                    if (!m.HasMeta("finish0") && m.GetShaderParameter("finish").AsInt32() == 2) m.SetMeta("finish0", 2);
                    if (m.HasMeta("finish0")) m.SetShaderParameter("finish", isMetal ? 3 : 2);
                }
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
        // (--tuck-weights 0: laid pieces keep their own bone weights; pictures that tell a weights mark from a lay mark)
        if (Args.Get("tuck-weights") == "0") GarmentTuck.Weights = false;
        // (her worn shape under the reaver's top: People.WornShape)
        People.WornShape(p, "reaver", look.TryGetValue("top", out var wornTop) && wornTop == "reaver.top");
        var steps = ApplySteps(p, calling, look, dyes).GetEnumerator();
        if (Live)
        {
            // (a live swap: up to the first lay here, the rest over the next frames)
            // (nothing more this frame: her new figure is being made in it)
            pending[p] = new Pending(steps);
            return;
        }
        while (steps.MoveNext()) steps.Current?.Wait();
    }

    /// <summary>True while a live swap makes her new figure (WorldScene.SetLoadout): Apply then leaves the garment tuck's
    /// work, and what follows it, to Pump over the next frames (the lay on a worker), and Busy says when she is dressed.
    /// Her first figure, and every other, is dressed at once.</summary>
    /// (Per thread: her cinematic double, made on a worker meanwhile, is dressed at once: Game.DoubleAhead.)
    [System.ThreadStatic] public static bool Live;
    /// <summary>A live swap's dressing still going on (Game.DoubleAhead waits for it: the caches here are shared).</summary>
    public static bool Dressing => pending.Count > 0;
    /// <summary>The main thread's share of a frame Pump may spend on dressing her (a step started runs to its end).</summary>
    const double PumpBudgetMs = 6;
    static readonly Dictionary<People.Person, Pending> pending = new();

    /// <summary>Apply's steps for one figure, run a few a frame.</summary>
    sealed class Pending(IEnumerator<System.Threading.Tasks.Task?> steps)
    {
        public bool Done;
        public double MainMs, MaxMs;
        public int Frames;
        System.Threading.Tasks.Task? wait;

        public void Step(double budgetMs)
        {
            var c = System.Diagnostics.Stopwatch.StartNew();
            Frames++;
            while (true)
            {
                if (wait != null)
                {
                    if (!wait.IsCompleted) break;
                    if (wait.IsFaulted)
                    {
                        GD.PushError($"wear: the garment tuck failed: {wait.Exception?.InnerException}");
                        Done = true;
                        break;
                    }
                    wait = null;
                }
                if (!steps.MoveNext()) { Done = true; break; }
                wait = steps.Current;
                if (c.Elapsed.TotalMilliseconds >= budgetMs) break;
            }
            double ms = c.Elapsed.TotalMilliseconds;
            MainMs += ms;
            MaxMs = Math.Max(MaxMs, ms);
        }
    }

    /// <summary>True while her figure p is still being dressed (a live swap: show the one before till then).</summary>
    public static bool Busy(People.Person p) => pending.ContainsKey(p);

    /// <summary>Her figure p's dressing dropped (a newer swap came first: the latest wins); a lay on a worker finishes
    /// unseen and nothing of it is used.</summary>
    public static void Cancel(People.Person p) => pending.Remove(p);

    /// <summary>Each frame (the main thread): the figures being dressed go on.</summary>
    public static void Pump()
    {
        // (not while a figure is made on a worker, Game.DoubleAhead: the next frame)
        if (pending.Count == 0 || !System.Threading.Monitor.TryEnter(People.BuildLock)) return;
        try
        {
            foreach (var (p, job) in pending.ToList())
            {
                job.Step(PumpBudgetMs);
                if (!job.Done) continue;
                pending.Remove(p);
                GD.Print($"her wear: live swap dressed over {job.Frames} frames, main thread {job.MainMs:F1} ms (at most {job.MaxMs:F1} ms a frame)");
            }
        }
        finally { System.Threading.Monitor.Exit(People.BuildLock); }
    }

    static IEnumerable<System.Threading.Tasks.Task?> ApplySteps(People.Person p, string calling, IReadOnlyDictionary<string, string> look, IReadOnlyDictionary<string, Dictionary<string, string>>? dyes)
    {
        var ap = System.Diagnostics.Stopwatch.StartNew();
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
        var ofPiece = new Dictionary<string, List<MeshInstance3D>>();
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
                    Of(ofPiece, r.Id).Add(mi);
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
                        Of(ofPiece, r.Id).Add(lm);
                    }
                }
                if (anyFull != null && found.TryGetValue($"{r.Id}_shadow", out var sm) && sm.GetParent() != null)
                {
                    Lay(p, sm, r.Id);
                    lodShadows.Add((sm, anyFull));
                    Of(ofPiece, r.Id).Add(sm);
                }
            }
            scene.Free();
        }

        if (Prof) GD.Print($"wear prof: pieces {ap.Elapsed.TotalMilliseconds:F1} ms");
        // Each piece laid under the other outfits' pieces outside it (one calling's full set: none).
        var clock = System.Diagnostics.Stopwatch.StartNew();
        var tuck = new TuckOut();
        foreach (var t in GarmentTucks(p, rows, ofPiece, tuck)) yield return t;
        var under = tuck.Under;
        int laidN = tuck.Laid;
        double laidMs = clock.Elapsed.TotalMilliseconds;

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
        else TuckMap(p, rows, under);
        if (Prof) GD.Print($"wear prof: tuck map {ap.Elapsed.TotalMilliseconds:F1} ms");
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
        if (Prof) GD.Print($"wear prof: lod {ap.Elapsed.TotalMilliseconds:F1} ms");
        if (HerLod.For(p) is { } hl) foreach (var mt in hl.MergeSteps(laid)) yield return mt;
        if (Prof) GD.Print($"wear prof: merge {ap.Elapsed.TotalMilliseconds:F1} ms");
        GD.Print($"her wear: {calling}, {string.Join(" ", look.OrderBy(kv => kv.Key).Select(kv => kv.Value))}" + (full ? " (her calling's set)" : " (no gameplay model: mixed)")
            + (laidN > 0 ? $", garment tuck: {laidN} meshes laid in {laidMs:F1} ms (worker {tuck.WorkerMs:F1} ms)" : ""));
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

    static List<MeshInstance3D> Of(Dictionary<string, List<MeshInstance3D>> d, string id) =>
        d.TryGetValue(id, out var l) ? l : d[id] = new List<MeshInstance3D>();

    /// <summary>The garment tuck: each worn piece's meshes laid down under the worn pieces over it (Rpg.GarmentTuck.Over:
    /// later in its slot order, of another outfit), new meshes in their place; `o` gets her points under laid pieces with
    /// their values (her skin goes in as far there, never removed by it). Steps (Apply): a piece's meshes are read here,
    /// laid on a worker (the task yielded), and made into meshes here, a piece after the one before it is done (an outer
    /// piece's weights are read from its meshes as they are then, laid or not).</summary>
    static IEnumerable<System.Threading.Tasks.Task?> GarmentTucks(People.Person p, List<ArmorPiece> rows, Dictionary<string, List<MeshInstance3D>> meshes, TuckOut o)
    {
        dumpApply++;
        SkinPoints? sp = null;
        var outers = new Dictionary<string, OuterWeights?>();   // (by the meshes in it and how: one piece's may serve another)
        foreach (var a in rows)
        {
            var over = rows.Where(b => GarmentTuck.Over(b, a)).ToList();
            if (over.Count == 0 || !meshes.TryGetValue(a.Id, out var mis)) continue;
            var c0 = System.Diagnostics.Stopwatch.StartNew();
            sp ??= SkinOf(p);
            if (Prof) GD.Print($"garment tuck: skin {c0.Elapsed.TotalMilliseconds:F1} ms");
            if (sp == null) yield break;
            var sig = string.Join("+", over.Select(b => b.Id).OrderBy(x => x));
            // (a piece's meshes are all laid before under these, or none are: one key; one remembered as moving nothing does nothing)
            var miss = new List<MeshInstance3D>();
            foreach (var mi in mis)
            {
                if (mi.Mesh is not ArrayMesh src) continue;
                if (laidMeshes.TryGetValue((src.GetInstanceId(), sig), out var got)) Use(a, mi, got, sp, o);
                else miss.Add(mi);
            }
            if (miss.Count == 0) continue;
            var feet = over.Select(Footprint).ToList();   // (feet: a footprint's records, loaded once)
            // (no footprint on her: the field is none, as Field finds)
            if (FootBox(sp, feet) is not Aabb pre) continue;
            // (the outer pieces' weights, by the outer meshes as they are now; a laid vertex moves at most 2 Reach + Smooth,
            // and looks Reach further: an outer mesh past that has no vertex any of this piece's can take)
            OuterWeights? ow = null;
            if (GarmentTuck.Weights && miss.Any(m => m.Skin != null))
            {
                var cw = System.Diagnostics.Stopwatch.StartNew();
                Aabb? region = null;
                foreach (var m in mis)
                    if (m.Mesh != null)
                    {
                        var bx = m.Transform * m.Mesh.GetAabb();
                        region = region == null ? bx : region.Value.Merge(bx);
                    }
                ow = region == null ? null : OuterOf(p, over.Select(b => b.Id).Where(meshes.ContainsKey).SelectMany(id => meshes[id]),
                    region.Value.Grow(3 * GarmentTuck.Reach + GarmentTuck.Smooth + 0.02f), outers);
                if (Prof) GD.Print($"garment tuck:   outer {ow?.Count ?? 0} verts read {cw.Elapsed.TotalMilliseconds:F1} ms");
                yield return null;
            }
            var cr = System.Diagnostics.Stopwatch.StartNew();
            var jobs = new List<LayMesh>();
            foreach (var mi in miss)
            {
                jobs.Add(ReadLay(mi, sig, ow != null));
                yield return null;
            }
            if (Prof) GD.Print($"garment tuck: {a.Id} {jobs.Count} meshes read {cr.Elapsed.TotalMilliseconds:F1} ms");
            var id = a.Id;
            var s0 = sp;
            yield return System.Threading.Tasks.Task.Run(() =>
            {
                var cc = System.Diagnostics.Stopwatch.StartNew();
                ComputeLays(id, jobs, s0, feet, pre, ow);
                lock (o) o.WorkerMs += cc.Elapsed.TotalMilliseconds;
            });
            foreach (var j in jobs)
            {
                if (j.State == 0) break;   // (the field came out none: the rest left as they are, unremembered)
                if (j.State == 1) { laidMeshes[j.Key] = (null!, Array.Empty<(int, float)>(), null); continue; }
                var cb = System.Diagnostics.Stopwatch.StartNew();
                var got = BuildLay(j);
                laidMeshes[j.Key] = got;
                Use(a, j.Mi, got, sp, o);
                if (Prof) GD.Print($"garment tuck: {a.Id} {j.Mi.Name} built {cb.Elapsed.TotalMilliseconds:F1} ms");
                yield return null;
            }
        }
    }

    /// <summary>What the garment tuck gives Apply.</summary>
    sealed class TuckOut
    {
        public int Laid;
        public Dictionary<long, float>? Under;
        public double WorkerMs;
    }

    /// <summary>A laid mesh (or one remembered as moving nothing) on its instance, and her points under it into o.</summary>
    static void Use(ArmorPiece a, MeshInstance3D mi, (ArrayMesh Mesh, (int Point, float T)[] Under, Skin? Skin) got, SkinPoints sp, TuckOut o)
    {
        if (got.Mesh == null) return;
        mi.Mesh = got.Mesh;
        if (got.Skin != null) mi.Skin = got.Skin;   // (mi is a fresh instance each Apply: nothing to restore)
        if (DumpPath != null) Dump(a.Id, mi);
        o.Laid++;
        o.Under ??= new Dictionary<long, float>();
        foreach (var (i, t) in got.Under)
        {
            long k = sp.Keys[i];
            float v = MathF.Min(t, 0.98f);
            if (!o.Under.TryGetValue(k, out var old) || v > old) o.Under[k] = v;
        }
    }

    /// <summary>One laid mesh into --tuck-dump.</summary>
    static void Dump(string id, MeshInstance3D mi)
    {
        dump ??= new System.IO.BinaryWriter(System.IO.File.Create(DumpPath!));
        var w = dump;
        var am = (ArrayMesh)mi.Mesh;
        w.Write(dumpApply); w.Write(id); w.Write(mi.Name.ToString()); w.Write(am.GetSurfaceCount());
        for (int s = 0; s < am.GetSurfaceCount(); s++)
        {
            var arr = am.SurfaceGetArrays(s);
            var vs = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            w.Write(vs.Length);
            foreach (var v in vs) { w.Write(v.X); w.Write(v.Y); w.Write(v.Z); }
            var bj = arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil ? Array.Empty<int>() : arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
            var bw = arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil ? Array.Empty<float>() : arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            var ix = arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? Array.Empty<int>() : arr[(int)Mesh.ArrayType.Index].AsInt32Array();
            w.Write(bj.Length); foreach (var x in bj) w.Write(x);
            w.Write(bw.Length); foreach (var x in bw) w.Write(x);
            w.Write(ix.Length); foreach (var x in ix) w.Write(x);
        }
        var sk = mi.Skin;
        int bc = sk?.GetBindCount() ?? 0;
        w.Write(bc);
        for (int i = 0; i < bc; i++) w.Write(sk!.GetBindName(i).ToString());
        w.Flush();
    }

    /// <summary>The outer pieces' rest vertices in her skeleton's space with their bone weights, on a 10 mm grid (dense over
    /// their box; a cell's vertices in the order they were added, so the nearest is the first of equals as it always was).</summary>
    sealed class OuterWeights
    {
        const float Cell = 0.01f;
        Vector3[] pos = new Vector3[4096];
        int[] bones = new int[4096 * 8];        // 8 per vertex, ids into names (-1: none)
        float[] weights = new float[4096 * 8];  // 8 per vertex
        int n;
        readonly List<string> names = new();
        readonly List<Transform3D> poses = new();
        readonly Dictionary<string, int> nameId = new();
        // (the grid: cells gx0..gx0+nx-1 etc.; a cell's vertices order[start[c]..start[c + 1]]; sparse: a cell's slot by key)
        int gx0, gy0, gz0, nx, ny, nz;
        int[] start = Array.Empty<int>(), order = Array.Empty<int>();
        float[] sx = Array.Empty<float>(), sy = Array.Empty<float>(), sz = Array.Empty<float>();   // (positions in cell order)
        Dictionary<long, int>? sparse;

        public int Count => n;

        /// <summary>A source mesh's skinned triangle surfaces (vertices, bones, weights, bones a vertex), read once.</summary>
        static readonly Dictionary<ulong, (Vector3[] V, int[] J, float[] W, int St)[]> raw = new();

        static (Vector3[] V, int[] J, float[] W, int St)[] Raw(ArrayMesh am)
        {
            ulong id = am.GetInstanceId();
            if (raw.TryGetValue(id, out var r)) return r;
            var l = new List<(Vector3[], int[], float[], int)>();
            for (int s = 0; s < am.GetSurfaceCount(); s++)
            {
                if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) continue;
                var arr = am.SurfaceGetArrays(s);
                if (arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil) continue;
                var vs = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var bj = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                var bw = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                int st = vs.Length == 0 ? 0 : bj.Length / vs.Length;
                if (st == 0) continue;
                l.Add((vs, bj, bw, st));
            }
            if (raw.Count > 256) raw.Clear();
            return raw[id] = l.ToArray();
        }

        internal static string BindName(Skin skin, int i, Skeleton3D? skel)
        {
            var n = skin.GetBindName(i).ToString();
            if (n.Length == 0 && skel != null && skin.GetBindBone(i) is var bb and >= 0) n = skel.GetBoneName(bb);
            return n;
        }

        /// <summary>b's vertices and binds (verts false: its binds alone, so a bind's pose is still the first piece's).</summary>
        [MethodImpl(MethodImplOptions.AggressiveOptimization)]
        public void Add(MeshInstance3D b, Skeleton3D? skel, bool verts = true)
        {
            if (b.Mesh is not ArrayMesh am || b.Skin is not { } skin) return;
            var map = new int[skin.GetBindCount()];
            for (int i = 0; i < map.Length; i++)
            {
                var nm = BindName(skin, i, skel);
                if (nm.Length == 0) { map[i] = -1; continue; }
                if (!nameId.TryGetValue(nm, out var id)) { nameId[nm] = id = names.Count; names.Add(nm); poses.Add(skin.GetBindPose(i)); }
                map[i] = id;
            }
            if (!verts) return;
            var xf = b.Transform;
            foreach (var (vs, bj, bw, st) in Raw(am))
            {
                if (n + vs.Length > pos.Length)
                {
                    int cap = Math.Max(pos.Length * 2, n + vs.Length);
                    Array.Resize(ref pos, cap);
                    Array.Resize(ref bones, cap * 8);
                    Array.Resize(ref weights, cap * 8);
                }
                // (each vertex alone: in parallel)
                int n0 = n;
                var (P, B, W) = (pos, bones, weights);
                System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, vs.Length, 4096), rg =>
                {
                    for (int i = rg.Item1; i < rg.Item2; i++)
                    {
                        int o = n0 + i;
                        P[o] = xf * vs[i];
                        for (int k = 0; k < 8; k++)
                        {
                            bool has = k < st && bj[i * st + k] >= 0 && bj[i * st + k] < map.Length;
                            B[o * 8 + k] = has ? map[bj[i * st + k]] : -1;
                            W[o * 8 + k] = has ? bw[i * st + k] : 0f;
                        }
                    }
                });
                n += vs.Length;
            }
        }

        static int CellOf(float x) => (int)MathF.Floor(x / Cell);

        bool built;

        /// <summary>Build, once.</summary>
        public void EnsureBuilt()
        {
            if (built) return;
            built = true;
            Build();
        }

        /// <summary>The grid over what was added (a counting sort: each cell's vertices in the order added).</summary>
        [MethodImpl(MethodImplOptions.AggressiveOptimization)]
        public void Build()
        {
            if (n == 0) return;
            var cb = System.Diagnostics.Stopwatch.StartNew();
            var cx = new int[n];
            var cy = new int[n];
            var cz = new int[n];
            int x0 = int.MaxValue, y0 = int.MaxValue, z0 = int.MaxValue, x1 = int.MinValue, y1 = int.MinValue, z1 = int.MinValue;
            for (int v = 0; v < n; v++)
            {
                cx[v] = CellOf(pos[v].X); cy[v] = CellOf(pos[v].Y); cz[v] = CellOf(pos[v].Z);
                x0 = Math.Min(x0, cx[v]); y0 = Math.Min(y0, cy[v]); z0 = Math.Min(z0, cz[v]);
                x1 = Math.Max(x1, cx[v]); y1 = Math.Max(y1, cy[v]); z1 = Math.Max(z1, cz[v]);
            }
            gx0 = x0; gy0 = y0; gz0 = z0;
            nx = x1 - x0 + 1; ny = y1 - y0 + 1; nz = z1 - z0 + 1;
            var cell = new int[n];
            int slots;
            if ((long)nx * ny * nz <= 1 << 24) // (a stray far vertex: cells by key instead)
            {
                slots = nx * ny * nz;
                for (int v = 0; v < n; v++) cell[v] = ((cx[v] - gx0) * ny + (cy[v] - gy0)) * nz + (cz[v] - gz0);
            }
            else
            {
                sparse = new Dictionary<long, int>();
                for (int v = 0; v < n; v++)
                {
                    long key = Key(cx[v] - gx0, cy[v] - gy0, cz[v] - gz0);
                    if (!sparse.TryGetValue(key, out var sl)) sparse[key] = sl = sparse.Count;
                    cell[v] = sl;
                }
                slots = sparse.Count;
            }
            start = new int[slots + 1];
            for (int v = 0; v < n; v++) start[cell[v] + 1]++;
            for (int c = 0; c < slots; c++) start[c + 1] += start[c];
            var at = (int[])start.Clone();
            order = new int[n];
            for (int v = 0; v < n; v++) order[at[cell[v]]++] = v;
            sx = new float[n]; sy = new float[n]; sz = new float[n];
            for (int k = 0; k < n; k++) { var pv = pos[order[k]]; sx[k] = pv.X; sy[k] = pv.Y; sz[k] = pv.Z; }
            if (Prof) GD.Print($"garment tuck:     grid {nx}x{ny}x{nz} {cb.Elapsed.TotalMilliseconds:F1} ms");
        }

        long Key(int x, int y, int z) => ((long)x * ny + y) * nz + z;

        /// <summary>The nearest added vertex to q within reach (-1: none): ring after ring of cells out from q's, the first
        /// of equals in ring, x, y, z and added order.</summary>
        [MethodImpl(MethodImplOptions.AggressiveOptimization)]
        int Nearest(Vector3 q, float reach, int hint = -1)
        {
            int cx = CellOf(q.X), cy = CellOf(q.Y), cz = CellOf(q.Z);
            int rings = (int)MathF.Ceiling(reach / Cell);
            int gx1 = gx0 + nx - 1, gy1 = gy0 + ny - 1, gz1 = gz0 + nz - 1;
            if (n == 0 || cx + rings < gx0 || cx - rings > gx1 || cy + rings < gy0 || cy - rings > gy1 || cz + rings < gz0 || cz - rings > gz1) return -1;
            int best = -1;
            float bd = reach * reach;
            // (a hint, the vertex before's nearest: nothing farther than it can win, so its distance bounds the search from
            // the start; the first of equals in the order above still wins)
            if (hint >= 0)
            {
                float dh = (pos[hint] - q).LengthSquared();
                if (dh < bd) bd = MathF.BitIncrement(dh);
            }
            for (int r = 0; r <= rings; r++)
            {
                int xa = Math.Max(cx - r, gx0), xb = Math.Min(cx + r, gx1);
                int ya = Math.Max(cy - r, gy0), yb = Math.Min(cy + r, gy1);
                int za = Math.Max(cz - r, gz0), zb = Math.Min(cz + r, gz1);
                for (int x = xa; x <= xb; x++)
                {
                    bool xe = x == cx - r || x == cx + r;
                    float dx = Gap(q.X, x);
                    if (dx * dx > bd) continue;
                    for (int y = ya; y <= yb; y++)
                    {
                        float dy = Gap(q.Y, y);
                        float dxy = dx * dx + dy * dy;
                        if (dxy > bd) continue;
                        if (xe || y == cy - r || y == cy + r)
                            for (int z = za; z <= zb; z++) Visit(x, y, z, dxy, q, ref best, ref bd);
                        else
                        {
                            // (inside the ring's box: only its two z faces)
                            if (cz - r >= gz0 && cz - r <= gz1) Visit(x, y, cz - r, dxy, q, ref best, ref bd);
                            if (r > 0 && cz + r >= gz0 && cz + r <= gz1) Visit(x, y, cz + r, dxy, q, ref best, ref bd);
                        }
                    }
                }
                // (everything in a ring past r is at least r cells away)
                if (best >= 0 && bd <= (r * Cell) * (r * Cell)) break;
                // (nor nearer than q's distance to the faces of the box of rings 0..r: past the best, or reach, nothing out
                // there can win)
                float lo = MathF.Min(MathF.Min(Out(q.X, cx, r), Out(q.Y, cy, r)), Out(q.Z, cz, r));
                if (lo > 0 && lo * lo > bd) break;
            }
            if (best < 0 && hint >= 0) return Nearest(q, reach);
            return best;
        }

        // (a slack past float rounding at cell faces: a cull never drops a vertex that could win, so the nearest is the same)
        const float Slack = 1e-5f;

        /// <summary>How far coordinate v lies outside cell c along its axis, less the slack (0: within).</summary>
        static float Gap(float v, int c)
        {
            float lo = c * Cell - Slack, hi = (c + 1) * Cell + Slack;
            return v < lo ? lo - v : v > hi ? v - hi : 0f;
        }

        /// <summary>How far coordinate v (in cell c) lies inside the faces of cells c - r..c + r, less the slack.</summary>
        static float Out(float v, int c, int r) => MathF.Min(v - (c - r) * Cell, (c + r + 1) * Cell - v) - Slack;

        [MethodImpl(MethodImplOptions.AggressiveOptimization | MethodImplOptions.AggressiveInlining)]
        void Visit(int x, int y, int z, float dxy, Vector3 q, ref int best, ref float bd)
        {
            float dz = Gap(q.Z, z);
            if (dxy + dz * dz > bd) return;
            int c;
            if (sparse == null) c = ((x - gx0) * ny + (y - gy0)) * nz + (z - gz0);
            else if (!sparse.TryGetValue(Key(x - gx0, y - gy0, z - gz0), out c)) return;
            float qx = q.X, qy = q.Y, qz = q.Z;
            for (int k = start[c], e = start[c + 1]; k < e; k++)
            {
                // (as (pos - q).LengthSquared(), to the bit)
                float ex = sx[k] - qx, ey = sy[k] - qy, ez = sz[k] - qz;
                float d = ex * ex + ey * ey + ez * ez;
                if (d < bd) { bd = d; best = order[k]; }
            }
        }

        /// <summary>Blends each laid vertex's weights in `arr` toward its nearest outer vertex's, by GarmentTuck.Amount of
        /// its lay value; binds the outer pieces use that the skin lacks are added to it (`skinOf`: the laid copy's skin, made
        /// on first need). True if any vertex changed.</summary>
        public bool Reweight(int[] bj, float[] bw, float[] pos3, float[] t, Transform3D toSkel, BindState binds, bool fmt8)
        {
            int count = t.Length;
            int st = count == 0 ? 0 : bj.Length / count;
            if (st == 0) return false;
            // (each vertex's nearest outer vertex alone: in parallel)
            var cr = System.Diagnostics.Stopwatch.StartNew();
            var nearest = new int[count];
            System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, count, 512), rg => Run(rg.Item1, rg.Item2));
            [MethodImpl(MethodImplOptions.AggressiveOptimization)]
            void Run(int i0, int i1)
            {
                int hint = -1;
                for (int i = i0; i < i1; i++)
                {
                    nearest[i] = -1;
                    if (GarmentTuck.Amount(t[i]) <= 0f) continue;
                    var q = toSkel * new Vector3(pos3[i * 3], pos3[i * 3 + 1], pos3[i * 3 + 2]);
                    nearest[i] = Nearest(q, GarmentTuck.Reach, hint);
                    if (nearest[i] >= 0) hint = nearest[i];
                }
            }
            double tNear = cr.Elapsed.TotalMilliseconds;
            var toA = new int[names.Count];
            Array.Fill(toA, -2);
            int Local(int g) => toA[g] != -2 ? toA[g] : toA[g] = binds.Of(names[g], poses[g]);
            // (the binds the outer vertices bring, added to the skin in the order a pass over the vertices first meets them)
            for (int i = 0; i < count; i++)
            {
                int v = nearest[i];
                if (v < 0) continue;
                for (int k = 0; k < 8; k++)
                    if (bones[v * 8 + k] >= 0 && weights[v * 8 + k] > 0f && toA[bones[v * 8 + k]] == -2) Local(bones[v * 8 + k]);
            }
            // (then each vertex's blend alone: in parallel)
            int cap = Math.Min(fmt8 ? 8 : 4, st);
            int any = 0;
            System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, count, 1024), rg => Blend(rg.Item1, rg.Item2));
            [MethodImpl(MethodImplOptions.AggressiveOptimization)]
            void Blend(int i0, int i1)
            {
                Span<int> jb = stackalloc int[8];
                Span<float> wb = stackalloc float[8];
                Span<int> jo = stackalloc int[cap];
                Span<float> wo = stackalloc float[cap];
                for (int i = i0; i < i1; i++)
                {
                    int v = nearest[i];
                    if (v < 0) continue;
                    float s = GarmentTuck.Amount(t[i]);
                    int m = 0;
                    for (int k = 0; k < 8; k++)
                    {
                        int g = bones[v * 8 + k];
                        if (g < 0 || weights[v * 8 + k] <= 0f) continue;
                        jb[m] = toA[g]; wb[m] = weights[v * 8 + k]; m++;
                    }
                    if (m == 0) continue;
                    GarmentTuck.BlendWeights(bj.AsSpan(i * st, st), bw.AsSpan(i * st, st), jb[..m], wb[..m], s, jo, wo);
                    for (int k = 0; k < st; k++)
                    {
                        bj[i * st + k] = k < cap ? jo[k] : 0;
                        bw[i * st + k] = k < cap ? wo[k] : 0f;
                    }
                    any = 1;
                }
            }
            bool changed = any != 0;
            double tBlend = cr.Elapsed.TotalMilliseconds;
            if (Prof) GD.Print($"garment tuck:     nearest {tNear:F1} ms ({nearest.Count(v => v >= 0)} found), blend {tBlend - tNear:F1} ms, back {cr.Elapsed.TotalMilliseconds - tBlend:F1} ms");
            return changed;
        }
    }

    /// <summary>The outer pieces' full meshes (not their LOD or shadow copies) as a weight lookup; a mesh whose box misses
    /// `region` (where the laid piece's vertices may look) gives its binds alone.</summary>
    static OuterWeights? OuterOf(People.Person p, IEnumerable<MeshInstance3D> mis, Aabb region, Dictionary<string, OuterWeights?> made)
    {
        var use = new List<(MeshInstance3D B, bool Verts)>();
        foreach (var b in mis)
        {
            var n = b.Name.ToString();
            if (n.Contains("_lod") || n.EndsWith("_shadow")) continue;
            use.Add((b, b.Mesh == null || (b.Transform * b.Mesh.GetAabb()).Grow(0.02f).Intersects(region)));
        }
        var key = string.Join(",", use.Select(u => $"{u.B.GetInstanceId()}:{u.B.Mesh?.GetInstanceId() ?? 0}:{u.Verts}"));
        if (made.TryGetValue(key, out var got)) return got;
        var o = new OuterWeights();
        foreach (var (b, verts) in use) o.Add(b, p.Skeleton, verts);
        if (o.Count == 0) return made[key] = null;
        return made[key] = o;   // (its grid made on first need, on the worker: EnsureBuilt)
    }

    /// <summary>The box of her points the footprints' records cover (before their spread; null: none of hers).</summary>
    static Aabb? FootBox(SkinPoints sp, List<IReadOnlyList<(long Key, float T)>> feet)
    {
        var lo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
        var hi = -lo;
        bool any = false;
        foreach (var recs in feet)
            foreach (var (k, t) in recs)
                if (t > 0 && sp.ByKey.TryGetValue(k, out int i))
                {
                    var v = new Vector3(sp.P[i * 3], sp.P[i * 3 + 1], sp.P[i * 3 + 2]);
                    lo = lo.Min(v);
                    hi = hi.Max(v);
                    any = true;
                }
        return any ? new Aabb(lo, hi - lo) : null;
    }

    /// <summary>The box of her points a footprint covers.</summary>
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static Aabb Covered(SkinPoints sp, float[] field)
    {
        var lo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
        var hi = -lo;
        for (int i = 0; i < field.Length; i++)
            if (field[i] > 0)
            {
                var v = new Vector3(sp.P[i * 3], sp.P[i * 3 + 1], sp.P[i * 3 + 2]);
                lo = lo.Min(v);
                hi = hi.Max(v);
            }
        return new Aabb(lo, hi - lo);
    }

    /// <summary>A piece's footprint on her: the larger of its tuck and its cover (armor_cover/ID.bin, tools/armor/cover.py)
    /// at each of her points.</summary>
    static IReadOnlyList<(long Key, float T)> Footprint(ArmorPiece r)
    {
        var path = $"res://art/{r.Dir}/armor_cover/{r.Id}.bin";
        if (tucks.TryGetValue("foot:" + path, out var f)) return f;
        var d = new Dictionary<long, float>();
        if (r.Tuck != null) foreach (var (k, t) in Records($"res://art/{r.Dir}/{r.Tuck}")) d[k] = t;
        if (FileAccess.FileExists(path))
            foreach (var (k, t) in Records(path))
                if (!d.TryGetValue(k, out var o) || t > o) d[k] = t;
        return tucks["foot:" + path] = d.Select(kv => (kv.Key, kv.Value)).ToArray();
    }

    /// <summary>Her body's points (her skin surfaces' bind positions and normals), once for her body meshes.</summary>
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static SkinPoints? SkinOf(People.Person p)
    {
        var bodies = p.Skeleton.GetChildren().OfType<MeshInstance3D>().Where(People.TuckBody).ToList();
        var id = string.Join(",", bodies.Select(b => b.Mesh?.GetInstanceId() ?? 0));
        if (skinPoints.TryGetValue(id, out var sp)) return sp;
        var pos = new List<float>();
        var nrm = new List<float>();
        var keys = new List<long>();
        foreach (var mi in bodies)
            for (int s = 0; s < mi.Mesh.GetSurfaceCount() && s < mi.GetSurfaceOverrideMaterialCount(); s++)
            {
                if (mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial m || !People.IsSkin(m)) continue;
                var arr = mi.Mesh.SurfaceGetArrays(s);
                var vs = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var ns = arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
                if (ns.Length != vs.Length) continue;
                for (int i = 0; i < vs.Length; i++)
                {
                    pos.Add(vs[i].X); pos.Add(vs[i].Y); pos.Add(vs[i].Z);
                    nrm.Add(ns[i].X); nrm.Add(ns[i].Y); nrm.Add(ns[i].Z);
                    keys.Add(Key(vs[i]));
                }
            }
        if (keys.Count == 0) return null;
        return skinPoints[id] = new SkinPoints(pos, nrm, keys);
    }

    /// <summary>One surface of a mesh to lay: its arrays (read on the main thread), what the lay makes of them.</summary>
    sealed class LaySurf
    {
        public required Godot.Collections.Array Arr;
        public Vector3[]? Vs;      // (null: not triangles)
        public int[]? Idx, Bj, Kept;
        public float[]? Bw;
        public bool Fmt8, Rew;
    }

    /// <summary>A mesh to lay: read on the main thread (ReadLay), laid anywhere (ComputeLays: plain arrays alone), made
    /// into a mesh on the main thread (BuildLay).</summary>
    sealed class LayMesh
    {
        public required MeshInstance3D Mi;
        public required ArrayMesh Src;
        public required Aabb Box;
        public required (ulong, string) Key;
        public required LaySurf[] Surfs;
        public required Transform3D Xf;
        public BindState? Binds;   // (null: no skin, or no outer weights: its weights stay)
        public int State;          // (0: not reached, 1: nothing of it moves, 2: laid)
        public bool Any, Reskinned;
        public (int Point, float T)[] Under = Array.Empty<(int, float)>();
    }

    /// <summary>A laid copy's skin as the weights blend makes it: its binds' names (the piece's, then those added) and
    /// those added with their poses, made into a Skin on the main thread.</summary>
    sealed class BindState(List<string> names)
    {
        public readonly List<(string Name, Transform3D Pose)> Adds = new();
        Dictionary<string, int>? of;

        /// <summary>The bind of `name` (added with `pose` if the skin lacks it).</summary>
        public int Of(string name, Transform3D pose)
        {
            if (of == null)
            {
                of = new Dictionary<string, int>();
                for (int i = 0; i < names.Count; i++) if (names[i].Length > 0) of[names[i]] = i;
            }
            if (!of.TryGetValue(name, out var bi))
            {
                bi = names.Count;
                names.Add(name);
                Adds.Add((name, pose));
                of[name] = bi;
            }
            return bi;
        }
    }

    static LayMesh ReadLay(MeshInstance3D mi, string sig, bool weights)
    {
        var am = (ArrayMesh)mi.Mesh;
        var surfs = new LaySurf[am.GetSurfaceCount()];
        bool skinned = weights && mi.Skin != null;
        for (int s = 0; s < surfs.Length; s++)
        {
            var arr = am.SurfaceGetArrays(s);
            var ls = surfs[s] = new LaySurf { Arr = arr };
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) continue;
            ls.Vs = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var idxV = arr[(int)Mesh.ArrayType.Index];
            ls.Idx = idxV.VariantType == Variant.Type.Nil ? Enumerable.Range(0, ls.Vs.Length).ToArray() : idxV.AsInt32Array();
            if (skinned && arr[(int)Mesh.ArrayType.Bones].VariantType != Variant.Type.Nil && arr[(int)Mesh.ArrayType.Weights].VariantType != Variant.Type.Nil)
            {
                ls.Bj = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                ls.Bw = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            }
            ls.Fmt8 = ((long)am.SurfaceGetFormat(s) & (long)Mesh.ArrayFormat.FlagUse8BoneWeights) != 0;
        }
        BindState? binds = null;
        if (skinned)
        {
            var skel = mi.GetParent() as Skeleton3D;
            var names = new List<string>();
            for (int i = 0; i < mi.Skin.GetBindCount(); i++) names.Add(OuterWeights.BindName(mi.Skin, i, skel));
            binds = new BindState(names);
        }
        return new LayMesh { Mi = mi, Src = am, Box = am.GetAabb(), Key = (am.GetInstanceId(), sig), Surfs = surfs, Xf = mi.Transform, Binds = binds };
    }

    /// <summary>A piece's meshes laid, in order (no Godot object touched: a worker's): the field of the pieces over it made
    /// when one may reach a mesh (one that misses the footprints' box by the spread misses it spread too).</summary>
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void ComputeLays(string id, List<LayMesh> jobs, SkinPoints sp, List<IReadOnlyList<(long Key, float T)>> feet, Aabb pre, OuterWeights? ow)
    {
        float[]? field = null;
        bool[]? near = null;
        Aabb box = default;
        foreach (var j in jobs)
        {
            var grown = j.Box.Grow(GarmentTuck.Reach + 2 * GarmentTuck.Smooth);
            if (!grown.Intersects(pre.Grow(GarmentTuck.Spread + 0.001f))) { j.State = 1; continue; }
            if (field == null)
            {
                var cf = System.Diagnostics.Stopwatch.StartNew();
                field = GarmentTuck.Field(sp, feet);
                if (field == null) return;
                double tg = cf.Elapsed.TotalMilliseconds;
                near = GarmentTuck.Near(sp, field);
                double tn = cf.Elapsed.TotalMilliseconds;
                box = Covered(sp, field);
                if (Prof) GD.Print($"garment tuck: {id} field {tg:F1} ms, near {tn - tg:F1} ms");
            }
            if (!grown.Intersects(box)) { j.State = 1; continue; }
            var ck = System.Diagnostics.Stopwatch.StartNew();
            LayCompute(j, sp, field, near!, ow);
            j.State = 2;
            if (Prof) GD.Print($"garment tuck: {id} {j.Surfs.Length} surfaces laid {ck.Elapsed.TotalMilliseconds:F1} ms");
        }
    }

    /// <summary>One mesh laid down by GarmentTuck.Lay (its weights blended toward the outer pieces'), and her points
    /// under it with their values.</summary>
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void LayCompute(LayMesh j, SkinPoints sp, float[] field, bool[] near, OuterWeights? ow)
    {
        // (her points under it: each one's largest value, in the order first met)
        var underT = new float[sp.Count];
        var underAt = new List<int>();
        foreach (var ls in j.Surfs)
        {
            if (ls.Vs is not { } vs) continue;
            var pos = new float[vs.Length * 3];
            System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, vs.Length, 8192), rg =>
            {
                for (int i = rg.Item1; i < rg.Item2; i++) { pos[i * 3] = vs[i].X; pos[i * 3 + 1] = vs[i].Y; pos[i * 3 + 2] = vs[i].Z; }
            });
            var c1 = System.Diagnostics.Stopwatch.StartNew();
            var kept = GarmentTuck.Lay(sp, field, near, pos, ls.Idx!, out var anchor, out var t);
            if (Prof) GD.Print($"garment tuck:   lay {vs.Length} verts {c1.Elapsed.TotalMilliseconds:F1} ms");
            if (kept == null) continue;
            j.Any = true;
            System.Threading.Tasks.Parallel.ForEach(System.Collections.Concurrent.Partitioner.Create(0, vs.Length, 8192), rg =>
            {
                for (int i = rg.Item1; i < rg.Item2; i++) vs[i] = new Vector3(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]);
            });
            ls.Kept = kept;
            if (j.Binds != null && ow != null && ls.Bj != null)
            {
                var c2 = System.Diagnostics.Stopwatch.StartNew();
                ow.EnsureBuilt();
                ls.Rew = ow.Reweight(ls.Bj, ls.Bw!, pos, t, j.Xf, j.Binds, ls.Fmt8);
                j.Reskinned |= ls.Rew;
                if (Prof) GD.Print($"garment tuck:   weights {vs.Length} verts {c2.Elapsed.TotalMilliseconds:F1} ms");
            }
            for (int i = 0; i < anchor.Length; i++)
                if (anchor[i] >= 0 && t[i] > 0)
                {
                    if (underT[anchor[i]] <= 0) { underAt.Add(anchor[i]); underT[anchor[i]] = t[i]; }
                    else if (t[i] > underT[anchor[i]]) underT[anchor[i]] = t[i];
                }
        }
        j.Under = underAt.Select(k => (k, underT[k])).ToArray();
    }

    /// <summary>A laid mesh made (its blend shapes kept, as People's masked meshes; null Mesh: nothing of it moved).</summary>
    static (ArrayMesh Mesh, (int Point, float T)[] Under, Skin? Skin) BuildLay(LayMesh j)
    {
        if (!j.Any) return (null!, Array.Empty<(int, float)>(), null);
        var am = j.Src;
        var mesh = new ArrayMesh { BlendShapeMode = am.BlendShapeMode };
        // (A run without a screen cannot read shape keys back from a mesh: it goes without.)
        bool shapes = am.GetBlendShapeCount() > 0 && DisplayServer.GetName() != "headless";
        if (shapes) for (int k = 0; k < am.GetBlendShapeCount(); k++) mesh.AddBlendShape(am.GetBlendShapeName(k));
        for (int s = 0; s < j.Surfs.Length; s++)
        {
            var ls = j.Surfs[s];
            var arr = ls.Arr;
            if (ls.Kept != null)
            {
                arr[(int)Mesh.ArrayType.Vertex] = ls.Vs!;
                arr[(int)Mesh.ArrayType.Index] = ls.Kept;
                if (ls.Rew)
                {
                    arr[(int)Mesh.ArrayType.Bones] = ls.Bj!;
                    arr[(int)Mesh.ArrayType.Weights] = ls.Bw!;
                }
            }
            long fmt = (long)am.SurfaceGetFormat(s);
            var flags = (Mesh.ArrayFormat)(fmt & ((long)Mesh.ArrayFormat.FlagUse8BoneWeights | (0xFFFL << (int)Mesh.ArrayFormat.FormatCustom0Shift)));
            mesh.AddSurfaceFromArrays(am.SurfaceGetPrimitiveType(s), arr, shapes ? am.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(), null, flags);
            mesh.SurfaceSetMaterial(s, am.SurfaceGetMaterial(s));
            mesh.SurfaceSetName(s, am.SurfaceGetName(s));
        }
        mesh.ResourceName = am.ResourceName;
        Skin? skin = null;
        if (j.Reskinned)
        {
            skin = (Skin)j.Mi.Skin.Duplicate();
            foreach (var (n, pose) in j.Binds!.Adds) skin.AddNamedBind(n, pose);
        }
        return (mesh, j.Under, skin);
    }

    /// <summary>The worn pieces' tuck of her skin, the largest at each of her points, into each body surface's tuck_map
    /// (and `under`: her points under garment-tucked pieces).</summary>
    static void TuckMap(People.Person p, List<ArmorPiece> rows, Dictionary<long, float>? under = null)
    {
        var at = new Dictionary<long, float>();
        foreach (var r in rows)
        {
            if (r.Tuck == null) continue;
            foreach (var (k, t) in Records($"res://art/{r.Dir}/{r.Tuck}"))
                if (!at.TryGetValue(k, out var o) || t * TuckScale > o) at[k] = t * TuckScale;
        }
        if (under != null)
            foreach (var (k, t) in under)
                if (!at.TryGetValue(k, out var o) || t > o) at[k] = t;
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
