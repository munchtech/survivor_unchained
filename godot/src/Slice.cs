using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained;

/// <summary>
/// The test slice: a night fight in the Verge, rebuilt in Godot to compare
/// with the three.js game. Everything is put together here, in code, from
/// the game's own assets (../public/assets, linked as res://assets) and the
/// zone as the web game builds it (res://data, tools/godot/export_zone.mjs).
///
/// Slice options (after `--`, see Shots.cs): --at X,Z to stand elsewhere;
/// --still for the place without the fight; --risen N, --start N (Fight.cs).
/// </summary>
public partial class Slice : Node3D
{
    ZoneData zone = null!;
    Camera3D cam = null!;
    Vector3 focus;

    public override void _Ready()
    {
        AddChild(new Shots());
        zone = new ZoneData("verge");
        AddChild(Ground.Build(zone));
        AddChild(Dressing.Flora(zone));
        AddChild(Dressing.Props(zone));
        AddChild(Dressing.Landmarks(zone));
        AddChild(Water.Build(zone));
        Night();

        // Where the fight is: by the Hunters' Blind, its fire lit.
        var at = (Args.Get("at") ?? "-22,-33").Split(',');
        float x = float.Parse(at[0], System.Globalization.CultureInfo.InvariantCulture);
        float z = float.Parse(at[1], System.Globalization.CultureInfo.InvariantCulture);
        focus = new Vector3(x, zone.HeightAt(x, z) + 0.8f, z);
        AddChild(Dressing.Lights(zone, focus));
        AddChild(Grass.Build(zone, new Vector2(x, z), Args.Num("grass", 22)));
        // The Hunters' Blind's fire, where the web game lights it (its stones
        // and logs came with the landmarks; the fire itself is Godot's).
        var fire = focus;
        foreach (var l in zone.Lights)
            if (l.On && new Vector2(l.At.X - x, l.At.Z - z).Length() < 12 && l.Color.R > l.Color.B)
            {
                fire = new Vector3(l.At.X, zone.HeightAt(l.At.X, l.At.Z), l.At.Z);
                if (Args.Has("firetest"))
                {
                    // Each part of the fire alone, side by side: flames,
                    // embers, smoke.
                    string[] parts = { "flames", "embers", "smoke" };
                    for (int i = 0; i < 3; i++)
                    {
                        var p = fire + new Vector3((i - 1) * 2.2f, 0, 3);
                        AddChild(Campfire.Build(p with { Y = zone.HeightAt(p.X, p.Z) }, ring: false, parts: parts[i]));
                    }
                }
                else AddChild(Campfire.Build(fire, ring: false));
            }
        if (Args.Has("still"))
        {
            // The place alone, from the game's camera.
            cam = new Camera3D { Fov = 34, Far = 600 };
            AddChild(cam);
            PlaceCamera();
        }
        else AddChild(new Fight(zone, focus with { Y = zone.HeightAt(x, z) }, fire));
        GD.Print($"slice ready: {RenderingServer.GetVideoAdapterName()}; {zone.Flora.Count} flora groups, {zone.Props.Count} props");
    }

    /// <summary>The web game's follow camera: a steep three-quarter view.</summary>
    void PlaceCamera()
    {
        float pitch = Mathf.DegToRad(Args.Num("pitch", 56)), dist = Args.Num("dist", 23);
        cam.Position = focus + new Vector3(0, Mathf.Sin(pitch) * dist, Mathf.Cos(pitch) * dist);
        cam.LookAt(focus);
    }

    /// <summary>Night in the wild: a cold moon, a dark sky, air you can see
    /// the fires in.</summary>
    void Night()
    {
        var sky = new ProceduralSkyMaterial
        {
            SkyTopColor = new Color("#03050d"), SkyHorizonColor = new Color("#18203a"),
            GroundBottomColor = new Color("#07080c"), GroundHorizonColor = new Color("#18203a"),
            SkyEnergyMultiplier = 1.0f,
        };
        var env = new Environment
        {
            BackgroundMode = Environment.BGMode.Sky,
            Sky = new Sky { SkyMaterial = sky },
            AmbientLightSource = Environment.AmbientSource.Color,
            AmbientLightColor = new Color("#3f5780"),
            AmbientLightEnergy = 0.42f,
            TonemapMode = Environment.ToneMapper.Agx,
            TonemapExposure = 1.9f,
            // Soft: a field of thin blades turns strong SSAO into black specks.
            SsaoEnabled = true, SsaoRadius = 1.0f, SsaoIntensity = 1.1f, SsaoDetail = 0.3f,
            GlowEnabled = true, GlowIntensity = 0.7f, GlowBloom = 0.04f, GlowHdrThreshold = 1.1f,
            FogEnabled = true, FogLightColor = new Color("#101a24"), FogDensity = 0.006f, FogSkyAffect = 0.6f,
            VolumetricFogEnabled = true, VolumetricFogDensity = 0.012f, VolumetricFogAlbedo = new Color("#8fa0c0"),
            VolumetricFogLength = 90, VolumetricFogAnisotropy = 0.3f,
            AdjustmentEnabled = true, AdjustmentContrast = 1.1f, AdjustmentSaturation = 0.95f,
        };
        // The glow's tighter levels only: the wide ones spread every bright
        // speck (an ember, a blade's edge) into a ball of light.
        float[] glow = { 0, 0.6f, 1, 0.5f, 0.15f, 0, 0 };
        for (int i = 0; i < glow.Length; i++) env.SetGlowLevel(i, glow[i]);
        // Debug switches, for telling artefacts apart.
        if (Args.Has("nossao")) env.SsaoEnabled = false;
        if (Args.Has("notaa")) GetViewport().UseTaa = false;
        AddChild(new WorldEnvironment { Environment = env });
        // The moon, where the web game's night puts it: 52 degrees up, from
        // azimuth 128 (0 = +x, 90 = +z).
        float el = Mathf.DegToRad(52), az = Mathf.DegToRad(128);
        var dir = new Vector3(Mathf.Cos(el) * Mathf.Cos(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Sin(az));
        var moon = new DirectionalLight3D
        {
            LightColor = new Color("#b8cbf2"), LightEnergy = 0.42f, ShadowEnabled = true,
            DirectionalShadowMaxDistance = 70, ShadowBlur = 1.5f, LightVolumetricFogEnergy = 0.6f,
        };
        AddChild(moon);
        moon.LookAtFromPosition(dir * 100, Vector3.Zero);
    }
}
