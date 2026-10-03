using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The pack (the web game's overlays/Inventory.tsx): the survivor as they
/// stand in the middle with what they wear round them, what they carry on
/// the right, and the chosen thing's card with what can be done with it.
/// Hover to read and compare (the worn thing beside it), click to choose,
/// double-click or right-click to wear or use. With a pad: move over the
/// slots, the card follows; A wears or uses (or takes off), X leaves it behind.
/// </summary>
public partial class InventoryScreen : Overlay
{
    public override string Kind => "inventory";
    public override Act? Toggle => Act.Inventory;
    string? sel;

    static readonly EquipSlot[] Left = { EquipSlot.Head, EquipSlot.Amulet, EquipSlot.Body, EquipSlot.Cloak };
    static readonly EquipSlot[] Right = { EquipSlot.Weapon, EquipSlot.Offhand, EquipSlot.Ring1, EquipSlot.Ring2, EquipSlot.Relic };
    public static readonly System.Collections.Generic.Dictionary<EquipSlot, (string Name, string Glyph)> Slots = new()
    {
        [EquipSlot.Weapon] = ("Weapon", "sword"), [EquipSlot.Offhand] = ("Off-hand", "shield"), [EquipSlot.Head] = ("Head", "helm"), [EquipSlot.Body] = ("Body", "armor"),
        [EquipSlot.Cloak] = ("Cloak", "cloak"), [EquipSlot.Amulet] = ("Amulet", "amulet"), [EquipSlot.Ring1] = ("Ring", "ring"), [EquipSlot.Ring2] = ("Ring", "ring"), [EquipSlot.Relic] = ("Relic", "relic"),
    };

    public InventoryScreen(Game g) : base(g) { Nav.Prefer = "pack:0"; }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var body = Frame("Pack", new Vector2(1320, 660), G.Key(Act.Inventory));
        var row = Style.H(24);
        row.SizeFlagsVertical = SizeFlags.ExpandFill;
        body.AddChild(row);

        // The survivor, with what they wear round them.
        var doll = Style.V(10);
        var dollRow = Style.H(12, Column(Left, ch), Figure(ch), Column(Right, ch));
        doll.AddChild(dollRow);
        doll.AddChild(Stats(ch));
        row.AddChild(doll);

        // What they carry.
        var pack = Style.V(8);
        pack.AddChild(ItemViews.Grid(ch.Pack, 6, 64, it => it.Uid == sel, null, it => Select(it.Uid), Primary,
            (it, over) => Tip(it != null && it.Uid != sel ? ItemViews.Compare(it, ch, true) : null, over), "pack", Drop));
        pack.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 17, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, Style.Small, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} / {ch.Pack.Count} carried", Style.Ui, Style.Caption, Style.InkDim)));
        row.AddChild(pack);

        // The chosen thing.
        var detail = Style.V(8);
        detail.CustomMinimumSize = new Vector2(360, 0);
        var found = sel != null ? Inventory.Find(ch, sel) : null;
        if (found != null)
        {
            var def = Items.Get(found.Item.Def);
            var acts = Style.H(8);
            if (found.InPack && def.Kind == ItemKind.Consumable) acts.AddChild(Style.Button("Use", () => G.Gear((j, b) => j.Use(found.Item.Uid, b)), true, true));
            if (found.InPack && Items.SlotFor(def) != null) acts.AddChild(Style.Button("Wear", () => G.Gear((j, b) => j.Equip(found.Item.Uid, null, b)), true, true));
            if (!found.InPack && found.Slot != EquipSlot.Weapon) acts.AddChild(Style.Button("Take off", () => G.Gear((j, b) => j.Unequip(found.Slot, b)), false, true));
            if (found.InPack && def.Kind != ItemKind.Quest) acts.AddChild(Style.Button("Leave behind", () => { sel = null; G.Journey.Drop(found.Item.Uid); }, false, true));
            detail.AddChild(ItemViews.Card(found.Item, ch, found.InPack, acts, 360));
        }
        else
        {
            detail.AddChild(Style.Gap(80));
            detail.AddChild(Glyphs.Icon("hand", 28, Style.GoldDim));
            detail.AddChild(Style.Label("Choose something to look at it closely.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Gear stays with you. Ember fades when you rest; what you carry, and what you wear, does not.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        }
        row.AddChild(detail);
        body.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        body.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Wear, use or take off"), (Act.Alt, "Leave behind"), (Act.TabNext, "Next page"), (Act.Cancel, "Close"))
            : MouseFooter("Click to choose", "Double-click or right-click to wear or use", "Hover to compare with what you wear"));
    }

    void Select(string uid) { sel = sel == uid ? null : uid; Refresh(); }

    void Drop(ItemInstance it)
    {
        if (Items.Get(it.Def).Kind == ItemKind.Quest) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;
        G.Journey.Drop(it.Uid);
    }

    void Primary(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        if (def.Kind == ItemKind.Consumable) G.Gear((j, b) => j.Use(it.Uid, b));
        else if (Items.SlotFor(def) != null) G.Gear((j, b) => j.Equip(it.Uid, null, b));
    }

    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(8);
        foreach (var s in slots)
        {
            var it = ch.Equipment[s];
            var (name, glyph) = Slots[s];
            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon ? () => G.Gear((j, b) => j.Unequip(slot, b)) : null;
            v.AddChild(ItemViews.Slot(it, 76, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, ch, false) : null, over), glyph, name, $"eq:{slot}"));
        }
        return v;
    }

    Control Figure(CharacterData ch)
    {
        var v = Style.V(4);
        v.AddChild(new Portrait(new Vector2I(220, 330)).Of(Loadouts.Of(ch)));
        v.AddChild(Style.Label(ch.Name, Style.Display, 20, Style.GoldHi, false, HorizontalAlignment.Center));
        v.AddChild(Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.Ui, 14, Style.InkDim, false, HorizontalAlignment.Center));
        return v;
    }

    public static Control Stats(CharacterData ch)
    {
        var k = Character.Kit(ch).Stats;
        (string, string)[] rows =
        {
            ("Health", $"{Math.Round(k.Get(Stat.MaxHealth))}"),
            ("Armour", $"{Math.Round(k.Get(Stat.Armor))} ({Math.Round(StatBlock.ArmorReduction(k.Get(Stat.Armor)) * 100)}%)"),
            ("Damage", $"{(Math.Round((k.Get(Stat.Damage) - 1) * 100) >= 0 ? "+" : "")}{Math.Round((k.Get(Stat.Damage) - 1) * 100)}%"),
            ("Speed", $"{k.Get(Stat.MoveSpeed):0.0}"),
            ("Critical", $"{Math.Round(k.Get(Stat.CritChance) * 100)}%"),
            ("Regeneration", $"{k.Get(Stat.Regen):0.0}/s"),
        };
        var g = new GridContainer { Columns = 4, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 14);
        foreach (var (a, b) in rows)
        {
            g.AddChild(Style.Label(a, Style.Ui, 14, Style.InkDim));
            g.AddChild(Style.Label(b, Style.UiBold, 15, Style.Ink));
        }
        return g;
    }
}

