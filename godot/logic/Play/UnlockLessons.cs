using System;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Play;

/* The lesson after a level-up card (data/content/unlock_cards.json, each row's teach): a card says what opened; the first fight
 * after it says how it plays, once. Pure (the tests compile it): the HUD feeds it when a card is queued (Opened), each frame
 * whether a fight is near (Tick) and the press of the key or the swap (Used); it hands back the row to teach and the HUD sets
 * the hint. A row is taught at most once per character: `taught` and `mark` are the character's own record (World.Facts
 * "lesson.<id>"). Only next_fight rows teach: an auto fires by itself (first_fire says nothing) and the road has no lesson. */
public sealed class UnlockLessons
{
    /// <summary>A fight that is already near this long after the card is the next fight, though it never left.</summary>
    public const double NearAfter = 3.0;

    readonly Func<string, bool> taught;
    readonly Action<string> mark;
    UnlockCard? waiting, showing;
    bool sawFar;
    double since;

    public UnlockLessons(Func<string, bool> taught, Action<string> mark) { this.taught = taught; this.mark = mark; }

    /// <summary>The row waiting for a fight, null none.</summary>
    public UnlockCard? Waiting => waiting;
    /// <summary>The row whose hint is up, null none.</summary>
    public UnlockCard? Showing => showing;

    /// <summary>Its card is queued: a key or stance row that teaches at the next fight now waits for one.</summary>
    public void Opened(UnlockCard row)
    {
        if (row.Start || !row.Teach.NextFight || taught(row.Id)) return;
        waiting = row; sawFar = false; since = 0;
    }

    /// <summary>One frame: whether a fight is near her, dt since the last. The row to teach now (once), else null: a fight
    /// near after one that was not, or already near NearAfter seconds after the card.</summary>
    public UnlockCard? Tick(bool fightNear, double dt = 0)
    {
        if (waiting == null) return null;
        since += dt;
        if (!fightNear) { sawFar = true; return null; }
        if (!sawFar && since < NearAfter) return null;
        showing = waiting; waiting = null;
        mark(showing.Id);
        return showing;
    }

    /// <summary>She pressed that key's skill (a skill's id), or swapped ("stance"): the lesson is no longer owed. True when its
    /// hint was up, so the caller takes it down.</summary>
    public bool Used(string id)
    {
        if (waiting?.Id == id) { mark(id); waiting = null; }
        if (showing?.Id != id) return false;
        showing = null;
        return true;
    }

    /// <summary>The hint ran its time out: it is no longer up (the row stays taught).</summary>
    public void Expired() => showing = null;
}
