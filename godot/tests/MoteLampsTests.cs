using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Seeking Motes on the arcanist's own road (lamps full) must not fall behind
/// the same skill under another calling's lamps: its lamps feed it, none may starve it.
/// (The probe: `Balance lamped`, godot/balance/Program.cs.)</summary>
[Collection("Balance")]
public class MoteLampsTests(ITestOutputHelper log)
{
    static double Dps(string calling, string type, string lamps, string? evo)
    {
        var rs = new double[6];
        Parallel.For(0, rs.Length, s => rs[s] = Probe.Lamped(calling, type, lamps, "seeking_motes", 8, evo, 7, 1 + (int)s).DamageBy.GetValueOrDefault("seeking_motes") / 40.0);
        return rs.OrderBy(x => x).ElementAt(rs.Length / 2);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("mote_cascade")]
    public void Moonweaver_lamps_do_not_starve_the_motes(string? evo)
    {
        double arc = Dps("arcanist", "moonweaver", "full", evo), warden = Dps("warden", "bulwark", "full", evo);
        log.WriteLine($"{evo ?? "rank 8"}: arcanist {arc:0}/s, warden {warden:0}/s");
        Assert.True(arc >= warden * 0.9, $"arcanist motes {arc:0}/s against the warden's {warden:0}/s");
    }
}
