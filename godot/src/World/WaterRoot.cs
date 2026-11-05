using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>A zone's water: its bodies with their looks as built, so a story state (ZoneView.SetState, the zone's
/// states.json "water") can lay its keys over them and take them off again.</summary>
public partial class WaterRoot : Node3D
{
    internal readonly List<(ShaderMaterial Mat, JsonElement Look)> Bodies = new();

    /// <summary>Each body's look as built with over[i]'s keys over it (none: as built): its colours, numbers and bed.</summary>
    public void Relook(JsonArray? over)
    {
        for (int i = 0; i < Bodies.Count; i++)
        {
            var (mat, built) = Bodies[i];
            var look = Water.Merge(built, over != null && i < over.Count ? over[i] : null);
            Water.Reset(mat);
            Water.Look(mat, look);
            Water.Bed(look);
        }
    }
}
