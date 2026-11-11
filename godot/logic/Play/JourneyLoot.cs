using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The survivor's side of loot (docs/design/LOOT_DESIGN.md): what a carrier leaves, judged by the
 * survivor's own filter where it falls; gear taken as it was rolled; and at a fight's end, what is
 * still lying gathered home or broken down. The rules are Rpg/Loot.cs and Rpg/LootFilter.cs. */
public sealed partial class Journey
{
    /// <summary>What a carrier leaves here, as the fight spawns it: rolled whole, and judged by the
    /// survivor's filter (a base first seen at a make always shows).</summary>
    public List<Sim.Loot> Drops(DropCtx x)
    {
        x.Ch ??= Ch;
        x.World ??= World;
        if (x.Allows == null) x.Allows = c => Rules.Test(c, Ctx);
        if (WorldTierOn)
        {
            var wt = Content.WorldTiers.Get(Content.WorldTiers.Of(World));
            x.Rarity *= wt.Rare; x.LegendaryMul *= wt.Legendary; x.Level += wt.ItemLevels;
        }
        bool owed = World.LootDebt >= Rpg.Drops.Rules.Debt;
        var rolled = Rpg.Drops.Roll(x);
        // A Legendary falling is said under the HUD, once (docs/design/LOOT_DESIGN.md §8.2); the debt's
        // paying is said in its own words.
        if (!x.Hush && rolled.Any(r => r.Tier is LootTier.Legendary or LootTier.Storied))
            OnAnnounce(new Announcement(owed ? Rpg.Drops.DebtPaid : Rpg.Drops.NamedFalls, "", "reward", 3.2));
        // In the night's arenas the materials are the night's end tally, not the ground's (crafting decision 7).
        if (x.Tally)
        {
            foreach (var r in rolled.Where(r => r.Material != null)) NightTally[r.Material!] = NightTally.GetValueOrDefault(r.Material!) + r.Qty;
            rolled = rolled.Where(r => r.Material == null).ToList();
        }
        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(rolled, Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();
    }

    /// <summary>The materials the night's carriers left in place of gear, paid at its end with the rest
    /// of the night's yield (and half spilled on a fall).</summary>
    public Dictionary<string, int> NightTally { get; } = new();

    /// <summary>The filter's word on a piece where it falls; a first sighting is remembered.</summary>
    public Verdict Judge(ItemInstance it)
    {
        bool first = false;
        if (Items.SlotFor(Items.Get(it.Def)) != null)
            first = Ch.Seen.Add($"{it.Def}@{Rpg.Drops.MakeOf(it).Key()}");
        return Ch.Filter.Judge(it, Ch, first);
    }

    /// <summary>A whole thing taken from the ground, as it was rolled. False if it would not fit.</summary>
    public bool Take(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        int qty = it.Qty;
        if (!Inventory.AddToPack(Ch, it)) { OnToast(new Toast(ToastKind.Warning, "Your pack is full", def.Name)); return false; }
        var tier = Rpg.Drops.TierOf(it);
        string? sub = tier switch
        {
            LootTier.Legendary => def.Description,
            LootTier.Set => Rpg.Drops.SetOf(def) is { } set ? $"{set.Name}: {Rpg.Drops.SetsWorn(Ch).GetValueOrDefault(set.Id)} of {set.Pieces.Count} worn" : def.Description,
            _ when Items.SlotFor(def) != null => $"{Inventory.RarityName(it)} {def.Kind.Key()} · {Rpg.Drops.MakeOf(it)} · level {Rpg.Drops.LevelOf(it)}",
            _ => null,
        };
        OnToast(new Toast(ToastKind.Loot, $"{Inventory.Name(it)}{(qty > 1 ? $" ×{qty}" : "")}", sub, def.Icon, it.Rarity));
        OnTouch();
        return true;
    }

    /// <summary>What a fight's end did with what was still lying. Held: protected pieces Rook keeps by the door
    /// (her shelves full), shelved as room is made.</summary>
    public sealed record Gathered(int Home, int Stored, int Broken, int Iron, int Shards, int Left, int Held = 0);

    /// <summary>Loot never lost at a fight's end: Rare and up, or a jackpot tier.</summary>
    static bool Protected(ItemInstance it) => it.Rarity >= 2 || Rpg.Drops.Jackpot(Rpg.Drops.TierOf(it));

    /// <summary>A protected piece to Rook: a free place on her shelves, else held by the door. True: shelved.</summary>
    bool Keep(ItemInstance it)
    {
        int j = World.Stash.IndexOf(null);
        if (j >= 0) { World.Stash[j] = it; return true; }
        World.Held.Add(it);
        return false;
    }

    /// <summary>What Rook was holding put on the shelves' free places, oldest first (the storeroom opened,
    /// a place freed, a shelf bought). How many went up.</summary>
    public int ShelveHeld()
    {
        int n = 0;
        while (World.Held.Count > 0 && World.Stash.IndexOf(null) is var j and >= 0)
        {
            World.Stash[j] = World.Held[0];
            World.Held.RemoveAt(0);
            n++;
        }
        if (n > 0) OnTouch();
        return n;
    }

    void SayHeld(int held)
    {
        if (held > 0) OnToast(new Toast(ToastKind.Loot, $"Rook is holding {held} {(held == 1 ? "thing" : "things")} for you", "Her shelves are full. Make room in the storeroom."));
    }

    /// <summary>A fight's end (docs/design/LOOT_DESIGN.md §6.2): what the filter shows and is still
    /// lying comes home, into the pack while there is room, Rare and up beyond it to Rook's storeroom;
    /// the rest of it, and what the filter hid (if the survivor lets it), is broken down for old iron.
    /// Nothing shown is lost to the fight.</summary>
    public Gathered Gather(Battle b)
    {
        int home = 0, stored = 0, broken = 0, iron = 0, shards = 0, left = 0, held = 0;
        foreach (var p in b.Pickups.Items)
        {
            if (!p.Alive) continue;
            if (p.Payload is not ItemInstance it)
            {
                // The people's material left lying is the night's too.
                if (p.Kind == PickupKind.Material && p.Ref != null) { Inventory.AddToPack(Ch, Inventory.Make(Ch, p.Ref, Math.Max(1, MathX.RoundInt(p.Value)))); b.Pickups.Release(p); }
                // A chart or a ruler's thing left lying comes home as if picked up (they go to the
                // satchel, which never fills): left, the ruler's charts and Marks were lost with the map.
                else if (p.Kind == PickupKind.Item && p.Ref != null && p.Look != Verdict.Hidden && PickedUp(p)) { home++; b.Pickups.Release(p); }
                continue;
            }
            bool shown = p.Look != Verdict.Hidden;
            if (shown && Inventory.Free(Ch) > 0 && Inventory.AddToPack(Ch, it)) home++;
            // Protected and shown: to Rook, never broken or left with the zone (SU-019).
            else if (shown && Protected(it)) { if (Keep(it)) stored++; else held++; }
            else if (shown || Ch.Filter.BreakHidden)
            {
                // (crafting's yield, the same as at the bench)
                var yield = Crafting.Yield(it);
                int n = yield.GetValueOrDefault(Crafting.Iron), c = yield.GetValueOrDefault(Crafting.Shard);
                if (n > 0) Inventory.AddToPack(Ch, Inventory.Make(Ch, Crafting.Iron, n));
                if (c > 0) Inventory.AddToPack(Ch, Inventory.Make(Ch, Crafting.Shard, c));
                iron += n;
                shards += c;
                broken++;
            }
            else { left++; continue; }
            b.Pickups.Release(p);
        }
        if (home + stored + broken + held > 0) OnTouch();
        SayHeld(held);
        return new Gathered(home, stored, broken, iron, shards, left, held);
    }

    /// <summary>(M9, ARPG 7.1) A zone left: Rare and better still lying (and shown) goes to Rook's storeroom, held by
    /// the door while her shelves are full (no shelves are added; SU-019); the rest is lost with the ground. Returns
    /// how many went onto the shelves.</summary>
    public int Abandon(Battle b)
    {
        int kept = 0, held = 0;
        foreach (var p in b.Pickups.Items)
        {
            if (!p.Alive || p.Payload is not ItemInstance it || p.Look == Verdict.Hidden) continue;
            if (!Protected(it)) continue;
            // (her shelves full: held by the door, not lost with the ground, SU-019)
            if (Keep(it)) kept++; else held++;
            b.Pickups.Release(p);
        }
        SayHeld(held);
        if (kept > 0)
        {
            OnToast(new Toast(ToastKind.Loot, $"Rook kept {kept} {(kept == 1 ? "thing" : "things")} you left"));
            OnTouch();
        }
        return kept;
    }
}
