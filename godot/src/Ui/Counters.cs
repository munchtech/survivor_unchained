using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// What every counter shares (docs/ui_review/greybox, approved): two fitted panels, theirs at the
/// left and yours at the right, each as tall as what it holds, with the keeper live in the world
/// between them (the owner: full pages are "often not the best choice"). A thing's card opens
/// beside it toward the middle, the worn piece with it; the prompts sit along the foot.
/// </summary>
public abstract partial class CounterScreen : Overlay
{
    protected CounterScreen(Game g) : base(g) { }

    /// <summary>Your panel's width: the pack's grid (six of 72) and its margins.</summary>
    protected const float YoursW = 548, Top = 150;
    protected static float YoursX => 1920 - 40 - YoursW;

    protected CharacterData Ch => G.Journey.Ch;

    /// <summary>Your side: the title, Close, then what you carry (PackBlock).</summary>
    protected VBoxContainer Yours(PackBlock block)
    {
        HideHud();
        var v = Fitted(new Vector2(YoursX, Top), YoursW);
        var head = Style.H(8, new Title("Your pack", 28, false));
        var close = Nav.Skip(CloseButton("Esc", G.CloseOverlay));
        close.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        head.AddChild(close);
        v.AddChild(head);
        block.Ch = Ch;
        block.Width = 484;
        block.Tile = 72;
        block.BigPurse = true;
        block.Refresh = Refresh;
        v.AddChild(block.Build());
        return v;
    }

    /// <summary>The foot's prompts, across the middle of the screen under the panels.</summary>
    protected void Foot(Control row)
    {
        // On a ground of their own: under the panels they lie on the world, which can be bright.
        var ground = new StyleBoxFlat { BgColor = new Color(0.05f, 0.04f, 0.05f, 0.72f), CornerDetail = 6, ContentMarginLeft = 18, ContentMarginRight = 18, ContentMarginTop = 6, ContentMarginBottom = 6 };
        ground.SetCornerRadiusAll(6);
        var plate = Style.Panel(ground, row);
        plate.MouseFilter = MouseFilterEnum.Ignore;
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(0, 994), Size = new Vector2(1920, 44) };
        centre.AddChild(plate);
        AddChild(centre);
    }

    /// <summary>A thing hovered on their side: its card opens to the right of their panel.</summary>
    protected void TheirTip(ItemInstance? it, Control? over, float theirEdge, Control? prompts = null, int? price = null, bool dear = false)
    {
        if (it == null || over == null) { TipBeside(null, null, null, false, 0); return; }
        var (card, worn) = ItemViews.Compare(it, Ch, Items.SlotFor(Items.Get(it.Def)) != null, prompts, price, dear);
        TipBeside(card, worn, over, false, theirEdge);
    }

    /// <summary>A thing hovered on your side: its card opens to the left of your panel.</summary>
    protected void YourTip(ItemInstance? it, Control? over, Control? prompts = null, int? price = null)
    {
        if (it == null || over == null) { TipBeside(null, null, null, true, YoursX); return; }
        var (card, worn) = ItemViews.Compare(it, Ch, Items.SlotFor(Items.Get(it.Def)) != null, prompts, price);
        TipBeside(card, worn, over, true, YoursX);
    }

    protected static Control Keys(params (string Cap, string Text)[] k) => Style.H(14, k.Select(x => Kit.Prompt(x.Cap, x.Text)).ToArray());
}

