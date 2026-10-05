using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

/// <summary>
/// Each skill's own voice, by its art: what it sounds like as it leaves her (a bowstring, a cold
/// chime, a fuse's fizz, chain running out), as it lands (a clay pot cracking, thunder, a moon
/// breaking like glass), and a little of itself on every hit (steel ringing on a chakram, a palm's
/// thump). The school's sounds stay under them; these say which skill it was. Each is gated, so a
/// crowd struck a hundred times a second is told by a few.
///
/// Made, not recorded, but for the few real things a recording does best (Recordings: chain, glass,
/// a bell, a knife, clay), pitched a little differently each time.
/// </summary>
public static partial class Sfx
{
    /// <summary>A skill leaving her (Ev.Muzzle): its own voice, or the school's if it has none.</summary>
    public static void Cast(string? art, School school, Where w = default)
    {
        if (A is not { } a) return;
        double p = w.Pan, t = Now;
        switch (art)
        {
            case "arrow" or "arrow_mark" or "arrow_rain":
                if (!a.Gate("cast:bow", 3, 110)) return;
                // The string: a dull pluck falling in pitch, and the fletching's hiss.
                a.Play(new Tone { F = R(190, 230), F2 = 105, Type = Wave.Triangle, D = 0.09, G = 0.06, Pan = p });
                a.Play(new Hiss { D = 0.07, G = 0.035, Bp = R(2400, 3000), Q = 1.6, Pan = p });
                if (art == "arrow_mark") a.Play(new Fm { F = R(1500, 1700), Ratio = 2, Index = 1, D = 0.18, G = 0.015, Pan = p });
                return;
            case "dagger" or "dagger_flurry" or "dagger_blood":
                if (!a.Gate("cast:knife", 3, 90)) return;
                a.Play(new Clip { Of = "drawKnife", G = 0.12, Pitch = R(1.15, 1.4), Pan = p });
                a.Play(new Hiss { A = 0.005, D = 0.08, G = 0.035, Bp = R(3200, 4200), Q = 2, Pan = p });
                return;
            case "chakram" or "chakram_razor" or "chakram_hail":
                if (!a.Gate("cast:chakram", 2, 200)) return;
                // A whirring blade: wind cut in a rising band, and steel ringing as it goes.
                a.Play(new Hiss { A = 0.03, D = 0.4, G = 0.05, Bp = 900, Bp2 = 2200, Q = 3, Pan = p });
                a.Play(new Fm { F = R(950, 1100), Ratio = 1.41, Index = 2.2, D = 0.45, G = 0.018, Pan = p, Verb = 0.2 });
                return;
            case "disc" or "disc_aegis" or "disc_reckon":
                if (!a.Gate("cast:disc", 2, 200)) return;
                a.Play(new Fm { F = R(700, 760), Ratio = 2, Index = 1.1, D = 0.55, G = 0.03, Pan = p, Verb = 0.4 });
                a.Play(new Hiss { A = 0.03, D = 0.3, G = 0.035, Bp = 1400, Bp2 = 2600, Q = 2.5, Pan = p });
                return;
            case "firepot":
                if (!a.Gate("cast:pot", 2, 250)) return;
                // Thrown: a fuse fizzing as it goes.
                a.Play(new Hiss { A = 0.01, D = 0.35, G = 0.045, Bp = R(4500, 5500), Q = 2.5, Pan = p });
                a.Play(new Tone { F = 160, F2 = 90, D = 0.08, G = 0.04, Pan = p });
                return;
            case "mote" or "mote_cascade" or "mote_star":
                if (!a.Gate("cast:mote", 3, 140)) return;
                // Small lights loosed: a soft chime off a pentatonic, each a different note.
                double[] notes = { 1046.5, 1174.7, 1318.5, 1568.0, 1760.0 };
                a.Play(new Fm { F = notes[(int)R(0, 4.99)], Ratio = 3, Index = 0.7, A = 0.005, D = 0.4, G = 0.018, Pan = p, Verb = 0.5 });
                return;
            case "moon" or "moon_brand":
                if (!a.Gate("cast:moon", 2, 250)) return;
                // Moonlight drawn: a cold, bell-like chime, out of tune with itself, and a breath.
                a.Play(new Fm { F = R(1250, 1400), Ratio = 2.76, Index = 1.3, A = 0.01, D = 0.75, G = 0.026, Pan = p, Verb = 0.6 });
                a.Play(new Hiss { A = 0.06, D = 0.3, G = 0.02, Bp = 6000, Q = 1.5, Pan = p, Verb = 0.3 });
                return;
            case "cinder" or "living_flame" or "star" or "frostfire":
                if (!a.Gate("cast:fire", 2, 200)) return;
                // A ball of fire away: a rush of flame rising in a band, and its low roar.
                a.Play(new Hiss { A = 0.03, D = 0.32, G = 0.07, Bp = 500, Bp2 = 1700, Q = 0.8, Pan = p });
                a.Play(new Tone { F = 85, F2 = 140, Type = Wave.Saw, A = 0.02, D = 0.28, G = 0.035, Lp = 380, Pan = p });
                if (art == "frostfire") a.Play(new Fm { T = t + 0.04, F = R(2100, 2400), Ratio = 3.1, Index = 1, D = 0.35, G = 0.018, Pan = p, Verb = 0.4 });
                return;
            case "shard" or "shard_deep" or "spear_ice":
                if (!a.Gate("cast:ice", 3, 120)) return;
                a.Play(new Clip { Of = "impactGlass_light", G = 0.1, Pitch = R(1.5, 1.9), Pan = p, Verb = 0.25 });
                a.Play(new Fm { F = R(2300, 2700), Ratio = 3.07, Index = 1.2, D = 0.18, G = 0.015, Pan = p });
                return;
            case "umbral" or "ruin" or "siphon":
                if (!a.Gate("cast:dark", 2, 160)) return;
                // Shadow loosed: a hollow whisper and a low growl under it.
                a.Play(new Hiss { A = 0.04, D = 0.38, G = 0.045, Bp = R(800, 1000), Q = 5, Pan = p, Verb = 0.3 });
                a.Play(new Tone { F = R(70, 85), F2 = 55, Type = Wave.Saw, A = 0.03, D = 0.35, G = 0.045, Lp = 320, Pan = p });
                return;
            case "tether" or "tether2" or "tether_mark":
                if (!a.Gate("cast:chain", 2, 200)) return;
                a.Play(new Clip { Of = "chainDrag", G = 0.16, Pitch = R(1.0, 1.2), Pan = p });
                return;
            case "herd" or "herd_great" or "herd_hunt":
                if (!a.Gate("cast:herd", 2, 300)) return;
                // Spirits loosed: a rush of wind going past.
                a.Play(new Hiss { A = 0.08, D = 0.5, G = 0.05, Bp = 700, Bp2 = 1800, Q = 1.2, Pan = p, Verb = 0.3 });
                return;
            default:
                Shoot(school, w);
                return;
        }
    }

