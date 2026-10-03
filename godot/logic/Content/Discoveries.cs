using System;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* Discoveries: weapon pairs that quietly do more together. Nobody tells you
 * these exist. Carry both and the codex remembers the pairing forever, with
 * a cryptic line for the ones not yet found. */

public sealed class Discovery
{
    public string Id = "", Name = "", Description = "", Hint = "";
    public (string A, string B) Weapons;
    public Action<WeaponInst, WeaponInst, Battle> Apply = (_, _, _) => { };
}

public static class Discoveries
{
    static TriggerDef T(TriggerEvent on, Effect[] effects, TriggerCond? when = null, double? chance = null, double? icd = null) =>
        new() { On = on, Effects = effects, When = when, Chance = chance, Icd = icd };

    public static readonly Discovery[] All =
    [
        new() { Id = "frostfire", Name = "Frostfire Bolt", Weapons = ("rimeshard", "cinderfall"),
            Description = "Cinders chill what survives them, both bolts hit 10% harder, and fire on the frozen is violent.",
            Hint = "When frost meets flame, something ancient stirs...",
            Apply = (a, b, battle) =>
            {
                a.Mods.Damage *= 1.1; b.Mods.Damage *= 1.1;
                battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(2.2, 0.8, Basis.Hit, School.Frost)], new() { School = School.Fire, TargetStatus = StatusKind.Frozen }, icd: 0.1), "disc:frostfire");
            } },
        new() { Id = "shadowflame", Name = "Shadowflame", Weapons = ("umbral_bolt", "cinderfall"),
            Description = "Umbral bolts detonate on impact, scorching everything nearby.",
            Hint = "Shadow and flame were ever entwined.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(1.4, 0.3, Basis.Hit, School.Fire)], new() { Weapon = a.Id }, icd: 0.15), "disc:shadowflame") },
        new() { Id = "deadly_brew", Name = "Deadly Brew", Weapons = ("knifestorm", "rimeshard"),
            Description = "Every thrown knife is coated in a numbing venom that chills its victim.",
            Hint = "A rogue with access to the alchemist's icebox is a dangerous thing.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Apply(new StatusPayload(StatusKind.Chill, 1, 1, 2), OnHit: true)], new() { Weapon = a.Id }), "disc:deadly_brew") },
        new() { Id = "tempest_pact", Name = "Tempest Pact", Weapons = ("axe_gyre", "arcweb"),
            Description = "Axe Gyre blades sometimes call the storm, loosing lightning on those they strike.",
            Hint = "Blessed blades may yet call the storm...",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Chain(3, 5, 0.8, Basis.Hit, School.Storm)], new() { Weapon = a.Id }, chance: 0.15), "disc:tempest_pact") },
        new() { Id = "radiant_gyre", Name = "Radiant Gyre", Weapons = ("axe_gyre", "dawnpulse"),
            Description = "Every spin of the Axe Gyre begins with a pulse of holy Light.",
            Hint = "Steel spun in faith becomes something more.",
            Apply = (a, _, battle) =>
            {
                a.Mods.Damage *= 1.1;
                battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Nova(3, 14, Basis.Flat, School.Holy, 0.4)], new() { Weapon = a.Id }, icd: 3.5), "disc:radiant_gyre");
            } },
        new() { Id = "truestrike", Name = "Truestrike", Weapons = ("volley", "seeking_motes"),
            Description = "Enchanted arrows curve in flight to seek their prey.",
            Hint = "The finest rangers fletch their arrows with a whisper of magic.",
            Apply = (a, _, _) => { a.Mods.Damage *= 1.08; a.Mods.Homing += 3; } },
        new() { Id = "celestial", Name = "Celestial Alignment", Weapons = ("moonbrand", "dawnpulse"),
            Description = "Sun and moon align: an extra moonbeam, and wider rings of Light.",
            Hint = "What happens when the moon rises on the light of dawn?",
            Apply = (a, b, _) => { a.Mods.Projectiles += 1; b.Mods.Area *= 1.12; } },
        new() { Id = "verdict", Name = "Verdict", Weapons = ("judgement_disc", "hallowed_ring"),
            Description = "The shield judges from hallowed ground: +1 ricochet and 10% more damage.",
            Hint = "A shield thrown from sacred ground carries a verdict.",
            Apply = (a, _, _) => { a.Mods.Damage *= 1.1; a.Mods.Pierce += 1; } },
        new() { Id = "thunderpalm", Name = "Grounded Lightning", Weapons = ("iron_palms", "arcweb"),
            Description = "Iron Palms carry the storm: some strikes loose lightning from what they hit.",
            Hint = "An open hand can hold lightning, if it is quick enough.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Chain(3, 5, 0.7, Basis.Hit, School.Storm)], new() { Weapon = a.Id }, chance: 0.18), "disc:thunderpalm") },
        new() { Id = "hailwheel", Name = "Rimed Edge", Weapons = ("gale_chakram", "rimeshard"),
            Description = "The chakram rimes whatever it cuts, and both hit 8% harder.",
            Hint = "A spinning edge through a hailstorm comes back cold.",
            Apply = (a, b, battle) =>
            {
                a.Mods.Damage *= 1.08; b.Mods.Damage *= 1.08;
                battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Apply(new StatusPayload(StatusKind.Chill, 1, 1, 2), OnHit: true)], new() { Weapon = a.Id }), "disc:hailwheel");
            } },
        new() { Id = "razor_wind", Name = "Razor Wind", Weapons = ("gale_chakram", "knifestorm"),
            Description = "One more ring in every throw, cutting 10% deeper.",
            Hint = "Every blade that flies wants a blade beside it.",
            Apply = (a, _, _) => { a.Mods.Projectiles += 1; a.Mods.Damage *= 1.1; } },
        new() { Id = "rotbloom", Name = "Rotbloom", Weapons = ("thornbloom", "blightfield"),
            Description = "Rot feeds the thicket: both fields hit 12% harder.",
            Hint = "Nothing grows as well as it does on something dead.",
            Apply = (a, b, _) => { a.Mods.Damage *= 1.12; b.Mods.Damage *= 1.12; } },
        new() { Id = "oath_and_arc", Name = "Oath of the Storm", Weapons = ("oathblade", "arcweb"),
            Description = "The blade carries the storm: a swing that finds a shocked creature calls lightning onto it.",
            Hint = "A sworn blade will carry whatever you ask it to.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Strike(1, 1.4, 1.2, Basis.Hit, School.Storm, 2)], new() { Weapon = a.Id, TargetStatus = StatusKind.Shock }, icd: 0.2), "disc:oath_arc") },
        new() { Id = "steam_burst", Name = "Steam Burst", Weapons = ("firepot", "hoarfrost"),
            Description = "A pot that breaks among the chilled bursts in scalding steam: half again as wide.",
            Hint = "What happens when the pot breaks on frozen ground?",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(1.6, 0.5, Basis.Hit, School.Fire)], new() { Weapon = a.Id, TargetStatus = StatusKind.Chill }, icd: 0.2), "disc:steam_burst") },
        new() { Id = "gathering_storm", Name = "Gathering Storm", Weapons = ("thunderhead", "arcweb"),
            Description = "The cloud's bolts on the shocked leap on to the next of them.",
            Hint = "A storm grows on what it has already struck.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Chain(2, 5, 0.4, Basis.Hit, School.Storm)], new() { Weapon = a.Id, TargetStatus = StatusKind.Shock }, icd: 0.1), "disc:gathering_storm") },
        new() { Id = "bone_and_bramble", Name = "Bone and Bramble", Weapons = ("gravecall", "thornbloom"),
            Description = "The risen walk the thorns unhurt, and strike a fifth harder for the ground they stand on.",
            Hint = "The dead have nothing left for thorns to catch on.",
            Apply = (a, _, _) => a.Mods.Damage *= 1.2 },
        new() { Id = "butchery", Name = "Butchery", Weapons = ("cleaver", "knifestorm"),
            Description = "Wounds opened by knives are torn wider by the cleaver: 40% more against the bleeding.",
            Hint = "Two blades, one purpose.",
            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(0.1, 0.4, Basis.Hit, School.Physical)], new() { Weapon = a.Id, TargetStatus = StatusKind.Bleed }), "disc:butchery") },
    ];
}
