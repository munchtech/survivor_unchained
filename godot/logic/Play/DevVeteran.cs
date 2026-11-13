using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>(M3) The balance harness's survivor of a level, in one place for the harness (MapSim.Survivor) and the game's
/// dev argument (--veteran L[:G], src/Game/Game.cs Quick): the same build under the same arguments, so a clip shows what
/// the sim measures. Before it the game's veteran was `--xp N` alone: the level with every attribute point unspent, no
/// gear but the starting weapon and one draught, where the sim's has the points in the calling's attribute, plain gear
/// at a rarity in six slots and five draughts (she fell at 94-110 s in the game on maps the sim cleared 32 of 32).</summary>
public static class DevVeteran
{
    /// <summary>The draughts the harness's map survivor carries on top of the journey's one.</summary>
    public const int Draughts = 4;

    /// <summary>A survivor at a level, as a player would have dressed them by then: the points in the calling's attribute,
    /// the calling's taught build (taught_builds.json) and its path's skills at the day's rank, as many as the level's
    /// slots hold, and plain gear at a rarity in six slots (the weapon stays the one begun with).</summary>
    public static void Dress(CharacterData ch, int level, int gearRarity, int seed)
    {
        string calling = ch.Archetype;
        while (ch.Level < level) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1);
        switch (calling) { case "arcanist": ch.Attributes.Wits += ch.Points; break; case "stalker": ch.Attributes.Finesse += ch.Points; break; default: ch.Attributes.Might += ch.Points; break; }
        ch.Points = 0;
        // (M3) A calling with a taught build carries it first (taught_builds.json, as a campaign survivor of that level does);
        // the path's skills fill what slots are left.
        TaughtBuilds.Grant(ch, ch.Level);
        // (bd-keys) and every point lit, as a player of that level has lit them: the levels gained above held each carried
        // skill's points (WickBook.Grew), which left her basic attack at rank 1 at level 30.
        WickBook.LightAll(ch);
        var path = Content.Paths.All.Where(p => p.Callings.Contains(calling)).OrderBy(p => p.Id).ToList();
        var pick = path[seed % path.Count];
        foreach (var id in pick.Weapons.Concat(path.SelectMany(p => p.Weapons)).Distinct())
        {
            if (ch.Slotted.Count >= SkillBook.Slots(ch)) break;
            if (!Content.Weapons.All.ContainsKey(id) || !SkillBook.Meets(ch, id) || !SkillBook.Carries(ch, id) || ch.Skills.Contains(id)) continue;
            ch.Skills.Add(id);
            SkillBook.TakeUp(ch, id);
        }
        var rng = new Rng((uint)seed * 31 + 5);
        (EquipSlot Slot, string Def)[] dress =
        [
            (EquipSlot.Head, rng.Chance(0.5) ? "iron_helm" : "leather_cap"), (EquipSlot.Body, rng.Chance(0.5) ? "chain_shirt" : "padded_jerkin"),
            (EquipSlot.Cloak, "travelers_cloak"), (EquipSlot.Amulet, "bone_amulet"), (EquipSlot.Ring1, "silver_ring"), (EquipSlot.Ring2, "copper_ring"),
        ];
        foreach (var (slot, def) in dress)
            ch.Equipment[slot] = Inventory.Make(ch, def, 1, gearRarity, (uint)rng.Int(1, 1 << 30));
    }

    /// <summary>The map survivor's belt: the harness's draughts on top of the journey's own.</summary>
    public static void Belt(CharacterData ch)
    {
        for (int i = 0; i < Draughts; i++) Inventory.AddToPack(ch, Inventory.Make(ch, "health_draught", 1));
    }

    /// <summary>The game's --veteran L[:G] (G: the gear's rarity, 2 if not given; the harness's --level L and its g2): dressed
    /// and belted as the harness's map survivor. The seed picks the path's skills and rolls the gear, as the harness's does.</summary>
    public static string Apply(CharacterData ch, string arg, int seed)
    {
        var parts = arg.Split(':');
        int level = int.TryParse(parts[0], out var l) ? Math.Clamp(l, 1, Character.MaxLevel) : Character.MaxLevel;
        int gear = parts.Length > 1 && int.TryParse(parts[1], out var g) ? g : 2;
        Dress(ch, level, gear, seed);
        Belt(ch);
        return $"veteran: level {ch.Level}, gear rarity {gear}, seed {seed}, {Draughts} draughts more";
    }

    /// <summary>Her, one line, at a fight's start (the harness and the game's --auto --clip both print it: the same line
    /// means the same build): level, points unspent, attributes, life, the kit's stats, what is worn by slot and rarity,
    /// draughts, the keys, and the press on her (the world tier, the kit's bite and cadence).</summary>
    public static string Line(Battle b, Journey j)
    {
        var ch = j.Ch;
        var inv = CultureInfo.InvariantCulture;
        var worn = new List<string>();
        foreach (var s in Enum.GetValues<EquipSlot>())
            if (ch.Equipment[s] is { } it) worn.Add($"{s}:{it.Rarity}");
        string keys = string.Join(" ", b.Weapons.Select(w => $"{w.Id}{w.Rank}@{w.Slot + 1}{(w.Slot2 >= 0 ? "+" + (w.Slot2 + 1) : "")}"));
        return string.Format(inv,
            "her: level {0} points {1} might {2} finesse {3} wits {4} resolve {5} | life {6:0} damage {7:0.00} armor {8:0.0} regen {9:0.00} block {10:0.00} speed {11:0.00} | worn {12} [{13}] | draughts {14} | keys {15} | world tier {16} kit x{17:0.00} every x{18:0.00}",
            ch.Level, ch.Points, ch.Attributes.Might, ch.Attributes.Finesse, ch.Attributes.Wits, ch.Attributes.Resolve,
            b.MaxHp, b.Stats.Get(Stat.Damage), b.Stats.Get(Stat.Armor), b.Stats.Get(Stat.Regen), b.Stats.Get(Stat.Block), b.Stats.Get(Stat.MoveSpeed),
            worn.Count, string.Join(" ", worn), j.Draughts, keys, j.WorldTierOn ? "on" : "off", b.KitDamageMul, b.KitEveryMul);
    }
}
