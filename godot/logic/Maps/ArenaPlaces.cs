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
        return new ArenaPlace(id, spec.People, mood, night, air);
    }

    /* ------------------------------------------------------------ nights -- */

    // An arena's night is seen from thirty metres up: the moon has to show the
    // ground's form, but the ground stays darker than everything that moves on
    // it, so the living read against it and the survivor's own light is the
    // brightest thing in the middle of the picture. Each place keeps its own.
    static readonly GradeSettings Grade = new([0.012, 0.02, 0.04], [1.0, 1.0, 1.03], [1.03, 1.0, 0.97],
        "#2a4a66", "#ffad5c", 0.22, 1.0, 0.16, 1.16);

    static (AtmospherePreset, ArenaAir) Light(string place) => place switch
    {
        // The barrow field: an open sky, a high cold moon, the chalk turf grey
        // under it, mist lying in the graves.
        "barrow" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#3a5070" },
            KeyColor = "#b8c8e6", KeyIntensity = 3.9, KeyElevation = 52, KeyAzimuth = 140, ShadowStrength = 0.78,
            HemiSky = "#3c4c68", HemiGround = "#1c1a18", HemiIntensity = 1.15, EnvIntensity = 0.8,
            FogColor = "#141c28", FogDensity = 0.004, Exposure = 1.62, Rim = "#a8c0f0", RimStrength = 0.8,
            Grade = Grade with { ShadowTint = "#2c4660", HighlightTint = "#ffb070", Saturation = 0.92 },
        }, new ArenaAir("#8a96a8", 0.05, 0.9, 1.6, 1.0, "#1c2430", 0, "#ff5a22", 1.0)),
        // The Hollow: old wood all round, the moon low and broken by the canopy
        // into pools; black litter, grey wolves, cold mist down by the water.
        "hollow" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#2a4448" },
            KeyColor = "#a8c4d4", KeyIntensity = 5.6, KeyElevation = 38, KeyAzimuth = 200, ShadowStrength = 0.82,
            // (The sky's light carries under the crowns: the leaves there are dim, never a hole.)
            HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 2.0, EnvIntensity = 0.85,
            FogColor = "#0e1818", FogDensity = 0.005, Exposure = 1.65, Rim = "#a0c8e0", RimStrength = 0.9,
            Grade = Grade with { ShadowTint = "#24443e", HighlightTint = "#ffb468", Saturation = 0.9, Lift = [0.01, 0.02, 0.03] },
        }, new ArenaAir("#7c9490", 0.06, 1.1, 1.4, 1.0, "#14201e", 0.55, "#ff5420", 0.9)),
        // The ruts: a road in a ravine, a warmer grey moon, the camp's fires and
        // their smoke hanging over the mud.
        "ruts" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#4a4458" },
            KeyColor = "#c0c6d6", KeyIntensity = 3.7, KeyElevation = 44, KeyAzimuth = 60, ShadowStrength = 0.78,
            HemiSky = "#3a4258", HemiGround = "#221a12", HemiIntensity = 1.1, EnvIntensity = 0.8,
            FogColor = "#1a1614", FogDensity = 0.0045, Exposure = 1.62, Rim = "#b4c0e0", RimStrength = 0.78,
            Grade = Grade with { ShadowTint = "#34445a", HighlightTint = "#ffa456", TintStrength = 0.24, Saturation = 0.94 },
        }, new ArenaAir("#8c8478", 0.025, 0.6, 1.8, 1.3, "#2a221c", 0, "#ff5a22", 1.0)),
        // The Dig: dust in the air, the moon dimmed by it, lamps everywhere and
        // the pit's glow; ember-stained clay, black spoil.
        "dig" => (Atmospheres.Night with
        {
            Sky = Atmospheres.Night.Sky with { Glow = "#4a3a34" },
            KeyColor = "#b0b6c4", KeyIntensity = 3.2, KeyElevation = 48, KeyAzimuth = 300, ShadowStrength = 0.74,
            HemiSky = "#383c4c", HemiGround = "#24180e", HemiIntensity = 1.05, EnvIntensity = 0.75,
            FogColor = "#1e1610", FogDensity = 0.005, Exposure = 1.6, Rim = "#b0bce0", RimStrength = 0.78,
            Grade = Grade with { ShadowTint = "#36404e", HighlightTint = "#ffa04c", TintStrength = 0.26, Saturation = 0.95 },
        }, new ArenaAir("#8a7a68", 0.02, 0.5, 2.0, 1.6, "#2e2218", 0, "#ff6a24", 1.1)),
        _ => throw new ArgumentException($"no arena place {place}"),
    };

    /// <summary>The places, for tools and tests.</summary>
    public static readonly string[] All = Names.Select(n => n.Place).ToArray();
}
