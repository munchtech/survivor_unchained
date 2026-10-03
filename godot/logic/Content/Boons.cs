using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using static SurvivorUnchained.Sim.StatusKind;

namespace SurvivorUnchained.Content;

/* What an ember level can buy besides combat skills (the weapons).
 *
 * PASSIVE skills are ordinary picks, ranked like weapons: numbers a build
 * is shaped around. Each weapon's evolutions name the passive that evolves
 * them: a weapon at rank 8 with one rank of it can become something else.
 *
 * BLESSINGS change how the fight works: each adds a rule to the machine
 * (marks, companions, chain reactions, bargains). They are milestones, not
 * picks. The GREAT blessings are an arena's own: one chosen as it begins and
 * another at its fifteenth minute, from all of them, whoever the survivor is
 * (anyone can do anything in the ember). Each works from the first second,
 * whatever the build, and deepens: the second may be a rank of the first
 * (Deeper: what each rank adds). The rest come at the Milestones (early,
 * then further apart), and wait until the build has something for them to
 * act on; a milestone may deepen a great blessing held, never give a new one.
 *
 * Every entry says what it touches with Tags, so the level-up draft can lean
 * toward what the build is already doing without ever forcing it. */

public enum Rarity { Common, Uncommon, Rare, Epic, Legendary }
public enum BoonKind { Passive, Blessing }

/// <summary>What a build must have for a card to be offered: a status it
/// applies, a kind of skill, a blessing held; any of several, or all of them
/// (a duo blessing wants two families at once).</summary>
public sealed record Requirement(StatusKind? Status = null, Tag? Tag = null, string? Boon = null, Requirement[]? Any = null, Requirement[]? All = null);

public sealed class BoonDef
{
    public string Id = "", Name = "", Icon = "";
    public Rarity Rarity;
    public int Max;
    public BoonKind Kind;
    /// <summary>Plain-language summary.</summary>
    public string Text = "";
    public string? Detail;
    public Func<int, StatMod[]>? Mods;
    public TriggerDef[]? Triggers;
    /// <summary>Offered only when the build meets this.</summary>
    public Requirement? Requires;
    public Tag[] Tags = Array.Empty<Tag>();
    /// <summary>What ranks 2 and 3 add: the words, and any triggers of their own.</summary>
    public string[]? DeeperText;
    public TriggerDef[][]? Deeper;
}

public static class Boons
{
    /// <summary>The ember levels that bring a blessing: the first a minute in,
    /// then further apart (5, 12, 21, 32, 45, 60 ...): at the ember's pace,
    /// about the first, fifth, tenth, twentieth and twenty-eighth minutes,
    /// between the great blessings rather than on them.</summary>
    public static readonly int[] Milestones = MakeMilestones();

    static int[] MakeMilestones()
    {
        var o = new List<int>();
        for (int l = 5, gap = 7; l < 400; l += gap, gap += 2) o.Add(l);
        return o.ToArray();
    }

    /// <summary>The great blessings, an arena's first choice and its fifteenth
    /// minute's: each works from the first second, whatever the build, and deepens.</summary>
    public static readonly string[] Great =
    [
        "hunters_mark", "momentum", "bloodthirst", "spirit_companion", "arcane_overflow", "glass_cannon",
        "duelists_grace", "restless_hands", "cinderwake", "iron_vow", "ember_tithe", "stormborn",
        "from_the_ashes", "grounding", "rootbind", "go_for_the_throat",
    ];

    /// <summary>What each great blessing is for (docs/SKILLS_DESIGN.md, "Great
    /// blessings"): every path's list holds a ward, and a path slow to fell a
    /// champion holds an answer.</summary>
    public enum GreatRole { Power, Ward, Answer, Tempo }

