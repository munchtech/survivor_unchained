using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

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
    /// <summary>A Mark's: the binders' ink, a violet that is no rarity's.</summary>
    public static readonly Color MarkInk = new("#c4a8ff");

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

    /// <summary>A change as a signed number alone ("+4", "+21%", "−0.2/s"), for the right of a line,
    /// and whether it is for the better.</summary>
    public static (string Text, bool Good) DeltaNumber(string key, double before, double after)
    {
        var (text, good) = Delta(key, before, after);
        int sp = text.IndexOf(' ');
        return (sp > 0 ? text[..sp] : text, good);
    }

    /* ----------------------------------------------------------- tiers -- */

    /// <summary>Each tier's colour (docs/design/LOOT_DESIGN.md 3): the band, everywhere the same, from
    /// a tile's edge to a card's name to a label on the ground. Set is verdigris, old bronze's patina.</summary>
    public static Color TierColour(LootTier t) => t switch
    {
        LootTier.Common => new("#c8c0b0"), LootTier.Uncommon => new("#6fd46a"), LootTier.Rare => new("#5aa8ff"),
        LootTier.Epic => new("#c070ff"), LootTier.Set => SetColour, LootTier.Legendary => new("#ffb040"),
        LootTier.Storied => new("#ff6a3a"), LootTier.Book or LootTier.Chart => new("#dccba4"), LootTier.Quest => new("#f3d9a0"),
        _ => new("#c8c0b0"),
    };

    public static readonly Color SetColour = new("#3fd6c0");

    /// <summary>A thing's colour: its tier's, except what is counted (a material, a draught) keeps its
    /// own rarity's, so an ember shard still glints among pelts.</summary>
    public static Color ColourOf(ItemInstance it)
    {
        var t = Drops.TierOf(it);
        return t is LootTier.Material or LootTier.Draught ? Style.RarityOf(it.Rarity) : TierColour(t);
    }

    public static string TierName(LootTier t) => t switch
    {
        LootTier.Draught => "Draught", LootTier.Quest => "Quest", _ => t.ToString(),
    };

    /// <summary>What a thing is, in a word, after its tier ("Epic helm").</summary>
    static readonly Dictionary<ItemKind, string> Nouns = new()
    {
        [ItemKind.Weapon] = "weapon", [ItemKind.Offhand] = "off-hand", [ItemKind.Head] = "helm", [ItemKind.Body] = "body armour", [ItemKind.Cloak] = "cloak",
        [ItemKind.Amulet] = "amulet", [ItemKind.Ring] = "ring", [ItemKind.Relic] = "relic",
    };

    /// <summary>The line under a card's name: tier and kind, then for gear its level and make
    /// ("Epic helm · level 14 · Wrought"); for what is counted, where it is kept.</summary>
    public static string KindLine(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        var t = Drops.TierOf(it);
        if (Items.SlotFor(def) != null)
        {
            string noun = def.Weapon is { } iw && Weapons.All.TryGetValue(iw.Id, out var w) ? w.Name.ToLowerInvariant() : Nouns.GetValueOrDefault(def.Kind, "piece");
            string head = $"{TierName(t)} {noun}";
            return Drops.Leveled(def) ? $"{head}  ·  level {Drops.LevelOf(it)}  ·  {Drops.MakeOf(it)}" : head;
        }
        return Drops.StoreOf(def, it) switch
        {
            Store.Pouch => def.Kind == ItemKind.Trophy ? "Trophy  ·  in the pouch" : "Material  ·  in the pouch",
            Store.Belt => "Draught  ·  on the belt",
            Store.Satchel => t == LootTier.Chart ? "Chart  ·  in the satchel" : "Book  ·  in the satchel",
            Store.Keys => def.Kind == ItemKind.Quest ? "Quest  ·  on the key ring" : "Tool  ·  on the key ring",
            _ => KindNames.GetValueOrDefault(def.Kind, def.Kind.ToString()),
        };
    }

    /* ------------------------------------------------------------ tiles -- */

    /// <summary>One tile of a grid (UI_RESEARCH 4: empty is quiet, a filled one carries its tier as
    /// tint and edge). Its corners each say one thing: its level top left, an upgrade (or a better
    /// make) top right, a set's link bottom left, how many or its price bottom right. A click chooses
    /// it, a double or right click does its first thing (wear, use, buy); with a name it takes focus,
    /// where A does that first thing and X its second (onAlt), and its card shows beside it. The
    /// marks are judged against `ch` (what they wear), when given.</summary>
    public static SlotView Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null, bool fresh = false, bool dim = false, bool dear = false, CharacterData? ch = null)
    {
        var box = new SlotView { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop, Item = it };
        box.AddThemeStyleboxOverride("panel", Kit.TileBox(it, selected));
        if (it != null)
        {
            var def = Items.Get(it.Def);
            var col = ColourOf(it);
            float k = 0.8f;
            var icon = ItemPhotos.Icon(def.Icon, (int)(size * k), col.Lightened(0.25f));
            icon.Position = new Vector2(size * (1 - k) / 2, size * (1 - k) / 2);
            icon.Size = new Vector2(size * k, size * k);
            box.AddChild(icon);
            // Steeped: the veins run through it wherever it is seen.
            if (Crafting.Slurried(it)) Steeped(icon);
            var tier = Drops.TierOf(it);
            bool small = size < 60;
            if (Drops.Leveled(def) && !small)
                Corner(box, Style.Label($"{Drops.LevelOf(it)}", Style.UiBold, 12, Kit.Ink2), new Vector2(5, 2));
            if (tier == LootTier.Set) Corner(box, new TileMark(TileMark.Kind.Link, SetColour), new Vector2(4, size - 18));
            var marks = Style.H(2);
            if (fresh) marks.AddChild(new TileMark(TileMark.Kind.Dot, Style.Ember));
            if (ch != null && Items.SlotFor(def) != null && Inventory.Find(ch, it.Uid) is not { Worn: true })
            {
                if (Drops.IsUpgrade(ch, it)) marks.AddChild(new TileMark(TileMark.Kind.Up, Style.Good));
                else if (Drops.BetterMake(ch, it)) marks.AddChild(new TileMark(TileMark.Kind.Anvil, Kit.Ink2));
            }
            if (marks.GetChildCount() > 0)
            {
                box.AddChild(marks);
                marks.Position = new Vector2(size - 4 - marks.GetCombinedMinimumSize().X, 4);
            }
            if (price is int p)
            {
                // The price on a dark tag at the foot, with its coin; red when it is more than you have.
                var pc = dear ? Style.Bad : Style.GoldHi;
                var tagBox = new StyleBoxFlat { BgColor = new Color(0.04f, 0.035f, 0.045f, 0.9f), ContentMarginLeft = 4, ContentMarginRight = 4, ContentMarginTop = 0, ContentMarginBottom = 0 };
                tagBox.SetCornerRadiusAll(3);
                var tag = Style.Panel(UiArt.Frame("price", tagBox), Style.H(3, Glyphs.Icon("coin", 11, pc), Style.Label($"{p}", Style.UiHeavy, Style.Badge, pc, false, HorizontalAlignment.Left, false)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                box.AddChild(tag);
                tag.Position = new Vector2(size - 3 - tag.GetCombinedMinimumSize().X, size - 3 - tag.GetCombinedMinimumSize().Y);
                if (it.Qty > 1) Corner(box, Style.Label($"×{it.Qty}", Style.UiHeavy, Style.Badge, Kit.Ink), new Vector2(5, 2));
            }
            else if (it.Qty > 1)
            {
                // How many, as a count (x3), never to be mistaken for a price.
                var q = Style.Label($"×{it.Qty}", Style.UiHeavy, small ? 12 : Style.Badge, Kit.Ink);
                q.HorizontalAlignment = HorizontalAlignment.Right;
                q.Size = new Vector2(size - 5, 16);
                q.Position = new Vector2(0, size - 17);
                box.AddChild(q);
            }
            if (refused || dim) box.Modulate = new Color(1, 1, 1, dim ? 0.25f : 0.4f);
        }
        else if (caption != null)
        {
            // An empty place on the body: its name, quiet, where the thing would go.
            var c = Style.Label(caption.ToUpperInvariant(), Style.UiBold, size < 72 ? 10 : 12, Kit.Glyph, false, HorizontalAlignment.Center, false);
            c.VerticalAlignment = VerticalAlignment.Center;
            c.Size = new Vector2(size, size);
            box.AddChild(c);
        }
        else if (emptyGlyph != null)
        {
            var icon = Glyphs.Icon(emptyGlyph, size / 2, Kit.Glyph);
            icon.Position = new Vector2(size / 4f, size / 4f);
            icon.Size = new Vector2(size / 2f, size / 2f);
            box.AddChild(icon);
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

    static void Corner(Control box, Control mark, Vector2 at)
    {
        mark.MouseFilter = Control.MouseFilterEnum.Ignore;
        mark.Position = at;
        box.AddChild(mark);
    }

    /// <summary>A grid of tiles (the pack, a shelf, the storeroom); with a name, each tile can take focus;
    /// setup readies each cell for dragging and dropping (its index, its item, the tile).</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null, Action<int, ItemInstance?, SlotView>? setup = null, Func<ItemInstance, bool>? dear = null,
        CharacterData? ch = null, int gap = 8, Func<ItemInstance, bool>? fresh = null)
    {
        var g = new GridContainer { Columns = cols, MouseFilter = Control.MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", gap);
        g.AddThemeConstantOverride("v_separation", gap);
        int i = 0;
        foreach (var it in items)
        {
            int? p = it != null && price != null ? price(it) : null;
            var slot = Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null,
                it != null && fresh?.Invoke(it) == true, false, it != null && dear?.Invoke(it) == true, ch);
            setup?.Invoke(i, it, slot);
            g.AddChild(slot);
            i++;
        }
        return g;
    }

    /// <summary>The rows a grid shows: those in use and one more (at least two), up to all it holds
    /// (UI_RESEARCH, "Waste no space"): the count in the head says the rest.</summary>
    public static int RowsShown(IReadOnlyList<ItemInstance?> places, int cols, int least = 2)
    {
        int last = -1;
        for (int i = 0; i < places.Count; i++) if (places[i] != null) last = i;
        int all = (places.Count + cols - 1) / cols;
        return Math.Clamp(last / cols + 2, Math.Min(least, all), all);
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

    /// <summary>A hovered thing's card and, for gear not worn, the worn piece it would replace
    /// (docs/design/UI_RESEARCH.md 7): the screen lays them beside the thing (Overlay.TipBeside).</summary>
    public static (Control Card, Control? Worn) Compare(ItemInstance it, CharacterData ch, bool compare, Control? prompts = null, int? price = null, bool dear = false)
    {
        var card = Card(it, ch, compare, null, 330, false, prompts, price, dear);
        if (!compare || Against(it, ch) is not { } worn) return (card, null);
        return (card, Card(worn, ch, false, null, 290, true));
    }

    /* ------------------------------------------------------------- card -- */

    /// <summary>What a number on a piece says, in words: its base's numbers read as "Armour 7", the
    /// rest as a change ("+8 health", "+12% fire resistance").</summary>
    public static string ModText(StatMod m, bool implicitBase = false)
    {
        string name = Noun(m.Stat);
        bool pct = m.Kind != ModKind.Flat || Percent(m.Stat);
        double v = pct ? m.Value * 100 : m.Value;
        string num = Math.Abs(v - Math.Round(v)) < 0.05 ? $"{Math.Round(v)}" : $"{v:0.#}";
        if (implicitBase && m.Kind == ModKind.Flat && m.Stat == Stat.Armor) return $"Armour {num}";
        string sign = v >= 0 ? "+" : "−";
        num = num.TrimStart('-');
        if (m.Kind == ModKind.More) return $"{num}% more {name}";
        if (m.Stat == Stat.Regen && m.Kind == ModKind.Flat) return $"{sign}{num} health a second";
        return $"{sign}{num}{(pct ? "%" : "")} {name}";
    }

    static bool Percent(string stat) => stat is "critChance" or "block" or "dodge" or "lifesteal" or "statusChance" or "executeThreshold" or "tenacity" || stat.StartsWith("resist.");

    static string Noun(string stat)
    {
        if (StatNames.TryGetValue(stat, out var n)) return n.ToLowerInvariant() is var l && l == "armour" ? "armour" : Style.Lower1(n);
        int dot = stat.IndexOf('.');
        if (dot > 0)
        {
            string what = stat[(dot + 1)..].Replace('_', ' ');
            return stat[..dot] switch
            {
                "vs" => $"damage to {Plural(what)}",
                "from" => $"less harm from {Plural(what)}",
                "resist" => $"{what} resistance",
                "damage" => $"{what} damage",
                _ => $"{stat[..dot]} {what}",
            };
        }
        return stat switch
        {
            "lightRadius" => "light", "healing" => "healing", "block" => "block", "pierce" => "pierce", "critDamage" => "critical damage", "dodge" => "dodge",
            "dashCharges" => "dashes", "pickupRadius" => "reach for what falls", "goldGain" => "gold found", "xpGain" => "experience", "luck" => "luck",
            _ => stat,
        };
        static string Plural(string w) => w.EndsWith("s") || w == "undead" ? w : w.EndsWith("f") ? w[..^1] + "ves" : w + "s";
    }

    /// <summary>Everything a thing is, on one card (UI_RESEARCH 8: ordered and ruled). Its name in its
    /// tier's colour over its kind, level and make; then what it does, a line each, with what wearing
    /// it would change set at each line's end when compared; then its power, its set, its heat and
    /// seams, what the world reads in it, its lore; then what it is worth and the keys for it, last.
    /// worn: the quieter card of the piece now worn, beside a comparison.</summary>
    public static PanelContainer Card(ItemInstance it, CharacterData? ch, bool compare, Control? actions = null, int width = 330, bool worn = false,
        Control? prompts = null, int? price = null, bool dear = false)
    {
        var def = Items.Get(it.Def);
        var tier = Drops.TierOf(it);
        var col = ColourOf(it);
        var card = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        card.AddThemeStyleboxOverride("panel", new CardBox { Tier = col, Worn = worn });
        card.CustomMinimumSize = new Vector2(width, 0);
        var v = Style.V(6);
        card.AddChild(v);
        if (worn) v.AddChild(Style.Label("WORN NOW", Style.UiHeavy, 12, Kit.Dim, false, HorizontalAlignment.Left, false));
        var name = Style.Label(Inventory.Name(it), Style.TextBold, worn ? 18 : 20, col, true);
        if (tier == LootTier.Set)
        {
            var mark = new TileMark(TileMark.Kind.Link, SetColour, 24) { SizeFlagsVertical = Control.SizeFlags.ShrinkCenter };
            v.AddChild(Style.H(8, mark, name));
        }
        else v.AddChild(name);
        var kind = Style.Label(KindLine(it), Style.Ui, 14, Kit.Dim, true);
        v.AddChild(kind);
        if (def.Weapon is { } iw && Weapons.All.TryGetValue(iw.Id, out var w))
            v.AddChild(Style.H(6, Glyphs.Icon(w.Art, 15, SchoolColors[w.School]), Style.Label($"{w.Name}  ·  rank {Inventory.WeaponRank(it)}  ·  {w.School.ToString().ToLowerInvariant()}", Style.UiBold, 14, SchoolColors[w.School])));

        // What wearing it would change, set beside the line that changes it; what no line explains
        // (what the worn piece gave and this does not) comes after.
        var diffs = new Dictionary<string, (double Before, double After)>();
        ItemInstance? against = null;
        if (compare && ch != null && Items.SlotFor(def) is EquipSlot slot && !Enum.GetValues<EquipSlot>().Any(s => ch.Equipment[s]?.Uid == it.Uid))
        {
            var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
            against = ch.Equipment[target];
            foreach (var (key, before, after) in Character.Compare(ch, it, target)) diffs[key] = (before, after);
        }
        var lines = Style.V(3);
        var uses = new Dictionary<string, int>();
        void Use(string k) => uses[k] = uses.GetValueOrDefault(k) + 1;
        foreach (var m in Drops.Implicit(def, it.Level)) Use(m.Stat);
        if (!def.Base) foreach (var m in def.Mods ?? new()) Use(m.Stat);
        foreach (var a in it.Affixes) if (Items.Affix(a.Id) is { } ad0) foreach (var k in ad0.Mods(a.Tier).Select(m => m.Stat).Distinct()) Use(k);
        Control Line(Control text, IEnumerable<string> keys)
        {
            text.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
            var row = Style.H(8, text);
            // (a number two lines both move is said once, after them, not beside the first)
            var key = keys.FirstOrDefault(k => diffs.ContainsKey(k) && uses.GetValueOrDefault(k) == 1);
            if (key != null)
            {
                var (b, a) = diffs[key];
                diffs.Remove(key);
                var (d, good) = DeltaNumber(key, b, a);
                var n = Kit.Num(d, 15, good ? Style.Good : Style.Bad);
                n.SizeFlagsVertical = Control.SizeFlags.ShrinkBegin;
                row.AddChild(n);
            }
            return row;
        }
        foreach (var m in Drops.Implicit(def, it.Level))
            lines.AddChild(Line(Style.Label(ModText(m, true), Style.Ui, 15, Kit.Ink2, true), new[] { m.Stat }));
        if (!def.Base)
            foreach (var m in def.Mods ?? new())
                lines.AddChild(Line(Style.Label(ModText(m), Style.Ui, 15, Kit.Ink2, true), new[] { m.Stat }));
        // Each affix with its grade (I to V: docs/CRAFTING_DESIGN.md 5.1); coals and worn skills have none.
        foreach (var a in it.Affixes)
        {
            if (Items.Affix(a.Id) is not { } ad || ad.Text(a.Tier) == "") continue;
            var keys = ad.Mods(a.Tier).Select(m => m.Stat).ToList();
            bool bright = a.Tier >= Crafting.Bright && ad.Kindled == null && ad.Grants == null && !ad.Slurry;
            if (ad.Slurry)
            {
                // The slurry's power, past the seams: its gift in green, its price after it in red.
                var parts = ad.Text(a.Tier).Split(';', 2);
                var row = Style.H(4, Glyphs.Icon("drop", 13, SlurryGreen), Style.Label(parts.Length > 1 ? $"{parts[0]};" : parts[0], Style.UiBold, 15, SlurryGreen));
                if (parts.Length > 1) row.AddChild(Style.Label(parts[1].Trim(), Style.UiBold, 15, Style.Bad));
                lines.AddChild(row);
                continue;
            }
            var text = Style.Label(ad.Text(a.Tier), Style.UiBold, 15, ad.Kindled != null ? Style.EmberHi : ad.Mark ? MarkInk : bright ? BrightGrade : Kit.Ink, true);
            if (ad.Kindled != null || ad.Grants != null) { lines.AddChild(Line(text, keys)); continue; }
            // The bright grade reads as a light, not as one more numeral.
            var grade = Style.Label(Crafting.Grade(a.Tier), Style.Display, bright ? 14 : 12, bright ? BrightGrade : Kit.Dim);
            if (bright) { grade.AddThemeConstantOverride("outline_size", 4); grade.AddThemeColorOverride("font_outline_color", SlurryGreen with { A = 0.45f }); }
            grade.CustomMinimumSize = new Vector2(22, 0);
            var g = Style.H(4, grade, text);
            text.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
            lines.AddChild(Line(g, keys));
        }
        if (diffs.Count > 0 && lines.GetChildCount() > 0 || lines.GetChildCount() > 0)
        {
            v.AddChild(Kit.RuleH());
            v.AddChild(lines);
        }
        if (diffs.Count > 0)
        {
            // What is lost from what is worn now: no line of this card says it.
            var lost = Style.V(2, Style.Label(against != null ? $"In place of {Inventory.Name(against)}" : "Wearing it", Style.TextItalic, 14, Kit.Dim, true));
            foreach (var (key, (b, a)) in diffs)
            {
                var (text, good) = Delta(key, b, a);
                lost.AddChild(Style.Label(text, Style.UiBold, 15, good ? Style.Good : Style.Bad, true));
            }
            v.AddChild(lost);
        }

        // What it does that no number says: a Legendary's power, a draught's use, a thing's purpose.
        if (def.Description != "")
        {
            bool power = tier is LootTier.Legendary or LootTier.Storied;
            v.AddChild(Style.Label(def.Description, power ? Style.TextBold : Style.Text, 15, power ? col.Lightened(0.35f) : Kit.Ink2, true));
        }
        if (tier == LootTier.Set && Drops.SetOf(def) is { } set)
        {
            int wornN = ch != null ? Drops.SetsWorn(ch).GetValueOrDefault(set.Id) : 0;
            var sv = Style.V(2, Style.H(8, Style.Label(set.Name.ToUpperInvariant(), Style.UiHeavy, 13, SetColour, false, HorizontalAlignment.Left, false),
                Style.Label($"{wornN} of {set.Pieces.Count} worn", Style.Ui, 14, Kit.Dim, false, HorizontalAlignment.Left, false)));
            foreach (var bonus in set.Bonuses)
            {
                bool lit = wornN >= bonus.Worn;
                sv.AddChild(Style.H(8, Style.Label($"{bonus.Worn}", Style.UiHeavy, 14, lit ? SetColour : Kit.Faint, false, HorizontalAlignment.Right, false),
                    Style.Label(bonus.Text, Style.Ui, 14, lit ? Kit.Ink : Kit.Faint, true)));
            }
            v.AddChild(Kit.RuleH());
            v.AddChild(sv);
        }
        if (it.Heat != null && Crafting.OpenSeams(it) is int open && open > 0)
            v.AddChild(Style.Label(open == 1 ? "An open seam: something can be worked into it" : $"{open} open seams: things can be worked into it", Style.TextItalic, 14, Kit.Dim, true));
        // (A steeped piece's veins say it is set, below; not twice.)
        bool slurried = Crafting.Slurried(it);
        if (it.Heat is int heat && !(heat == 0 && slurried))
            v.AddChild(Style.Label(heat > 0 ? $"Heat {heat} of {it.HeatFull ?? heat}: it can still be worked" : "Set: nothing more can be worked into it", Style.UiBold, 14, heat > 0 ? Style.Ember : Kit.Dim));
        if (def.Downside != null) v.AddChild(Style.Label(def.Downside, Style.UiBold, 14, Style.Bad, true));
        foreach (var t in (def.Tags ?? new()).Concat(it.Marks ?? new()).Distinct())
            if (TagLines.TryGetValue(t, out var tl)) v.AddChild(Style.H(6, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(tl, Style.TextItalic, 14, Style.GoldHi, true)));
        if (def.Lore != null) v.AddChild(Style.Label(def.Lore, Style.TextItalic, 14, Kit.Dim, true));
        if (it.History is { Count: > 0 } h) v.AddChild(Style.V(1, h.Select(x => (Control)Style.Label(x, Style.TextItalic, 14, Kit.Faint, true)).ToArray()));

        // Last: what it is worth (or costs here) and the keys for it.
        var foot = Style.H(12);
        int worth = price ?? (int)Math.Round(def.Value * Math.Max(1, it.Qty));
        var pc = dear ? Style.Bad : Style.GoldHi;
        foot.AddChild(Style.H(4, Glyphs.Icon("coin", 14, pc), Style.Label(price != null ? $"{worth}" : $"{worth}", Style.UiBold, 14, pc)));
        if (it.Qty > 1) foot.AddChild(Style.Label($"×{it.Qty}", Style.UiBold, 14, Kit.Dim));
        if (dear && ch != null) foot.AddChild(Style.Label($"{worth - (int)Math.Floor(ch.Gold)} more than you have", Style.Ui, 14, Style.Bad));
        if (!worn)
        {
            v.AddChild(Kit.RuleH());
            v.AddChild(foot);
        }
        if (prompts != null && !worn) v.AddChild(prompts);
        if (actions != null) v.AddChild(actions);
        return card;
    }
}

/// <summary>A card's ground: the tooltip art when painted, a raised dark plate until then, with a
/// strip of the thing's tier along its top edge in either case (the art cannot know the tier).</summary>
public partial class CardBox : StyleBox
{
    public Color Tier = Colors.White;
    public bool Worn;

    public CardBox()
    {
        ContentMarginLeft = ContentMarginRight = 16;
        ContentMarginTop = 16;
        ContentMarginBottom = 14;
    }

    public override void _Draw(Rid ci, Rect2 r)
    {
        // The shadow it casts on the world, so it reads as lifted off what it is over.
        RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position + new Vector2(6, 8), r.Size), new Color(0, 0, 0, 0.4f));
        // (the worn card is told apart by its quieter strip and its words, not by another frame)
        if (UiArt.Frames.TryGetValue("tooltip", out var s) && UiArt.Tex(s.File) is { } tex)
            UiArt.DrawSlice(ci, r, s, tex, s.Ground != null ? UiArt.Tex(s.Ground) : null);
        else
        {
            RenderingServer.CanvasItemAddRect(ci, r, Worn ? new Color("#1d1b1f") : new Color("#221f24"));
            var edge = Worn ? new Color("#3e3a40") : new Color("#4a464c");
            RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position, new Vector2(r.Size.X, 1)), edge);
            RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position + new Vector2(0, r.Size.Y - 1), new Vector2(r.Size.X, 1)), edge);
            RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position, new Vector2(1, r.Size.Y)), edge);
            RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position + new Vector2(r.Size.X - 1, 0), new Vector2(1, r.Size.Y)), edge);
        }
        RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position + new Vector2(1, 1), new Vector2(r.Size.X - 2, Worn ? 2 : 3)), Tier with { A = Worn ? 0.55f : 1 });
    }
}

