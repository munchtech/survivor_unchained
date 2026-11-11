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
 * carried by day in a few slots (more as the survivor grows), at a rank
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

    /// <summary>Does the survivor measure up to it (now: gear and points move this).</summary>
    public static bool Meets(CharacterData ch, string id) => Have(ch, Attribute(id)) >= Need;

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
        if (ch.Slotted.Count < Slots(ch)) ch.Slotted.Add(id);
        return true;
    }

    /// <summary>How many learned skills can be carried by day: two from the start (her grip and her
    /// type's first), three from the fourth level, four from the fifth, five from the seventh and
    /// six from the ninth (a build is 2-3 pressed, the rest kindled), so a map build has room (CLASS_IDENTITY_AND_TALENTS.md §3.7).</summary>
    public static int Slots(CharacterData ch) => SlotsAt(ch.Level);
    public static int SlotsAt(int level) => level >= 9 ? 6 : level >= 7 ? 5 : level >= 5 ? 4 : level >= 4 ? 3 : 2;

    /// <summary>A learned skill's points (its rank by day, held or burning) at a level: one at the first, then one every
    /// second level, to MaxRank (8) at the fifteenth (docs/design/ARPG.md 3.5; skill_lamps.json rules.points).</summary>
    public static int PointsAt(int level) => Math.Min(Weapons.MaxRank, 1 + (Math.Max(1, level) - 1) / 2);

    /// <summary>A learned skill's points by day: it grows with the survivor. The rank a day fight takes is
    /// WickBook.DayRank (the points she still holds unlit do not burn).</summary>
    public static int Rank(CharacterData ch) => PointsAt(ch.Level);

    /// <summary>(M9) A carried skill's rank by day with what her gear adds (Character.SkillPlus), to MaxRank:
    /// rank is lit lamps on its wick, so a "+1" lights one more.</summary>
    public static int RankOf(CharacterData ch, string skill) => Math.Min(Weapons.MaxRank, Rank(ch) + Character.SkillPlus(ch, skill));

    public static bool Slot(CharacterData ch, string id)
    {
        if (!Knows(ch, id) || !Carries(ch, id) || ch.Slotted.Contains(id) || ch.Slotted.Count >= Slots(ch)) return false;
        ch.Slotted.Add(id);
        return true;
    }

    public static void Unslot(CharacterData ch, string id) => ch.Slotted.Remove(id);

    /// <summary>What is carried by day and can be used: slotted, measured up to, the
    /// calling's to carry (one that is not lies idle, as one not measured up to
    /// does: an old save keeps it, unused), within the slots. Its rank is WickBook.DayRank (Rank when nothing is held).</summary>
    public static IEnumerable<(string Id, int Rank)> Carried(CharacterData ch) =>
        ch.Slotted.Where(id => Weapons.All.ContainsKey(id) && Knows(ch, id) && Meets(ch, id) && Carries(ch, id)).Take(Slots(ch)).Select(id => (id, WickBook.DayRank(ch, id)));

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
