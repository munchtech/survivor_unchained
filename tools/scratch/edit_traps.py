import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Discoveries.cs', [
("""        new() { Id = "thunderpalm", Name = "Thunderpalm", Weapons = ("iron_palms", "arcweb"),""",
"""        new() { Id = "thunderpalm", Name = "Grounded Lightning", Weapons = ("iron_palms", "arcweb"),"""),
("""        new() { Id = "hailwheel", Name = "Hailwheel", Weapons = ("gale_chakram", "rimeshard"),""",
"""        new() { Id = "hailwheel", Name = "Rimed Edge", Weapons = ("gale_chakram", "rimeshard"),"""),
("""        new() { Id = "butchery", Name = "Butchery", Weapons = ("cleaver", "knifestorm"),""",
"""        new() { Id = "steam_burst", Name = "Steam Burst", Weapons = ("firepot", "hoarfrost"),
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
        new() { Id = "butchery", Name = "Butchery", Weapons = ("cleaver", "knifestorm"),"""),
])

edit('logic/Rpg/SkillBook.cs', [
("""        var favours = Callings.Archetype(ch.Archetype).Favours;
        var pick = ch.Discovered.Where(id => CanLearn(ch, id) && Meets(ch, id))
            .OrderByDescending(id => Weapons.All[id].Tags.Count(favours.Contains)).ThenBy(id => id).FirstOrDefault();
        if (pick == null || Weapons.All[pick].Tags.Count(favours.Contains) == 0) return null;""",
"""        var favours = Callings.Archetype(ch.Archetype).Favours;
        // Its own paths first, then its kind of skill.
        double Own(string id) => (Paths.All.Any(p => p.Callings.Contains(ch.Archetype) && p.Weapons.Contains(id)) ? 2 : 0) + Weapons.All[id].Tags.Count(favours.Contains);
        var pick = ch.Discovered.Where(id => CanLearn(ch, id) && Meets(ch, id))
            .OrderByDescending(Own).ThenBy(id => id).FirstOrDefault();
        if (pick == null || Own(pick) == 0) return null;"""),
])

# Traps: a passive that only touches some kinds of skill, offered to a build with none of them.
edit('logic/Sim/LevelUp.cs', [
("""            double wgt = Weight(d.Rarity) * 0.75 * Affinity(d.Tags, tags) * Again(o);
            if (r > 0) wgt *= 1.35;""", """            double wgt = Weight(d.Rarity) * 0.75 * Affinity(d.Tags, tags) * Again(o);
            if (r > 0) wgt *= 1.35;
            // A passive for kinds of skill the build has none of is a trap: far
            // less likely, and the card says so.
            if (Affects.TryGetValue(d.Id, out var kinds) && !b.Weapons.Any(w => kinds.Any(w.Tags.Contains)) && evolves.Count == 0)
            {
                wgt *= 0.3;
                o.Why.Add("Little use to what you carry now");
            }"""),
("""    /// <summary>Statuses the build applies, from weapons, evolutions and triggers.</summary>""",
"""    /// <summary>The passives that only touch some kinds of combat skill, and
    /// which: offered to a build with none of them, they are a trap.</summary>
    public static readonly Dictionary<string, Tag[]> Affects = new()
    {
        ["duplicity"] = [Tag.Projectile, Tag.Orbit, Tag.Chain, Tag.Melee, Tag.Summon, Tag.Storm],
        ["velocity"] = [Tag.Projectile],
        ["emberblood"] = [Tag.Fire],
        ["conduit"] = [Tag.Storm],
        ["venom"] = [Tag.Dot, Tag.Steel],
        ["kinship"] = [Tag.Summon],
        ["perennial"] = [Tag.Zone, Tag.Orbit, Tag.Summon, Tag.Explosion],
        ["serration"] = [Tag.Physical, Tag.Steel],
    };

    /// <summary>Statuses the build applies, from weapons, evolutions and triggers.</summary>"""),
])
print('ok')
