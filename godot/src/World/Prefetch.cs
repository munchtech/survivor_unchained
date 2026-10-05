using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// The kit's textures a place is built from, decoded side by side before it
/// is built. They are KTX2 files of Basis UASTC (assets/), each transcoded on
/// the CPU as it loads; loaded one at a time on the main thread they were most
/// of the Waystation's build. Here the files are read and transcoded on .NET
/// worker threads (Image.LoadKtxFromBuffer: the same code Godot's KTX loader
/// runs, so the same textures), made into textures on the main thread, and
/// handed to Godot's resource cache under their own paths, where the
/// building's loads find them. Godot's threaded resource loader is not used:
/// fetching whole scenes with it crashed the game as it quit, now and then
/// (4.5.1). Nothing is held past the frame the place is built in: the scenes
/// that use a texture keep it.
/// </summary>
public static class Prefetch
{
    static readonly List<ImageTexture> made = new();
    /// <summary>Each scene file's KTX2 textures (read from its header once).</summary>
    static readonly Dictionary<string, string[]> ktxOf = new();

    /// <summary>Everything the place will be built from: its flora and props,
    /// its landmarks, the arms that may be carried, the heroine as `her` is
    /// dressed, and in a place with people, every piece of the townsfolk's wardrobe.</summary>
    public static void Zone(ZoneData z, PersonSpec? her, bool folk)
    {
        Release();
        var scenes = new List<string>(Dressing.Files(z)) { $"{z.Dir}/landmarks.glb" };
        foreach (var w in DirAccess.GetFilesAt("res://assets/weapons"))
            if (w.EndsWith(".glb")) scenes.Add($"res://assets/weapons/{w}");
        if (her != null) scenes.AddRange(People.Files(her));
        if (folk) scenes.AddRange(Wardrobe());
        // Each scene's header read once a session, side by side (some 3 ms a
        // file, 200 files in town).
        var unread = new List<string>();
        foreach (var s in scenes) if (!ktxOf.ContainsKey(s) && !unread.Contains(s)) unread.Add(s);
        var read = new ConcurrentDictionary<string, string[]>();
        Parallel.ForEach(unread, s => read[s] = KtxOf(s));
        foreach (var (s, t) in read) ktxOf[s] = t;
        var want = new List<string>();
        var seen = new HashSet<string>();
        foreach (var s in scenes)
            foreach (var t in ktxOf[s])
                if (seen.Add(t) && !ResourceLoader.HasCached(t)) want.Add(t);
        Decode(want);
        // Let go once this frame's building is done (the place is built in one go).
        if (made.Count > 0) Callable.From(Release).CallDeferred();
    }

    /// <summary>The KTX2 files a scene names as its own dependencies (any thread).</summary>
    static string[] KtxOf(string scene)
    {
        var list = new List<string>();
        if (ResourceLoader.Exists(scene))
            foreach (var d in ResourceLoader.GetDependencies(scene))
            {
                // "uid::type::path" (or the bare path): the path is the last part.
                int cut = d.LastIndexOf("::", System.StringComparison.Ordinal);
                var path = cut >= 0 ? d[(cut + 2)..] : d;
                if (path.StartsWith("uid://")) path = ResourceUid.GetIdPath(ResourceUid.TextToId(path));
                if (path.EndsWith(".ktx2")) list.Add(path);
            }
        return list.ToArray();
    }

    /// <summary>The files read and transcoded on worker threads; each made a
    /// texture on this one as it arrives, and cached under its path.</summary>
    static void Decode(List<string> paths)
    {
        if (paths.Count == 0) return;
        using var done = new BlockingCollection<(string Path, Image? Img)>();
        var work = Task.Run(() =>
        {
            try { Parallel.ForEach(paths, p => done.Add((p, Read(p)))); }
            finally { done.CompleteAdding(); }
        });
        foreach (var (path, img) in done.GetConsumingEnumerable())
        {
            if (img == null) continue;
            // Another load may have made it meanwhile: never two under one path.
            if (!ResourceLoader.HasCached(path))
            {
                var tex = ImageTexture.CreateFromImage(img);
                tex.TakeOverPath(path);
                made.Add(tex);
            }
            img.Dispose();
        }
        work.Wait();
    }

    static Image? Read(string path)
    {
        var bytes = FileAccess.GetFileAsBytes(path);
        if (bytes.Length == 0) return null;
        var img = new Image();
        if (img.LoadKtxFromBuffer(bytes) == Error.Ok && !img.IsEmpty()) return img;
        img.Dispose();
        return null;
    }

    /// <summary>Our hold on what was decoded let go: the scenes built from it
    /// keep their own (what no one used is freed).</summary>
    public static void Release()
    {
        foreach (var t in made) t.Dispose();
        made.Clear();
    }

    static List<string>? wardrobe;

    /// <summary>Every file a townsperson can be made from: both bodies, every
    /// outfit Lore can give (with hood and pauldron), every hairstyle and the
    /// beard, and whatever the named people wear.</summary>
    static List<string> Wardrobe()
    {
        if (wardrobe != null) return wardrobe;
        var all = new HashSet<string>();
        foreach (var sex in new[] { Sex.Male, Sex.Female })
        {
            all.Add($"res://assets/people/{(sex == Sex.Female ? "Superhero_Female_FullBody" : "Superhero_Male_FullBody")}.gltf");
            foreach (var kind in new[] { "peasant", "ranger", "bare" })
                foreach (var part in Lore.OutfitFor(sex, kind, true, true)) all.Add($"res://assets/people/{part}.gltf");
            foreach (var hair in Lore.HairStyles(sex)) all.Add($"res://assets/people/{hair}.gltf");
        }
        all.Add("res://assets/people/Hair_Beard.gltf");
        foreach (var n in Lore.Npcs.Values)
            if (n.Person is { } spec)
                foreach (var f in People.Files(spec)) all.Add(f);
        return wardrobe = new List<string>(all);
    }
}
