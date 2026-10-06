G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"
p = G + r"\src\Game\Game.cs"
s = open(p, encoding="utf-8").read()
a = '''        hud.SetBruise(scene.Bruise);
'''
b = '''        hud.SetBruise(scene.Bruise);
        // The boss's script, for the looks that read its state (Grimtunnel under the ground).
        scene.Fx.Boss = zone switch { ArenaRun ar => ar.BossScript, MapRun mr => mr.BossScript, StoryNight sn => sn.BossScript, _ => null };
'''
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
p = G + r"\src\Fx\BattleFx.Dig.cs"
s = open(p, encoding="utf-8").read()
a = '''    void StepDig(float dt)
    {
'''
b = '''    void StepDig(float dt)
    {
        CrowdView.Under ??= e => Boss is GrimtunnelStory { Under: true } gu && gu.E == e;
'''
assert a in s
s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
