using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-067) A blow called off (she got up at a checkpoint) calls its mark off too: the HUD and the
/// ground hear an Off under the mark's id, so no warning outlives the blow it warned of.</summary>
public sealed class CancelBlowsMarkTests
{
    [Fact]
    public void A_cancelled_blow_sends_its_mark_off()
    {
        // old: CancelBlows cleared the list silently; the HUD's mark stayed on its wall-clock timer
        var b = BattleTests.Arena(4);
        var blow = b.Blow(new Battle.EnemyBlow { Delay = 2.0, Damage = 10, Shape = TelegraphShape.Circle, Radius = 2, X = 30, Z = 30 });
        var own = b.Blow(new Battle.EnemyBlow { OwnMark = true, Delay = 2.0, Damage = 10, Shape = TelegraphShape.Circle, Radius = 2, X = 30, Z = 30 });
        b.Events.Drain();
        b.CancelBlows();
        var offs = b.Events.Drain().OfType<Ev.Telegraph>().Where(t => t.Phase == TellPhase.Off).ToList();
        Assert.Single(offs);
        Assert.Equal(blow.MarkId, offs[0].Id);
        Assert.Empty(b.Blows);
    }
}
