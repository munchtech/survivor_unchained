using System;
using System.Globalization;

namespace SurvivorUnchained.World;

/// <summary>
/// The moments of the day (the web game's render/atmosphere.ts PRESETS):
/// night in the wild, night inside walls, dusk, dawn and a hard country's
/// day. Presets blend, so dusk can slide into night over an expedition and
/// dawn can break over a boss's corpse.
/// </summary>
public static class Atmospheres
{
    // Moonlight, not darkness: a cold blue key strong enough to throw shadows
    // and show the ground's form from the high camera, the shadows lifted
    // toward blue so nothing sinks to black, and the fires left as the only
    // warmth (AgX in Godot sits darker than the web game's tone mapping).
    static readonly GradeSettings NightGrade = new([0.02, 0.035, 0.07], [1.0, 1.0, 1.03], [1.02, 1.0, 0.98],
        "#2f5a86", "#ffad5c", 0.24, 1.06, 0.2, 1.14) { Toe = 0 };   // (the wilds: 0.75 once ToeColour keeps their moon blue, judge round 2; see the rendering handoff)

    public static readonly AtmospherePreset Night = new(
        new SkySettings("#040814", "#1c2a4c", "#07090f", "#4a6ea8", 20, 1, 1),
        "#a9c4ff", 3.4, 50, 128, 0.7,
        "#4a6699", "#2a241c", 1.25, 0.8, "#16243a", 0.008, 1.6, "#9fc0ff", 0.6, NightGrade);

    /// <summary>Night inside walls: the moon is a cold wash, and what light
    /// there is comes from lamps, doorways and braziers.</summary>
    public static readonly AtmospherePreset NightTown = Night with
    {
        Sky = Night.Sky with { Glow = "#2c4470" },
        // (E9d r2: the moon and the fill raised (key 1.35, hemi 0.58 #2c3e62, env 0.4, lift 0.01/0.018/0.035, contrast 1.22):
        // away from the lamps the grass and the yards sank to black, p50 under 1 of 255; a moonlit blue-violet now)
        KeyColor = "#a4b8ec", KeyIntensity = 1.8, KeyElevation = 48, ShadowStrength = 0.55,
        HemiSky = "#3a4a7c", HemiGround = "#1e1812", HemiIntensity = 0.82, EnvIntensity = 0.52,
        FogColor = "#0b121c", FogDensity = 0.011, Exposure = 1.32, Rim = "#86a4e8", RimStrength = 0.42,
        Grade = NightGrade with
        {
            Lift = [0.024, 0.034, 0.064], ShadowTint = "#2e4470", HighlightTint = "#ffa34e", TintStrength = 0.3,
            Saturation = 1.0, Vibrance = 0.2, Contrast = 1.16, Toe = 0.5,
        },
        // (Rendering r1, triage judge B1: she was dim in town by night (her ember at 1, Low Ford's 2.2) and the yards off
        // the lamps black (tnight_01's right half p50 8 of 255): a modest ember, 1.7 (her skin p50 at tnight_00 38 to 47),
        // the lift 0.016/0.024/0.05 to 0.024/0.034/0.064 (that right half p50 8 to 12))
        Ember = 1.7,
    };

    /// <summary>The title and the Look: night, with the grade's toe held whole, so her irises, brows and dark hair keep
    /// their colour at the camera that judges them.</summary>
    public static readonly AtmospherePreset Front = Night with { Grade = NightGrade with { Toe = 1 } };

    // The golden hour going blue: a low warm sun with long shadows, the shade lifted toward violet,
    // and the light between day's and the moon's. The day's clock shows it every evening; at 18
    // degrees and half the light it was darker than the night itself (the sun grazing the ground,
    // the wood's long shadows over all of it: the Verge went black).
    public static readonly AtmospherePreset Dusk = new(
        new SkySettings("#24305a", "#c07850", "#16141a", "#ffa060", 7, 0.15, 0),
        "#ffc890", 4.4, 34, 200, 0.72,
        "#7088c8", "#3a2c20", 1.3, 0.6, "#4a4a62", 0.005, 1.45, "#ffbe8a", 0.32,
        new([0.02, 0.022, 0.05], [1.0, 1.0, 1.02], [1.02, 1.0, 0.98], "#40508a", "#ffb878", 0.16, 0.98, 0.12, 1.12));

