using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Play;

/* The tutorial's callouts (docs/story/TUTORIAL_COPY.md; the owner, 18 October: "a more direct
 * helper tip like freeze frame arrow point kinda deal"). A zone asks for one at its moment
 * (IZoneHost.Teach); the Teacher keeps them in a line, shows one at a time, waits while anything
 * else has the screen, lets one whose moment has passed go unseen (it can come again), and
 * remembers in the profile which have been seen. The game draws them (src/Ui/Callout.cs). */

/// <summary>Freeze: the fight stops, the world dims, an arrow and the words, until the player acts.
/// Arrow: the arrow and the words beside the thing for a few seconds, the fight running on.
/// Panel: on the level-up draft (which already holds the fight still).</summary>
public enum CalloutKind { Freeze, Arrow, Panel }

/// <summary>What a callout points at. Hud: a part of the interface ("chain", "dash", "draught",
/// "art", "socket:WEAPON", "banner", "cards", "card:weapon"). World: points in the world, asked
/// every frame (none: the thing is gone). Banner: an announcement shown again and held under it.</summary>
public sealed record Aim
{
    public string? Hud { get; init; }
    public Func<IReadOnlyList<(double X, double Y, double Z)>>? World { get; init; }
    public Announcement? Banner { get; init; }

    public static Aim At(string hud) => new() { Hud = hud };
    public static Aim In(Func<IReadOnlyList<(double X, double Y, double Z)>> world) => new() { World = world };
}

/// <summary>One callout: its id (once a profile), kind, title and line, what it points at, and the
/// action that answers it (an Act's name: "dash", "draught", "flare"; null: any key goes on).</summary>
public sealed record Callout(string Id, CalloutKind Kind, string Title, string Line, Aim Target, string? Answer = null)
{
    /// <summary>Game seconds it may wait for the screen before its moment has passed.</summary>
    public double Patience { get; init; } = 8;
}

/// <summary>Where a callout's target is now: on screen, not yet (a draft without the card), or gone.</summary>
public enum Presence { Here, NotYet, Gone }

/// <summary>What has the screen, as the game reports it each frame.</summary>
[Flags]
public enum Busy
{
    None = 0, Cinematic = 1, Transit = 2, Fall = 4, Overlay = 8, Draft = 16, Banner = 32, Say = 64, Prompt = 128, Hint = 256,
}

/// <summary>The profile's memory of callouts: whether they are wanted at all, and which were seen.</summary>
public interface ITeachMemory
{
    bool Tips { get; }
    bool Seen(string id);
    void Mark(string id);
}

/// <summary>A memory held in a set (the tests, a host without a profile).</summary>
public sealed class TeachMemory : ITeachMemory
{
    public bool Tips { get; set; } = true;
    public readonly HashSet<string> SeenIds = new();
    public bool Seen(string id) => SeenIds.Contains(id);
    public void Mark(string id) => SeenIds.Add(id);
}

/// <summary>The line of callouts. Time is given in: `now` in game seconds (stopped while the fight
/// is), `real` in real seconds (a freeze's hold, an arrow's life).</summary>
public sealed class Teacher
{
    /// <summary>A freeze can't be gone on from before this (a mashed key never skips it unread).</summary>
    public const double MinHold = 0.5;
    /// <summary>How long an arrow shows.</summary>
    public const double ArrowLife = 4;
    /// <summary>An arrow cut off by something else before this was not read: it can come again.</summary>
    public const double ArrowRead = 2.5;
    /// <summary>After a callout's moment passed unseen, it is not asked for again for this long.</summary>
    public const double Requeue = 2;

    readonly ITeachMemory memory;
    readonly List<(Callout C, double At)> queue = new();
    readonly Dictionary<string, double> dropped = new();

    /// <summary>On screen now.</summary>
    public Callout? Current { get; private set; }
    /// <summary>When the current one came up (real seconds).</summary>
    public double ShownAt { get; private set; }
    /// <summary>Each event: "queued", "shown", "answered", "dropped", with its callout and a word on how.</summary>
    public Action<string, Callout, string>? Log;

