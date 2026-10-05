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
        bool owed = World.LootDebt >= Rpg.Drops.Rules.Debt;
        var rolled = Rpg.Drops.Roll(x);
        // A Legendary falling is said under the HUD, once (docs/design/LOOT_DESIGN.md §8.2); the debt's
        // paying is said in its own words.
        if (rolled.Any(r => r.Tier is LootTier.Legendary or LootTier.Storied))
            OnAnnounce(new Announcement(owed ? Rpg.Drops.DebtPaid : Rpg.Drops.NamedFalls, "", "reward", 3.2));
        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(rolled, Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();
    }

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

    /// <summary>What a fight's end did with what was still lying.</summary>
    public sealed record Gathered(int Home, int Stored, int Broken, int Iron, int Shards, int Left);

    /// <summary>A fight's end (docs/design/LOOT_DESIGN.md §6.2): what the filter shows and is still
    /// lying comes home, into the pack while there is room, Rare and up beyond it to Rook's storeroom;
    /// the rest of it, and what the filter hid (if the survivor lets it), is broken down for old iron.
    /// Nothing shown is lost to the fight.</summary>
    public Gathered Gather(Battle b)
    {
        int home = 0, stored = 0, broken = 0, iron = 0, shards = 0, left = 0;
        foreach (var p in b.Pickups.Items)
        {
            if (!p.Alive) continue;
            if (p.Payload is not ItemInstance it)
            {
                // The people's material left lying is the night's too.
                if (p.Kind == PickupKind.Material && p.Ref != null) { Inventory.AddToPack(Ch, Inventory.Make(Ch, p.Ref, Math.Max(1, MathX.RoundInt(p.Value)))); b.Pickups.Release(p); }
                continue;
            }
            bool shown = p.Look != Verdict.Hidden;
            if (shown && Inventory.Free(Ch) > 0 && Inventory.AddToPack(Ch, it)) home++;
            else if (shown && it.Rarity >= 2 && World.Stash.IndexOf(null) is var j and >= 0) { World.Stash[j] = it; stored++; }
            else if (shown && Rpg.Drops.Jackpot(Rpg.Drops.TierOf(it))) { left++; continue; }
            else if (shown || Ch.Filter.BreakHidden)
            {
                int n = Crafting.Rules.BreakDown[Math.Clamp(it.Rarity, 0, Crafting.Rules.BreakDown.Count - 1)];
                int c = it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null);
                if (n > 0) Inventory.AddToPack(Ch, Inventory.Make(Ch, Crafting.Iron, n));
                if (c > 0) Inventory.AddToPack(Ch, Inventory.Make(Ch, Crafting.Shard, c));
                iron += n;
                shards += c;
                broken++;
            }
            else { left++; continue; }
            b.Pickups.Release(p);
        }
        if (home + stored + broken > 0) OnTouch();
        return new Gathered(home, stored, broken, iron, shards, left);
    }
}