    public static readonly AtmospherePreset Dawn = new(
        new SkySettings("#3b5a8f", "#f2b48a", "#2a2220", "#ffd2a0", 6, 0, 0),
        "#ffd1a0", 2.8, 22, 20, 0.8,
        "#8aa0d0", "#3a2a1a", 0.85, 0.85, "#a89aa0", 0.0065, 1.0, "#ffd8b0", 0.2,
        new([0.02, 0.02, 0.04], [1.0, 1.0, 1.0], [1.04, 1.01, 0.97], "#56709a", "#ffc88a", 0.16, 0.96, 0.12, 1.14));

    /// <summary>Day in a hard country: a low gold sun, cold in the shadows,
    /// the air never quite clear, but light enough to be glad of.</summary>
    public static readonly AtmospherePreset Day = new(
        new SkySettings("#4f74a6", "#c4ccd0", "#34302c", "#fff0d0", 8, 0, 0),
        "#ffeccc", 3.8, 46, 55, 0.82,
        "#9cb2cc", "#463626", 1.0, 0.85, "#a4aeb4", 0.0055, 1.0, "#e6eef8", 0.18,
        new([0.01, 0.014, 0.026], [1.0, 1.0, 1.0], [1.04, 1.01, 0.96], "#3a5872", "#ffd9a0", 0.2, 1.05, 0.16, 1.12));

    /* ------------------------------------------------- play's own (E1) -- */
    // Play's presets (look bible 1c, "The trick"): a low key that models the ground from the high
    // camera, the ambient two to three stops under it, no black lift, shadows cool and dark, and a
    // grade that keeps warm highlights over cool shadows at a saturation of about 0.9. Only play
    // names them (the zones' AtmosphereFor); the cinematics, arenas and the title keep the presets
    // above, which their shots were judged under. The play camera sits south of her (+z) looking
    // north, so a key from the east or west (azimuth near 0 or 180) throws its shadows across the road.

    // (Round 2, judge: the highlight tint near white, so the fire and her ember carry the warmth and the moon stays
    // blue, not grey; the shade tint doubled, over a blue-only lift, so the shade is deep blue, not dead black.)
    // The shade tint is a blue of mid luma (#a6bced, luma 0.5 in linear): the grade adds it as (tint - 0.5), so it
    // turns the shade blue without darkening it. #2c4e7e at 0.2 also took 0.09 off every dark, crushing the wood's
    // shade to black (p50 5 on the road).
    // (Round 3, judge: the shade brown and moonlit grass khaki under a blue moon. The moon's colour was never the fault:
    // olive grass and brown earth under it come out of AgX khaki and brown (measured on --grade-off frames), and the
    // grade's warm-hue hold and toe kept them so. The grade's Moon step now gives what is weakly coloured the moon's
    // silver-blue, and leaves what is strongly coloured (the fires, her ember's pool) its own.)
    static readonly GradeSettings PlayNightGrade = new([0.004, 0.010, 0.024], [1.0, 1.0, 1.03], [1.03, 1.0, 0.96],
        "#a6bced", "#fff4ea", 0.2, 0.9, 0.1, 1.13) { Toe = 1, Moon = 1, MoonDrop = 0.65, MoonSat = 0.14,
        PaintVib = 0.8, PaintHi = 0.8, PaintShadow = "#24404a", PaintShadowK = 0.7, PaintLift = 0.02 };   // (the paint grade: art style round 2's camp, 20 Oct; G1 r2: a dark teal shade, #1d2a52 made the unlit field one slate-navy, and MoonSat 0.06 to 0.085 keeps the moonlit grass blue, C 3, under the paint vibrance's fade; G1 r3: 0.14, moonlit grass C 2.8 to 4.7 (the moon's own colour is moot here: #86b5ff left it at 2.8, the Moon step drops its chroma))

