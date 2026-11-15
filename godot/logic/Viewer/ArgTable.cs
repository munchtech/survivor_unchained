using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Viewer;

/// <summary>
/// The developer's switches as the game reads them (Args, src/Shots.cs): "--key value" pairs, a key with no value
/// (the next word is another --key, or none) reads "1", words that are not keys are skipped. Read once from the
/// command line, or replaced by an override: the look viewer (docs/tools/LOOK_VIEWER.md) replays the game with a new
/// set of switches before each scene load, as game_frame.py would launch it, and clears the override to get the
/// command line back.
/// </summary>
public sealed class ArgTable
{
    readonly Func<IReadOnlyList<string>> source;
    Dictionary<string, string>? parsed, over;

    public ArgTable(Func<IReadOnlyList<string>> source) { this.source = source; }

    public static Dictionary<string, string> Parse(IReadOnlyList<string> a)
    {
        var d = new Dictionary<string, string>();
        for (int i = 0; i < a.Count; i++)
        {
            if (!a[i].StartsWith("--")) continue;
            var key = a[i][2..];
            var val = i + 1 < a.Count && !a[i + 1].StartsWith("--") ? a[++i] : "1";
            d[key] = val;
        }
        return d;
    }

    /// <summary>The switches in force: the override's, else the command line's.</summary>
    public Dictionary<string, string> All() => over ?? (parsed ??= Parse(source()));

    /// <summary>Every later read sees these switches instead of the command line (null: the command line again).</summary>
    public void Override(IReadOnlyList<string>? args) => over = args == null ? null : Parse(args);

    public bool Overridden => over != null;
}
