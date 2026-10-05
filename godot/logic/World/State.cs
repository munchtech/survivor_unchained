using System.Collections.Generic;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* The world's memory: everything that persists between expeditions, between
 * sessions, between one character and the next.
 *
 * Facts are the world's state, as plain keyed values ('beasts.population',
 * 'caravan.cargo'). Knowledge is what the PLAYER knows (clues, lore,
 * background learning) - kept apart from facts, because the world can be one
 * way and the player can not know it yet. History is what happened, with who
 * saw it; people carry memories of those events and opinions shaped by them.
 *
 * Every piece is JSON-shaped so the save is the state, with no translation. */

public enum Axis { Trust, Affection, Respect, Fear }
public enum TimeOfDay { Dawn, Day, Dusk, Night }
public enum QuestStatus { Unknown, Active, Resolved, Failed, Abandoned }

/// <summary>How someone feels about the survivor, -100..100 on each axis.
/// Contradictions are allowed and are the point: someone can respect you and
/// fear you and not like you at all.</summary>
public class Feel
{
    public double? Trust, Affection, Respect, Fear;
    public double? Of(Axis a) => a switch { Axis.Trust => Trust, Axis.Affection => Affection, Axis.Respect => Respect, _ => Fear };
}

public sealed class NpcState
{
    public string Id = "";
    public bool Alive = true;
    public double Trust, Affection, Respect, Fear;
    /// <summary>History event ids this person knows about (witnessed or heard).</summary>
    public List<string> Memories = new();
    /// <summary>Where they are now, when it differs from their schedule.</summary>
    public string? Location;
    /// <summary>Free flags ('met', 'once:lamp').</summary>
    public Dictionary<string, Fact> Flags = new();
    /// <summary>Dialogue nodes already seen.</summary>
    public List<string> Seen = new();

    public double this[Axis a]
    {
        get => a switch { Axis.Trust => Trust, Axis.Affection => Affection, Axis.Respect => Respect, _ => Fear };
        set
        {
            switch (a)
            {
                case Axis.Trust: Trust = value; break;
                case Axis.Affection: Affection = value; break;
                case Axis.Respect: Respect = value; break;
                default: Fear = value; break;
            }
        }
    }

    public Fact Flag(string key) => Flags.TryGetValue(key, out var v) ? v : Fact.Null;
}

public sealed class FactionState
{
    public string Id = "";
    /// <summary>How the faction regards the player, -100..100.</summary>
    public double Standing;
    /// <summary>How strong it is in the region, 0..100.</summary>
    public double Strength = 50;
    public Dictionary<string, Fact> Flags = new();
}

public class HistoryDef
{
    public string Id = "";
    /// <summary>One line in the voice of someone telling it.</summary>
    public string Text = "";
    public List<string> Tags = new();
    /// <summary>How far it travels as gossip: 0 private, 1 local, 2 the whole town.</summary>
    public int Spread;
    /// <summary>How people who hear of it feel, by default.</summary>
    public Feel? Sentiment;
    /// <summary>Who takes it personally, and how.</summary>
    public Dictionary<string, Feel>? Reactions;
}

public sealed class HistoryEvent : HistoryDef
{
    public int Day;
}

public sealed class QuestState
{
    public string Id = "";
    public QuestStatus Status = QuestStatus.Unknown;
    /// <summary>Journal entries unlocked, in the order found.</summary>
    public List<string> Entries = new();
    public string? Outcome;
    public int? StartedDay;
}

public sealed class CorpseState
{
    public string Zone = "";
    public double X, Z;
    public double Gold;
    public List<ItemInstance> Items = new();
    public int Day;
    public string Killer = "", HeroName = "";
}

public sealed class NemesisState
{
    public string Zone = "";
    /// <summary>The creature it was (an enemy id).</summary>
    public string Def = "";
    public string Title = "";
    public int Level;
    public List<ItemInstance> Carries = new();
    public string HeroName = "";
    public bool Killed;
}

public sealed class LegacyEntry
{
    public string Name = "", Archetype = "", Background = "";
    public int Level, Day;
    public string Killer = "", Zone = "", Epitaph = "";
}

public sealed class ScheduledChange
{
    public int Day;
    public string Id = "";
    public List<Change> Effect = new();
}

public sealed class GroundItem
{
    public string Zone = "";
    public double X, Z;
    public ItemInstance Item = null!;
}

