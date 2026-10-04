using System;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/* The survivor's side of crafting (docs/CRAFTING_DESIGN.md): the Waystation's
 * hands quoted and done, with what the interface says about it, and the gear
 * folded back into the fight when a worn piece changes. The rules are
 * Rpg/Crafting.cs; this is only the journey keeping the survivor told. */
public sealed partial class Journey
{
    /// <summary>Crafting's view of the world: the survivor, and what the crafter charges them.</summary>
    public CraftCtx Craft => new(Ctx, PriceMod);

    readonly Rng craftRng = new((uint)Environment.TickCount);

    /// <summary>What the crafter said over the last craft (the bench shows it); null until one is done.</summary>
    public Said? CraftSaid { get; set; }

    /// <summary>Do a quoted craft on a piece the survivor has; what it did, said. False if it could not be done.</summary>
    public bool Work(string uid, Quote q, Battle? b)
    {
        var loc = Inventory.Find(Ch, uid);
        if (loc == null) return false;
        var it = loc.Item;
        if (!q.Ok) { Warn(q.Blocked!); return false; }
        string before = Inventory.Name(it);
        int heat = it.Heat ?? 0;
        if (!Crafting.Do(Craft, it, q, craftRng)) { Warn("It could not be done."); return false; }
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb);
        var def = Items.Get(it.Def);
        string? sub = q.Verb switch
        {
            Verb.BreakDown => string.Join(", ", q.Gives.Select(kv => $"{kv.Value} {Items.Get(kv.Key).Name}")),
            Verb.Remake => $"{Inventory.RarityName(it)} now. A seam opens.",
            Verb.Rekindle => $"Heat {it.Heat} of {it.HeatFull}",
            Verb.Cage when q.Affix == null => "Three more coals",
            _ => it.Heat == 0 ? "It's set now: nothing more can be worked into it." : $"{q.After} · heat {heat} to {it.Heat}",
        };
        string title = q.Verb switch
        {
            Verb.BreakDown => $"Broken down: {before}",
            Verb.Cage when q.Affix == null => Inventory.Name(it),
            _ => Inventory.Name(it),
        };
        OnToast(new Toast(ToastKind.Loot, title, sub, def.Icon, it.Rarity));
        if (!loc.InPack) RefreshKit(b); else OnTouch();
        return true;
    }

    /// <summary>What the arena's end carried out goes in the pouch; the night's name is kept
    /// with the shards, so a coal caged from them says where it came from.</summary>
    public void Carry(Crafting.NightYield y, string? night = null)
    {
        foreach (var (m, n) in y.Kept) Inventory.AddToPack(Ch, Inventory.Make(Ch, m, n));
        if (night != null && y.Kept.ContainsKey(Crafting.Shard)) World.Facts["shards.from"] = night;
        OnTouch();
    }
}
