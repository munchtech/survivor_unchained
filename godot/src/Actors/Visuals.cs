using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// What each creature looks like (the web game's render/visuals.ts), keyed
/// by EnemyDef.Visual: people (the Risen, the Kerchiefs) dressed and armed,
/// with a clip for each thing they do; beasts (wolves, boars, lamplings)
/// from their own models (Beasts.cs). The crowd bakes each (Vat.cs).
/// </summary>
public static class Visuals
{
    /// <summary>The clip for each thing a kind does. Slam: its blow on the ground (CastKind.Slam),
    /// played once from the cast's start and through the get-up after it. Aim and Shot: a crossbow's
    /// kneel and aim (CastKind.Aim), and the shot that ends it.</summary>
    public sealed record Clips(string Move, string Idle, string Attack, string Windup, string Die = "Death01", string Rise = "Idle_Loop", string Hit = "Hit_Chest", string? Cast = null,
        string? Slam = null, string? Aim = null, string? Shot = null);

    /// <summary>A kind of creature. Offset: moved in its own space before
    /// scaling (a long beast centred on its collision circle).</summary>
    public sealed record Spec(string Key, PersonSpec? Person, Held? Arms, Clips Clips, double Scale = 1, Vector3? Offset = null);

    const string Kerchief = "#7a1a18", KerchiefDark = "#3a1412";
    const string Rot = "#8e9680", Grave = "#4a4638", GraveDark = "#24221c";

    static Clips Shamble(string idle, string attack, string windup, string move = "Zombie_Walk_Fwd_Loop", string? cast = null) =>
        new(move, idle, attack, windup, "Death01", "LayToIdle", "Hit_Chest", cast);
    /// <summary>A caster's call, horn or drum (a cast: FolkClips.Crowd): the weapon or the fist thrust up and shaken.</summary>
    const string Rally = "Rally";
    /// <summary>A heavy's blow on the ground (FolkClips.Crowd): both fists, or the axe, up overhead and down.</summary>
    const string GroundSlam = "Slam";

    static Clips Fight(string move, string idle, string attack, string windup, string hit = "Hit_Chest", string? cast = Rally) =>
        new(move, idle, attack, windup, "Death01", "Idle_Loop", hit, cast);

    static PersonSpec P(Sex sex, string kind, bool hood = false, bool pauldron = false, string? hair = null, bool beard = false, string? hairColor = null,
        string? skin = null, double? figure = null, string? cloth = null, string? under = null) => new()
    {
        Sex = sex, Outfit = Lore.OutfitFor(sex, kind, hood, pauldron), Hair = hair, Beard = beard, HairColor = hairColor, Skin = skin, Figure = figure,
        Dye = cloth != null || under != null ? new Dye { Cloth = cloth, Under = under } : null,
    };

    static readonly Dictionary<string, Spec> cache = new();

