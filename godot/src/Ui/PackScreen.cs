using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Your side, in the Pack and at every counter (docs/ui_review/greybox): what you carry in the
/// pack's places, a grid showing the rows in use and one more, the count saying the rest; the
/// slotless stores (docs/design/LOOT_DESIGN.md 6) as tabs over one compact row, things that never
/// take a place and always stack (the owner: "we also don't want to feel cheated with things that
/// should stack, or should not even take up inventory spots"); and the purse. A screen sets what
/// clicks, hovers and prices mean, and the block builds the same grid language everywhere.
/// </summary>
public sealed class PackBlock
{
    public enum Shelf { Pouch, Satchel, Keys, Belt }
    static readonly (Shelf Shelf, string Name, string Empty)[] Shelves =
    {
        (Shelf.Pouch, "Pouch", "The pouch is empty: what the night's fights leave goes here, for the Waystation's hands."),
        (Shelf.Satchel, "Satchel", "The satchel is empty: books and charts go here."),
        (Shelf.Keys, "Key ring", "Nothing on the key ring: tools and what the story gives you hang here."),
        (Shelf.Belt, "Belt", "The belt is empty: draughts ride here, ready to drink."),
    };

    /// <summary>The store last looked at, the same at every counter.</summary>
    public static Shelf Open = Shelf.Pouch;

    public CharacterData Ch = null!;
    public int Cols = 6, Tile = 70, StoreTile = 52, StoreCols = 8;
    public float Width = 460;
    public string Nav = "pack";
    public string Title = "Carried";
    public Func<ItemInstance, bool>? Selected, Dear, Fresh;
    public Func<ItemInstance, int?>? Price;
    public Action<ItemInstance>? Click, Primary;
    public Action<ItemInstance?, Control?>? Hover;
    public Action<int, ItemInstance?, SlotView>? Setup;
    /// <summary>What sits at the end of the grid's head (Filter and Sort).</summary>
    public Control[] HeadEnd = Array.Empty<Control>();
    /// <summary>The purse's size: large at a counter, where it is spent.</summary>
    public bool BigPurse;
    public Action Refresh = () => { };

    public static List<ItemInstance> Things(CharacterData ch, Shelf s) => s switch
    {
        Shelf.Pouch => Inventory.Pouch(ch),
        Shelf.Satchel => ch.Satchel.ToList(),
        Shelf.Keys => ch.Keys.ToList(),
        _ => Inventory.Belt(ch),
    };

