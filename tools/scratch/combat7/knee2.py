W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\tests"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

r = W + r"\RoostTests.cs"
sub(r, """            var choice = n.Zone.Interactables.FirstOrDefault(i => i.Id == "story:finish");
            choice?.Act();""", """            if (n.Zone.Choice != null) n.Zone.Answer("finish");""")
sub(r, """    /// <summary>At his knee, the owner's choice: spare him, or finish it. The outcome is the one she chose.</summary>""",
"""    /// <summary>At his knee, the owner's choice: spare him, or finish it. It is put to her wherever she stands,
    /// named; the outcome is the one she chose.</summary>""")
sub(r, """        }, until: () => n.Zone.Interactables.Any(i => i.Id == "story:let_go"));
        Assert.Equal("Spare him", n.Zone.Interactables.First(i => i.Id == "story:let_go").Verb);
        n.Zone.Interactables.First(i => i.Id == (spare ? "story:let_go" : "story:finish")).Act();
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(spare ? "spared" : "dead", n.J.World.Fact("redcowl").Str);
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));""", """        }, until: () => n.Zone.Choice != null);
        var c = n.Zone.Choice!;
        Assert.Equal("Redcowl", c.Who);
        Assert.Equal("Spare him, or finish it", c.Title);
        Assert.Equal(["Spare him", "Finish it"], c.Answers.Select(a => a.Verb));
        // Nothing near him to walk to: the choice is answered from anywhere.
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));
        // Left waiting, it waits, and his lot keep back from her.
        Step(n, 20);
        Assert.Same(c, n.Zone.Choice);
        Assert.False(n.Zone.Won);
        Assert.DoesNotContain(n.B.Enemies.Living(), e => !e.Scripted && n.B.HostileToPlayer(e) && !e.Status.Has(StatusKind.Fear) && e.Def.Id.StartsWith("kerchief"));
        n.Zone.Answer(spare ? "let_go" : "finish");
        Assert.Null(n.Zone.Choice);
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(spare ? "spared" : "dead", n.J.World.Fact("redcowl").Str);""")

s = W + r"\StoryNightTests.cs"
sub(s, """        }, until: () => n.Zone.Interactables.Any(i => i.Id == "story:let_go"));
        var choice = n.Zone.Interactables.First(i => i.Id == (letGo ? "story:let_go" : "story:finish"));
        Assert.Equal("Let him go", n.Zone.Interactables.First(i => i.Id == "story:let_go").Verb);
        choice.Act();
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(letGo ? "spared" : "dead", n.J.World.Fact("greymuzzle").Str);
        Assert.Equal(!letGo, n.J.World.Fact("promise.broken").Truthy);
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));""", """        }, until: () => n.Zone.Choice != null);
        var c = n.Zone.Choice!;
        Assert.Equal("Greymuzzle", c.Who);
        Assert.Equal("Let him go, or finish it", c.Title);
        Assert.Equal(["let_go", "finish"], c.Answers.Select(a => a.Id));
        Assert.Equal("Let him go", c.Answers[0].Verb);
        n.Zone.Answer("nonsense");
        Assert.Same(c, n.Zone.Choice);
        n.Zone.Answer(letGo ? "let_go" : "finish");
        Assert.Null(n.Zone.Choice);
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(letGo ? "spared" : "dead", n.J.World.Fact("greymuzzle").Str);
        Assert.Equal(!letGo, n.J.World.Fact("promise.broken").Truthy);
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));""")
print("ok")
