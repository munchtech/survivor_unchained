using System.Collections.Concurrent;
using Godot;

namespace SurvivorUnchained;

/// <summary>StringNames made once. Every StringName made from a string in a per-frame call is a Godot disposable (a weak
/// handle and a finalizer) that survives its first collection; this hands back the same one for the same text.</summary>
public static class Sn
{
    static readonly ConcurrentDictionary<string, StringName> made = new();
    public static StringName Of(string s) => made.TryGetValue(s, out var n) ? n : made.GetOrAdd(s, k => new StringName(k));
}
