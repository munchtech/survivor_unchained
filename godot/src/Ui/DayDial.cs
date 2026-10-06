using System;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The day's clock by the place's name (the experience director's brief): a shallow arc in four
/// bands in proportion to the day (dawn, day, dusk, night), her mark moving round it. The present
/// band is lit, the rest faint; what of it has passed is fainter still. Dusk is ember-warm and
/// night moon-blue; at night a pale moon rides the arc instead of her ember, and after the night's
/// turn (DayClock.NudgeAt) what is left of it cools toward the morning. While the clock stands
/// still (the first day before she has somewhere to be, a screen open, a fight) the dial dims. No
/// numbers: the arc is read at a glance, as the light is.
/// </summary>
public partial class DayDial : Control
{
    public const float W = 136, H = 30;
    double clock;
    bool running;
    float dim = 1;

    static readonly (double From, double To, Color Ink)[] Bands =
    {
        (0, DayClock.DayAt, new Color("#d8b8c8")),
        (DayClock.DayAt, DayClock.DuskAt, new Color("#ecd9a6")),
        (DayClock.DuskAt, DayClock.NightAt, new Color("#ff8a3a")),
        (DayClock.NightAt, DayClock.NightEnds, new Color("#86a6e0")),
    };

    public DayDial()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        CustomMinimumSize = new Vector2(W, H);
    }

    public void Set(double clock, bool running)
    {
        this.clock = Math.Clamp(clock, 0, DayClock.NightEnds);
        this.running = running;
    }

    public override void _Process(double delta)
    {
        dim = Mathf.MoveToward(dim, running ? 1 : 0.45f, (float)delta * 2);
        QueueRedraw();
    }

    /// <summary>A point on the arc at a time of day: the arc rises from its left end to the top and
    /// falls to its right end, a little more than a half ellipse.</summary>
    Vector2 At(double s)
    {
        float k = (float)(s / DayClock.NightEnds), a = Mathf.Lerp(Mathf.Pi * 1.17f, Mathf.Pi * 1.83f, k);
        var c = new Vector2(W / 2, H + 18);
        return c + new Vector2(Mathf.Cos(a) * (W / 2 - 6), Mathf.Sin(a) * (H + 10));
    }

    public override void _Draw()
    {
        var now = DayClock.At(clock);
        int nowBand = (int)now;
        bool late = now == TimeOfDay.Night && clock >= DayClock.NudgeAt;
        for (int b = 0; b < Bands.Length; b++)
        {
            var (from, to, ink) = Bands[b];
            bool lit = b == nowBand;
            int steps = Math.Max(3, (int)((to - from) / DayClock.NightEnds * 48));
            for (int i = 0; i < steps; i++)
            {
                double s0 = from + (to - from) * i / steps, s1 = from + (to - from) * (i + 1) / steps;
                bool passed = s1 <= clock;
                var c = ink;
                // The night's last stretch cools toward the morning once the night has turned.
                if (b == 3 && late && !passed) c = c.Lerp(new Color("#c8ccd8"), (float)((s0 - DayClock.NudgeAt) / (DayClock.NightEnds - DayClock.NudgeAt)) * 0.7f);
                float a = passed ? 0.26f : lit ? 1f : 0.5f;
                // (a dark line under each stroke, so it reads over sunlit ground as well as night)
                DrawLine(At(s0) + new Vector2(0, 1), At(s1) + new Vector2(0, 1), new Color(0, 0, 0, 0.5f * dim), lit && !passed ? 5 : 4, true);
                DrawLine(At(s0), At(s1), c with { A = a * dim }, lit && !passed ? 3.5f : 2.2f, true);
            }
            // a fine notch where one band gives way to the next
            if (b > 0) DrawCircle(At(from), 1.6f, new Color(0.9f, 0.85f, 0.75f, 0.45f * dim));
        }
        var p = At(clock);
        if (now == TimeOfDay.Night)
        {
            // The pale moon riding the arc: a disc with the dark taking a bite from it.
            DrawCircle(p, 9, new Color(0.6f, 0.7f, 1f, 0.16f * dim));
            DrawCircle(p, 5.5f, new Color("#e4ebff") with { A = dim });
            DrawCircle(p + new Vector2(2.6f, -1.6f), 4.6f, new Color(0.06f, 0.07f, 0.12f, 0.92f * dim));
        }
        else
        {
            // Her mark: the ember she carries, breathing.
            float br = 0.85f + 0.15f * Mathf.Sin(Time.GetTicksMsec() / 1000f * 2.2f);
            DrawCircle(p, 10, Style.Ember with { A = 0.2f * br * dim });
            DrawCircle(p, 4.2f, Style.Ember with { A = dim });
            DrawCircle(p, 2, Style.EmberHi with { A = dim });
        }
    }
}
