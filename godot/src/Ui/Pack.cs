using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>Buying and selling (docs/UI_DESIGN.md, "Shop"): the seller's shelf
/// on the left with its prices (red when more than you have), your pack on
/// the right; hover to read and compare, right-click or double-click to buy
/// or sell, or drag across; the chosen thing read closely under your pack.
/// What they will not buy is dimmed.</summary>
public partial class ShopScreen : Overlay
{
    public override string Kind => "shop";
    readonly string shop;
    (string Uid, bool Buy)? sel;
    VBoxContainer inspect = null!;

    public ShopScreen(Game g, string shop) : base(g) { this.shop = shop; Nav.Prefer = "shelf:0"; }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var def = Lore.Shops[shop];
        var who = Lore.Person(shop);
        var page = Page(def.Name, who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, null, "Esc");

        // The merchant, as large as the wares: who you are dealing with, and how they deal with you.
        var them = Pane(page, new Rect2(0, 0, 440, 920));
        if (who?.Person != null)
        {
            var frame = Style.Panel(Style.Well(0));
            frame.CustomMinimumSize = new Vector2(400, 470);
            frame.AddChild(new Portrait(new Vector2I(400, 470), Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1));
            them.AddChild(frame);
        }
        if (who != null)
        {
            var plaque = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            plaque.AddChild(new Plaque(who.Name, 26, 40));
            them.AddChild(plaque);
            var st = w.Npc(shop);
            double mod = G.Journey.PriceMod(shop);
            int pct = (int)Math.Round((mod - 1) * 100);
            them.AddChild(Style.Label(Style.Cap1(Rules.Attitude(st)), Style.TextItalic, Style.Body, Style.InkDim, false, HorizontalAlignment.Center));
            them.AddChild(Style.Label(pct == 0 ? "Their usual prices" : pct < 0 ? $"Prices {-pct}% under their usual" : $"Prices {pct}% over their usual",
                Style.UiBold, Style.Small, pct < 0 ? Style.Good : pct > 0 ? Style.Bad : Style.Ink, false, HorizontalAlignment.Center));
        }
        them.AddChild(Style.Label(def.BuysAll ? "They will buy anything." : $"They buy {string.Join(", ", def.Buys.Select(b => b.Replace('_', ' ')))}, at {def.Pays * 100:0}% of its worth.",
            Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        if (def.RestockDays > 0)
            them.AddChild(Style.Label($"New stock every {def.RestockDays} day{(def.RestockDays == 1 ? "" : "s")}.", Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        // What is on their mind, in the story's own words: a merchant is a person first.
        if (who != null && Lore.ConcernOf(shop, G.Journey.Ctx) is string mind)
            them.AddChild(Style.Panel(Style.Slab(14), Style.Label($"“{mind}”", Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center)));

        // The counter: their wares in a well of large slots, the chosen thing read closely beneath.
        var counter = Pane(page, new Rect2(470, 0, 880, 920));
        var stock = w.Shops.GetValueOrDefault(shop)?.Stock ?? new();
        var shelf = stock.Cast<ItemInstance?>().ToList();
        while (shelf.Count < 21 || shelf.Count % 7 != 0) shelf.Add(null);
        counter.AddChild(new Section("Their wares", "a price in red is more than you have"));
        var well = Style.Panel(Style.Well(12));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        centre.AddChild(ItemViews.Grid(shelf, 7, 104, it => sel is { Buy: true } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, true),
            it => Choose(it.Uid, true), Buy, (it, over) => Hover(it, over, true), "shelf", null, (i, it, v) =>
            {
                if (it != null) v.Drag = $"shelf:{it.Uid}";
                v.CanTake = d => d.StartsWith("mine:");
                v.Take = d => Sell(d[5..]);
            }, dear: it => G.Journey.PriceOf(shop, it.Uid, true) is int p && p > ch.Gold));
        well.AddChild(centre);
        counter.AddChild(well);
        counter.AddChild(new Section("Read closely"));
        inspect = Style.V(Style.Gap2);
        inspect.SizeFlagsVertical = SizeFlags.ExpandFill;
        counter.AddChild(inspect);

        // What you carry, and what you have to spend.
        var mine = Pane(page, new Rect2(1380, 0, 460, 920));
        mine.AddChild(new Section("Your pack", $"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count}"));
        var mwell = Style.Panel(Style.Well(10));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(ItemViews.Grid(ch.Pack, 5, 72, it => sel is { Buy: false } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, false),
            it => Choose(it.Uid, false), it => Sell(it.Uid), (it, over) => Hover(it, over, false), "mine", null, (i, it, v) =>
            {
                if (it != null) v.Drag = $"mine:{it.Uid}";
                v.CanTake = d => d.StartsWith("shelf:");
                v.Take = d => Buy(d[6..]);
            }));
        mwell.AddChild(mc);
        mine.AddChild(mwell);
        // The materials pouch sells too (docs/CRAFTING_DESIGN.md 4.3): a whole stack at once.
        var pouch = Inventory.Pouch(ch);
        if (pouch.Count > 0)
        {
            mine.AddChild(new Section("Your pouch", "a stack sells whole"));
            var pwell = Style.Panel(Style.Well(10));
            var pc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            var cells = pouch.Cast<ItemInstance?>().ToList();
            while (cells.Count % 5 != 0) cells.Add(null);
            pc.AddChild(ItemViews.Grid(cells, 5, 72, it => sel is { Buy: false } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, false),
                it => Choose(it.Uid, false), it => Sell(it.Uid), (it, over) => Hover(it, over, false), "pouch"));
            pwell.AddChild(pc);
            mine.AddChild(pwell);
        }
        var purse = Style.H(Style.Gap2, Glyphs.Icon("coin", 34, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.Display, 40, Style.GoldHi), Style.Label("gold", Style.TextItalic, Style.Body, Style.InkDim));
        purse.Alignment = BoxContainer.AlignmentMode.Center;
        mine.AddChild(purse);
        mine.AddChild(Style.Label("What they will not buy is dimmed.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        ShowInspect();
        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Buy or sell"), (Act.Cancel, "Close"))
            : MouseFooter("Right-click or double-click to buy or sell", "or drag it across", "hover to compare"));
    }

    void Buy(ItemInstance it) => Buy(it.Uid);
    void Buy(string uid)
    {
        var p = G.Journey.PriceOf(shop, uid, true);
        if (p == null || p > G.Journey.Ch.Gold) { Sound.Sfx.Deny(); return; }
        G.Journey.Buy(shop, uid);
    }

    void Sell(string uid)
    {
        if (G.Journey.PriceOf(shop, uid, false) == null) { Sound.Sfx.Deny(); return; }
        if (sel?.Uid == uid) sel = null;
        G.Journey.Sell(shop, uid);
    }

    void Choose(string uid, bool buy) { sel = sel?.Uid == uid ? null : (uid, buy); Refresh(); }

    void Hover(ItemInstance? it, Control? over, bool buying)
    {
        var ch = G.Journey.Ch;
        if (Controls.Instance.UsingPad) { if (it != null) { sel = (it.Uid, buying); ShowInspect(); } Tip(null, null); return; }
        Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Compare(it, ch, true).Card : null, over);
    }

