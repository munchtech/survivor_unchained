using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Rpg;

/* Who the survivor is, before anything happens to them.
 *
 * A calling (archetype) is how they fight: a body, a base, the weapons they
 * can start with and the two abilities they choose between. A background is
 * where they came from, and it is deliberately NOT a stat bonus: it is
 * knowledge (what you can notice and understand), a starting possession,
 * and how the world first reads you. Traits are what a character becomes
 * over time - some chosen at level-ups, some given by the world for what
 * you did in it. All of it is data (data/content/archetypes.json). */

public sealed class CallingBase
{
    public double MaxHealth, MoveSpeed, Armor, Regen, PickupRadius, CritChance;
}

public sealed class Palette
{
    public string Id = "", Name = "", Ui = "";
    public Dictionary<string, string> Paint = new();
}

public sealed class Archetype
{
    public string Id = "", Name = "", Tagline = "", Description = "", Model = "";
    public string? AltModel;
    public CallingBase Base = new();
    /// <summary>Items that grant each starting weapon choice.</summary>
    public List<string> Weapons = new();
    /// <summary>The two abilities to choose between (the web game's ids).</summary>
    public List<string> Abilities = new();
    /// <summary>The kinds of skill the calling leans toward: the draft offers them a little more.</summary>
    public List<Tag> Favours = new();
    public List<Palette> Palettes = new();
}

public sealed class Background
{
    public string Id = "", Name = "", Summary = "", Story = "";
    public List<string> Knowledge = new(), Items = new(), Opens = new();
    /// <summary>How factions first regard you.</summary>
    public Dictionary<string, double> Standing = new();
    /// <summary>How particular people first regard you.</summary>
    public Dictionary<string, Feel> Npc = new();
}

public enum TraitSource { Levelup, World, Background }

public sealed class TraitDef
{
    public string Id = "", Name = "", Text = "";
    public TraitSource Source;
    public List<StatMod>? Mods;
    public List<TriggerDef>? Triggers;
    /// <summary>World tags it carries ('wolf_friend' changes how the Pack reacts).</summary>
    public List<string>? Tags;
}

public static class Callings
{
    sealed class File
    {
        public Dictionary<string, Archetype> Archetypes = new();
        public Dictionary<string, Background> Backgrounds = new();
        public Dictionary<string, TraitDef> Traits = new();
    }

    static File? data;
    static File D => data ??= Json.Parse<File>(Json.ReadContent("archetypes.json"));

    public static Dictionary<string, Archetype> Archetypes => D.Archetypes;
    public static Dictionary<string, Background> Backgrounds => D.Backgrounds;
    public static Dictionary<string, TraitDef> Traits => D.Traits;

    public static Archetype Archetype(string id) => Archetypes.TryGetValue(id, out var a) ? a : throw new KeyNotFoundException($"no calling {id}");
    public static Background Background(string id) => Backgrounds.TryGetValue(id, out var b) ? b : throw new KeyNotFoundException($"no background {id}");
    public static TraitDef? Trait(string id) => Traits.TryGetValue(id, out var t) ? t : null;

    /// <summary>The traits a level-up can offer.</summary>
    public static List<string> LevelupTraits => Traits.Values.Where(t => t.Source == TraitSource.Levelup).Select(t => t.Id).ToList();

    /// <summary>Where each calling's attributes start.</summary>
    public static Attributes StartAttributes(string archetype) => archetype switch
    {
        "warden" => new() { Might = 6, Finesse = 3, Wits = 3, Resolve = 6 },
        "reaver" => new() { Might = 7, Finesse = 4, Wits = 2, Resolve = 5 },
        "arcanist" => new() { Might = 2, Finesse = 4, Wits = 8, Resolve = 4 },
        _ => new() { Might = 3, Finesse = 8, Wits = 4, Resolve = 3 },
    };
}