    public static readonly Dictionary<string, GreatRole> GreatRoles = new()
    {
        ["momentum"] = GreatRole.Power, ["arcane_overflow"] = GreatRole.Power, ["glass_cannon"] = GreatRole.Power,
        ["duelists_grace"] = GreatRole.Power, ["cinderwake"] = GreatRole.Power, ["stormborn"] = GreatRole.Power,
        ["spirit_companion"] = GreatRole.Power,
        ["bloodthirst"] = GreatRole.Ward, ["iron_vow"] = GreatRole.Ward, ["from_the_ashes"] = GreatRole.Ward, ["grounding"] = GreatRole.Ward,
        ["hunters_mark"] = GreatRole.Answer, ["rootbind"] = GreatRole.Answer, ["go_for_the_throat"] = GreatRole.Answer,
        ["restless_hands"] = GreatRole.Tempo, ["ember_tithe"] = GreatRole.Tempo,
    };
    /// <summary>Passive skills a survivor can hold at once.</summary>
    public const int MaxPassives = 6;
    public static bool IsMilestone(int level) => Array.BinarySearch(Milestones, level) >= 0;
    public static bool IsGreat(string id) => Array.IndexOf(Great, id) >= 0;

    static StatMod Inc(string stat, double v, string source) => new(stat, ModKind.Inc, v, source);
    static StatMod Flat(string stat, double v, string source) => new(stat, ModKind.Flat, v, source);
    static StatMod More(string stat, double v, string source) => new(stat, ModKind.More, v, source);
    static StatusPayload P(StatusKind k, double chance, double power, double duration) => new(k, chance, power, duration);
    static TriggerDef T(TriggerEvent on, Effect[] effects, TriggerCond? when = null, double? chance = null, double? icd = null, string? text = null) =>
        new() { On = on, Effects = effects, When = when, Chance = chance, Icd = icd, Text = text };

