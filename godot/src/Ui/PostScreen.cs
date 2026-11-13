using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>A lit lamp-post's menu (Play/PostMenu.cs has what it offers and its gates): Travel, World tier, Lamps, Leave, as
/// the pause menu's column of lines (MenuList), on a fitted panel at the left. Functional only: its look is the UI lead's.</summary>
public partial class PostScreen : Overlay
{
    public override string Kind => "post";
    readonly LampPosts.Post post;
    readonly MenuList menu;
    /// <summary>"" (the menu), "travel", "tier", "unions" or "road".</summary>
    string page = "";

    public PostScreen(Game g, LampPosts.Post post) : base(g)
    {
        this.post = post;
        menu = new MenuList(Refresh, 20);
        // (bd-ui2) --post-page road: the post opens straight on that page (pictures of the road page).
        if (Args.Get("post-page") is "road" or "travel" or "tier" or "unions") page = Args.Get("post-page")!;
    }

    protected override void Build()
    {
        HideHud();
        if (page == "road") { RoadPage(); return; }
        var col = Fitted(new Vector2(Inset, Inset), 720);
        col.AddChild(new Title(post.Name, 30, false));
        var w = G.Journey.World;
        var tier = WorldTiers.Get(WorldTiers.Of(w));
        // (M5 r4: the tier only once the tier rows are offered, PostMenu.FullMenu: "World tier II" at 2.7 minutes meant nothing)
        string sub = PostMenu.FullMenu(w) ? $"{PostMenu.ZoneName(post.Zone)}  ·  World tier {tier.Name}" : PostMenu.ZoneName(post.Zone);
        col.AddChild(Style.Label(sub, Style.TextItalic, 17, Kit.HeadInk, false, HorizontalAlignment.Center, false));
        col.AddChild(Kit.RuleH());
        menu.Items.Clear();
        if (page == "travel")
        {
            foreach (var grp in PostMenu.Travel(w, post))
                foreach (var p in grp.Posts)
                {
                    var to = p;
                    menu.Add(p.Name, () => G.PostTravel(post, to), grp.Name);
                }
            menu.Add("Back", Back);
        }
        else if (page == "tier")
        {
            foreach (var t in PostMenu.Tiers(w))
            {
                int n = t.N;
                string label = t.Current ? $"{t.Name}  (now)" : t.Open ? t.Name : $"{t.Name}  (locked)";
                menu.Add(label, () =>
                {
                    if (!t.Open) { G.Toast(new Toast(ToastKind.Warning, t.Opens ?? "Not yet open")); return; }
                    if (!t.Current) G.PostTier(n);
                    page = ""; menu.Focus = 0; Refresh();
                }, t.Open ? t.Numbers : t.Opens, t.Current);
            }
            menu.Add("Back", Back);
        }
        else if (page == "unions")
        {
            // (bd-sockets) A plain list: each Union joined or not, its price the first time; the look is bd-ui's.
            foreach (var l in PostMenu.Unions(G.Journey.Ch))
            {
                string id = l.Union.Id;
                string label = l.Joined ? $"{l.Union.Name}  (joined)" : l.Union.Name;
                string note = l.Refused ?? (l.Joined ? "Unjoin: free" : l.Price > 0 ? $"Join: {l.Price} rare items, once" : "Join: free");
                menu.Add(label, () => G.PostUnion(post, id), note, l.Joined);
            }
            menu.Add("Back", Back);
        }
        else
        {
            foreach (var (opt, refused) in PostMenu.Options(w, G.Battle, post, G.Journey.Ch))
                switch (opt)
                {
                    case PostMenu.Option.Rest:
                        menu.Add("Rest", () => { if (refused != null) G.Toast(new Toast(ToastKind.Warning, refused)); else G.PostRest(post); }, refused ?? "You will rise here");
                        break;
                    case PostMenu.Option.Travel:
                        menu.Add("Travel", () => Go("travel", refused), refused ?? "To another lamp you have lit");
                        break;
                    case PostMenu.Option.Tier:
                        menu.Add("World tier", () => Go("tier", null), tier.Name);
                        break;
                    case PostMenu.Option.Road:
                        bool due = LampBook.Roadless(G.Journey.Ch);
                        menu.Add(due ? "Choose your road" : "Road", () => Go("road", refused), refused ?? (due ? "Two roads lie open to you" : $"{LampBook.Walked(G.Journey.Ch)?.Name}: change it, free"));
                        break;
                    case PostMenu.Option.Lamps:
                        menu.Add("Lamps", () => { if (refused != null) G.Toast(new Toast(ToastKind.Warning, refused)); else G.PostLamps(post); }, refused ?? "Put lamps out, change layouts");
                        break;
                    case PostMenu.Option.Unions:
                        menu.Add("Unions", () => Go("unions", refused), refused ?? "Join two skills as one");
                        break;
                    default:
                        menu.Add("Leave", G.CloseOverlay);
                        break;
                }
        }
        menu.Focus = System.Math.Clamp(menu.Focus, 0, menu.Items.Count - 1);
        var list = menu.Build();
        list.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        col.AddChild(list);
    }

    /* ------------------------------------------------------------- road -- */

