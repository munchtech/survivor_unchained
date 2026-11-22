using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(P3, docs/design/DEN_ROSTER.md, the owner 22 Nov "I approve den roster") The kit's shared charge is off in a
/// dungeon: no woken den pack's foe casts the telegraph kit's "charge" (MapRun.Press, KitCharges). A Wayfinder's map keeps
/// it (the control: the same harness, the same people, no dungeon). Arena nights and story fights keep theirs: ArenaTests,
/// ChampionsTests, EncountersTests, MassGraceTests and StandSwingTests run their kit charges unchanged.</summary>
[Collection("Balance")]
public class DenKitGateTests
{
    readonly ITestOutputHelper _out;
    public DenKitGateTests(ITestOutputHelper o) { _out = o; }

    /// <summary>The kit charges marked on her by a run's rank and file (not the ruler's Drive), and the fight seconds.</summary>
    static (int Lanes, MapRunResult R) Count(int seed, string dungeon)
    {
        int lanes = 0;
        MapSim.Tap = (t, evs, b, bossUp) =>
        {
            if (bossUp) return;
            foreach (var e in evs)
                if (e is Ev.Telegraph { Tell: "charge", Phase: TellPhase.Warn, Boss: false }) lanes++;
        };
        try
        {
            var def = DungeonGen.Get("hollow")!;
            var r = MapSim.Play(new MapRunSpec(seed, "warden", 1, def.People, 6, 1, [], "deft", 8, dungeon));
            return (lanes, r);
        }
        finally { MapSim.Tap = null; }
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public void A_den_pack_casts_no_kit_charge(int seed)
    {
        var (lanes, r) = Count(seed, "hollow");
        _out.WriteLine($"den s{seed}: kit lanes {lanes}, room fight {r.FightRoomSec:0}s, packs {r.PacksCleared}/{r.Packs}, heavy marks {r.HeavyRoom}");
        Assert.True(r.FightRoomSec > 20, $"den s{seed}: too little fighting to read ({r.FightRoomSec:0} s)");
        Assert.Equal(0, lanes);
    }

    [Fact]
    public void A_wayfinders_map_keeps_the_kit_charge()
    {
        var (lanes, r) = Count(1, "");
        _out.WriteLine($"map s1: kit lanes {lanes}, room fight {r.FightRoomSec:0}s, packs {r.PacksCleared}/{r.Packs}");
        Assert.True(lanes > 0, "a Wayfinder's map's packs should still cast the kit's charge");
    }
}