    public VBoxContainer Build()
    {
        var ch = Ch;
        var v = Style.V(Style.Gap3);
        v.CustomMinimumSize = new Vector2(Width, 0);
        int held = ch.Pack.Count(p => p != null);
        v.AddChild(Kit.Head(Title, $"{held} of {ch.Pack.Count}", HeadEnd));
        int rows = ItemViews.RowsShown(ch.Pack, Cols);
        var grid = ItemViews.Grid(ch.Pack.Take(rows * Cols), Cols, Tile, Selected, Price, Click, Primary, Hover, Nav, null, Setup, Dear, ch, 8, Fresh);
        // (the tiles stand on the page itself: a well round them would be a box round boxes)
        v.AddChild(grid);

        // The stores: tabs over one row, the purse at the row's end.
        var tabs = Kit.Tabs(Shelves.Select(s => s.Name).ToArray(), (int)Open, k => { Open = (Shelf)k; Refresh(); }, 15, 18,
            Shelves.Select(s => Things(ch, s.Shelf) is { Count: > 0 } l ? $"{l.Count}" : "").ToArray());
        var purse = Style.H(5, Glyphs.Icon("coin", BigPurse ? 22 : 16, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", BigPurse ? Style.Display : Style.UiBold, BigPurse ? 24 : 17, Style.GoldHi, false, HorizontalAlignment.Left, false));
        foreach (var c in purse.GetChildren().OfType<Control>()) c.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        purse.TooltipText = "The purse";
        var tabRow = Style.H(8, tabs, new Control { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill, MouseFilter = Control.MouseFilterEnum.Ignore }, purse);
        v.AddChild(Style.Gap(2));
        v.AddChild(tabRow);
        var things = Things(ch, Open);
        if (things.Count == 0)
            v.AddChild(Style.Label(Shelves[(int)Open].Empty, Style.TextItalic, 15, Kit.Dim, true));
        else
            v.AddChild(ItemViews.Grid(things, StoreCols, StoreTile, Selected, Price, Click, Primary, Hover, $"{Nav}:{Open}".ToLowerInvariant(), null, null, Dear, ch, 6));
        return v;
    }
}

/// <summary>
/// The Pack (docs/ui_review/greybox/greybox_pack.png, approved, at the book panel's width): what
/// the survivor wears round their figure, slots where each thing is worn; beside it what they
/// carry, the stores and the purse, then the six numbers that matter. No inspect panel: a thing's
/// card opens beside it on the world's side, the worn piece beside that, what wearing it would
/// change at each line's end. Mouse: hover to read and compare, right-click or double-click to
/// wear or use, drag to wear, take off or move, click to hold its card open with what can be
/// done to it, hold Del over it to break it down. Pad: A wears or uses, X held breaks down, Y sorts,
/// LT and RT turn the stores.
/// </summary>
public partial class InventoryScreen : Overlay
{
    public override string Kind => "inventory";
    public override Act? Toggle => Act.Inventory;
    public override float CameraShift => -330;
    public override float CameraNear => 0.56f;
    string? sel;
    bool filterOpen;

    /// <summary>Where each thing is worn on the doll: the left column, then the right, staggered.</summary>
    static readonly (EquipSlot Slot, bool Right, float Y)[] Doll =
    {
        // (the first places sit level with the carried grid's first row, so the two halves share a line)
        (EquipSlot.Head, false, 36), (EquipSlot.Cloak, false, 122), (EquipSlot.Body, false, 208), (EquipSlot.Relic, false, 294),
        (EquipSlot.Amulet, true, 58), (EquipSlot.Weapon, true, 144), (EquipSlot.Offhand, true, 230), (EquipSlot.Ring1, true, 316), (EquipSlot.Ring2, true, 402),
    };
    public static readonly Dictionary<EquipSlot, (string Name, string Glyph)> Slots = new()
    {
        [EquipSlot.Weapon] = ("Weapon", "sword"), [EquipSlot.Offhand] = ("Off-hand", "shield"), [EquipSlot.Head] = ("Head", "helm"), [EquipSlot.Body] = ("Body", "armor"),
        [EquipSlot.Cloak] = ("Cloak", "cloak"), [EquipSlot.Amulet] = ("Amulet", "amulet"), [EquipSlot.Ring1] = ("Ring", "ring"), [EquipSlot.Ring2] = ("Ring", "ring"), [EquipSlot.Relic] = ("Relic", "relic"),
    };

    // What has been looked at this session: anything else carried is marked new.
    static readonly HashSet<string> seen = new();
    static bool seeded;

    public InventoryScreen(Game g) : base(g) { Nav.Prefer = "pack:0"; }

    CharacterData Ch => G.Journey.Ch;
    readonly Dictionary<string, (Label Now, Label Change)> numbers = new();

    protected override void Build()
    {
        var ch = Ch;
        if (!seeded) { seeded = true; foreach (var it in Carried(ch)) seen.Add(it.Uid); }
        // The tiles are new: what was hovered is gone with the old ones until the pointer moves.
        hoverIt = null;
        hoverAt = null;
        var v = BookPanel(null);
        var body = Style.H(24, DollView(ch));
        var right = Style.V(Style.Gap3);
        var block = new PackBlock
        {
            Ch = ch, Width = 460, Nav = "pack", Selected = it => it.Uid == sel, Click = it => Select(it.Uid), Primary = Primary, Hover = Hover,
            Setup = SetupCell, Fresh = it => !seen.Contains(it.Uid), Refresh = Refresh,
            HeadEnd = new Control[] { Nav.Skip(Kit.Word("Filter", () => { filterOpen = !filterOpen; Sound.Sfx.Page(); Refresh(); }, filterOpen ? Style.Focus : null)), Nav.Skip(Kit.Word("Sort", Sort)) },
        };
        right.AddChild(block.Build());
        right.AddChild(Style.Gap(4));
        right.AddChild(Kit.Head("Standing"));
        right.AddChild(Numbers());
        right.AddChild(Style.Label($"Self ({G.Key(Act.Character)}): every number, and where it comes from.", Style.TextItalic, 14, Kit.Faint));
        body.AddChild(right);
        v.AddChild(body);
        v.AddChild(Prompts());
        ShowNumbers(null);
        if (filterOpen) AddChild(new FilterPanel(G, () => { filterOpen = false; Refresh(); }) { Position = new Vector2(BookX - 14 - FilterPanel.W, 16) });
        // A thing held open: its card stays beside it until it is let go.
        Callable.From(ShowHeld).CallDeferred();
    }

    static IEnumerable<ItemInstance> Carried(CharacterData ch) =>
        ch.Pack.Where(p => p != null).Select(p => p!).Concat(Enum.GetValues<EquipSlot>().Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!));

    /* --------------------------------------------------------- the doll -- */

    // (as tall as the column of what she carries beside it, so neither leaves an empty strip above the prompts)
    const int DollW = 352, DollH = 468, SlotS = 64;

    Control DollView(CharacterData ch)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(DollW, DollH), MouseFilter = MouseFilterEnum.Ignore };
        // No box under her: a pool of shade where she stands, fading into the panel on every side.
        var pool = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f), Width = 128, Height = 128,
                Gradient = new Gradient { Colors = new[] { new Color(0, 0, 0, 0.32f), new Color(0, 0, 0, 0.18f), new Color(0, 0, 0, 0) }, Offsets = new[] { 0f, 0.55f, 1f } },
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Position = new Vector2(-20, -10), Size = new Vector2(DollW + 40, DollH + 20),
        };
        holder.AddChild(pool);
        var fig = Figure(ch, DollW - 2 * SlotS - 8, DollH - 16);
        fig.Position = new Vector2(SlotS + 4, 8);
        holder.AddChild(fig);
        foreach (var (s, right, y) in Doll)
        {
            var it = ch.Equipment[s];
            var (name, glyph) = Slots[s];
            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon ? () => G.Gear((j, b) => j.Unequip(slot, b)) : null;
            var view = ItemViews.Slot(it, SlotS, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Hover(it, over), glyph, name, $"eq:{slot}", null, false, false, false, ch, engraved: true);
            view.Position = new Vector2(right ? DollW - SlotS - 6 : 6, y);
            // Dragged from the pack, a thing that fits is worn here; dragged away from here, it is taken off.
            view.Drag = it != null && slot != EquipSlot.Weapon ? $"eq:{slot}:{it.Uid}" : null;
            view.CanTake = d => d.StartsWith("pack:") && Inventory.Find(Ch, d[5..]) is { } w && Items.Fits(Items.Get(w.Item.Def), slot);
            view.Take = d => { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(d[5..], slot, b)); };
            holder.AddChild(view);
        }
        return holder;
    }

    /// <summary>The survivor drawn live, on a pool of ember light.</summary>
    public static Control Figure(CharacterData ch, int w = 420, int h = 620)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(w, h), Size = new Vector2(w, h), MouseFilter = MouseFilterEnum.Ignore };
        var glow = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.5f, 0.2f, 0.13f), new Color(1, 0.5f, 0.2f, 0) }, Offsets = new[] { 0f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.62f), FillTo = new Vector2(1f, 0.62f), Width = 128, Height = 128,
            },
            Size = new Vector2(w, h), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        holder.AddChild(glow);
        holder.AddChild(DollPortrait(Loadouts.Of(ch), w, h));
        return holder;
    }

    static Portrait? doll;
    static string dollKey = "";

    /// <summary>The figure, kept across a screen's rebuilds while it looks the same: taken out of
    /// the page being thrown away and set in the new one, its idle never restarted (built anew each
    /// time, it stood in its bind pose for a frame on every refresh).</summary>
    static Portrait DollPortrait(Play.Loadout lo, int w, int h)
    {
        var key = $"{w}x{h} {Loadouts.Look(lo)}";
        if (doll != null && IsInstanceValid(doll) && !doll.IsQueuedForDeletion() && key == dollKey && doll.GetParent() is { } was)
        {
            // (its old page is queued to be freed with all it holds; out of it, the doll is not)
            was.RemoveChild(doll);
            return doll;
        }
        dollKey = key;
        return doll = new Portrait(new Vector2I(w, h)).Of(lo);
    }

    /* -------------------------------------------------------- the numbers -- */

    static readonly (string Key, string Name)[] Shown =
    {
        (Stat.MaxHealth, "Health"), (Stat.Armor, "Armour"), (Stat.Damage, "Damage"), (Stat.CritChance, "Critical"), (Stat.MoveSpeed, "Speed"), (Stat.Regen, "Regeneration"),
    };

    static string Format(string key, double v) => key switch
    {
        Stat.MaxHealth => $"{Math.Round(v)}",
        Stat.Armor => $"{Math.Round(v)} · {Math.Round(StatBlock.ArmorReduction(v) * 100)}%",
        Stat.Damage => $"{(v >= 1 ? "+" : "")}{Math.Round((v - 1) * 100)}%",
        Stat.MoveSpeed => $"{v:0.0}",
        Stat.CritChance => $"{Math.Round(v * 100)}%",
        _ => $"{v:0.0}/s",
    };

    Control Numbers()
    {
        numbers.Clear();
        var g = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 24);
        g.AddThemeConstantOverride("v_separation", 0);
        foreach (var (key, name) in Shown)
        {
            var label = Style.Label(name, Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            label.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var now = Kit.Num("", 16);
            var change = Kit.Num("", 14, Style.Good);
            change.CustomMinimumSize = new Vector2(44, 0);
            numbers[key] = (now, change);
            var holder = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(218, 28) };
            holder.AddThemeStyleboxOverride("panel", new LineUnder());
            holder.AddChild(Style.H(6, label, now, change));
            g.AddChild(holder);
        }
        return g;
    }

    /// <summary>The numbers; with a thing that could be worn, what wearing it would change.</summary>
    void ShowNumbers(ItemInstance? preview)
    {
        var ch = Ch;
        var k = Character.Kit(ch).Stats;
        var diffs = new Dictionary<string, (double B, double A)>();
        if (preview != null && Items.SlotFor(Items.Get(preview.Def)) is EquipSlot slot && Inventory.Find(ch, preview.Uid) is not { Worn: true })
        {
            var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
            foreach (var (key, b, a) in Character.Compare(ch, preview, target)) diffs[key] = (b, a);
        }
        foreach (var (key, _) in Shown)
        {
            if (!numbers.TryGetValue(key, out var at) || !IsInstanceValid(at.Now)) continue;
            at.Now.Text = Format(key, k.Get(key));
            if (diffs.TryGetValue(key, out var d))
            {
                var (text, good) = ItemViews.DeltaNumber(key, d.B, d.A);
                at.Change.Text = text;
                at.Change.AddThemeColorOverride("font_color", good ? Style.Good : Style.Bad);
            }
            else at.Change.Text = "";
        }
    }

    /* --------------------------------------------------- hovering, held -- */

    ItemInstance? hoverIt;
    Control? hoverAt;
    double hold;
    ColorRect? holdFill;

    void SetupCell(int i, ItemInstance? it, SlotView view)
    {
        var ch = Ch;
        if (it != null) view.Drag = $"pack:{it.Uid}";
        // Along the pack, a thing moves (or changes places); from the body, it is taken off into this place.
        view.CanTake = d => d.StartsWith("pack:") || d.StartsWith("eq:");
        view.Take = d =>
        {
            if (d.StartsWith("pack:") && Inventory.Find(ch, d[5..]) is { InPack: true } from)
            {
                (ch.Pack[i], ch.Pack[from.Index]) = (ch.Pack[from.Index], ch.Pack[i]);
                Sound.Sfx.Click();
                Refresh();
            }
            else if (d.StartsWith("eq:"))
            {
                var parts = d.Split(':');
                if (!Enum.TryParse<EquipSlot>(parts[1], out var slot)) return;
                G.Gear((j, b) => j.Unequip(slot, b));
                // Into the place it was dropped on, if that is free.
                if (ch.Pack[i] == null && Inventory.Find(ch, parts[2]) is { InPack: true } at && at.Index != i)
                {
                    (ch.Pack[i], ch.Pack[at.Index]) = (ch.Pack[at.Index], null);
                    Refresh();
                }
            }
        };
    }

    /// <summary>Hovered (mouse) or focused (pad): its card beside it, and what it would change.</summary>
    void Hover(ItemInstance? it, Control? over)
    {
        hoverIt = it;
        hoverAt = over;
        hold = 0;
        if (it != null) seen.Add(it.Uid);
        ShowNumbers(it ?? Held);
        if (it == null) { ShowHeld(); return; }
        var (card, worn) = ItemViews.Compare(it, Ch, Items.SlotFor(Items.Get(it.Def)) != null, CardKeys(it));
        TipBeside(card, worn, over, true, BookX);
    }

    /// <summary>The keys for a thing, at its card's foot: what the hand in use can do to it.</summary>
    Control? CardKeys(ItemInstance it)
    {
        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return null;
        var def = Items.Get(it.Def);
        bool pad = Controls.Instance.UsingPad;
        var parts = new List<Control>();
        string? first = loc.Worn ? loc.Slot != EquipSlot.Weapon ? "take off" : null : def.Kind == ItemKind.Consumable ? "use" : Items.SlotFor(def) != null ? "wear" : null;
        if (first != null) parts.Add(pad ? Kit.Prompt(Act.Confirm, Style.Cap1(first)) : Kit.Prompt("Rclick", Style.Cap1(first)));
        if (CanBreak(it)) parts.Add(Kit.Prompt(Act.Alt, "Hold: break down"));
        if (!pad) parts.Add(Kit.Prompt("Click", "More"));
        if (parts.Count == 0) return null;
        var h = Style.H(14, parts.ToArray());
        return h;
    }

    bool CanBreak(ItemInstance it) => Inventory.Find(Ch, it.Uid) is { InPack: true } && !G.Journey.InArena && Crafting.BreakDown(G.Journey.Craft, it).Ok;

    public override void _Process(double delta)
    {
        base._Process(delta);
        // Del (or X on a pad) held over a thing breaks it down when the press fills: no second dialog.
        bool held = hoverIt != null && Controls.Instance.Held(Act.Alt) && CanBreak(hoverIt) && IsInstanceValid(hoverAt);
        if (held) hold += delta / HoldButton.Time;
        else hold = Math.Max(0, hold - delta / HoldButton.Drain);
        if (hold > 0 && IsInstanceValid(hoverAt))
        {
            if (holdFill == null || !IsInstanceValid(holdFill) || holdFill.GetParent() != hoverAt)
            {
                holdFill = new ColorRect { Color = Style.BloodHi with { A = 0.45f }, MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
                hoverAt!.AddChild(holdFill);
            }
            var s = hoverAt!.Size;
            float hgt = (float)Math.Min(1, hold) * (s.Y - 4);
            holdFill.Position = new Vector2(2, s.Y - 2 - hgt);
            holdFill.Size = new Vector2(s.X - 4, hgt);
        }
        else if (holdFill != null && IsInstanceValid(holdFill)) { holdFill.QueueFree(); holdFill = null; }
        if (hold >= 1 && hoverIt != null)
        {
            var it = hoverIt;
            hold = 0;
            hoverIt = null;
            BreakDown(it);
        }
    }

    /// <summary>The thing held open (clicked): in the pack, worn, or in a store.</summary>
    ItemInstance? Held => sel == null ? null : Inventory.Find(Ch, sel)?.Item;

    void Select(string uid) { sel = sel == uid ? null : uid; Sound.Sfx.Click(); Refresh(); }

    /// <summary>The held thing's card, beside it, with what can be done to it as presses.</summary>
    void ShowHeld()
    {
        if (hoverIt != null) return;
        if (Held is not { } it) { TipBeside(null, null, null, true, BookX); return; }
        var at = FindTile(it.Uid);
        if (at == null) { TipBeside(null, null, null, true, BookX); return; }
        var loc = Inventory.Find(Ch, it.Uid)!;
        var def = Items.Get(it.Def);
        var acts = Style.H(8);
        if (loc.Worn && loc.Slot != EquipSlot.Weapon) acts.AddChild(Style.Button("Take off", () => Primary(it), false, true));
        if (!loc.Worn && def.Kind == ItemKind.Consumable) acts.AddChild(Style.Button("Use", () => Primary(it), true, true));
        if (loc.InPack && Items.SlotFor(def) != null) acts.AddChild(Style.Button("Wear", () => Primary(it), true, true));
        if (CanBreak(it) && Crafting.BreakDown(G.Journey.Craft, it) is { Ok: true } bq)
            acts.AddChild(Style.HoldButton($"Break down for {Items.Several(Crafting.Iron, bq.Gives[Crafting.Iron])}", () => BreakDown(it)));
        // A jar of the Dig's slurry carried: the one gamble, by the survivor's own hand.
        bool steep = loc.InPack && !G.Journey.InArena && Crafting.CanSteep(Ch) && Crafting.Steep(G.Journey.Craft, it).Ok;
        if (steep) acts.AddChild(Style.HoldButton("Steep", () => Steep(it)));
        if (!loc.Worn && !G.Journey.StillNeeded(it)) acts.AddChild(Style.HoldButton("Leave behind", () => Leave(it)));
        var (card, worn) = ItemViews.Compare(it, Ch, Items.SlotFor(def) != null);
        var col = (VBoxContainer)card.GetChild(0);
        if (came is { } cm && cm.Uid == it.Uid)
        {
            var c = cm.Mood > 0 ? ItemViews.SlurryGreen : cm.Mood < 0 ? Style.Bad : new Color("#9aa890");
            col.AddChild(Style.V(2, Style.Label("STEEPED", Style.UiHeavy, 12, c), Style.Label(cm.Text, Style.UiBold, 15, cm.Mood < 0 ? Style.Bad : Kit.Ink, true)));
        }
        if (steep)
        {
            col.AddChild(Style.Label("Steeped, it comes to one of these, and is set for good after:", Style.UiBold, 14, Kit.Ink2, true));
            col.AddChild(ForgeScreen.SlurryOdds(it, 296));
        }
        acts.AddThemeConstantOverride("separation", 8);
        var wrap = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
        wrap.AddThemeConstantOverride("h_separation", 8);
        wrap.AddThemeConstantOverride("v_separation", 8);
        foreach (var b in acts.GetChildren().OfType<Control>().ToList()) { acts.RemoveChild(b); wrap.AddChild(b); }
        col.AddChild(wrap);
        TipBeside(card, worn, at, true, BookX);
    }

    Control? FindTile(string uid)
    {
        // (C# classes are Panels to the engine's own search by type, so the tree is walked here)
        static SlotView? Walk(Node n, string uid)
        {
            foreach (var c in n.GetChildren())
            {
                if (c is SlotView s && s.Item?.Uid == uid && s.IsVisibleInTree()) return s;
                if (Walk(c, uid) is { } found) return found;
            }
            return null;
        }
        return Walk(this, uid);
    }

    /* ------------------------------------------------------------- acts -- */

    void Primary(ItemInstance it)
    {
        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return;
        var def = Items.Get(it.Def);
        if (loc.Worn) { if (loc.Slot != EquipSlot.Weapon) G.Gear((j, b) => j.Unequip(loc.Slot, b)); else Sound.Sfx.Deny(); return; }
        if (def.Kind == ItemKind.Consumable) G.Gear((j, b) => j.Use(it.Uid, b));
        else if (Items.SlotFor(def) != null) { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(it.Uid, null, b)); }
        else Sound.Sfx.Deny();
    }

    /// <summary>Breaking down cannot be undone: held to full, never asked twice (never in an arena).</summary>
    void BreakDown(ItemInstance it)
    {
        var q = Crafting.BreakDown(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;
        Sound.Sfx.Shatter();
        G.Journey.Work(it.Uid, q, G.Battle);
        // The HUD's toasts are hidden under the book: what it came to is said at its foot.
        said = ($"Broken down: {Inventory.Name(it)}. {Style.Cap1(string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))))}, into the pouch.", Time.GetTicksMsec());
        Refresh();
    }

    /// <summary>What the slurry just did to a piece, said on its card while it stays held.</summary>
    (string Uid, string Text, int Mood)? came;

    /// <summary>Steeping, by the survivor's own hand (docs/CRAFTING_DESIGN.md 9): the odds on the held
    /// card while a jar is carried, the press held to full. Never in an arena.</summary>
    void Steep(ItemInstance it)
    {
        var q = Crafting.Steep(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        Sound.Sfx.Pour();
        if (!G.Journey.Work(it.Uid, q, G.Battle)) return;
        var (text, mood) = Crafting.Outcome(it, q);
        came = (it.Uid, text, mood);
        sel = it.Uid;
        Refresh();
    }

    void Leave(ItemInstance it)
    {
        if (G.Journey.StillNeeded(it)) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;
        G.Journey.Drop(it.Uid);
    }

    /// <summary>The pack in order: by where a thing is worn, finer first, then by name.</summary>
    void Sort()
    {
        var ch = Ch;
        static int Group(ItemDef d) => Items.SlotFor(d) is EquipSlot s ? (int)s : 50;
        var items = ch.Pack.Where(p => p != null).Select(p => p!).OrderBy(p => Group(Items.Get(p.Def))).ThenByDescending(p => Drops.TierOf(p)).ThenByDescending(p => Drops.LevelOf(p)).ThenBy(p => Inventory.Name(p)).ToList();
        for (int i = 0; i < ch.Pack.Count; i++) ch.Pack[i] = i < items.Count ? items[i] : null;
        Sound.Sfx.Page();
        Refresh();
    }

    /* ------------------------------------------------------------- foot -- */

    (string Text, ulong At)? said;

    Control Prompts()
    {
        // Something just done, said for a few seconds where the prompts are: the HUD is under the book.
        if (said is { } s && Time.GetTicksMsec() - s.At < 3500)
        {
            var l = Style.Label(s.Text, Style.TextItalic, 15, Kit.Ink2, true, HorizontalAlignment.Center);
            l.CustomMinimumSize = new Vector2(0, 30);
            l.CreateTween().TweenProperty(l, "modulate:a", 0.0f, 0.6).SetDelay(Math.Max(0, 3.0 - (Time.GetTicksMsec() - s.At) / 1000.0));
            return l;
        }
        bool pad = Controls.Instance.UsingPad;
        var p = pad
            ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Wear or use"), Kit.Prompt(Act.Alt, "Hold: break down"), Kit.Prompt(Act.Alt2, "Sort"), Kit.Prompt(Act.SubNext, "Stores"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Rclick", "Wear or use"), Kit.Prompt("Drag", "Move"), Kit.Prompt("Click", "Hold open"), Kit.Prompt(G.Key(Act.Alt), "Hold: break down"));
        p.CustomMinimumSize = new Vector2(0, 30);
        return p;
    }

    public override bool Key(Act a)
    {
        switch (a)
        {
            case Act.SubNext: PackBlock.Open = (PackBlock.Shelf)(((int)PackBlock.Open + 1) % 4); Sound.Sfx.Page(); Refresh(); return true;
            case Act.SubPrev: PackBlock.Open = (PackBlock.Shelf)(((int)PackBlock.Open + 3) % 4); Sound.Sfx.Page(); Refresh(); return true;
            case Act.Alt2: Sort(); return true;
            // The press is held, not tapped: a tap of X or Del does nothing on its own.
            case Act.Alt: return hoverIt != null;
            case Act.Cancel when filterOpen: filterOpen = false; Refresh(); return true;
            case Act.Cancel when sel != null: sel = null; Refresh(); return true;
        }
        return false;
    }
}