    /// <summary>The close view's paint grade by night (art style round 1's, which kept her copper hair): the view grade
    /// (Atmosphere.ViewGrade) takes it over the preset's as the view closes in. (Round 1's 0.7 vibrance took her shaded side
    /// from chroma 2.6 to 4.3, so it was off here; G1 r4: back at 0.7 under the skin and copper protection and the dark fade,
    /// one grade on her and the world: her shaded skin's chroma 7.9 to 8.3, lit skin 9.7 to 9.8, the neck's shade hue 21-22 both ways.)</summary>
    public static readonly GradeSettings CloseNightPaint = PlayNightGrade with
    {
        PaintVib = 0.7, PaintHi = 0.7, PaintShadow = "#22305a", PaintShadowK = 0.8, PaintLift = 0.015, PaintShadowSkin = 1,
        MoonSat = 0.085,   // (G1 r3: the play night's 0.14 is the camp grass's; the close view keeps the 0.085 she was judged under)
    };   // contrast 1.13 (round 3b: 1.08 left the pools at 0.46-0.53)

    /// <summary>The Low Ford road by night, in play: the moon low at the road's far end (north, a little
    /// west), so it lights the road's corridor through the wood, and what stands on it throws a long
    /// shadow down the road toward the camera, rimmed by the moon; the fires and her ember the warm
    /// pools in a cold dark. (From the east or west, the wood's shadows filled the road.) Round 3: the ambient was five
    /// stops under the moon (ambient-only frames: the open ground at luma 5), so the shade read as brown-black, lit by the
    /// shadows' 10% moon leak on brown earth; the sky's light at 2.2 times brings it to two and a half stops under, blue,
    /// with its texture; the moon 0.3 of a stop down kept the road's middle grey under 35. Round 3b (measured): the moon down to 20 degrees, so the
    /// trees' shadows lie longer across the road; the sky 2.2, exposure 1.5, her ember 2.2, the grade's contrast 1.13: night
    /// p50 15-31, pools 0.52-0.71, road B's p95/p50 2.5. Round 3c: the river's mist 0.14 and light 0.17 (the ford's
    /// water sat at p50 31 under its beacon's pool: 2.4-2.7 now, pools 0.61-0.65).</summary>
    public static readonly AtmospherePreset LowFordNight = Night with
    {
        // (Low Ford r1, triage judge: outside her pool near-black navy, one hue, the trunks' shadows huge black bars. The moon
        // 28 to 48 degrees (a shadow 1.9 to 0.9 times its caster's height) at 2.6, not 2.7 (its sun-facing ground held), lighter
        // shadows (0.9 to 0.6: the shade takes 40% of the moon); a violet fill (hemisphere #33508c to #463c8a at 4.0) and the
        // grade's moon step on the shade only (MoonTop 0.44, hue 280): the shade violet, the moonlit grass and the needles keep
        // their teal-green, the lamps' and fires' pockets warm. Frame median luma 26-30 to 33-45 of 255.)
        // (Rendering r1, triage judge B4: a lifted, saturated violet-blue wash, not darkness: play p50 38-47, p95/p50 1.7-2.0,
        // pools 0.32-0.41. The fill alone (hemisphere 4.0 to 1.5) moved p50 by 2: the moonlit ground is the frame's median, so
        // the moon 2.6 to 1.7 (its colour and angle kept) and the exposure 1.95 to 1.3, with the warm lights held or raised:
        // her ember 2.2 to 8 (twice its old light at the new exposure), the camp fire 16 to 52 (zone.json). The shade from
        // violet to a teal-blue: the fill #463c8a to #34507e at 1.6, the moon step's hue 280 to 240 and chroma 0.16 to 0.10,
        // the paint shade #4a2f78 to #2c4870; the darkest 30%'s OKLab hue 277-289 to 249-252, chroma 4.4-5.1 to 2.4-3.1.
        // Play frames: p50 22-29, p95/p50 2.4-3.1, pools 0.53-0.65 (lfplay_02's level-up flash: p50 45, her flare scales with the ember).)
        KeyColor = "#80b6f2", KeyIntensity = 1.7,   // (G1 r2: #a9c4ff at 6.5 bleached the moonlit grass grey-white, frost; G1 r3: 5.8 to 4.9, the camp ground's median L -0.5)
        // (E4f, judge E4 r3: at 20 degrees the trees' shadows lay across the camp and road as a fence of long straight bars; up
        // to 28. Measured at the camp: x0.73 (sin 20 / sin 28) left the moonlit ground 1.6-2.5 OKLab L brighter (p85, p95); x0.55
        // holds it (35.5 / 45.4 against 35.4 / 46.0). The frame's median still rises 1.6 L*: the shadows are shorter, the point)
        KeyElevation = 48, KeyAzimuth = 250, ShadowStrength = 0.8,   // (Low Ford r3, judge r2: the lit ground and the shade barely parted: 0.6 to 0.68; lf5p, judge lf4: the wood road's dapple still murky, 0.8)
        HemiSky = "#34507e", HemiGround = "#1e1a14", HemiIntensity = 1.6, EnvIntensity = 0.6,
        FogColor = "#16223a", FogDensity = 0.008, Exposure = 1.3, Rim = "#9fc0ff", RimStrength = 0.75,
        Grade = PlayNightGrade with { MoonDrop = 0.5, MoonHue = 240, MoonSat = 0.10, MoonTop = 0.44, MoonWidth = 0.15, PaintVib = 0.55, PaintShadow = "#2c4870", PaintShadowK = 0.75 },
        // (Rendering r2, judge r1 D1: at 8 she read as a figure carrying a floodlight, her pool larger than the camp fire's and
        // her crown clipped white: 3.5, with the pool off her and people (PlayerView.FolkLight lights them), 2500K, 0.75x its reach)
        Haze = 0.006, Mist = 0.18, MistColor = "#2c3a50", Ember = 3.5,
        CrowdRim = 0.2, RiverLight = 0.55, RiverSky = 0.45, RiverBend = 0.5,
        // (Low Ford r3, judge r2: the moon's glitter a noisy white blob round her, every warm pool's grass lime)
        RiverMoon = 1, GrassLampOchre = 0.7,
        // (Low Ford lf5p, judge lf4: the night bushes too saturated; her pool tipped the meadow ground olive-chartreuse)
        BushNightSat = 0.4, GroundEmberOchre = 0.6,
        Frost = 1,
    };

