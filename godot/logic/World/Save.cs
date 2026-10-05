using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* Persistence: the proof that this is not a run.
 *
 * One record per slot holds the character, the world and where the survivor
 * stands. It is written on rest, on changing zone and on every event the
 * world would not want to forget (a quest resolved, a death), and it can be
 * exported as a code so a save is never trapped on one machine.
 *
 * Versioned: a save from an older build is migrated forward on load, never
 * discarded. A save that fails to parse is set aside, not overwritten. */

public sealed class SaveLocation { public string Zone = ""; public double X, Z, Facing; }

/// <summary>The wounds carried from zone to zone until the survivor rests
/// (named for when it carried the ember too; a save from then still reads).</summary>
public sealed class EmberCarry
{
    public double? Hp;
}

public sealed class SaveData
{
    public int Version = Saves.Version;
    public long SavedAt;
    public double Playtime;
    public CharacterData Character = null!;
    public WorldState World = null!;
    public SaveLocation Location = new();
    public EmberCarry? Ember;
}

public sealed record SlotInfo(int Slot, string Name, int Level, string Archetype, int Day, string Zone, long SavedAt, bool Alive);

/// <summary>The save slots, as files in a folder (the game's user folder).</summary>
public sealed class Saves
{
    public const int Version = 4;
    public const int SlotCount = 3;
    readonly string dir;

    public Saves(string dir)
    {
        this.dir = dir;
        Directory.CreateDirectory(dir);
    }

    string PathOf(int slot) => Path.Combine(dir, $"slot{slot}.json");
    string MetaPath => Path.Combine(dir, "meta.json");

    public static SaveData Migrate(SaveData d)
    {
        // Version 1 is the first; later versions add steps here, oldest first.
        d.World.Stash ??= new();
        // Whole shelves, at least the one that comes with the room (a save from before shelves had two).
        while (d.World.Stash.Count < WorldState.Shelf || d.World.Stash.Count % WorldState.Shelf != 0) d.World.Stash.Add(null);
        d.World.Legacy ??= new();
        d.World.Shops ??= new();
        d.World.GroundItems ??= new();
        // 2: shops remember which conditional lines this restock has rolled.
        // An older shelf already holds whatever of them it rolled, so those
        // count as rolled (or they would be put up a second time).
        foreach (var (id, st) in d.World.Shops)
        {
            st.Offered ??= new();
            if (d.Version >= 2 || !Lore.Shops.TryGetValue(id, out var def)) continue;
            for (int i = 0; i < def.Lines.Count; i++)
                if (def.Lines[i].When != null && st.Stock.Any(it => it.Def == def.Lines[i].Id)) st.Offered.Add($"{i}:{def.Lines[i].Id}");
        }
        // 3: crafting (docs/CRAFTING_DESIGN.md). Materials leave the pack for the pouch, and
        // every piece that can be worked has its heat (what was made before heat existed
        // is as hot as its rarity, never colder).
        var ch = d.Character;
        ch.Materials ??= new();
        // 4: the pack holds gear only (docs/design/LOOT_DESIGN.md §6): materials and trophies to the
        // pouch, books, charts and marked things to the satchel, quest things and tools to the key
        // ring, draughts to the belt. A draught kind past the belt's limit stays in the pack.
        ch.Satchel ??= new();
        ch.Keys ??= new();
        ch.Belt ??= new();
        ch.Filter ??= new();
        ch.Seen ??= new();
        d.World.Owned ??= new();
        for (int i = 0; i < ch.Pack.Count; i++)
            if (ch.Pack[i] is { } it && Items.Find(it.Def) is { } def && Drops.StoreOf(def, it) != Store.Pack)
            {
                ch.Pack[i] = null;
                if (!Inventory.AddToPack(ch, it)) ch.Pack[i] = it;
            }
        void Heat(ItemInstance? it)
        {
            if (it == null || it.Heat != null || Items.Find(it.Def) is not { } def || !Crafting.Workable(def)) return;
            it.Heat = it.HeatFull = Crafting.HeatAtMaking(it.Rarity);
        }
        foreach (var it in ch.Pack) Heat(it);
        foreach (var s in Items.EquipSlots) Heat(ch.Equipment[s]);
        foreach (var it in d.World.Stash) Heat(it);
        foreach (var it in d.World.Nemesis?.Carries ?? new()) Heat(it);
        foreach (var it in d.World.Corpse?.Items ?? new()) Heat(it);
        d.Version = Version;
        return d;
    }

    public bool Write(int slot, SaveData data)
    {
        data.Version = Version;
        data.SavedAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        try
        {
            // Written beside, then moved over: a crash mid-write never leaves half a save.
            var tmp = PathOf(slot) + ".tmp";
            File.WriteAllText(tmp, Json.Write(data));
            File.Move(tmp, PathOf(slot), true);
            File.WriteAllText(MetaPath, $"{{\"last\":{slot}}}");
            return true;
        }
        catch (IOException) { return false; }
        catch (UnauthorizedAccessException) { return false; }
    }

    public static SaveData? Parse(string raw)
    {
        var d = Json.Parse<SaveData>(raw);
        if (d.Character == null || d.World == null) throw new FormatException("incomplete save");
        return Migrate(d);
    }

    public SaveData? Read(int slot)
    {
        var p = PathOf(slot);
        if (!File.Exists(p)) return null;
        var raw = File.ReadAllText(p);
        try { return Parse(raw); }
        catch (Exception e) when (e is FormatException or System.Text.Json.JsonException)
        {
            // Keep the broken record aside for a bug report; never overwrite it.
            File.Move(p, $"{p}.broken.{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}", true);
            return null;
        }
    }

    public List<SlotInfo> Slots()
    {
        var o = new List<SlotInfo>();
        for (int i = 0; i < SlotCount; i++)
            if (Read(i) is { } d)
                o.Add(new SlotInfo(i, d.Character.Name, d.Character.Level, d.Character.Archetype, d.World.Day, d.Location.Zone, d.SavedAt, d.Character.Alive));
        return o;
    }

    public int? LastSlot()
    {
        try
        {
            if (!File.Exists(MetaPath)) return null;
            using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(MetaPath));
            return doc.RootElement.TryGetProperty("last", out var v) ? v.GetInt32() : null;
        }
        catch (Exception) { return null; }
    }

    public void Remove(int slot)
    {
        if (File.Exists(PathOf(slot))) File.Delete(PathOf(slot));
    }

    /// <summary>A compact code for moving a save between machines.</summary>
    public string? ExportCode(int slot) =>
        File.Exists(PathOf(slot)) ? Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(File.ReadAllText(PathOf(slot)))) : null;

    public bool ImportCode(int slot, string code)
    {
        try
        {
            var raw = System.Text.Encoding.UTF8.GetString(Convert.FromBase64String(code.Trim()));
            var d = Parse(raw);
            if (d == null) return false;
            File.WriteAllText(PathOf(slot), Json.Write(d));
            return true;
        }
        catch (Exception) { return false; }
    }
}
