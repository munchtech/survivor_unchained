using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/// <summary>Why a Union can't be joined or unjoined (None: it can).</summary>
public enum UnionNo { None, Unknown, Level, Calling, NotCarried, NoTurn, Shared, Joined, NotJoined, Price }

/* The campaign's Unions (docs/design/ARPG.md 3.3, BUILD_DIRECTION.md "Unions", BUILD_UNLOCKS.md level 15).
 *
 * A Union opens at level 15, for two skills she carries whose Turns both burn (the 4th lamp of a strand lit on each
 * wick: "both evolved" in the campaign). The first time she joins one she learns it, and pays its price in rare items
 * from her pack (skills.json "price", 2 by default); after that it is hers, and joining or unjoining it is free at any
 * lit lamp-post, as every respec is (Play/PostMenu.cs asks for the post). Learned Unions are the character's
 * (CharacterData.UnionsKnown); the joined ones are the lamp layout's (LampLayout.Unions), since a layout is a whole build.
 * No limiter on which pairs (the owner, 13 Nov: same school is fine), but a skill is half of one joined Union at a time.
 *
 * In a fight a joined Union keeps both keys, one per half, with its bond (Battle.GrantUnion: Slot is A's key, Slot2 B's),
 * at the rank of its better half. The arena's night draft (LevelUp.ReadyUnions, Battle.Unite) keeps its own rule. */
public static class UnionJoin
{
    /// <summary>The level Unions open at: BUILD_UNLOCKS.md's ladder (level 15). One copy only: when the ladder is in
    /// code (bd-ranks), read it from there.</summary>
    public const int Level = 15;

    /// <summary>The rarity scale's tiers (items.json "raritynames"): Rare and above pay; Storied (a named thing with a
    /// history) never does.</summary>
    public const int Rare = 2, Legendary = 4;

    public static bool Open(CharacterData ch) => ch.Level >= Level;

    public static bool Known(CharacterData ch, string id) => ch.UnionsKnown.Contains(id);

    /// <summary>The Unions joined on a layout (the active one by default).</summary>
    public static IReadOnlyList<string> Joined(CharacterData ch, LampLayout? l = null) => (l ?? LampBook.Now(ch)).Unions ??= new();

    /// <summary>The skill's Turn burns by day: among the lamps a day fight lights (WickBook.DayPath to DayRank).</summary>
    public static bool TurnBurning(CharacterData ch, string skill) =>
        WickBook.DayPath(ch, skill).Take(WickBook.DayRank(ch, skill)).Any(id => Wicks.IsTurn(skill, id));

    /// <summary>What a Union costs her the first time: 0 once known.</summary>
    public static int PriceFor(CharacterData ch, UnionDef u) => Known(ch, u.Id) ? 0 : Math.Max(0, u.Price);

    /// <summary>What may pay: unequipped gear in her pack, Rare to Legendary, the cheapest first (rarity, then value).</summary>
    public static List<ItemInstance> Payable(CharacterData ch) =>
        ch.Pack.Where(it => it != null && it.Rarity >= Rare && it.Rarity <= Legendary && Items.Find(it.Def) is { } d && Items.SlotFor(d) != null)
            .Select(it => it!).OrderBy(it => it.Rarity).ThenBy(it => Items.Find(it.Def)!.Value).ToList();

    /// <summary>The Unions on offer to her: her calling's, either half carried. (Ready or not: Why says what is missing.)</summary>
    public static List<UnionDef> Offered(CharacterData ch) =>
        Unions.All.Where(u => Weapons.CanCarry(ch.Archetype, u.Id) && (ch.Slotted.Contains(u.A) || ch.Slotted.Contains(u.B) || Known(ch, u.Id))).ToList();

    /// <summary>Whether the Union may be joined now (the post is PostMenu's to ask), price aside when the pack can pay it.</summary>
    public static UnionNo CanJoin(CharacterData ch, string id)
    {
        if (Unions.Find(id) is not { } u) return UnionNo.Unknown;
        if (!Open(ch)) return UnionNo.Level;
        if (!Weapons.CanCarry(ch.Archetype, u.Id)) return UnionNo.Calling;
        var joined = Joined(ch);
        if (joined.Contains(id)) return UnionNo.Joined;
        if (!ch.Slotted.Contains(u.A) || !ch.Slotted.Contains(u.B)) return UnionNo.NotCarried;
        if (!TurnBurning(ch, u.A) || !TurnBurning(ch, u.B)) return UnionNo.NoTurn;
        if (joined.Select(Unions.Find).Any(o => o != null && (o.A == u.A || o.A == u.B || o.B == u.A || o.B == u.B))) return UnionNo.Shared;
        if (Payable(ch).Count < PriceFor(ch, u)) return UnionNo.Price;
        return UnionNo.None;
    }

