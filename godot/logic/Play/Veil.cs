namespace SurvivorUnchained.Play;

/// <summary>
/// The black over the play (GameHud): a fade to black or back, and the pull into an arena (the world
/// swirls in and burns away to the dark, shaders/pull.gdshader). Engine-free, so the order of events
/// is tested (VeilTests).
///
/// Two rules, both from the demo gate's item 6 (3 November: an arena entry with the blessing picked in
/// its first frames held black for a whole night):
/// - The pull counts in real time, as Game.Travel's waits do. Counted in frame time it fell behind: the
///   arena is built behind it in a few long frames, and the engine clamps a long frame's delta (about
///   0.13 s), so after 3 s of real time the pull had counted 0.32 s and its end came after the lift.
/// - A lift (a fade toward clear) cancels a pending pull, so no pull's end can re-blacken the screen
///   after it, whatever the order.
/// </summary>
public sealed class Veil
{
    double fadeFrom = 1, fadeTo = 1, fadeT = 1, fadeDur = 1;
    double pullStart = -1, pullDur = 1;

    /// <summary>The black's strength now, 0 (clear) to 1.</summary>
    public double Alpha { get; private set; } = 1;
    /// <summary>Whether the pull's swirl shows, and how far through it is (0..1).</summary>
    public bool Pulling => pullStart >= 0;
    public double PullProgress { get; private set; }

    /// <summary>Pulled into an arena over some seconds (real time); at its end the black holds.</summary>
    public void Pull(double seconds, double now)
    {
        pullStart = now;
        pullDur = System.Math.Max(0.1, seconds);
        PullProgress = 0;
    }

    /// <summary>Fade to black (1) or back (0) over some seconds. A lift cancels a pending pull.</summary>
    public void Fade(double to, double seconds)
    {
        fadeFrom = Alpha;
        fadeTo = to;
        fadeT = 0;
        fadeDur = System.Math.Max(0.01, seconds);
        if (to < 0.5) { pullStart = -1; PullProgress = 0; }
    }

    /// <summary>One frame: delta is the frame's time (the fade's clock), now the real time in seconds (the pull's).</summary>
    public void Tick(double delta, double now)
    {
        if (pullStart >= 0)
        {
            PullProgress = System.Math.Clamp((now - pullStart) / pullDur, 0, 1);
            if (now - pullStart >= pullDur)
            {
                // Burned through: the dark holds.
                pullStart = -1;
                PullProgress = 0;
                fadeFrom = fadeTo = 1;
                fadeT = fadeDur = 1;
                Alpha = 1;
            }
        }
        if (fadeT < fadeDur)
        {
            fadeT += delta;
            double k = System.Math.Clamp(fadeT / fadeDur, 0, 1);
            k = k * k * (3 - 2 * k);
            Alpha = fadeFrom + (fadeTo - fadeFrom) * k;
        }
    }
}
