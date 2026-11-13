using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-052) LAMPS_OFF is a dev switch: read through the dev gate when a lamp lights, never
/// cached before the host sets the gate, so a release build lights every lamp whatever the environment says.</summary>
[Collection("Balance")]
public sealed class LampsOffGateTests
{
    const string Probe = "audit.su052.probe";

    static bool Lit()
    {
        var l = new LampLoadout();
        l.Add(new LampEffect { Do = LampDo.Rule, Rule = Probe });
        return l.Rules.ContainsKey(Probe);
    }

    [Fact]
    public void Lamps_off_counts_in_dev_and_is_ignored_in_release()
    {
        Environment.SetEnvironmentVariable("LAMPS_OFF", Probe);
        try
        {
            DevOverrides.On = true;
            Assert.False(Lit());
            DevOverrides.On = false;
            Assert.True(Lit());
        }
        finally { DevOverrides.On = true; Environment.SetEnvironmentVariable("LAMPS_OFF", null); }
        Assert.True(Lit());
    }
}