    /// <summary>(bd-ui2) The road page: her calling's roads side by side (RoadPageModel has the data), the one walked tagged
    /// and bright-bordered, the other with "Walk this road" held (a change at a lamp-post: LampBook's own, Game.PostRoad).</summary>
    void RoadPage()
    {
        var ch = G.Journey.Ch;
        var pg = RoadPageModel.Of(ch);
        const float PW = 560;
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        centre.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        AddChild(centre);
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        centre.AddChild(panel);
        var root = Style.V(Style.Gap3);
        panel.AddChild(root);
        root.AddChild(new Title(LampBook.Roadless(ch) ? "Choose your road" : "Your road", 30, false));
        root.AddChild(Style.Label(post.Name, Style.TextItalic, 17, Kit.HeadInk, false, HorizontalAlignment.Center, false));
        var row = Style.H(24);
        root.AddChild(row);
        foreach (var r in pg.Roads) row.AddChild(RoadPanelOf(r, pg, PW));
        root.AddChild(Kit.RuleH());
        root.AddChild(Style.Label(RoadPageModel.Foot, Style.Text, 18, Kit.Ink, true, HorizontalAlignment.Center, false));
        var back = Kit.Word("Back", Back, Kit.Ink, 20);
        back.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        root.AddChild(back);
    }

    Control RoadPanelOf(RoadPageModel.RoadPanel r, RoadPageModel.Page pg, float width)
    {
        var panel = new PanelContainer { CustomMinimumSize = new Vector2(width, 0), MouseFilter = MouseFilterEnum.Stop };
        var sb = new StyleBoxFlat { BgColor = new Color(0, 0, 0, 0.22f), BorderColor = r.Walked ? Style.GoldHi : Kit.Faint };
        sb.SetBorderWidthAll(r.Walked ? 2 : 1);
        sb.SetCornerRadiusAll(3);
        sb.SetContentMarginAll(18);
        panel.AddThemeStyleboxOverride("panel", sb);
        var v = Style.V(Style.Gap3);
        panel.AddChild(v);
        var top = Style.H(10, new Title(r.Name, 24, false));
        v.AddChild(top);
        if (r.Walked) v.AddChild(Style.Label("WALKED", Style.UiHeavy, 14, Style.EmberHi));
        v.AddChild(Style.Label(r.Line, Style.TextItalic, 17, Kit.HeadInk, true));
        v.AddChild(Kit.RuleH());
        if (r.RoadSkill is { } rs) v.AddChild(Entry("Teaches", rs, SkillName(rs), SkillText(rs), GlyphOfSkill(rs)));
        if (r.Strike is { } st) v.AddChild(Entry("Flare Strike", st.Id, st.Name, st.Text, Glyphs.IconKey(st.Icon)));
        if (r.Stand is { } sd) v.AddChild(Entry("Stand", sd.Id, sd.Name, sd.Text, Glyphs.IconKey(sd.Icon)));
        v.AddChild(Style.SubLabel("Leans toward"));
        var lean = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
        lean.AddThemeConstantOverride("h_separation", 18);
        lean.AddThemeConstantOverride("v_separation", 4);
        foreach (var id in r.Leaning)
        {
            var c = Style.H(6, Glyphs.Icon(GlyphOfSkill(id), 22, Style.GoldHi, true), Style.Label(SkillName(id), Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false));
            c.MouseFilter = MouseFilterEnum.Stop;
            c.TooltipText = $"{SkillName(id)}: {SkillText(id)}";
            lean.AddChild(c);
        }
        v.AddChild(lean);
        v.AddChild(Kit.RuleH());
        if (!pg.Open) v.AddChild(Style.Label(pg.Gate, Style.TextItalic, 17, Kit.Faint));
        else if (!r.Walked)
        {
            string id = r.Id;
            var held = new HoldPad("Hold to walk this road", () => { G.PostRoad(post, id); Refresh(); }, true, 240);
            held.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            Nav.Mark(held, $"road:{id}", held.Nudge);
            v.AddChild(held);
        }
        return panel;
    }

    /// <summary>A labelled line: the small caption, then its glyph and name, then the words from data under it.</summary>
    static Control Entry(string caption, string id, string name, string text, string glyph)
    {
        var v = Style.V(2);
        v.AddChild(Style.SubLabel(caption));
        v.AddChild(Style.H(8, Glyphs.Icon(glyph, 22, Style.GoldHi, true), Style.Label(name, Style.UiBold, 18, Kit.Ink, false, HorizontalAlignment.Left, false)));
        if (text != "") v.AddChild(Style.Label(text, Style.Ui, 15, Kit.Ink2, true));
        return v;
    }

    static string SkillName(string id) => Weapons.All.TryGetValue(id, out var w) ? w.Name : id;
    static string SkillText(string id) => Weapons.All.TryGetValue(id, out var w) ? w.Description : "";
    static string GlyphOfSkill(string id) => Weapons.All.TryGetValue(id, out var w) ? Glyphs.ForSkill(w.Id, w.Art) : Glyphs.IconKey(id);

    const float Inset = 16;

    void Go(string to, string? refused)
    {
        if (refused != null) { G.Toast(new Toast(ToastKind.Warning, refused)); return; }
        page = to; menu.Focus = 0; Refresh();
    }

    void Back() { page = ""; menu.Focus = 0; Refresh(); }

    public override bool Key(Act a)
    {
        if (page != "" && a is Act.Cancel or Act.Pause) { Back(); return true; }
        return menu.Key(a);
    }
}
