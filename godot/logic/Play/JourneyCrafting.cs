using System;
using System.Collections.Generic;
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
        // A trophy set has its own words, said the once ("fang.set").
        string? moment = q.Verb == Verb.Set && Crafting.Rules.Settings.GetValueOrDefault(q.Def ?? "") is { } s ? $"{s.Moment}.set" : null;
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment);
        // The slurry's outcome is said as what the survivor sees (the story lead's narration), after
        // whatever Snib says over it.
        string? seen = q.Verb == Verb.Steep ? Crafting.Line(Crafting.Rules.Slurry.Crafter, $"steep.{q.Outcome}") : null;
        if (seen != null) CraftSaid = (CraftSaid ?? new Said(null, null, null)) with { After = seen };
        if (q.Verb == Verb.Steep && q.Outcome == "down" && q.Crafter != "" && CraftSaid is { Before: null } said && Crafting.Line(q.Crafter, "steep.bad") is { } bad)
            CraftSaid = said with { Line = bad };
        var def = Items.Get(it.Def);
        string? sub = q.Verb switch
        {
            Verb.BreakDown => string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))),
            Verb.Steep => seen ?? "Steeped: it is set for good.",
            Verb.Bind => $"{q.After}. What it came from is gone.",
            Verb.Remake => $"{Inventory.RarityName(it)} now. A seam opens.",
            Verb.Rekindle => $"Heat {it.Heat} of {it.HeatFull}",
            Verb.Cage when q.Affix == null => "Three more coals",
            Verb.Set => q.After,
            _ => it.Heat == 0 ? "It's set now: nothing more can be worked into it." : $"{q.After} · heat {heat} to {it.Heat}",
        };
        string title = q.Verb switch
        {
            Verb.BreakDown => $"Broken down: {before}",
            Verb.Cage when q.Affix == null => Inventory.Name(it),
            _ => Inventory.Name(it),
        };
        OnToast(new Toast(ToastKind.Loot, title, sub, def.Icon, it.Rarity));
        if (loc.Worn) RefreshKit(b); else OnTouch();
        return true;
    }

    /// <summary>Do a quoted craft that makes something new (a brew, the flask, a commission put on
    /// the bench); what it did, said. False if it could not be done.</summary>
    public bool Make(Quote q)
    {
        if (!q.Ok) { Warn(q.Blocked!); return false; }
        if (!Crafting.Make(Craft, q)) { Warn("It could not be done."); return false; }
        var brew = q.Verb == Verb.Brew ? Crafting.BrewOf(q.Def!) : null;
        CraftSaid = q.Verb switch
        {
            Verb.Buy when q.Def == Crafting.Rules.Slurry.Jar => Crafting.Line(q.Crafter, "jar.sale") is { } js ? new Said(null, js, null) : null,
            Verb.Buy => CraftSaid,
            Verb.Commission => Crafting.Line(q.Crafter, "commission.take") is { } l ? new Said(null, l, null) : null,
            _ => Crafting.Speak(Craft, q.Crafter, q.Verb, brew?.Moment, brew?.Say),
        };
        var def = Items.Get(q.Def!);
        string title = q.Verb switch
        {
            Verb.Brew => q.Count == 1 ? def.Name : $"{def.Name} ×{q.Count}",
            Verb.Commission => q.After?.Split(':')[0] ?? def.Name,
            _ => def.Name,
        };
        string? sub = q.Verb switch
        {
            Verb.Brew => $"You carry {Inventory.Count(Ch, q.Def!)}",
            Verb.Buy when q.Def == Crafting.Rules.Slurry.Jar => CraftSaid?.Line ?? $"You carry {Inventory.Count(Ch, q.Def!)}",
            Verb.Commission => $"On {Crafting.Crafter(q.Crafter)?.Name ?? "the"}'s bench: ready tomorrow morning",
            _ => def.Description,
        };
        OnToast(new Toast(ToastKind.Loot, title, sub, def.Icon, q.Verb == Verb.Commission ? Crafting.Rules.Commission.Rarity : def.Rarity));
        OnTouch();
        return true;
    }

    /// <summary>A commission ready on the smith's bench, handed over (null if none is, or the pack is full).</summary>
    public ItemInstance? CollectCommission()
    {
        var it = Crafting.Collect(Craft);
        if (it == null) return null;
        if (Crafting.Line(Crafting.Rules.Commission.Crafter, "commission.ready") is { } l) CraftSaid = new Said(null, l, null);
        OnToast(new Toast(ToastKind.Loot, Inventory.Name(it), "Made for you", Items.Get(it.Def).Icon, it.Rarity));
        OnTouch();
        return it;
    }

    /// <summary>Wenna's flask, filled by the inn overnight: what the morning report says of it.</summary>
    string? Flask()
    {
        var (filled, dry) = Crafting.Refill(Ch);
        string crafter = Crafting.Rules.Flask.Crafter;
        if (filled > 0)
        {
            World.Facts.Remove("flask.dry.said");
            string n = filled switch { 1 => "one draught", 2 => "two draughts", 3 => "three draughts", _ => $"{filled} draughts" };
            return Crafting.Line(crafter, "flask.filled")?.Replace("{n} draughts", n).Replace("{n}", $"{filled}");
        }
        // Dry: said once, until it is filled again (a nag every morning would be a chore).
        if (dry && !World.Fact("flask.dry.said").Truthy)
        {
            World.Facts["flask.dry.said"] = true;
            return Crafting.Line(crafter, "flask.dry");
        }
        return null;
    }

    /// <summary>What the arena's end carried out goes in the pouch; the night's name is kept
    /// with the shards, so a coal caged from them says where it came from.</summary>
    public void Carry(Crafting.NightYield y, string? night = null)
    {
        foreach (var (m, n) in y.Kept) Inventory.AddToPack(Ch, Inventory.Make(Ch, m, n));
        if (night != null && y.Kept.ContainsKey(Crafting.Shard)) World.Facts["shards.from"] = night;
        OnTouch();
    }

    /* ----------------------------------------------------------- the two kits -- */

    /// <summary>A piece from the pack worn in one of the two kits (Rpg/Kits.cs), a ring to whichever hand
    /// of that kit is free; the fight takes it up at once if that kit is the one on.</summary>
    public void EquipKit(string uid, KitKind kit, EquipSlot? slot, Battle? b)
    {
        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if ((slot ?? Items.SlotFor(def)) is not EquipSlot t || !Items.Fits(def, t)) return;
        if (slot == null && t == EquipSlot.Ring1 && Kits.HasOwn(Ch, kit, EquipSlot.Ring1) && !Kits.HasOwn(Ch, kit, EquipSlot.Ring2)) t = EquipSlot.Ring2;
        if (!Kits.Put(Ch, kit, loc.Item, t)) { Warn("No room in your pack for what you are wearing"); return; }
        bool on = kit == Kits.On(Ch);
        OnToast(new Toast(ToastKind.Loot, on ? $"Wearing {Inventory.Name(loc.Item)}" : $"{Inventory.Name(loc.Item)}, worn {(kit == KitKind.Night ? "by night" : "by day")}",
            Icon: def.Icon, Rarity: loc.Item.Rarity));
        RefreshKit(b);
    }

    /// <summary>A kit's piece taken off into the pack; off the night kit, that slot wears the day's piece again.</summary>
    public void UnequipKit(KitKind kit, EquipSlot slot, Battle? b)
    {
        // (the night's own weapon can go: the day's is still in hand by night)
        if (kit == KitKind.Day && slot == EquipSlot.Weapon) { Warn("You will not walk this road unarmed"); return; }
        if (!Kits.Clear(Ch, kit, slot)) { Warn("Your pack is full"); return; }
        RefreshKit(b);
    }
}
