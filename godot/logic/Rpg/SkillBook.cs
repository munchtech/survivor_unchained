using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* The skills a survivor has learned for the day.
 *
 * The ember's cards stay in the arenas; what comes out is knowing them. A
 * combat skill seen burning in an arena (discovered) can be learned in the
 * world: from a tome (a story fight won, a curiosity shop, a quest's
 * reward), from the survivor's calling as they grow (every third level it
 * teaches one of its own kind they have seen), or worn (gear that grants a
 * skill needs no learning, and goes with the gear). Learned skills are
 * carried by day in a few keys (more as the survivor grows), at a rank
 * that grows with them; each asks something of the one who uses it (a
 * spell asks wits, a blade might, a thrown thing finesse, a prayer or a
 * living thing resolve), and one the survivor no longer measures up to
 * (gear changed, points put elsewhere) lies idle until they do. */
public static class SkillBook
{
    /// <summary>What a skill asks of the attribute it leans on.</summary>
    public const int Need = 6;

    public static string Tome(string id) => $"tome_{id}";

    /// <summary>The attribute a skill leans on: spells on wits, holy and living
    /// things on resolve, blades and shields on might, what is thrown or shot on finesse.</summary>
    public static string Attribute(string id)
    {
        var w = Weapons.All[id];
        if (w.Tags.Contains(Tag.Spell)) return "Wits";
        if (w.School is School.Holy or School.Nature) return "Resolve";
        // (M3) A shield's skill too (Iron Vow, not a melee blow, leaned on finesse and lay idle on a warden).
        if (w.Tags.Contains(Tag.Melee) || w.Tags.Contains(Tag.Shield)) return "Might";
        return "Finesse";
    }

    public static int Have(CharacterData ch, string attribute) => attribute switch
    {
        "Might" => ch.Attributes.Might, "Finesse" => ch.Attributes.Finesse, "Wits" => ch.Attributes.Wits, _ => ch.Attributes.Resolve,
    };

    /// <summary>Does the survivor measure up to it (now: gear and points move this). (bd-keys) A skill her calling's taught
    /// build teaches always does: the calling put it in her hands, so a taught key never lies idle (Dawnpulse leans on wits,
    /// which a warden has three of).</summary>
    public static bool Meets(CharacterData ch, string id) => Have(ch, Attribute(id)) >= Need
        || TaughtBuilds.Of(ch.Archetype) is { } t && (t.Keys.Exists(s => s.Skill == id));

    public static bool Knows(CharacterData ch, string id) => ch.Skills.Contains(id);

    /// <summary>The survivor's calling may carry it (Weapons.CanCarry: a kindred skill is two callings').</summary>
    public static bool Carries(CharacterData ch, string id) => Weapons.CanCarry(ch.Archetype, id);

    /// <summary>Seen burning in an arena, not yet learned, and the calling's to carry.</summary>
    public static bool CanLearn(CharacterData ch, string id) => Weapons.All.TryGetValue(id, out var w) && w.Findable && ch.Discovered.Contains(id) && !Knows(ch, id) && Carries(ch, id);

    public static bool Learn(CharacterData ch, string id)
    {
        if (!CanLearn(ch, id)) return false;
        ch.Skills.Add(id);
        // A free slot takes it straight into hand.
        TakeUp(ch, id);
        return true;
    }

    /* (bd-keys, docs/design/SKILL_KINDS.md) Her bar: five keys, all pressed, the basic attack held in the first; a union
     * takes two keys; the keys open at levels 1, 4, 5 and 9, the ninth opening two (Iron Vow and Shield Charge). Every carried skill is in ch.Slotted, in key order. A skill
     * that only ever runs itself (Weapons.AutoOnly) is never slotted. Skills her gear grants that run themselves stack
     * beside the keys with no cap (Character.Bar). */

    /// <summary>The keys open at a level (BUILD_UNLOCKS.md, BUILD_DIRECTION.md Round 10): the basic attack's at the first, then the fourth, fifth and ninth (two keys at the ninth: Iron Vow and Shield Charge).</summary>
    public static int KeysAt(int level) => level >= 9 ? 5 : level >= 5 ? 3 : level >= 4 ? 2 : 1;

    /// <summary>How many learned skills she carries by day: the keys open at her level.</summary>
    public static int Slots(CharacterData ch) => KeysAt(ch.Level);