    void ShowInspect()
    {
        if (!IsInstanceValid(inspect)) return;
        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        var ch = G.Journey.Ch;
        var stock = G.Journey.World.Shops.GetValueOrDefault(shop)?.Stock ?? new();
        ItemInstance? chosen = sel is var (uid, buy) ? (buy ? stock.FirstOrDefault(x => x.Uid == uid) : ch.Pack.FirstOrDefault(x => x?.Uid == uid) ?? Inventory.Pouch(ch).FirstOrDefault(x => x.Uid == uid)) : null;
        if (chosen == null || sel is not var (_, buying))
        {
            inspect.AddChild(Style.Gap(Style.Gap4));
            var c = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            c.AddChild(Glyphs.Icon("coin", 30, Style.GoldDim));
            inspect.AddChild(c);
            inspect.AddChild(Style.Label("Choose something on their shelf to buy, or in your pack to sell.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            inspect.AddChild(Style.Label("What they will not buy is dimmed; a price in red is more than you have.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
            return;
        }
        var price = G.Journey.PriceOf(shop, chosen.Uid, buying);
        bool pad = Controls.Instance.UsingPad, short_ = buying && price is int pp && ch.Gold < pp;
        // Only what is shown is made: a pad reads a prompt, a mouse presses a button.
        Control act;
        if (price == null) act = Style.Label(buying ? "Not for sale." : "They will not buy this.", Style.TextItalic, Style.Caption, Style.InkDim);
        else if (short_) act = Style.Label($"{price} gold: you have {Math.Floor(ch.Gold)}.", Style.UiBold, Style.Caption, Style.Bad);
        else if (pad) act = Style.Hint(Act.Confirm, buying ? $"Buy for {price} gold" : $"Sell for {price} gold");
        else act = buying ? Style.Button($"Buy  ·  {price} gold", () => Buy(chosen.Uid), true, true) : Style.Button($"Sell  ·  {price} gold", () => Sell(chosen.Uid), true, true);
        // Bought gear reads beside what it would replace, as in the pack.
        var card = ItemViews.Card(chosen, ch, true, act, buying && ItemViews.Against(chosen, ch) != null ? 480 : 820);
        if (buying && ItemViews.Against(chosen, ch) is { } worn)
            inspect.AddChild(Style.H(Style.Gap3, card, Style.V(4, Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim), ItemViews.Card(worn, ch, false, null, 320, true))));
        else inspect.AddChild(card);
    }
}

/// <summary>Rook's storeroom: kept safe, whatever becomes of you. A click (or A,
/// a double click, a right click, or a drag) moves a thing between the pack
/// and the store.</summary>
public partial class StashScreen : Overlay
{
    public override string Kind => "stash";

    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }

    VBoxContainer inspect = null!;

    /// <summary>What is hovered or focused, read in the pack's pane rather than in a tip over the slots.</summary>
    void Read(ItemInstance? it)
    {
        if (!IsInstanceValid(inspect)) return;
        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        if (it == null)
        {
            inspect.AddChild(Style.Label(Controls.Instance.UsingPad ? "Move over a thing to read it." : "Hover a thing to read it; click or drag it to move it.", Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
            return;
        }
        inspect.AddChild(ItemViews.Card(it, G.Journey.Ch, false, null, 600));
    }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var page = Page("Rook's Storeroom", "Kept safe, whatever becomes of you", null, "Esc");
        // The store is the larger: it keeps what a life on the road cannot carry.
        var store = Pane(page, new Rect2(0, 0, 1140, 920));
        store.AddChild(new Section("Stored", $"{w.Stash.Count(x => x != null)} of {w.Stash.Count}  ·  {w.Shelves} shel{(w.Shelves == 1 ? "f" : "ves")}"));
        var well = Style.Panel(Style.Well(12));
        var sc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        sc.AddChild(ItemViews.Grid(w.Stash, 8, 118, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Read(it), "store", null,
            (i, it, v) => { if (it != null) v.Drag = $"store:{it.Uid}"; v.CanTake = d => d.StartsWith("mine:"); v.Take = d => G.Journey.ToStash(d[5..]); }));
        well.AddChild(sc);
        // More shelves than the page holds scroll (UI design's shelf pages will replace this).
        var shelves = Style.Scroll(well);
        shelves.CustomMinimumSize = new Vector2(0, Mathf.Min(760, w.Stash.Count / 8 * 124 + 24));
        store.AddChild(shelves);
        // Another shelf, bought from Rook (the owner's: shelves of 24).
        if (Crafting.ShelfPrice(G.Journey.Craft) is int price)
        {
            bool can = ch.Gold >= price;
            var buy = Style.Button($"Another shelf from Rook: {price} gold", () =>
            {
                if (!Crafting.BuyShelf(G.Journey.Craft)) { Sound.Sfx.Deny(); return; }
                Sound.Sfx.Loot(false);
                Refresh();
            }, false, true);
            buy.Disabled = !can;
            store.AddChild(Style.H(Style.Gap3, buy, Style.Label(can ? $"{WorldState.Shelf} more places" : $"{price} gold; you have {Math.Floor(ch.Gold)}", Style.TextItalic, Style.Small, can ? Style.InkDim : Style.Bad)));
        }
        var mine = Pane(page, new Rect2(1170, 0, 670, 920));
        mine.AddChild(new Section("Your pack", $"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count}"));
        var mwell = Style.Panel(Style.Well(12));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(ItemViews.Grid(ch.Pack, 6, 92, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Read(it), "mine", null,
            (i, it, v) => { if (it != null) v.Drag = $"mine:{it.Uid}"; v.CanTake = d => d.StartsWith("store:"); v.Take = d => G.Journey.FromStash(d[6..]); }));
        mwell.AddChild(mc);
        mine.AddChild(mwell);
        mine.AddChild(new Section("Read closely"));
        inspect = Style.V(Style.Gap2);
        mine.AddChild(inspect);
        Read(null);
        PageFooter(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store"), (Act.Cancel, "Close")) : MouseFooter("Click, or drag, to move between pack and store"));
    }
}