    static readonly GradeSettings PlayDawnGrade = new([0, 0, 0], [1.0, 1.0, 1.02], [1.0, 1.0, 1.0],
        "#a6bced", "#ffbe7a", 0.55, 0.9, 0.1, 1.14) { Toe = 0.5, Moon = 1.0, MoonSat = 0.05, MoonTop = 0.45, MoonWidth = 0.2,
        PaintVib = 0.75, PaintHi = 0.7, PaintShadow = "#403878", PaintShadowK = 0.51, PaintLift = 0.01 };   // (G1 r2: shadowk 0.6 and no lift crushed the shaded decals, indigo over the square) (the paint grade, the day's family; a mid-luma blue, as the night's: #3e5a8a took 0.12 off the shade, brown and murky)

    /// <summary>The Low Ford at dawn, in play: the sun 18 degrees up in the north-north-east, cheated from C04 A's
    /// rising sun toward the road's far end (as the moon was), so the wood road's corridor gets sun (from the east-north-east
    /// the wood's shadows filled it: 83% cover) and the wood's shadows fall toward the camera; the sun a pale gold,
    /// not orange; the shade cool and two stops under it: the sky's horizon and glow, which light the shade, cool
    /// (C04 A's orange horizon made every shadow brown), and the grade's Moon step cooling the shade only; the fog a
    /// thin cool veil, not a mauve murk. (C04 A's hand-back takes this sun on its cut: GameCinema "atmosphere".)</summary>
    public static readonly AtmospherePreset LowFordDawn = Dawn with
    {
        Sky = Dawn.Sky with { Horizon = "#7c90b8", Glow = "#c8d0e0" },
        KeyColor = "#ffd6b0", KeyIntensity = 10.0,   // (G1 r2: #ffdbad 9 degrees toward peach: it leaned mustard-khaki on the grass)
        KeyElevation = 18, KeyAzimuth = -60, ShadowStrength = 0.95,
        HemiSky = "#7b91c0", HemiGround = "#2c3446", HemiIntensity = 1.08, EnvIntensity = 0.7,   // (G1 r3: #6f8fd8 at 0.9 35% less saturated, same hue, +20%: the square's indigo 41% to 40%; its shaded decals' p10 L 23.9 to 24.0, the fill is not what holds them)
        FogColor = "#8c9cb4", FogDensity = 0.003, Exposure = 1.25, Rim = "#ffd8b0", RimStrength = 0.25,
        Grade = PlayDawnGrade, Haze = 0.004, Mist = 0.14, MistColor = "#7a8aa2", CrowdRim = 0.05, Ember = 0.5,
        Frost = 0.5, FrostThaw = 1,
    };

