using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M5 r3) No tutorial card on a champion's wake (Play/Zones/ChampionGate.cs).</summary>
public class ChampionGateTests
{
    [Fact]
    public void A_card_waits_within_six_seconds_of_a_champions_wake()
    {
        // 20 m off, waking at 9, closing at 5 m/s: 2.2 s away, so the card waits
        Assert.True(ChampionGate.WakeIn(20, 9, 5) < ChampionGate.Ahead);
        // 50 m off at 5 m/s: 8.2 s, the card may show
        Assert.False(ChampionGate.WakeIn(50, 9, 5) < ChampionGate.Ahead);
        // standing, or walking away: never
        Assert.Equal(double.PositiveInfinity, ChampionGate.WakeIn(20, 9, 0));
        Assert.Equal(double.PositiveInfinity, ChampionGate.WakeIn(20, 9, -5));
        // inside its reach: now
        Assert.Equal(0, ChampionGate.WakeIn(8, 9, 0));
    }
}