/// <summary>
/// Rook's storeroom: kept safe, whatever becomes of you. Her shelf at the left, shelves of 24 bought
/// from her as tabs (the owner approved "Rook's storeroom grows by bought shelves"), your pack at the
/// right. A click, a right click or a drag moves a thing across.
/// </summary>
public partial class StashScreen : CounterScreen
{
    public override string Kind => "stash";
    const float TheirsW = 548;
    static int shelf;

    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }

    protected override void Build()
    {
        var ch = Ch;
        var w = G.Journey.World;
        shelf = Math.Clamp(shelf, 0, w.Shelves - 1);
        var v = Fitted(new Vector2(40, Top), TheirsW);
        v.AddChild(new Title("Rook's storeroom", 28));
        // The shelves as tabs, and another to be had from her: the price in its words.
        var names = Enumerable.Range(0, w.Shelves).Select(i => $"Shelf {ArtsScreen.Numerals[Math.Min(i, ArtsScreen.Numerals.Length - 1)]}").ToArray();
        var row = Style.H(12, Kit.Tabs(names, shelf, k => { shelf = k; Refresh(); }, 15, 20));
        row.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        if (Crafting.ShelfPrice(G.Journey.Craft) is int price)
        {
            bool can = ch.Gold >= price;
            var buy = Style.HoldButton($"Another shelf · {price} gold", () =>
            {
                if (!Crafting.BuyShelf(G.Journey.Craft)) { Sound.Sfx.Deny(); return; }
                Sound.Sfx.Loot(false);
                shelf = w.Shelves - 1;
                Refresh();
            }, false);
            buy.Disabled = !can;
            buy.TooltipText = can ? $"{WorldState.Shelf} more places, kept by Rook" : $"{price} gold: you have {Math.Floor(ch.Gold)}";
            row.AddChild(buy);
        }
        else row.AddChild(Style.Label("kept safe, whatever becomes of you", Style.TextItalic, 15, Kit.Faint));
        v.AddChild(row);
        var places = w.Stash.Skip(shelf * WorldState.Shelf).Take(WorldState.Shelf).ToList();
        int on = places.Count(x => x != null);
        v.AddChild(Kit.Head("On the shelf", $"{on} of {places.Count}", Nav.Skip(Kit.Word("Sort", SortShelf))));
        int rows = ItemViews.RowsShown(places, 6);
        int first = shelf * WorldState.Shelf;
        var grid = ItemViews.Grid(places.Take(rows * 6), 6, 72, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid),
            (it, over) => TheirTip(it, over, 40 + TheirsW, Keys(("Click", "Take it")), null), "store", null,
            (i, it, sv) => { if (it != null) sv.Drag = $"store:{it.Uid}"; sv.CanTake = d => d.StartsWith("mine:"); sv.Take = d => ToShelf(d[5..], first + i); }, null, ch);
        var well = Style.Panel(Kit.WellBox(6), grid);
        well.MouseFilter = MouseFilterEnum.Ignore;
        v.AddChild(well);

        Yours(new PackBlock
        {
            Nav = "mine", Click = it => Store(it), Primary = it => Store(it), Hover = (it, over) => YourTip(it, over, Keys(("Click", "Store it"))),
            Setup = (i, it, sv) => { if (it != null) sv.Drag = $"mine:{it.Uid}"; sv.CanTake = d => d.StartsWith("store:"); sv.Take = d => G.Journey.FromStash(d[6..]); },
            HeadEnd = new Control[] { Nav.Skip(Kit.Word("Sort", SortPack)) },
        });
        bool pad = Controls.Instance.UsingPad;
        Foot(pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Move across"), Kit.Prompt(Act.SubNext, "Shelf"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Move across"), Kit.Prompt("Drag", "Move"), Kit.Prompt(G.Key(Act.SubPrev) + " " + G.Key(Act.SubNext), "Shelf"), Kit.Prompt("Esc", "Close")));
    }

    void Store(ItemInstance it)
    {
        // Only what takes a place goes on a shelf: the stores never fill, so there is nothing to keep for them.
        if (Inventory.Find(Ch, it.Uid) is not { InPack: true }) { Sound.Sfx.Deny(); return; }
        G.Journey.ToStash(it.Uid);
    }

    /// <summary>Onto a chosen place on the shelf being looked at, if it is free.</summary>
    void ToShelf(string uid, int place)
    {
        var w = G.Journey.World;
        G.Journey.ToStash(uid);
        int at = w.Stash.FindIndex(x => x?.Uid == uid);
        if (at >= 0 && at != place && place < w.Stash.Count && w.Stash[place] == null) { (w.Stash[place], w.Stash[at]) = (w.Stash[at], null); Refresh(); }
    }

    void SortShelf()
    {
        var w = G.Journey.World;
        int first = shelf * WorldState.Shelf;
        var things = w.Stash.Skip(first).Take(WorldState.Shelf).Where(x => x != null).Select(x => x!)
            .OrderBy(p => Items.SlotFor(Items.Get(p.Def)) is EquipSlot s ? (int)s : 50).ThenByDescending(p => Drops.TierOf(p)).ThenBy(Inventory.Name).ToList();
        for (int i = 0; i < WorldState.Shelf && first + i < w.Stash.Count; i++) w.Stash[first + i] = i < things.Count ? things[i] : null;
        Sound.Sfx.Page();
        Refresh();
    }

    void SortPack()
    {
        var ch = Ch;
        var items = ch.Pack.Where(p => p != null).Select(p => p!).OrderBy(p => Items.SlotFor(Items.Get(p.Def)) is EquipSlot s ? (int)s : 50).ThenByDescending(p => Drops.TierOf(p)).ThenBy(Inventory.Name).ToList();
        for (int i = 0; i < ch.Pack.Count; i++) ch.Pack[i] = i < items.Count ? items[i] : null;
        Sound.Sfx.Page();
        Refresh();
    }

    public override bool Key(Act a)
    {
        var w = G.Journey.World;
        if (a == Act.SubNext && w.Shelves > 1) { shelf = (shelf + 1) % w.Shelves; Sound.Sfx.Page(); Refresh(); return true; }
        if (a == Act.SubPrev && w.Shelves > 1) { shelf = (shelf + w.Shelves - 1) % w.Shelves; Sound.Sfx.Page(); Refresh(); return true; }
        return false;
    }
}

