W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/EncounterTests.cs": [
        ("""public class EncounterTests
{""", """public class EncounterTests
{
    /// <summary>A crossbow kneels to shoot (RangedSpec.Aim; the animation lead's kneel): planted for its
    /// aim, the wind-up shown from its start, and its line fixed as it kneels, so a step off the line
    /// in time is a dodge, as a lunge's wind-up is.</summary>
    [Fact]
    public void A_crossbow_kneels_and_aims_before_it_looses_and_its_line_is_fixed()
    {
        var b = BattleTests.Arena(7);
        var p = b.Player;
        var x = b.SpawnEnemy("levy_crossbow", p.X + 7, p.Z, new Battle.SpawnOpts { Level = 1 })!;
        x.RangedT = 0;
        double aim = x.Def.Ranged!.Aim;
        Assert.InRange(aim, 0.4, 0.8);
        bool knelt = false;
        for (int i = 0; i < 60 && !knelt; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            knelt = x.State == EnemyState.Casting && x.Cast == CastKind.Aim;
        }
        Assert.True(knelt);
        Assert.Equal(EnemyAnim.Windup, x.Anim);
        Assert.True(x.AnimT < 0.05);
        Assert.DoesNotContain(b.Projectiles.Living(), pr => pr.Owner == Side.Enemy);
        // She steps well off the line while it aims; it looses down the line it knelt to.
        double lineZ = p.Z;
        p.Z += 4;
        for (double t = 0; t < aim + 0.05; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); p.Z = lineZ + 4; }
        var bolts = b.Projectiles.Living().Where(pr => pr.Owner == Side.Enemy).ToList();
        Assert.NotEmpty(bolts);
        // The middle bolt of the three flies along the fixed line, not toward where she went.
        var mid = bolts.OrderBy(pr => Math.Abs(pr.Vz)).First();
        Assert.True(Math.Abs(mid.Vz) < Math.Abs(mid.Vx) * 0.05, $"bolt ({mid.Vx:0.0},{mid.Vz:0.0})");
        Assert.NotEqual(CastKind.Aim, x.Cast);
    }
"""),
    ],
}
