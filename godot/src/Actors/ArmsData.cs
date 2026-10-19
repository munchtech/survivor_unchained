using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>Adds the rows of res://art/weapons/weapons.json to Arms.All (Arms' static constructor calls it): a new weapon
/// of a known kind is data, not C#. A C# row of the same id wins.</summary>
public static class ArmsData
{
    public const string Path = "res://art/weapons/weapons.json";

    public static void Merge(Dictionary<string, Arms.Spec> all)
    {
        if (!FileAccess.FileExists(Path)) return;
        WeaponsData.Merge(all, WeaponsData.Parse(FileAccess.GetFileAsString(Path)),
            r => new Arms.Spec(r.File, r.Length, r.Grip, Node: r.Node, Pistol: r.Pistol, Lean: r.Lean, Kind: r.Kind));
    }
}
