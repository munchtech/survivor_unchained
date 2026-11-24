using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>A place's cached resources let go when the game leaves it (the tester lane, 24 Nov: after the town was taken
/// apart and collected, static caches still held about 513 MB of textures the den never draws: NPC packages' scenes, the
/// dressing's and the house kit's meshes and materials; --mem-statics). Called from Game.LetGoOfLast once the last place is
/// freed and nothing is being built ahead. A cache entry is dropped when nothing asked for it since the last place change
/// (Asked: the new place, built before this runs, asked for what it uses, so that stays shared); a plain list of materials
/// by its Godot reference count (only the cache holds it). The next place that wants one loads or
/// makes it again. A new cache of a place's things adds one line to LetGo.</summary>
public static class PlaceCache
{
    /// <summary>Held by something besides the cache (a node, a mesh, a material): its reference count above the cache's one.</summary>
    public static bool Held(GodotObject? o) => o is RefCounted r && GodotObject.IsInstanceValid(r) && r.GetReferenceCount() > 1;

    /// <summary>The entries <paramref name="keep"/> says no to removed; how many.</summary>
    public static int Prune<K, V>(Dictionary<K, V> d, Func<V, bool> keep) where K : notnull
    {
        var gone = d.Where(kv => !keep(kv.Value)).Select(kv => kv.Key).ToList();
        foreach (var k in gone) d.Remove(k);
        return gone.Count;
    }

    /// <summary>A cache by place id: the other places' entries removed; how many.</summary>
    public static int Others<V>(Dictionary<string, V> d, string? here)
    {
        var gone = d.Keys.Where(k => k != here).ToList();
        foreach (var k in gone) d.Remove(k);
        return gone.Count;
    }

    /// <summary>A cache's keys asked for since the last place change (any thread): Prune drops the rest. A cache's entries can
    /// hold each other (a mesh's surface holds a kit material), so a reference count alone keeps them all (24 Nov, measured:
    /// den after town, 54 of ~420 MB let go by counts alone).</summary>
    public sealed class Asked
    {
        readonly HashSet<object> keys = new();
        public Asked() { lock (all) all.Add(this); }
        internal void Clear() { lock (keys) keys.Clear(); }
        public void Add(object k) { lock (keys) keys.Add(k); }
        public int Prune<K, V>(Dictionary<K, V> d) where K : notnull
        {
            lock (keys)
            {
                var gone = d.Keys.Where(k => !keys.Contains(k)).ToList();
                foreach (var k in gone) d.Remove(k);
                return gone.Count;   // (the keys stay till the next place's build begins: Begin; one Asked may prune two caches)
            }
        }
    }

    static readonly List<Asked> all = new();

    /// <summary>A place's build begins (Game.Stage, Game.Prepare): what every cache was asked for till now forgotten, so
    /// LetGo keeps only what this place asks (the tester lane, 24 Nov: started in the town, the den's first LetGo let go of
    /// nothing: every ask since the game began still counted).</summary>
    public static void Begin() { lock (all) foreach (var a in all) a.Clear(); }

    /// <summary>Every place cache pruned (<paramref name="here"/>: the place now shown); a log line with the counts.</summary>
    public static void LetGo(string? here)
    {
        if (Args.Has("place-cache-keep")) return;   // (dev A/B: the caches as before)
        int npc = NpcPackage.LetGoOfPlace(), dye = NpcDye.LetGoOfPlace(), dress = Dressing.LetGoOfPlace(), kit = KitLook.LetGoOfPlace(), walls = OwnWalls.LetGoOfPlace();
        int made = Made.LetGoOfPlace(), grade = Atmosphere.LetGoOfPlace(), maps = SurvivorUnchained.Ui.MapScreen.LetGoOfPlace(here) + SurvivorUnchained.Ui.Minimap.LetGoOfPlace(here);
        GD.Print($"load: place caches let go: npc {npc}, dye {dye}, dressing {dress}, kit {kit}, own walls {walls}, made {made}, grade luts {grade}, map drawings {maps}");
    }
}
