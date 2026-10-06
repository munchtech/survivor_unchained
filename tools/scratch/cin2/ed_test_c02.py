import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"
p = os.path.join(G, r"tests\PrologueTests.cs")
s = open(p, encoding="utf-8").read()
old = '''    [Fact]
    public void Falling_here_is_forgiven()'''
new = '''    [Fact]
    public void At_the_ford_C02_plays_and_leaves_the_warden_an_arms_length_off_facing_her()
    {
        // With a screen, the cinematic replaces the captions and the barks: the zone
        // waits, hides its own Warden while the cinematic's is on, and its last cue
        // starts the fight with him where it left him.
        var s = Make();
        s.Host.Plays = id => id == "c02";
        var ford = s.Meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, 2.5, -31);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        var (id, done, _) = Assert.Single(s.Host.Cines);
        Assert.Equal("c02", id);
        Assert.Null(s.Host.Held);
        Run(s, 10);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        Assert.DoesNotContain(s.B.Enemies.Living(), e => e.Tag == "warden");
        s.Zone.CineEvent("warden_cine");
        s.Zone.CineEvent("warden_up");
        done!();
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        var w = s.B.Enemies.Living().Single(e => e.Tag == "warden");
        var (x, _, z, _) = SurvivorUnchained.Cinema.CineFile.Load("c02").Mark("warden_end");
        Assert.Equal((x, z), (w.X, w.Z));
        Assert.True(Math.Cos(w.Facing - Math.Atan2(-31 - z, 2.5 - x)) > 0.99);
        Assert.Equal("Put out the lamps", s.Host.Tracked.Single().Steps[1].Text);
    }

    [Fact]
    public void Falling_here_is_forgiven()'''
assert s.count(old) == 1
s = s.replace(old, new)
if "using System;" not in s:
    s = "using System;\n" + s
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
