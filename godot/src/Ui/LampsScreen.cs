using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

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
    public override float CameraShift => -330;
    public override float CameraNear => 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => BookFrame;

    /// <summary>The tab is on the chain (v2, not --board).</summary>
    public static bool On => Lamps.V2 && !ArtsScreen.BoardOn;

    /// <summary>The height Arts' page-name row and its gap took (measured: the board's window at y 234).</summary>
    const float Room = 27;

    LampPage? page;
    /// <summary>The visit outlives a rebuild: the lamps lit since the book opened go out anywhere until it closes (§9).</summary>
    LampSession? visit;

    public LampsScreen(Game g) : base(g) { }

    bool Safe => G.Battle is not { Combat: true };

    public override bool Key(Act a) => page != null && IsInstanceValid(page) && page.Key(a);

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var v = BookPanel(null);
        // C's rows are placed from the content rect's top (y 152 at 1080), under the row Arts' page names take: the
        // same row, unseen, keeps the page where the mock has it
        v.AddChild(new Control { CustomMinimumSize = new Vector2(0, Room), MouseFilter = MouseFilterEnum.Ignore });
        LampBoard.Demo(ch, G.Journey.World);
        if (visit != null && visit.Layout != LampBook.State(ch).Active) visit = null;
        page = new LampPage(ch, G.Journey.World, G.Zone?.Id, visit, Safe) { CustomMinimumSize = new Vector2(0, LampPage.Height) };
        visit = page.Visit;
        v.AddChild(page);
    }
}
