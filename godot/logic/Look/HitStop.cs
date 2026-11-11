using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Look;

/// <summary>Local hit-stop's table (data/content/hit_stop.json), in milliseconds as written.</summary>
public sealed class HitStopTable
{
    [JsonPropertyName("trash_ms")] public double TrashMs;
    [JsonPropertyName("heavy_ms")] public double HeavyMs = 50;
    [JsonPropertyName("crit_ms")] public double CritMs = 55;
    [JsonPropertyName("art_ms")] public double ArtMs = 55;
    [JsonPropertyName("hurt_ms")] public double HurtMs = 60;
    [JsonPropertyName("elite_kill_ms")] public double EliteKillMs = 90;
    [JsonPropertyName("boss_kill_ms")] public double BossKillMs = 100;
    [JsonPropertyName("cap_ms")] public double CapMs = 150;
    [JsonPropertyName("gap_ms")] public double GapMs = 90;
    [JsonPropertyName("crowd_n")] public int CrowdN = 30;
    [JsonPropertyName("crowd_scale")] public double CrowdScale = 0.5;
    [JsonPropertyName("rate")] public double Rate = 0.06;
    [JsonPropertyName("shake_m")] public double ShakeM = 0.03;
    [JsonPropertyName("shake_hz")] public double ShakeHz = 30;
    [JsonPropertyName("catchup_s")] public double CatchupS = 0.08;
    [JsonPropertyName("first_hit_delay_ms")] public double FirstHitDelayMs = 30;

    static HitStopTable? loaded;
    public static HitStopTable Load => loaded ??= Json.Parse<HitStopTable>(Json.ReadContent("hit_stop.json"));
}

/// <summary>Per-body hit-stop bookkeeping (view side only: the sim is never asked to wait). A body is held for a short
/// while, its clocks run at the table's rate; asks stack by the longer remaining (never the sum), no hold lasts past
/// the cap from its start, and after a hold the body cannot be held again for the gap. Plain C#, no engine.</summary>
public sealed class HitStops
{
    /// <summary>The survivor's body id (enemy ids are 0 and up).</summary>
    public const int Her = -1;

    sealed class Slot { public bool Held; public double Age, Left, Gap, Dx, Dz; }

    readonly HitStopTable t;
    readonly Dictionary<int, Slot> slots = new();
    public HitStops(HitStopTable? table = null) { t = table ?? HitStopTable.Load; }
    public HitStopTable Table => t;

    /// <summary>Asks to hold a body for these seconds (the blow's direction Dx, Dz is for the victim's shake). Returns
    /// true if this started a hold now (false: nothing asked, in its gap, or extended/kept a hold already running).</summary>
    public bool Ask(int body, double seconds, int onScreen, double dx = 0, double dz = 0)
    {
        if (seconds <= 0) return false;
        if (onScreen > t.CrowdN) seconds *= t.CrowdScale;
        double cap = t.CapMs / 1000;
        if (!slots.TryGetValue(body, out var s)) slots[body] = s = new Slot();
        if (s.Held)
        {
            double left = Math.Min(Math.Max(s.Left, seconds), Math.Max(0, cap - s.Age));
            if (left > s.Left) { s.Left = left; s.Dx = dx; s.Dz = dz; }
            return false;
        }
        if (s.Gap > 0) return false;
        s.Held = true; s.Age = 0; s.Left = Math.Min(seconds, cap); s.Dx = dx; s.Dz = dz;
        return true;
    }

    /// <summary>Runs every hold and gap down on the real clock.</summary>
    public void Tick(double dt)
    {
        if (slots.Count == 0) return;
        List<int>? gone = null;
        foreach (var (id, s) in slots)
        {
            if (s.Held)
            {
                s.Age += dt; s.Left -= dt;
                if (s.Left <= 0) { s.Held = false; s.Left = 0; s.Gap = t.GapMs / 1000; }
            }
            else if ((s.Gap -= dt) <= 0) (gone ??= new()).Add(id);
        }
        if (gone != null) foreach (var id in gone) slots.Remove(id);
    }

    public bool Held(int body) => slots.TryGetValue(body, out var s) && s.Held;
    /// <summary>The clock rate of a body: the table's while held, else 1.</summary>
    public double Rate(int body) => Held(body) ? t.Rate : 1;
    /// <summary>Seconds of hold left (0 when not held).</summary>
    public double Left(int body) => slots.TryGetValue(body, out var s) && s.Held ? s.Left : 0;
    /// <summary>1 at the start of a hold, falling linearly to 0 at its end (0 when not held).</summary>
    public double Fade(int body) => slots.TryGetValue(body, out var s) && s.Held && s.Age + s.Left > 0 ? s.Left / (s.Age + s.Left) : 0;

    /// <summary>A held body's shake offset (metres) along the blow, alternating sign at shake_hz, fading with the hold.</summary>
    public (double X, double Z) Shake(int body)
    {
        if (!slots.TryGetValue(body, out var s) || !s.Held) return (0, 0);
        double l = Math.Sqrt(s.Dx * s.Dx + s.Dz * s.Dz);
        if (l < 1e-6) return (0, 0);
        double a = t.ShakeM * Fade(body) * (((long)(s.Age * t.ShakeHz * 2) & 1) == 0 ? 1 : -1) / l;
        return (s.Dx * a, s.Dz * a);
    }
}
