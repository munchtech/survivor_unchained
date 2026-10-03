using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Items on screen (the web game's ItemCard and ItemGrid): a slot in a
/// grid, rimmed in its rarity's colour, with how many and (in a shop) the
/// price; and a card with everything an item is: what it does to the fight,
/// what it says to the world, what it is worth and where it came from. A
/// hovered item compares itself with what it would replace.
/// </summary>
public static class ItemViews
{
    public static readonly Dictionary<string, string> TagLines = new()
    {
        ["beastscent"] = "Wolves smell the forest on you, not the town.",
        ["kerchief_colors"] = "Kerchiefs read you as one of theirs. So does the Watch.",
        ["plague_mask"] = "You can breathe where the air is blighted.",
        ["holy_light"] = "The dead do not like its light.",
        ["necromantic"] = "The Order of Morning Light will not approve.",
        ["lockpick"] = "Opens simple locks.",
        ["scholar_lens"] = "Old script becomes legible through it.",
        ["wolf_fang"] = "A statement to any wolf that sees it.",
        ["fireproof"] = "Fire finds little purchase.",
        ["digger_lamp"] = "The lamplings know whose it is.",
        ["moon_touched"] = "Something in the grove marked you.",
        ["explosive"] = "Something could be blown open with this. Or up.",
        ["warden_iron"] = "Remembers the light it held.",
        ["wolf_pelts"] = "Any wolf that smells it will know what it is.",
    };

    static readonly Dictionary<ItemKind, string> KindNames = new()
    {
        [ItemKind.Weapon] = "Weapon", [ItemKind.Offhand] = "Off-hand", [ItemKind.Head] = "Head", [ItemKind.Body] = "Body", [ItemKind.Cloak] = "Cloak",
        [ItemKind.Amulet] = "Amulet", [ItemKind.Ring] = "Ring", [ItemKind.Relic] = "Relic", [ItemKind.Material] = "Material",
        [ItemKind.Consumable] = "Consumable", [ItemKind.Quest] = "Quest item", [ItemKind.Tool] = "Tool", [ItemKind.Trophy] = "Trophy",
    };

    static readonly Dictionary<string, string> StatNames = new()
    {
        ["maxHealth"] = "Health", ["armor"] = "Armour", ["damage"] = "Damage", ["cooldown"] = "Weapon speed", ["area"] = "Area", ["critChance"] = "Critical chance",
        ["moveSpeed"] = "Speed", ["regen"] = "Regeneration", ["damage.fire"] = "Fire damage", ["damage.frost"] = "Frost damage", ["damage.holy"] = "Holy damage",
        ["damage.physical"] = "Physical damage", ["resist.fire"] = "Fire resistance", ["resist.nature"] = "Nature resistance",
    };

    public static readonly Dictionary<Sim.School, Color> SchoolColors = new()
    {
        [Sim.School.Physical] = new("#e8dcc4"), [Sim.School.Fire] = new("#ff8a4a"), [Sim.School.Frost] = new("#8fd0ff"), [Sim.School.Storm] = new("#9ab8ff"),
        [Sim.School.Nature] = new("#8ae05a"), [Sim.School.Arcane] = new("#cc88ff"), [Sim.School.Holy] = new("#ffd46a"), [Sim.School.Shadow] = new("#a87aff"),
    };

    static (string Text, bool Good) Delta(string key, double before, double after)
    {
        double d = after - before;
        string name = StatNames.GetValueOrDefault(key, key);
        if (key == "cooldown") { int pct = (int)Math.Round((before / after - 1) * 100); return ($"{(pct >= 0 ? "+" : "")}{pct}% {name}", pct >= 0); }
        if (key == "moveSpeed") { int pct = (int)Math.Round((after / before - 1) * 100); return ($"{(pct >= 0 ? "+" : "")}{pct}% {name}", pct >= 0); }
        if (key is "maxHealth" or "armor") return ($"{(d > 0 ? "+" : "")}{Math.Round(d * 10) / 10} {name}", d > 0);
        if (key == "regen") return ($"{(d > 0 ? "+" : "")}{d:0.0}/s {name}", d > 0);
        double p = Math.Round(d * 1000) / 10;
        return ($"{(p > 0 ? "+" : "")}{p}% {name}", d > 0);
    }

    /// <summary>A soft pool of light, brightest in the middle.</summary>
    static readonly GradientTexture2D Halo = new()
    {
        Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
        Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 1f } },
    };

    /// <summary>One slot of a grid: empty, or an item rimmed in its rarity. A
    /// click chooses it, a double click or a right click does its first thing
    /// (wear, use, buy); with a name it can take focus, where A does that first
    /// thing, X its second (onAlt), and its card shows beside it.</summary>
    public static Control Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null)
    {
        var box = new Panel { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop };
        var rim = it != null ? Style.RarityOf(it.Rarity) with { A = selected ? 1 : 0.55f } : Style.Line with { A = 0.18f };
        var bg = it != null ? new Color(0.08f, 0.07f, 0.09f, 0.95f).Lerp(Style.RarityOf(it.Rarity), 0.08f) : new Color(0.05f, 0.045f, 0.06f, 0.8f);
        var flat = Style.Box(bg, rim, selected ? 2 : 1, 4, 0);
        box.AddThemeStyleboxOverride("panel", UiArt.Frame(it != null ? $"slot_{Math.Clamp(it.Rarity, 0, 5)}" : "slot", flat));
        if (it != null)
        {
            var def = Items.Get(it.Def);
            // The finer the thing, the more light it sits in.
            if (it.Rarity > 0)
            {
                var halo = new TextureRect
                {
                    Texture = Halo, Position = new Vector2(1, 1), Size = new Vector2(size - 2, size - 2), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
                    Modulate = Style.RarityOf(it.Rarity) with { A = 0.12f + 0.07f * it.Rarity }, MouseFilter = Control.MouseFilterEnum.Ignore,
                };
                box.AddChild(halo);
            }
            // Smaller over a caption, which stays readable under it.
            float k = caption != null ? 0.72f : 0.86f;
            var icon = ItemPhotos.Icon(def.Icon, (int)(size * k), Style.RarityOf(it.Rarity).Lightened(0.25f));
            icon.Position = new Vector2(size * (1 - k) / 2, caption != null ? size * 0.02f : size * 0.05f);
            icon.Size = new Vector2(size * k, size * k);
            box.AddChild(icon);
            if (it.Qty > 1)
            {
                // How many, as a count (x3), never to be mistaken for a price.
                var q = Style.Label($"×{it.Qty}", Style.UiHeavy, Style.Badge, Style.Ink);
                q.HorizontalAlignment = HorizontalAlignment.Right;
                q.Size = new Vector2(size - 6, 16);
                q.Position = new Vector2(0, size - 18);
                box.AddChild(q);
            }
            if (Items.SlotFor(def) != null)
            {
                var dot = new ColorRect { Color = Style.Gold with { A = 0.7f }, Size = new Vector2(4, 4), Position = new Vector2(size - 8, 4), MouseFilter = Control.MouseFilterEnum.Ignore };
                box.AddChild(dot);
            }
            if (price is int p)
            {
                // The price on a dark tag at the top, with its coin.
                var tag = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f, 0.85f), Style.GoldDim, 1, 3, 3), Style.H(2, Glyphs.Icon("coin", 11, Style.GoldHi), Style.Label($"{p}", Style.UiHeavy, Style.Badge, Style.GoldHi)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                tag.Position = new Vector2(2, 2);
                box.AddChild(tag);
            }
            if (refused) box.Modulate = new Color(1, 1, 1, 0.4f);
        }
        else if (emptyGlyph != null)
        {
            var icon = Glyphs.Icon(emptyGlyph, size / 2, Style.Gold with { A = 0.22f });
            icon.Position = new Vector2(size / 4f, size / 4f - (caption != null ? 5 : 0));
            icon.Size = new Vector2(size / 2f, size / 2f);
            box.AddChild(icon);
        }
        if (caption != null)
        {
            var c = Style.Label(caption.ToUpperInvariant(), Style.UiHeavy, 10, Style.GoldDim, false, HorizontalAlignment.Center);
            c.Position = new Vector2(0, size - 16);
            c.Size = new Vector2(size, 14);
            box.AddChild(c);
        }
        box.GuiInput += e =>
        {
            if (e is not InputEventMouseButton { Pressed: true } mb || it == null) return;
            if (mb.ButtonIndex == MouseButton.Right) onDouble?.Invoke();
            else if (mb.ButtonIndex == MouseButton.Left) { if (mb.DoubleClick) onDouble?.Invoke(); else onClick?.Invoke(); }
        };
        if (onHover != null)
        {
            box.MouseEntered += () => onHover(it != null ? box : null);
            box.MouseExited += () => onHover(null);
        }
        if (navId != null)
            Nav.Mark(box, navId, it != null ? onDouble ?? onClick ?? (() => { }) : () => { }, it != null ? onAlt : null, null,
                () => onHover?.Invoke(it != null ? box : null), () => onHover?.Invoke(null));
        return box;
    }

    /// <summary>A grid of slots (the pack, a shelf, the storeroom); with a name, each slot can take focus.</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null)
    {
        var g = new GridContainer { Columns = cols, MouseFilter = Control.MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 5);
        g.AddThemeConstantOverride("v_separation", 5);
        int i = 0;
        foreach (var it in items)
        {
            int? p = it != null && price != null ? price(it) : null;
            g.AddChild(Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null));
            i++;
        }
        return g;
    }

    /// <summary>The worn thing an item would replace, if any (the second ring's place when the first is taken).</summary>
    public static ItemInstance? Against(ItemInstance it, CharacterData ch)
    {
        var def = Items.Get(it.Def);
        if (Items.SlotFor(def) is not EquipSlot slot) return null;
        if (Enum.GetValues<EquipSlot>().Any(s => ch.Equipment[s]?.Uid == it.Uid)) return null;
        var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
        return ch.Equipment[target];
    }

    /// <summary>A hovered thing's card, with the worn one it would replace beside it
    /// (the ARPGs' side-by-side comparison: docs/UI_RESEARCH.md 7.1).</summary>
    public static Control Compare(ItemInstance it, CharacterData ch, bool compare)
    {
        var card = Card(it, ch, compare);
        if (!compare || Against(it, ch) is not { } worn) return card;
        var h = Style.H(Style.Gap2, card);
        var w = Style.V(4, Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim), Card(worn, ch, false, null, 300, true));
        h.AddChild(w);
        return h;
    }

    /// <summary>Everything an item is, on one card (worn: the quieter card beside a comparison).</summary>
    public static PanelContainer Card(ItemInstance it, CharacterData? ch, bool compare, Control? actions = null, int width = 340, bool worn = false)
    {
        var def = Items.Get(it.Def);
        var col = Style.RarityOf(it.Rarity);
        var card = Style.Panel(UiArt.Frame(worn ? "tooltip_worn" : "tooltip", Style.Box(new Color(0.07f, 0.062f, 0.08f, worn ? 0.94f : 0.98f), col with { A = worn ? 0.35f : 0.6f }, 1, 5, 14)));
        card.CustomMinimumSize = new Vector2(width, 0);
        var v = Style.V(6);
        card.AddChild(v);
        var head = Style.H(10);
        var photo = Style.Panel(Style.Box(new Color(0.03f, 0.03f, 0.04f), col with { A = 0.35f }, 1, 4, 4), ItemPhotos.Icon(def.Icon, 64, col.Lightened(0.25f)));
        head.AddChild(photo);
        var names = Style.V(2);
        names.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        names.AddChild(Style.Label(Inventory.Name(it), Style.TextBold, 19, col, true));
        var kind = Style.H(Style.Gap2, Style.Label($"{Inventory.RarityName(it)} {KindNames.GetValueOrDefault(def.Kind, def.Kind.ToString())}{(def.Unique ? " · Unique" : "")}", Style.Ui, Style.Caption, Style.InkDim), Style.Gems(it.Rarity, 5));
        kind.Alignment = BoxContainer.AlignmentMode.Begin;
        names.AddChild(kind);
        head.AddChild(names);
        v.AddChild(head);
        if (def.Weapon is { } iw && Weapons.All.TryGetValue(iw.Id, out var w))
            v.AddChild(Style.H(6, Glyphs.Icon(w.Art, 15, SchoolColors[w.School]), Style.Label($"{w.Name} · rank {iw.Rank} · {w.School.ToString().ToLowerInvariant()}", Style.UiBold, 14, SchoolColors[w.School])));
        v.AddChild(Style.Label(def.Description, Style.Text, Style.Small, Style.Ink, true));
        var lines = Inventory.Lines(it).Where(l => l != "").ToList();
        if (lines.Count > 0) v.AddChild(Style.V(1, lines.Select(l => (Control)Style.Label(l, Style.UiBold, Style.Caption, new Color("#9ad8ff"), true)).ToArray()));
        if (def.Downside != null) v.AddChild(Style.Label(def.Downside, Style.UiBold, Style.Caption, Style.Bad, true));
        foreach (var t in def.Tags ?? new())
            if (TagLines.TryGetValue(t, out var tl)) v.AddChild(Style.H(6, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(tl, Style.TextItalic, Style.Caption, Style.GoldHi, true)));
        if (def.Lore != null) v.AddChild(Style.Label(def.Lore, Style.TextItalic, Style.Caption, Style.InkDim, true));
        if (it.History is { Count: > 0 } h) v.AddChild(Style.V(1, h.Select(x => (Control)Style.Label(x, Style.TextItalic, Style.Caption, Style.InkFaint, true)).ToArray()));
        if (compare && ch != null && Items.SlotFor(def) is EquipSlot slot)
        {
            var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
            bool isWorn = Enum.GetValues<EquipSlot>().Any(s => ch.Equipment[s]?.Uid == it.Uid);
            if (!isWorn)
            {
                var diffs = Character.Compare(ch, it, target);
                if (diffs.Count > 0)
                {
                    v.AddChild(Style.Rule());
                    var against = ch.Equipment[target];
                    v.AddChild(Style.Label($"Instead of {(against != null ? Inventory.Name(against) : "nothing")}", Style.UiBold, Style.Caption, Style.InkDim));
                    foreach (var (key, before, after) in diffs)
                    {
                        // Better or worse said three ways: colour, the sign, and a word.
                        var (text, good) = Delta(key, before, after);
                        v.AddChild(Style.H(6, Style.Label(good ? "better" : "worse", Style.UiHeavy, Style.Badge, good ? Style.Good : Style.Bad), Style.Label(text, Style.UiBold, Style.Small, good ? Style.Good : Style.Bad)));
                    }
                }
            }
        }
        var foot = Style.H(12);
        if (it.Qty > 1) foot.AddChild(Style.Label($"×{it.Qty}", Style.UiBold, Style.Caption, Style.InkDim));
        foot.AddChild(Style.H(4, Glyphs.Icon("coin", 14, Style.GoldHi), Style.Label($"{def.Value * Math.Max(1, it.Qty)}", Style.UiBold, Style.Caption, Style.GoldHi)));
        v.AddChild(foot);
        if (actions != null) v.AddChild(actions);
        return card;
    }
}
