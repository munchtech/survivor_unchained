using System;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A probe or generator that is a tool, not a test: skipped (and shown as
/// skipped) unless the environment variable is set (to the given value, if one is
/// given). Run it with the variable set and it behaves exactly as before.</summary>
public class ProbeFactAttribute : FactAttribute
{
    public ProbeFactAttribute(string envVar, string? value = null) => Skip = Reason(envVar, value);

    internal static string? Reason(string envVar, string? value)
    {
        var v = Environment.GetEnvironmentVariable(envVar);
        bool on = value == null ? !string.IsNullOrEmpty(v) : v == value;
        return on ? null : $"probe: opt-in, set {envVar}{(value == null ? "" : "=" + value)} to run";
    }
}

/// <summary>ProbeFact for a theory.</summary>
public class ProbeTheoryAttribute : TheoryAttribute
{
    public ProbeTheoryAttribute(string envVar, string? value = null) => Skip = ProbeFactAttribute.Reason(envVar, value);
}
