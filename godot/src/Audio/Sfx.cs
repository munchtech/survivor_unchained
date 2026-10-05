using System;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

/// <summary>
/// Every one-shot the game makes, by name (the web game's audio/sfx.ts).
/// Each is a little recipe: a thump, a hiss through a filter, a struck bell,
/// a recording where a real thing sounds best (Recordings: a blow, a body
/// falling, coins, a door, a footstep, the interface's clicks), layered and
/// pitched a bit differently every time so that the
/// two-hundredth sword hit does not sound like the first played again. Pan
/// and near (0..1, how close to the survivor) come from where it happened.
/// </summary>
public static class Sfx
{
    static Synth? A => Synth.Instance is { Live: true } s ? s : null;
    static double R(double a, double b) => Synth.R(a, b);
    static double Semis(double n) => Math.Pow(2, n / 12);
    static double Now => Synth.Instance?.Now ?? 0;

    public readonly record struct Where(double Pan = 0, double Near = 1);

    /* ------------------------------------------------------------ combat -- */

    public static void Hit(School school, bool crit, Where w = default)
    {
        if (A is not { } a || !a.Gate("hit", 7, 70)) return;
        double pan = w.Pan, g = 0.5 + 0.5 * w.Near;
        switch (school)
        {
            case School.Fire:
                a.Play(new Hiss { D = R(0.1, 0.16), G = 0.1 * g, Lp = 3200, Lp2 = 600, Pan = pan });
                a.Play(new Tone { F = R(120, 150), F2 = 60, D = 0.1, G = 0.12 * g, Pan = pan });
                break;
            case School.Frost:
                a.Play(new Fm { F = R(2200, 2800), Ratio = 3.07, Index = 1.2, D = 0.2, G = 0.035 * g, Pan = pan, Verb = 0.3 });
                a.Play(new Hiss { D = 0.05, G = 0.06 * g, Hp = 4200, Pan = pan });
                break;
            case School.Storm:
                a.Play(new Hiss { D = 0.07, G = 0.1 * g, Bp = 3200, Q = 0.6, Pan = pan });
                a.Play(new Tone { F = R(80, 110), Type = Wave.Square, D = 0.06, G = 0.035 * g, Lp = 1400, Pan = pan });
                break;
            case School.Holy:
                a.Play(new Fm { F = R(800, 1000), Ratio = 2, Index = 0.8, D = 0.35, G = 0.04 * g, Pan = pan, Verb = 0.4 });
                a.Play(new Hiss { D = 0.05, G = 0.05 * g, Bp = 2400, Pan = pan });
                break;
            case School.Nature:
                a.Play(new Hiss { D = 0.1, G = 0.09 * g, Bp = 500, Bp2 = 1400, Q = 3, Pan = pan });
                break;
            case School.Shadow or School.Arcane:
                a.Play(new Tone { F = R(200, 260), F2 = 90, Type = Wave.Saw, D = 0.13, G = 0.06 * g, Lp = 1100, Pan = pan });
                a.Play(new Hiss { D = 0.06, G = 0.05 * g, Bp = 1400, Pan = pan });
                break;
            default:
                // Steel into something that bleeds: a recorded blow under the made crack.
                a.Play(new Clip { Of = crit ? "impactPunch_heavy" : "impactPunch_medium", G = 0.4 * g, Pitch = R(0.85, 1.15), Pan = pan });
                a.Play(new Hiss { D = R(0.05, 0.08), G = 0.1 * g, Bp = R(1500, 2200), Bp2 = 600, Q = 1.2, Pan = pan });
                a.Play(new Tone { F = R(130, 160), F2 = 65, D = 0.08, G = 0.1 * g, Pan = pan });
                break;
        }
        if (crit && a.Gate("crit", 3, 90)) a.Play(new Fm { F = R(1100, 1400), Ratio = 2.71, Index = 2.5, D = 0.28, G = 0.05 * g, Pan = pan, Verb = 0.25 });
    }

    public static void Blocked(Where w = default)
    {
        if (A is not { } a || !a.Gate("block", 2, 90)) return;
        a.Play(new Clip { Of = "impactMetal_medium", G = 0.35, Pitch = R(0.9, 1.1), Pan = w.Pan, Verb = 0.2 });
        a.Play(new Fm { F = R(520, 640), Ratio = 1.41, Index = 3.5, D = 0.35, G = 0.04, Pan = w.Pan, Verb = 0.3 });
    }

    /// <summary>A ward giving way: a bright crack, and glass going everywhere.</summary>
    public static void Shatter()
    {
        if (A is not { } a || !a.Gate("shatter", 1, 250)) return;
        a.Play(new Clip { Of = "impactGlass_light", G = 0.35, Pitch = R(0.9, 1.1), Verb = 0.3 });
        a.Play(new Fm { F = R(1700, 1900), Ratio = 2.76, Index = 4, D = 0.5, G = 0.05, Verb = 0.45 });
        a.Play(new Fm { T = Now + 0.03, F = R(2500, 2800), Ratio = 3.41, Index = 3, D = 0.6, G = 0.035, Verb = 0.5 });
        a.Play(new Hiss { A = 0.002, D = 0.35, G = 0.05, Hp = 3500, Verb = 0.3 });
    }

    /// <summary>Your own heart, when you are close to the end: lub, dub.</summary>
    public static void Heartbeat(double urgency)
    {
        if (A is not { } a) return;
        double g = 0.05 + 0.06 * urgency;
        a.Play(new Tone { F = 58, F2 = 42, D = 0.16, G = g, Lp = 220 });
        a.Play(new Tone { T = Now + 0.24, F = 52, F2 = 38, D = 0.2, G = g * 0.75, Lp = 200 });
    }

    public static void Kill(Family family, bool elite, bool boss, Where w = default)
    {
        if (A is not { } a || !a.Gate("kill", 5, 90)) return;
        double pan = w.Pan, g = 0.5 + 0.5 * w.Near;
        a.Play(new Tone { F = R(95, 115), F2 = 38, D = 0.2, G = 0.14 * g, Pan = pan });
        a.Play(new Hiss { D = 0.14, G = 0.05 * g, Lp = 1100, Lp2 = 200, Pan = pan });
        // What falls: dry bones clattering, or a body.
        a.Play(family == Family.Undead
            ? new Clip { Of = "impactWood_medium", G = 0.3 * g, Pitch = R(1.2, 1.5), Pan = pan }
            : new Clip { Of = "impactSoft_heavy", G = 0.45 * g, Pitch = R(0.8, 1.0) * (elite || boss ? 0.8 : 1), Pan = pan });
        if (family == Family.Undead)
        {
            // Bones: two dry cracks.
            a.Play(new Hiss { D = 0.03, G = 0.08 * g, Bp = 2600, Q = 4, Pan = pan });
            a.Play(new Hiss { T = Now + 0.045, D = 0.025, G = 0.06 * g, Bp = 3400, Q = 4, Pan = pan });
        }
        else if (family is Family.Wolf or Family.Beast or Family.Boar)
            a.Play(new Tone { F = R(800, 1000), F2 = 420, Type = Wave.Triangle, D = 0.12, G = 0.035 * g, Pan = pan });
        else if (family is Family.Lampling or Family.Kerchief or Family.Human)
            a.Play(new Tone { F = R(260, 320), F2 = 150, Type = Wave.Triangle, D = 0.14, G = 0.03 * g, Lp = 900, Pan = pan });
        if (elite || boss)
        {
            a.Play(new Tone { F = 70, F2 = 28, D = boss ? 1.6 : 0.8, G = boss ? 0.45 : 0.3, Pan = pan });
            a.Play(new Hiss { D = boss ? 1.4 : 0.7, G = 0.12, Lp = 900, Lp2 = 120, Brown = true });
            if (boss) Stinger("triumph");
        }
    }

    public static void Hurt(double amount)
    {
        if (A is not { } a || !a.Gate("hurt", 2, 160)) return;
        double k = Math.Min(1, amount / 30);
        a.Play(new Tone { F = 120, F2 = 55, Type = Wave.Saw, D = 0.22, G = 0.12 + 0.12 * k, Lp = 520 });
        a.Play(new Hiss { D = 0.16, G = 0.08 + 0.06 * k, Lp = 1400, Lp2 = 300 });
    }

    public static void Dodge() => A?.Play(new Hiss { A = 0.02, D = 0.18, G = 0.08, Bp = 900, Bp2 = 3200, Q = 1.4 });

