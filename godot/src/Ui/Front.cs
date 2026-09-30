using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The title (the web game's screens/Title.tsx): a fire on the Low Ford
/// road, someone sitting by it, and the name of the game carved over the
/// dark. The menu is short on purpose. The first time, a word on who the
/// game is for.
/// </summary>
public partial class TitleScreen : Overlay
{
    public override string Kind => "title";
    public override bool Dismissable => false;
    readonly MenuList menu;
    string panel = "";
    bool left;

    public TitleScreen(Game g) : base(g) { menu = new MenuList(Refresh, 24); }

    static readonly Dictionary<string, string> ZoneNames = new() { ["lowford"] = "The Low Ford Road", ["waystation"] = "The Waystation", ["verge"] = "Thornhollow Verge" };

    static string Ago(long savedAt)
    {
        double s = (DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() - savedAt) / 1000.0;
        if (s < 90) return "just now";
        if (s < 3600) return $"{Math.Round(s / 60)} minutes ago";
        if (s < 86400) return $"{Math.Round(s / 3600)} hours ago";
        return $"{Math.Round(s / 86400)} days ago";
    }

    protected override void Build()
    {
        if (!Settings.Current.Mature) { Mature(); return; }
        // A shade over the left of the picture, where the words are.
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D { Gradient = new Gradient { Offsets = new[] { 0f, 0.34f, 0.6f }, Colors = new[] { new Color(0.016f, 0.012f, 0.024f, 0.86f), new Color(0.016f, 0.012f, 0.024f, 0.55f), new Color(0.016f, 0.012f, 0.024f, 0) } }, Width = 256, Height = 4 },
            StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        Style.Fill(shade);
        AddChild(shade);
        var brand = Style.V(2);
        brand.Position = new Vector2(134, 140);
        brand.AddChild(Style.Label("A tale of the Ember Watch", Style.TextItalic, 19, new Color("#c8a878")));
        var b1 = Style.Label("SURVIVOR", Style.Display, 92, new Color("#f0c878"));
        b1.AddThemeConstantOverride("outline_size", 0);
        brand.AddChild(b1);
        brand.AddChild(Style.Label("U N C H A I N E D", Style.Display, 54, new Color("#d8a050")));
        var rule = new ColorRect { Color = Style.Gold, CustomMinimumSize = new Vector2(420, 1), MouseFilter = MouseFilterEnum.Ignore };
        brand.AddChild(Style.Gap(12));
        brand.AddChild(rule);
        brand.AddChild(Style.Gap(8));
        brand.AddChild(Style.Label("The run ends. The story doesn't.", Style.TextItalic, 23, new Color("#e8dcc6")));
        AddChild(brand);

        var slots = G.Saves.Slots();
        var latest = slots.OrderByDescending(s => s.SavedAt).FirstOrDefault();
        menu.Items.Clear();
        if (latest != null)
            menu.Add("Continue", () => G.Continue(latest.Slot), $"{latest.Name} · {Callings.Archetypes.GetValueOrDefault(latest.Archetype)?.Name} {latest.Level} · Day {latest.Day}", true);
        menu.Add("New Journey", G.NewJourney, null, latest == null);
        if (slots.Count > 0) menu.Add("Journeys", () => Panel("load"));
        menu.Add("Settings", () => Panel("settings"));
        menu.Add("Controls", () => Panel("controls"));
        menu.Add("Credits", () => Panel("credits"));
        menu.Add("Quit", G.QuitGame);
        var list = menu.Build();
        list.Position = new Vector2(134, 560);
        AddChild(list);

        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(20));
            box.Position = new Vector2(540, panel == "controls" ? 140 : 540);
            box.CustomMinimumSize = new Vector2(panel == "controls" ? 720 : 520, 0);
            var v = Style.V(8, Style.Cap(panel switch { "load" => "Journeys", "settings" => "Settings", "controls" => "Controls", _ => "Credits" }, 16));
            switch (panel)
            {
                case "load":
                    foreach (var s in slots)
                    {
                        var arch = Callings.Archetypes.GetValueOrDefault(s.Archetype);
                        var row = Style.H(12);
                        row.AddChild(Glyphs.Icon(s.Archetype switch { "warden" => "shield", "reaver" => "axe", "arcanist" => "staff", _ => "bow" }, 26, Style.Gold));
                        var words = Style.V(0, Style.Label(s.Name, Style.Display, 18, s.Alive ? new Color("#f2e6cc") : new Color("#a08a80")),
                            Style.Label($"{arch?.Name} {s.Level} · Day {s.Day} · {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.UiBold, 13, Style.InkDim),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.TextItalic, 13, Style.InkFaint));
                        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                        row.AddChild(words);
                        int slot = s.Slot;
                        row.AddChild(Style.Button("Resume", () => G.Continue(slot), true, true));
                        row.AddChild(Style.Button("Forget", () => { G.Saves.Remove(slot); Refresh(); }, false, true));
                        v.AddChild(row);
                    }
                    break;
                case "settings": v.AddChild(SettingsPanel.Build(G, Refresh)); break;
                case "controls": v.AddChild(new ControlsPanel()); break;
                default:
                    foreach (var line in Credits) v.AddChild(Style.Label(line, Style.Text, 15, new Color("#ddd0b8"), true));
                    break;
            }
            box.AddChild(v);
            AddChild(box);
        }
        var foot = Style.Label("BETA  ·  THE FIRST CHAPTER", Style.UiBold, 12, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
    }

    static readonly string[] Credits =
    {
        "People and their clothes, hair and movement: Quaternius (Universal Base Characters, Modular Character Outfits, Universal Animation Libraries 1 and 2; CC0).",
        "A woman survivor's body: Genshin Style Anime Female Base Mesh by donizaki (Sketchfab, CC BY 4.0).",
        "Weapons, from Sketchfab (CC BY 4.0): Chevalier Sword by rubenve; Viking Sword by Michael Makivic; medieval sword by LowSeb; Zweihander by Siesta; Medieval Mace by Kama Modeling; Viking battle axe by Mikhail Antonov; Snake Axe by Ashley Jay Thornton; Mage Staff by RMBehan; Medieval Crossbow by iedalton; Medieval Shield by Artem Mykhailov; Silver Bladed weapons by Peter Nox.",
        "Houses, walls and props: Quaternius (Medieval Village MegaKit, Fantasy Props MegaKit, Stylized Nature MegaKit; CC0).",
        "The ground: Poly Haven (photoscanned materials; CC0).",
        "Creatures, from Sketchfab (CC BY 4.0): Animated Wolf Scene by Roo; Animated Realistic Boar by AnimalMesh 3D; Goblin Ghoul by Rodrigo Bento (the lamplings).",
        "Effects and sounds: Kenney (Particle Pack, Impact Sounds, RPG Audio, Interface Sounds; CC0). Field recordings from OpenGameArt (CC0): thimras, PagDev, Ted Kerr, vishwajai.",
        "World, lore and combat roots: The Ember Watch.",
        "Typefaces: Cinzel, Alegreya, Alegreya Sans (OFL).",
        "Built with Godot.",
    };

    void Panel(string p) { panel = panel == p ? "" : p; Refresh(); }

    void Mature()
    {
        AddChild(Style.Scrim(null, 0.75f));
        var card = Style.Centered(Style.Panel(Style.Plate(26)), new Vector2(560, 300));
        AddChild(card);
        var v = Style.V(10, Style.Cap("For adults", 18));
        if (left) v.AddChild(Style.Label("Another time, then. The fire will still be burning.", Style.Text, 17, Style.Ink, true));
        else
        {
            v.AddChild(Style.Label("Survivor Unchained is made for adults. It has graphic violence and gore, strong language, revealing clothes and sexual themes. Nothing sexual is shown on screen.", Style.Text, 17, Style.Ink, true));
            v.AddChild(Style.Label("Gore can be reduced or turned off in Settings.", Style.TextItalic, 15, Style.InkDim, true));
            v.AddChild(Style.H(10, Style.Button("I am 18 or over", Agree, true), Style.Button("Leave", () => { left = true; Refresh(); })));
        }
        card.AddChild(v);
    }

    void Agree()
    {
        Settings.Current.Mature = true;
        Settings.Current.Save();
        Refresh();
    }

    public override bool Key(Act a)
    {
        if (!Settings.Current.Mature)
        {
            if (a == Act.Confirm && !left) { Agree(); return true; }
            return true;
        }
        if (a == Act.Cancel && panel != "") { panel = ""; Refresh(); return true; }
        return menu.Key(a);
    }
}

/// <summary>What is being made at the fire (the web game's CreationDraft).</summary>
public sealed class CreationDraft
{
    public int Step;
    public string Name = "", Archetype = "warden", WeaponItem = "worn_oathblade", Ability = "shield_bash", StartBoon = "hunters_mark", Background = "hunter";
    public string Palette = "steel", Model = "knight", Cloak = "calling", Skin = "fair", Hair = "as_is", HairStyle = "Hair_SimpleParted";
    public bool Headgear = true, Beard = true;
    public Sex Sex = Sex.Male;
    public double Figure = 1.0;

    public CreationChoice Choice() => new()
    {
        Name = Name.Trim(), Archetype = Archetype, Background = Background, Palette = Palette, Model = Model, WeaponItem = WeaponItem, Ability = Ability, StartBoon = StartBoon,
        Headgear = Headgear, Cloak = Cloak, Skin = Skin, Hair = Hair, Sex = Sex, HairStyle = HairStyle, Beard = Beard, Figure = Figure,
    };

    /// <summary>What the figure by the fire looks like: changes when this does.</summary>
    public string LookKey => $"{Archetype}|{Model}|{WeaponItem}|{Palette}|{Headgear}|{Cloak}|{Skin}|{Hair}|{Sex}|{HairStyle}|{Beard}|{Figure}";
}

/// <summary>
/// Making the survivor, by the fire (the web game's screens/Create.tsx).
/// Four steps, each a question the world will ask again later: Calling (how
/// do you fight?), Arms (with what, and what do your hands do?), Origin
/// (where are you from?), Name (who are you?). The figure by the fire
/// changes as you choose; the panel on the right says what each choice means.
/// </summary>
public partial class CreateScreen : Overlay
{
    public override string Kind => "create";
    public override bool Dismissable => false;
    readonly CreationDraft d;
    static readonly string[] Steps = { "Calling", "Arms", "Origin", "Name" };
    static readonly string[] Numerals = { "I", "II", "III", "IV" };
    static readonly Dictionary<string, string> ClassGlyph = new() { ["warden"] = "shield", ["reaver"] = "axe", ["arcanist"] = "staff", ["stalker"] = "bow" };
    static readonly Dictionary<string, string> BgGlyph = new() { ["hunter"] = "claw", ["scholar"] = "book", ["outcast"] = "mask", ["devout"] = "sun" };
    static readonly string[] Names = { "Ashe", "Brannagh", "Corwen", "Dace", "Edda", "Fen", "Garrow", "Hollis", "Isolde", "Jessamy", "Kell", "Lorne", "Maren", "Nolly", "Orrin", "Pim", "Quill", "Rhosyn", "Sabre", "Tamsin", "Ulla", "Voss", "Wren", "Yarrow" };
    static readonly Dictionary<string, string> HairNames = new() { ["Hair_SimpleParted"] = "Parted", ["Hair_Buzzed"] = "Cropped", ["Hair_Long"] = "Long", ["Hair_Buns"] = "Buns", ["Hair_BuzzedFemale"] = "Cropped", ["none"] = "Shorn" };
    LineEdit? nameBox;

    public CreateScreen(Game g, CreationDraft draft) : base(g) { d = draft; }

    void Set(Action change) { change(); G.DressFigure(d); Refresh(); }

    void ChooseArchetype(string id)
    {
        var a = Callings.Archetype(id);
        d.Archetype = id; d.WeaponItem = a.Weapons[0]; d.Ability = a.Abilities[0]; d.Palette = a.Palettes[0].Id; d.Model = a.Model; d.Headgear = true;
    }

    bool CanBegin => d.Name.Trim().Length > 0;

    void Begin()
    {
        if (!CanBegin) { Set(() => d.Step = 3); return; }
        G.BeginJourney(d.Choice());
    }

    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        var left = Style.Panel(Style.Plate(20));
        left.Position = new Vector2(40, 40);
        left.Size = new Vector2(520, 1000);
        AddChild(left);
        var col = Style.V(10);
        left.AddChild(col);
        col.AddChild(Style.Label("By the fire on the Low Ford road", Style.TextItalic, 16, new Color("#c8a878")));
        col.AddChild(Style.Cap("Who sits here?", 22));
        var steps = Style.H(4);
        for (int i = 0; i < Steps.Length; i++)
        {
            int s = i;
            steps.AddChild(Style.Button($"{Numerals[i]}  {Steps[i]}", () => Set(() => d.Step = s), d.Step == i, true));
        }
        col.AddChild(steps);
        col.AddChild(Style.Rule());
        var body = d.Step switch { 0 => Calling(), 1 => Arms(a), 2 => Origin(), _ => NameLook(a) };
        var scroll = Style.Scroll(body);
        col.AddChild(scroll);
        var foot = Style.H(10, Style.Button(d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); }));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(d.Step < 3 ? Style.Button($"Next: {Steps[d.Step + 1]}", () => Set(() => d.Step++), true) : Style.Button("Begin the journey", Begin, true));
        col.AddChild(foot);

        var right = Style.Panel(Style.Box(new Color(0.05f, 0.04f, 0.06f, 0.82f), Style.Line, 1, 6, 22));
        right.Position = new Vector2(1400, 120);
        right.Size = new Vector2(480, 0);
        right.CustomMinimumSize = new Vector2(480, 0);
        right.AddChild(d.Step switch { 0 => CallingDetail(a), 1 => ArmsDetail(), 2 => OriginDetail(), _ => Summary(a) });
        AddChild(right);

        var cap = Style.V(0, Style.Label(d.Name.Trim() == "" ? "Nameless" : d.Name.Trim(), Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center),
            Style.Label($"{Callings.Background(d.Background).Name} {a.Name}", Style.TextItalic, 17, Style.Ink, false, HorizontalAlignment.Center));
        cap.Position = new Vector2(760, 960);
        cap.Size = new Vector2(560, 80);
        AddChild(cap);
    }

    static Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null)
    {
        var b = Style.Button("", act);
        b.CustomMinimumSize = new Vector2(440, 66);
        if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4));
        var row = Style.H(12, Glyphs.Icon(glyph, 28, on ? Style.EmberHi : Style.Gold));
        var words = Style.V(0, Style.Label(name, Style.Display, 17, on ? Colors.White : Style.GoldHi), Style.Label(tag, Style.Ui, 13, tagColor ?? Style.InkDim, true));
        words.CustomMinimumSize = new Vector2(360, 0);
        row.AddChild(words);
        row.Position = new Vector2(12, 8);
        b.AddChild(row);
        return b;
    }

    Control Calling()
    {
        var v = Style.V(6);
        foreach (var (id, a) in Callings.Archetypes)
            v.AddChild(Choice(ClassGlyph.GetValueOrDefault(id, "sword"), a.Name, a.Tagline, d.Archetype == id, () => Set(() => ChooseArchetype(id))));
        return v;
    }

    Control Arms(Archetype a)
    {
        var v = Style.V(6, Style.SubLabel("Weapon"));
        foreach (var id in a.Weapons)
        {
            var it = Items.Get(id);
            var w = it.Weapon != null ? Weapons.All.GetValueOrDefault(it.Weapon.Id) : null;
            v.AddChild(Choice(it.Icon, it.Name, w != null ? $"{w.Name} · {w.School.ToString().ToLowerInvariant()}" : "", d.WeaponItem == id, () => Set(() => d.WeaponItem = id),
                w != null ? ItemViews.SchoolColors[w.School] : null));
        }
        v.AddChild(Style.SubLabel("Ability"));
        foreach (var id in a.Abilities)
        {
            var ab = Abilities.ById(id);
            v.AddChild(Choice(ab.Icon, ab.Name, $"{ab.Cooldown} s{(ab.Interrupts ? " · breaks channels" : "")}", d.Ability == id, () => Set(() => d.Ability = id)));
        }
        v.AddChild(Style.H(8, Style.SubLabel("Starting blessing"), Style.Label("yours at the start of every expedition", Style.TextItalic, 13, Style.InkDim)));
        var grid = new GridContainer { Columns = 3 };
        grid.AddThemeConstantOverride("h_separation", 6);
        grid.AddThemeConstantOverride("v_separation", 6);
        foreach (var id in Boons.StartBlessings)
        {
            var bd = Boons.Find(id)!;
            var b = Style.Segment(bd.Name, d.StartBoon == id, () => Set(() => d.StartBoon = id));
            b.TooltipText = bd.Text;
            grid.AddChild(b);
        }
        v.AddChild(grid);
        return v;
    }

    Control Origin()
    {
        var v = Style.V(6);
        foreach (var (id, bg) in Callings.Backgrounds)
            v.AddChild(Choice(BgGlyph.GetValueOrDefault(id, "map"), bg.Name, bg.Summary, d.Background == id, () => Set(() => d.Background = id)));
        return v;
    }

    Control NameLook(Archetype a)
    {
        var v = Style.V(8, Style.SubLabel("Name"));
        nameBox = new LineEdit { Text = d.Name, PlaceholderText = "Your name", MaxLength = 18, CustomMinimumSize = new Vector2(360, 38), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        Style.Font(nameBox, Style.Display, 20, Style.GoldHi, false);
        nameBox.AddThemeStyleboxOverride("normal", Style.Box(new Color("#0d0c10"), Style.GoldDim, 1, 4, 10));
        nameBox.AddThemeStyleboxOverride("focus", Style.Box(new Color("#0d0c10"), Style.LineHi, 1, 4, 10));
        nameBox.TextChanged += t =>
        {
            var clean = new string(t.Where(c => char.IsLetter(c) || c is '\'' or ' ' or '-').ToArray());
            d.Name = clean;
            if (clean != t) { nameBox.Text = clean; nameBox.CaretColumn = clean.Length; }
        };
        nameBox.TextSubmitted += _ => Begin();
        v.AddChild(Style.H(8, nameBox, Style.Button("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), false, true)));
        Callable.From(() => nameBox?.GrabFocus()).CallDeferred();

        v.AddChild(Style.SubLabel("Body"));
        var body = Style.H(6);
        foreach (var sx in new[] { Sex.Male, Sex.Female })
            body.AddChild(Style.Segment(sx == Sex.Male ? "Man" : "Woman", d.Sex == sx, () => Set(() =>
            {
                d.Sex = sx;
                var styles = Lore.HairStyles(sx);
                if (!styles.Contains(d.HairStyle) && d.HairStyle != "none") d.HairStyle = styles[0];
            })));
        if (d.Sex == Sex.Male) body.AddChild(Style.Segment(d.Beard ? "Bearded" : "Clean-shaven", d.Beard, () => Set(() => d.Beard = !d.Beard)));
        v.AddChild(body);
        if (d.Sex == Sex.Female)
        {
            var slider = new HSlider { MinValue = 0, MaxValue = 1.5, Step = 0.1, Value = d.Figure, CustomMinimumSize = new Vector2(220, 24) };
            slider.DragEnded += _ => Set(() => d.Figure = slider.Value);
            string Word(double f) => f < 0.45 ? "Slender" : f < 0.95 ? "Shapely" : f < 1.25 ? "Full" : "Buxom";
            v.AddChild(Style.H(10, Style.Label("Figure", Style.UiBold, 14, Style.Ink), slider, Style.Label(Word(d.Figure), Style.Ui, 14, Style.InkDim)));
        }
        // A woman goes bare in a body of her own (Loadouts.HerBody): no
        // clothes to colour, no hood over her hair.
        bool her = d.Sex == Sex.Female;
        if (!her)
        {
            v.AddChild(Style.SubLabel("Colours"));
            var pal = new GridContainer { Columns = 2 };
            foreach (var p in a.Palettes) pal.AddChild(Style.Segment(p.Name, d.Palette == p.Id, () => Set(() => d.Palette = p.Id)));
            v.AddChild(pal);
        }
        v.AddChild(Style.SubLabel("Skin"));
        v.AddChild(Swatches(Lore.Skins, d.Skin, id => d.Skin = id, "#f6c4a0"));
        bool hairHidden = !her && (d.Archetype == "stalker" ? d.Model == "rogue_hooded" : d.Headgear && d.Archetype != "reaver");
        v.AddChild(Style.H(8, Style.SubLabel("Hair"), hairHidden ? Style.Label("under the hood", Style.TextItalic, 13, Style.InkDim) : new Control()));
        var cuts = Style.H(4);
        foreach (var h in Lore.HairStyles(d.Sex).Append("none")) cuts.AddChild(Style.Segment(HairNames.GetValueOrDefault(h, h), d.HairStyle == h, () => Set(() => d.HairStyle = h)));
        if (hairHidden) cuts.Modulate = new Color(1, 1, 1, 0.5f);
        v.AddChild(cuts);
        v.AddChild(Swatches(Lore.Hairs, d.Hair, id => d.Hair = id, "#6a5a48"));
        if (d.Archetype != "reaver" && !her)
        {
            v.AddChild(Style.SubLabel("Hood"));
            if (a.AltModel != null) v.AddChild(Style.Button(d.Model == a.Model ? "Hood up" : "Hood down", () => Set(() => d.Model = d.Model == a.Model ? a.AltModel! : a.Model), false, true));
            if (d.Archetype != "stalker") v.AddChild(Style.Button(d.Headgear ? "Hood up" : "Hood down", () => Set(() => d.Headgear = !d.Headgear), false, true));
        }
        v.AddChild(Style.SubLabel("Cloak"));
        v.AddChild(Swatches(Lore.CloakDyes, d.Cloak, id => d.Cloak = id, "#3a2a20"));
        return v;
    }

    Control Swatches(List<LookChoice> list, string now, Action<string> set, string fallback)
    {
        var h = Style.H(5);
        foreach (var c in list)
        {
            var id = c.Id;
            var b = new Button { CustomMinimumSize = new Vector2(30, 30), FocusMode = FocusModeEnum.None, TooltipText = c.Name };
            var col = string.IsNullOrEmpty(c.Color) ? new Color(fallback) : new Color(c.Color);
            b.AddThemeStyleboxOverride("normal", Style.Box(col, now == id ? Style.GoldHi : new Color(0, 0, 0, 0.8f), now == id ? 3 : 1, 15, 0));
            b.AddThemeStyleboxOverride("hover", Style.Box(col.Lightened(0.1f), Style.LineHi, 2, 15, 0));
            b.AddThemeStyleboxOverride("pressed", Style.Box(col, Style.GoldHi, 3, 15, 0));
            b.Pressed += () => Set(() => set(id));
            h.AddChild(b);
        }
        h.AddChild(Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.Ui, 14, Style.InkDim));
        return h;
    }

    static Label Line(string bold, string text) => Style.Label($"{bold}   {text}", Style.Text, 15, Style.Ink, true);

    static Control Bar(string label, double v, double max) => Style.H(10, Style.Label(label, Style.UiBold, 14, Style.InkDim), SheetScreen.Bar(v / max, "", Style.Gold, 240));

    Control CallingDetail(Archetype a) => Style.V(8,
        Style.Cap(a.Name, 24), Style.Label(a.Tagline, Style.TextItalic, 17, new Color("#c8a878"), true), Style.Label(a.Description, Style.Text, 16, Style.Ink, true), Style.Rule(),
        Bar("Health  ", a.Base.MaxHealth, 200), Bar("Armour  ", a.Base.Armor + 1, 7), Bar("Speed    ", a.Base.MoveSpeed - 4, 2), Bar("Precision", a.Base.CritChance, 0.12), Style.Rule(),
        Line("Weapons", string.Join(" · ", a.Weapons.Select(w => Items.Get(w).Name))), Line("Abilities", string.Join(" · ", a.Abilities.Select(x => Abilities.ById(x).Name))));

    Control ArmsDetail()
    {
        var it = Items.Get(d.WeaponItem);
        var w = it.Weapon != null ? Weapons.All.GetValueOrDefault(it.Weapon.Id) : null;
        var ab = Abilities.ById(d.Ability);
        var v = Style.V(8, Style.H(12, ItemPhotos.Icon(it.Icon, 72, Style.GoldHi), Style.V(2, Style.Cap(it.Name, 20),
            w != null ? Style.Label($"{w.Name} · {w.School.ToString().ToLowerInvariant()}", Style.UiBold, 15, ItemViews.SchoolColors[w.School]) : new Control())));
        v.AddChild(Style.Label(it.Description, Style.Text, 16, Style.Ink, true));
        if (it.Lore != null) v.AddChild(Style.Label(it.Lore, Style.TextItalic, 15, Style.InkDim, true));
        if (w != null && w.Evolutions.Length > 0)
            v.AddChild(Line("At rank 8", string.Join(", or ", w.Evolutions.Select(e => $"{e.Name} (with {string.Join(" or ", e.Catalysts.Select(c => Boons.Find(c)?.Name ?? c))})"))));
        v.AddChild(Style.Rule());
        v.AddChild(Style.H(10, Glyphs.Icon(ab.Icon, 30, new Color("#ffe2b0")), Style.V(2, Style.H(6, Style.Label(ab.Name, Style.UiBold, 16, Style.GoldHi), Style.Key(G.Key(Act.Ability))),
            Style.Label(ab.Description, Style.Text, 14, Style.Ink, true))));
        v.AddChild(Style.Rule());
        var boon = Boons.Find(d.StartBoon)!;
        v.AddChild(Line(boon.Name, boon.Text));
        return v;
    }

    Control OriginDetail()
    {
        var bg = Callings.Background(d.Background);
        var v = Style.V(8, Style.Cap(bg.Name, 24), Style.Label(bg.Summary, Style.TextItalic, 17, new Color("#c8a878"), true), Style.Label(bg.Story, Style.TextItalic, 15, Style.Ink, true), Style.Rule(),
            Line("You know", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))));
        foreach (var i in bg.Items)
        {
            var it = Items.Get(i);
            v.AddChild(Style.H(10, ItemPhotos.Icon(it.Icon, 40, Style.RarityOf(it.Rarity)), Style.V(0, Style.Label(it.Name, Style.UiBold, 15, Style.RarityOf(it.Rarity)), Style.Label(it.Description, Style.Ui, 13, Style.InkDim, true))));
        }
        v.AddChild(Style.Rule());
        v.AddChild(Style.SubLabel("What it opens"));
        foreach (var o in bg.Opens) v.AddChild(Style.Label($"• {o}", Style.Text, 15, Style.Ink, true));
        return v;
    }

    Control Summary(Archetype a)
    {
        var bg = Callings.Background(d.Background);
        return Style.V(8, Style.Cap(d.Name.Trim() == "" ? "Nameless" : d.Name.Trim(), 24), Style.Label($"{bg.Name} {a.Name}", Style.TextItalic, 17, new Color("#c8a878")),
            Style.Label(bg.Story, Style.TextItalic, 15, Style.Ink, true), Style.Rule(),
            Line("Carries", Items.Get(d.WeaponItem).Name + string.Concat(bg.Items.Select(i => $", {Items.Get(i).Name}"))),
            Line("Hands", Abilities.ById(d.Ability).Name), Line("Blessing", Boons.Find(d.StartBoon)!.Name),
            Line("Knows", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))), Style.Rule(),
            Style.Label("Night is falling on the Low Ford road. The fire is low. What you do from here, the world will remember.", Style.TextItalic, 15, Style.InkDim, true));
    }

    public override bool Key(Act a)
    {
        if (nameBox != null && nameBox.HasFocus() && a is not (Act.Cancel or Act.Confirm)) return true;
        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(3, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }
        if (a == Act.Cancel) { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); return true; }
        if (a == Act.Confirm) { if (d.Step < 3) Set(() => d.Step++); else Begin(); return true; }
        return true;
    }
}
