using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The day's book's Lamps tab (v2; docs/design/LAMPS_SCREEN_BRIEF.md §10 "Where it opens from", §16 "Input in the book"):
/// direction C's page (LampPage: the header, the board, the wick tabs and panel, the prompt row) on the book's panel,
/// after Arts on the chain. L opens it; LB/RB turn the book's tabs as everywhere. --board keeps the old functional
/// Lamps and Wicks pages in Arts instead.
/// </summary>
public partial class LampsScreen : Overlay
{
    public override string Kind => "lamps";
    public override Act? Toggle => Act.Lamps;
    // (A, Open wide: the book's camera shift and frame go, the play camera holds)
    public override float CameraShift => wide ? 0 : -330;
    public override float CameraNear => wide ? 1 : 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => wide ? null : BookFrame;

    /// <summary>A, Open wide (§4, §12 A, §16): R3 / Z in C; R3 / Z / B in A goes back. --lamps-wide opens on it.</summary>
    bool wide = SurvivorUnchained.Args.Has("lamps-wide");
    LampGrade? grade;
    HerMask? her;
    /// <summary>A's open and close on LampMotion's clock (§11): the grade in over 0.35 s and the page's chrome over
    /// 0.25 s (the board has its own); the close, all of it out over 0.2 s, then the book's page.</summary>
    double openAt = -1, closeAt = -1;
    bool Closing => closeAt >= 0;

    /// <summary>The tab is on the chain (v2, not --board).</summary>
    public static bool On => Lamps.V2 && !ArtsScreen.BoardOn;

    /// <summary>The height Arts' page-name row and its gap took (measured: the board's window at y 234).</summary>
    const float Room = 27;

    LampPage? page;
    /// <summary>The visit outlives a rebuild: the lamps lit since the book opened go out anywhere until it closes (§9).</summary>
    LampSession? visit;

    public LampsScreen(Game g) : base(g)
    {
        TreeExiting += () =>
        {
            if (wide) G.Hud.LampsWide(false);
            if (grade != null && IsInstanceValid(grade)) grade.QueueFree();
            if (her != null && IsInstanceValid(her)) her.QueueFree();
        };
    }

    // (--lamps-measure / --lamps-moves: the worst frame over the 20 after an open or a toggle, the hitch check)
    ulong lastTick;
    int probe;
    double worst;
    public override void _Process(double delta)
    {
        ulong now = Time.GetTicksUsec();
        double d = lastTick == 0 ? 0 : (now - lastTick) / 1000.0;
        lastTick = now;
        Motion();
        if (probe <= 0) return;
        worst = System.Math.Max(worst, d);
        if (--probe == 0) GD.Print($"LAMPWIDE open hitch: worst frame {worst:F1} ms over 20 frames ({(wide ? "A" : "C")}, knock built in {LampKnock.BuildMs:F1} ms)");
    }

    void Probe() { if (SurvivorUnchained.Args.Has("lamps-measure") || SurvivorUnchained.Args.Has("lamps-moves")) { probe = 20; worst = 0; } }

    void Motion()
    {
        double t = LampMotion.Now;
        if (Closing)
        {
            float a = 1 - (float)System.Math.Clamp((t - closeAt) / 0.2, 0, 1);
            if (grade != null && IsInstanceValid(grade)) grade.Amount = a;
            if (page != null && IsInstanceValid(page)) page.ChromeAlpha(a);
            if (a <= 0) { closeAt = -1; Back(); }
            return;
        }
        if (openAt < 0 || !wide) return;
        float g = (float)System.Math.Clamp((t - openAt) / 0.35, 0, 1), c = LampMotion.EaseOut((t - openAt) / 0.25);
        if (grade != null && IsInstanceValid(grade)) grade.Amount = g;
        if (page != null && IsInstanceValid(page)) page.ChromeAlpha(c);
        if (g >= 1 && c >= 1) openAt = -1;
    }

    void ToggleWide()
    {
        if (Closing) return;
        if (wide)
        {
            // A to the book: the reverse of the open over 0.2 s, no stagger, then the page switches back
            Sound.Sfx.Page();
            closeAt = LampMotion.Now;
            openAt = -1;
            if (page != null && IsInstanceValid(page)) page.Board.PlayClose();
            return;
        }
        Probe();
        wide = !wide;
        Sound.Sfx.Page();
        G.Hud.LampsWide(wide, SkillBook.Carried(G.Journey.Ch).Where(c => Weapons.All.ContainsKey(c.Id)).Take(6));
        G.Reframe(this);
        Refresh();
    }

    /// <summary>The close has run: the book's page (C) again.</summary>
    void Back()
    {
        Probe();
        wide = false;
        G.Hud.LampsWide(false, SkillBook.Carried(G.Journey.Ch).Where(c => Weapons.All.ContainsKey(c.Id)).Take(6));
        G.Hud.ShowPlay(false);
        if (grade != null && IsInstanceValid(grade)) grade.QueueFree();
        grade = null;
        her?.QueueFree(); her = null;
        G.Reframe(this);
        Refresh();
    }

