using System;
using System.Linq;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Maps;

/* Where an ember arena is. Every arena is a place in the valley, held in the
 * ember for one night: the people who fill it fill it where they live. The
 * Risen come up out of the Seventh Legion's barrow field; the Pack hunts its
 * own Hollow, where the slurry runs in the stream; the Kerchiefs hold the
 * caravan road below the Roost; the Lamplings boil up out of the Dig. Each
 * place has its own ground, its own shapes, its own night, and the ember's
 * ring round its edge, where the scar holds you in.
 *
 * Its mood is what its name says: a "Burnt" place is smoky, a "Drowned"
 * one standing in water, a "Lampless" one darker, so the table's names
 * and the place agree. */

/// <summary>What a place's night is like, past what the sky preset says: low
/// mist, the air's body, the moon through a canopy, the ember's colour.</summary>
public sealed record ArenaAir(
    string MistColor, double MistDensity, double MistHeight, double MistFalloff,
    double Haze, string HazeColor, double Dapple, string Ember, double EmberGlow);

/// <summary>An arena's place: which ground, which shapes, which night.</summary>
public sealed record ArenaPlace(string Id, string People, string Mood, AtmospherePreset Night, ArenaAir Air)
{
    public bool HasMood(string mood) => Mood == mood;
    /// <summary>(P9 set) The ground's set (godot/art/arena/GROUND: its layers, their sizes and looks), when not its people's
    /// place's: a story place paved its own way (the Vault's flags). Everything else (grass, moss, water) stays the place's.</summary>
    public string Ground { get; init; } = "";
    public string GroundId => Ground != "" ? Ground : Id;
}

public static class ArenaPlaces
{
    /// <summary>Where each people lives.</summary>
    public static string IdFor(string people) => people switch
    {
        "dead" => "barrow",
        "kerchiefs" => "ruts",
        "lamplings" => "dig",
        _ => "hollow",
    };

    /// <summary>The words a place is called by on the table, by place (the
    /// valley's words, northern and old: story owns them). A howe or a low is
    /// a grave-mound, a lych-way a corpse road, the chesters an old Legion
    /// camp; a delph is a quarry, a sough a mine's drain.</summary>
    public static readonly (string Place, string[] Words)[] Names =
    {
        ("barrow", new[] { "Howes", "Lows", "Barrows", "Lych-Way", "Chesters", "Burying-Ground" }),
        ("hollow", new[] { "Dene", "Clough", "Holt", "Shaw", "Brake", "Den" }),
        ("ruts", new[] { "Ruts", "Drove", "Cutting", "Ravine", "Waggon-Way", "Gap" }),
        // Not "Dig": the Dig is Grimtunnel's, and the atlas is other places.
        ("dig", new[] { "Sump", "Delph", "Sough", "Spoil", "Workings" }),
    };

    /// <summary>What each people's places are like, as the table names them (the story
    /// bible, "The nights"): their own words, so a name says whose ground it is.</summary>
    public static readonly (string Place, string[] Words)[] Adjectives =
    {
        ("barrow", new[] { "Lampless", "Quiet", "Morrow", "Drowned", "Burnt", "Cold" }),
        ("hollow", new[] { "Grey", "Deep", "Thorn", "Bracken", "Drowned", "Whelping", "Bitter" }),
        // The hungry gap is the farmer's lean weeks of spring, when the stores are gone.
        ("ruts", new[] { "Red", "Salt", "Toll", "Gallows", "Hungry", "Widow's", "Drowned" }),
        ("dig", new[] { "Praying", "Gold", "Warm", "Black", "Deep", "Lamplit", "Drowned" }),
    };

