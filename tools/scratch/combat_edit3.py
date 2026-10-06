import re
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:60])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Content\Enemies.cs', [
('''        /* ---------------------------------------------------- your own, raised -- */''',
'''        /* ------------------------------------- what rules a people, at the half hour -- */
        // The arena's bosses (Play/Bosses/ArenaBosses.cs): their people's champion's body made
        // half again as big, so the thing the fight is about is the thing the eye finds; health
        // as the champion's, multiplied by the boss contract (ArenaBoss.HealthMul).
        new() { Id = "boss_pack", Name = "The Pack-Mother", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 2.15,
            Health = 520, Speed = 5.4, Damage = 18, Radius = 1.2, Mass = 14, Xp = 55, Resists = Beast, Behavior = Behavior.Pack,
            Lunge = new(9, 4.8, 0.6, 0.45, 19),
            Elite = true, Loot = "alpha", AttackEvery = 0.8,
            Note = "She does not chase. She howls, the Pack wheels round behind you, and she runs the gap they leave. Go through the wolves, never the gap. Fire stops her howling." },
        new() { Id = "boss_dead", Name = "The Barrow Lord", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior_elite", Scale = 2.05,
            // Not the dead's frost and shadow: every school can lay him down in time; holy twice as fast.
            Health = 420, Speed = 2.6, Damage = 22, Radius = 1.1, Mass = 14, Xp = 40, Gold = 12, Resists = new() { [School.Holy] = -0.5, [School.Fire] = -0.15 }, Behavior = Behavior.Chase,
            Lunge = new(8, 5.5, 0.75, 0.5, 17),
            Elite = true, Loot = "elite", AttackEvery = 1.1,
            Note = "A legion's officer who heard the order to stand and never heard another. He fights in walls of his dead. Put down, he gets up again, unless someone stands over him until he stays down." },
        new() { Id = "boss_lamplings", Name = "The Ganger", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 2.2,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 0.95, Mass = 12, Xp = 40, Gold = 12, Behavior = Behavior.Chase, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.2 },
            Ranged = new() { Range = 11, Cooldown = 4.5, Speed = 8, School = School.Fire, Lob = true, Zone = new(2.2, 3.5, 0.4), Art = "firepot" },
            Elite = true, AttackEvery = 1.2,
            Note = "Foreman of a Dig gang, the biggest of them and the loudest. Where it stands the ground is not to be trusted: it goes under, comes up under you, and leaves holes. Frost catches it in the dirt." },
        new() { Id = "boss_kerchiefs", Name = "The Red Hand", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.9,
            Health = 480, Speed = 3.4, Damage = 22, Radius = 1.1, Mass = 14, Xp = 45, Gold = 20, Behavior = Behavior.Chase,
            Lunge = new(8.5, 5.0, 0.7, 0.45, 18),
            Elite = true, Loot = "elite", AttackEvery = 1.0,
            Note = "He takes a toll: your best weapon, for a while, and a runner to carry it off. Catch the runner. Lightning makes him drop it." },

        /* ---------------------------------------------------- your own, raised -- */'''),
('''        new() { Id = "grimtunnel_roused", Name = "Grimtunnel, Roused", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 2.1,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 0.8, Mass = 8,''',
'''        new() { Id = "grimtunnel_roused", Name = "Grimtunnel, Roused", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 2.4,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 1.0, Mass = 14,'''),
])

edit(r'logic\Maps\MapOffers.cs', [
('''"wolf_alpha", "The Pack-Mother", "Alpha of the Deep Wood",''', '''"boss_pack", "The Pack-Mother", "Alpha of the Deep Wood",'''),
('''"barrow_knight", "The Barrow Lord", "Who Would Not Lie Down",''', '''"boss_dead", "The Barrow Lord", "Who Would Not Lie Down",'''),
# The story's own (docs/STORY_BIBLE.md): a table arena fields a foreman of the Dig, never Grimtunnel or his name.
('''"grimtunnel_roused", "Grimtunnel, Roused", "Boss of the Deep Dig",''', '''"boss_lamplings", "The Ganger", "Foreman of the Deep Dig",'''),
('''"enforcer", "The Red Hand", "Warlord of the Ravine",''', '''"boss_kerchiefs", "The Red Hand", "Warlord of the Ravine",'''),
])

edit(r'logic\Play\Zones\Verge.cs', [
('''Story("hollow_by_night", "The Hollow by Night", "pack", 311, "wolf_alpha", "Greymuzzle",''', '''Story("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle",'''),
('''Story("roost_raid", "Raid on the Roost", "kerchiefs", 523, "enforcer", "Redcowl",''', '''Story("roost_raid", "Raid on the Roost", "kerchiefs", 523, "boss_kerchiefs", "Redcowl",'''),
('''Story("vault_opened", "Behind the Sealed Door", "dead", 947, "barrow_knight", "The Barrow Lord",''', '''Story("vault_opened", "Behind the Sealed Door", "dead", 947, "boss_dead", "The Barrow Lord",'''),
])

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''            "wolf_alpha" => "A howl from the edge of the wood; the wolves lift their heads.",
            "barrow_knight" => "A drum, slow, under everything; the dead turn to face it.",
            "grimtunnel_roused" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "enforcer" => "A whistle, three notes, and an answering whistle.",''',
'''            "boss_pack" => "A howl from the edge of the wood; the wolves lift their heads.",
            "boss_dead" => "A drum, slow, under everything; the dead turn to face it.",
            "grimtunnel_roused" or "boss_lamplings" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "boss_kerchiefs" => "A whistle, three notes, and an answering whistle.",'''),
])

edit(r'logic\Play\Bosses\ArenaBosses.cs', [
('''        "wolf_alpha" => new PackMother(arena),
        "barrow_knight" => new BarrowLord(arena),
        "grimtunnel_roused" => new Grimtunnel(arena),
        "enforcer" => new RedHand(arena),''',
'''        "boss_pack" => new PackMother(arena),
        "boss_dead" => new BarrowLord(arena),
        "grimtunnel_roused" => new Grimtunnel(arena),
        "boss_lamplings" => new Grimtunnel(arena, ganger: true),
        "boss_kerchiefs" => new RedHand(arena),'''),
])
print("ok")