    public static readonly Dictionary<string, BoonDef> All = new BoonDef[]
    {
        /* -------------------------------------------------- passive skills -- */
        new() { Id = "might", Name = "Legion Bronze", Icon = "fist", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "Old-empire bronze, green at the edges and still the hardest thing in the valley: +10% damage with everything.", Mods = r => [Inc(Stat.Damage, 0.1 * r, "boon:might")] },
        new() { Id = "haste", Name = "Trimmed Wick", Icon = "wing", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "A wick trimmed short burns quick: every weapon fires 8% more often.", Mods = r => [More(Stat.Cooldown, Math.Pow(0.92, r) - 1, "boon:haste")] },
        new() { Id = "fleetfoot", Name = "Toll-Runner's Boots", Icon = "boot", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "Worn thin on the toll road: +10% movement speed.", Mods = r => [Inc(Stat.MoveSpeed, 0.1 * r, "boon:fleetfoot")] },
        new() { Id = "greed", Name = "Lampling's Scoop", Icon = "magnet", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "Ember, gold and draughts fly to you from 1.2 m farther, and every stone holds 4% more ember. The Dig will want it back.",
            Mods = r => [Flat(Stat.PickupRadius, 1.2 * r, "boon:greed"), Inc(Stat.XpGain, 0.04 * r, "boon:greed")] },
        new() { Id = "vitality", Name = "Morrow Pippins", Icon = "heart", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Heal],
            Text = "A pocketful of the valley's apples: +25 maximum health, and a heal when taken.", Mods = r => [Flat(Stat.MaxHealth, 25 * r, "boon:vitality")] },
        new() { Id = "ironhide", Name = "Watch Mail", Icon = "shield", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "From the Watch's stores, never paid for: +3 armour. Each point helps a little less than the last.", Mods = r => [Flat(Stat.Armor, 3 * r, "boon:ironhide")] },
        new() { Id = "precision", Name = "Night-Eyes", Icon = "crosshair", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive,
            Text = "You see the weak places better in the dark: +7% critical strike chance.", Mods = r => [Flat(Stat.CritChance, 0.07 * r, "boon:precision")] },
        new() { Id = "ferocity", Name = "Wolf-Tooth", Icon = "claw", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "It bites deeper than it should: +25% critical strike damage.", Mods = r => [Flat(Stat.CritDamage, 0.25 * r, "boon:ferocity")] },
        new() { Id = "expanse", Name = "Ford Lamp", Icon = "expand", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Area],
            Text = "Light thrown wide, like the lamps at the ford: +12% area. Novas, fields, orbits, storms and auras are bigger; chains, beams and blades reach farther.",
            Mods = r => [Inc(Stat.Area, 0.12 * r, "boon:expanse")] },
        new() { Id = "duplicity", Name = "Second Shadow", Icon = "triple", Rarity = Rarity.Epic, Max = 2, Kind = BoonKind.Passive, Tags = [Tag.Projectile],
            Text = "Everything you send out has a shadow that flies beside it: +1 projectile.", Mods = r => [Flat(Stat.Projectiles, r, "boon:duplicity")] },
        new() { Id = "fortune", Name = "Crossroads Penny", Icon = "coin", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "Left at the crossroads, and picked up again: +10% luck. A fourth card more often, rarer cards, ranks that surge, better drops.", Mods = r => [Flat(Stat.Luck, 0.1 * r, "boon:fortune")] },
        new() { Id = "wisdom", Name = "Wayfinder's Chart", Icon = "book", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "Every road on it, and some that aren't there yet: +6% ember from every stone, and a redraw with every rank.", Mods = r => [Inc(Stat.XpGain, 0.06 * r, "boon:wisdom")] },
        new() { Id = "recovery", Name = "Bitterroot", Icon = "leaf", Rarity = Rarity.Common, Max = 4, Kind = BoonKind.Passive, Tags = [Tag.Heal],
            Text = "Chewed slowly, as the hunters do: +0.6 health regenerated per second.", Mods = r => [Flat(Stat.Regen, 0.6 * r, "boon:recovery")] },
        new() { Id = "velocity", Name = "Grey Fletching", Icon = "spear", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Projectile],
            Text = "Goose-grey and cut close: projectiles fly 12% faster and land 5% harder.",
            Mods = r => [Inc(Stat.ProjectileSpeed, 0.12 * r, "boon:velocity"), Inc(Stat.DamageOf(Tag.Projectile), 0.05 * r, "boon:velocity")] },
        new() { Id = "perennial", Name = "Evergreen", Icon = "perennial", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Zone, Tag.Orbit, Tag.Summon],
            Text = "+10% duration: fields, gyres, beasts and ground effects last longer.", Mods = r => [Inc(Stat.Duration, 0.1 * r, "boon:perennial")] },
        new() { Id = "evasion", Name = "Fen Step", Icon = "feint", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "Light on soft ground: +7% chance to avoid a blow entirely.", Mods = r => [Flat(Stat.Dodge, 0.07 * r, "boon:evasion")] },
        new() { Id = "thorns", Name = "Bramble Coat", Icon = "thorn", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Nature, Tag.Aura],
            Text = "Struck, you burst with thorns: everything close takes a blow that grows with the ember, and what struck you takes a fifth of its blow back.",
            Mods = r => [Flat(Stat.Thorns, r, "boon:thorns")] },
        new() { Id = "serration", Name = "Whetstone", Icon = "bleed", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive, Tags = [Tag.Physical, Tag.Dot],
            Text = "Critical strikes open a wound that bleeds 30% of the blow over 3 s.",
            Detail = "Bleeding hurts more while the victim moves. A fresh crit reopens the wound at whichever bleed is worse.",
            Mods = r => [Flat(Stat.CritChance, 0.02 * r, "boon:serration")],
            Triggers = [T(TriggerEvent.Crit, [new Effect.Apply(P(Bleed, 1, 0.3, 3), OnHit: true)], text: "Crits bleed.")] },
        new() { Id = "chilling", Name = "The Ford's Cold", Icon = "frostaura", Rarity = Rarity.Rare, Max = 3, Kind = BoonKind.Passive, Tags = [Tag.Frost, Tag.Aura],
            Text = "The cold of the ford never quite left you: creatures near you are slowed, more as they come closer.", Mods = _ => [] },
        new() { Id = "searing", Name = "Morning Light", Icon = "retaura", Rarity = Rarity.Rare, Max = 4, Kind = BoonKind.Passive, Tags = [Tag.Holy, Tag.Aura, Tag.Area],
            Text = "A holy light sears everything near you twice a second.", Mods = _ => [] },
        new() { Id = "emberblood", Name = "Emberblood", Icon = "flame", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Fire, Tag.Dot],
            Text = "+10% fire damage; what you set burning burns 15% longer, and strikes you 6% weaker.",
            Mods = r => [Inc(Stat.DamageOf(School.Fire), 0.1 * r, "boon:emberblood"), Inc(Stat.StatusDurationOf(Burn), 0.15 * r, "boon:emberblood")] },
        new() { Id = "conduit", Name = "Conduit", Icon = "static", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Storm, Tag.Chain],
            Text = "+10% storm damage, and the shocked take 6% more from the blow that finds them.",
            Mods = r => [Inc(Stat.DamageOf(School.Storm), 0.1 * r, "boon:conduit"), Flat(Stat.ShockBonus, 0.06 * r, "boon:conduit")] },
        new() { Id = "venom", Name = "Ember-Slurry", Icon = "plague", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Dot],
            Text = "What the Dig pours into the stream: damage over time (burning, bleeding, poison, searing) is 12% stronger, and every status takes hold 10% more often.",
            Mods = r => [Inc(Stat.DamageOf(Tag.Dot), 0.12 * r, "boon:venom"), Flat(Stat.StatusChance, 0.1 * r, "boon:venom")] },
        new() { Id = "kinship", Name = "Pack-Bond", Icon = "spiritwolf", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Summon],
            Text = "What fights for you strikes 15% harder and is 15% tougher.",
            Mods = r => [Inc(Stat.SummonDamage, 0.15 * r, "boon:kinship"), Inc(Stat.SummonHealth, 0.15 * r, "boon:kinship")] },
        new() { Id = "spirit_companion", Name = "Spirit Companion", Icon = "spiritwolf", Rarity = Rarity.Rare, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Summon],
            Text = "Call a spirit wolf that hunts beside you. Each rank calls another.", Mods = _ => [],
            DeeperText = ["A second wolf answers.", "A third wolf: a pack of your own."] },
        new() { Id = "grave_call", Name = "Grave Call", Icon = "risen", Rarity = Rarity.Rare, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Summon, Tag.Shadow],
            Text = "Raise a ghoul to shamble after the horde. Slow, and it hits very hard.", Mods = _ => [] },
        new() { Id = "dread_command", Name = "Dread Command", Icon = "command", Rarity = Rarity.Epic, Max = 5, Kind = BoonKind.Blessing, Tags = [Tag.Summon],
            Text = "+30% damage and +10% attack speed for everything you have summoned.", Requires = new(Tag: Tag.Summon),
            Mods = r => [Inc(Stat.SummonDamage, 0.3 * r, "boon:dread_command"), Inc(Stat.SummonHaste, 0.1 * r, "boon:dread_command")] },
        new() { Id = "dark_bargain", Name = "Dark Bargain", Icon = "skull", Rarity = Rarity.Epic, Max = 3, Kind = BoonKind.Blessing,
            Text = "The dark grows: 15% more of them, and 5% faster. You grow too: +15% ember and gold.",
            Detail = "A curse you choose. More creatures means more ember, more gold, and more danger. Stacks.",
            Mods = r => [Inc(Stat.XpGain, 0.15 * r, "boon:dark_bargain"), Inc(Stat.GoldGain, 0.15 * r, "boon:dark_bargain")] },
        new() { Id = "warding", Name = "Warding Light", Icon = "aegis", Rarity = Rarity.Rare, Max = 3, Kind = BoonKind.Passive, Tags = [Tag.Holy],
            Text = "Blocks one blow completely, then recharges (12 / 9 / 6 s).", Mods = r => [Flat(Stat.Block, r, "boon:warding")] },

        /* ------------------------------------------------------- blessings -- */
        new() { Id = "kindling", Name = "Kindling", Icon = "kindling", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Fire, Tag.Dot],
            Text = "Anything that dies burning hands its fire to two neighbours.", Requires = new(Status: Burn),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Spread(Burn, 3.2, 2, 2)], new() { TargetStatus = Burn })] },
        new() { Id = "pyre_burst", Name = "Pyre Burst", Icon = "pyre", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Fire, Tag.Explosion],
            Text = "Burning creatures have a 25% chance to explode when they die.", Requires = new(Status: Burn),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.4, 0.22, Basis.MaxHp, School.Fire, P(Burn, 0.7, 0.25, 3))], new() { TargetStatus = Burn }, chance: 0.25, icd: 0.05)] },
        new() { Id = "emberseekers", Name = "Emberseekers", Icon = "embers", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Fire, Tag.Projectile],
            Text = "Every explosion throws out two embers that seek the strongest creature near you.", Requires = new(Tag: Tag.Explosion),
            Triggers = [T(TriggerEvent.Explode, [new Effect.Missiles(2, 14, Basis.Flat, School.Fire, Seek.Strongest, 9, "ember_seeker")], icd: 0.2)] },
        new() { Id = "shatter", Name = "Shatter", Icon = "shatter", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Frost, Tag.Explosion],
            Text = "Frozen creatures shatter when they die, spraying frost that chills everything nearby.", Requires = new(Status: Chill),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.6, 0.25, Basis.MaxHp, School.Frost, P(Chill, 1, 2, 2.5))], new() { TargetStatus = Frozen }, icd: 0.1)] },
        new() { Id = "deep_chill", Name = "Deep Chill", Icon = "frostaura", Rarity = Rarity.Uncommon, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Frost],
            Text = "Chill builds twice as fast. Frozen creatures take 35% more from everything.", Requires = new(Status: Chill),
            Mods = _ => [Inc(Stat.StatusDamage, 0.15, "syn:deep_chill")] },
        new() { Id = "static_charge", Name = "Static Charge", Icon = "static", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Storm, Tag.Chain],
            Text = "Hitting a shocked creature sends a spark leaping to two more.", Requires = new(Status: Shock),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Chain(2, 5, 0.5, Basis.Hit, School.Storm)], new() { TargetStatus = Shock }, icd: 0.08)] },
        new() { Id = "butchers_mark", Name = "Butcher's Mercy", Icon = "execute", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Physical],
            Text = "Critical strikes on bleeding creatures finish anything below 15% health.", Requires = new(Status: Bleed),
            Triggers = [T(TriggerEvent.Crit, [new Effect.Execute(0.15)], new() { TargetStatus = Bleed, HpBelow = 0.15 })] },
        new() { Id = "blood_scent", Name = "Blood Scent", Icon = "scent", Rarity = Rarity.Uncommon, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Physical],
            Text = "Killing something that bleeds quickens you: +8% speed and attack rate for 3 s, stacking three times.", Requires = new(Status: Bleed),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Buff("blood_scent", Stat.MoveSpeed, 0.08, ModKind.Inc, 3, 3), new Effect.Buff("blood_scent_cd", Stat.Cooldown, -0.06, ModKind.More, 3, 3)], new() { TargetStatus = Bleed })] },
        new() { Id = "hunters_mark", Name = "Hunter's Mark", Icon = "mark", Rarity = Rarity.Rare, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Ranged],
            Text = "Every 5 s the toughest thing near you is marked: it takes 30% more from everything, and its death eases your cooldowns.",
            Triggers = [T(TriggerEvent.Tick, [new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 12, Count: 1)], icd: 5),
                T(TriggerEvent.Kill, [new Effect.Cooldown(0.6, Effect.CooldownScope.All)], new() { TargetStatus = Mark })],
            DeeperText = ["The two toughest are marked.", "A marked death passes the mark to the toughest thing near it."],
            Deeper = [[T(TriggerEvent.Tick, [new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 12, Count: 2)], icd: 5)],
                [T(TriggerEvent.Kill, [new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 8, Count: 1)], new() { TargetStatus = Mark })]] },
        new() { Id = "plague_bearer", Name = "Plague Bearer", Icon = "plague", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Dot, Tag.Shadow, Tag.Nature],
            Text = "Poisoned creatures pass their poison to three neighbours when they die.", Requires = new(Status: Poison),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Spread(Poison, 3, 3, 3)], new() { TargetStatus = Poison })] },
        new() { Id = "sanctify", Name = "Sanctify", Icon = "sanctify", Rarity = Rarity.Uncommon, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Holy],
            Text = "Holy damage is 40% stronger, and the seared burn with it.", Requires = new(Status: Sear),
            Mods = _ => [Inc(Stat.DamageOf(School.Holy), 0.4, "syn:sanctify")] },
        new() { Id = "consecration", Name = "Consecration", Icon = "consecrate", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Holy, Tag.Zone],
            Text = "The seared leave hallowed ground where they fall.", Requires = new(Status: Sear),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Zone(1.8, 3, 8, Basis.Flat, School.Holy, "zone_holy")], new() { TargetStatus = Sear }, chance: 0.35)] },
        new() { Id = "soul_harvest", Name = "They Get Up", Icon = "risen", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Summon, Tag.Shadow],
            Text = "What dies near you sometimes gets up again, on your side, for 14 s (up to six at once).",
            Triggers = [T(TriggerEvent.Kill, [new Effect.Raise(Effect.RaiseKind.Ghoul, 14, 6)], chance: 0.06)] },
        new() { Id = "pack_leader", Name = "Pack Leader", Icon = "howl", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Summon, Tag.Nature],
            Text = "Your dash howls: every ally near you strikes 40% harder for 4 s, and a spirit wolf answers.", Requires = new(Tag: Tag.Summon),
            Triggers = [T(TriggerEvent.Dash, [new Effect.Buff("pack", Stat.SummonDamage, 0.4, ModKind.Inc, 4), new Effect.Raise(Effect.RaiseKind.SpiritWolf, 8, 3)], icd: 3)] },
        new() { Id = "momentum", Name = "The Long Road", Icon = "boot", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "While you are moving your weapons fire 25% faster. Never stand still.",
            Mods = r => r >= 2
                ? [new StatMod(Stat.Cooldown, ModKind.More, -0.2, "syn:momentum", ModWhen.Moving), new StatMod(Stat.MoveSpeed, ModKind.Inc, 0.1, "syn:momentum", ModWhen.Moving)]
                : [new StatMod(Stat.Cooldown, ModKind.More, -0.2, "syn:momentum", ModWhen.Moving)],
            DeeperText = ["And 10% faster on your feet while you keep them moving.", "Every dash fires every weapon at once (once in 3 s)."],
            Deeper = [[], [T(TriggerEvent.Dash, [new Effect.Cooldown(99, Effect.CooldownScope.All)], icd: 3)]] },
        new() { Id = "bloodthirst", Name = "Bloodthirst", Icon = "drain", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Heal],
            Text = "Every 25 kills restore 6% of your health. The horde is your medicine.",
            Triggers = [T(TriggerEvent.Kill, [new Effect.Heal(0.0024, Basis.MaxHp)], icd: 0)],
            DeeperText = ["A champion's death mends 8% of your health.", "Below a third of your health, every kill mends twice as much."],
            Deeper = [[T(TriggerEvent.Kill, [new Effect.Heal(0.08, Basis.MaxHp)], new() { Elite = true })],
                [T(TriggerEvent.Kill, [new Effect.Heal(0.0024, Basis.MaxHp)], new() { SelfHpBelow = 0.34 })]] },
        new() { Id = "arcane_overflow", Name = "Ember Flood", Icon = "arcane", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Spell],
            Text = "Each ember stone you gather has an 8% chance to fire every weapon at once.",
            Triggers = [T(TriggerEvent.Ember, [new Effect.Cooldown(99, Effect.CooldownScope.All)], chance: 0.08, icd: 0.4)],
            DeeperText = ["And a 10% chance to hand back a dash.", "And a 4% chance to bring your art back at once."],
            Deeper = [[T(TriggerEvent.Ember, [new Effect.Cooldown(Abilities.Dash.Recharge, Effect.CooldownScope.Dash)], chance: 0.1, icd: 0.4)],
                [T(TriggerEvent.Ember, [new Effect.Cooldown(99, Effect.CooldownScope.Ability)], chance: 0.04, icd: 1)]] },
        new() { Id = "glass_cannon", Name = "Burn Bright", Icon = "flame", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "45% more damage, and 35% less health. Burn bright, burn short.",
            Mods = r => r >= 2
                ? [More(Stat.Damage, 0.45, "syn:glass"), More(Stat.MaxHealth, -0.35, "syn:glass"), More(Stat.CritDamage, 0.3, "syn:glass")]
                : [More(Stat.Damage, 0.45, "syn:glass"), More(Stat.MaxHealth, -0.35, "syn:glass")],
            DeeperText = ["Critical strikes land 30% harder.", "A perfect dodge mends 8% of your health."],
            Deeper = [[], [T(TriggerEvent.PerfectDodge, [new Effect.Heal(0.08, Basis.MaxHp)])]] },

        /* ---------------------------------------- blessings to start with -- */
        new() { Id = "duelists_grace", Name = "Duelist's Grace", Icon = "feint", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "A perfect dodge fires every weapon at once, and its sure strikes last a second longer.",
            Detail = "Slip a telegraphed blow in the first moments of a dash.",
            Triggers = [T(TriggerEvent.PerfectDodge, [new Effect.Cooldown(99, Effect.CooldownScope.All)])],
            DeeperText = ["The moment to slip a blow is half again as long.", "A perfect dodge takes 3 s off your art's wait."],
            Deeper = [[], [T(TriggerEvent.PerfectDodge, [new Effect.Cooldown(3, Effect.CooldownScope.Ability)])]] },
        new() { Id = "restless_hands", Name = "Restless Hands", Icon = "hand", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "Your art is ready 25% sooner, and every use of it hands back a dash.",
            Mods = _ => [More(Stat.AbilityCooldown, -0.25, "syn:restless_hands")],
            Triggers = [T(TriggerEvent.Ability, [new Effect.Cooldown(Abilities.Dash.Recharge, Effect.CooldownScope.Dash)])],
            DeeperText = ["Every use of your art fires every weapon at once.", "Every kill takes a tenth of a second off your art's wait."],
            Deeper = [[T(TriggerEvent.Ability, [new Effect.Cooldown(99, Effect.CooldownScope.All)])],
                [T(TriggerEvent.Kill, [new Effect.Cooldown(0.1, Effect.CooldownScope.Ability)])]] },
        new() { Id = "cinderwake", Name = "Cinderwake", Icon = "embers", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Fire, Tag.Zone],
            Text = "Your dash leaves a line of fire behind it, and comes back a fifth sooner.",
            Mods = _ => [More(Stat.DashCooldown, -0.2, "syn:cinderwake")],
            DeeperText = ["The fire is wider and burns longer.", "What stands in it is slowed, and set burning."] },
        new() { Id = "iron_vow", Name = "Iron Vow", Icon = "aegis", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "A barrier of 12% of your health, back whenever you go 5 s unstruck.",
            DeeperText = ["18% of your health, back after 4 s.", "24%, and when it breaks it throws back everything near you."] },
        // The wards and answers the paths were missing: a ward for fire and for
        // storm, an answer to champions for the green and for the host.
        new() { Id = "from_the_ashes", Name = "Cold, Then Not", Icon = "embers", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Fire],
            Text = "Once a night, a blow that would end you does not. You go cold; then the ember catches, and you rise with half your health while everything near you burns.",
            DeeperText = ["You rise whole, and the fire reaches twice as far.", "Twice a night."] },
        new() { Id = "grounding", Name = "Grounding", Icon = "static", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Storm, Tag.Chain],
            Text = "A fifth of every blow that reaches you is turned aside as lightning, which leaps from you to three creatures near you.",
            Triggers = [T(TriggerEvent.Hurt, [new Effect.Chain(3, 7, 4, Basis.Hit, School.Storm)], icd: 0.3)],
            DeeperText = ["A third of every blow.", "The lightning leaps to six, and shocks all it strikes."],
            Deeper = [[], [T(TriggerEvent.Hurt, [new Effect.Chain(3, 7, 4, Basis.Hit, School.Storm), new Effect.Apply(P(Shock, 1, 1, 3), OnHit: false, Radius: 7, Count: 6)], icd: 0.3)]] },
        new() { Id = "rootbind", Name = "Rootbind", Icon = "thorn", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Nature],
            Text = "Every 6 s roots seize the toughest thing near you: they hold it fast for a second, and while they hold it, it takes 40% more from everything.",
            Triggers = [T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 1), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 1)], icd: 6)],
            DeeperText = ["The two toughest are seized.", "The roots come every 4 s."],
            Deeper = [[T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 2), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 2)], icd: 6)],
                [T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 2), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 2)], icd: 12)]] },
        new() { Id = "go_for_the_throat", Name = "Go for the Throat", Icon = "howl", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Summon],
            Text = "What fights for you goes for the toughest thing near you, and strikes champions 40% harder.",
            Mods = r => r >= 2 ? [Inc(Stat.SummonHaste, 0.2, "syn:go_for_the_throat")] : [],
            DeeperText = ["They strike 20% faster.", "Each champion that falls calls up a spirit wolf that stays the night."],
            Deeper = [[], [T(TriggerEvent.Kill, [new Effect.Raise(Effect.RaiseKind.SpiritWolf, 0, 6)], new() { Elite = true })]] },
        new() { Id = "ember_tithe", Name = "Ember Tithe", Icon = "coin", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,
            Text = "25% more ember, and ember stones come to you from twice as far.",
            Mods = r => [Inc(Stat.XpGain, r >= 2 ? 0.45 : 0.25, "syn:ember_tithe"), Inc(Stat.PickupRadius, 1, "syn:ember_tithe")],
            DeeperText = ["45% more ember.", "Every ember level mends 10% of your health."],
            Deeper = [[], [T(TriggerEvent.LevelUp, [new Effect.Heal(0.1, Basis.MaxHp)])]] },
        new() { Id = "stormborn", Name = "Stormborn", Icon = "bolt", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Storm],
            Text = "Every 3 s lightning finds something near you.",
            Triggers = [T(TriggerEvent.Tick, [new Effect.Strike(1, 1.5, 24, Basis.Flat, School.Storm, 9)], icd: 3)],
            DeeperText = ["Half again as often.", "Twice as often as it began."],
            Deeper = [[T(TriggerEvent.Tick, [new Effect.Strike(1, 1.5, 24, Basis.Flat, School.Storm, 9)], icd: 6)],
                [T(TriggerEvent.Tick, [new Effect.Strike(1, 1.5, 24, Basis.Flat, School.Storm, 9)], icd: 6)]] },
        new() { Id = "storm_caller", Name = "Storm Caller", Icon = "bolt", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Storm],
            Text = "Every 16th kill calls lightning down on the thickest knot of creatures near you.", Requires = new(Tag: Tag.Storm),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Strike(3, 1.6, 30, Basis.Flat, School.Storm, 6)], chance: 1.0 / 16)] },
        new() { Id = "fracture", Name = "Fracture", Icon = "shatter", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Frost, Tag.Fire],
            Text = "Fire on the frozen is a violent thing: burning a frozen creature makes it explode.", Requires = new(All: [new(Status: Chill), new(Status: Burn)]),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.6, 1.2, Basis.Hit, School.Frost)], new() { School = School.Fire, TargetStatus = Frozen }, icd: 0.05)] },

        /* --------------------------------- duos: two families, one rule -- */
        new() { Id = "overload", Name = "Overload", Icon = "bolt", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Storm, Tag.Fire, Tag.Explosion],
            Text = "Lightning on the burning is a blast: storm damage to a burning creature makes it explode.",
            Requires = new(All: [new(Any: [new(Status: Shock), new(Tag: Tag.Storm)]), new(Status: Burn)]),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.2, 0.9, Basis.Hit, School.Fire)], new() { School = School.Storm, TargetStatus = Burn }, icd: 0.08)] },
        new() { Id = "frostbite", Name = "Frostbite", Icon = "frost", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Frost, Tag.Physical, Tag.Dot],
            Text = "The frozen bleed out: a frozen creature's bleeding hurts three times as much.",
            Requires = new(All: [new(Status: Chill), new(Status: Bleed)]) },

        /* ------------------------------ more for the families that had few -- */
        new() { Id = "contagion", Name = "Contagion", Icon = "plague", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Dot, Tag.Nature],
            Text = "Poison spreads on its own: each second a poisoned creature passes a dose to the nearest of its neighbours.", Requires = new(Status: Poison) },
        new() { Id = "deaths_due", Name = "Death's Due", Icon = "mark", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Arcane, Tag.Explosion],
            Text = "A marked creature that dies bursts for a tenth of its health, and the toughest thing near it is marked.", Requires = new(Status: Mark),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.2, 0.1, Basis.MaxHp, School.Arcane), new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 6, Count: 1)],
                new() { TargetStatus = Mark }, icd: 0.2)] },
    }.ToDictionary(b => b.Id);

    /// <summary>The order the boons were written in (the draft walks them in it).</summary>
    public static readonly string[] Order = All.Keys.ToArray();

    public static BoonDef? Find(string id) => All.TryGetValue(id, out var d) ? d : null;
}