    /// <summary>A's wick panel from the HUD's geometry (§16): between the statues if the gap between their inner edges
    /// across its height is at least its width + 48 px, else above both heads at 780 px, its bottom 24 px above the higher
    /// head's top, centered on the bar.</summary>
    public static Rect2 WickRect()
    {
        const float Wd = 780, Ht = 282;
        _ = LampKnock.Hud;
        float plateTop = HudBottom.MapY(DgPanel.TopY);
        var (gl, gr) = LampKnock.InnerEdges(plateTop - 24 - Ht, plateTop - 24);
        Rect2 r;
        if (gr - gl >= Wd + 48) r = new Rect2(Mathf.Round((gl + gr) / 2 - Wd / 2), plateTop - 24 - Ht, Wd, Ht);
        else r = new Rect2(Mathf.Round(HudBottom.MapX(960) - Wd / 2), Mathf.Round(LampKnock.HeadsTop - 24 - Ht), Wd, Ht);
        GD.Print($"LAMPWIDE wick panel: {r.Position.X:F0},{r.Position.Y:F0} {r.Size.X:F0}x{r.Size.Y:F0} (HUD scale {HudBottom.Scale:F2}, inner gap {gl:F0}-{gr:F0}, heads top {LampKnock.HeadsTop:F0})");
        return r;
    }

    bool Safe => G.Battle is not { Combat: true };

    public override bool Key(Act a) => Closing || (page != null && IsInstanceValid(page) && page.Key(a));

    protected override void Build()
    {
        if (wide) { BuildWide(); return; }
        var ch = G.Journey.Ch;
        var v = BookPanel(null);
        // C's rows are placed from the content rect's top (y 152 at 1080), under the row Arts' page names take: the
        // same row, unseen, keeps the page where the mock has it
        v.AddChild(new Control { CustomMinimumSize = new Vector2(0, Room), MouseFilter = MouseFilterEnum.Ignore });
        LampBoard.Demo(ch, G.Journey.World);
        if (visit != null && visit.Layout != LampBook.State(ch).Active) visit = null;
        page = new LampPage(ch, G.Journey.World, G.Zone?.Id, visit, Safe) { CustomMinimumSize = new Vector2(0, LampPage.Height) };
        visit = page.Visit;
        page.OpenWide += ToggleWide;
        v.AddChild(page);
    }

    void BuildWide()
    {
        var ch = G.Journey.Ch;
        LampBoard.Demo(ch, G.Journey.World);
        if (visit != null && visit.Layout != LampBook.State(ch).Active) visit = null;
        G.Hud.LampsWide(true, SkillBook.Carried(ch).Where(c => Weapons.All.ContainsKey(c.Id)).Take(6));
        var seats = new System.Collections.Generic.List<Vector2>();
        int n = System.Math.Min(6, SkillBook.Carried(ch).Count(c => Weapons.All.ContainsKey(c.Item1)));
        for (int i = 0; i < n; i++) seats.Add(HudBottom.Map(DgPanel.Seat(i)));
        seats.Add(HudBottom.Map(DgPanel.GlassAt));
        bool night = G.Journey.World?.Time == TimeOfDay.Night;
        var vp = (Vector2)GetTree().Root.Size;
        if (her == null && !HerMask.Off) { her = new HerMask(); G.AddChild(her); }
        if (grade == null)
        {
            grade = new LampGrade(night);
            G.AddChild(grade);
            openAt = LampMotion.Now;
        }
        page = new LampPage(ch, G.Journey.World, G.Zone?.Id, visit, Safe, true, WickRect(), seats) { Position = Vector2.Zero, Size = new Vector2(1920, 1080) };
        visit = page.Visit;
        page.OpenWide += ToggleWide;
        var board = page.Board;
        var vf = vp / new Vector2(1920, 1080);
        board.Knock(LampKnock.Hud, her?.Texture, vp);
        board.Keep = LampKnock.Boxes.Select(b => new Box(b.X0, b.Y0 - LampPage.FieldTop, b.X1, b.Y1 - LampPage.FieldTop)).ToList();
        grade.Field(new Vector4(0, LampPage.FieldTop * vf.Y, vp.X, LampPage.FieldBottom * vf.Y), new Vector4(0, 40 * vf.Y, 0, 60 * vf.Y), vp, LampKnock.Hud, null);
        var g2 = grade;
        board.Relaid += () => { if (IsInstanceValid(g2)) g2.Pools(board.LitScreen(), board.IsValley); };
        // (in the tree only now: the board builds on entering, with its knockout and keep-outs set)
        AddChild(page);
        // (debug --lamps-noboard: the graded world alone, for the night's luma outside the pools)
        if (SurvivorUnchained.Args.Has("lamps-noboard")) foreach (var c in board.GetChildren()) if (c is CanvasItem ci) ci.Visible = false;
        // (the chrome and the grade start with the board's open, after the build)
        if (openAt >= 0) { openAt = LampMotion.Now; page.ChromeAlpha(0); }
    }
}
