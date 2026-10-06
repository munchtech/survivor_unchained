import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"
FILES = {
os.path.join(ROOT, r"balance\Harness\Probe.cs"): [
("""        var kinds = people.Arena.Where(h => h.From <= minute).Select(h => h.Def).Where(d => Enemies.Get(d).Ranged == null).ToList();""",
"""        // The yardstick is the people's rank and file as the day knows them (Denizens.Horde), not
        // the arena's growing roster: a new kind of splitter or guard would otherwise move every
        // path's number with it, and the bounds would measure the roster, not the paths.
        var kinds = people.Horde.Select(h => h.Def).Where(d => Enemies.Get(d).Ranged == null && people.Arena.Any(a => a.Def == d && a.From <= minute)).ToList();"""),
],
os.path.join(ROOT, r"tests\ArenaTests.cs"): [
("""        var s = Make(Spec("dead"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 5.4 * 60;""",
"""        var s = Make(Spec("dead"));
        s.B.Player.Iframes = 1e9;
        // (Nothing of hers to kill them: the count is of what rises, not of what she mows.)
        foreach (var w in s.B.Weapons.ToList()) s.B.RemoveWeapon(w.Id);
        s.B.Time = 5.4 * 60;"""),
],
}
