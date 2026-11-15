using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Viewer;

/// <summary>
/// Which of the game's per-session package caches belong to one package (NpcPackage.Forget, NpcDye.Forget): its
/// name's own entries, and the scene files under its folder (res://art/npc/NAME/...). The look viewer forgets them
/// before each replay, so an edited package is read again from its files.
/// </summary>
public static class PackageCache
{
    public static bool OwnsFile(string name, string file) =>
        file.StartsWith($"res://art/npc/{name}/", StringComparison.Ordinal);

    /// <summary>Removes the entries whose key matches; how many went.</summary>
    public static int Forget<TKey, TValue>(IDictionary<TKey, TValue> cache, Func<TKey, bool> of)
    {
        var gone = cache.Keys.Where(of).ToList();
        foreach (var k in gone) cache.Remove(k);
        return gone.Count;
    }
}
