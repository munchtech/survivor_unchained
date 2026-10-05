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
    /// <summary>The slurry's sick green: what it put in a piece, and the veins.</summary>
    public static readonly Color SlurryGreen = new("#a8e08a");
    /// <summary>The bright grade (V), which only the slurry gives: a pale light, not a rarity's colour.</summary>
    public static readonly Color BrightGrade = new("#eaffd6");

    /// <summary>A steeped piece's picture with the slurry in it (design 9: "green-black veins, a sick
    /// glow"): the veins run through the thing itself, not over its frame, so they are drawn by a
    /// shader on the picture's own pixels. Returns the icon it was given.</summary>
    public static Control Steeped(Control icon)
    {
        foreach (var c in icon.GetChildren()) if (c is TextureRect r) r.Material = SlurryMaterial;
        if (icon is TextureRect self) self.Material = SlurryMaterial;
        return icon;
    }

    static ShaderMaterial? slurry;
    static ShaderMaterial SlurryMaterial => slurry ??= new ShaderMaterial { Shader = new Shader { Code = SlurryShader } };

    // A net of thin veins (the borders of warped cells), thinned out in patches so it reads as grown
    // through the piece rather than laid over it; near black at their hearts, a sick green light
    // along them, and a green cast over the whole.
    const string SlurryShader = @"shader_type canvas_item;