    /// <summary>A blow slipped at the last moment: a bright ring, like a
    /// blade drawn across a bell, over a low whoomph.</summary>
    public static void Perfect()
    {
        if (A is not { } a || !a.Gate("perfect", 1, 200)) return;
        a.Play(new Fm { F = 1318.5, Ratio = 2.76, Index = 2.5, D = 0.9, G = 0.06, Verb = 0.55 });
        a.Play(new Fm { T = Now + 0.04, F = 1975.5, Ratio = 3.01, Index = 1.8, D = 0.8, G = 0.04, Verb = 0.6 });
        a.Play(new Tone { F = 110, F2 = 55, D = 0.35, G = 0.12 });
        a.Play(new Hiss { A = 0.005, D = 0.3, G = 0.06, Bp = 2400, Bp2 = 6000, Q = 1.2, Verb = 0.3 });
    }

    /// <summary>Her rise (BattleFx.Rise), in the slowed world's time: the cold (a glassy breath
    /// in and one beat of the heart), then the ember catching (a low rush of fire) or the
    /// Order's answer (one toll of a watch bell, deep and long).</summary>
    public static void Rise(bool ember)
    {
        if (A is not { } a) return;
        a.DuckSfx(0.35f, 1.6);
        double t = Now;
        a.Play(new Hiss { A = 0.12, D = 0.55, G = 0.05, Bp = 5200, Bp2 = 8000, Q = 2.2, Verb = 0.55 });
        a.Play(new Fm { F = 1567.98, F2 = 1318.5, Ratio = 2.76, Index = 0.9, A = 0.08, D = 0.7, G = 0.025, Verb = 0.7 });
        a.Play(new Tone { T = t + 0.12, F = 62, F2 = 38, D = 0.32, G = 0.24 });
        if (ember)
        {
            a.Play(new Tone { T = t + 0.4, F = 70, F2 = 47, D = 0.3, G = 0.2 });
            a.Play(new Hiss { T = t + 0.48, A = 0.05, D = 1.3, G = 0.16, Bp = 280, Bp2 = 2200, Q = 0.7, Verb = 0.35 });
            a.Play(new Tone { T = t + 0.48, F = 55, F2 = 98, A = 0.04, D = 1.0, G = 0.14, Type = Wave.Saw, Lp = 280, Lp2 = 1100 });
            a.Play(new Hiss { T = t + 0.6, A = 0.3, D = 1.4, G = 0.04, Hp = 3500, Verb = 0.2 });
        }
        else
        {
            a.Play(new Clip { T = t + 0.36, Of = "impactBell_heavy", G = 0.5, Pitch = 0.5, Verb = 0.85 });
            a.Play(new Fm { T = t + 0.36, F = 196, Ratio = 2.76, Index = 0.7, A = 0.01, D = 3.4, G = 0.05, Verb = 0.85 });
            a.Play(new Fm { T = t + 0.36, F = 98, Ratio = 1.4, Index = 0.5, A = 0.01, D = 3.8, G = 0.06, Verb = 0.8 });
        }
    }

    public static void Dash()
    {
        if (A is not { } a) return;
        a.Play(new Hiss { A = 0.02, D = 0.26, G = 0.1, Bp = 500, Bp2 = 2600, Q = 1.1 });
        a.Play(new Tone { F = 180, F2 = 90, D = 0.2, G = 0.05 });
    }

    public static void Swing(Where w = default)
    {
        if (A is not { } a || !a.Gate("swing", 3, 110)) return;
        a.Play(new Hiss { A = 0.01, D = 0.09, G = 0.04, Bp = R(2000, 2600), Bp2 = 800, Q = 2, Pan = w.Pan });
    }

    public static void Shoot(School school, Where w = default)
    {
        if (A is not { } a || !a.Gate("shoot", 4, 90)) return;
        if (school == School.Physical)
        {
            a.Play(new Tone { F = R(280, 330), F2 = 190, Type = Wave.Triangle, D = 0.08, G = 0.035, Pan = w.Pan });
            a.Play(new Hiss { D = 0.05, G = 0.03, Hp = 3000, Pan = w.Pan });
        }
        else a.Play(new Tone { F = R(800, 1000), F2 = 300, D = 0.1, G = 0.025, Pan = w.Pan });
    }

    public static void Explosion(double power, Where w = default)
    {
        if (A is not { } a || !a.Gate("boom", 3, 150)) return;
        double g = Math.Min(1.4, 0.5 + power * 0.4) * (0.5 + 0.5 * w.Near);
        a.Play(new Tone { F = 80, F2 = 28, D = 0.7, G = 0.35 * g, Pan = w.Pan });
        a.Play(new Hiss { D = 0.9, G = 0.25 * g, Lp = 1600, Lp2 = 140, Brown = true, Pan = w.Pan });
        a.Play(new Hiss { D = 0.25, G = 0.1 * g, Bp = 2400, Q = 0.6, Pan = w.Pan });
    }

    public static void Nova(School school)
    {
        if (A is not { } a || !a.Gate("nova", 2, 200)) return;
        a.Play(new Tone { F = 190, F2 = 55, D = 0.4, G = 0.18 });
        a.Play(new Hiss { A = 0.02, D = 0.35, G = 0.08, Bp = 700, Bp2 = 2200, Q = 0.8 });
        if (school == School.Frost) a.Play(new Fm { F = 1800, Ratio = 3.1, Index = 1, D = 0.5, G = 0.03, Verb = 0.4 });
        if (school == School.Holy) a.Play(new Fm { F = 660, Ratio = 2, Index = 0.6, D = 0.8, G = 0.04, Verb = 0.5 });
    }

    public static void Bash()
    {
        if (A is not { } a) return;
        a.Play(new Tone { F = 140, F2 = 50, D = 0.25, G = 0.28 });
        a.Play(new Fm { F = 420, Ratio = 1.41, Index = 3, D = 0.3, G = 0.05, Verb = 0.25 });
        a.Play(new Hiss { D = 0.18, G = 0.1, Lp = 1800, Lp2 = 300 });
    }

