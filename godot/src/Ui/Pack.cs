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
/// The pack (docs/UI_DESIGN.md, "Pack"): one screen for what the survivor
/// wears and what they carry, built for the two questions it is opened to
/// answer, "is this better?" and "what do I do with it?".
///
/// On the left the survivor as they stand, what they wear round them, and
/// their standing, which shows what would change (before and after, better
/// or worse) while a thing is hovered or focused. On the right what they
/// carry: filters, sort, the pack, and the chosen thing read closely with
/// what can be done with it. Mouse: hover to read and compare (the worn
/// thing's card beside), click to choose, double-click or right-click to
/// wear or use, drag to wear, take off or move. Pad: move over the slots,
/// the card follows; A wears, uses or takes off, X leaves behind (twice: it
/// cannot be undone), Y sorts, LT and RT filter.
/// </summary>
public partial class InventoryScreen : Overlay
{
    public override string Kind => "inventory";
    public override Act? Toggle => Act.Inventory;
    string? sel, leaving;
    int filter;
    VBoxContainer stats = null!, inspect = null!;
    Control foot = null!;

    static readonly EquipSlot[] Left = { EquipSlot.Head, EquipSlot.Amulet, EquipSlot.Body, EquipSlot.Cloak };
    static readonly EquipSlot[] Right = { EquipSlot.Weapon, EquipSlot.Offhand, EquipSlot.Ring1, EquipSlot.Ring2, EquipSlot.Relic };
    public static readonly Dictionary<EquipSlot, (string Name, string Glyph)> Slots = new()
    {
        [EquipSlot.Weapon] = ("Weapon", "sword"), [EquipSlot.Offhand] = ("Off-hand", "shield"), [EquipSlot.Head] = ("Head", "helm"), [EquipSlot.Body] = ("Body", "armor"),
        [EquipSlot.Cloak] = ("Cloak", "cloak"), [EquipSlot.Amulet] = ("Amulet", "amulet"), [EquipSlot.Ring1] = ("Ring", "ring"), [EquipSlot.Ring2] = ("Ring", "ring"), [EquipSlot.Relic] = ("Relic", "relic"),
    };

    /// <summary>The filters: what each shows.</summary>
    static readonly (string Name, Func<ItemDef, bool> Has)[] Filters =
    {
        ("All", _ => true),
        ("Gear", d => Items.SlotFor(d) != null),
        ("Draughts", d => d.Kind == ItemKind.Consumable),
        ("Materials", d => d.Kind is ItemKind.Material or ItemKind.Trophy or ItemKind.Tool),
        ("Quest", d => d.Kind == ItemKind.Quest),
    };

    // What has been looked at this session: anything else in the pack is marked new.
    static readonly HashSet<string> seen = new();
    static bool seeded;

    public InventoryScreen(Game g) : base(g) { Nav.Prefer = "pack:0"; }

    CharacterData Ch => G.Journey.Ch;

    /// <summary>The pack is a panel at the right; the survivor stands in view between it and the
    /// thing read closely at the left.</summary>
    public override float CameraShift => -188;
    const float PanelW = 880;

