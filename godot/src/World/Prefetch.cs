using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// What a place is about to load, asked for all at once on the engine's
/// worker threads before it is built. The kits' textures are UASTC in KTX2,
/// decoded on the CPU as each loads, and one at a time on the main thread the
/// Waystation's scenes took nine of its twelve seconds; together on the
/// worker threads the same files took two and a half. The building itself is
/// unchanged: its own loads find each file already loaded. What is fetched is
/// kept, as the kit pieces always were, so a person's clothes are no longer
/// loaded again for the next one who wears them.
/// </summary>
public static class Prefetch
{
    static readonly List<string> asked = new();
    static readonly Dictionary<string, Resource> kept = new();

    /// <summary>Everything the place will be built from: its flora and props,
    /// its landmarks, the arms that may be carried, the heroine as `her` is
    /// dressed, and in a place with people, every piece of the townsfolk's wardrobe.</summary>
    public static void Zone(ZoneData z, PersonSpec? her, bool folk)
    {
        Collect();
        var want = new List<string>(Dressing.Files(z)) { $"{z.Dir}/landmarks.glb" };
        foreach (var w in DirAccess.GetFilesAt("res://assets/weapons"))
            if (w.EndsWith(".glb")) want.Add($"res://assets/weapons/{w}");
        if (her != null) want.AddRange(People.Files(her));
        if (folk) want.AddRange(Wardrobe());
        Ask(want);
        // All of it in before the building starts, so the building's own loads
        // only ever find a file loaded. (Left to join a load still under way,
        // they now and then left a resource one reference short, and the game
        // crashed as it quit: Godot 4.5.1, two runs in ten.)
        Collect();
    }

    /// <summary>Each file not already loaded or on its way, asked for (its own
    /// textures and meshes loaded side by side too).</summary>
    public static void Ask(IEnumerable<string> paths)
    {
        foreach (var p in paths)
        {
            if (kept.ContainsKey(p) || asked.Contains(p) || ResourceLoader.HasCached(p) || !ResourceLoader.Exists(p)) continue;
            if (ResourceLoader.LoadThreadedRequest(p, "", true) == Error.Ok) asked.Add(p);
        }
    }

    /// <summary>What was asked for, taken in and kept (the loader holds each
    /// until it is collected; this waits for any still loading).</summary>
    public static void Collect()
    {
        foreach (var p in asked)
            if (ResourceLoader.LoadThreadedGet(p) is { } r) kept[p] = r;
        asked.Clear();
    }

    /// <summary>All of it let go, while the engine is still whole (the game
    /// calls this as it leaves the tree). Held by C# to the very end, it was
    /// disposed only once the engine had begun to come apart, and now and then
    /// the game crashed as it quit (two runs in twenty).</summary>
    public static void Release()
    {
        Collect();
        foreach (var r in kept.Values) r.Dispose();
        kept.Clear();
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