    /// <summary>The art in hand: each has a voice of its own.</summary>
    public static void Art(string id)
    {
        if (A is not { } a) return;
        switch (id)
        {
            case "shield_bash": Bash(); break;
            case "sprint":
                // A gust, and the breath taken for it.
                a.Play(new Hiss { A = 0.05, D = 0.5, G = 0.09, Bp = 600, Bp2 = 2400, Q = 0.9 });
                a.Play(new Hiss { A = 0.01, D = 0.15, G = 0.05, Hp = 2500 });
                break;
            case "mirror_step":
                a.Play(new Fm { F = 1760, Ratio = 1.5, Index = 1.2, D = 0.7, G = 0.04, Verb = 0.6 });
                a.Play(new Fm { T = Now + 0.03, F = 2349, Ratio = 1.5, Index = 1, D = 0.6, G = 0.03, Verb = 0.6 });
                a.Play(new Hiss { A = 0.01, D = 0.2, G = 0.05, Bp = 3000, Bp2 = 5000, Q = 1.5 });
                break;
            case "mirror_break":
                if (!a.Gate("glass", 2, 90)) return;
                a.Play(new Clip { Of = "impactGlass_light", G = 0.35, Pitch = R(0.9, 1.15) });
                a.Play(new Fm { F = R(2200, 2800), Ratio = 2.76, Index = 2, D = 0.5, G = 0.03, Verb = 0.5 });
                break;
            case "mirror_strike":
                if (!a.Gate("mstrike", 3, 80)) return;
                a.Play(new Hiss { A = 0.01, D = 0.1, G = 0.035, Bp = R(2600, 3400), Bp2 = 1200, Q = 2 });
                break;
            case "bull_rush":
                a.Play(new Tone { F = 90, F2 = 45, Type = Wave.Saw, D = 0.4, G = 0.12, Lp = 400 });
                a.Play(new Clip { Of = "impactSoft_heavy", G = 0.4, Pitch = 0.8 });
                a.Play(new Hiss { A = 0.02, D = 0.4, G = 0.08, Lp = 900, Lp2 = 200, Brown = true });
                break;
            case "wraith_walk":
                // A low, wrong chord.
                a.Play(new Fm { F = 110, Ratio = 1.007, Index = 3, D = 1.2, G = 0.07, Verb = 0.6 });
                a.Play(new Fm { F = 164.8, Ratio = 0.993, Index = 2, D = 1.1, G = 0.05, Verb = 0.6 });
                a.Play(new Hiss { A = 0.1, D = 0.8, G = 0.05, Bp = 400, Bp2 = 1200, Q = 2 });
                break;
            case "drain":
                if (!a.Gate("drain", 3, 70)) return;
                a.Play(new Tone { F = R(300, 360), F2 = 120, D = 0.18, G = 0.03, Type = Wave.Triangle });
                break;
            case "cinder_trail":
                a.Play(new Hiss { A = 0.05, D = 0.7, G = 0.12, Lp = 2400, Lp2 = 500, Brown = true });
                a.Play(new Tone { F = 70, F2 = 110, D = 0.5, G = 0.08 });
                break;
            case "grapple":
                a.Play(new Clip { Of = "impactMetal_medium", G = 0.3, Pitch = R(1.1, 1.3) });
                a.Play(new Hiss { A = 0.01, D = 0.25, G = 0.06, Bp = 1800, Bp2 = 900, Q = 3 });
                break;
            case "grapple_miss":
                a.Play(new Hiss { A = 0.01, D = 0.25, G = 0.05, Bp = 1800, Bp2 = 700, Q = 3 });
                break;
            case "chain_whirl":
                a.Play(new Hiss { A = 0.02, D = 0.35, G = 0.08, Bp = 1400, Bp2 = 2600, Q = 2.5 });
                a.Play(new Clip { Of = "impactMetal_medium", G = 0.25, Pitch = 0.9 });
                break;
            case "echo_step":
                a.Play(new Fm { F = 880, Ratio = 1.5, Index = 1.5, D = 1.0, G = 0.04, Verb = 0.7 });
                a.Play(new Fm { T = Now + 0.25, F = 880, Ratio = 1.5, Index = 1.5, D = 0.8, G = 0.02, Verb = 0.7 });
                break;
            case "echo_recall":
                a.Play(new Fm { F = 440, Ratio = 2, Index = 2, D = 0.6, G = 0.06, Verb = 0.6 });
                a.Play(new Tone { F = 200, F2 = 900, D = 0.25, G = 0.05 });
                a.Play(new Hiss { A = 0.02, D = 0.3, G = 0.06, Bp = 1500, Bp2 = 4000, Q = 1.2 });
                break;
            case "vault":
                a.Play(new Clip { Of = "cloth", G = 0.3, Pitch = R(0.9, 1.1) });
                a.Play(new Hiss { A = 0.01, D = 0.22, G = 0.06, Bp = 700, Bp2 = 2400, Q = 1.1 });
                a.Play(new Clip { T = Now + 0.05, Of = "impactWood_medium", G = 0.12, Pitch = 1.4 });
                break;
            case "iron_vow":
                a.Play(new Fm { F = 523.3, Ratio = 2, Index = 0.8, D = 0.9, G = 0.035, Verb = 0.6 });
                a.Play(new Fm { T = Now + 0.06, F = 784, Ratio = 2, Index = 0.6, D = 0.8, G = 0.025, Verb = 0.6 });
                break;
            case "blink":
                a.Play(new Fm { F = 1800, Ratio = 3.1, Index = 1, D = 0.5, G = 0.04, Verb = 0.4 });
                a.Play(new Hiss { A = 0.005, D = 0.25, G = 0.06, Bp = 3000, Bp2 = 800, Q = 1 });
                break;
            default: Bash(); break;
        }
    }

    public static void Spawn(SpawnStyle style, Where w = default)
    {
        if (A is not { } a || w.Near < 0.2 || !a.Gate("spawn", 2, 250)) return;
        if (style == SpawnStyle.Rise) a.Play(new Hiss { A = 0.15, D = 0.5, G = 0.05 * w.Near, Lp = 500, Brown = true, Pan = w.Pan });
        else if (style == SpawnStyle.Burrow) a.Play(new Hiss { A = 0.05, D = 0.35, G = 0.06 * w.Near, Bp = 300, Q = 1.5, Brown = true, Pan = w.Pan });
    }

    /* --------------------------------------------------------- pickups --- */