    public static Spec Of(string visual)
    {
        if (cache.TryGetValue(visual, out var s)) return s;
        s = visual switch
        {
            "skeleton_minion" => new(visual, P(Sex.Male, "peasant", hair: "Hair_Buzzed", hairColor: "#5a5448", skin: Rot, cloth: Grave, under: GraveDark), null,
                Shamble("Zombie_Idle_Loop", "Zombie_Scratch", "Zombie_Idle_Loop") with { Slam = GroundSlam }),
            "risen_ally" => new(visual, P(Sex.Female, "peasant", hair: "Hair_Long", hairColor: "#6a665e", skin: Rot, figure: 0.9, cloth: Grave, under: GraveDark), null,
                Shamble("Zombie_Idle_Loop", "Zombie_Scratch", "Zombie_Idle_Loop")),
            "skeleton_warrior" => new(visual, P(Sex.Male, "ranger", pauldron: true, beard: true, hairColor: "#4a4640", skin: Rot, cloth: "#3e4238"),
                new Held { Right = "viking_sword", Forearm = "shield_round" }, Shamble("Idle_Shield_Loop", "Sword_Regular_A", "Idle_Shield_Loop", cast: Rally)),
            "skeleton_warrior_elite" => new(visual, P(Sex.Male, "ranger", hood: true, pauldron: true, beard: true, hairColor: "#3a3630", skin: Rot, cloth: "#2a2c2e"),
                new Held { Right = "zweihander" }, Shamble("Sword_Idle", "Sword_Attack", "Sword_Idle", "Walk_Loop", Rally)),
            "skeleton_rogue" => new(visual, P(Sex.Female, "ranger", hood: true, skin: Rot, figure: 0.8, cloth: "#3a3e34"),
                new Held { Right = "crossbow" }, Shamble("Pistol_Idle_Loop", "Pistol_Shoot", "Pistol_Idle_Loop", cast: Rally)),
            "skeleton_mage" => new(visual, P(Sex.Male, "peasant", hood: true, beard: true, hairColor: "#4a4640", skin: Rot, cloth: "#2e2a36", under: "#16141a"),
                new Held { Right = "short_staff" }, Shamble("Zombie_Idle_Loop", "Spell_Simple_Shoot", "Spell_Simple_Idle_Loop", cast: Rally)),
            // A footpad: quick, hooded, a knife in each hand.
            "kerchief_rogue" => new(visual, P(Sex.Female, "ranger", hood: true, skin: "#e0a47c", figure: 1.1, cloth: Kerchief),
                new Held { Right = "daggers", Left = "dagger_b" }, Fight("Jog_Fwd_Loop", "Sword_Idle", "Sword_Regular_B", "Sword_Idle")),
            // A pillager: hooded, throwing what comes to hand.
            "kerchief_hooded" => new(visual, P(Sex.Male, "ranger", hood: true, beard: true, hairColor: "#3a2618", skin: "#c4945e", cloth: Kerchief), null,
                Fight("Jog_Fwd_Loop", "Idle_Loop", "OverhandThrow", "Idle_Loop")),
            // A bruiser: bare-chested behind a round shield, an axe.
            "kerchief_brute" => new(visual, P(Sex.Male, "bare", pauldron: true, hair: "Hair_Buzzed", beard: true, hairColor: "#2a1a12", skin: "#946040", under: KerchiefDark),
                new Held { Right = "viking_axe", Forearm = "shield_round" }, Fight("Walk_Loop", "Idle_Shield_Loop", "Sword_Regular_A", "Idle_Shield_Loop", "Idle_Shield_Break", cast: null) with { Slam = GroundSlam }, 1.1),
            // An enforcer: a big man in a red hood with a greataxe.
            "kerchief_enforcer" => new(visual, P(Sex.Male, "bare", hood: true, beard: true, hairColor: "#1a1410", skin: "#e0a47c", cloth: Kerchief, under: KerchiefDark),
                new Held { Right = "snake_axe" }, Fight("Jog_Fwd_Loop", "Sword_Idle", "Sword_Attack", "Sword_Idle"), 1.15),
            // Long bodies read as spiders when a pack closes on you: smaller,
            // and centred on the body so the head does not reach through the survivor.
            "wolf" or "wolf_blighted" or "wolf_spirit" => Beast(visual, 0.82, new Vector3(0, 0, -0.22f)),
            "wolf_alpha" => Beast(visual, 0.92, new Vector3(0, 0, -0.22f)),
            "boar" => Beast(visual, 0.95, new Vector3(0, 0, -0.12f)),
            // The diggers: small, pale, hunched, a lamp hung before each face.
            "lampling" or "lampling_sapper" or "grimtunnel" => Beast(visual, 1, null),
            _ => Of("skeleton_minion") with { Key = visual },
        };
        cache[visual] = s;
        return s;
    }

    static Spec Beast(string key, double scale, Vector3? offset) =>
        new(key, null, null, new Clips("run", "idle", "attack", "windup", "die", "rise", "hit"), scale, offset);

    /// <summary>Colour and glow a creature is drawn with, beyond its model.</summary>
    public static (Color Tint, float Glow) Tint(string visual) => visual switch
    {
        "risen_ally" => (new Color(0.7f, 1.1f, 0.8f), 0.12f),
        // One wolf model for all: the alpha's coat dark, the blighted one gone
        // sick and green, the spirit pale and lit from within.
        "wolf_alpha" => (new Color(0.55f, 0.53f, 0.52f), 0),
        "wolf_blighted" => (new Color(0.78f, 0.9f, 0.58f), 0.04f),
        "wolf_spirit" => (new Color(0.85f, 1.0f, 1.35f), 0.7f),
        _ => (Colors.White, 0),
    };
}
