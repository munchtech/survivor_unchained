using System;
using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A release build takes no tuning file from the environment (Codex audit SU-007): the variables
/// count only while the host has overrides on (the game sets it to Args.Dev; tests and harnesses keep it on).</summary>
[Collection("Balance")]
public sealed class DevOverridesTests
{
    [Fact]
    public void Tuning_variables_are_ignored_when_overrides_are_off()
    {
        const string name = "SU_AUDIT_OVERRIDE_PROBE";
        Environment.SetEnvironmentVariable(name, "x.json");
        try
        {
            Assert.Equal("x.json", DevOverrides.Env(name));
            DevOverrides.On = false;
            Assert.Null(DevOverrides.Env(name));
        }
        finally { DevOverrides.On = true; Environment.SetEnvironmentVariable(name, null); }
    }
}
