using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-064) A death is entered once: a second killing call on a body already falling (an execute
/// behind the killing blow, a death hook's own burst) is no second kill, no second ember and no second event.</summary>
public sealed class DeathOnceTests
{
    [Fact]
    public void A_body_already_falling_is_not_killed_again()
    {
        // old: the second call counted a second kill, dropped a second ember and emitted a second Ev.Kill
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy("risen", 6, 6)!;
        b.Events.Drain();
        b.KillEnemy(e, true, null);
        int kills = b.KillCount, picks = b.Pickups.Living().Count();
        b.KillEnemy(e, true, null);
        Assert.Equal(EnemyState.Dying, e.State);
        Assert.Equal(1, kills);
        Assert.Equal(kills, b.KillCount);
        Assert.Equal(picks, b.Pickups.Living().Count());
        Assert.Single(b.Events.Drain().OfType<Ev.Kill>());
        Assert.Equal(1, b.KillsByFamily[e.Def.Family]);
    }
}