vec2 h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float vn(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h2(i).x, h2(i + vec2(1.0, 0.0)).x, f.x), mix(h2(i + vec2(0.0, 1.0)).x, h2(i + vec2(1.0, 1.0)).x, f.x), f.y);
}
float edge(vec2 x) {
    vec2 n = floor(x), f = fract(x);
    float d1 = 8.0, d2 = 8.0;
    for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 r = g + h2(n + g) - f;
        float d = dot(r, r);
        if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
    }
    return sqrt(d2) - sqrt(d1);
}
void fragment() {
    vec4 c = COLOR;
    vec2 p = UV * 3.4 + vec2(vn(UV * 5.0), vn(UV * 5.0 + 7.3)) * 0.55;
    float e = edge(p);
    float keep = smoothstep(0.32, 0.62, vn(UV * 2.2 + 3.1));
    float vein = (1.0 - smoothstep(0.015, 0.06, e)) * keep;
    float glow = (1.0 - smoothstep(0.0, 0.2, e)) * keep;
    vec3 col = mix(c.rgb, c.rgb * vec3(0.62, 0.86, 0.55), 0.4);
    col += vec3(0.22, 0.5, 0.12) * glow * 0.45;
    col = mix(col, vec3(0.02, 0.06, 0.02), vein * 0.92);
    COLOR = vec4(col, c.a);
}";

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
        ["greymuzzle_fang"] = "The Pack knows it by sight.",
        ["slurried"] = "Steeped: green-black veins run through it. It is set for good.",
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

    /// <summary>A change in words: "+5% Area", and whether it is for the better.</summary>
    public static (string Text, bool Good) Delta(string key, double before, double after)
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
    public static SlotView Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null, bool fresh = false, bool dim = false, bool dear = false)
    {
        var box = new SlotView { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop, Item = it };
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
            // Steeped: the veins run through it wherever it is seen.
            if (Crafting.Slurried(it)) Steeped(icon);
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
                // The price on a dark tag at the top, with its coin; red when it is more than you have.
                var pc = dear ? Style.Bad : Style.GoldHi;
                var tag = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f, 0.85f), dear ? Style.Bad with { A = 0.6f } : Style.GoldDim, 1, 3, 3), Style.H(2, Glyphs.Icon("coin", 11, pc), Style.Label($"{p}", Style.UiHeavy, Style.Badge, pc)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                tag.Position = new Vector2(2, 2);
                box.AddChild(tag);
            }
            // New since the pack was last looked at: an ember mark until it is.
            if (fresh)
            {
                var mark = Style.Panel(Style.Box(Style.Ember, Style.EmberHi, 1, 6, 3), Style.Label("NEW", Style.UiHeavy, 10, new Color("#2a1206"), false, HorizontalAlignment.Center, false));
                mark.MouseFilter = Control.MouseFilterEnum.Ignore;
                mark.Position = new Vector2(2, 2);
                box.AddChild(mark);
            }
            if (refused || dim) box.Modulate = new Color(1, 1, 1, dim ? 0.25f : 0.4f);
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
            var c = Style.Label(caption.ToUpperInvariant(), Style.UiHeavy, 11, Style.GoldDim, false, HorizontalAlignment.Center);
            // Inside the painted well's lip, not on it.
            c.Position = new Vector2(0, size - (UiArt.Has("slot") ? 23 : 16));
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

    /// <summary>A grid of slots (the pack, a shelf, the storeroom); with a name, each slot can take focus;
    /// setup readies each cell for dragging and dropping (its index, its item, the slot).</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null, Action<int, ItemInstance?, SlotView>? setup = null, Func<ItemInstance, bool>? dear = null)
    {
        var g = new GridContainer { Columns = cols, MouseFilter = Control.MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 5);
        g.AddThemeConstantOverride("v_separation", 5);
        int i = 0;
        foreach (var it in items)
        {
            int? p = it != null && price != null ? price(it) : null;
            var slot = Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null,
                dear: it != null && dear?.Invoke(it) == true);
            setup?.Invoke(i, it, slot);
            g.AddChild(slot);
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
        bool slurried = Crafting.Slurried(it);
        var pic = ItemPhotos.Icon(def.Icon, 64, col.Lightened(0.25f));
        if (slurried) Steeped(pic);
        var photo = Style.Panel(Style.Box(new Color(0.03f, 0.03f, 0.04f), slurried ? SlurryGreen with { A = 0.5f } : col with { A = 0.35f }, 1, 4, 4), pic);
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
        // Each affix with its grade (I to IV: docs/CRAFTING_DESIGN.md 5.1); coals and worn skills have none.
        var lines = it.Affixes.Select(a => (Def: Items.Affix(a.Id), a.Tier)).Where(x => x.Def != null && x.Def.Text(x.Tier) != "").ToList();
        if (lines.Count > 0)
            v.AddChild(Style.V(1, lines.Select(x =>
            {
                bool bright = x.Tier >= Crafting.Bright && x.Def!.Kindled == null && x.Def.Grants == null && !x.Def.Slurry;
                if (x.Def!.Slurry)
                {
                    // The slurry's power, past the seams: its gift in green, its price after it in red.
                    var parts = x.Def.Text(x.Tier).Split(';', 2);
                    var row = Style.H(4, Glyphs.Icon("drop", 13, SlurryGreen), Style.Label(parts.Length > 1 ? $"{parts[0]};" : parts[0], Style.UiBold, Style.Caption, SlurryGreen));
                    if (parts.Length > 1) row.AddChild(Style.Label(parts[1].Trim(), Style.UiBold, Style.Caption, Style.Bad));
                    return (Control)row;
                }
                var text = Style.Label(x.Def.Text(x.Tier), Style.UiBold, Style.Caption, x.Def.Kindled != null ? Style.EmberHi : bright ? BrightGrade : new Color("#9ad8ff"), true);
                if (x.Def.Kindled != null || x.Def.Grants != null) return text;
                // The bright grade reads as a light, not as one more numeral.
                var grade = Style.Label(Crafting.Grade(x.Tier), Style.Display, bright ? 14 : 12, bright ? BrightGrade : Style.GoldDim);
                if (bright) { grade.AddThemeConstantOverride("outline_size", 4); grade.AddThemeColorOverride("font_outline_color", SlurryGreen with { A = 0.45f }); }
                grade.CustomMinimumSize = new Vector2(22, 0);
                return Style.H(4, grade, text);
            }).ToArray()));
        if (it.Heat != null && Crafting.OpenSeams(it) is int open && open > 0)
            v.AddChild(Style.Label(open == 1 ? "An open seam: something can be worked into it" : $"{open} open seams: things can be worked into it", Style.TextItalic, Style.Caption, Style.GoldDim, true));
        // (A steeped piece's veins say it is set, below; not twice.)
        if (it.Heat is int heat && !(heat == 0 && slurried))
            v.AddChild(Style.Label(heat > 0 ? $"Heat {heat} of {it.HeatFull ?? heat}: it can still be worked" : "Set: nothing more can be worked into it", Style.UiBold, Style.Caption, heat > 0 ? Style.Ember : Style.InkDim));
        if (def.Downside != null) v.AddChild(Style.Label(def.Downside, Style.UiBold, Style.Caption, Style.Bad, true));
        foreach (var t in (def.Tags ?? new()).Concat(it.Marks ?? new()).Distinct())
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