    /// <summary>The Waystation at dawn: the sun 14 degrees up a little north of east, raking its streets
    /// (azimuth -10, so the day's arc runs on through the day's 290 to dusk's 200 without crossing the camera).</summary>
    public static readonly AtmospherePreset WaystationDawn = LowFordDawn with
    {
        KeyElevation = 14, KeyAzimuth = -10, Haze = 0.003, Frost = 0, FrostThaw = 0,
    };

    static readonly GradeSettings PlayDayGrade = new([0, 0, 0], [1.0, 1.0, 1.0], [1.01, 1.0, 0.99],
        "#b0c0de", "#ffd49a", 0.25, 0.9, 0.1, 1.12) { Toe = 0.5, Moon = 0.5, MoonSat = 0.04, MoonTop = 0.45, MoonWidth = 0.2,
        PaintVib = 0.75, PaintHi = 0.7, PaintShadow = "#403878", PaintShadowK = 0.45 };   // (the paint grade: art style round 2's town, 20 Oct; its #2a3c78 at 0.6 moved violet and down to the target's shade: p0-30 C 2.2 h 274 to 1.8 h 291, target 0.9 h 331)

    /// <summary>The Waystation by day: a hard country's low sun, 28 degrees up in the east-north-east, so the
    /// houses' shadows fall across the north-south street and the square toward the south-west (from the north,
    /// round 2, they fell along it and left the south street flat: 14% cover).
    /// Art style round 2 (approved 20 Oct): a warmer, stronger sun (#ffd8a0, a touch warmer than r2's #ffe0a8 toward the
    /// target's: the sunlit stone's Oklab hue 68 to 64, target 65), a violet sky fill, a warm bounce, and the paint grade.</summary>
    public static readonly AtmospherePreset WaystationDay = Day with
    {
        KeyColor = "#ffd8a0", KeyIntensity = 6.6, KeyElevation = 28, KeyAzimuth = 330, ShadowStrength = 0.95,
        HemiSky = "#a9a9e5", HemiGround = "#605245",   // (G1 r2: the sky 10% up, shaded grass murky olive; the bounce at half its saturation, #6a4e34 took the mud amber)
        HemiIntensity = 0.7, EnvIntensity = 0.55,
        // (Rendering r1, triage judge C3: the shade read warm brown: the paint shade #403878 at 0.45 to a sky blue #34589a at 0.55;
        // a cast shadow on the square's cobbles OKLab hue 282 to 266, chroma 2.05 to 2.14; the sunlit stone unchanged, h 60 C 3.1.
        // (The fill's colour, #a9a9e5 to #8cacec, moved neither.) The brown that remains is the mud decals round the props.)
        Exposure = 1.05, RimStrength = 0.18, Grade = PlayDayGrade with { PaintShadow = "#34589a", PaintShadowK = 0.55 }, Haze = 0.004, Mist = 0.05, MistColor = "#a8acb4", Ember = 0.5,
    };