    /// <summary>The old keys-plus-autos ladder (four keys 1/4/5/9 plus autos 1/7/10; before the five-key bar), kept only so map and harness scaling hold
    /// (MapRun's DayMul, the arena and day-sim harnesses); flagged for a re-tune. Two from the start, three at the fourth
    /// level, four at the fifth, five at the seventh, six at the ninth, seven at the tenth.</summary>
    public static int OldBarSlotsAt(int level) => level >= 10 ? 7 : level >= 9 ? 6 : level >= 7 ? 5 : level >= 5 ? 4 : level >= 4 ? 3 : 2;

    /// <summary>The keys her carried skills take (a union two).</summary>
    public static int KeysUsed(CharacterData ch) => ch.Slotted.Where(id => Weapons.All.ContainsKey(id)).Sum(Weapons.SlotCost);

    /// <summary>Room for it among the keys at her level. A skill that only runs itself is never slotted.</summary>
    public static bool HasRoom(CharacterData ch, string id) => HasRoom(ch, id, ch.Level);
    public static bool HasRoom(CharacterData ch, string id, int level) => !Weapons.AutoOnly(id) && KeysUsed(ch) + Weapons.SlotCost(id) <= KeysAt(level);

    /// <summary>A skill just come into her hands takes a free key. False when there is none (it waits learned).</summary>
    public static bool TakeUp(CharacterData ch, string id)
    {
        if (ch.Slotted.Contains(id) || !Weapons.All.ContainsKey(id) || !HasRoom(ch, id)) return false;
        ch.Slotted.Add(id);
        return true;
    }

    /// <summary>Put one carried skill down and another in its place (the basic attack's key holds whatever she puts in it:
    /// the key keeps its number). The new one must be hers to carry, known or worn, and fit the keys.</summary>
    public static bool Swap(CharacterData ch, string from, string to)
    {
        int i = ch.Slotted.IndexOf(from);
        if (i < 0 || ch.Slotted.Contains(to) || !Weapons.All.ContainsKey(to) || !(Knows(ch, to) || Character.Worn(ch, to)) || !Carries(ch, to) || Weapons.AutoOnly(to)) return false;
        ch.Slotted[i] = to;
        if (KeysUsed(ch) > KeysAt(ch.Level)) { ch.Slotted[i] = from; return false; }
        return true;
    }

    /// <summary>A learned skill's points (its rank by day, held or burning) at a level: one at the first, then one every
    /// second level, to MaxRank (8) at the fifteenth (docs/design/ARPG.md 3.5; skill_lamps.json rules.points).</summary>
    public static int PointsAt(int level) => Math.Min(Weapons.MaxRank, 1 + (Math.Max(1, level) - 1) / 2);

    /// <summary>A learned skill's points by day: it grows with the survivor. The rank a day fight takes is
    /// WickBook.DayRank (the points she still holds unlit do not burn).</summary>
    public static int Rank(CharacterData ch) => PointsAt(ch.Level);

    /// <summary>(M9) A carried skill's rank by day with what her gear adds (Character.SkillPlus), to MaxRank:
    /// rank is lit lamps on its wick, so a "+1" lights one more.</summary>
    public static int RankOf(CharacterData ch, string skill) => Math.Min(Weapons.MaxRank, Rank(ch) + Character.SkillPlus(ch, skill));

    /// <summary>(bd-keys) Her second weapon set's stance, once the ladder opens it (taught_builds.json "stance": the
    /// Warden's at the eighth level): (bd-wire) the one the weapon she wears as her second set picks (WornStance), else the
    /// one she chose among her calling's offers, else its default. Null before.</summary>
    public static string? StanceOf(CharacterData ch)
    {
        if (TaughtBuilds.Of(ch.Archetype)?.Stance is not { } s || ch.Level < s.Level) return null;
        string id = WornStance(ch) is { } w && s.Offers.Contains(w) ? w
            : ch.Stance != "" && s.Offers.Contains(ch.Stance) ? ch.Stance : s.Default;
        return Stances.Find(id) != null ? id : null;
    }

