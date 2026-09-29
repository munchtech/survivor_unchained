using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using static SurvivorUnchained.Sim.StatusKind;

namespace SurvivorUnchained.Content;

/* The arsenal. Every weapon fires on its own; what the survivor does is
 * choose them, rank them and decide what they become.
 *
 *   - Tags and a school on everything, so gear and boons can say "your
 *     projectiles" or "your fire" and mean it.
 *   - Evolution BRANCHES. A rank-8 weapon does not have one destiny; it
 *     becomes whatever the rest of the build pulls it toward. Each branch
 *     names the passive skill that evolves it (a rank of it is enough), and
 *     a weapon with both passives asks which it should become.
 *
 * Rank growth (applied by the runtime): +20% damage per rank, +4% area per
 * rank, +6% duration per rank, one more projectile at ranks 4 and 7. */

public enum WeaponBehavior { Aimed, Spray, Ring, Nova, Zone, Chain, Orbit, Storm, Bounce, Beam, Palm, Herd, Chakram, Slash }

/// <summary>A weapon's numbers; unset ones fall back (in an evolution's Set,
/// to the base).</summary>
public sealed class WeaponStats
{
    public double? Cooldown, Damage, Speed, Pierce, Range, Radius, Life, Homing, Splash, Spread, Duration, TickRate;
    public double? Chains, ChainRange, Bounces, OrbitRadius, OrbitSpeed, Strikes, StormRadius, BeamWidth, Reach, Arc;
    public double? Knockback, ExpandTime, Heal, Slow;
    public int? Projectiles;
    public bool? AtTarget;
    public StatusPayload? Status;
    /// <summary>A burst of shots in quick succession instead of all at once.</summary>
    public bool? Burst;
    /// <summary>Also leaves burning / hallowed / blighted ground where it hits.</summary>
    public GroundSpec? GroundOnHit;
    /// <summary>Projectiles split into smaller ones on hit.</summary>
    public int? SplitOnHit;
    /// <summary>Chains fork into two at each jump.</summary>
    public bool? Fork;
}

/// <summary>Multiplicative on damage, cooldown, area, speed, duration; additive on counts.</summary>
public sealed class EvoMods
{
    public double? Damage, Cooldown, Area, Speed, Duration;
    public int? Projectiles, Pierce, Bounces, Chains, Strikes;
}

public sealed class Evolution
{
    public string Id = "", Name = "", Description = "";
    /// <summary>The passive skills that evolve it: at rank 8 with a rank in any.</summary>
    public string[] Catalysts = System.Array.Empty<string>();
    public EvoMods Mods = new();
    public WeaponStats? Set;
    public WeaponBehavior? Behavior;
    public School? School;
    public Tag[]? AddTags;
    public string? Art;
}

public sealed class WeaponDef
{
    public string Id = "", Name = "";
    public School School;
    public WeaponBehavior Behavior;
    public Tag[] Tags = System.Array.Empty<Tag>();
    public WeaponStats Base = new();
    public string Art = "";
    /// <summary>Bosses and elites: crowd weapons hit one big target softly.</summary>
    public double? BossDamage;
    public string Description = "";
    public Evolution[] Evolutions = System.Array.Empty<Evolution>();
    /// <summary>Offered in the level-up pool? Starting-only weapons are not.</summary>
    public bool Findable;
}

public static class Weapons
{
    public const int MaxRank = 8;
    public const int MaxWeapons = 6;
    public const double DamageStep = 0.2, AreaStep = 0.04, DurationStep = 0.06;
    public const int ProjRankA = 4, ProjRankB = 7;

    static StatusPayload S(StatusKind k, double chance, double power, double duration) => new(k, chance, power, duration);
    static GroundSpec G(double radius, double duration, double dpsPct) => new(radius, duration, dpsPct);