    /// <summary>A blade's or a palm's swing (Ev.Slash), by its art.</summary>
    public static void Swing(string? art, Where w)
    {
        if (A is not { } a) return;
        double p = w.Pan;
        switch (art)
        {
            case "slash_steel" or "slash_holy" or "slash_blood":
                if (!a.Gate("swing:blade", 3, 110)) return;
                a.Play(new Hiss { A = 0.01, D = 0.12, G = 0.06, Bp = R(1900, 2500), Bp2 = 700, Q = 1.6, Pan = p });
                a.Play(art == "slash_holy"
                    ? new Fm { F = R(880, 960), Ratio = 2, Index = 0.9, D = 0.4, G = 0.02, Pan = p, Verb = 0.4 }
                    : new Fm { F = R(1500, 1800), Ratio = 1.41, Index = 2, D = 0.18, G = 0.012, Pan = p });
                return;
            case "slash_heavy" or "slash_spin" or "slash_quake":
                if (!a.Gate("swing:heavy", 2, 150)) return;
                // A heavy edge: a low whoosh and the weight behind it.
                a.Play(new Hiss { A = 0.02, D = 0.2, G = 0.08, Bp = 650, Bp2 = 250, Q = 1.2, Pan = p });
                a.Play(new Tone { F = 75, F2 = 42, D = 0.18, G = 0.07, Pan = p });
                return;
            case "palm" or "palm_temple" or "palm_storm":
                if (!a.Gate("swing:palm", 2, 150)) return;
                // An open hand's force: a thump in the chest and the air pushed out.
                a.Play(new Tone { F = 115, F2 = 45, D = 0.18, G = 0.11, Pan = p });
                a.Play(new Hiss { A = 0.005, D = 0.13, G = 0.07, Lp = 1000, Lp2 = 250, Pan = p });
                if (art == "palm_storm") a.Play(new Hiss { D = 0.08, G = 0.05, Bp = 3500, Q = 0.7, Pan = p });
                return;
            default:
                Swing(w);
                return;
        }
    }