    /// <summary>The mood each of those words makes. "Quiet" is the valley's word for the
    /// dead, "Lampless" comes from the Order's dusk call, "Praying" is Tam's; a word with
    /// nothing to show leaves the place's own night as it is ("still").</summary>
    public static readonly (string Word, string Mood)[] Moods =
    {
        ("Lampless", "moonless"), ("Deep", "moonless"),
        ("Quiet", "mist"), ("Morrow", "mist"), ("Cold", "mist"), ("Grey", "mist"), ("Praying", "mist"),
        ("Drowned", "drowned"),
        ("Burnt", "ashen"), ("Warm", "ashen"), ("Black", "ashen"),
        ("Thorn", "thorned"), ("Bracken", "thorned"),
        ("Gallows", "gallows"),
        ("Whelping", "still"), ("Bitter", "still"), ("Red", "still"), ("Salt", "still"), ("Toll", "still"),
        ("Hungry", "still"), ("Widow's", "still"), ("Gold", "still"), ("Lamplit", "still"),
    };

    /// <summary>The mood a name gives (its first word that has one), or "".</summary>
    public static string MoodOf(string name)
    {
        foreach (var w in name.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            foreach (var (word, mood) in Moods)
                if (w == word) return mood;
        return "";
    }

    public static ArenaPlace For(MapSpec spec)
    {
        string id = IdFor(spec.People);
        string mood = spec.Mood != "" ? spec.Mood : MoodOf(spec.Name);
        // The Risen's barrow field burned by the blight theme of old: the same as ashen.
        if (mood == "" && spec.Theme == "blight") mood = "ashen";
        var (night, air) = Light(id);
        (night, air) = mood switch
        {
            // Less moon, more dark: the light the survivor carries is most of what there is.
            "moonless" => (night with { KeyIntensity = night.KeyIntensity * 0.55, HemiIntensity = night.HemiIntensity * 0.7, Exposure = night.Exposure * 0.94 },
                air with { MistDensity = air.MistDensity * 1.4 }),
            // Mist lying thick in the low ground.
            "mist" or "drowned" => (night, air with { MistDensity = air.MistDensity * 1.8, MistHeight = air.MistHeight + 0.6 }),
            // Smoke in the air, and the ember nearer the surface.
            "ashen" => (night with { FogColor = "#1c1612" }, air with { Haze = air.Haze * 1.5, HazeColor = "#3a2a20", EmberGlow = air.EmberGlow * 1.25 }),
            _ => (night, air),
        };
        // (Rendering 4: the crowd's own light by night, her lamp and the sky's fill in its paint: Zone.CrowdFill)
        return new ArenaPlace(id, spec.People, mood, night with { CrowdFill = 0.65, CrowdRim = 0.2 }, air);
    }

    /// <summary>(P9 set) A story place's own ground and night, where it has them (its people's place otherwise): the
    /// Vault's flags and its moon over the roofless hall (VaultNight).</summary>
    public static ArenaPlace ForStory(ArenaPlace place, string story) => story switch
    {
        "vault_opened" => place with { Ground = "vault", Night = VaultNight with { CrowdFill = place.Night.CrowdFill, CrowdRim = place.Night.CrowdRim } },
        _ => place,
    };

    /* ------------------------------------------------------------ nights -- */

    // An arena's night is seen from thirty metres up: the moon has to show the
    // ground's form, but the ground stays darker than everything that moves on
    // it, so the living read against it and the survivor's own light is the
    // brightest thing in the middle of the picture. Each place keeps its own.
    // (H2 R1: the moon bluer (each place's own hue) and 0.85 of what it was, her ember 1 to 4.5 in a paler gold (#ffcc9c, her
    // own #ffa868 lit the litter rust) reaching 1.3 times as far: a hot core (Oklab L 0.57) and a long soft fall, the key's
    // p95/p50 1.6 to 2.3; the moon's rim on the crowd (CrowdRim 0.2, the road's) and its fill 1 to 0.65, so the horde's
    // bodies stand under her pool and the rim draws them. Measured on the Deep Shaw at 14 min: round 2's trial rh.)
    // (H2 R1, the look bible: the play night's paint grade, as the Low Ford road's: the moon's colour on what it lights,
    // the shade painted moon indigo, her skin's hues spared. The old grade's shadow tint on brown litter left a brown-black
    // murk: shade hue 66-92, grey 43-62%, cold 0-3%. Each place keeps its own shade hue.)
    static readonly GradeSettings Grade = Atmospheres.PlayNightGrade with
    {
        // (The moon's step reaches further than the road's (MoonLo/MoonHi 0.06/0.16 to 0.12/0.24 of C/L): the litter and
        // clay are brown (C/L ~0.12-0.2), and PaintShadowSkin spares skin's hues, which are theirs too, so the paint shade
        // alone left the ground brown (trial A: shade hue 50-68, grey 56%). Her ember's pool and the fires, C/L 0.3 and up, keep their own.
        // Measured on the Deep Shaw at 14 min (trial tc2): shade hue 256, grey 9%, cold 65%, key 2.05, pool 0.33, midC 0.070.)
        MoonDrop = 0.7, MoonHue = 240, MoonSat = 0.13, MoonLo = 0.12, MoonHi = 0.24, MoonTop = 0.44, MoonWidth = 0.15,
        // (Judge r1: the play grade's pale shadow tint lifted the ground's darks 0.07 to 0.14 (Oklab L) and its moon masses
        // went (bright/dark 2.9-6.3 to 1.5); its vibrance on the pool's litter painted it rust (h 40, C 0.10). A dark navy
        // tint at 0.15 with half the toe takes the darks back (ground p10 0.143 to 0.097, ratio 2.46), and a darker, deeper
        // paint shade keeps them coloured (shade chroma 0.025 to 0.034, grey 9% to 5%); vibrance 0.55 to 0.3.)
        ShadowTint = "#2c4870", TintStrength = 0.15, Toe = 0.5,
        PaintVib = 0.3, PaintShadow = "#1c3060", PaintShadowK = 0.95, PaintLift = 0, PaintShadowSkin = 1,
    };

    /// <summary>(P9 set) The Vault by night (the story place's own, ForStory): a high moon over the roofless hall from the
    /// south-west, so it lights the facade's south face and the walls' tops and rakes the court's and the hall's
    /// flags, the west wall's broken top throwing its shadow across the hall's floor in bands with the moon's pools
    /// between, and it shines a way down the cut stair (it runs north, toward the moon's back); her ember the warm
    /// source; the shade the play night's moon indigo (Grade). Derived from (a) the look bible's night (rules 1-3:
    /// key 2.0+, pool 0.35+, Lp50 0.15-0.30, flat black 20% or less), the shots (docs/cinematics/shoot/c13.md), the
    /// play camera (pitch 64, 22-27 m); (c) inherited: the barrow's night (Light("barrow")), whose moon from the
    /// south-west (140) filled the narrow stair with its wall's shadow.</summary>
    public static readonly AtmospherePreset VaultNight = Atmospheres.Night with
    {
        Sky = Atmospheres.Night.Sky with { Glow = "#3a5070" },
        // (Round 2, measured on the play frames, court, hall and landing, --air-tune sweeps: the barrow's key 3.3 and sky 1.15
        // left one moonlit blue field, key 1.4-1.7 at any moon; a lower moon from the south-west (42 degrees) puts the west
        // walls' shadows across the floors, the sky's fill 0.95 keeps that shade off flat black, and her ember 16 against
        // a moon of 3.2 makes her pool the brightest thing in the frame: key 2.0-2.2, pool 0.40-0.57, Lp50 0.23-0.25.)
        KeyColor = "#94acee", KeyIntensity = 3.2, KeyElevation = 42, KeyAzimuth = 135, ShadowStrength = 0.82,
        HemiSky = "#36486c", HemiGround = "#1a1a1e", HemiIntensity = 0.95, EnvIntensity = 0.75,
        FogColor = "#121a28", FogDensity = 0.004, Exposure = 1.62, Rim = "#a8c0f0", RimStrength = 0.8,
        Grade = Grade, Ember = 16, EmberColor = "#ffcc9c", EmberReach = 1.35,
    };

    static (AtmospherePreset, ArenaAir) Light(string place) => place switch
    {
        // The barrow field: an open sky, a high cold moon, the chalk turf grey
        // under it, mist lying in the graves.
        "barrow" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#3a5070" },
            KeyColor = "#8fa8ec", KeyIntensity = 3.3, KeyElevation = 52, KeyAzimuth = 140, ShadowStrength = 0.78,
            HemiSky = "#3c4c68", HemiGround = "#1c1a18", HemiIntensity = 1.15, EnvIntensity = 0.8,
            FogColor = "#141c28", FogDensity = 0.004, Exposure = 1.62, Rim = "#a8c0f0", RimStrength = 0.8,
            Grade = Grade, Ember = 4.5, EmberColor = "#ffcc9c", EmberReach = 1.3,
        }, new ArenaAir("#8a96a8", 0.05, 0.9, 1.6, 1.0, "#1c2430", 0, "#ff5a22", 1.0)),
        // The Hollow: old wood all round, the moon low and broken by the canopy
        // into pools; black litter, grey wolves, cold mist down by the water.
        "hollow" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#2a4448" },
            KeyColor = "#8fb4f0", KeyIntensity = 4.7, KeyElevation = 38, KeyAzimuth = 200, ShadowStrength = 0.82,
            // (The sky's light carries under the crowns: the leaves there are dim, never a hole.)
            HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 2.0, EnvIntensity = 0.85,
            FogColor = "#0e1818", FogDensity = 0.005, Exposure = 1.65, Rim = "#a0c8e0", RimStrength = 0.9,
            Grade = Grade, Ember = 4.5, EmberColor = "#ffcc9c", EmberReach = 1.3,
        }, new ArenaAir("#7c9490", 0.06, 1.1, 1.4, 1.0, "#14201e", 0.55, "#ff5420", 0.9)),
        // The ruts: a road in a ravine, a warmer grey moon, the camp's fires and
        // their smoke hanging over the mud.
        "ruts" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#4a4458" },
            KeyColor = "#9aaee6", KeyIntensity = 3.1, KeyElevation = 44, KeyAzimuth = 60, ShadowStrength = 0.78,
            HemiSky = "#3a4258", HemiGround = "#221a12", HemiIntensity = 1.1, EnvIntensity = 0.8,
            FogColor = "#1a1614", FogDensity = 0.0045, Exposure = 1.62, Rim = "#b4c0e0", RimStrength = 0.78,
            Grade = Grade, Ember = 4.5, EmberColor = "#ffcc9c", EmberReach = 1.3,
        }, new ArenaAir("#8c8478", 0.025, 0.6, 1.8, 1.3, "#2a221c", 0, "#ff5a22", 1.0)),
        // The Dig: dust in the air, the moon dimmed by it, lamps everywhere and
        // the pit's glow; ember-stained clay, black spoil.
        "dig" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#4a3a34" },
            KeyColor = "#94a4dc", KeyIntensity = 2.7, KeyElevation = 48, KeyAzimuth = 300, ShadowStrength = 0.74,
            HemiSky = "#383c4c", HemiGround = "#24180e", HemiIntensity = 1.05, EnvIntensity = 0.75,
            FogColor = "#1e1610", FogDensity = 0.005, Exposure = 1.6, Rim = "#b0bce0", RimStrength = 0.78,
            Grade = Grade, Ember = 4.5, EmberColor = "#ffcc9c", EmberReach = 1.3,
        }, new ArenaAir("#8a7a68", 0.02, 0.5, 2.0, 1.6, "#2e2218", 0, "#ff6a24", 1.1)),
        _ => throw new ArgumentException($"no arena place {place}"),
    };

    /// <summary>The places, for tools and tests.</summary>
    public static readonly string[] All = Names.Select(n => n.Place).ToArray();
}