    /// <summary>Play's night going to dawn by k (0 to 1), where no C04 A brings the sun up: the moon sets and the
    /// sun rises, each from its own place. The key fades out by halfway, turns there unseen (no light, no shadow)
    /// and fades in as the sun; a blended key wheeled its shadows 280 degrees round her.</summary>
    public static AtmospherePreset Dawning(double k)
    {
        var p = Blend(LowFordNight, LowFordDawn, k);
        var from = k < 0.5 ? LowFordNight : LowFordDawn;
        double w = Math.Abs(2 * k - 1);
        return p with { KeyAzimuth = from.KeyAzimuth, KeyElevation = from.KeyElevation, KeyIntensity = from.KeyIntensity * w * w * (3 - 2 * w) };
    }

    public static AtmospherePreset ByName(string name) => name switch
    {
        "night" => Night, "nightTown" => NightTown, "dusk" => Dusk, "dawn" => Dawn, "day" => Day,
        _ => throw new ArgumentException($"no atmosphere {name}"),
    };

    static double Lerp(double a, double b, double t) => a + (b - a) * t;
    static double[] Lerp3(double[] a, double[] b, double t) => [Lerp(a[0], b[0], t), Lerp(a[1], b[1], t), Lerp(a[2], b[2], t)];

    /// <summary>a blended toward b by t (colours mixed in linear light, as
    /// three.js mixes them).</summary>
    public static AtmospherePreset Blend(AtmospherePreset a, AtmospherePreset b, double t) => new(
        new SkySettings(Mix(a.Sky.Top, b.Sky.Top, t), Mix(a.Sky.Horizon, b.Sky.Horizon, t), Mix(a.Sky.Bottom, b.Sky.Bottom, t),
            Mix(a.Sky.Glow, b.Sky.Glow, t), Lerp(a.Sky.GlowPower, b.Sky.GlowPower, t), Lerp(a.Sky.Stars, b.Sky.Stars, t), Lerp(a.Sky.Moon, b.Sky.Moon, t)),
        Mix(a.KeyColor, b.KeyColor, t), Lerp(a.KeyIntensity, b.KeyIntensity, t), Lerp(a.KeyElevation, b.KeyElevation, t),
        Lerp(a.KeyAzimuth, b.KeyAzimuth, t), Lerp(a.ShadowStrength, b.ShadowStrength, t),
        Mix(a.HemiSky, b.HemiSky, t), Mix(a.HemiGround, b.HemiGround, t), Lerp(a.HemiIntensity, b.HemiIntensity, t),
        Lerp(a.EnvIntensity, b.EnvIntensity, t), Mix(a.FogColor, b.FogColor, t), Lerp(a.FogDensity, b.FogDensity, t),
        Lerp(a.Exposure, b.Exposure, t), Mix(a.Rim, b.Rim, t), Lerp(a.RimStrength, b.RimStrength, t),
        new GradeSettings(Lerp3(a.Grade.Lift, b.Grade.Lift, t), Lerp3(a.Grade.Gamma, b.Grade.Gamma, t), Lerp3(a.Grade.Gain, b.Grade.Gain, t),
            Mix(a.Grade.ShadowTint, b.Grade.ShadowTint, t), Mix(a.Grade.HighlightTint, b.Grade.HighlightTint, t),
            Lerp(a.Grade.TintStrength, b.Grade.TintStrength, t), Lerp(a.Grade.Saturation, b.Grade.Saturation, t),
            Lerp(a.Grade.Vibrance, b.Grade.Vibrance, t), Lerp(a.Grade.Contrast, b.Grade.Contrast, t)) 
        {
            Toe = Lerp(a.Grade.Toe, b.Grade.Toe, t), Moon = Lerp(a.Grade.Moon, b.Grade.Moon, t), MoonHue = Lerp(a.Grade.MoonHue, b.Grade.MoonHue, t),
            MoonSat = Lerp(a.Grade.MoonSat, b.Grade.MoonSat, t), MoonDrop = Lerp(a.Grade.MoonDrop, b.Grade.MoonDrop, t),
            MoonLo = Lerp(a.Grade.MoonLo, b.Grade.MoonLo, t), MoonHi = Lerp(a.Grade.MoonHi, b.Grade.MoonHi, t),
            MoonTop = Lerp(a.Grade.MoonTop, b.Grade.MoonTop, t), MoonWidth = Lerp(a.Grade.MoonWidth, b.Grade.MoonWidth, t),
            PaintVib = Lerp(a.Grade.PaintVib, b.Grade.PaintVib, t), PaintHi = Lerp(a.Grade.PaintHi, b.Grade.PaintHi, t),
            PaintShadow = MixOr(a.Grade.PaintShadow, b.Grade.PaintShadow, t),
            PaintShadowK = Lerp(a.Grade.PaintShadowK, b.Grade.PaintShadowK, t), PaintLift = Lerp(a.Grade.PaintLift, b.Grade.PaintLift, t),
            PaintShadowSkin = Lerp(a.Grade.PaintShadowSkin, b.Grade.PaintShadowSkin, t), PaintVibDark = Lerp(a.Grade.PaintVibDark, b.Grade.PaintVibDark, t),
        })
        {
            Haze = Lerp(a.Haze, b.Haze, t), Mist = Lerp(a.Mist, b.Mist, t), MistColor = Mix(a.MistColor, b.MistColor, t), Ember = Lerp(a.Ember, b.Ember, t),
            CrowdRim = Lerp(a.CrowdRim, b.CrowdRim, t), RiverLight = Lerp(a.RiverLight, b.RiverLight, t),
            RiverSky = Lerp(a.RiverSky, b.RiverSky, t), RiverBend = Lerp(a.RiverBend, b.RiverBend, t),
            RiverMoon = Lerp(a.RiverMoon, b.RiverMoon, t), GrassLampOchre = Lerp(a.GrassLampOchre, b.GrassLampOchre, t),
            BushNightSat = Lerp(a.BushNightSat, b.BushNightSat, t), GroundEmberOchre = Lerp(a.GroundEmberOchre, b.GroundEmberOchre, t),
            Frost = Lerp(a.Frost, b.Frost, t), FrostThaw = Lerp(a.FrostThaw, b.FrostThaw, t),
        };