    /// <summary>A blast by its art (Ev.Explosion): a firepot's clay cracking, frost shattering.</summary>
    public static void Burst(string? art, double power, Where w)
    {
        Explosion(power, w);
        if (A is not { } a) return;
        double p = w.Pan, g = 0.5 + 0.5 * w.Near;
        switch (art)
        {
            case "firepot" when a.Gate("burst:pot", 2, 150):
                a.Play(new Clip { Of = "impactPlate_medium", G = 0.18 * g, Pitch = R(0.62, 0.75), Pan = p });
                a.Play(new Hiss { T = Now + 0.03, A = 0.02, D = 0.5, G = 0.08 * g, Bp = 400, Bp2 = 1400, Q = 0.7, Pan = p });
                break;
            case "frostfire" when a.Gate("burst:frostfire", 2, 150):
                a.Play(new Clip { Of = "impactGlass_light", G = 0.22 * g, Pitch = R(0.85, 1.0), Pan = p, Verb = 0.3 });
                a.Play(new Fm { F = R(1900, 2200), Ratio = 2.76, Index = 2.5, D = 0.5, G = 0.025 * g, Pan = p, Verb = 0.4 });
                break;
        }
    }

    /// <summary>A blow from the sky (Ev.Strike), heard as it lands, `delay` from now.</summary>
    public static void Falling(string? art, double delay, Where w)
    {
        if (A is not { } a) return;
        double p = w.Pan, t = Now + System.Math.Max(0, delay), g = 0.5 + 0.5 * w.Near;
        switch (art)
        {
            case "storm_bolt" or "storm_eye" or "storm_clap" or "arc_sky":
            {
                if (!a.Gate("fall:thunder", 3, 160)) return;
                double k = art == "storm_clap" ? 1.4 : art == "arc_sky" ? 0.6 : 1;
                // The crack, then the rumble rolling after it.
                a.Play(new Hiss { T = t, A = 0.001, D = 0.1, G = 0.13 * k * g, Hp = 1800, Pan = p });
                a.Play(new Hiss { T = t + 0.02, A = 0.01, D = 0.9 * k, G = 0.12 * k * g, Lp = 900, Lp2 = 110, Brown = true, Pan = p });
                a.Play(new Tone { T = t, F = 62, F2 = 30, D = 0.5, G = 0.1 * k * g, Pan = p });
                return;
            }
            case "moonfall":
                if (!a.Gate("fall:moon", 2, 200)) return;
                // A moon coming down: a falling glassy note, and a soft deep landing.
                a.Play(new Fm { T = t - 0.25, F = 1900, F2 = 950, Ratio = 2.76, Index = 1, D = 0.45, G = 0.022 * g, Pan = p, Verb = 0.6 });
                a.Play(new Tone { T = t, F = 90, F2 = 40, D = 0.4, G = 0.1 * g, Pan = p });
                a.Play(new Clip { T = t, Of = "impactGlass_light", G = 0.12 * g, Pitch = R(0.7, 0.85), Pan = p, Verb = 0.5 });
                return;
            case "arrow_rain":
                if (!a.Gate("fall:arrows", 2, 200)) return;
                a.Play(new Hiss { T = t - 0.2, A = 0.15, D = 0.25, G = 0.04 * g, Bp = 3000, Bp2 = 1800, Q = 2, Pan = p });
                for (int i = 0; i < 3; i++) a.Play(new Clip { T = t + i * 0.04, Of = "impactWood_medium", G = 0.1 * g, Pitch = R(1.5, 1.9), Pan = p });
                return;
            case "slash_quake":
                if (!a.Gate("fall:quake", 2, 200)) return;
                a.Play(new Clip { T = t, Of = "impactMining", G = 0.3 * g, Pitch = R(0.6, 0.75), Pan = p });
                a.Play(new Tone { T = t, F = 55, F2 = 30, D = 0.45, G = 0.12 * g, Pan = p });
                return;
        }
    }

