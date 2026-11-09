using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play;

/// <summary>
/// (M5 r3) One story text channel at a time: the narrator's line (the bottom band, IZoneHost.Say) and a named speaker's
/// line (Grimtunnel's, the Warden's: Voices' card with its name) never open over one another. The judge, round 2: the dawn
/// narration printed on top of Grimtunnel's line and his name; at a champion's wake the narration ran through the Knight's
/// body. So each asks here and is shown in order of asking:
///   a narration waits while a speaker's line is up, while the hold is on (a champion's wake beat, HoldNarration), and,
///     after one that was itself held, keeps the spacing its zone gave it from the line before (so a held "In the reeds..."
///     is not cut short by the "Gray light..." its zone timed 4.4 s after it);
///   a speaker's line waits while a narration is up;
///   nothing overtakes what was asked before it.
/// Engine-free: the game passes what is up now (the HUD's band, Voices' named cards) and the clock.
/// </summary>
public sealed class StoryText
{
    public enum Kind { Narration, Speaker }

    readonly Func<double> clock;
    readonly Func<bool> narrationUp, speakerUp;
    readonly Queue<(Kind Kind, double Asked, Action Show, string? Who)> line = new();
    double holdUntil = double.NegativeInfinity;
    (double Asked, double Shown)? lastNarration;

    /// <summary>A narration waits at most this long behind speakers (s); then it shows (the story is never lost).</summary>
    public const double MostWait = 12;
    /// <summary>A champion's wake beat is fresh this long (s): the narration band stays clear of it.</summary>
    public const double WakeHold = 3;

    /// <summary>(M5 r4) A champion wakes within WakeAhead seconds (ChampionGate.Waking): no narration opens, and one up
    /// now is taken down (TakeDown) and asked again, to show after the wake's hold. The judge, round 3: Ser Aldric's line
    /// opened 1.7 s before he woke, so the hold after the wake never caught it.</summary>
    public Func<bool>? WakeSoon { get; set; }
    /// <summary>Takes the narration band down now (the HUD's band and the narrator's voice).</summary>
    public Action? TakeDown { get; set; }
    /// <summary>Seconds before a champion's wake the band is kept clear.</summary>
    public const double WakeAhead = 2;

    /// <summary>Two narrations asked within this many seconds are one beat's lines: a held first keeps their spacing.</summary>
    public const double BeatGap = 10;

    /// <summary>The narration shown last (to ask again if a wake comes while it is up) and whether it was already taken
    /// down once (a line is taken down once; asked again it stays).</summary>
    (Action Show, bool Again)? upNow;

    public StoryText(Func<double> clock, Func<bool> narrationUp, Func<bool> speakerUp)
    {
        this.clock = clock; this.narrationUp = narrationUp; this.speakerUp = speakerUp;
    }

    /// <summary>Lines asked for and not yet shown.</summary>
    public int Waiting => line.Count;

    /// <summary>No narration opens before `seconds` from now (a champion's wake beat).</summary>
    public void HoldNarration(double seconds) => holdUntil = Math.Max(holdUntil, clock() + seconds);

    public bool NarrationHeld => clock() < holdUntil;

    /// <summary>A line asked for: shown now if its channel is clear and nothing waits before it, else in its turn (Tick).</summary>
    public void Ask(Kind kind, Action show, string? who = null)
    {
        line.Enqueue((kind, clock(), show, who));
        Tick();
    }

    /// <summary>Show what may be shown now, in order (call every frame).</summary>
    public void Tick()
    {
        if (!narrationUp()) upNow = null;
        bool soon = WakeSoon?.Invoke() == true;
        if (soon) holdUntil = Math.Max(holdUntil, clock() + 0.1);
        if (soon && upNow is { Again: false } u && narrationUp() && TakeDown != null)
        {
            // (taken down and asked again at the head of the line: it shows after the wake's hold)
            TakeDown();
            upNow = null;
            // (r4 capture: the prediction flickered off 0.8 s later and the line came back over Nan Sallow's wake; held
            // through the wake's window, its own hold added when it comes; Nan Sallow woke 3.2 s after the take-down)
            holdUntil = Math.Max(holdUntil, clock() + WakeAhead + 3);
            var rest = new List<(Kind, double, Action, string?)>(line);
            line.Clear();
            line.Enqueue((Kind.Narration, clock(), () => { u.Show(); upNow = (u.Show, true); }, null));
            foreach (var x in rest) line.Enqueue(x);
            lastNarration = null;
        }
        while (line.Count > 0)
        {
            var (kind, asked, show, _) = line.Peek();
            double now = clock();
            if (kind == Kind.Narration)
            {
                bool late = now - asked >= MostWait;
                if (!late && (speakerUp() || now < holdUntil)) return;
                // (the spacing holds only for lines of one beat: a delay never carries into a line asked long after.
                // r4c capture: an earlier held line's delay held the Warden's heart line 12 s, to MostWait)
                if (lastNarration is { } ln && ln.Shown > ln.Asked + 1e-6 && asked - ln.Asked <= BeatGap
                    && now < ln.Shown + (asked - ln.Asked)) return;
                lastNarration = (asked, now);
            }
            else if (narrationUp()) return;
            line.Dequeue();
            if (kind == Kind.Narration) upNow = (show, false);
            show();
        }
    }

    /// <summary>A speaker's lines still waiting dropped (Ev.Hush: their moment has gone).</summary>
    public void Drop(string who)
    {
        var keep = new List<(Kind, double, Action, string?)>(line);
        line.Clear();
        foreach (var x in keep) if (x.Item4 != who) line.Enqueue(x);
    }

    /// <summary>Everything waiting dropped (a zone left, a film began).</summary>
    public void Clear() => line.Clear();
}
