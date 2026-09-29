using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Core;

/// <summary>Enum values as the web game's keys ('physical', 'lowHealth') and back.</summary>
public static class EnumKey<T> where T : struct, Enum
{
    static readonly Dictionary<T, string> keys = new();
    static readonly Dictionary<string, T> back = new();
    public static readonly T[] All = Enum.GetValues<T>();

    static EnumKey()
    {
        foreach (var v in All)
        {
            var n = v.ToString();
            var k = char.ToLowerInvariant(n[0]) + n[1..];
            keys[v] = k;
            back[k] = v;
        }
    }

    public static string Of(T v) => keys[v];
    public static T Parse(string k) => back.TryGetValue(k, out var v) ? v : throw new ArgumentException($"no {typeof(T).Name} '{k}'");
    public static bool TryParse(string k, out T v) => back.TryGetValue(k, out v);
}

public static class EnumKeys
{
    public static string Key<T>(this T v) where T : struct, Enum => EnumKey<T>.Of(v);
}