    /// <summary>The ladder past its clamp, two octaves on to three: only a lodestone's sweep climbs it.</summary>
    static readonly int[] HighLadder = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27, 29, 31, 34, 36];

    /// <summary>The ember stones as a phrase the player conducts by walking (S-02): each stone (or a
    /// handful taken in one frame, merged into one louder voice) a step up the score's D minor
    /// pentatonic from D6, round and clear (a sine and its third harmonic, a twin a few cents
    /// sharp). At the top it holds and shimmers an octave over; a bar nearly full adds a soft fifth.
    /// A lodestone's sweep may climb a third octave.</summary>
    public static void Xp(int step, int merged, bool nearFull, bool sweep)
    {
        if (A is not { } a || !a.Gate("xp", 8, 100)) return;
        var ladder = sweep ? HighLadder : Ladder;
        int top = ladder.Length - 1;
        double f = 1174.66 * Semis(ladder[Math.Clamp(step, 0, top)]);
        double g = 0.036 * Math.Min(2.83, Math.Sqrt(Math.Max(1, merged)));
        a.Play(new Fm { F = f, Ratio = 3.0, Index = 0.3, A = 0.002, D = 0.09, G = g });
        a.Play(new Tone { F = f, A = 0.002, D = 0.09, G = g * 0.5, Detune = 7 });
        if (step > top) a.Play(new Tone { F = f * 2, A = 0.004, D = 0.14, G = g * 0.3, Verb = 0.4 });
        if (nearFull) a.Play(new Tone { F = f * 1.5, A = 0.003, D = 0.1, G = g * 0.35 });
    }

    /// <summary>A lodestone taken: the field breathed in (a rush of air rising) under a quick run up
    /// the ladder, before the stones pour in and carry it on.</summary>
    public static void Lodestone()
    {
        if (A is not { } a) return;
        double t = Now;
        a.Play(new Hiss { T = t, A = 0.55, D = 0.25, G = 0.09, Lp = 300, Lp2 = 3500, Brown = true, Bus = Bus.Ui });
        for (int i = 0; i < 8; i++)
            a.Play(new Fm { T = t + i * 0.045, F = 1174.66 * Semis(Ladder[i]), Ratio = 3.0, Index = 0.3, A = 0.002, D = 0.12, G = 0.03, Verb = 0.3, Bus = Bus.Ui });
    }

    /// <summary>A crowd going down at once: one falling layer under the separate kills, louder the
    /// more fell in the moment (S-08).</summary>
    public static void CrowdFall(int n)
    {
        if (A is not { } a || !a.Gate("crowdfall", 1, 70)) return;
        a.Play(new Hiss { D = 0.18 + 0.02 * Math.Min(8, n), G = Math.Min(0.11, 0.02 + 0.008 * n), Lp = 800, Brown = true });
    }

    /// <summary>A swell as a crowd melts (S-08): a sub thump and a root and fifth a step further up
    /// the ladder at each of the four thresholds, so a cleared swarm is heard rising to a peak.</summary>
    public static void Swell(int tier)
    {
        if (A is not { } a) return;
        double t = Now, f = 587.33 * Semis(Ladder[Math.Min(Ladder.Length - 1, 3 + tier * 2)]);
        a.Play(new Tone { T = t, F = 60, F2 = 35, D = 0.12 + 0.03 * tier, G = 0.28 + 0.05 * tier, Bus = Bus.Ui });
        a.Play(new Hiss { T = t, D = 0.3, G = 0.04 + 0.02 * tier, Lp = 800, Brown = true, Bus = Bus.Ui });
        a.Play(new Fm { T = t, F = f, Ratio = 2.01, Index = 0.6, A = 0.05, D = 0.8, G = 0.032 + 0.008 * tier, Verb = 0.6, Bus = Bus.Ui });
        a.Play(new Fm { T = t + 0.03, F = f * 1.5, Ratio = 2.01, Index = 0.5, A = 0.05, D = 0.8, G = 0.024 + 0.006 * tier, Verb = 0.6, Bus = Bus.Ui });
    }

    public static void Gold()
    {
        if (A is not { } a || !a.Gate("gold", 3, 80)) return;
        if (a.Gate("coins", 1, 180)) a.Play(new Clip { Of = "handleCoins", G = 0.22, Pitch = R(0.95, 1.25) });
        a.Play(new Fm { F = R(2400, 2700), Ratio = 1.93, Index = 1.5, D = 0.12, G = 0.035 });
        a.Play(new Fm { T = Now + 0.045, F = R(3100, 3500), Ratio = 1.93, Index = 1.5, D = 0.14, G = 0.03 });
    }

    /// <summary>Loot landing, by its tier (Rpg.LootTier: 0 Common to 6 Storied, then material, book,
    /// chart, draught, quest), from where it lands (docs/design/LOOT_DESIGN.md §8.1). Placeholders until
    /// a sound lead: each tier its own, the rarer the longer it rings, and none heard twice a second.</summary>
    public static void Drop(int tier, Where w = default)
    {
        if (A is not { } a || !a.Gate($"drop{tier}", 1, 500)) return;
        double pan = w.Pan, g = 0.6 + 0.4 * w.Near;
        switch (tier)
        {
            case 0: // Common: a dull clink, cloth and iron.
                a.Play(new Tone { F = R(140, 170), F2 = 85, D = 0.08, G = 0.06 * g, Pan = pan });
                a.Play(new Hiss { D = 0.05, G = 0.04 * g, Bp = R(800, 1000), Q = 1.5, Pan = pan });
                break;
            case 1: // Uncommon: the clink, and a soft high ring.
                a.Play(new Tone { F = R(150, 170), F2 = 90, D = 0.07, G = 0.05 * g, Pan = pan });
                a.Play(new Fm { T = Now + 0.03, F = 1568, Ratio = 2.0, Index = 0.6, D = 0.4, G = 0.025 * g, Pan = pan, Verb = 0.35 });
                break;
            case 2: // Rare: one clear bell, struck once.
                a.Play(new Fm { F = 880, Ratio = 3.5, Index = 1.6, A = 0.002, D = 1.3, G = 0.05 * g, Pan = pan, Verb = 0.45 });
                a.Play(new Fm { F = 1320, Ratio = 2.76, Index = 0.8, A = 0.002, D = 0.9, G = 0.02 * g, Pan = pan, Verb = 0.45 });
                break;
            case 3: // Epic: a struck bell held, with a low hum under it.
                a.Play(new Fm { F = 660, Ratio = 2.76, Index = 2.2, A = 0.002, D = 2.2, G = 0.06 * g, Pan = pan, Verb = 0.6 });
                a.Play(new Fm { F = 1320, Ratio = 3.5, Index = 1.0, A = 0.002, D = 1.6, G = 0.025 * g, Pan = pan, Verb = 0.6 });
                a.Play(new Tone { F = 110, A = 0.15, D = 1.8, G = 0.035 * g, Lp = 600, Pan = pan });
                break;
            case 4: // Set: two bells a fifth apart, struck together: a pair.
                a.Play(new Fm { F = 660, Ratio = 3.5, Index = 1.6, A = 0.002, D = 1.8, G = 0.05 * g, Pan = pan - 0.1, Verb = 0.55 });
                a.Play(new Fm { F = 990, Ratio = 3.5, Index = 1.6, A = 0.002, D = 1.8, G = 0.045 * g, Pan = pan + 0.1, Verb = 0.55 });
                a.Play(new Tone { F = 165, A = 0.1, D = 1.4, G = 0.025 * g, Lp = 700, Pan = pan });
                break;
            case 5 or 6: // Legendary, Storied: the toll (and its breath of fire).
                Toll(tier == 6);
                break;
            case 7: // Material: a soft pat.
                a.Play(new Tone { F = R(190, 220), F2 = 120, D = 0.05, G = 0.035 * g, Pan = pan });
                a.Play(new Hiss { D = 0.04, G = 0.025 * g, Lp = 900, Pan = pan });
                break;
            case 8 or 10: // Book, draught: a soft thump and a small glassy tick.
                a.Play(new Tone { F = 180, F2 = 110, D = 0.06, G = 0.04 * g, Pan = pan });
                a.Play(new Fm { T = Now + 0.02, F = 2093, Ratio = 2.0, Index = 0.4, D = 0.25, G = 0.015 * g, Pan = pan, Verb = 0.3 });
                break;
            case 9: // Chart: paper, and a small chime.
                a.Play(new Hiss { D = 0.18, G = 0.05 * g, Bp = 3000, Q = 0.8, Pan = pan });
                a.Play(new Fm { T = Now + 0.06, F = 2093, Ratio = 2.0, Index = 0.5, D = 0.5, G = 0.02 * g, Pan = pan, Verb = 0.4 });
                break;
            default: // Quest: a short warm chime.
                a.Play(new Fm { F = 523, Ratio = 2.0, Index = 0.5, D = 0.8, G = 0.035 * g, Pan = pan, Verb = 0.45 });
                a.Play(new Fm { T = Now + 0.08, F = 784, Ratio = 2.0, Index = 0.5, D = 0.8, G = 0.03 * g, Pan = pan, Verb = 0.45 });
                break;
        }
    }

    /// <summary>A Legendary has fallen: the horde's sound drops by half for a moment, and the toll
    /// sounds, a deep bell with its fifth and octave, long in the air, heard for nothing else; a
    /// rising shimmer after. Faint: the reminder while it lies untaken.</summary>
    public static void Toll(bool storied = false, bool faint = false)
    {
        if (A is not { } a || !a.Gate("toll", 1, faint ? 4000 : 900)) return;
        double g = faint ? 0.35 : 1;
        // The hush is the music's and the world's, never the fight's (combat: a warning under a duck is
        // a blow unheard). On the interface's bus, so the toll carries over the horde.
        if (!faint) a.DuckBeds(0.35f, 1.2);
        a.Play(new Tone { F = 55, A = 0.004, D = 0.6, G = 0.12 * g, Lp = 300, Bus = Bus.Ui });
        a.Play(new Fm { F = 98, Ratio = 2.76, Index = 3, A = 0.004, D = 6, G = 0.12 * g, Verb = 0.8, Bus = Bus.Ui });
        a.Play(new Fm { T = Now + 0.02, F = 147, Ratio = 3.01, Index = 1.5, A = 0.004, D = 5, G = 0.06 * g, Verb = 0.8, Bus = Bus.Ui });
        a.Play(new Fm { T = Now + 0.03, F = 196, Ratio = 2.0, Index = 1.0, A = 0.004, D = 4.5, G = 0.05 * g, Verb = 0.8, Bus = Bus.Ui });
        if (faint) return;
        a.Play(new Fm { T = Now + 0.45, F = 1760, F2 = 2637, A = 0.6, D = 2.2, G = 0.02, Ratio = 2.0, Index = 0.7, Verb = 0.85, Bus = Bus.Ui });
        if (storied) a.Play(new Hiss { T = Now + 0.5, A = 0.4, D = 1.6, G = 0.06, Lp = 1200, Verb = 0.5, Bus = Bus.Ui });
    }

    public static void Loot(bool rare = false)
    {
        if (A is not { } a) return;
        a.Play(new Fm { F = 1320, Ratio = 2.01, Index = 0.9, D = 0.7, G = 0.045, Verb = 0.4 });
        a.Play(new Fm { T = Now + 0.06, F = 1980, Ratio = 2.01, Index = 0.9, D = 0.8, G = 0.035, Verb = 0.4 });
        if (rare) a.Play(new Fm { T = Now + 0.14, F = 2640, Ratio = 3.01, Index = 0.7, D = 1.2, G = 0.03, Verb = 0.6 });
        a.Play(new Hiss { A = 0.05, D = 0.5, G = 0.02, Hp = 6000 });
        a.Play(new Clip { Of = "handleSmallLeather", G = 0.2, Pitch = R(0.9, 1.1) });
    }

    public static void Heal()
    {
        if (A is not { } a || !a.Gate("heal", 1, 400)) return;
        a.Play(new Fm { F = 660, Ratio = 2, Index = 0.5, A = 0.05, D = 0.6, G = 0.04, Verb = 0.5 });
        a.Play(new Fm { T = Now + 0.08, F = 990, Ratio = 2, Index = 0.5, A = 0.05, D = 0.7, G = 0.03, Verb = 0.5 });
    }

    /* ---------------------------------------------------------- growth --- */

    /// <summary>The most repeated reward, dark then light (S-04): the minor figure quick, landing on a
    /// held major third and fifth above it (the old Picardy cadence), so it resolves upward and
    /// reads as a gain. A milestone (a blessing next) has the evolution's low saw under it.</summary>
    public static void LevelUp(bool milestone = false)
    {
        if (A is not { } a) return;
        double b = 587.33, t = Now;
        int[] dark = [0, 3, 7];
        for (int i = 0; i < dark.Length; i++) a.Play(new Fm { T = t + i * 0.05, F = b * Semis(dark[i]), Ratio = 3.5, Index = 0.35, D = 0.6, G = 0.045, Verb = 0.5 });
        foreach (var s in new[] { 12, 16, 19 })
            a.Play(new Fm { T = t + 0.16, F = b * Semis(s), Ratio = 3.5, Index = 0.3, A = 0.01, D = 1.5, G = 0.04, Verb = 0.65 });
        a.Play(new Tone { F = 146.8, A = 0.2, D = 1.6, G = 0.1, Type = Wave.Triangle });
        a.Play(new Hiss { A = 0.3, D = 0.9, G = 0.025, Hp = 6500 });
        if (milestone) a.Play(new Tone { T = t + 0.16, F = 73.4, A = 0.25, D = 2.0, G = 0.12, Type = Wave.Saw, Lp = 400, Lp2 = 1400 });
    }

    public static void Evolve()
    {
        if (A is not { } a) return;
        a.DuckSfx(0.4f, 1.2);
        double b = 293.66;
        int[] steps = [0, 7, 12, 16, 19, 24];
        for (int i = 0; i < steps.Length; i++) a.Play(new Fm { T = Now + i * 0.09, F = b * Semis(steps[i]), Ratio = 2.01, Index = 0.8, D = 2.2, G = 0.045, Verb = 0.7 });
        a.Play(new Tone { F = 73.4, A = 0.3, D = 2.4, G = 0.16, Type = Wave.Saw, Lp = 400, Lp2 = 1400 });
    }

    /// <summary>What ruled the night falls: the fight's noise drops away, a blow from under the
    /// ground, the night's chord rising and held, a shimmer as the ember leaves it. (Its own
    /// sounds go round the duck, on the music and interface buses.)</summary>
    public static void Fall()
    {
        if (A is not { } a) return;
        double t = Now;
        a.DuckSfx(0.3f, 1.9);
        a.Play(new Tone { T = t, F = 55, F2 = 22, D = 2.4, G = 0.45, Bus = Bus.Ui });
        a.Play(new Hiss { T = t, D = 1.8, G = 0.15, Lp = 900, Lp2 = 80, Brown = true, Bus = Bus.Ui });
        int[] s = [0, 7, 12, 16, 19, 24];
        for (int i = 0; i < s.Length; i++)
            a.Play(new Fm { T = t + 0.35 + i * 0.11, F = 146.83 * Semis(s[i]), Ratio = 2.01, Index = 0.7, A = 0.08, D = 3.2, G = 0.045, Verb = 0.8, Bus = Bus.Music });
        a.Play(new Hiss { T = t + 0.3, A = 0.6, D = 2.4, G = 0.03, Hp = 7000, Bus = Bus.Ui });
    }

    /* ----------------------------------------------------------- a chest --- */

    /// <summary>The score's key, D minor, as a pentatonic ladder (semitones): what a chest's
    /// things land on, one step each, so the opening is a phrase and not a row of dings.</summary>
    static readonly int[] Ladder = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24];

    /// <summary>A chest held before it bursts: the wood strains, the lid knocks against its lock,
    /// a low swell rises under it. The fight is held down for the whole opening (its own sounds
    /// are on the interface bus, round the duck).</summary>
    public static void ChestShake(double seconds, double whole)
    {
        if (A is not { } a) return;
        double t = Now;
        a.DuckSfx(0.2f, whole);
        a.Play(new Hiss { T = t, A = seconds, D = 0.2, G = 0.07, Lp = 180, Lp2 = 2400, Brown = true, Bus = Bus.Ui });
        a.Play(new Tone { T = t, F = 55, F2 = 98, Glide = seconds, A = seconds, D = 0.25, G = 0.13, Type = Wave.Saw, Lp = 150, Lp2 = 900, Bus = Bus.Ui });
        a.Play(new Clip { T = t, Of = "creak", G = 0.28, Pitch = 0.72, Bus = Bus.Ui });
        for (int i = 0; i < 4; i++)
            a.Play(new Clip { T = t + seconds * (0.22 + i * 0.2), Of = "impactWood_medium", G = 0.07 + i * 0.04, Pitch = R(0.95, 1.2), Bus = Bus.Ui });
    }

    /// <summary>The lid thrown back and the light out of it: a blow from under, the wood's
    /// clap, a bright rush of air, and the jingle the chest's size earns: one thing, a bell
    /// figure; three, a drum and a held chord; five or a hoard, a choir and a gong.</summary>
    public static void ChestBurst(int count)
    {
        if (A is not { } a) return;
        double t = Now;
        a.Play(new Tone { T = t, F = 70, F2 = 30, D = 0.5, G = 0.42, Bus = Bus.Ui });
        a.Play(new Clip { T = t, Of = "impactWood_medium", G = 0.45, Pitch = 0.7, Bus = Bus.Ui });
        a.Play(new Hiss { T = t, A = 0.01, D = 0.7, G = 0.07, Hp = 5000, Verb = 0.5, Bus = Bus.Ui });
        double d = 293.66;
        if (count >= 5)
        {
            // A choir's chord swelling (detuned saws, soft), a gong under it.
            foreach (var s in new[] { 0, 7, 12, 16, 19 })
                for (int k = 0; k < 2; k++)
                    a.Play(new Tone { T = t + 0.05, F = d * Semis(s), Type = Wave.Saw, A = 0.6, Hold = 1.2, D = 1.6, G = 0.022, Lp = 600, Lp2 = 2200, Detune = k == 0 ? -9 : 9, Verb = 0.8, Bus = Bus.Music });
            a.Play(new Fm { T = t, F = 98, Ratio = 1.41, Index = 3.2, A = 0.01, D = 3.2, G = 0.12, Verb = 0.6, Bus = Bus.Ui });
            a.Play(new Fm { T = t, F = 196, Ratio = 2.76, Index = 1.4, A = 0.01, D = 2.4, G = 0.05, Verb = 0.6, Bus = Bus.Ui });
        }
        else if (count >= 3)
        {
            // A drum (two strokes) and a warm held chord.
            for (int i = 0; i < 2; i++)
            {
                a.Play(new Tone { T = t + 0.12 + i * 0.16, F = 110, F2 = 52, D = 0.35, G = 0.3, Bus = Bus.Ui });
                a.Play(new Hiss { T = t + 0.12 + i * 0.16, D = 0.12, G = 0.05, Bp = 900, Q = 1.2, Bus = Bus.Ui });
            }
            foreach (var s in new[] { 0, 7, 12, 15 })
                a.Play(new Tone { T = t + 0.1, F = d * Semis(s), Type = Wave.Triangle, A = 0.25, Hold = 0.6, D = 1.0, G = 0.03, Verb = 0.7, Bus = Bus.Music });
        }
        else
        {
            // A small bell figure, rising.
            int[] s = [0, 7, 12];
            for (int i = 0; i < s.Length; i++)
                a.Play(new Fm { T = t + 0.06 + i * 0.09, F = 2 * d * Semis(s[i]), Ratio = 3.01, Index = 0.6, D = 0.9, G = 0.035, Verb = 0.6, Bus = Bus.Ui });
        }
    }

    /// <summary>A thing out of a chest lands in its place: a clunk, and a bell one step further up
    /// the ladder than the last. An evolution lands on the night's chord instead, held.</summary>
    public static void ChestLand(int step, bool evolution)
    {
        if (A is not { } a) return;
        double t = Now;
        a.Play(new Clip { T = t, Of = "impactMetal_medium", G = 0.14, Pitch = R(0.85, 0.95), Lp = 3000, Bus = Bus.Ui });
        a.Play(new Tone { T = t, F = 140, F2 = 70, D = 0.12, G = 0.14, Bus = Bus.Ui });
        double f = 587.33 * Semis(Ladder[Math.Clamp(step, 0, Ladder.Length - 1)]);
        a.Play(new Fm { T = t, F = f, Ratio = 3.5, Index = 0.45, D = 1.1, G = 0.05, Verb = 0.6, Bus = Bus.Ui });
        a.Play(new Fm { T = t + 0.012, F = f * 2, Ratio = 2.01, Index = 0.3, D = 0.6, G = 0.018, Verb = 0.6, Bus = Bus.Ui });
        if (!evolution) return;
        int[] s = [0, 7, 12, 16, 19, 24];
        for (int i = 0; i < s.Length; i++)
            a.Play(new Fm { T = t + 0.05 + i * 0.07, F = 293.66 * Semis(s[i]), Ratio = 2.01, Index = 0.8, A = 0.02, D = 2.4, G = 0.04, Verb = 0.8, Bus = Bus.Music });
        a.Play(new Tone { T = t, F = 73.4, A = 0.15, D = 2.2, G = 0.14, Type = Wave.Saw, Lp = 400, Lp2 = 1400, Bus = Bus.Ui });
    }

    /// <summary>A reel's icon turning over: a dry tick, quieter as it slows.</summary>
    public static void ChestTick(double g)
    {
        if (A is not { } a || !a.Gate("chestTick", 3, 60)) return;
        a.Play(new Clip { Of = "tick", G = 0.05 * g, Pitch = R(1.3, 1.5), Bus = Bus.Ui });
    }

    /// <summary>The fight's noise held down for a big moment (an evolution, a chest), so it is heard.</summary>
    public static void Moment(double seconds, float depth = 0.4f) => A?.DuckSfx(depth, seconds);

    /* ------------------------------------------------------------ crafts --- */

    /// <summary>The hammer on the anvil: a count of blows for a temper (Brannoc tempers without a
    /// word, counting), one heavy blow for the rest, each ringing off into the smithy.</summary>
    public static void Anvil(int blows = 1)
    {
        if (A is not { } a) return;
        bool rec = Recordings.Pick("anvil") != null;
        for (int i = 0; i < blows; i++)
        {
            double t = Now + i * 0.26;
            if (rec) a.Play(new Clip { Of = "anvil", T = t, G = 0.42, Pitch = R(0.97, 1.03) - i * 0.015, Verb = 0.3, Bus = Bus.Ui });
            a.Play(new Clip { Of = "impactMetal_heavy", T = t, G = 0.16, Pitch = R(0.85, 0.95), Verb = 0.25, Bus = Bus.Ui });
            a.Play(new Fm { T = t, F = 1320 * R(0.98, 1.02), Ratio = 2.76, Index = 1.4, D = 1.1, G = 0.025, Verb = 0.6, Bus = Bus.Ui });
        }
    }

    /// <summary>A coal shut in its cage: a struck bell, and a hiss as the ember settles.</summary>
    public static void Cage()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "impactBell_heavy", G = 0.22, Pitch = R(0.8, 0.88), Verb = 0.5, Bus = Bus.Ui });
        a.Play(new Hiss { T = Now + 0.08, D = 0.9, G = 0.07, Bp = 3200, Bp2 = 900, Q = 1.2, Verb = 0.3, Bus = Bus.Ui });
        a.Play(new Fm { T = Now + 0.05, F = 660, Ratio = 3.01, Index = 0.8, D = 1.8, G = 0.03, Verb = 0.8, Bus = Bus.Ui });
    }

    /// <summary>A draught poured off the still: glass set down, a pour, a cork.</summary>
    public static void Pour()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "impactGlass_light", G = 0.22, Pitch = R(1.05, 1.15), Bus = Bus.Ui });
        a.Play(new Hiss { T = Now + 0.06, D = 0.5, G = 0.06, Bp = 1400, Bp2 = 700, Q = 3, Bus = Bus.Ui });
        for (int i = 0; i < 5; i++) a.Play(new Tone { T = Now + 0.1 + i * 0.07 + R(0, 0.03), F = R(500, 900), F2 = R(900, 1400), D = 0.05, G = 0.02, Bus = Bus.Ui });
        a.Play(new Clip { Of = "impactWood_medium", T = Now + 0.55, G = 0.12, Pitch = R(1.6, 1.8), Bus = Bus.Ui });
    }

    public static void Discovery()
    {
        if (A is not { } a) return;
        int[] steps = [0, 3, 10];
        for (int i = 0; i < steps.Length; i++) a.Play(new Fm { T = Now + i * 0.16, F = 880 * Semis(steps[i]), Ratio = 3.01, Index = 0.5, D = 1.6, G = 0.04, Verb = 0.7, Bus = Bus.Ui });
    }

    /* ------------------------------------------------------------ story --- */

    public static void Stinger(string kind)
    {
        if (A is not { } a) return;
        double t = Now;
        switch (kind)
        {
            case "boss" or "danger":
            {
                bool big = kind == "boss";
                foreach (var f in big ? new[] { 73.4, 110, 146.8 } : new[] { 110, 164.8 })
                    a.Play(new Tone { T = t, F = f, Type = Wave.Saw, A = 0.4, D = big ? 2.6 : 1.4, G = big ? 0.07 : 0.05, Lp = 350, Lp2 = 1500, Detune = R(-8, 8), Bus = Bus.Music, Verb = 0.5 });
                a.Play(new Tone { T = t, F = 60, F2 = 30, D = 1.2, G = big ? 0.4 : 0.25 });
                a.Play(new Hiss { T = t, D = 1, G = 0.12, Lp = 700, Lp2 = 100, Brown = true });
                break;
            }
            case "triumph":
            {
                int[] s = [0, 4, 7, 12];
                for (int i = 0; i < s.Length; i++) a.Play(new Tone { T = t + 0.25 + i * 0.12, F = 293.66 * Semis(s[i]), Type = Wave.Triangle, A = 0.05, D = 1.8, G = 0.06, Bus = Bus.Music, Verb = 0.6 });
                break;
            }
            case "story":
            {
                int[] s = [0, 5, 7];
                for (int i = 0; i < s.Length; i++) a.Play(new Fm { T = t + i * 0.22, F = 440 * Semis(s[i]), Ratio = 2.01, Index = 0.6, D = 1.8, G = 0.04, Verb = 0.7, Bus = Bus.Ui });
                break;
            }
            case "pull":
            {
                // Pulled into an arena: a rush that climbs, a chord under it, and a blow as it lands.
                a.Play(new Hiss { T = t, D = 1.1, G = 0.16, Lp = 300, Lp2 = 3500, Brown = true });
                foreach (var f in new[] { 55.0, 82.4, 110 })
                    a.Play(new Tone { T = t, F = f, F2 = f * 1.5, Type = Wave.Saw, A = 0.7, D = 0.9, G = 0.05, Lp = 300, Lp2 = 1600, Detune = R(-6, 6), Bus = Bus.Music, Verb = 0.5 });
                a.Play(new Tone { T = t + 1.05, F = 70, F2 = 28, D = 1.4, G = 0.45 });
                a.Play(new Hiss { T = t + 1.05, D = 0.8, G = 0.1, Lp = 900, Lp2 = 120, Brown = true });
                break;
            }
            case "zone":
                a.Play(new Tone { T = t, F = 146.8, Type = Wave.Triangle, A = 0.6, D = 2.8, G = 0.05, Bus = Bus.Music, Verb = 0.8 });
                a.Play(new Tone { T = t + 0.3, F = 220, Type = Wave.Triangle, A = 0.6, D = 2.6, G = 0.04, Bus = Bus.Music, Verb = 0.8 });
                a.Play(new Fm { T = t + 0.6, F = 587.3, Ratio = 3.5, Index = 0.3, D = 2.4, G = 0.03, Verb = 0.9, Bus = Bus.Music });
                break;
        }
    }

    /// <summary>A cinematic's sound, by its cue name: made here for what the
    /// recordings lack (water closing over a head, a drip on stone, an owl,
    /// frost cracking), or a recording by its family's name. Temp sound,
    /// until the cinematics' own recordings come (docs/team/cinematics.md).</summary>
    public static void Cine(string name, double gain = 1, double pan = 0)
    {
        if (A is not { } a) return;
        double t = Now, g = gain;
        switch (name)
        {
            case "water_close":
                // Under: a muffled closing, a weight, bubbles going up past the ear.
                a.Play(new Hiss { T = t, A = 0.04, D = 1.6, G = 0.32 * g, Lp = 520, Lp2 = 110, Brown = true });
                a.Play(new Tone { T = t, F = 58, F2 = 34, D = 1.3, G = 0.42 * g });
                for (int i = 0; i < 9; i++)
                {
                    double bt = t + 0.12 + i * R(0.06, 0.14);
                    a.Play(new Tone { T = bt, F = R(260, 420), F2 = R(700, 1100), D = R(0.04, 0.08), G = 0.035 * g * (1 - i / 11.0), Lp = 1400, Pan = R(-0.3, 0.3) });
                }
                break;
            case "drip":
                a.Play(new Tone { T = t, F = R(1250, 1500), F2 = R(520, 640), D = 0.09, G = 0.11 * g, Verb = 0.35, Pan = pan });
                a.Play(new Tone { T = t + 0.004, F = 2700, F2 = 1800, D = 0.03, G = 0.04 * g, Pan = pan });
                break;
            case "owl":
                foreach (var (dt, f) in new[] { (0.0, 392.0), (0.62, 349.0), (0.9, 349.0) })
                    a.Play(new Tone { T = t + dt, F = f, F2 = f * 0.94, Type = Wave.Triangle, A = 0.06, D = 0.34, G = 0.045 * g, Lp = 900, Verb = 0.8, Bus = Bus.Amb, Pan = pan });
                break;
            case "frost_crack":
                // Frost splitting in a line: a run of small cracks, then the ground giving.
                for (int i = 0; i < 14; i++)
                    a.Play(new Hiss { T = t + i * R(0.03, 0.07), D = R(0.02, 0.05), G = R(0.05, 0.11) * g, Bp = R(1800, 4200), Q = 4, Pan = pan + R(-0.15, 0.15) });
                a.Play(new Tone { T = t + 0.55, F = 46, F2 = 28, D = 1.1, G = 0.5 * g });
                a.Play(new Hiss { T = t + 0.55, D = 0.9, G = 0.18 * g, Lp = 260, Lp2 = 90, Brown = true });
                break;
            case "roots":
                for (int i = 0; i < 7; i++)
                    a.Play(new Hiss { T = t + i * R(0.08, 0.16), D = R(0.06, 0.12), G = 0.06 * g, Bp = R(500, 1100), Q = 2.5, Brown = true, Pan = pan });
                break;
            case "rasp":
                // A breath with no breath in it.
                a.Play(new Hiss { T = t, A = 0.35, D = 1.2, G = 0.07 * g, Bp = 850, Bp2 = 600, Q = 1.6, Brown = true, Pan = pan });
                break;
            case "breath_out":
                a.Play(new Hiss { T = t, A = 0.25, D = 1.4, G = 0.05 * g, Bp = 1500, Bp2 = 900, Q = 0.9, Pan = pan });
                break;
            case "cloth_water":
                a.Play(new Hiss { T = t, A = 0.05, D = 0.9, G = 0.06 * g, Bp = 2400, Q = 0.7, Pan = pan });
                for (int i = 0; i < 4; i++) a.Play(new Tone { T = t + 0.2 + i * R(0.12, 0.2), F = R(1100, 1500), F2 = R(500, 700), D = 0.07, G = 0.05 * g, Verb = 0.3, Pan = pan });
                break;
            case "hit":
                // As the weapon comes up: a deep drum under a scrape of metal.
                a.Play(new Tone { T = t, F = 62, F2 = 33, D = 1.5, G = 0.55 * g });
                a.Play(new Hiss { T = t, D = 0.5, G = 0.2 * g, Lp = 400, Lp2 = 100, Brown = true });
                a.Play(new Hiss { T = t + 0.02, A = 0.05, D = 0.9, G = 0.06 * g, Bp = 3400, Bp2 = 2600, Q = 7, Verb = 0.5 });
                a.Play(new Tone { T = t, F = 110, Type = Wave.Saw, D = 1.8, G = 0.05 * g, Lp = 700, Lp2 = 200, Bus = Bus.Music, Verb = 0.6 });
                break;
            case "drone":
                // The Night's root, bowed and breathing, up from nothing over four seconds.
                foreach (var f in new[] { 55.0, 82.41, 110.0 })
                    a.Play(new Tone { T = t, F = f, Type = Wave.Saw, A = 4, Hold = 3, D = 4, G = 0.045 * g, Lp = 260, Lp2 = 520, Detune = R(-7, 7), Bus = Bus.Music, Verb = 0.7 });
                a.Play(new Hiss { T = t, A = 4, D = 6, G = 0.035 * g, Bp = 700, Q = 1.2, Bus = Bus.Music, Verb = 0.6 });
                break;
            // C03's (docs/cinematics/shoot/c03.md), made until they are recorded.
            case "kneel_water":
                // A great weight going down into the river: a heavy slap and the water closing.
                a.Play(new Tone { T = t, F = 90, F2 = 46, D = 0.5, G = 0.32 * g, Pan = pan });
                a.Play(new Hiss { T = t, A = 0.01, D = 0.7, G = 0.13 * g, Bp = 1200, Bp2 = 500, Q = 0.8, Pan = pan });
                break;
            case "sink":
                // The greatsword going under: a long bubble, rising.
                for (int i = 0; i < 6; i++)
                    a.Play(new Tone { T = t + i * R(0.12, 0.22), F = R(220, 320), F2 = R(600, 900), D = R(0.06, 0.1), G = 0.04 * g * (1 - i / 8.0), Lp = 1600, Pan = pan });
                a.Play(new Tone { T = t, F = 70, F2 = 40, D = 0.6, G = 0.18 * g });
                break;
            case "lamp_out":
                // The flame into the water: a hiss of steam, a small pop, then nothing.
                a.Play(new Hiss { T = t, A = 0.005, D = 0.9, G = 0.12 * g, Bp = 4200, Bp2 = 2200, Q = 1.2, Pan = pan });
                a.Play(new Tone { T = t, F = 420, F2 = 160, D = 0.08, G = 0.08 * g, Pan = pan });
                break;
            case "heart_hum":
                // A wet finger round a glass rim: a pure tone and its fifth, slow to come.
                a.Play(new Tone { T = t, F = 740, F2 = 752, A = 0.8, Hold = 1.6, D = 1.4, G = 0.035 * g, Verb = 0.6, Pan = pan });
                a.Play(new Tone { T = t + 0.2, F = 1110, F2 = 1122, A = 0.9, Hold = 1.2, D = 1.4, G = 0.014 * g, Verb = 0.6, Pan = pan });
                break;
            case "burst":
                // The mud bursting up: a wet thump, earth and gravel, stones rattling down.
                a.Play(new Tone { T = t, F = 72, F2 = 30, D = 0.8, G = 0.6 * g });
                a.Play(new Hiss { T = t, A = 0.005, D = 1.0, G = 0.3 * g, Lp = 900, Lp2 = 200, Brown = true, Pan = pan });
                for (int i = 0; i < 10; i++)
                    a.Play(new Hiss { T = t + 0.15 + i * R(0.04, 0.09), D = R(0.02, 0.05), G = R(0.03, 0.07) * g, Bp = R(1500, 3500), Q = 3, Pan = pan + R(-0.3, 0.3) });
                break;
            case "sniff":
                a.Play(new Hiss { T = t, A = 0.02, D = 0.12, G = 0.07 * g, Bp = 2600, Q = 1.4, Pan = pan });
                a.Play(new Hiss { T = t + 0.16, A = 0.02, D = 0.1, G = 0.06 * g, Bp = 2900, Q = 1.4, Pan = pan });
                break;
            case "groan":
                // Under everything: first felt more than heard, then timber taking a load, 3 s.
                a.Play(new Tone { T = t, F = 31, F2 = 27, A = 1.0, Hold = 1.6, D = 1.4, G = 0.5 * g });
                a.Play(new Tone { T = t + 0.6, F = 52, F2 = 44, Type = Wave.Saw, A = 0.8, Hold = 1.4, D = 1.2, G = 0.06 * g, Lp = 320, Lp2 = 180, Verb = 0.5 });
                a.Play(new Hiss { T = t + 0.4, A = 1.0, D = 2.0, G = 0.06 * g, Lp = 220, Lp2 = 90, Brown = true });
                break;
            default:
                a.Play(new Clip { T = t, Of = name, G = 0.3 * g, Pan = pan });
                break;
        }
    }

    public static void Death()
    {
        if (A is not { } a) return;
        a.Play(new Tone { F = 110, F2 = 36, Type = Wave.Saw, A = 0.1, D = 2.8, G = 0.12, Lp = 700, Lp2 = 120, Bus = Bus.Music, Verb = 0.7 });
        a.Play(new Tone { F = 55, F2 = 27, A = 0.1, D = 2.6, G = 0.25 });
        a.Play(new Hiss { A = 1.2, D = 1.2, G = 0.06, Bp = 900, Bp2 = 250, Q = 0.7 });
    }

    public static void Quest()
    {
        if (A is not { } a) return;
        a.Play(new Tone { F = 440, Type = Wave.Triangle, A = 0.02, D = 0.35, G = 0.05, Bus = Bus.Ui, Verb = 0.4 });
        a.Play(new Tone { T = Now + 0.14, F = 587.33, Type = Wave.Triangle, A = 0.02, D = 0.7, G = 0.05, Bus = Bus.Ui, Verb = 0.5 });
    }

    public static void Rel(bool good)
    {
        if (A is not { } a) return;
        double f = good ? 659.25 : 415.3;
        a.Play(new Fm { F = f, Ratio = 2, Index = 0.4, D = 0.6, G = 0.03, Bus = Bus.Ui, Verb = 0.5 });
        a.Play(new Fm { T = Now + 0.1, F = good ? f * Semis(4) : f * Semis(-3), Ratio = 2, Index = 0.4, D = 0.7, G = 0.025, Bus = Bus.Ui, Verb = 0.5 });
    }

    /// <summary>A people's tell, a moment before its rush (combat's charge
    /// director): the Pack's howl, the Kerchiefs' drum, a Lampling's fuse, the
    /// barrow's whistle. Recorded takes (tools/comfy/sfx_clips.py), heard over
    /// the fight and never quite the same twice; a made sound if a take is
    /// missing, so a tell is never silent.</summary>
    public static void Tell(string id)
    {
        if (A is not { } a || !a.Gate("tell", 1, 900)) return;
        if (Recordings.Has(id))
        {
            a.Play(new Clip { Of = id, G = id == "tell_fuse" ? 0.5 : 0.62, Pitch = R(0.94, 1.05), Verb = id == "tell_fuse" ? 0.15 : 0.45 });
            return;
        }
        switch (id)
        {
            case "tell_howl":
                a.Play(new Tone { F = 420, F2 = 620, D = 1.6, G = 0.08, Type = Wave.Triangle, Verb = 0.6 });
                break;
            case "tell_drum":
                for (int i = 0; i < 3; i++) a.Play(new Tone { T = Now + i * 0.42, F = 70, F2 = 42, D = 0.5, G = 0.3, Verb = 0.4 });
                break;
            case "tell_fuse":
                a.Play(new Hiss { D = 1.1, G = 0.08, Hp = 3500, Verb = 0.1 });
                break;
            default:
                a.Play(new Fm { F = 1900, Ratio = 2.01, Index = 0.4, D = 0.6, G = 0.05, Verb = 0.6 });
                break;
        }
    }

    public static void Door()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "doorOpen", G = 0.4, Pitch = R(0.9, 1.05), Verb = 0.2 });
        a.Play(new Clip { Of = "creak", T = Now + 0.05, G = 0.18, Pitch = R(0.9, 1.1), Verb = 0.2 });
    }

    /// <summary>A footstep, on grass, dirt, stone or boards.</summary>
    public static void Step(string surface, double g = 1)
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = $"footstep_{surface}", G = 0.16 * g, Pitch = R(0.9, 1.1), Lp = surface == "grass" ? 2600 : null });
    }

    /* -------------------------------------------------------- interface --- */

    public static void Hover() { if (A is { } a && a.Gate("hover", 1, 45)) a.Play(new Clip { Of = "tick", G = 0.05, Pitch = R(1.1, 1.25), Bus = Bus.Ui }); }

    public static void Click()
    {
        if (A is not { } a || !a.Gate("click", 2, 60)) return;
        a.Play(new Clip { Of = "click", G = 0.2, Pitch = R(0.95, 1.05), Bus = Bus.Ui });
    }

    public static void Open()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "open", G = 0.18, Bus = Bus.Ui });
        a.Play(new Hiss { A = 0.03, D = 0.2, G = 0.025, Bp = 1600, Bp2 = 900, Q = 0.7, Bus = Bus.Ui });
    }

    public static void Close() => A?.Play(new Clip { Of = "close", G = 0.16, Bus = Bus.Ui });

    public static void Page() { if (A is { } a && a.Gate("page", 1, 120)) a.Play(new Clip { Of = "bookFlip", G = 0.2, Pitch = R(0.95, 1.1), Bus = Bus.Ui }); }

    /// <summary>The tab chain dragged to another tab (tools/uiforge/chainanim.py; heavy forged
    /// chain, the owner: "a little wimpy"). Each link that runs by knocks low iron with a thud of
    /// body under it, timed as the chain moves on its spring (a slow start, quickest early, then
    /// easing). Under them the drag, a grinding rumble. Then a solid clunk as it stops, a chink
    /// as it settles, a softer one as it swings back, and the hiss of the new links taking the
    /// heat. `links` is how many links pass; `secs` stretches the timing (0.32: the game's slide).</summary>
    public static void ChainSlide(int links = 6, double secs = 0.32)
    {
        if (A is not { } a || !a.Gate("chain", 1, 120)) return;
        int n = Math.Clamp(links, 2, 14);
        double t0 = Now, k = secs / 0.32;
        for (int i = 0; i < n; i++)
        {
            double u = (i + 0.5) / n;
            double t = t0 + k * (0.025 + 0.2 * u + 0.04 * u * u) + R(-0.004, 0.004);
            double g = (1.0 - 0.4 * u) * R(0.8, 1.15);
            a.Play(new Fm { T = t, F = R(700, 1300), Ratio = R(1.4, 2.6), Index = R(3, 5), D = R(0.07, 0.13), G = 0.035 * g, Pan = R(-0.15, 0.15), Verb = 0.15, Bus = Bus.Ui });
            double f = R(150, 230);
            a.Play(new Tone { T = t, F = f, F2 = f * 0.8, D = 0.05, G = 0.025 * g, Lp = 500, Bus = Bus.Ui });
        }
        a.Play(new Hiss { T = t0 + 0.02 * k, A = 0.05, D = 0.26 * k, G = 0.035, Lp = 900, Brown = true, Bus = Bus.Ui });
        double stop = t0 + 0.29 * k;
        a.Play(new Tone { T = stop, F = 92, F2 = 68, D = 0.25, G = 0.09, Lp = 380, Bus = Bus.Ui });
        a.Play(new Fm { T = stop, F = R(380, 440), Ratio = 1.41, Index = 4, D = 0.32, G = 0.05, Verb = 0.3, Bus = Bus.Ui });
        a.Play(new Hiss { T = stop, D = 0.07, G = 0.04, Bp = 700, Q = 1, Bus = Bus.Ui });
        a.Play(new Fm { T = stop + 0.17, F = R(1300, 1600), Ratio = 2.76, Index = 2.8, D = 0.14, G = 0.022, Verb = 0.25, Bus = Bus.Ui });
        a.Play(new Fm { T = stop + 0.42, F = R(1500, 1800), Ratio = 3.1, Index = 2.2, D = 0.1, G = 0.01, Verb = 0.25, Bus = Bus.Ui });
        a.Play(new Hiss { T = stop - 0.05, A = 0.18, D = 0.7, G = 0.014, Hp = 4500, Bus = Bus.Ui });
    }

    public static void Pick()
    {
        if (A is not { } a) return;
        a.Play(new Fm { F = 740, Ratio = 2, Index = 0.7, D = 0.3, G = 0.04, Bus = Bus.Ui, Verb = 0.3 });
        a.Play(new Tone { F = 220, F2 = 180, D = 0.12, G = 0.04, Bus = Bus.Ui });
    }

    public static void Equip()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "cloth", G = 0.25, Pitch = R(0.95, 1.05), Bus = Bus.Ui });
        a.Play(new Fm { F = R(380, 460), Ratio = 1.41, Index = 2.2, D = 0.22, G = 0.04, Bus = Bus.Ui });
        a.Play(new Hiss { D = 0.06, G = 0.03, Bp = 1800, Bus = Bus.Ui });
    }

    public static void Deny()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "error", G = 0.18, Pitch = 0.9, Bus = Bus.Ui });
    }
}