    /* ------------------------------------------------------------ colour -- */

    /// <summary>'#rrggbb' as linear rgb (three.js's Color.set with colour
    /// management on).</summary>
    public static (double R, double G, double B) Linear(string hex)
    {
        int v = int.Parse(hex.AsSpan(1), NumberStyles.HexNumber);
        return (ToLinear(((v >> 16) & 255) / 255.0), ToLinear(((v >> 8) & 255) / 255.0), ToLinear((v & 255) / 255.0));
    }

    /// <summary>Linear rgb as '#rrggbb' (Color.getHexString).</summary>
    public static string Hex(double r, double g, double b)
    {
        static int C(double x) => (int)Math.Floor(Math.Clamp(ToSrgb(x), 0, 1) * 255 + 0.5);
        return $"#{C(r):x2}{C(g):x2}{C(b):x2}";
    }

    static double ToLinear(double c) => c < 0.04045 ? c * 0.0773993808 : Math.Pow(c * 0.9478672986 + 0.0521327014, 2.4);
    static double ToSrgb(double c) => c < 0.0031308 ? c * 12.92 : 1.055 * Math.Pow(c, 0.41666) - 0.055;

    /// <summary>Mix, where an empty colour (none) takes the other's: its strength blends on its own.</summary>
    static string MixOr(string a, string b, double t) => a == "" ? b : b == "" ? a : Mix(a, b, t);

    static string Mix(string a, string b, double t)
    {
        var (ar, ag, ab) = Linear(a);
        var (br, bg, bb) = Linear(b);
        return Hex(Lerp(ar, br, t), Lerp(ag, bg, t), Lerp(ab, bb, t));
    }
}