    /// <summary>(bd-wire) The stance the piece she wears as her second set (the off-hand slot) picks by its weapon kind
    /// (its icon, else its base's: Content/Stances.ForKind; a shield the shield, a second blade twin blades, a mace or
    /// hammer the mace), or null when she wears none or its kind picks no stance. The ladder and her calling's offers
    /// still decide whether it opens (StanceOf).</summary>
    public static string? WornStance(CharacterData ch)
    {
        if (ch.Equipment[EquipSlot.Offhand] is not { } it || !Items.All.TryGetValue(it.Def, out var def)) return null;
        return Stances.ForKind(def.Icon)
            ?? (def.Of != null && Items.All.TryGetValue(def.Of, out var b) ? Stances.ForKind(b.Icon) : null);
    }

    /// <summary>(bd-keys) Take up another stance weapon for set B (one of her calling's offers; free at any lamp-post, like
    /// every respec). False when it is not offered.</summary>
    public static bool SetStance(CharacterData ch, string id)
    {
        if (TaughtBuilds.Of(ch.Archetype)?.Stance is not { } s || !s.Offers.Contains(id) || Stances.Find(id) == null) return false;
        ch.Stance = id;
        return true;
    }

    /// <summary>Carry a skill she knows (or her gear grants: it goes with the gear) in a key, if one is free.</summary>
    public static bool Slot(CharacterData ch, string id)
    {
        if (!(Knows(ch, id) || Character.Worn(ch, id)) || !Carries(ch, id) || ch.Slotted.Contains(id) || !Weapons.All.ContainsKey(id) || !HasRoom(ch, id)) return false;
        ch.Slotted.Add(id);
        return true;
    }

    public static void Unslot(CharacterData ch, string id) => ch.Slotted.Remove(id);

    /// <summary>What is carried by day and can be used: slotted, learned, measured up to, the calling's to carry (one that
    /// is not lies idle, as one not measured up to does: an old save keeps it, unused), within the keys
    /// open at her level, in ch.Slotted's order (the keys in key order). Its rank is WickBook.DayRank (Rank when nothing is
    /// held). A worn skill she put in a key is Character.Bar's, not this.</summary>
    public static IEnumerable<(string Id, int Rank)> Carried(CharacterData ch)
    {
        int keys = KeysAt(ch.Level);
        foreach (var id in ch.Slotted.ToList())
        {
            if (!Weapons.All.ContainsKey(id) || !Carries(ch, id)) continue;
            // (a worn skill she put in a key holds it, though Character.Bar, not this, takes it up)
            bool use = Knows(ch, id) && Meets(ch, id);
            if (!use && (Knows(ch, id) || !Character.Worn(ch, id))) continue;
            if (Weapons.AutoOnly(id)) continue;
            if (Weapons.SlotCost(id) <= keys) { keys -= Weapons.SlotCost(id); if (use) yield return (id, WickBook.DayRank(ch, id)); }
        }
    }

    /// <summary>The skills attuned for the night: those carried by day (and
    /// measured up to). In an arena the ember offers them in its first drafts,
    /// and each comes in at NightRank.</summary>
    public static IEnumerable<string> Attuned(CharacterData ch) => Carried(ch).Select(c => c.Id).Where(id => Weapons.All[id].Findable);

    /// <summary>The rank an attuned skill comes in at by night: two, and three
    /// once the survivor has grown (the tenth level), so the day's growth is
    /// felt in the dark without the ember starting anywhere but low.</summary>
    public static int NightRank(CharacterData ch) => ch.Level >= 10 ? 3 : 2;

    /// <summary>Every third level the calling teaches one of its own kind the
    /// survivor has seen burn (and is up to): its id, or null.</summary>
    public static string? Calling(CharacterData ch)
    {
        if (ch.Level % 3 != 0) return null;
        var favours = Callings.Archetype(ch.Archetype).Favours;
        // Its own paths first, then its kind of skill.
        double Own(string id) => (Paths.All.Any(p => p.Callings.Contains(ch.Archetype) && p.Weapons.Contains(id)) ? 2 : 0) + Weapons.All[id].Tags.Count(favours.Contains);
        var pick = ch.Discovered.Where(id => CanLearn(ch, id) && Meets(ch, id))
            .OrderByDescending(Own).ThenBy(id => id).FirstOrDefault();
        if (pick == null || Own(pick) == 0) return null;
        Learn(ch, pick);
        return pick;
    }
}
