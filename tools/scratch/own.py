import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')
p = 'logic/Sim/LevelUp.cs'
s = open(p, encoding='utf-8').read()
old = """    /// <summary>Skill drafts dealt this arena (a reroll is the same draft).</summary>
    public int SkillDrafts;
}"""
new = """    /// <summary>Skill drafts dealt this arena (a reroll is the same draft).</summary>
    public int SkillDrafts;
    /// <summary>The calling's own great blessing has been in a hand this night.</summary>
    public bool OwnShown;
}"""
assert s.count(old) == 1
s = s.replace(old, new)
old = """            for (int i = 0; i < count; i++)
                if ((TakeFrom(b, pool, order[System.Math.Min(i, order.Length - 1)]) ?? TakeFrom(b, pool)) is { } c) offers.Add(c.O);
            return Shown(b, offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b)));"""
new = """            // The calling's own comes once a night: as Dusk's power half the time, else at Midnight.
            var own = pool.FirstOrDefault(c => Boons.All[c.O.Id].Calling != null && c.O.From == 0);
            bool ownNow = own != null && !mem.OwnShown && (mem.Greats >= 1 || b.Rng.Next() < 0.5);
            if (ownNow) { pool.Remove(own!); mem.OwnShown = true; order = [order[0], order[2], null]; }
            for (int i = 0; i < count - (ownNow ? 1 : 0); i++)
                if ((TakeFrom(b, pool, order[System.Math.Min(i, order.Length - 1)]) ?? TakeFrom(b, pool)) is { } c) offers.Add(c.O);
            if (ownNow) offers.Insert(System.Math.Min(1, offers.Count), own!.O);
            return Shown(b, offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b)));"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

# The test: once a night, whatever the seed.
p = 'tests/BlessingTests.cs'
s = open(p, encoding='utf-8').read()
old = """            Assert.True(seen, $"{calling} never saw its own");
        }
    }"""
new = """            Assert.True(seen, $"{calling} never saw its own");
        }
        // Once a night: at Dusk or, failing that, at Midnight.
        for (uint seed = 1; seed <= 60; seed++)
        {
            var b = BattleTests.Arena(seed);
            b.Calling = "reaver";
            b.GreatOwed = 1;
            var dusk = LevelUp.Draft(b);
            bool atDusk = dusk.Any(o => o.Id == "blood_up");
            LevelUp.Choose(b, dusk.First(o => o.Id != "blood_up"));
            b.GreatOwed = 1;
            var midnight = LevelUp.Draft(b);
            Assert.True(atDusk ^ midnight.Any(o => o.Id == "blood_up"), $"seed {seed}");
        }
    }"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