/// <summary>The small marks in a tile's corners and before a card's name: the up-arrow of an upgrade,
/// the anvil of a better make, a set's chain-link, the ember dot of something new. Painted marks
/// (icons/glyph/link_set_14.png and its 24 px kin, up.png, anvil.png) win where they exist.</summary>
public partial class TileMark : Control
{
    public enum Kind { Up, Anvil, Link, Dot }
    readonly Kind kind;
    readonly Color colour;
    readonly int size;

    public TileMark(Kind kind, Color colour, int size = 14)
    {
        this.kind = kind;
        this.colour = colour;
        this.size = size;
        MouseFilter = MouseFilterEnum.Ignore;
        CustomMinimumSize = new Vector2(kind == Kind.Dot ? 8 : size, size);
    }

    public override void _Draw()
    {
        string? art = kind switch { Kind.Link => $"link_set_{(size >= 20 ? 24 : 14)}", Kind.Up => "up", Kind.Anvil => "anvil", _ => null };
        if (art != null && UiArt.Icon("glyph", art) is { } t)
        {
            DrawTextureRect(t, new Rect2(Vector2.Zero, new Vector2(size, size)), false, colour);
            return;
        }
        float s = size;
        var shade = new Color(0, 0, 0, 0.7f);
        switch (kind)
        {
            case Kind.Dot:
                DrawCircle(new Vector2(4, 4), 4.5f, shade);
                DrawCircle(new Vector2(4, 4), 3.2f, colour);
                break;
            case Kind.Up:
                var tri = new[] { new Vector2(s / 2, 1), new Vector2(s - 1, s * 0.62f), new Vector2(s * 0.66f, s * 0.62f), new Vector2(s * 0.66f, s - 1), new Vector2(s * 0.34f, s - 1), new Vector2(s * 0.34f, s * 0.62f), new Vector2(1, s * 0.62f) };
                DrawColoredPolygon(tri.Select(p => p + new Vector2(0, 1)).ToArray(), shade);
                DrawColoredPolygon(tri, colour);
                break;
            case Kind.Anvil:
                // A smith's anvil in profile: the face, the waist, the foot.
                DrawRect(new Rect2(1, s * 0.25f, s - 2, s * 0.22f), colour);
                DrawColoredPolygon(new[] { new Vector2(1, s * 0.25f), new Vector2(-1, s * 0.12f), new Vector2(3, s * 0.25f) }, colour);
                DrawRect(new Rect2(s * 0.36f, s * 0.47f, s * 0.28f, s * 0.24f), colour);
                DrawRect(new Rect2(s * 0.2f, s * 0.71f, s * 0.6f, s * 0.18f), colour);
                break;
            case Kind.Link:
                // Two links of chain, the second through the first.
                DrawArc(new Vector2(s * 0.36f, s * 0.42f), s * 0.28f, 0, Mathf.Tau, 20, shade, 3.2f * s / 14, true);
                DrawArc(new Vector2(s * 0.64f, s * 0.6f), s * 0.28f, 0, Mathf.Tau, 20, shade, 3.2f * s / 14, true);
                DrawArc(new Vector2(s * 0.36f, s * 0.4f), s * 0.28f, 0, Mathf.Tau, 20, colour, 2 * s / 14, true);
                DrawArc(new Vector2(s * 0.64f, s * 0.58f), s * 0.28f, Mathf.Pi * 1.1f, Mathf.Pi * 2.9f, 20, colour, 2 * s / 14, true);
                break;
        }
    }
}