    public Teacher(ITeachMemory memory) { this.memory = memory; }

    public ITeachMemory Memory => memory;
    public int Waiting => queue.Count;
    public bool Queued(string id) => queue.Any(q => q.C.Id == id);

    /// <summary>A zone's ask (said every frame its moment holds is fine): taken into the line unless
    /// tips are off, it was seen, it is already waiting or up, or it was just let go.</summary>
    public bool Offer(Callout c, double now)
    {
        if (!memory.Tips || memory.Seen(c.Id)) return false;
        if (Current?.Id == c.Id || Queued(c.Id)) return false;
        if (dropped.TryGetValue(c.Id, out var d) && now - d < Requeue && now >= d) return false;
        queue.Add((c, now));
        Log?.Invoke("queued", c, "");
        return true;
    }

    /// <summary>Whether what has the screen keeps this callout waiting. A panel callout belongs on
    /// the draft and waits for it; everything else waits for a clear screen.</summary>
    public static bool Blocked(Callout c, Busy busy) => c.Kind == CalloutKind.Panel
        ? (busy & Busy.Draft) == 0 || (busy & (Busy.Cinematic | Busy.Transit | Busy.Fall | Busy.Overlay)) != 0
        : busy != Busy.None;

    /// <summary>A step: the one up ends if its time is over (an arrow) or its panel closed; what
    /// waits too long or lost its target is let go unseen; the first in line that can show, shows.
    /// Returns the callout that came up this step, if one did.</summary>
    public Callout? Update(double now, double real, Busy busy, Func<Callout, Presence> where)
    {
        if (Current is { } cur)
        {
            switch (cur.Kind)
            {
                case CalloutKind.Arrow:
                    if (real - ShownAt >= ArrowLife) Close("time", real);
                    else if (Blocked(cur, busy) || where(cur) == Presence.Gone)
                    {
                        if (real - ShownAt >= ArrowRead) Close("cut", real);
                        else Withdraw(now, "cut", real);
                    }
                    break;
                case CalloutKind.Panel:
                    if ((busy & Busy.Draft) == 0) Close("panel", real);
                    break;
            }
            if (Current != null) return null;
        }
        if (!memory.Tips) { queue.Clear(); return null; }
        for (int i = 0; i < queue.Count; i++)
        {
            var (c, at) = queue[i];
            if (memory.Seen(c.Id)) { queue.RemoveAt(i--); continue; }
            var p = where(c);
            if (p == Presence.Gone || now - at > c.Patience)
            {
                queue.RemoveAt(i--);
                dropped[c.Id] = now;
                Log?.Invoke("dropped", c, p == Presence.Gone ? "gone" : "waited");
                continue;
            }
            if (Blocked(c, busy) || p == Presence.NotYet) continue;
            queue.RemoveAt(i);
            Current = c;
            ShownAt = real;
            Log?.Invoke("shown", c, "");
            return c;
        }
        return null;
    }

    /// <summary>Whether a freeze may be gone on now (its minimum hold is over).</summary>
    public bool CanContinue(double real) => Current != null && real - ShownAt >= MinHold;

    /// <summary>The one up is done (answered, gone on, skipped, or its time is over): seen.</summary>
    public void Close(string how, double real)
    {
        if (Current is not { } c) return;
        memory.Mark(c.Id);
        Log?.Invoke("answered", c, how);
        Current = null;
    }

    /// <summary>The one up is taken down unseen (its moment passed under it): it can come again.</summary>
    public void Withdraw(double now, string how, double real)
    {
        if (Current is not { } c) return;
        dropped[c.Id] = now;
        Log?.Invoke("dropped", c, how);
        Current = null;
    }

    /// <summary>Everything waiting let go (the zone left).</summary>
    public void Clear(double now)
    {
        foreach (var (c, _) in queue) { dropped[c.Id] = now; Log?.Invoke("dropped", c, "left"); }
        queue.Clear();
        if (Current != null) Withdraw(now, "left", 0);
    }
}
