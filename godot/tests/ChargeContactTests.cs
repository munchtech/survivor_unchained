using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-073) A charge strikes whoever it runs into once per 0.8 s: a creature in contact is no
/// longer struck on every tick the way she never was.</summary>
public sealed class ChargeContactTests
{
    [Fact]
    public void A_charge_into_a_creature_strikes_it_once_per_cooldown()
    {
        // old: the creature branch never set AttackT, so it struck the ally every tick of contact (about 24 blows here)
        var b = BattleTests.Arena(4);
        double fx = b.Player.X + 40, fz = b.Player.Z;
        var ally = b.SpawnEnemy("risen", fx, fz, new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally })!;
        ally.MaxHp = ally.Hp = 1e7;
        var knight = b.SpawnEnemy("barrow_knight", fx - 0.6, fz)!;
        knight.AttackT = 0;
        b.Events.Drain();
        int hits = 0;
        for (int i = 0; i < 24; i++)   // 0.4 s of contact
        {
            knight.X = ally.X - 0.6; knight.Z = ally.Z;
            knight.State = EnemyState.Lunging; knight.StateT = 0.5; knight.LungeX = 1; knight.LungeZ = 0;
            knight.Target = ally.Id;
            b.Tick(1 / 60.0, 0, 0);
            hits += b.Events.Drain().OfType<Ev.Hit>().Count(h => h.Target == ally.Id);
        }
        Assert.Equal(1, hits);
    }
}
