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

    /// <summary>The line the ember starts on: back from the credits, it is still on Credits.</summary>
    string? focus;

    // (--panel load|settings|controls: opened on that panel, for pictures)
    public TitleScreen(Game g, string? focus = null) : base(g) { menu = new MenuList(Refresh, 24); this.focus = focus; if (Args.Get("panel") is "load" or "settings" or "controls") panel = Args.Get("panel")!; }

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
        // (a panel open takes the name's place: the picture keeps its fire, the panel its room)
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
        if (panel == "") AddChild(brand);

        var slots = G.Saves.Slots();
        var latest = slots.OrderByDescending(s => s.SavedAt).FirstOrDefault();
        menu.Items.Clear();
        if (latest != null)
            menu.Add("Continue", () => G.Continue(latest.Slot), $"{latest.Name} · {Callings.Archetypes.GetValueOrDefault(latest.Archetype)?.Name} {latest.Level} · Day {latest.Day}", true);
        menu.Add("New Journey", G.NewJourney, null, latest == null);
        if (slots.Count > 0) menu.Add("Journeys", () => Panel("load"));
        menu.Add("Settings", () => Panel("settings"));
        menu.Add("Controls", () => Panel("controls"));
        menu.Add("Credits", G.Credits);
        menu.Add("Quit", G.QuitGame);
        if (focus != null) { menu.Focus = Math.Max(0, menu.Items.FindIndex(i => i.Label == focus)); focus = null; }
        var list = menu.Build();
        list.Position = new Vector2(134, 560);
        AddChild(list);
        Nav.Scope = null;

        if (panel != "")
        {
            // A fitted panel over the fire's picture, as the pause opens its own: its name, its rows as
            // type, back with its key at its foot.
            var v = Fitted(new Vector2(540, 16), panel == "controls" ? 600 : panel == "settings" ? 780 : 640);
            Nav.Scope = v;
            v.AddChild(new Title(panel switch { "load" => "Journeys", "settings" => "Settings", _ => "Controls" }, 30, false));
            switch (panel)
            {
                case "load":
                    foreach (var s in slots)
                    {
                        var arch = Callings.Archetypes.GetValueOrDefault(s.Archetype);
                        var mark = Glyphs.Icon(s.Archetype switch { "warden" => "shield", "reaver" => "axe", "arcanist" => "staff", _ => "bow" }, 30, s.Alive ? Kit.Ink2 : Kit.Faint, true);
                        mark.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                        var words = Style.V(0, Style.Label(s.Name.ToUpperInvariant(), Style.Display, 20, s.Alive ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false),
                            Style.Label($"{arch?.Name} {s.Level}  ·  Day {s.Day}  ·  {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.TextItalic, 16, Kit.HeadInk, false, HorizontalAlignment.Left, false),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.Ui, 14, Kit.Dim, false, HorizontalAlignment.Left, false));
                        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                        int slot = s.Slot;
                        var resume = Kit.Word("Resume", () => G.Continue(slot), Style.EmberHi, 17);
                        var forget = Kit.Word("Forget", () => { G.Saves.Remove(slot); Refresh(); }, Kit.Dim, 15);
                        foreach (var c in new Control[] { resume, forget }) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                        v.AddChild(Style.H(Style.Gap4, mark, words, resume, forget));
                    }
                    break;
                case "settings": v.AddChild(SettingsPanel.Build(G, Refresh)); break;
                default: v.AddChild(new ControlsPanel()); break;
            }
            v.AddChild(Style.V(Style.Gap3, Kit.RuleH(), Nav.Id(Kit.Keyed(Act.Cancel, "Back", () => Panel(panel)), "back")));
        }
        var (built, stale) = Made;
        var foot = Style.Label($"BETA  ·  THE FIRST CHAPTER{(built is DateTime t ? $"  ·  BUILT {t:d MMMM, HH:mm}".ToUpperInvariant() : "")}", Style.UiBold, Style.Badge, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
        if (stale)
        {
            var warn = Style.Label("This build is older than the game's code, so the newest work is not in it. Open the project in Godot and press Play (it builds first).",
                Style.UiBold, Style.Caption, Style.EmberHi, true);
            warn.Position = new Vector2(134, 1000);
            warn.Size = new Vector2(900, 0);
            AddChild(warn);
        }
    }

    static (DateTime?, bool)? build;

    /// <summary>When the game's code was last built, and whether any of it has changed since:
    /// run from the project manager, Godot starts the last build without making a new one, and
    /// the owner once looked for work that was not in the build they ran. (Godot loads the code
    /// from memory, so the build is read from where the editor writes it; an exported game has
    /// neither, and says nothing.)</summary>
    static (DateTime?, bool) Made => build ??= ReadBuild();

    static (DateTime?, bool) ReadBuild()
    {
        try
        {
            var dll = ProjectSettings.GlobalizePath("res://.godot/mono/temp/bin/Debug/SurvivorUnchained.dll");
            if (!System.IO.File.Exists(dll)) return (null, false);
            var t = System.IO.File.GetLastWriteTime(dll);
            bool stale = false;
            foreach (var dir in new[] { "res://src", "res://logic" })
            {
                var path = ProjectSettings.GlobalizePath(dir);
                if (System.IO.Directory.Exists(path) && System.IO.Directory.EnumerateFiles(path, "*.cs", System.IO.SearchOption.AllDirectories)
                    .Any(f => System.IO.File.GetLastWriteTime(f) > t.AddMinutes(1))) stale = true;
            }
            return (t, stale);
        }
        catch (Exception) { return (null, false); }
    }

    void Panel(string p) { panel = panel == p ? "" : p; Refresh(); }

    void Mature()
    {
        AddChild(Style.Scrim(null, 0.75f));
        // The first thing the game says: a fitted panel over the fire, its words as type and its two
        // answers as words with their keys (no card, no buttons' boxes).
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        AddChild(centre);
        var panel = Style.Panel(Kit.Window(Margin + 8, Margin, Margin));
        panel.CustomMinimumSize = new Vector2(620, 0);
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        centre.AddChild(panel);
        var v = Style.V(Style.Gap4, new Title("For adults", 30, false));
        // (broken into even lines across the panel's measure, never a word or two alone on the last)
        Label Words(string t, bool quiet = false)
        {
            var f = quiet ? Style.TextItalic : Style.Text;
            int size = quiet ? 16 : 18;
            return Style.Label(Kit.Balance(t, f, size, 620 - 2 * (Margin + 8)), f, size, quiet ? Kit.Dim : Kit.Ink2, false, HorizontalAlignment.Center, false);
        }
        if (left) v.AddChild(Words("Another time, then. The fire will still be burning."));
        else
        {
            v.AddChild(Words("Survivor Unchained is made for adults. It has graphic violence and gore, strong language, revealing clothes and sexual themes. Nothing sexual is shown on screen."));
            v.AddChild(Words("Gore can be reduced or turned off in Settings.", true));
            var agree = Nav.Id(Kit.Keyed(Act.Confirm, "I am 18 or over", Agree, Style.EmberHi), "agree");
            var leave = Nav.Id(Kit.Keyed(Act.Cancel, "Leave", () => { left = true; Refresh(); }), "leave");
            v.AddChild(Style.V(Style.Gap3, Kit.RuleH(), Style.H(0, agree, new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore }, leave)));
        }
        panel.AddChild(v);
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
            if (a == Act.Cancel && !left) { left = true; Refresh(); }
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
    /// <summary>A hero's own beard (Lore.Hero's beards: the male hero's), or "".</summary>
    public string BeardStyle = "";
    public bool Headgear = true, Beard = true;
    /// <summary>The survivor is the heroine, unless a man is chosen.</summary>
    public Sex Sex = Sex.Female;
    public double Figure = 1.0;
    /// <summary>Her eyes, the paint on her face, and her face: its sliders
    /// (her own face where none is moved) and the face it started from.</summary>
    public string Eyes = "moss", Paint = "none", FaceShape = "own";
    public Dictionary<string, double> Face = new();
    /// <summary>The look step's part (hair, face, shape, paint, body) and the face's group of sliders.</summary>
    public int Section, FaceGroup;

    public CreationChoice Choice() => new()
    {
        Name = Name.Trim(), Archetype = Archetype, Background = Background, Palette = Palette, Model = Model, WeaponItem = WeaponItem, Ability = Ability,
        Headgear = Headgear, Cloak = Cloak, Skin = Skin, Hair = Hair, Sex = Sex, HairStyle = HairStyle, Beard = Beard, Figure = Figure,
        // (a hero's own body's face, eyes and paint: Loadouts.HeroKit)
        Face = Loadouts.HeroKit(Sex) != null ? new Dictionary<string, double>(Face) : null,
        Eyes = Loadouts.HeroKit(Sex) != null ? Eyes : null, Paint = Loadouts.HeroKit(Sex) != null ? Paint : null,
        FaceShape = Loadouts.HeroKit(Sex) != null ? FaceShape : null,
        BeardStyle = Loadouts.HeroKit(Sex) is { Beards.Count: > 0 } && BeardStyle != "" ? BeardStyle : null,
    };

    /// <summary>The figure by the fire is built again when this changes (who
    /// they are, what they wear and hold); a man's hair and skin are his clothes' kit.</summary>
    public string BodyKey => $"{Archetype}|{Model}|{WeaponItem}|{Palette}|{Headgear}|{Cloak}|{Sex}|{Figure}|{Beard}" + (Sex == Sex.Male ? $"|{Skin}|{Hair}|{HairStyle}|{BeardStyle}" : "");

    /// <summary>What the figure looks like: changes when this does (her hair,
    /// skin, eyes, face and paint are changed on her where she stands).</summary>
    public string LookKey => $"{BodyKey}|{Skin}|{Hair}|{HairStyle}|{Eyes}|{Paint}|{FaceShape}|{string.Join(",", Face.OrderBy(f => f.Key).Select(f => $"{f.Key}={f.Value:0.###}"))}";

    /// <summary>A body chosen: its own hairstyle kept if it is one of its own,
    /// its own first otherwise; a hero's own eyes, paint and face start as theirs.</summary>
    public void SetSex(Sex sx)
    {
        Sex = sx;
        Section = FaceGroup = 0;
        if (Loadouts.HeroKit(sx) is { } kit)
        {
            HairStyle = sx == Sex.Female ? Loadouts.HerHair(HairStyle) : kit.Cuts.Any(c => c.Id == HairStyle) ? HairStyle : kit.Cuts[0].Id;
            Eyes = kit.Eyes.FirstOrDefault()?.Id ?? "";
            Paint = kit.Paints.FirstOrDefault()?.Id ?? "none";
            BeardStyle = kit.Beards.FirstOrDefault()?.Id ?? "";
            FaceShape = kit.Faces.FirstOrDefault()?.Id ?? "";
            Face = new Dictionary<string, double>(kit.Faces.FirstOrDefault()?.Shape ?? new());
        }
        else if (!Lore.HairStyles(sx).Contains(HairStyle) && HairStyle != "none") HairStyle = Lore.HairStyles(sx)[0];
    }
}

/// <summary>
/// Making the survivor, by the fire (the web game's screens/Create.tsx).
/// Five steps, each a question the world will ask again later: Calling (who
/// sits here, a woman or a man, and how do they fight?), Look (what does she
/// look like? second, so no one misses it), Arms (with what, and what do
/// their hands do?), Origin (where are they from?), Name (who are they?).
/// The figure by the fire changes as you choose, and can be turned
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
    static readonly string[] Steps = { "Calling", "Look", "Arms", "Origin", "Name" };
    static readonly string[] Numerals = { "I", "II", "III", "IV", "V" };
    /// <summary>The look comes straight after the calling: the calling dresses her, then she is shaped.</summary>
    public const int CallingStep = 0, LookStep = 1, ArmsStep = 2, OriginStep = 3, NameStep = 4;
    static readonly Dictionary<string, string> ClassGlyph = new() { ["warden"] = "shield", ["reaver"] = "axe", ["arcanist"] = "staff", ["stalker"] = "bow" };
    static readonly Dictionary<string, string> BgGlyph = new() { ["hunter"] = "claw", ["scholar"] = "book", ["outcast"] = "mask", ["devout"] = "sun" };
    // Never a name the story has spent or nearly spent (Ashe, Kell, Orrin; Ysolde, Brannoc, Corran, Holloway, Tam).
    static readonly string[] Names = { "Alder", "Bryony", "Cass", "Dace", "Edda", "Fen", "Garrow", "Hester", "Ilse", "Jessamy", "Kit", "Lorne", "Maren", "Nolly", "Orla", "Pim", "Quill", "Rhosyn", "Sabre", "Tegan", "Ulla", "Voss", "Wren", "Yarrow" };
    LineEdit? nameBox;

    public CreateScreen(Game g, CreationDraft draft) : base(g) { d = draft; }

    void Set(Action change)
    {
        int step = d.Step, section = d.Section;
        string cut = d.HairStyle;
        change();
        G.DressFigure(d);
        // A new step or part frames the figure for it (the look's parts come near: her hair, her face);
        // a new cut turns her so it shows (a braid down her back is seen from behind).
        if (d.Step != step || d.Section != section || d.HairStyle != cut) G.FrameFigure(SectionZoom(), SectionTurn());
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

    /// <summary>Each step's question, the title over its column: the world asks them again later.</summary>
    string Question => d.Step switch
    {
        CallingStep => "Who sits here?",
        LookStep => Her ? "What does she look like?" : "What does he look like?",
        ArmsStep => "With what?",
        OriginStep => Her ? "Where is she from?" : "Where is he from?",
        _ => Her ? "Who is she?" : "Who is he?",
    };

    /// <summary>The two panels' width and their inset from the screen's edges: the choices on the
    /// left, what the one taken means on the right, mirrored, the figure standing between them.</summary>
    const float PanelW = 560, Inset = 16;

    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        // The figure between the panels: dragged, she turns; the wheel brings her near.
        AddChild(Stage());
        // The left panel: the steps on their chain, the step's question, the choices, the way on.
        var col = Fitted(new Vector2(Inset, Inset), PanelW);
        // (the steps are turned with LB and RB, or [ and ], drawn at the chain's ends)
        var steps = new ChainTabs(Steps.Select(s => (s, "")).ToArray(), d.Step, k => { if (k != d.Step) { Sound.Sfx.Page(); Set(() => d.Step = k); } },
            (G.Key(Act.TabPrev), G.Key(Act.TabNext)), 20) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        col.AddChild(steps);
        var head = Style.V(2, new Title(Question, 30, false),
            Style.Label("By the fire on the Low Ford road", Style.TextItalic, 17, Kit.HeadInk, false, HorizontalAlignment.Center, false));
        col.AddChild(head);
        if (d.Step == LookStep) col.AddChild(SectionTabs());
        col.AddChild(d.Step switch { CallingStep => Calling(), LookStep => Look(a), ArmsStep => Arms(a), OriginStep => Origin(), _ => NamePage(a) });
        col.AddChild(Foot());
        // The right panel, its twin: what the choice means, read closely.
        var right = Fitted(new Vector2(1920 - Inset - PanelW, Inset), PanelW);
        right.AddChild(d.Step switch { CallingStep => CallingDetail(a), LookStep => LookDetail(a), ArmsStep => ArmsDetail(), OriginStep => OriginDetail(), _ => Summary(a) });
        // Who they are becoming, set on the ground at the figure's feet (not while the look is near her face).
        if (d.Step != LookStep) AddChild(Nameplate(a));
    }

    /// <summary>The panel's foot: back (or leave) and the way on, each its key and its word, at
    /// either end; from the calling, the way on names what the look holds, so no one walks past it.</summary>
    Control Foot()
    {
        var back = Kit.Keyed(Act.Cancel, d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); });
        Nav.Id(back, "back");
        string next = d.Step + 1 == LookStep ? $"Next: {Their.ToLowerInvariant()} hair, face and paint" : $"Next: {Steps[Math.Min(d.Step + 1, NameStep)].ToLowerInvariant()}";
        var on = d.Step < NameStep ? Nav.Id(Kit.Keyed(Act.Confirm, next, () => Set(() => d.Step++), Style.EmberHi), "next") : Nav.Id(Kit.Keyed(Act.Confirm, "Begin the journey", Begin, Style.EmberHi), "begin");
        var row = Style.H(0, back, new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore }, on);
        return Style.V(Style.Gap3, Kit.RuleH(), row);
    }

    /// <summary>The name and what they are, as type on the ground at the figure's feet: no banner.</summary>
    static Control Plate(string name, string what)
    {
        var v = Style.V(0, WorldType.Lettering(name, Style.Display, 36, new Color("#f2e8d4")), WorldType.Lettering(what, Style.TextItalic, 19, new Color("#d8cebc")));
        foreach (var l in v.GetChildren().OfType<Label>()) l.HorizontalAlignment = HorizontalAlignment.Center;
        var c = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(Inset + PanelW, 884), Size = new Vector2(1920 - 2 * (Inset + PanelW), 96) };
        c.AddChild(v);
        return c;
    }

    Control Nameplate(Archetype a) => Plate(d.Name.Trim() == "" ? "NAMELESS" : d.Name.Trim().ToUpperInvariant(), $"{Callings.Background(d.Background).Name} {a.Name}");

    /// <summary>A choice as a line of type: its mark, its name in capitals and what it is under it;
    /// the one taken marked with the ember, as the menus mark theirs, and lit. No box.</summary>
    Button Row(string glyph, string name, string tag, bool on, Action act, string id, Color? tagColor = null, bool marked = true)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        Nav.Id(b, id);
        if (on) b.SetMeta("on", true);
        var ink = on ? new Color("#fff2d8") : Kit.Ink2;
        var title = Style.Label(name.ToUpperInvariant(), Style.Display, 20, ink, false, HorizontalAlignment.Left, false);
        var words = Style.V(0, title, Style.Label(tag, Style.TextItalic, 16, tagColor ?? Kit.Dim, false, HorizontalAlignment.Left, false));
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        // (drawn glyphs, all one hand: the painted ones are a mix of full colour and line)
        var icon = Glyphs.Icon(glyph, 30, on ? Style.EmberHi : Kit.Dim, true);
        icon.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        var row = Style.H(Style.Gap4, icon, words);
        if (marked)
        {
            // (the ember diamond, as the pause and the title mark their line)
            var markBox = new Control { CustomMinimumSize = new Vector2(12, 0), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.Fill };
            // (turned about its corner: its middle on the name's capitals)
            if (on) markBox.AddChild(new ColorRect { Color = Style.Ember, Size = new Vector2(8, 8), Rotation = Mathf.Pi / 4, Position = new Vector2(6, 8), MouseFilter = MouseFilterEnum.Ignore });
            row.AddChild(markBox);
            row.MoveChild(markBox, 0);
        }
        row.MouseFilter = MouseFilterEnum.Ignore;
        foreach (var c in row.GetChildren().OfType<Control>()) c.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        b.CustomMinimumSize = row.GetCombinedMinimumSize() + new Vector2(0, 4);
        row.Position = new Vector2(0, 2);
        b.MouseEntered += () => title.AddThemeColorOverride("font_color", Kit.Ink);
        b.MouseExited += () => title.AddThemeColorOverride("font_color", ink);
        b.Pressed += act;
        return b;
    }

    Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null) => Row(glyph, name, tag, on, act, $"choice:{name}", tagColor);

    /// <summary>Words to choose between, the one chosen in full ink over the ember's underline (the
    /// house's tabs), centred; each with its focus id.</summary>
    static HBoxContainer Words(string[] names, int on, Action<int> pick, string[] ids, int size = 19, int gap = 40)
    {
        var tabs = Kit.Tabs(names, on, pick, size, gap);
        tabs.Alignment = BoxContainer.AlignmentMode.Center;
        int i = 0;
        foreach (var b in tabs.GetChildren().OfType<Button>())
        {
            Nav.Id(b, ids[i]);
            if (i == on) b.SetMeta("on", true);
            i++;
        }
        return tabs;
    }

    /// <summary>Who sits here (a woman or a man: the first thing anyone asks), and how they fight.</summary>
    Control Calling()
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(Words(new[] { "A woman", "A man" }, Her ? 0 : 1, k => Set(() => d.SetSex(k == 0 ? Sex.Female : Sex.Male)), new[] { "sex:Female", "sex:Male" }));
        v.AddChild(Style.Gap(Style.Gap1));
        foreach (var (id, a) in Callings.Archetypes)
            v.AddChild(Choice(ClassGlyph.GetValueOrDefault(id, "sword"), a.Name, a.Tagline, d.Archetype == id, () => Set(() => ChooseArchetype(id))));
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Kit.RuleH());
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(LookInvite());
        return v;
    }

    /// <summary>The look, offered under the callings: her portrait in its ring and what can be
    /// shaped, so the step that makes her theirs is seen before anyone walks past it. No card:
    /// the portrait is the one painted thing on the panel.</summary>
    Button LookInvite()
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        Nav.Id(b, "invite:look");
        b.Pressed += () => Set(() => { d.Step = LookStep; d.Section = 0; });
        const int size = 104;
        var face = new Cameo(Art("look"), "", false, () => { }, size, null, "mask") { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(size + 14, size + 4) };
        bool pad = Controls.Instance.UsingPad;
        string them = Her ? "her" : "him", their = Their.ToLowerInvariant();
        var head = Style.Label($"II  ·  {Their} look".ToUpperInvariant(), Style.Display, 20, Kit.Ink, false, HorizontalAlignment.Left, false);
        var line = Style.Label(Kit.Balance($"{Their} hair and its colour, {their} face and eyes, the paint on it, {their} skin.", Style.Text, 16, 330), Style.Text, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
        var shape = Style.Label($"Shape {them}", Style.TextItalic, 16, Style.EmberHi, false, HorizontalAlignment.Left, false);
        var go = Style.H(Style.Gap2, pad ? Style.PadButton("RB") : Style.Key(G.Key(Act.TabNext)), shape);
        foreach (var c in go.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        var words = Style.V(Style.Gap1, head, line, go);
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        var row = Style.H(Style.Gap4, face, words);
        row.MouseFilter = MouseFilterEnum.Ignore;
        foreach (var c in row.GetChildren().OfType<Control>()) c.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        b.CustomMinimumSize = row.GetCombinedMinimumSize();
        b.MouseEntered += () => head.AddThemeColorOverride("font_color", new Color("#fff2d8"));
        b.MouseExited += () => head.AddThemeColorOverride("font_color", Kit.Ink);
        return b;
    }

    Control Arms(Archetype a)
    {
        var v = Style.V(Style.Gap2, Kit.Head("Weapon"));
        foreach (var id in a.Weapons)
        {
            var it = Items.Get(id);
            var w = it.Weapon != null ? Weapons.All.GetValueOrDefault(it.Weapon.Id) : null;
            v.AddChild(Choice(it.Icon, it.Name, w != null ? $"{w.Name} · {w.School.ToString().ToLowerInvariant()}" : "", d.WeaponItem == id, () => Set(() => d.WeaponItem = id),
                w != null ? ItemViews.SchoolColors[w.School] : null));
        }
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Kit.Head("Art in hand", "all four known; more on the road"));
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
        var v = Style.V(Style.Gap2);
        foreach (var (id, bg) in Callings.Backgrounds)
            v.AddChild(Choice(BgGlyph.GetValueOrDefault(id, "map"), bg.Name, bg.Summary, d.Background == id, () => Set(() => d.Background = id)));
        return v;
    }

    /// <summary>The last step: their name, written on a line (typed, or one from the road), and
    /// who they are, read back before the journey begins.</summary>
    Control NamePage(Archetype a)
    {
        var v = Style.V(Style.Gap2, Kit.Head("Name"));
        nameBox = new LineEdit { Text = d.Name, PlaceholderText = "Your name", MaxLength = 18, CustomMinimumSize = new Vector2(300, 44), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        Style.Font(nameBox, Style.Display, 26, Kit.Ink, false);
        nameBox.AddThemeColorOverride("font_placeholder_color", Kit.Faint);
        nameBox.AddThemeColorOverride("caret_color", Style.EmberHi);
        // Written on a rule, as a name is signed in a ledger: no field's box.
        StyleBoxFlat Ruled(Color c) => new() { BgColor = Colors.Transparent, BorderColor = c, BorderWidthBottom = 1, ContentMarginLeft = 2, ContentMarginRight = 2, ContentMarginTop = 4, ContentMarginBottom = 6 };
        nameBox.AddThemeStyleboxOverride("normal", Ruled(Kit.Edge));
        nameBox.AddThemeStyleboxOverride("focus", Ruled(Style.Ember));
        nameBox.TextChanged += t =>
        {
            var clean = new string(t.Where(c => char.IsLetter(c) || c is '\'' or ' ' or '-').ToArray());
            d.Name = clean;
            if (clean != t) { nameBox.Text = clean; nameBox.CaretColumn = clean.Length; }
        };
        nameBox.TextSubmitted += _ => Begin();
        var road = Nav.Id(Kit.Word("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), Style.EmberHi, 16), "roadname");
        road.SizeFlagsVertical = SizeFlags.ShrinkEnd;
        v.AddChild(Style.H(Style.Gap4, Nav.Skip(nameBox), road));
        // The keyboard types at once; a pad cannot type, so it is offered names instead.
        if (!Controls.Instance.UsingPad) Callable.From(() => nameBox?.GrabFocus()).CallDeferred();
        else if (d.Name.Trim() == "") Nav.Prefer = "roadname";
        // Who they are, each step's answer on its line; a press goes back to it.
        v.AddChild(Style.Gap(Style.Gap3));
        v.AddChild(Kit.Head(Her ? "Who she is" : "Who he is"));
        var bg = Callings.Background(d.Background);
        var ab = Abilities.ById(d.Ability);
        v.AddChild(Recall(CallingStep, ClassGlyph.GetValueOrDefault(d.Archetype, "sword"), a.Name, a.Tagline));
        v.AddChild(Recall(LookStep, "mask", Her ? "Her look" : "His look", LookWords()));
        v.AddChild(Recall(ArmsStep, ab.Icon, Items.Get(d.WeaponItem).Name, $"and {ab.Name} in hand"));
        v.AddChild(Recall(OriginStep, BgGlyph.GetValueOrDefault(d.Background, "map"), bg.Name, bg.Summary));
        return v;
    }

    /// <summary>A step's answer, read back: pressed, it goes back to that step.</summary>
    Button Recall(int step, string glyph, string name, string words) => Row(glyph, name, words, false, () => Set(() => d.Step = step), $"recall:{step}", null, false);

    /* ------------------------------------------- the right panel's type -- */

    /// <summary>What a choice is, read closely on the right panel: its name centred over it, what it
    /// is in a line of italic, then its words; its numbers as a ledger line; its parts as lines.</summary>
    static Control DTitle(string text) => new Title(text, 28, false);
    static Label DSub(string text) => Style.Label(text, Style.TextItalic, 18, Kit.HeadInk, true, HorizontalAlignment.Center, false);
    static Label DBody(string text, bool italic = false) => Style.Label(text, italic ? Style.TextItalic : Style.Text, 17, italic ? Kit.Dim : Kit.Ink2, true, HorizontalAlignment.Left, false);

    /// <summary>A part as a line: its name in small capitals in a column, its words after.</summary>
    static Control Line(string label, string text)
    {
        // (the small capitals centred on the words' first line, however many lines they run to)
        var l = Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 13, Kit.HeadInk, false, HorizontalAlignment.Left, false);
        l.CustomMinimumSize = new Vector2(92, 23);
        l.VerticalAlignment = VerticalAlignment.Center;
        l.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        var w = Style.Label(text, Style.Text, 16, Kit.Ink2, true, HorizontalAlignment.Left, false);
        w.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return Style.H(Style.Gap3, l, w);
    }

    /// <summary>Numbers as a ledger line: each numeral over its name in small capitals, fine rules between.</summary>
    static Control Ledger(params (string Value, string Label)[] cells)
    {
        var line = Style.H(0);
        line.Alignment = BoxContainer.AlignmentMode.Center;
        for (int i = 0; i < cells.Length; i++)
        {
            if (i > 0) line.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(29, 52) });
            var cell = Style.V(0, Style.Label(cells[i].Value, Style.Display, 32, Kit.Ink, false, HorizontalAlignment.Center, true),
                Style.Label(cells[i].Label.ToUpperInvariant(), Style.DisplayLight, 13, Kit.HeadInk, false, HorizontalAlignment.Center, false));
            cell.CustomMinimumSize = new Vector2(98, 0);
            line.AddChild(cell);
        }
        return line;
    }

    Control CallingDetail(Archetype a) => Style.V(Style.Gap3,
        DTitle(a.Name), DSub(a.Tagline), DBody(a.Description), Kit.RuleH(),
        Ledger(($"{a.Base.MaxHealth:0}", "Health"), ($"{a.Base.Armor:0}", "Armour"), ($"{a.Base.MoveSpeed:0.0}", "Speed"), ($"{a.Base.CritChance * 100:0}%", "Precision")),
        Kit.RuleH(),
        Line("Arms", string.Join(" · ", a.Weapons.Select(w => Items.Get(w).Name))), Line("Arts", string.Join(" · ", a.Abilities.Select(x => Abilities.ById(x).Name))));

    Control ArmsDetail()
    {
        var it = Items.Get(d.WeaponItem);
        var w = it.Weapon != null ? Weapons.All.GetValueOrDefault(it.Weapon.Id) : null;
        var ab = Abilities.ById(d.Ability);
        var photo = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        photo.AddChild(ItemPhotos.Icon(it.Icon, 84, Style.GoldHi));
        var v = Style.V(Style.Gap3, photo, DTitle(it.Name));
        if (w != null) v.AddChild(Style.Label($"{w.Name} · {w.School.ToString().ToLowerInvariant()}", Style.TextItalic, 18, ItemViews.SchoolColors[w.School], false, HorizontalAlignment.Center, false));
        v.AddChild(DBody(it.Description));
        if (it.Lore != null) v.AddChild(DBody(it.Lore, true));
        if (w != null && w.Evolutions.Length > 0)
            v.AddChild(Line("At rank 8", string.Join(", or ", w.Evolutions.Select(e => $"{e.Name} (with {string.Join(" or ", e.Catalysts.Select(c => Boons.Find(c)?.Name ?? c))})"))));
        v.AddChild(Kit.RuleH());
        // The art in hand: its mark, its name and key, what it does.
        var name = Style.H(Style.Gap2, Style.Label(ab.Name.ToUpperInvariant(), Style.Display, 18, Kit.Ink, false, HorizontalAlignment.Left, false), Style.Prompt(Act.Ability));
        foreach (var c in name.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        var what = Style.V(Style.Gap1, name, Style.Label(ab.Description, Style.Text, 16, Kit.Ink2, true, HorizontalAlignment.Left, false));
        what.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var mark = Glyphs.Icon(ab.Icon, 34, Style.EmberHi, true);
        mark.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        v.AddChild(Style.H(Style.Gap4, mark, what));
        return v;
    }

    Control OriginDetail()
    {
        var bg = Callings.Background(d.Background);
        var v = Style.V(Style.Gap3, DTitle(bg.Name), DSub(bg.Summary), DBody(bg.Story, true), Kit.RuleH(),
            Line("You know", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))));
        foreach (var i in bg.Items)
        {
            var it = Items.Get(i);
            var pic = ItemPhotos.Icon(it.Icon, 40, Style.RarityOf(it.Rarity));
            pic.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var words = Style.V(0, Style.Label(it.Name, Style.UiBold, 16, Style.RarityOf(it.Rarity), false, HorizontalAlignment.Left, false), Style.Label(it.Description, Style.Text, 15, Kit.Dim, true, HorizontalAlignment.Left, false));
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var carried = Style.H(Style.Gap3, pic, words);
            carried.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var l = Style.Label("CARRIES", Style.UiHeavy, 13, Kit.HeadInk, false, HorizontalAlignment.Left, false);
            l.CustomMinimumSize = new Vector2(92, 0);
            l.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            v.AddChild(Style.H(Style.Gap3, l, carried));
        }
        v.AddChild(Kit.RuleH());
        v.AddChild(Kit.Head("What it opens"));
        foreach (var o in bg.Opens) v.AddChild(DBody($"•  {o}"));
        return v;
    }

    Control Summary(Archetype a)
    {
        var bg = Callings.Background(d.Background);
        return Style.V(Style.Gap3, DTitle(d.Name.Trim() == "" ? "Nameless" : d.Name.Trim()), DSub($"{bg.Name} {a.Name}"), DBody(bg.Story, true), Kit.RuleH(),
            Line("Carries", Items.Get(d.WeaponItem).Name + string.Concat(bg.Items.Select(i => $", {Items.Get(i).Name}"))),
            Line("Hands", Abilities.ById(d.Ability).Name),
            Line("Knows", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))), Kit.RuleH(),
            Style.Label("Night is falling on the Low Ford road. The fire is low. What you do from here, the world will remember.", Style.TextItalic, 17, Kit.HeadInk, true, HorizontalAlignment.Center, false));
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
