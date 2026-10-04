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
        // The painted logo (title/logo.png) when there is one; else the name set in Cinzel.
        if (UiArt.Art("title/logo.png") is { } logo)
            brand.AddChild(new TextureRect { Texture = logo, CustomMinimumSize = logo.GetSize(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspect, MouseFilter = MouseFilterEnum.Ignore });
        else
        {
            var b1 = Style.Label("SURVIVOR", Style.Display, 92, new Color("#f0c878"));
            b1.AddThemeConstantOverride("outline_size", 0);
            brand.AddChild(b1);
            brand.AddChild(Style.Label("U N C H A I N E D", Style.Display, 54, new Color("#d8a050")));
        }
        // The house's rule under the name: gold running out from an ember stone at either end.
        brand.AddChild(Style.Gap(4));
        brand.AddChild(new Plaque("", 14, 182));
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
        Nav.Scope = null;

        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(20));
            box.Position = new Vector2(540, panel == "controls" ? 90 : panel == "credits" ? 300 : 500);
            box.CustomMinimumSize = new Vector2(panel == "controls" ? 820 : panel == "credits" ? 760 : 560, 0);
            Nav.Scope = box;
            var v = Style.V(10, new Plaque(panel switch { "load" => "Journeys", "settings" => "Settings", "controls" => "Controls", _ => "Credits" }, 26, 50));
            switch (panel)
            {
                case "load":
                    foreach (var s in slots)
                    {
                        var arch = Callings.Archetypes.GetValueOrDefault(s.Archetype);
                        var row = Style.H(12);
                        row.AddChild(Glyphs.Icon(s.Archetype switch { "warden" => "shield", "reaver" => "axe", "arcanist" => "staff", _ => "bow" }, 26, Style.Gold));
                        var words = Style.V(0, Style.Label(s.Name, Style.Display, 18, s.Alive ? new Color("#f2e6cc") : new Color("#a08a80")),
                            Style.Label($"{arch?.Name} {s.Level} · Day {s.Day} · {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.UiBold, Style.Caption, Style.InkDim),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.TextItalic, Style.Caption, Style.InkFaint));
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
                    foreach (var line in Credits) v.AddChild(Style.Label(line, Style.Text, Style.Small, new Color("#ddd0b8"), true));
                    break;
            }
            box.AddChild(v);
            AddChild(box);
        }
        var foot = Style.Label("BETA  ·  THE FIRST CHAPTER", Style.UiBold, Style.Badge, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
    }

    static readonly string[] Credits =
    {
        "People and their clothes, hair and movement: Quaternius (Universal Base Characters, Modular Character Outfits, Universal Animation Libraries 1 and 2; CC0).",
        "A woman survivor's body: a figure made for the game in ComfyUI, rigged from the Genshin Style Anime Female Base Mesh by donizaki (Sketchfab, CC BY 4.0).",
        "The heroine's movement: keyed for the game; her ways of standing from the 100STYLE dataset by Ian Mason et al. (CC BY 4.0), retargeted and re-keyed.",
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
        if (panel != "")
        {
            // Back closes the panel; inside it, focus moves over its rows.
            if (a is Act.Cancel or Act.Pause) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }
}

/// <summary>What is being made at the fire (the web game's CreationDraft).</summary>
public sealed class CreationDraft
{
    public int Step;
    public string Name = "", Archetype = "warden", WeaponItem = "worn_oathblade", Ability = "shield_bash", Background = "hunter";
    public string Palette = "steel", Model = "knight", Cloak = "calling", Skin = "fair", Hair = "as_is", HairStyle = "long";
    public bool Headgear = true, Beard = true;
    /// <summary>The survivor is the heroine, unless a man is chosen.</summary>
    public Sex Sex = Sex.Female;
    public double Figure = 1.0;
    /// <summary>Her eyes, the paint on her face, and her face: its sliders
    /// (her own face where none is moved) and the face it started from.</summary>
    public string Eyes = "moss", Paint = "none", FaceShape = "own";
    public Dictionary<string, double> Face = new();
    /// <summary>The look step's part (body, hair, face, paint) and the face's group of sliders.</summary>
    public int Section, FaceGroup;

    public CreationChoice Choice() => new()
    {
        Name = Name.Trim(), Archetype = Archetype, Background = Background, Palette = Palette, Model = Model, WeaponItem = WeaponItem, Ability = Ability,
        Headgear = Headgear, Cloak = Cloak, Skin = Skin, Hair = Hair, Sex = Sex, HairStyle = HairStyle, Beard = Beard, Figure = Figure,
        Face = Sex == Sex.Female ? new Dictionary<string, double>(Face) : null, Eyes = Sex == Sex.Female ? Eyes : null, Paint = Sex == Sex.Female ? Paint : null,
    };

    /// <summary>The figure by the fire is built again when this changes (who
    /// they are, what they wear and hold); a man's hair and skin are his clothes' kit.</summary>
    public string BodyKey => $"{Archetype}|{Model}|{WeaponItem}|{Palette}|{Headgear}|{Cloak}|{Sex}|{Figure}|{Beard}" + (Sex == Sex.Male ? $"|{Skin}|{Hair}|{HairStyle}" : "");

    /// <summary>What the figure looks like: changes when this does (her hair,
    /// skin, eyes, face and paint are changed on her where she stands).</summary>
    public string LookKey => $"{BodyKey}|{Skin}|{Hair}|{HairStyle}|{Eyes}|{Paint}|{string.Join(",", Face.OrderBy(f => f.Key).Select(f => $"{f.Key}={f.Value:0.###}"))}";

    /// <summary>A body chosen: her own hairstyle or his, kept if it is one of theirs.</summary>
    public void SetSex(Sex sx)
    {
        Sex = sx;
        if (sx == Sex.Female) HairStyle = Loadouts.HerHair(HairStyle);
        else if (!Lore.HairStyles(sx).Contains(HairStyle) && HairStyle != "none") HairStyle = Lore.HairStyles(sx)[0];
        Section = 0;
    }
}

/// <summary>
/// Making the survivor, by the fire (the web game's screens/Create.tsx).
/// Five steps, each a question the world will ask again later: Calling (how
/// do you fight?), Arms (with what, and what do your hands do?), Origin
/// (where are you from?), Look (what does she look like?), Name (who are
/// you?). The figure by the fire changes as you choose, and can be turned
/// (drag, or the right stick) and brought near (the wheel, or the right
/// stick) to her face; the panel on the right says what each choice means.
/// Enter or A on a choice takes it; on the one already taken, it moves on
/// (so A, A walks through); LB and RB turn the steps, LT and RT the look's parts.
/// </summary>
public partial class CreateScreen : Overlay
{
    public override string Kind => "create";
    public override bool Dismissable => false;
    readonly CreationDraft d;
    static readonly string[] Steps = { "Calling", "Arms", "Origin", "Look", "Name" };
    static readonly string[] Numerals = { "I", "II", "III", "IV", "V" };
    const int LookStep = 3, NameStep = 4;
    static readonly Dictionary<string, string> ClassGlyph = new() { ["warden"] = "shield", ["reaver"] = "axe", ["arcanist"] = "staff", ["stalker"] = "bow" };
    static readonly Dictionary<string, string> BgGlyph = new() { ["hunter"] = "claw", ["scholar"] = "book", ["outcast"] = "mask", ["devout"] = "sun" };
    // Never a name the story has spent or nearly spent (Ashe, Kell, Orrin; Ysolde, Brannoc, Corran, Holloway, Tam).
    static readonly string[] Names = { "Alder", "Bryony", "Cass", "Dace", "Edda", "Fen", "Garrow", "Hester", "Ilse", "Jessamy", "Kit", "Lorne", "Maren", "Nolly", "Orla", "Pim", "Quill", "Rhosyn", "Sabre", "Tegan", "Ulla", "Voss", "Wren", "Yarrow" };
    LineEdit? nameBox;

    public CreateScreen(Game g, CreationDraft draft) : base(g) { d = draft; }

    void Set(Action change)
    {
        int step = d.Step, section = d.Section;
        change();
        G.DressFigure(d);
        // A new step or part frames the figure for it (the look's parts come near: her hair, her face).
        if (d.Step != step || d.Section != section) G.FrameFigure(SectionZoom(), SectionTurn());
        Refresh();
    }

    void ChooseArchetype(string id)
    {
        var a = Callings.Archetype(id);
        d.Archetype = id; d.WeaponItem = a.Weapons[0]; d.Ability = a.Abilities[0]; d.Palette = a.Palettes[0].Id; d.Model = a.Model; d.Headgear = true;
    }

    bool CanBegin => d.Name.Trim().Length > 0;

    void Begin()
    {
        if (!CanBegin)
        {
            // No name yet: offer one from the road (a pad cannot type), and wait for a second word.
            Set(() => { d.Step = NameStep; d.Name = Names[Random.Shared.Next(Names.Length)]; });
            Nav.FocusId = "begin";
            return;
        }
        G.BeginJourney(d.Choice());
    }

    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        // (the column's place in its list, kept through the rebuild a choice makes)
        float was = scroll != null && IsInstanceValid(scroll) && scrollKey == (d.Step, d.Section) ? scroll.ScrollVertical : 0;
        // The figure between the column and the plate: dragged, she turns; the wheel brings her near.
        AddChild(Stage());
        // A forged column down the left, the figure by the fire in the middle, the choice read
        // closely on the right (docs/UI_DESIGN.md, "Creation").
        var column = Style.Panel(Style.Plate(0));
        column.Position = new Vector2(-30, -30);
        column.Size = new Vector2(620, 1140);
        AddChild(column);
        var col = Style.V(Style.Gap3);
        col.Position = new Vector2(52, 44);
        col.Size = new Vector2(486, 1000);
        AddChild(col);
        col.AddChild(Style.Label("By the fire on the Low Ford road", Style.TextItalic, Style.Body, new Color("#c8a878")));
        col.AddChild(new Plaque("Who sits here?", 30, 30));
        col.AddChild(StepRoad());
        if (d.Step == LookStep) col.AddChild(SectionTabs());
        var body = d.Step switch { 0 => Calling(), 1 => Arms(a), 2 => Origin(), LookStep => Look(a), _ => NamePage(a) };
        var sc = Style.Scroll(body);
        sc.SizeFlagsVertical = SizeFlags.ExpandFill;
        col.AddChild(sc);
        scroll = sc;
        scrollKey = (d.Step, d.Section);
        if (was > 0) Callable.From(() => { if (IsInstanceValid(sc)) sc.ScrollVertical = (int)was; }).CallDeferred();
        var foot = Style.H(10, Nav.Id(Style.Button(d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); }), "back"));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(d.Step < NameStep ? Nav.Id(Style.Button($"Next: {Steps[d.Step + 1]}", () => Set(() => d.Step++), true), "next") : Nav.Id(Style.Button("Begin the journey", Begin, true), "begin"));
        col.AddChild(foot);

        var right = Style.Panel(Style.Plate(24));
        right.Position = new Vector2(1380, 110);
        right.Size = new Vector2(500, 0);
        right.CustomMinimumSize = new Vector2(500, 0);
        right.AddChild(d.Step switch { 0 => CallingDetail(a), 1 => ArmsDetail(), 2 => OriginDetail(), LookStep => LookDetail(a), _ => Summary(a) });
        AddChild(right);

        // Who they are becoming, on a banner at the figure's feet.
        var cap = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 20), Style.V(0, Style.Label(d.Name.Trim() == "" ? "NAMELESS" : d.Name.Trim().ToUpperInvariant(), Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center),
            Style.Label($"{Callings.Background(d.Background).Name} {a.Name}", Style.TextItalic, Style.Body, Style.Ink, false, HorizontalAlignment.Center)));
        cap.CustomMinimumSize = new Vector2(380, 0);
        AddChild(cap);
        cap.Position = new Vector2(1010 - 190, 960);
    }

    /// <summary>The four steps as a road of medallions: done in gold, this one lit, the rest dark.</summary>
    Control StepRoad()
    {
        bool pad = Controls.Instance.UsingPad;
        var road = Style.H(0);
        road.Alignment = BoxContainer.AlignmentMode.Center;
        var lb = pad ? Style.PadButton("LB") : Style.Key(G.Key(Act.TabPrev));
        lb.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        road.AddChild(lb);
        for (int i = 0; i < Steps.Length; i++)
        {
            int st = i;
            bool here = d.Step == i, done = i < d.Step;
            var b = Style.Button("", () => Set(() => d.Step = st), false, true);
            foreach (var x in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(x, new StyleBoxEmpty());
            var v = Style.V(2);
            v.MouseFilter = MouseFilterEnum.Ignore;
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(new Medallion(here ? 52 : 44, Numerals[i])
            {
                Ring = here ? Style.Ember : done ? Style.Gold : Style.InkFaint, Ink = here ? Style.EmberHi : done ? Style.GoldHi : Style.InkDim,
                Core = done || here ? new Color("#3a2210") : new Color("#120f14"), Lit = here,
            });
            v.AddChild(mc);
            v.AddChild(Style.Label(Steps[i], Style.UiBold, Style.Caption, here ? Style.EmberHi : done ? Style.GoldHi : Style.InkDim, false, HorizontalAlignment.Center));
            v.Size = new Vector2(84, 80);
            b.AddChild(v);
            b.CustomMinimumSize = new Vector2(84, 80);
            road.AddChild(Nav.Skip(b));
            if (i < Steps.Length - 1)
            {
                var line = new ColorRect { Color = i < d.Step ? Style.Gold : Style.Line, CustomMinimumSize = new Vector2(16, 2), SizeFlagsVertical = SizeFlags.ShrinkBegin, MouseFilter = MouseFilterEnum.Ignore };
                var lw = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
                lw.AddThemeConstantOverride("margin_top", 26);
                lw.AddChild(line);
                road.AddChild(lw);
            }
        }
        var rb = pad ? Style.PadButton("RB") : Style.Key(G.Key(Act.TabNext));
        rb.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        road.AddChild(rb);
        return road;
    }

    /// <summary>A choice as a crested card: its mark on a medallion, its name, its words; the one taken lit in ember.</summary>
    static Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null)
    {
        var b = Style.Button("", act);
        b.CustomMinimumSize = new Vector2(470, 92);
        Nav.Id(b, $"choice:{name}");
        var box = OrnateBox.Make(OrnateBox.Kind.Card, 0, on ? Style.Ember : Style.GoldDim);
        box.Crest = on ? 40 : 0;
        box.Glow = on ? 0.8f : 0;
        var hover = OrnateBox.Make(OrnateBox.Kind.Card, 0, on ? Style.EmberHi : Style.Gold);
        hover.Crest = 40;
        b.AddThemeStyleboxOverride("normal", box);
        b.AddThemeStyleboxOverride("hover", hover);
        b.AddThemeStyleboxOverride("pressed", hover);
        if (on) b.SetMeta("on", true);
        var row = Style.H(14, new Medallion(64, "", glyph) { Ring = on ? Style.Ember : Style.Gold, Ink = on ? Style.EmberHi : Style.GoldHi, Lit = on });
        var words = Style.V(0, Style.Label(name.ToUpperInvariant(), Style.Display, 21, on ? Colors.White : Style.GoldHi), Style.Label(tag, Style.Ui, Style.Small, tagColor ?? Style.InkDim, true));
        words.CustomMinimumSize = new Vector2(360, 0);
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(words);
        row.Position = new Vector2(14, 14);
        row.MouseFilter = MouseFilterEnum.Ignore;
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
        v.AddChild(Style.H(8, Style.SubLabel("Art in hand"), Style.Label("you know all four; more are learned on the road", Style.TextItalic, Style.Caption, Style.InkDim)));
        foreach (var id in ArtBook.Starting(a.Id))
        {
            var ab = Abilities.ById(id);
            string kind = ab.Movement ? "a way of moving" : "the calling's own";
            v.AddChild(Choice(ab.Icon, ab.Name, $"{kind} · {ab.Cooldown} s{(ab.Interrupts ? " · breaks channels" : "")}", d.Ability == id, () => Set(() => d.Ability = id)));
        }
        return v;
    }

    Control Origin()
    {
        var v = Style.V(6);
        foreach (var (id, bg) in Callings.Backgrounds)
            v.AddChild(Choice(BgGlyph.GetValueOrDefault(id, "map"), bg.Name, bg.Summary, d.Background == id, () => Set(() => d.Background = id)));
        return v;
    }

    /// <summary>The last step: their name (typed, or one from the road), and
    /// who they are, read back before the journey begins.</summary>
    Control NamePage(Archetype a)
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
        v.AddChild(Style.H(8, Nav.Skip(nameBox), Nav.Id(Style.Button("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), false, true), "roadname")));
        // The keyboard types at once; a pad cannot type, so it is offered names instead.
        if (!Controls.Instance.UsingPad) Callable.From(() => nameBox?.GrabFocus()).CallDeferred();
        else if (d.Name.Trim() == "") Nav.Prefer = "roadname";
        // Who they are, each step's answer on its medallion; a press goes back to it.
        v.AddChild(Style.Gap(6));
        v.AddChild(Style.SubLabel(d.Sex == Sex.Female ? "Who she is" : "Who he is"));
        var bg = Callings.Background(d.Background);
        var ab = Abilities.ById(d.Ability);
        v.AddChild(Recall(0, ClassGlyph.GetValueOrDefault(d.Archetype, "sword"), a.Name, a.Tagline));
        v.AddChild(Recall(1, ab.Icon, Items.Get(d.WeaponItem).Name, $"and {ab.Name} in hand"));
        v.AddChild(Recall(2, BgGlyph.GetValueOrDefault(d.Background, "map"), bg.Name, bg.Summary));
        v.AddChild(Recall(LookStep, "mask", d.Sex == Sex.Female ? "Her look" : "His look", LookWords()));
        return v;
    }

    /// <summary>A step's answer, read back: pressed, it goes back to that step.</summary>
    Button Recall(int step, string glyph, string name, string words)
    {
        var b = Style.Button("", () => Set(() => d.Step = step));
        b.CustomMinimumSize = new Vector2(470, 70);
        Nav.Id(b, $"recall:{step}");
        foreach (var x in new[] { "normal", "hover", "pressed" })
            b.AddThemeStyleboxOverride(x, x == "normal" ? new StyleBoxEmpty() : Style.Slab(0));
        var row = Style.H(12, new Medallion(52, "", glyph) { Ring = Style.GoldDim, Ink = Style.GoldHi });
        var w = Style.V(0, Style.Label(name, Style.UiBold, Style.Small, Style.GoldHi), Style.Label(words, Style.Ui, Style.Caption, Style.InkDim, true));
        w.CustomMinimumSize = new Vector2(380, 0);
        w.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(w);
        row.Position = new Vector2(8, 9);
        row.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        return b;
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
        // The art's words take the panel's width (they were squeezed into a column).
        var what = Style.V(2, Style.H(6, Style.Label(ab.Name, Style.UiBold, Style.Small, Style.GoldHi), Style.Prompt(Act.Ability)),
            Style.Label(ab.Description, Style.Text, Style.Small, Style.Ink, true));
        what.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        v.AddChild(Style.H(10, Glyphs.Icon(ab.Icon, 30, new Color("#ffe2b0")), what));
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
            Line("Hands", Abilities.ById(d.Ability).Name),
            Line("Knows", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))), Style.Rule(),
            Style.Label("Night is falling on the Low Ford road. The fire is low. What you do from here, the world will remember.", Style.TextItalic, 15, Style.InkDim, true));
    }

    public override bool Key(Act a)
    {
        // Typing a name: the letters are the name's, not the menu's.
        if (nameBox != null && nameBox.HasFocus() && a is not (Act.Cancel or Act.Confirm)) return true;
        if (nameBox != null && nameBox.HasFocus() && a == Act.Confirm) { nameBox.ReleaseFocus(); Begin(); return true; }
        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(NameStep, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }
        // The look's parts, on the triggers (or , and .).
        if (d.Step == LookStep && a is Act.SubNext or Act.SubPrev)
        {
            int n = Sections.Length;
            Set(() => d.Section = (d.Section + (a == Act.SubNext ? 1 : n - 1)) % n);
            Sound.Sfx.Page();
            return true;
        }
        if (a == Act.Cancel) { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); return true; }
        if (a == Act.Confirm)
        {
            // On a choice not yet taken, Enter or A takes it (focus does it); otherwise, onward.
            if (Nav.KeyMode && Nav.Current is { } c && !c.C.HasMeta("on")) return false;
            if (d.Step < NameStep) Set(() => d.Step++); else Begin();
            return true;
        }
        return false;
    }
}