/// <summary>
/// Buying and selling: the merchant's head and wares at the left, prices on the tiles (red when
/// more than you have), your pack at the right, the merchant live in the world between. Hover to
/// read and compare; right-click, double-click or drag across to buy or sell. What they will not
/// buy is dimmed.
/// </summary>
public partial class ShopScreen : CounterScreen
{
    public override string Kind => "shop";
    readonly string shop;
    const float TheirsW = 684;

    public ShopScreen(Game g, string shop) : base(g) { this.shop = shop; Nav.Prefer = "shelf:0"; }

    protected override void Build()
    {
        var ch = Ch;
        var w = G.Journey.World;
        var def = Lore.Shops[shop];
        var who = Lore.Person(shop);
        var v = Fitted(new Vector2(40, Top), TheirsW);

        // Who you are dealing with, and how they deal with you, in one compact head.
        var head = Style.H(16);
        if (who?.Person != null)
        {
            var face = new Portrait(new Vector2I(96, 96), Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1);
            face.Material = Round;
            head.AddChild(face);
        }
        var names = Style.V(3);
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        names.AddChild(Style.Label((who?.Name ?? def.Name).ToUpperInvariant(), Style.Display, 26, Kit.Ink, false, HorizontalAlignment.Left, false));
        double mod = G.Journey.PriceMod(shop);
        int pct = (int)Math.Round((mod - 1) * 100);
        var st = w.Shops.GetValueOrDefault(shop);
        int days = st != null && def.RestockDays > 0 ? Math.Max(0, st.RestockDay - w.Day) : -1;
        string stand = string.Join("  ·  ", new[]
        {
            who != null ? Rules.Attitude(w.Npc(shop)) : def.Name,
            pct == 0 ? "their usual prices" : pct < 0 ? $"{-pct}% under their usual" : $"{pct}% over their usual",
            days > 0 ? $"new stock in {days} day{(days == 1 ? "" : "s")}" : days == 0 ? "new stock tomorrow" : null,
        }.Where(s => s != null));
        names.AddChild(Style.Label(stand, Style.Ui, 15, pct < 0 ? Style.Good : pct > 0 ? Style.Bad : Kit.Dim, true));
        // What is on their mind, in the story's own words: a merchant is a person first.
        if (who != null && Lore.ConcernOf(shop, G.Journey.Ctx) is string mind)
            names.AddChild(Style.Label($"“{mind}”", Style.TextItalic, 17, Kit.Ink2, true));
        head.AddChild(names);
        v.AddChild(head);

        var stock = st?.Stock ?? new();
        v.AddChild(Kit.Head("Wares", $"{stock.Count}"));
        var shelf = stock.Cast<ItemInstance?>().ToList();
        while (shelf.Count % 7 != 0 || shelf.Count == 0) shelf.Add(null);
        var grid = ItemViews.Grid(shelf, 7, 80, null, it => G.Journey.PriceOf(shop, it.Uid, true), null, Buy,
            (it, over) => TheirTip(it, over, 40 + TheirsW, Keys(("Rclick", "Buy")), it != null ? G.Journey.PriceOf(shop, it.Uid, true) : null, it != null && G.Journey.PriceOf(shop, it.Uid, true) > ch.Gold),
            "shelf", null, (i, it, sv) =>
            {
                if (it != null) sv.Drag = $"shelf:{it.Uid}";
                sv.CanTake = d => d.StartsWith("mine:");
                sv.Take = d => Sell(d[5..]);
            }, it => G.Journey.PriceOf(shop, it.Uid, true) is int p && p > ch.Gold, ch);
        var well = Style.Panel(Kit.WellBox(6), grid);
        well.MouseFilter = MouseFilterEnum.Ignore;
        v.AddChild(well);
        v.AddChild(Style.Label(def.BuysAll ? $"They will buy anything, at {def.Pays * 100:0}% of its worth." : $"They buy {Buys(def)}, at {def.Pays * 100:0}% of their worth; the rest is dimmed.",
            Style.TextItalic, 15, Kit.Dim, true));

        Yours(new PackBlock
        {
            Nav = "mine", Price = it => G.Journey.PriceOf(shop, it.Uid, false), Primary = Sell, Hover = (it, over) => YourTip(it, over, Keys(("Rclick", "Sell")), it != null ? G.Journey.PriceOf(shop, it.Uid, false) : null),
            Setup = (i, it, sv) => { if (it != null) sv.Drag = $"mine:{it.Uid}"; sv.CanTake = d => d.StartsWith("shelf:"); sv.Take = d => Buy(d[6..]); },
        });
        bool pad = Controls.Instance.UsingPad;
        Foot(pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Buy or sell"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Rclick", "Buy or sell"), Kit.Prompt("Drag", "Across"), Kit.Prompt("Esc", "Close")));
    }

    /// <summary>What they buy, in the plural words a person would say.</summary>
    static string Buys(ShopDef def)
    {
        static string Word(string kind) => kind switch
        {
            "material" => "materials", "consumable" => "draughts", "trophy" => "trophies", "ring" => "rings", "amulet" => "amulets", "cloak" => "cloaks",
            "weapon" => "weapons", "offhand" => "off-hands", "head" => "helms", "body" => "body armour", "relic" => "relics", "tool" => "tools",
            _ => kind.Replace('_', ' '),
        };
        var w = def.Buys.Select(Word).ToList();
        return w.Count <= 1 ? string.Join("", w) : $"{string.Join(", ", w.Take(w.Count - 1))} and {w[^1]}";
    }

    static ShaderMaterial? round;

    /// <summary>A face in a round, its edge soft.</summary>
    static ShaderMaterial Round => round ??= new ShaderMaterial
    {
        Shader = new Shader { Code = "shader_type canvas_item;\nvoid fragment() { float d = length(UV - vec2(0.5)); COLOR.a *= 1.0 - smoothstep(0.47, 0.5, d); }" },
    };

    void Buy(ItemInstance it) => Buy(it.Uid);
    void Buy(string uid)
    {
        var p = G.Journey.PriceOf(shop, uid, true);
        if (p == null || p > Ch.Gold) { Sound.Sfx.Deny(); return; }
        G.Journey.Buy(shop, uid);
    }

    void Sell(ItemInstance it) => Sell(it.Uid);
    void Sell(string uid)
    {
        if (G.Journey.PriceOf(shop, uid, false) == null) { Sound.Sfx.Deny(); return; }
        G.Journey.Sell(shop, uid);
    }
}
