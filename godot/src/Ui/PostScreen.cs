using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>A lit lamp-post's menu (Play/PostMenu.cs has what it offers and its gates): Travel, World tier, Lamps, Leave, as
/// the pause menu's column of lines (MenuList), on a fitted panel at the left. Functional only: its look is the UI lead's.</summary>
public partial class PostScreen : Overlay
{
    public override string Kind => "post";
    readonly LampPosts.Post post;
    readonly MenuList menu;
    /// <summary>"" (the menu), "travel", "tier" or "unions".</summary>
    string page = "";

    public PostScreen(Game g, LampPosts.Post post) : base(g)
    {
        this.post = post;
        menu = new MenuList(Refresh, 20);
    }

    protected override void Build()
    {
        HideHud();
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