    public static readonly Dictionary<string, WeaponDef> All = new WeaponDef[]
    {
        new()
        {
            Id = "oathblade", Name = "Oathblade", School = School.Physical, Behavior = WeaponBehavior.Slash, Tags = [Tag.Melee, Tag.Steel, Tag.Physical, Tag.Area],
            Base = new() { Cooldown = 1.05, Damage = 24, Reach = 2.8, Arc = 2.3, Knockback = 0.9, Projectiles = 1 },
            Art = "slash_steel", BossDamage = 1.4,
            Description = "Your blade swings on its own at whatever is nearest, cutting everything in a wide arc in front of you.",
            Evolutions =
            [
                new() { Id = "oathkeeper", Name = "Oathkeeper", Description = "Every swing throws a crescent of holy light that carries on through the crowd.",
                    Catalysts = ["ironhide"], Mods = new() { Damage = 1.5, Cooldown = 0.85, Area = 1.2 }, AddTags = [Tag.Holy, Tag.Projectile], Art = "slash_holy" },
                new() { Id = "graveedge", Name = "Grave-Edge", Description = "The edge drinks: every cut bleeds, and anything bleeding below a sixth of its life is simply finished.",
                    Catalysts = ["serration"], Mods = new() { Damage = 1.6, Cooldown = 0.9 }, Set = new() { Status = S(Bleed, 1, 0.35, 3) }, Art = "slash_blood" },
            ],
        },
        new()
        {
            Id = "cleaver", Name = "Butcher's Cleaver", School = School.Physical, Behavior = WeaponBehavior.Slash, Tags = [Tag.Melee, Tag.Steel, Tag.Physical, Tag.Area],
            Base = new() { Cooldown = 1.45, Damage = 34, Reach = 2.5, Arc = 3.4, Knockback = 1.3, Projectiles = 1, Status = S(Bleed, 0.35, 0.3, 3) },
            Art = "slash_heavy", BossDamage = 1.3,
            Description = "A heavy, wide chop all the way round the front of you. Opens wounds.",
            Evolutions =
            [
                new() { Id = "whirlwind", Name = "Whirlwind", Description = "The chop becomes a full turn: everything around you, every time.",
                    Catalysts = ["fleetfoot", "ferocity"], Mods = new() { Damage = 1.4, Cooldown = 0.8 }, Set = new() { Arc = 6.283 }, Art = "slash_spin" },
                new() { Id = "bonesplitter", Name = "Bonesplitter", Description = "Each chop sends a shockwave ahead of it that shatters the frozen and staggers the rest.",
                    Catalysts = ["might"], Mods = new() { Damage = 1.7, Area = 1.25 }, Set = new() { Knockback = 2.2 }, AddTags = [Tag.Explosion], Art = "slash_quake" },
            ],
        },
        new()
        {
            Id = "seeking_motes", Name = "Seeking Motes", School = School.Arcane, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Arcane],
            Base = new() { Cooldown = 0.93, Damage = 5.5, Speed = 8.4, Projectiles = 3, Pierce = 2, Range = 14, Homing = 5.5, Life = 2.2, Radius = 0.18, Burst = true },
            Art = "mote", BossDamage = 1.7, Findable = true,
            Description = "A rapid volley of small seeking motes that curve through the crowd on their own.",
            Evolutions =
            [
                new() { Id = "mote_cascade", Name = "Mote Cascade", Description = "The motes multiply beyond counting, and each one splits in two when it strikes.",
                    Catalysts = ["duplicity"], Mods = new() { Damage = 1.4, Projectiles = 3 }, Set = new() { SplitOnHit = 2 }, Art = "mote_cascade" },
                new() { Id = "starseeker", Name = "Starseeker", Description = "Motes hunt the strongest thing on the field, and they bite deeper for every critical strike.",
                    Catalysts = ["precision"], Mods = new() { Damage = 1.9, Cooldown = 0.85 }, Set = new() { Homing = 9 }, Art = "mote_star" },
            ],
        },
        new()
        {
            Id = "cinderfall", Name = "Cinderfall", School = School.Fire, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Fire, Tag.Explosion],
            Base = new() { Cooldown = 1.75, Damage = 31, Speed = 8.6, Projectiles = 1, Pierce = 0, Range = 15, Splash = 1.8, Life = 2.4, Radius = 0.28, Status = S(Burn, 0.5, 0.25, 3) },
            Art = "cinder", Findable = true,
            Description = "A slow, heavy cinder that bursts on impact and sets what it touches alight.",
            Evolutions =
            [
                new() { Id = "fallen_star", Name = "Fallen Star", Description = "The cinder becomes a falling star: a huge blast that leaves the ground burning.",
                    Catalysts = ["expanse"], Mods = new() { Damage = 1.5, Area = 1.45 }, Set = new() { GroundOnHit = G(2.2, 3, 0.25) }, Art = "star" },
                new() { Id = "living_flame", Name = "Living Flame", Description = "Cinders burst into three seeking flames that hunt on after the blast.",
                    Catalysts = ["perennial"], Mods = new() { Damage = 1.35, Cooldown = 0.85 }, Set = new() { SplitOnHit = 3, Homing = 4 }, Art = "living_flame" },
            ],
        },
        new()
        {
            Id = "rimeshard", Name = "Rimeshard", School = School.Frost, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Frost],
            Base = new() { Cooldown = 1.2, Damage = 18, Speed = 9.1, Projectiles = 1, Pierce = 2, Range = 14.5, Life = 2.2, Radius = 0.22, Status = S(Chill, 1, 1, 2.5) },
            Art = "shard", BossDamage = 1.1, Findable = true,
            Description = "Bitter cold that pierces and chills. Enough chill and a thing freezes solid.",
            Evolutions =
            [
                new() { Id = "deepwinter", Name = "Deepwinter", Description = "Winter takes the field: shards burst into a ring of smaller shards on the frozen.",
                    Catalysts = ["haste"], Mods = new() { Damage = 1.5, Cooldown = 0.8, Projectiles = 1 }, Set = new() { SplitOnHit = 4 }, Art = "shard_deep" },
                new() { Id = "glacier_spear", Name = "Glacier Spear", Description = "One enormous lance of ice that runs the length of the field and freezes all it passes.",
                    Catalysts = ["velocity"], Mods = new() { Damage = 2.1, Speed = 1.4, Pierce = 20 }, Set = new() { Radius = 0.5, Status = S(Chill, 1, 3, 3) }, Art = "spear_ice" },
            ],
        },
        new()
        {
            Id = "arcweb", Name = "Arcweb", School = School.Storm, Behavior = WeaponBehavior.Chain, Tags = [Tag.Chain, Tag.Spell, Tag.Storm],
            Base = new() { Cooldown = 1.65, Damage = 27, Chains = 5, ChainRange = 6.25, Range = 11, Status = S(Shock, 0.5, 1, 3) },
            Art = "arc", BossDamage = 3.5, Findable = true,
            Description = "Lightning that leaps from foe to foe.",
            Evolutions =
            [
                new() { Id = "skybreak", Name = "Skybreak", Description = "The sky answers every call: each leap also brings a bolt straight down.",
                    Catalysts = ["precision"], Mods = new() { Damage = 1.5, Chains = 2 }, AddTags = [Tag.Storm], Art = "arc_sky" },
                new() { Id = "tempest_coil", Name = "Tempest Coil", Description = "The lightning forks at every leap. A crowd becomes a web.",
                    Catalysts = ["expanse"], Mods = new() { Damage = 1.25 }, Set = new() { Fork = true }, Art = "arc_fork" },
            ],
        },
        new()
        {
            Id = "dawnpulse", Name = "Dawnpulse", School = School.Holy, Behavior = WeaponBehavior.Nova, Tags = [Tag.Nova, Tag.Area, Tag.Spell, Tag.Holy],
            Base = new() { Cooldown = 2.6, Damage = 27, Radius = 3.75, ExpandTime = 0.35, Knockback = 0.65, Status = S(Sear, 1, 1, 3) },
            Art = "nova_holy", BossDamage = 2.4, Findable = true,
            Description = "A ring of Light erupts outward from you, throwing back what it touches. The dead hate it.",
            Evolutions =
            [
                new() { Id = "circle_of_dawn", Name = "Circle of Dawn", Description = "Each dawn mends you as it burns them.",
                    Catalysts = ["vitality", "recovery"], Mods = new() { Damage = 1.5, Area = 1.2 }, Set = new() { Heal = 4 }, Art = "nova_dawn" },
                new() { Id = "sunbreak", Name = "Sunbreak", Description = "The pulse leaves a ring of daylight on the ground that goes on burning.",
                    Catalysts = ["might"], Mods = new() { Damage = 1.4 }, Set = new() { GroundOnHit = G(3.5, 2.5, 0.3) }, Art = "nova_sun" },
            ],
        },
        new()
        {
            Id = "hallowed_ring", Name = "Hallowed Ground", School = School.Holy, Behavior = WeaponBehavior.Zone, Tags = [Tag.Zone, Tag.Area, Tag.Aura, Tag.Holy],
            Base = new() { Cooldown = 3.95, Damage = 10, Radius = 3, Duration = 4, TickRate = 0.5, Status = S(Sear, 0.4, 1, 2) },
            Art = "zone_holy", BossDamage = 1.7, Findable = true,
            Description = "Hallows the ground beneath your feet. Whatever stands in it burns.",
            Evolutions =
            [
                new() { Id = "sanctified_earth", Name = "Sanctified Earth", Description = "Sacred ground that shelters as it burns: stand in it and blows glance off you.",
                    Catalysts = ["ironhide"], Mods = new() { Damage = 1.5, Area = 1.25, Duration = 1.3 }, Art = "zone_sanct" },
                new() { Id = "pyre_of_faith", Name = "Pyre of Faith", Description = "The ground catches fire as well as light. Everything in it burns twice.",
                    Catalysts = ["searing"], Mods = new() { Damage = 1.4 }, School = School.Fire, Set = new() { Status = S(Burn, 0.6, 0.3, 3) }, AddTags = [Tag.Fire], Art = "zone_pyre" },
            ],
        },
        new()
        {
            Id = "umbral_bolt", Name = "Umbral Bolt", School = School.Shadow, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Shadow],
            Base = new() { Cooldown = 1.1, Damage = 23.7, Speed = 9.1, Projectiles = 1, Pierce = 2, Range = 14.5, Life = 2.4, Radius = 0.22 },
            Art = "umbral", Findable = true,
            Description = "Bolts of shadow that tear straight through ranks.",
            Evolutions =
            [
                new() { Id = "ruin_bolt", Name = "Ruin Bolt", Description = "Ruin that nothing can stop: the bolt passes through everything and tears a wound behind it.",
                    Catalysts = ["might"], Mods = new() { Damage = 1.6, Pierce = 20, Speed = 1.2 }, Art = "ruin" },
                new() { Id = "soul_siphon", Name = "Soul Siphon", Description = "Each bolt drinks a little of whatever it passes through and gives it to you.",
                    Catalysts = ["recovery"], Mods = new() { Damage = 1.4, Projectiles = 1 }, Set = new() { Heal = 0.6 }, Art = "siphon" },
            ],
        },
        new()
        {
            Id = "knifestorm", Name = "Knifestorm", School = School.Physical, Behavior = WeaponBehavior.Ring, Tags = [Tag.Projectile, Tag.Thrown, Tag.Steel, Tag.Physical],
            Base = new() { Cooldown = 1.43, Damage = 16.4, Speed = 8.65, Projectiles = 6, Pierce = 1, Life = 0.9, Radius = 0.2, Status = S(Bleed, 0.15, 0.3, 3) },
            Art = "dagger", BossDamage = 2.9, Findable = true,
            Description = "A whirling ring of thrown steel in every direction.",
            Evolutions =
            [
                new() { Id = "steel_flurry", Name = "Steel Flurry", Description = "The steel never stops moving: twice the knives, twice as often.",
                    Catalysts = ["fleetfoot"], Mods = new() { Damage = 1.3, Cooldown = 0.65, Projectiles = 4 }, Art = "dagger_flurry" },
                new() { Id = "thousand_cuts", Name = "A Thousand Cuts", Description = "Every knife opens a wound, and wounds on the same body stack.",
                    Catalysts = ["serration"], Mods = new() { Damage = 1.4, Projectiles = 2 }, Set = new() { Status = S(Bleed, 1, 0.4, 3.5) }, Art = "dagger_blood" },
            ],
        },
        new()
        {
            Id = "axe_gyre", Name = "Axe Gyre", School = School.Physical, Behavior = WeaponBehavior.Orbit, Tags = [Tag.Orbit, Tag.Melee, Tag.Steel, Tag.Physical, Tag.Area],
            Base = new() { Cooldown = 4.6, Damage = 23.7, Projectiles = 3, OrbitRadius = 2.1, OrbitSpeed = 4.2, Duration = 3.2, Radius = 0.5 },
            Art = "axe", Findable = true,
            Description = "Axes circle you, shredding all who close in.",
            Evolutions =
            [
                new() { Id = "gyrestorm", Name = "Gyrestorm", Description = "Become the storm of blades: more axes, spinning faster, never stopping.",
                    Catalysts = ["ferocity"], Mods = new() { Damage = 1.5, Projectiles = 3, Duration = 1.8 }, Set = new() { OrbitSpeed = 5.2 }, Art = "axe_storm" },
                new() { Id = "reavers_wheel", Name = "Reaver's Wheel", Description = "The axes bite and stay bitten: every cut bleeds, and a bleeding kill flings the axe outward.",
                    Catalysts = ["serration"], Mods = new() { Damage = 1.5 }, Set = new() { Status = S(Bleed, 1, 0.35, 3), OrbitRadius = 2.8 }, Art = "axe_blood" },
            ],
        },
        new()
        {
            Id = "volley", Name = "Volley", School = School.Physical, Behavior = WeaponBehavior.Spray, Tags = [Tag.Projectile, Tag.Ranged, Tag.Physical],
            Base = new() { Cooldown = 1.54, Damage = 15.5, Speed = 10.5, Projectiles = 3, Pierce = 2, Range = 15.5, Spread = 0.16, Life = 1.7, Radius = 0.2 },
            Art = "arrow", BossDamage = 1.4, Findable = true,
            Description = "A widening spread of hunting arrows loosed at the nearest foe.",
            Evolutions =
            [
                new() { Id = "arrowfall", Name = "Arrowfall", Description = "The sky darkens with arrows: each volley also rains down on the thickest part of the crowd.",
                    Catalysts = ["velocity"], Mods = new() { Damage = 1.4, Projectiles = 2 }, Set = new() { Strikes = 6, StormRadius = 5 }, Art = "arrow_rain" },
                new() { Id = "predators_volley", Name = "Predator's Volley", Description = "Arrows fly straight to the marked and the wounded, and every one leaves its own mark.",
                    Catalysts = ["precision"], Mods = new() { Damage = 1.6 }, Set = new() { Homing = 3, Status = S(Mark, 0.35, 1, 4) }, Art = "arrow_mark" },
            ],
        },
        new()
        {
            Id = "moonbrand", Name = "Moonbrand", School = School.Arcane, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Arcane],
            Base = new() { Cooldown = 1.32, Damage = 21.8, Speed = 7.3, Projectiles = 1, Pierce = 0, Range = 14, Homing = 4, Life = 2.6, Radius = 0.24, Status = S(Mark, 0.25, 1, 4) },
            Art = "moon", Findable = true,
            Description = "Moonlit flame that tracks its prey and leaves it marked.",
            Evolutions =
            [
                new() { Id = "moonfall", Name = "Moonfall", Description = "Moons fall wherever the enemy gathers.",
                    Catalysts = ["greed", "expanse"], Mods = new() { Damage = 1.5 }, Behavior = WeaponBehavior.Storm, Set = new() { Strikes = 5, StormRadius = 5.75, Splash = 1.5 }, Art = "moonfall" },
                new() { Id = "lunar_brand", Name = "Lunar Brand", Description = "Every moon marks, and a marked thing that dies throws the mark to its neighbours.",
                    Catalysts = ["fortune"], Mods = new() { Damage = 1.5, Projectiles = 1 }, Set = new() { Status = S(Mark, 1, 1, 6) }, Art = "moon_brand" },
            ],
        },
        new()
        {
            Id = "judgement_disc", Name = "Judgement Disc", School = School.Holy, Behavior = WeaponBehavior.Bounce, Tags = [Tag.Projectile, Tag.Thrown, Tag.Bounce, Tag.Holy],
            Base = new() { Cooldown = 2.3, Damage = 27.3, Speed = 9.8, Projectiles = 1, Bounces = 5, Range = 15, Life = 3.0, Radius = 0.28, Knockback = 0.3 },
            Art = "disc", BossDamage = 2.45, Findable = true,
            Description = "A hurled shield that ricochets between enemies.",
            Evolutions =
            [
                new() { Id = "reckoning", Name = "Reckoning", Description = "Judgement finds every last one of them: endless ricochets that grow heavier with each.",
                    Catalysts = ["fortune", "precision"], Mods = new() { Damage = 1.4, Bounces = 6 }, Art = "disc_reckon" },
                new() { Id = "aegis_wheel", Name = "Aegis Wheel", Description = "The shield comes home each time, and while it flies it guards you.",
                    Catalysts = ["ironhide", "vitality"], Mods = new() { Damage = 1.5, Projectiles = 1 }, Art = "disc_aegis" },
            ],
        },
        new()
        {
            Id = "blightfield", Name = "Blightfield", School = School.Shadow, Behavior = WeaponBehavior.Zone, Tags = [Tag.Zone, Tag.Area, Tag.Dot, Tag.Shadow],
            Base = new() { Cooldown = 4.3, Damage = 11.8, Radius = 3.25, Duration = 4.5, TickRate = 0.45, AtTarget = true, Status = S(Poison, 0.6, 0.2, 4) },
            Art = "zone_blight", Findable = true,
            Description = "Corrupts the ground under the nearest crowd; anything standing in it rots.",
            Evolutions =
            [
                new() { Id = "blighted_earth", Name = "Blighted Earth", Description = "The blight spreads wider the longer it feeds, and holds what it feeds on.",
                    Catalysts = ["chilling"], Mods = new() { Damage = 1.4, Area = 1.3, Duration = 1.3 }, Set = new() { Slow = 0.5 }, Art = "zone_blight2" },
                new() { Id = "plaguebloom", Name = "Plaguebloom", Description = "Whatever dies in the blight bursts, and the blight goes on with them.",
                    Catalysts = ["perennial"], Mods = new() { Damage = 1.4 }, Set = new() { GroundOnHit = G(2, 3, 0.3) }, Art = "zone_plague" },
            ],
        },
        new()
        {
            Id = "reaving_arc", Name = "Reaving Arc", School = School.Shadow, Behavior = WeaponBehavior.Nova, Tags = [Tag.Nova, Tag.Area, Tag.Melee, Tag.Shadow],
            Base = new() { Cooldown = 2.4, Damage = 31, Radius = 3.25, ExpandTime = 0.28, Knockback = 0.5, Heal = 3 },
            Art = "nova_blood", BossDamage = 2.9, Findable = true,
            Description = "A sweeping graveblade that carves health out of the wound it makes.",
            Evolutions =
            [
                new() { Id = "rend_and_mend", Name = "Rend and Mend", Description = "The blade drinks deeper than any wound can hold.",
                    Catalysts = ["recovery", "vitality"], Mods = new() { Damage = 1.5, Area = 1.15 }, Set = new() { Heal = 6 }, Art = "nova_rend" },
                new() { Id = "harrowing", Name = "The Harrowing", Description = "What the arc kills gets up again, briefly, on your side.",
                    Catalysts = ["expanse"], Mods = new() { Damage = 1.4 }, AddTags = [Tag.Summon], Art = "nova_harrow" },
            ],
        },
        new()
        {
            Id = "grave_tether", Name = "Grave Tether", School = School.Shadow, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Shadow, Tag.Heal],
            Base = new() { Cooldown = 1.6, Damage = 25.5, Speed = 9.5, Projectiles = 1, Pierce = 2, Range = 15, Life = 2.4, Radius = 0.24, Heal = 1.5 },
            Art = "tether", Findable = true,
            Description = "A coil of dark magic that wounds the living and knits your own flesh back together.",
            Evolutions =
            [
                new() { Id = "tether_of_anguish", Name = "Tether of Anguish", Description = "The tether takes more, and gives more back.",
                    Catalysts = ["wisdom", "recovery"], Mods = new() { Damage = 1.5, Projectiles = 1 }, Set = new() { Heal = 3 }, Art = "tether2" },
                new() { Id = "deathcoil", Name = "Deathcoil", Description = "Each coil leaves the struck marked for the grave: they take more from everything.",
                    Catalysts = ["duplicity"], Mods = new() { Damage = 1.4 }, Set = new() { Status = S(Mark, 1, 1, 4) }, Art = "tether_mark" },
            ],
        },
        new()
        {
            Id = "iron_palms", Name = "Iron Palms", School = School.Physical, Behavior = WeaponBehavior.Palm, Tags = [Tag.Melee, Tag.Physical, Tag.Area],
            Base = new() { Cooldown = 0.95, Damage = 15, Projectiles = 3, Reach = 2.95, Arc = 1.25, Knockback = 0.35 },
            Art = "palm", BossDamage = 1.15, Findable = true,
            Description = "A flurry of open-handed strikes at whatever is closest, each a short cone that hits everything in it.",
            Evolutions =
            [
                new() { Id = "temple_breaker", Name = "Temple Breaker", Description = "Every palm lands like the temple bell.",
                    Catalysts = ["evasion"], Mods = new() { Damage = 1.6, Area = 1.2 }, Set = new() { Knockback = 0.9 }, Art = "palm_temple" },
                new() { Id = "thunder_palm", Name = "Thunder Palm", Description = "The palms carry the storm into whatever they strike.",
                    Catalysts = ["haste"], Mods = new() { Damage = 1.45 }, School = School.Storm, Set = new() { Status = S(Shock, 0.6, 1, 3) }, AddTags = [Tag.Storm], Art = "palm_storm" },
            ],
        },
        new()
        {
            Id = "spirit_herd", Name = "Spirit Herd", School = School.Nature, Behavior = WeaponBehavior.Herd, Tags = [Tag.Summon, Tag.Nature, Tag.Area],
            Base = new() { Cooldown = 2.6, Damage = 21, Speed = 8.25, Projectiles = 2, Pierce = 99, Range = 15.5, Life = 1.8, Radius = 0.4, Knockback = 0.55 },
            Art = "herd", BossDamage = 1.8, Findable = true,
            Description = "Spirit beasts stampede from behind you toward the nearest foe, trampling everything in the way.",
            Evolutions =
            [
                new() { Id = "great_herd", Name = "The Great Herd", Description = "The herd does not end. It only thins.",
                    Catalysts = ["perennial"], Mods = new() { Damage = 1.4, Projectiles = 3, Duration = 1.3 }, Art = "herd_great" },
                new() { Id = "wild_hunt", Name = "The Wild Hunt", Description = "The herd runs in green fire, and each beast goes up in it at the end of its run.",
                    Catalysts = ["fleetfoot"], Mods = new() { Damage = 1.4 }, Set = new() { Splash = 1.9 }, AddTags = [Tag.Explosion], Art = "herd_hunt" },
            ],
        },
        new()
        {
            Id = "thornbloom", Name = "Thornbloom", School = School.Nature, Behavior = WeaponBehavior.Zone, Tags = [Tag.Zone, Tag.Area, Tag.Nature],
            Base = new() { Cooldown = 3.8, Damage = 11, Radius = 2.3, Duration = 4, TickRate = 0.5, AtTarget = true, Slow = 0.55 },
            Art = "zone_thorn", Findable = true,
            Description = "Brambles burst up under the nearest crowd, tearing at everything caught and holding it slow.",
            Evolutions =
            [
                new() { Id = "everbloom", Name = "Everbloom", Description = "The brambles flower, and the flowers have thorns too.",
                    Catalysts = ["thorns"], Mods = new() { Damage = 1.4, Area = 1.3, Duration = 1.3 }, Art = "zone_bloom" },
                new() { Id = "strangleroot", Name = "Strangleroot", Description = "The roots do not let go: what they hold is held still.",
                    Catalysts = ["chilling"], Mods = new() { Damage = 1.3 }, Set = new() { Slow = 0.15, Status = S(Stun, 0.25, 1, 1) }, Art = "zone_root" },
            ],
        },
        new()
        {
            Id = "gale_chakram", Name = "Gale Chakram", School = School.Physical, Behavior = WeaponBehavior.Chakram, Tags = [Tag.Projectile, Tag.Thrown, Tag.Steel, Tag.Physical],
            Base = new() { Cooldown = 1.7, Damage = 16, Speed = 9.5, Projectiles = 1, Range = 8.25, Life = 2.6, Radius = 0.3 },
            Art = "chakram", BossDamage = 1.4, Findable = true,
            Description = "A bladed ring thrown out on the wind. It cuts everything on the way out, and on the way back.",
            Evolutions =
            [
                new() { Id = "razorgale", Name = "Razorgale", Description = "The ring splits the wind in two and comes back sharper.",
                    Catalysts = ["serration"], Mods = new() { Damage = 1.5, Projectiles = 1 }, Set = new() { Status = S(Bleed, 0.5, 0.3, 3) }, Art = "chakram_razor" },
                new() { Id = "hailwheel", Name = "Hailwheel", Description = "A spinning edge through a hailstorm comes back cold.",
                    Catalysts = ["chilling"], Mods = new() { Damage = 1.4, Projectiles = 1 }, School = School.Frost, Set = new() { Status = S(Chill, 1, 1, 2.5) }, AddTags = [Tag.Frost], Art = "chakram_hail" },
            ],
        },
        new()
        {
            Id = "verdant_lance", Name = "Verdant Lance", School = School.Nature, Behavior = WeaponBehavior.Beam, Tags = [Tag.Beam, Tag.Spell, Tag.Nature],
            Base = new() { Cooldown = 1.43, Damage = 20, Range = 15.5, BeamWidth = 0.65, Duration = 0.35, Status = S(Poison, 0.3, 0.15, 3) },
            Art = "beam_green", BossDamage = 2.45, Findable = true,
            Description = "A lance of green fire that burns everything standing in its path.",
            Evolutions =
            [
                new() { Id = "verdant_gaze", Name = "Verdant Gaze", Description = "The gaze widens until the world is a line of green fire.",
                    Catalysts = ["evasion", "expanse"], Mods = new() { Damage = 1.5, Area = 1.8 }, Art = "beam_gaze" },
                new() { Id = "sunlance", Name = "Sunlance", Description = "The lance turns gold, and holy, and sears the dead to ash.",
                    Catalysts = ["searing"], Mods = new() { Damage = 1.5 }, School = School.Holy, Set = new() { Status = S(Sear, 1, 1, 3) }, AddTags = [Tag.Holy], Art = "beam_sun" },
            ],
        },
    }.ToDictionary(w => w.Id);

    /// <summary>The weapons the level-up draft can offer.</summary>
    public static readonly string[] Pool = All.Values.Where(w => w.Findable).Select(w => w.Id).ToArray();

    public static WeaponDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown weapon {id}");
}
