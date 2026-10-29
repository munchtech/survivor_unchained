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
            var v = Fitted(new Vector2(540, 16), panel == "load" ? 640 : 600);
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
    public string Palette = "steel", Model = "knight", Cloak = "calling", Skin = "fair", Hair = "as_is", HairStyle = "braid";
    /// <summary>A hero's own beard (Lore.Hero's beards: the male hero's), or "".</summary>
    public string BeardStyle = "";
    public bool Headgear = true, Beard = true;
    /// <summary>The survivor is the heroine, unless a man is chosen.</summary>
    public Sex Sex = Sex.Female;
    public double Figure = 1.0;
    /// <summary>Her eyes, the paint on her face, and her face: its sliders
    /// (her own face where none is moved) and the face it started from.</summary>
    public string Eyes = "moss", Paint = "none", FaceShape = "own";
    /// <summary>Her hair's highlights: "" off, "auto" her hair colour's own, or a highlight's id (World.Lore.HighlightColor).</summary>
    public string HairHighlight = "";
    public Dictionary<string, double> Face = new();
    /// <summary>The group last touched, by screen (the calling's: 0 calling, 1 arms, 2 origin, read
    /// closely on the right; the look's: 0 her face's rows, 1 her hair's, framing her for it), and the
    /// face's group of sliders (kept for the data; no sliders are offered).</summary>
    public int Section, FaceGroup;
    /// <summary>Her eyes or her skin chosen by hand this creation (not saved): a face taken after keeps them.</summary>
    public bool EyesPicked, SkinPicked;

    public CreationChoice Choice() => new()
    {
        Name = Name.Trim(), Archetype = Archetype, Background = Background, Palette = Palette, Model = Model, WeaponItem = WeaponItem, Ability = Ability,
        Headgear = Headgear, Cloak = Cloak, Skin = Skin, Hair = Hair, Sex = Sex, HairStyle = HairStyle, Beard = Beard, Figure = Figure,
        // (a hero's own body's face, eyes and paint: Loadouts.HeroKit)
        Face = Loadouts.HeroKit(Sex) != null ? new Dictionary<string, double>(Face) : null,
        Eyes = Loadouts.HeroKit(Sex) != null ? Eyes : null, Paint = Loadouts.HeroKit(Sex) != null ? Paint : null,
        FaceShape = Loadouts.HeroKit(Sex) != null ? FaceShape : null,
        HairHighlight = Sex == Sex.Female && HairHighlight != "" ? HairHighlight : null,
        BeardStyle = Loadouts.HeroKit(Sex) is { Beards.Count: > 0 } && BeardStyle != "" ? BeardStyle : null,
    };

    /// <summary>The figure by the fire is built again when this changes (who
    /// they are, what they wear and hold); a man's hair and skin are his clothes' kit.</summary>
    public string BodyKey => $"{Archetype}|{Model}|{WeaponItem}|{Palette}|{Headgear}|{Cloak}|{Sex}|{Figure}|{Beard}" + (Sex == Sex.Male ? $"|{Skin}|{Hair}|{HairStyle}|{BeardStyle}" : "");

    /// <summary>What the figure looks like: changes when this does (her hair,
    /// skin, eyes, face and paint are changed on her where she stands).</summary>
    public string LookKey => $"{BodyKey}|{Skin}|{Hair}|{HairHighlight}|{HairStyle}|{Eyes}|{Paint}|{FaceShape}|{string.Join(",", Face.OrderBy(f => f.Key).Select(f => $"{f.Key}={f.Value:0.###}"))}";

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
/// Making the survivor, by the fire (the web game's screens/Create.tsx; docs/UI_DESIGN.md 7.2).
/// Two screens, as the owner asked ("pick calling/arms and look/name, just the 2 screens"): the
/// first, who sits here and how they fight (a woman; the man greyed until his own model ships),
/// the calling, the weapon and the art in hand, and the origin, whose traits, things carried and
/// story openings are its own; the second, her look and her name on one page, with no sliders
/// (her face, cut and paint as numbered cycles, her hair's colour, eyes and skin as beads).
/// The figure by the fire changes as you choose, and can be turned (drag, or the right stick)
/// and brought near (the wheel, or the right stick) to her face; the panel on the right reads
/// closely the group last touched, then, on the second screen, who they are.
/// Enter or A on a choice takes it; on the one already taken, it moves on
/// (so A, A walks through); LB and RB turn the screens.
/// </summary>
public partial class CreateScreen : Overlay
{
    public override string Kind => "create";
    public override bool Dismissable => false;
    readonly CreationDraft d;
    static readonly string[] Steps = { "Calling and arms", "Look and name" };
    /// <summary>The two screens: who they are and how they fight, then how they look and their name.</summary>
    public const int CallingStep = 0, LookStep = 1;
    static readonly Dictionary<string, string> ClassGlyph = new() { ["warden"] = "shield", ["reaver"] = "axe", ["arcanist"] = "staff", ["stalker"] = "bow" };
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
        G.FigureArms(d.Step != LookStep);
        // A new screen or row frames the figure for it (the look's rows come near: her hair, her face);
        // a new cut turns her so it shows (a braid down her back is seen from behind).
        if (d.Step != step || d.Section != section || d.HairStyle != cut) G.FrameFigure(SectionZoom(), SectionTurn());
        Refresh();
    }

    /// <summary>To a screen: its first group (the calling; her face, near).</summary>
    void Go(int step) => Set(() =>
    {
        step = Math.Clamp(step, CallingStep, LookStep);
        if (step != d.Step) { d.Step = step; d.Section = 0; }
    });

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
            Set(() => { d.Step = LookStep; d.Name = Names[Random.Shared.Next(Names.Length)]; });
            Nav.FocusId = "begin";
            return;
        }
        G.BeginJourney(d.Choice());
    }

    /// <summary>Each screen's question, the title over its column: the world asks them again later.</summary>
    string Question => d.Step == CallingStep ? "Who sits here?" : Her ? "Who is she?" : "Who is he?";

    /// <summary>The two panels' width and their inset from the screen's edges: the choices on the
    /// left, what the one taken means on the right, mirrored, the figure standing between them.</summary>
    const float PanelW = 560, Inset = 16;

    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        // The figure between the panels: dragged, she turns; the wheel brings her near.
        AddChild(Stage());
        // The left panel: the screens on their chain, the screen's question, the choices, the way on.
        var col = Solid(Fitted(new Vector2(Inset, Inset), PanelW));
        // (the screens are turned with LB and RB, or [ and ], drawn at the chain's ends)
        var steps = new ChainTabs(Steps.Select(s => (s, "")).ToArray(), d.Step, k => { if (k != d.Step) { Sound.Sfx.Page(); Go(k); } },
            (G.Key(Act.TabPrev), G.Key(Act.TabNext)), 20) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        col.AddChild(steps);
        var head = Style.V(2, new Title(Question, 30, false),
            Style.Label("By the fire on the Low Ford road", Style.TextItalic, 17, Kit.HeadInk, false, HorizontalAlignment.Center, false));
        col.AddChild(head);
        if (d.Step == CallingStep) col.AddChild(Calling(a));
        else
        {
            // (from the pad, the look starts at her face; the keyboard types her name at once)
            Nav.Prefer = "cycle:face";
            col.AddChild(Look());
        }
        col.AddChild(Foot());
        // The right panel, its twin: what the group last touched means, read closely; then who they are.
        var right = Solid(Fitted(new Vector2(1920 - Inset - PanelW, Inset), PanelW));
        right.AddChild(d.Step == CallingStep ? d.Section switch { 1 => ArmsDetail(), 2 => OriginDetail(), _ => CallingDetail(a) } : LookDetail(a));
        // Who they are becoming, set on the ground at the figure's feet (not by her face: the name's field shows it).
        if (d.Step == CallingStep) AddChild(Nameplate(a));
    }

    /// <summary>Creation's panels nearly opaque (about 0.95, over the house's 0.84): the bright world by the
    /// fire showed through them behind the choices. A dark ground under the painted one, inside its edge.</summary>
    VBoxContainer Solid(VBoxContainer col)
    {
        if (col.GetParent() is not Control panel) return col;
        panel.SelfModulate = Colors.White;
        var under = new Panel { MouseFilter = MouseFilterEnum.Ignore };
        under.AddThemeStyleboxOverride("panel", new StyleBoxFlat { BgColor = Kit.Ground with { A = 0.5f }, CornerRadiusTopLeft = 4, CornerRadiusTopRight = 4, CornerRadiusBottomLeft = 4, CornerRadiusBottomRight = 4 });
        AddChild(under);
        MoveChild(under, panel.GetIndex());
        void Fit() { under.Position = panel.Position + new Vector2(4, 4); under.Size = panel.Size - new Vector2(8, 8); }
        panel.Resized += Fit;
        Fit();
        return col;
    }

    /// <summary>The panel's foot: back (or leave) and the way on, each its key and its word, at
    /// either end; from the calling, the way on names what the next screen holds, so no one walks past it.</summary>
    Control Foot()
    {
        var back = Kit.Keyed(Act.Cancel, d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Go(d.Step - 1); else G.CancelCreation(); });
        Nav.Id(back, "back");
        var on = d.Step < LookStep ? Nav.Id(Kit.Keyed(Act.Confirm, $"Next: {Their.ToLowerInvariant()} look and name", () => Go(d.Step + 1), Style.EmberHi), "next")
            : Nav.Id(Kit.Keyed(Act.Confirm, "Begin the journey", Begin, Style.EmberHi), "begin");
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
        // (its focus rings its mark, glyph and words, not the column's width)
        Nav.Framed(b, row, icon);
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

    /// <summary>The first screen: who sits here (a woman or a man: the first thing anyone asks), how
    /// they fight (the calling, then the weapon and the art in hand), and where they are from.</summary>
    Control Calling(Archetype a)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(SexRow());
        v.AddChild(Style.Gap(Style.Gap1));
        foreach (var (id, c) in Callings.Archetypes)
            v.AddChild(Choice(ClassGlyph.GetValueOrDefault(id, "sword"), c.Name, c.Tagline, d.Archetype == id, () => Set(() => { d.Section = 0; ChooseArchetype(id); })));
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Arms(a));
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Origin());
        // (the height of the weapon rows a calling lacks, kept here at the foot so the frame and foot stay put)
        if (a.Weapons.Count < 3) v.AddChild(Style.Gap((3 - a.Weapons.Count) * weaponRowH));
        return v;
    }

    /// <summary>A woman, or a man: his own body is still to come, so he is shown greyed with "coming
    /// later" under him as a calling's line is, never pressed nor come to by the keys; no picture of
    /// him. The pair centred on the panel's middle.</summary>
    Control SexRow()
    {
        var woman = Nav.Loud(Nav.Underlined(Nav.Id(Kit.Tab("A woman", Her, () => { if (!Her) Set(() => d.SetSex(Sex.Female)); }, 19, 0.6f), "sex:Female")));
        var man = Kit.Tab("A man", !Her, () => { }, 19);
        man.Disabled = true;
        man.MouseFilter = MouseFilterEnum.Ignore;
        man.MouseDefaultCursorShape = CursorShape.Arrow;
        man.AddThemeColorOverride("font_disabled_color", Kit.Dim);
        man.Modulate = Colors.White with { A = 0.45f };
        man.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        Nav.Skip(man);
        var later = Style.Label("coming later", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false);
        // (the tab's foot leaves room for an underline it never has: its line tucks up under the word)
        var him = Style.V(-8, man, later);
        // (each word in a cell as wide as the other's, so the pair's middle is the panel's middle)
        float w = Math.Max(woman.GetCombinedMinimumSize().X, Math.Max(man.GetCombinedMinimumSize().X, later.GetCombinedMinimumSize().X)) + 8;
        var left = new HBoxContainer { CustomMinimumSize = new Vector2(w, 0), Alignment = BoxContainer.AlignmentMode.Center, MouseFilter = MouseFilterEnum.Ignore };
        left.AddChild(woman);
        woman.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        him.CustomMinimumSize = new Vector2(w, 0);
        var row = Style.H(40, left, him);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        return row;
    }

    /// <summary>Where a list's words begin (past its mark and glyph): the word rows and their lines align to it.</summary>
    const int TextEdge = 74;

    /// <summary>The arms: the calling's weapons as its rows (room kept for three, so the rows under them
    /// never move between callings), and the four arts it starts with as words, the one in hand's kind and
    /// pace under them (the right panel reads both closely).</summary>
    float weaponRowH;

    Control Arms(Archetype a)
    {
        var v = Style.V(Style.Gap2, Kit.Head("Weapon"));
        weaponRowH = 0;
        foreach (var id in a.Weapons)
        {
            var it = Items.Get(id);
            var w = it.Weapon != null ? Weapons.All.GetValueOrDefault(it.Weapon.Id) : null;
            var r = Choice(it.Icon, it.Name, w != null ? $"{w.Name} · {w.School.ToString().ToLowerInvariant()}" : "", d.WeaponItem == id, () => Set(() => { d.Section = 1; d.WeaponItem = id; }),
                w != null ? ItemViews.SchoolColors[w.School] : null);
            weaponRowH = r.CustomMinimumSize.Y;
            v.AddChild(r);
        }
        v.AddChild(Style.Gap(Style.Gap1));
        v.AddChild(Kit.Head("Art in hand"));
        v.AddChild(Flow(ArtBook.Starting(a.Id).Select(id => (Abilities.ById(id).Name, d.Ability == id, (Action)(() => Set(() => { d.Section = 1; d.Ability = id; })), $"art:{id}"))));
        var ab = Abilities.ById(d.Ability);
        v.AddChild(Note($"{(ab.Movement ? "A way of moving" : "The calling's own")} · {ab.Cooldown} s{(ab.Interrupts ? " · breaks channels" : "")}"));
        return v;
    }

    /// <summary>Where they are from, as words, the one chosen in a line under them.</summary>
    Control Origin() => Style.V(Style.Gap2, Kit.Head("Origin"),
        Flow(Callings.Backgrounds.Select(p => (p.Value.Name, d.Background == p.Key, (Action)(() => { var id = p.Key; Set(() => { d.Section = 2; d.Background = id; }); }), $"origin:{p.Key}"))),
        Note(Callings.Background(d.Background).Summary));

    /// <summary>A chosen word's line, quiet italic under its words, from the lists' text edge.</summary>
    static Control Note(string text) => Indent(Style.Label(text, Style.TextItalic, 16, Kit.Dim, true, HorizontalAlignment.Left, false));

    /// <summary>Set in from the panel's edge to the lists' text edge.</summary>
    static MarginContainer Indent(Control c)
    {
        var m = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
        m.AddThemeConstantOverride("margin_left", TextEdge);
        m.AddChild(c);
        return m;
    }

    /// <summary>Words to choose between, as the house's tabs from the lists' text edge, each with its focus
    /// id; focused, an ember line under the word, not a box.</summary>
    static Control Flow(IEnumerable<(string Text, bool On, Action Press, string Id)> words)
    {
        var list = words.ToList();
        var f = Kit.TabFlow(list.Select(w => (w.Text, w.On, w.Press)), 17, 26, 4, 0.6f);
        f.Alignment = FlowContainer.AlignmentMode.Begin;
        int i = 0;
        foreach (var b in f.GetChildren().OfType<Button>()) Nav.Loud(Nav.Underlined(Nav.Id(b, list[i++].Id)));
        return Indent(f);
    }

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

    Control CallingDetail(Archetype a)
    {
        // (what the left does not list: the four arts they start with, and what the origin chosen gives)
        var bg = Callings.Background(d.Background);
        return Style.V(Style.Gap3,
            DTitle(a.Name), DSub(a.Tagline), DBody(a.Description), Kit.RuleH(),
            Ledger(($"{a.Base.MaxHealth:0}", "Health"), ($"{a.Base.Armor:0}", "Armor"), ($"{a.Base.MoveSpeed:0.0}", "Speed"), ($"{a.Base.CritChance * 100:0}%", "Precision")),
            Kit.RuleH(),
            Line("Arts", string.Join(" · ", ArtBook.Starting(a.Id).Select(x => Abilities.ById(x).Name))),
            Line("Carries", string.Join(" · ", bg.Items.Select(i => Items.Get(i).Name))),
            Line("Knows", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))));
    }

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
        var name = Style.H(Style.Gap2, Style.Label(ab.Name.ToUpperInvariant(), Style.Display, 18, Kit.Ink, false, HorizontalAlignment.Left, false), Style.Prompt(Act.Flare));
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

    VBoxContainer Summary(Archetype a)
    {
        var bg = Callings.Background(d.Background);
        return Style.V(Style.Gap3, DTitle(d.Name.Trim() == "" ? "Nameless" : d.Name.Trim()), DSub($"{bg.Name} {a.Name}"), DBody(bg.Story, true), Kit.RuleH(),
            Line("Carries", Items.Get(d.WeaponItem).Name + string.Concat(bg.Items.Select(i => $", {Items.Get(i).Name}"))),
            Line("In hand", Abilities.ById(d.Ability).Name),
            Line("Knows", string.Join(", ", bg.Knowledge.Select(k => SheetScreen.Know.GetValueOrDefault(k, k)))), Kit.RuleH(),
            Style.Label("Night is falling on the Low Ford road. The fire is low. What you do from here, the world will remember.", Style.TextItalic, 17, Kit.HeadInk, true, HorizontalAlignment.Center, false));
    }

    public override bool Key(Act a)
    {
        if (nameBox != null && nameBox.HasFocus())
        {
            // Typing a name: the letters are the name's, not the menu's (W, S and Backspace among them);
            // the arrows up and down and Tab leave the name for the row beside it, left and right stay
            // in the text, Escape only lets the name go, Enter begins.
            bool Held(Godot.Key k) => Input.IsPhysicalKeyPressed(k);
            if (a is Act.Up or Act.Down && (Held(Godot.Key.Up) || Held(Godot.Key.Down)) || a == Act.Inventory && Held(Godot.Key.Tab))
            {
                nameBox.ReleaseFocus();
                Nav.KeyMode = true;
                Nav.FocusId = "name";
                Nav.Key(a == Act.Up ? Act.Up : Act.Down);
                return true;
            }
            if (a == Act.Confirm) { nameBox.ReleaseFocus(); Begin(); return true; }
            if (a == Act.Cancel && Held(Godot.Key.Escape)) nameBox.ReleaseFocus();
            return true;
        }
        if (a == Act.TabNext) { Go(d.Step + 1); return true; }
        if (a == Act.TabPrev) { Go(d.Step - 1); return true; }
        if (a == Act.Cancel) { if (d.Step > 0) Go(d.Step - 1); else G.CancelCreation(); return true; }
        if (a == Act.Confirm)
        {
            // On a choice not yet taken, Enter or A takes it (focus does it); otherwise, onward.
            if (Nav.KeyMode && Nav.Current is { } c && !c.C.HasMeta("on")) return false;
            if (d.Step < LookStep) Go(d.Step + 1); else Begin();
            return true;
        }
        return false;
    }
}