public sealed class ShopState
{
    public List<ItemInstance> Stock = new();
    public int RestockDay;
    public double PriceMult = 1;
    /// <summary>The conditional lines (by "index:item") already rolled for this
    /// restock: a line that becomes true between restocks is put on the shelf
    /// the next time the shop is opened, once, and not rolled again.</summary>
    public List<string> Offered = new();
}

public sealed class WorldState
{
    public int Version = 1;
    public uint Seed;
    public int Day = 1;
    public TimeOfDay Time = TimeOfDay.Dusk;
    /// <summary>Seconds of free play since this day's dawn (DayClock): where in its time of day the
    /// world is, so the day moves on by itself.</summary>
    public double Clock = DayClock.DuskAt;
    public Dictionary<string, Fact> Facts = new();
    public List<string> Knowledge = new();
    public Dictionary<string, NpcState> Npcs = new();
    public Dictionary<string, FactionState> Factions = new();
    public Dictionary<string, QuestState> Quests = new();
    public List<HistoryEvent> History = new();
    public List<ScheduledChange> Scheduled = new();
    /// <summary>Zone-persistent objects: opened chests, burned walls, picked herbs.</summary>
    public Dictionary<string, Dictionary<string, Fact>> Zones = new();
    public CorpseState? Corpse;
    public NemesisState? Nemesis;
    /// <summary>What a night with the ember lit outside an arena (the prologue's) has taught,
    /// banked until its dawn (Journey.Douse).</summary>
    public double NightLessons;
    /// <summary>Seconds played by kind of play (prologue, town, wild, story night, table night,
    /// map): the owner wants the story two fifths of the game early on, and this is how it is
    /// measured rather than guessed (Journey.StoryShare).</summary>
    public Dictionary<string, double> TimeIn = new();
    /// <summary>Discoveries recorded in the codex.</summary>
    public List<string> Codex = new();
    /// <summary>Bestiary kill counts by creature.</summary>
    public Dictionary<string, int> Bestiary = new();
    /// <summary>Items on the ground that must persist (dropped quest items).</summary>
    public List<GroundItem> GroundItems = new();
    /// <summary>The inn's storage: it belongs to the world, so it outlives a character.</summary>
    public List<ItemInstance?> Stash = NewStash();
    /// <summary>The dark's debt (docs/design/LOOT_DESIGN.md §5.3): gear rolls since the last
    /// Legendary; at Loot's figure a boss's hoard holds one for certain.</summary>
    public int LootDebt;
    /// <summary>A Legendary has fallen in this world: the first story boss's certain one is paid.</summary>
    public bool FirstLegendary;
    /// <summary>The Set and Legendary pieces that have fallen here (a never-owned piece is likelier).</summary>
    public HashSet<string> Owned = new();
    /// <summary>Those who came before.</summary>
    public List<LegacyEntry> Legacy = new();
    /// <summary>Shop stock and prices, by shop.</summary>
    public Dictionary<string, ShopState> Shops = new();
    /// <summary>The ember arena begun (Arena/Arena.cs), until it is over.</summary>
    public Arena.ArenaSpec? Arena;
    /// <summary>The Wayfinder's chart being walked, while it is (docs/SKILLS_DESIGN.md §17).</summary>
    public Maps.Chart? Map;
    /// <summary>Story fights lost, waiting at the Wayfinder's table to be taken again.</summary>
    public List<Arena.ArenaSpec> Rematches = new();

    /// <summary>A shelf of Rook's storeroom: one comes with the room, more are bought from her
    /// (Crafting.ShelfPrice). A save from before shelves kept 48 places: two shelves.</summary>
    public const int Shelf = 24;
    public int Shelves => System.Math.Max(1, Stash.Count / Shelf);
    static List<ItemInstance?> NewStash() { var s = new List<ItemInstance?>(Shelf); for (int i = 0; i < Shelf; i++) s.Add(null); return s; }

    public static WorldState Fresh(uint seed) => new() { Seed = seed };

    public Fact Fact(string key) => Facts.TryGetValue(key, out var v) ? v : World.Fact.Null;

    public NpcState Npc(string id)
    {
        if (!Npcs.TryGetValue(id, out var s)) Npcs[id] = s = new NpcState { Id = id };
        return s;
    }

    public Dictionary<string, Fact> Zone(string id)
    {
        if (!Zones.TryGetValue(id, out var z)) Zones[id] = z = new();
        return z;
    }
}