/// <summary>Buying and selling (the web game's Shop): the seller's shelf on
/// the left, your pack on the right, the price on every tag; what they
/// will not buy is dimmed.</summary>
public partial class ShopScreen : Overlay
{
    public override string Kind => "shop";
    readonly string shop;
    (string Uid, bool Buy)? sel;

    public ShopScreen(Game g, string shop) : base(g) { this.shop = shop; Nav.Prefer = "shelf:0"; }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var def = Lore.Shops[shop];
        var who = Lore.Person(shop);
        var body = Frame(def.Name, new Vector2(1380, 640), "Esc", who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, fit: true);
        var row = Style.H(22);
        body.AddChild(row);
        var stock = w.Shops.GetValueOrDefault(shop)?.Stock ?? new();
        var shelf = stock.Cast<ItemInstance?>().ToList();
        while (shelf.Count < 20) shelf.Add(null);
        var left = Style.V(8, Style.SubLabel("For sale"),
            ItemViews.Grid(shelf, 5, 64, it => sel is { Buy: true } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, true),
                it => { sel = (it.Uid, true); Refresh(); }, it => G.Journey.Buy(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Compare(it, ch, true) : null, over), "shelf"));
        row.AddChild(left);

        var detail = Style.V(8);
        detail.CustomMinimumSize = new Vector2(360, 0);
        ItemInstance? chosen = sel is var (uid, buy) ? (buy ? stock.FirstOrDefault(x => x.Uid == uid) : ch.Pack.FirstOrDefault(x => x?.Uid == uid)) : null;
        if (chosen != null && sel is var (_, buying))
        {
            var price = G.Journey.PriceOf(shop, chosen.Uid, buying);
            Control act;
            if (buying)
            {
                var b = Style.Button($"Buy · {price} gold", () => G.Journey.Buy(shop, chosen.Uid), true, true);
                b.Disabled = price == null || ch.Gold < price;
                act = b;
            }
            else if (price != null) act = Style.Button($"Sell · {price} gold", () => { sel = null; G.Journey.Sell(shop, chosen.Uid); }, true, true);
            else act = Style.Label("They will not buy this.", Style.TextItalic, 14, Style.InkDim);
            detail.AddChild(ItemViews.Card(chosen, ch, true, act, 360));
        }
        else
        {
            detail.AddChild(Style.Gap(80));
            detail.AddChild(Glyphs.Icon("coin", 28, Style.GoldDim));
            detail.AddChild(Style.Label("Choose something on the shelf, or in your pack.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Prices soften for people who like you.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        }
        row.AddChild(detail);

        var right = Style.V(8, Style.SubLabel("Your pack"),
            ItemViews.Grid(ch.Pack, 6, 56, it => sel is { Buy: false } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, false),
                it => { sel = (it.Uid, false); Refresh(); }, it => G.Journey.Sell(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Card(it, ch, true) : null, over), "mine"),
            Style.H(16, Style.H(4, Glyphs.Icon("coin", 17, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, Style.Small, Style.GoldHi))));
        row.AddChild(right);
        body.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Buy or sell"), (Act.Cancel, "Close"))
            : MouseFooter("Click to choose", "Double-click or right-click to buy or sell"));
    }
}

/// <summary>Rook's storeroom: kept safe, whatever becomes of you. A click
/// moves a thing between the pack and the store.</summary>
public partial class StashScreen : Overlay
{
    public override string Kind => "stash";

    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var body = Frame("Rook's Storeroom", new Vector2(1120, 560), "Esc", "Kept safe, whatever becomes of you.", fit: true);
        var row = Style.H(28);
        body.AddChild(row);
        row.AddChild(Style.V(8, Style.SubLabel($"Stored  ·  {w.Stash.Count(x => x != null)} of {w.Stash.Count}"),
            ItemViews.Grid(w.Stash, 8, 56, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "store")));
        row.AddChild(Style.V(8, Style.SubLabel("Your pack"),
            ItemViews.Grid(ch.Pack, 6, 56, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "mine")));
        body.AddChild(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store"), (Act.Cancel, "Close")) : MouseFooter("Click to move between pack and store"));
    }
}