    /// <summary>Join the Union on the active layout. The first time, it is learned and paid for: with the pack items
    /// named (their Uids, exactly the price, each payable), or the cheapest payable when none are named.</summary>
    public static UnionNo Join(CharacterData ch, string id, IReadOnlyCollection<string>? pay = null)
    {
        var no = CanJoin(ch, id);
        if (no != UnionNo.None) return no;
        var u = Unions.Find(id)!;
        int price = PriceFor(ch, u);
        if (price > 0)
        {
            var can = Payable(ch);
            List<ItemInstance> paid;
            if (pay == null) paid = can.Take(price).ToList();
            else
            {
                paid = can.Where(it => pay.Contains(it.Uid)).ToList();
                if (pay.Distinct().Count() != price || paid.Count != price) return UnionNo.Price;
            }
            foreach (var it in paid) ch.Pack[ch.Pack.IndexOf(it)] = null;
            ch.UnionsKnown.Add(id);
        }
        LampBook.Now(ch).Unions.Add(id);
        return UnionNo.None;
    }

    public static UnionNo CanUnjoin(CharacterData ch, string id) =>
        Unions.Find(id) == null ? UnionNo.Unknown : Joined(ch).Contains(id) ? UnionNo.None : UnionNo.NotJoined;

    /// <summary>Unjoin the Union on the active layout: free; it stays learned.</summary>
    public static UnionNo Unjoin(CharacterData ch, string id)
    {
        var no = CanUnjoin(ch, id);
        if (no == UnionNo.None) LampBook.Now(ch).Unions.Remove(id);
        return no;
    }

    /// <summary>The joined Unions a fight takes now: both halves still carried and burning their Turns (a respec that
    /// puts a Turn out leaves the Union joined but asleep, and the halves fight apart).</summary>
    public static List<UnionDef> Live(CharacterData ch) =>
        !Open(ch) ? new() : Joined(ch).Select(Unions.Find).Where(u => u != null && ch.Slotted.Contains(u.A) && ch.Slotted.Contains(u.B)
            && TurnBurning(ch, u.A) && TurnBurning(ch, u.B)).Select(u => u!).ToList();

    /// <summary>The battle's side: each Union whose two halves are in the fight joins them (Battle.GrantUnion keeps their
    /// keys, A's and B's, and their lit lamps), at the rank of its better half. Returns the Unions put in.</summary>
    public static List<WeaponInst> Apply(Battle b, IEnumerable<UnionDef> live)
    {
        var o = new List<WeaponInst>();
        foreach (var u in live)
        {
            var a = b.Weapons.Find(w => w.Id == u.A);
            var c = b.Weapons.Find(w => w.Id == u.B);
            if (a == null || c == null || b.Weapons.Exists(w => w.Id == u.Into)) continue;
            int rank = Math.Max(a.Rank, c.Rank);
            if (b.GrantUnion(u.Id) is not { } w) continue;
            // (Not Battle.SetRank: a Union has no wick path of its own to relight; CarryTurns lit it from its parts.)
            w.Rank = rank;
            if (w.Half != null) w.Half.Rank = rank;
            o.Add(w);
        }
        return o;
    }

    public static List<WeaponInst> Apply(Battle b, CharacterData ch) => Apply(b, Live(ch));

    /// <summary>Why, in plain words (null: it can).</summary>
    public static string? Why(UnionNo no, UnionDef? u = null) => no switch
    {
        UnionNo.None => null,
        UnionNo.Level => $"Unions open at level {Level}",
        UnionNo.Calling => "Not for your calling",
        UnionNo.NotCarried => u == null ? "Carry both its skills" : $"Carry {Weapons.Get(u.A).Name} and {Weapons.Get(u.B).Name}",
        UnionNo.NoTurn => "Both its skills need a Turn burning",
        UnionNo.Shared => "One of its skills is in another Union",
        UnionNo.Joined => "Joined already",
        UnionNo.NotJoined => "Not joined",
        UnionNo.Price => u == null ? "Not enough rare items in your pack" : $"Costs {u.Price} rare items from your pack",
        _ => "No such Union",
    };
}