    protected override void Build()
    {
        var ch = Ch;
        if (!seeded) { seeded = true; foreach (var it in Carried(ch)) seen.Add(it.Uid); }
        // A panel at the right (docs/UI_DESIGN.md 6, "Page or panel"): the pack is what is tweaked
        // mid-play, so the world stays in view, as in Diablo IV, PoE and Last Epoch.
        var area = SidePanel("Pack", $"{ch.Name}  ·  Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", true, PanelW);
        var v = Style.V(Style.Gap2);
        v.Size = area.Size;
        area.AddChild(v);

        // What they wear, round them.
        var doll = Style.H(Style.Gap3, Column(Left, ch), Figure(ch, 300, 376), Column(Right, ch));
        doll.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(doll);
        var standWell = Style.Panel(Style.Well(10));
        stats = Style.V(2);
        standWell.AddChild(stats);
        v.AddChild(standWell);
        ShowStats(null);

        // What they carry.
        v.AddChild(FilterRow());
        var well = Style.Panel(Style.Well(10));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        // Materials live in the pouch, not the pack (docs/CRAFTING_DESIGN.md 4.3): their filter shows it.
        if (filter == PouchFilter) centre.AddChild(ItemViews.Grid(PouchView(ch), 8, 84, it => it.Uid == sel, null, it => Select(it.Uid), null, Hover, "pack", Leave, null));
        else centre.AddChild(ItemViews.Grid(ch.Pack, 8, 84, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, SetupCell));
        well.AddChild(centre);
        v.AddChild(well);
        v.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 18, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)} gold", Style.UiBold, Style.Body, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count} carried", Style.Ui, Style.Small, Style.InkDim),
            Style.Label(ch.Materials.Count == 0 ? "the pouch is empty" : $"{ch.Materials.Values.Sum()} in the pouch", Style.Ui, Style.Small, Style.InkDim)));

        // The thing chosen, read closely, at the left over the world: beside the survivor, not under the panel.
        inspect = Style.V(Style.Gap2);
        inspect.Position = new Vector2(40, 120);
        inspect.Size = new Vector2(480, 900);
        AddChild(inspect);
        ShowInspect(Selected);
        foot = new Control { CustomMinimumSize = new Vector2(PanelW - 40, 30), MouseFilter = MouseFilterEnum.Ignore };
        SideFooter(foot);
        Footer();
    }

    const int PouchFilter = 3;

    /// <summary>The pouch's materials, then the trophies and tools the pack holds, as one shelf.</summary>
    static List<ItemInstance?> PouchView(CharacterData ch)
    {
        var o = Inventory.Pouch(ch).Cast<ItemInstance?>().Concat(ch.Pack.Where(p => p != null && Items.Get(p.Def).Kind is ItemKind.Trophy or ItemKind.Tool)).ToList();
        while (o.Count < 24 || o.Count % 8 != 0) o.Add(null);
        return o;
    }

    static IEnumerable<ItemInstance> Carried(CharacterData ch) =>
        ch.Pack.Where(p => p != null).Select(p => p!).Concat(Enum.GetValues<EquipSlot>().Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!));

    /* --------------------------------------------------------- the doll -- */

    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(Style.Gap1);
        v.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var s in slots)
        {
            var it = ch.Equipment[s];
            var (name, glyph) = Slots[s];
            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon ? () => G.Gear((j, b) => j.Unequip(slot, b)) : null;
            var view = ItemViews.Slot(it, 72, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Hover(it, over), glyph, name, $"eq:{slot}");
            // Dragged from the pack, a thing that fits is worn here; dragged away from here, it is taken off.
            view.Drag = it != null && slot != EquipSlot.Weapon ? $"eq:{slot}:{it.Uid}" : null;
            view.CanTake = d => d.StartsWith("pack:") && Inventory.Find(Ch, d[5..]) is { } w && Items.Fits(Items.Get(w.Item.Def), slot);
            view.Take = d => { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(d[5..], slot, b)); };
            v.AddChild(view);
        }
        return v;
    }

    /// <summary>The survivor drawn live, large, on a pool of ember light.</summary>
    public static Control Figure(CharacterData ch, int w = 420, int h = 620)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(w, h), MouseFilter = MouseFilterEnum.Ignore };
        // The page's one hero plate rounds the figure (frames/hero_plate.png), behind it, so nothing moves when it lands.
        if (UiArt.Has("hero_plate"))
        {
            var plate = new Panel { MouseFilter = MouseFilterEnum.Ignore };
            plate.AddThemeStyleboxOverride("panel", UiArt.Frame("hero_plate", new StyleBoxEmpty()));
            Style.Fill(plate);
            holder.AddChild(plate);
        }
        var glow = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.5f, 0.2f, 0.16f), new Color(1, 0.5f, 0.2f, 0) }, Offsets = new[] { 0f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.6f), FillTo = new Vector2(1f, 0.6f), Width = 128, Height = 128,
            },
            Size = new Vector2(w, h), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        holder.AddChild(glow);
        holder.AddChild(Doll(Loadouts.Of(ch), w, h));
        return holder;
    }

    static Portrait? doll;
    static string dollKey = "";

    /// <summary>The figure, kept across a screen's rebuilds while it looks the same: taken out of
    /// the page being thrown away and set in the new one, its idle never restarted (built anew each
    /// time, it stood in its bind pose for a frame on every refresh).</summary>
    static Portrait Doll(Play.Loadout lo, int w, int h)
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

    /* ------------------------------------------------------- the standing -- */

    static readonly (string Key, string Name)[] Shown =
    {
        (Stat.MaxHealth, "Health"), (Stat.Armor, "Armour"), (Stat.Damage, "Damage"), (Stat.MoveSpeed, "Speed"), (Stat.CritChance, "Critical"), (Stat.Regen, "Regeneration"),
    };

    /// <summary>The survivor's standing; with a thing that could be worn, what it would change.</summary>
    void ShowStats(ItemInstance? preview)
    {
        if (!IsInstanceValid(stats)) return;
        foreach (var c in stats.GetChildren()) { stats.RemoveChild(c); c.QueueFree(); }
        var ch = Ch;
        var k = Character.Kit(ch).Stats;
        var diffs = new Dictionary<string, double>();
        string? against = null;
        if (preview != null && Items.SlotFor(Items.Get(preview.Def)) is EquipSlot slot && !Enum.GetValues<EquipSlot>().Any(s => ch.Equipment[s]?.Uid == preview.Uid))
        {
            var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
            foreach (var (key, _, after) in Character.Compare(ch, preview, target)) diffs[key] = after;
            against = ItemViews.Against(preview, ch) is { } worn ? Inventory.Name(worn) : "nothing";
        }
        var g = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 26);
        g.AddThemeConstantOverride("v_separation", 3);
        foreach (var (key, name) in Shown)
        {
            double now = k.Get(key);
            var label = Style.Label(name, Style.Ui, Style.Small, Style.InkDim);
            label.CustomMinimumSize = new Vector2(110, 0);
            var line = Style.H(8, label, Style.Label(Format(key, now), Style.UiBold, Style.Small, Style.Ink));
            if (diffs.TryGetValue(key, out var then))
            {
                bool better = then > now;
                line.AddChild(Style.Label($"to {Format(key, then)}", Style.UiBold, Style.Small, better ? Style.Good : Style.Bad));
                line.AddChild(Style.Label(better ? "better" : "worse", Style.UiHeavy, Style.Badge, better ? Style.Good : Style.Bad));
            }
            g.AddChild(line);
        }
        stats.AddChild(g);
        if (preview == null || against == null) return;
        // What it changes that the standing does not show, in the card's words.
        var rest = Character.Compare(ch, preview, Items.SlotFor(Items.Get(preview.Def))!.Value).Where(d => Shown.All(s => s.Key != d.Key)).ToList();
        stats.AddChild(Style.Label(diffs.Count == 0 ? $"In place of {against}: nothing here changes." : $"In place of {against}", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var (key, before, after) in rest)
        {
            var (text, good) = ItemViews.Delta(key, before, after);
            stats.AddChild(Style.H(6, Style.Label(good ? "better" : "worse", Style.UiHeavy, Style.Badge, good ? Style.Good : Style.Bad), Style.Label(text, Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad)));
        }
    }

    static string Format(string key, double v) => key switch
    {
        Stat.MaxHealth => $"{Math.Round(v)}",
        Stat.Armor => $"{Math.Round(v)} ({Math.Round(StatBlock.ArmorReduction(v) * 100)}%)",
        Stat.Damage => $"{(v >= 1 ? "+" : "")}{Math.Round((v - 1) * 100)}%",
        Stat.MoveSpeed => $"{v:0.0}",
        Stat.CritChance => $"{Math.Round(v * 100)}%",
        _ => $"{v:0.0}/s",
    };

    /* ---------------------------------------------------------- the pack -- */

    Control FilterRow()
    {
        var h = Style.H(6);
        bool pad = Controls.Instance.UsingPad;
        h.AddChild(pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)));
        for (int i = 0; i < Filters.Length; i++)
        {
            int f = i;
            h.AddChild(Nav.Skip(Style.Segment(Filters[i].Name, filter == i, () => { filter = f; Sound.Sfx.Page(); Refresh(); })));
        }
        h.AddChild(pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        h.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var sort = Style.Button("", Sort, false, true);
        var sr = Style.H(6, pad ? Style.PadButton("Y") : Glyphs.Icon("expand", 16, Style.GoldHi), Style.Label("Sort", Style.UiBold, Style.Small, Style.GoldHi));
        sr.MouseFilter = MouseFilterEnum.Ignore;
        sr.Position = new Vector2(10, 5);
        sort.AddChild(sr);
        sort.CustomMinimumSize = new Vector2(sr.GetCombinedMinimumSize().X + 22, 32);
        h.AddChild(Nav.Skip(sort));
        return h;
    }

    void SetupCell(int i, ItemInstance? it, SlotView view)
    {
        var ch = Ch;
        if (it != null)
        {
            view.Drag = $"pack:{it.Uid}";
            if (!seen.Contains(it.Uid))
            {
                // Marked new until it is looked at.
                var mark = Style.Panel(Style.Box(Style.Ember, Style.EmberHi, 1, 6, 3), Style.Label("NEW", Style.UiHeavy, 10, new Color("#2a1206"), false, HorizontalAlignment.Center, false));
                mark.MouseFilter = MouseFilterEnum.Ignore;
                mark.Position = new Vector2(2, 2);
                view.AddChild(mark);
            }
            if (!Filters[filter].Has(Items.Get(it.Def))) view.Modulate = new Color(1, 1, 1, 0.22f);
        }
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

    /// <summary>Hovered (mouse) or focused (pad): its card, and what it would change.</summary>
    void Hover(ItemInstance? it, Control? over)
    {
        if (it != null) seen.Add(it.Uid);
        ShowStats(it);
        if (Controls.Instance.UsingPad) { if (it != null) ShowInspect(it); Tip(null, null); return; }
        Tip(it != null && it.Uid != sel ? ItemViews.Compare(it, Ch, InPack(it)) : null, over);
    }

    bool InPack(ItemInstance it) => Inventory.Find(Ch, it.Uid) is { InPack: true } || Inventory.FromPouch(it.Uid) != null;

    /// <summary>The chosen thing: in the pack, worn, or a stack in the pouch.</summary>
    ItemInstance? Selected => sel == null ? null : Inventory.Find(Ch, sel)?.Item ?? Inventory.Pouch(Ch).FirstOrDefault(p => p.Uid == sel);

    /// <summary>Breaking down cannot be undone either: held to full, never asked twice (never in an arena).</summary>
    void BreakDown(ItemInstance it)
    {
        var q = Crafting.BreakDown(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;
        Sound.Sfx.Shatter();
        // The HUD's toasts are hidden under the pack: what it came to is said where it was read.
        broke = ($"Broken down: {Inventory.Name(it)}", $"{Style.Cap1(string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))))}, into the pouch for the forge.",
            Items.Get(q.Gives.Keys.First()).Icon, Time.GetTicksMsec());
        // Only the pack changed: the figure is not dressed again (that rebuilds her, and she blinks out).
        G.Journey.Work(it.Uid, q, G.Battle);
        Refresh();
    }

    /// <summary>What was just done to a thing and what it came to (broken down, steeped), said in the
    /// reading place: the HUD's toasts are under the pack.</summary>
    (string Title, string Sub, string Icon, ulong At)? broke;

    /// <summary>Steeping, by the survivor's own hand (docs/CRAFTING_DESIGN.md 9): the odds shown under the
    /// card while a jar is carried, the press held to full; what it came to said after. Never in an arena.</summary>
    void Steep(ItemInstance it)
    {
        var q = Crafting.Steep(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        Sound.Sfx.Pour();
        if (!G.Journey.Work(it.Uid, q, G.Battle)) return;
        // What it came to, said plainly over its card (the piece stays chosen, so the card shows it
        // as it is now), with how it looked under it.
        var (text, mood) = Crafting.Outcome(it, q);
        came = (it.Uid, text, mood, G.Journey.CraftSaid?.After);
        sel = it.Uid;
        Refresh();
    }

    /// <summary>What the slurry just did to a piece, said over its card while it stays chosen.</summary>
    (string Uid, string Text, int Mood, string? Seen)? came;

    void Select(string uid) { sel = sel == uid ? null : uid; leaving = null; Refresh(); }

    void Primary(ItemInstance it)
    {
        leaving = null;
        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return;
        var def = Items.Get(it.Def);
        if (!loc.InPack) { if (loc.Slot != EquipSlot.Weapon) G.Gear((j, b) => j.Unequip(loc.Slot, b)); else Sound.Sfx.Deny(); return; }
        if (def.Kind == ItemKind.Consumable) G.Gear((j, b) => j.Use(it.Uid, b));
        else if (Items.SlotFor(def) != null) { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(it.Uid, null, b)); }
        else Sound.Sfx.Deny();
    }

    /// <summary>Leaving a thing behind cannot be undone: the first time asks, the second does it.</summary>
    void Leave(ItemInstance it)
    {
        if (G.Journey.StillNeeded(it) || !InPack(it)) { Sound.Sfx.Deny(); return; }
        if (leaving != it.Uid) { leaving = it.Uid; Sound.Sfx.Hover(); ShowInspect(it); Footer(); return; }
        leaving = null;
        if (sel == it.Uid) sel = null;
        G.Journey.Drop(it.Uid);
    }

    /// <summary>The pack in order: gear by where it is worn, then draughts, then the rest; finer first.</summary>
    void Sort()
    {
        var ch = Ch;
        static int Group(ItemDef d) => Items.SlotFor(d) is EquipSlot s ? (int)s : d.Kind switch
        {
            ItemKind.Consumable => 20, ItemKind.Material => 30, ItemKind.Trophy => 31, ItemKind.Tool => 32, ItemKind.Quest => 40, _ => 50,
        };
        var items = ch.Pack.Where(p => p != null).Select(p => p!).OrderBy(p => Group(Items.Get(p.Def))).ThenByDescending(p => p.Rarity).ThenBy(p => Inventory.Name(p)).ToList();
        for (int i = 0; i < ch.Pack.Count; i++) ch.Pack[i] = i < items.Count ? items[i] : null;
        Sound.Sfx.Page();
        Refresh();
    }

    /// <summary>The thing chosen (or focused, with a pad) read closely, with what can be done with it.</summary>
    void ShowInspect(ItemInstance? it)
    {
        if (!IsInstanceValid(inspect)) return;
        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        // Shown for a few seconds, however often the page is built again meanwhile.
        if (it == null && broke is { } b && Time.GetTicksMsec() - b.At < 3000)
        {
            var words = Style.V(1, Style.Label(b.Title, Style.UiBold, Style.Body, Style.Ink, true),
                Style.Label(b.Sub, Style.TextItalic, Style.Small, Style.InkDim, true));
            words.CustomMinimumSize = new Vector2(380, 0);
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var row = Style.H(Style.Gap3, ItemPhotos.Icon(b.Icon, 48, Style.InkDim), words);
            var note = Style.Panel(Style.Slab(14), row);
            note.CustomMinimumSize = new Vector2(480, 0);
            inspect.AddChild(note);
            note.CreateTween().TweenProperty(note, "modulate:a", 0f, 0.8).SetDelay(Math.Max(0, 3.0 - (Time.GetTicksMsec() - b.At) / 1000.0));
            return;
        }
        if (it == null) return;
        var def = Items.Get(it.Def);
        if (came is { } cm && cm.Uid == it.Uid)
        {
            var col = cm.Mood > 0 ? ItemViews.SlurryGreen : cm.Mood < 0 ? Style.Bad : new Color("#9aa890");
            var words = Style.V(2, Style.Label("STEEPED", Style.UiHeavy, Style.Badge, col), Style.Label(cm.Text, Style.UiBold, Style.Body, cm.Mood < 0 ? Style.Bad : Style.Ink, true));
            if (cm.Seen != null) words.AddChild(Style.Label(cm.Seen, Style.TextItalic, Style.Small, Style.InkDim, true));
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var note = Style.Panel(Style.Box(new Color("#121a10"), col with { A = 0.6f }, 1, 5, 14), Style.H(Style.Gap3, Glyphs.Icon("drop", 28, col), words));
            note.CustomMinimumSize = new Vector2(480, 0);
            inspect.AddChild(note);
        }
        else if (came is { } old && old.Uid != it.Uid) came = null;
        var acts = Style.H(8);
        // A stack in the pouch: read, and left behind if it must be.
        if (Inventory.FromPouch(it.Uid) != null)
        {
            if (!Controls.Instance.UsingPad) acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it all behind for good" : "Leave behind", () => Leave(it), false, true));
            inspect.AddChild(ItemViews.Card(it, Ch, false, acts, 480));
            return;
        }
        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return;
        if (!Controls.Instance.UsingPad)
        {
            if (loc.InPack && def.Kind == ItemKind.Consumable) acts.AddChild(Style.Button("Use", () => Primary(it), true, true));
            if (loc.InPack && Items.SlotFor(def) != null) acts.AddChild(Style.Button("Wear", () => Primary(it), true, true));
            if (!loc.InPack && loc.Slot != EquipSlot.Weapon) acts.AddChild(Style.Button("Take off", () => Primary(it), false, true));
            if (loc.InPack && !G.Journey.StillNeeded(it))
                acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it behind for good" : "Leave behind", () => Leave(it), false, true));
            // Gear not kept breaks down to old iron for the forge (docs/CRAFTING_DESIGN.md 5.2).
            if (loc.InPack && !G.Journey.InArena && Crafting.BreakDown(G.Journey.Craft, it) is { Ok: true } bq)
            {
                // Held, in the colour of what cannot be undone.
                acts.AddChild(Style.HoldButton($"Break down for {Items.Several(Crafting.Iron, bq.Gives[Crafting.Iron])}", () => BreakDown(it)));
            }
            // A jar of the Dig's slurry carried: the one gamble, by the survivor's own hand.
            if (!G.Journey.InArena && Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) > 0 && Crafting.Steep(G.Journey.Craft, it) is { Ok: true })
            {
                acts.AddChild(Style.HoldButton("Steep", () => Steep(it)));
            }
        }
        // Gear in the pack reads beside what it would replace: the ARPGs' side by side.
        if (loc.InPack && Items.SlotFor(def) != null)
        {
            inspect.AddChild(ItemViews.Card(it, Ch, true, acts, 480));
            SteepOdds(it);
            var worn = ItemViews.Against(it, Ch);
            inspect.AddChild(Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim));
            if (worn != null) inspect.AddChild(ItemViews.Card(worn, Ch, false, null, 480, true));
            else
            {
                var empty = Style.Panel(Style.Slab(16), Style.Label("Nothing in that place: wearing it is all gain.", Style.TextItalic, Style.Small, Style.InkDim, true));
                empty.CustomMinimumSize = new Vector2(480, 0);
                inspect.AddChild(empty);
            }
            return;
        }
        inspect.AddChild(ItemViews.Card(it, Ch, loc.InPack, acts, 480));
        SteepOdds(it);
    }

    /// <summary>A jar carried and a piece it can take: everything it could come to, seen before the jar is
    /// opened (design 9), the same odds as at Snib's bench, laid out for this piece.</summary>
    void SteepOdds(ItemInstance it)
    {
        if (G.Journey.InArena || Controls.Instance.UsingPad || Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) == 0 || !Crafting.Steep(G.Journey.Craft, it).Ok) return;
        var lines = Style.V(Style.Gap2, Style.Label("Steeped, it comes to one of these, and is set for good after:", Style.UiBold, Style.Small, Style.Ink, true),
            ForgeScreen.SlurryOdds(it, 450));
        var slab = Style.Panel(Style.Box(new Color("#121a10"), ItemViews.SlurryGreen with { A = 0.45f }, 1, 5, 12), lines);
        slab.CustomMinimumSize = new Vector2(480, 0);
        inspect.AddChild(slab);
    }

    void Footer()
    {
        if (!IsInstanceValid(foot)) return;
        foreach (var c in foot.GetChildren()) { foot.RemoveChild(c); c.QueueFree(); }
        Control f;
        if (leaving != null && (Inventory.Find(Ch, leaving)?.Item ?? Inventory.Pouch(Ch).FirstOrDefault(p => p.Uid == leaving)) is { } l)
            f = Style.H(Style.Gap5, Style.Hint(Act.Alt, $"again to leave {Inventory.Name(l)} behind for good", Style.Bad), Style.Hint(Act.Cancel, "Keep it"));
        else if (Controls.Instance.UsingPad)
            f = Overlay.Footer((Act.Confirm, "Wear or use"), (Act.Alt, "Leave"), (Act.Alt2, "Sort"), (Act.SubNext, "Filter"), (Act.Cancel, "Close"));
        else f = MouseFooter("Right-click to wear or use", "drag to wear or take off", "hover to compare");
        if (f is BoxContainer bc) bc.Alignment = BoxContainer.AlignmentMode.Center;
        if (f is Label lb) lb.HorizontalAlignment = HorizontalAlignment.Center;
        f.Size = foot.CustomMinimumSize;
        foot.AddChild(f);
    }

    public override bool Key(Act a)
    {
        switch (a)
        {
            case Act.SubNext: filter = (filter + 1) % Filters.Length; Sound.Sfx.Page(); Refresh(); return true;
            case Act.SubPrev: filter = (filter + Filters.Length - 1) % Filters.Length; Sound.Sfx.Page(); Refresh(); return true;
            case Act.Alt2: Sort(); return true;
            case Act.Cancel when leaving != null:
                leaving = null;
                Footer();
                ShowInspect(Selected);
                return true;
        }
        if (a is Act.Up or Act.Down or Act.Left or Act.Right && leaving != null) { leaving = null; Footer(); }
        return false;
    }

    /// <summary>The survivor's standing as a small table (also shown on the sheet).</summary>
    public static Control Stats(CharacterData ch)
    {
        var k = Character.Kit(ch).Stats;
        var g = new GridContainer { Columns = 4, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 14);
        foreach (var (key, name) in Shown)
        {
            g.AddChild(Style.Label(name, Style.Ui, Style.Caption, Style.InkDim));
            g.AddChild(Style.Label(Format(key, k.Get(key)), Style.UiBold, Style.Small, Style.Ink));
        }
        return g;
    }
}

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
        Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Compare(it, ch, true) : null, over);
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
        shelves.SizeFlagsVertical = SizeFlags.ShrinkBegin;
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
