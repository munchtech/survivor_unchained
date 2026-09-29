using System.Globalization;
using Godot;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained;

/// <summary>
/// A zone, stood up from its exported data (World/ZoneView.cs) under the
/// atmosphere of an hour of the day, seen from the game's camera; with
/// --fight, the slice's night fight in it. Everything is put together here,
/// in code, from the game's own assets (../public/assets, linked as
/// res://assets) and the zones as the web game builds them (res://data/zones,
/// tools/godot/export_zone.mjs).
///
/// Options (after `--`, see Shots.cs):
///   --zone lowford|waystation|verge   (default verge)
///   --time day|night|dusk|dawn        (default night)
///   --at X,Z        where to look (default: the Verge's Hunters' Blind, or
///                   the zone's start)
///   --lit all|I,J   light these lights too (the runtime lights them in play)
///   --heal H        the blight drawn back (0..1)
///   --fight         the slice's fight here (--risen N, --start N: Fight.cs)
///   --pitch, --dist the camera
/// </summary>
public partial class Slice : Node3D
{
    ZoneData zone = null!;
    Camera3D cam = null!;
    Vector3 focus;

    public override void _Ready()
    {
        // The colour sheets as Godot should have them, before any model loads.
        SurvivorUnchained.View.Textures.Mend();
        AddChild(new Shots());
        var id = Args.Get("zone") ?? "verge";
        zone = new ZoneData(id);
        var meta = zone.Meta;

        float x, z;
        if (Args.Get("at") is string at)
        {
            var p = at.Split(',');
            x = float.Parse(p[0], CultureInfo.InvariantCulture);
            z = float.Parse(p[1], CultureInfo.InvariantCulture);
        }
        else if (id == "verge") (x, z) = (-22, -33);
        else (x, z) = ((float)meta.Start.X, (float)meta.Start.Z);
        focus = new Vector3(x, zone.HeightAt(x, z) + 0.8f, z);

        var view = new ZoneView(zone, new Vector2(x, z), Args.Num("grass", 26));
        AddChild(view);
        var time = Args.Get("time") ?? "night";
        bool night = time == "night";
        var air = new Atmosphere();
        AddChild(air);
        air.Set(night ? (id == "waystation" ? Atmospheres.NightTown : Atmospheres.Night) : Atmospheres.ByName(time));
        view.SetNight(night);
        if (Args.Has("heal")) view.SetHeal(Args.Num("heal", 0));
        if (Args.Get("lit") is string lit)
        {
            if (lit == "all") for (int i = 0; i < meta.Lights.Count; i++) view.SetLit(i, true);
            else foreach (var s in lit.Split(',')) view.SetLit(int.Parse(s), true);
        }
        else if (id == "verge" && night)
            // The slice's fight is by the Hunters' Blind, its fire lit.
            view.SetLit(meta.Refs.GetProperty("blindFire").GetInt32(), true);

        if (Args.Has("fight"))
        {
            var fire = focus;
            if (id == "verge")
            {
                var l = zone.Lights[meta.Refs.GetProperty("blindFire").GetInt32()];
                fire = l.At with { Y = zone.HeightAt(l.At.X, l.At.Z) };
            }
            AddChild(new Fight(zone, focus with { Y = zone.HeightAt(x, z) }, fire));
        }
        else
        {
            cam = new Camera3D { Fov = 34, Near = 0.5f, Far = 1400 };
            AddChild(cam);
            PlaceCamera();
            RenderingServer.GlobalShaderParameterSet("survivor", Vector4.Zero);
        }
        GD.Print($"zone {id} at {x},{z} ({time}): {RenderingServer.GetVideoAdapterName()}; {zone.Flora.Count} flora groups, {zone.Props.Count} props, {meta.Lights.Count} lights");
    }

    /// <summary>The web game's follow camera: a steep three-quarter view.</summary>
    void PlaceCamera()
    {
        float pitch = Mathf.DegToRad(Args.Num("pitch", 56)), dist = Args.Num("dist", 23);
        cam.Position = focus + new Vector3(0, Mathf.Sin(pitch) * dist, Mathf.Cos(pitch) * dist);
        cam.LookAt(focus);
    }
}