    /// <summary>Lightning leaping between them (Ev.Chain): a zap and a snap.</summary>
    public static void Arc(Where w)
    {
        if (A is not { } a || !a.Gate("arc", 3, 120)) return;
        a.Play(new Hiss { D = 0.11, G = 0.06, Bp = R(3000, 4200), Q = 0.8, Pan = w.Pan });
        a.Play(new Tone { F = R(90, 130), Type = Wave.Square, D = 0.09, G = 0.025, Lp = 2200, Pan = w.Pan });
    }

    /// <summary>A lance of light held on them (Ev.Beam): a hum for as long as it burns.</summary>
    public static void Lance(string? art, double duration, Where w)
    {
        if (A is not { } a || !a.Gate("lance", 1, 300)) return;
        double d = System.Math.Clamp(duration, 0.2, 1.5);
        if (art == "beam_sun")
        {
            a.Play(new Fm { F = 440, Ratio = 2, Index = 0.6, A = 0.08, D = d, G = 0.025, Pan = w.Pan, Verb = 0.5 });
            a.Play(new Fm { F = 660, Ratio = 2, Index = 0.5, A = 0.1, D = d, G = 0.018, Pan = w.Pan, Verb = 0.5 });
        }
        else
        {
            // The green lance: a living hum, wood-dark under a bright edge.
            a.Play(new Tone { F = 196, Type = Wave.Saw, A = 0.06, D = d, G = 0.03, Lp = 700, Pan = w.Pan });
            a.Play(new Hiss { A = 0.05, D = d, G = 0.025, Bp = 1600, Q = 4, Pan = w.Pan });
        }
    }

    /// <summary>A little of the skill itself on a hit (Ev.Hit's art), over the school's.</summary>
    public static void HitOf(string? art, Where w)
    {
        if (A is not { } a || art == null) return;
        double p = w.Pan, g = 0.5 + 0.5 * w.Near;
        switch (art)
        {
            case "chakram" or "chakram_razor" or "chakram_hail" when a.Gate("hit:steelring", 2, 90):
                a.Play(new Clip { Of = "impactMetal_light", G = 0.12 * g, Pitch = R(1.3, 1.6), Pan = p });
                break;
            // (Held low and few: over the school's own blow, three a breath clipped the tape.)
            case "palm" or "palm_temple" or "palm_storm" when a.Gate("hit:palm", 2, 110):
                a.Play(new Clip { Of = "impactPunch_heavy", G = 0.14 * g, Pitch = R(0.75, 0.9), Pan = p });
                break;
            case "dagger" or "dagger_flurry" or "dagger_blood" when a.Gate("hit:knife", 3, 80):
                a.Play(new Clip { Of = "knifeSlice", G = 0.12 * g, Pitch = R(1.0, 1.3), Pan = p });
                break;
            case "arrow" or "arrow_mark" when a.Gate("hit:arrow", 3, 80):
                a.Play(new Clip { Of = "impactWood_medium", G = 0.1 * g, Pitch = R(1.6, 2.0), Pan = p });
                break;
            case "moon" or "moon_brand" when a.Gate("hit:moon", 2, 150):
                a.Play(new Fm { F = R(1700, 1900), Ratio = 2.76, Index = 1.5, D = 0.3, G = 0.015 * g, Pan = p, Verb = 0.5 });
                break;
            case "tether" or "tether2" or "tether_mark" when a.Gate("hit:chain", 2, 160):
                a.Play(new Clip { Of = "chainLink", G = 0.12 * g, Pitch = R(0.9, 1.15), Pan = p });
                break;
            case "disc" or "disc_aegis" or "disc_reckon" when a.Gate("hit:disc", 2, 120):
                a.Play(new Fm { F = R(980, 1060), Ratio = 2, Index = 1.2, D = 0.3, G = 0.016 * g, Pan = p, Verb = 0.35 });
                break;
        }
    }
}
