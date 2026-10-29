using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.View;

/// <summary>
/// A zone, stood up from its exported data (ZoneData): the ground, the
/// water, the flora, the kits' pieces, the landmarks, and what the web
/// game's ZoneKit keeps alive (src/world/zones/kit.ts): its lights, which
/// the runtime lights and puts out (a light's glowing bits and its fire go
/// with it), the fires, chimney smoke, moths round the lamps after dark,
/// and what only shows after dark.
///
/// The web game can afford a dozen lights and moves them to the lamps
/// nearest the survivor; here every lamp is a light of its own, faded out
/// with distance from the camera, and the big ones cast shadows near it.
/// </summary>
public partial class ZoneView : Node3D
{
    public readonly ZoneData Data;
    public Landmarks Landmarks { get; private set; } = null!;
    readonly List<OmniLight3D> lights = new();
    readonly List<float> phases = new();
    readonly List<bool> lit = new();
    /// <summary>Every light's spec: the zone's, then those the runtime set down.</summary>
    List<ZoneData.LightSpec> specs = null!;
    readonly Dictionary<int, MeshInstance3D> flames = new();
    Node3D lightRoot = null!;
    readonly HashSet<string> stopped = new();
    readonly List<(int Light, Node3D Fire)> fires = new();
    readonly HashSet<string> fireGlow = new();
    readonly List<GpuParticles3D> chimneys = new();
    readonly List<(int Light, GpuParticles3D Moths)> moths = new();
    ShaderMaterial ground = null!;
    MultiMeshInstance3D? grass, leaves;
    Node3D props = null!;
    double time;
    public bool Night { get; private set; }

    /// <param name="grassAround">Where to grow the meadow (the web game grows
    /// it round the survivor as they go); null for none.</param>
    public ZoneView(ZoneData z, Vector2? grassAround = null, float grassRadius = 40) : this(z)
    {
        Slices.All(Build(grassAround, grassRadius));
        WaterLevel();
        // (its paint the latest now, for the thaw's sun: GroundPaint.SunAt)
        if (z.Place == null) GroundPaint.Of(z);
    }

    /// <summary>A zone to be stood up a few steps a frame (Build), ahead of the journey to it: nothing of it
    /// reaches the place still shown (the water's height for the stones goes out as it enters the tree).</summary>
    public ZoneView(ZoneData z)
    {
        Data = z;
        Name = $"Zone_{z.Id}";
    }

    bool later;
    public override void _EnterTree() { if (later) WaterLevel(); }

    /// <summary>(the water's height for our own stones' wet band, kit.gdshader's OWN_ROCK; none: far under everything)</summary>
    void WaterLevel()
    {
        bool has = Data.Meta.Places.TryGetValue("WATER_Y", out var wly);
        Water.Level = has ? wly.GetSingle() : null;
        RenderingServer.GlobalShaderParameterSet("water_level", has ? new Vector4(wly.GetSingle(), 0, 0, 1) : new Vector4(0, -1000, 0, 0));
    }

    /// <summary>Its steps (Slices): the ground and water, the flora, the scatter, the props piece by piece, the
    /// landmarks, the meadow, the lights and fires one by one. Built ahead (Game.Prepare), a frame may end at
    /// each; built at once, they run straight through.</summary>
    public IEnumerable<object?> Build(Vector2? grassAround = null, float grassRadius = 40, bool ahead = false)
    {
        var z = Data;
        later = ahead;
        Perf.Lap("zone view", true);
        var g = Ground.Build(z);
        ground = (ShaderMaterial)g.Mesh.SurfaceGetMaterial(0);
        AddChild(g);
        yield return "ground";
        AddChild(Water.Build(z));
        yield return "water";
        if (MistLayers.Build(z) is { } mist) AddChild(mist);
        Perf.Lap("ground and water");
        yield return "mist";
        var flora = Dressing.Flora(z);
        AddChild(flora);
        // Nothing grows in a fire pit: neither the flora nor the meadow (GrowGrass).
        foreach (var f in z.Meta.Fires)
            if (f.Ring)
            {
                pits.Add(new Vector4((float)f.X, (float)f.Z, 0.95f * (float)f.Size, 0));
                Bare(flora, new Vector3((float)f.X, (float)f.Y, (float)f.Z), 0.95f * (float)f.Size);
            }
        Perf.Lap("flora");
        yield return "flora";
        if (Scatter.Build(z) is { } sc) AddChild(sc);
        Perf.Lap("scatter");
        yield return "scatter";
        foreach (var p in OwnProps.For(z.Id)?.Places ?? new())
            if (p.Bare is Vector2 b) pits.Add(new Vector4(p.At.X, p.At.Y, b.X, b.Y));
        props = new Node3D { Name = "Props" };
        foreach (var s in Dressing.Props(z, props)) yield return s;
        AddChild(props);
        Perf.Lap("props");
        Landmarks = new Landmarks(z);
        AddChild(Landmarks.Root);
        yield return "landmarks";
        // Our own props placed by the zone's data (OwnProps: props_own.json "place"), the blocked-out ones hidden.
        var ownProps = OwnProps.For(z.Id);
        if (ownProps != null) AddChild(OwnProps.Dress(z, ownProps, Landmarks.Root));
        // The camp on the Low Ford road, made for its close-ups (Camp.cs); its logs ours where the data places them.
        if (z.Id == "lowford") AddChild(Camp.Dress(Landmarks.Root, logs: ownProps == null || !ownProps.Places.Exists(p => p.Preset.StartsWith("log"))));
        Perf.Lap("landmarks");
        yield return "own props";
        // An ember arena's ring, its mist and its streams.
        if (z.Place != null)
        {
            var edge = ArenaEdge.Build(z);
            AddChild(edge);
            // A story place's gates, found by name as the night opens them (Show).
            foreach (var c in edge.GetChildren())
                if (c is Node3D n3 && n3.Name.ToString().StartsWith("gate_")) Landmarks.Nodes["gate:" + n3.Name.ToString()[5..]] = n3;
            Perf.Lap("arena edge");
        }
        // (An arena whose place grows none, the Dig, has no meadow at all.)
        if (grassAround is Vector2 at && (z.Place == null || ArenaGround.GrowsGrass(z.Place.Id))) GrowGrass(at, grassRadius);
        Perf.Lap("grass");
        yield return "grass";

        var meta = z.Meta;
        specs = new List<ZoneData.LightSpec>(z.Lights);
        lightRoot = new Node3D { Name = "Lights" };
        AddChild(lightRoot);
        for (int i = 0; i < meta.Lights.Count; i++) { MakeLight(z.Lights[i]); yield return null; }
        var fx = new Node3D { Name = "Fires" };
        AddChild(fx);
        foreach (var f in meta.Fires)
        {
            yield return "light or fire";
            // The web game's ring of stones round it goes; the fire's own ring takes its place.
            var fat = new Vector3((float)f.X, (float)f.Y, (float)f.Z);
            if (f.Ring) HideLandmarksNear(fat, 0.85f * (float)f.Size);
            var fire = Campfire.Build(fat, (float)f.Size, ring: f.Ring);
            fx.AddChild(fire);
            fires.Add((f.Light, fire));
            TownFire(fat, (float)f.Size, f.Light, fire, fx);   // (E9d r2: a cook fire's smoke; a brazier's fire unshadowed; ZoneView.Town)
            if (f.Light >= 0 && f.Light < lights.Count) lights[f.Light].LightCullMask &= ~(Campfire.CoalLayer | Campfire.RingLayer);
            // The web game marks a fire's flame with a glowing ball; here the
            // fire has flames of its own, and the ball would only bloom white.
            if (f.Light >= 0 && f.Light < meta.Lights.Count)
                foreach (var glow in meta.Lights[f.Light].Glow) { fireGlow.Add(glow); if (Node(glow) is Node3D ball) ball.Visible = false; }
        }
        // The lamps: modeled holders with the flame kit's flames in them (Lamps.cs, look bible 10), where
        // the web game hung glowing balls (the road's lanterns, the gate's torches, the ford's three beacons).
        yield return "fire";
        WireLamps(meta);
        yield return "lamps";
        foreach (var c in meta.Chimneys)
        {
            var smoke = Plume();   // (E9d: the town's plumes, ZoneView.Town)
            // (each its own name: a second "Chimney" under one parent was renamed "@Chimney@n", and HouseFade, finding
            // "Chimney*", tied one plume of 18 to its house: the rest hung over the cut rooms)
            smoke.Name = "Chimney" + chimneys.Count;
            smoke.Position = new Vector3((float)c.X, (float)c.Y, (float)c.Z);
            fx.AddChild(smoke);
            chimneys.Add(smoke);
        }
        foreach (var m in meta.Moths)
        {
            var p = Campfire.Moths();
            p.Position = z.Lights[m].At;
            fx.AddChild(p);
            moths.Add((m, p));
        }
        for (int i = 0; i < lights.Count; i++) SetLit(i, z.Lights[i].On);
        NightLamps();   // (Env 22 r1f: props_own.json's night lamps, ZoneView.Town; after the zone's own lights, each its own new light)
        SetNight(false);
    }

    /// <summary>The zone's lights kept off her own layer (PlayerView.HerLayer: the close view by night), or given back.</summary>
    public void HerUnlit(bool off)
    {
        foreach (var l in lights) l.LightCullMask = off ? l.LightCullMask & ~(PlayerView.HerLayers | Brush.MaskLayer) : l.LightCullMask | PlayerView.HerLayers;
    }

    /// <summary>The lit light nearest `at` within `within` metres (a fire by her), or null.</summary>
    public OmniLight3D? NearestLit(Vector3 at, float within)
    {
        OmniLight3D? best = null; float bd = within * within;
        for (int i = 0; i < lights.Count; i++)
        {
            if (!lit[i]) continue;
            float d = lights[i].GlobalPosition.DistanceSquaredTo(at);
            if (d < bd) { bd = d; best = lights[i]; }
        }
        return best;
    }

    OmniLight3D MakeLight(ZoneData.LightSpec l)
    {
        int i = lights.Count;
        phases.Add((float)(MathX.Hash1(i, 7) * 100));
        lit.Add(false);
        var light = new OmniLight3D
        {
            Name = $"Light{i}", Position = l.At, LightColor = l.Color,
            // three.js's intensity I lights to I/pi what Godot's energy E lights to E.
            LightEnergy = l.Intensity / Mathf.Pi,
            OmniRange = l.Distance > 0 ? l.Distance : 60, OmniAttenuation = 1.7f,
            // The big lights (fires, lanterns) cast shadows near the camera, at dusk and by night (Shadows).
            ShadowEnabled = false, DistanceFadeShadow = 28, DistanceFadeEnabled = true,
            DistanceFadeBegin = 45, DistanceFadeLength = 20, LightVolumetricFogEnergy = 1.2f,
        };
        lights.Add(light);
        lightRoot.AddChild(light);
        return light;
    }

    /// <summary>A light set down now (a torch, a lamp lit in play), with a
    /// small flame that glows while it is on. Returns its index.</summary>
    public int AddLight(Vector3 at, Color color, float intensity, float distance, float flicker, float glowSize, Color glowColor)
    {
        var spec = new ZoneData.LightSpec(at, color, intensity, distance, flicker, true);
        int i = lights.Count;
        specs.Add(spec);
        MakeLight(spec);
        if (glowSize > 0)
        {
            var c = glowColor.SrgbToLinear() * 3;
            var flame = new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = glowSize, Height = glowSize * 2.4f, RadialSegments = 8, Rings = 4 },
                MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(c.R, c.G, c.B) },
                Position = at, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            };
            lightRoot.AddChild(flame);
            flames[i] = flame;
        }
        SetLit(i, true);
        return i;
    }

    /// <summary>A light's shadows on or off (the night Watch's torch).</summary>
    public void SetShadow(int light, bool on) { if (light >= 0 && light < lights.Count) lights[light].ShadowEnabled = on; }

    /// <summary>A light that goes where something carries it.</summary>
    public void MoveLight(int light, Vector3 at)
    {
        specs[light] = specs[light] with { At = at };
        lights[light].Position = at;
        if (flames.TryGetValue(light, out var f)) f.Position = at;
    }

    /// <summary>A light turned up or down (a cinematic's grade: the camp's fire
    /// burned down to embers), its colour changed, its flicker slowed; 1 is as built.</summary>
    public void SetLevel(int light, float level, Color? color = null, float flickerRate = 1)
    {
        if (light < 0 || light >= lights.Count) return;
        levels[light] = (level, flickerRate);
        if (color is Color c) lights[light].LightColor = c;
        if (specs[light].Flicker <= 0 || driven.Contains(light)) lights[light].LightEnergy = specs[light].Intensity / Mathf.Pi * level;
    }

    readonly Dictionary<int, (float Level, float Rate)> levels = new();
    static readonly bool FireTrace = SurvivorUnchained.Args.Has("fire-trace");

    /// <summary>A light's shadow softened (its source "size" metres across; 0 is as built, hard):
    /// a cinematic's fire throws soft shadows, not razor spokes.</summary>
    public void SetSize(int light, float size)
    {
        if (light < 0 || light >= lights.Count) return;
        lights[light].LightSize = Mathf.Max(0, size);
    }

    /// <summary>How far a fire's light has sunk toward its coals (SetFire).</summary>
    readonly Dictionary<int, float> lightDrop = new();
    /// <summary>How far a burnt-down fire's light drifts about its place (SetFire's sway; 0 for every other light).</summary>
    readonly Dictionary<int, float> lightSway = new();

    /// <summary>A fire's flames scaled (0: embers only); its embers and smoke stay.</summary>
    public void SetFire(int light, float flames, float lift = 0, float sway = 0)
    {
        // "sway": metres the burnt-down fire's light drifts about its place (slow, like coals breathing), so a
        // shadow it throws far off visibly moves (C01 s2: her shadow on the bedroll stood dead still).
        lightSway[light] = sway;
        foreach (var (l, fire) in fires)
        {
            if (l != light || fire.GetNodeOrNull<Node3D>("Flames") is not Node3D f) continue;
            // A fire burnt down throws up only the odd spark.
            if (fire.GetNodeOrNull<GpuParticles3D>("Embers") is { } sparks) sparks.AmountRatio = Mathf.Lerp(0.2f, 1f, Mathf.Clamp(flames, 0, 1));
            f.Visible = flames > 0.02f;
            f.Scale = new Vector3(Mathf.Sqrt(Mathf.Max(flames, 0.02f)), Mathf.Max(flames, 0.02f), Mathf.Sqrt(Mathf.Max(flames, 0.02f)));
            // Burnt down, the light comes from low over the coals, not from a
            // flame a metre up (the coals' own glow lights what is just over them).
            if (light >= 0 && light < lights.Count)
            {
                var at = specs[light].At;
                lightDrop[light] = Mathf.Max(0, at.Y - Mathf.Lerp(fire.Position.Y + 0.18f + lift, at.Y, Mathf.Clamp(flames, 0, 1)));
                lights[light].Position = at + Vector3.Down * lightDrop[light];
            }
        }
    }

    /// <summary>A turning piece (the pump's wheel) stops.</summary>
    public void Stop(string node) => stopped.Add(node);

    /// <summary>A node of the landmarks the runtime reaches for, by name.</summary>
    /// <summary>The lights a lamp's flame flickers (not the zone's own formula), and each one's holders' glass.</summary>
    readonly HashSet<int> driven = new();
    /// <summary>The lamps' holders (and the ford's pylons) out of the lamps' own lights (WireLamps): a lamp's light
    /// sits a hand from its iron and glass and would flare them white (the "hot blob"); lamps cast no shadow, so the
    /// base that would shade the stone under it can't, and the stone is kept out instead.</summary>
    public const uint LampLayer = 1u << 11;
    readonly Dictionary<int, List<Node3D>> lampGlass = new();
    readonly List<(int Light, Flame Flame)> lampFlames = new();
    /// <summary>The zone's own torches (props_own.json "lit"): burning by night only.</summary>
    readonly List<(Node3D Holder, Flame Flame)> ownTorches = new();
    Queue<float>? lampDebugAt;
    bool nearDone;

    static System.Collections.Generic.HashSet<int> LightList(string name) => new((SurvivorUnchained.Args.Get(name) ?? "").Split(',', System.StringSplitOptions.RemoveEmptyEntries).Select(int.Parse));
    static readonly System.Collections.Generic.HashSet<int> ForcedOff = LightList("lights-off"), ForcedOn = LightList("lights-on");
    /// <summary>--lamp-energy K, --lamp-color HEX: the road lamps' light, for pictures (pools on the dirt).</summary>
    static readonly float LampEnergy = SurvivorUnchained.Args.Num("lamp-energy", 1.9f);
    /// <summary>--lamp-range M, --lamp-att A: the road lamps' reach and falloff (the data's 10-13 m lit the whole road evenly).</summary>
    static readonly float LampRange = SurvivorUnchained.Args.Num("lamp-range", 4.5f), LampAtt = SurvivorUnchained.Args.Num("lamp-att", 2f);
    // A paler warm than the web game's #ffa860: on the brown dirt that orange read as mud (E2 judges), this as lamplight.
    static readonly string LampColor = SurvivorUnchained.Args.Get("lamp-color") ?? "#ffc890";
    /// <summary>--lamp-soft M, --lamp-flame K: a lamp flame's soft edge and brightness, for pictures.</summary>
    static readonly float LampSoft = SurvivorUnchained.Args.Num("lamp-soft", 0.02f);
    static readonly float LampFlameK = SurvivorUnchained.Args.Num("lamp-flame", 3.2f);
    /// <summary>--lamp-tilt T, --lamp-core H, --lamp-wide K: a lamp flame's lean to the camera, core start, width, for pictures.</summary>
    static readonly float LampTilt = SurvivorUnchained.Args.Num("lamp-tilt", 0.6f), LampCore = SurvivorUnchained.Args.Num("lamp-core", 0.55f), LampWide = SurvivorUnchained.Args.Num("lamp-wide", 2.2f),
        LampPull = SurvivorUnchained.Args.Num("lamp-pull", 0.15f);
    /// <summary>--ford-flame S: the ford lamps' flame scale (the lamp kind's 0.16 m card), for a 0.5 m cage.</summary>
    /// <summary>--ford-light-up M, --ford-pylon-dark: the ford light's height over the flame's base (0.9: over the iron, which
    /// it leaves out, a soft pool on the pylon's top, not the hot square it laid from 0.16), and the pylon kept out of it, for pictures.
    /// (E7 round 2: 0.35, in the cage by the flame, now our pier is kept out of its lamp's light and the iron is on its own layer.)</summary>
    static readonly float FordLightUp = SurvivorUnchained.Args.Num("ford-light-up", 0.35f);
    static readonly bool FordPylonLit = !SurvivorUnchained.Args.Has("ford-pylon-dark");
    /// <summary>--ford-flame-k K: the ford flames' brightness over the road lamps' (AgX whitens a bright blue).</summary>
    // (Low Ford r3, judge r2: the ford irons read unlit from the play camera: 0.25 to 0.6, with the river's lamp_pool round them)
    static readonly float FordFlameK = SurvivorUnchained.Args.Num("ford-flame-k", 0.6f);
    /// <summary>--ford-core-blue B: the ford flames' core pulled toward blue (0 = blue-white, which AgX clips to pure white).</summary>
    static readonly float FordCoreBlue = SurvivorUnchained.Args.Num("ford-core-blue", 1.3f);
    /// <summary>--lamp-scale S: the road lamps' flame scale (the lamp kind's 0.16 m card; the post's cage is 0.27 m tall), for pictures.</summary>
    static readonly float LampScale = SurvivorUnchained.Args.Num("lamp-scale", 1.3f);
    /// <summary>--holder-lamp-scale S: the flame in our own lamp holders (the posts' 0.27 m cage; Low Ford r1: at 1.3 the flame was
    /// a sliver beside its lit glass, the cage a pale box), for pictures.</summary>
    static readonly float HolderLampScale = SurvivorUnchained.Args.Num("holder-lamp-scale", 1.6f);
    /// <summary>--post-lamp-att A, --post-lamp-energy K: the post lantern's falloff and its light against the road lamps' (the
    /// ground's pool at 2.1 m kept: 2.1^-0.7 / 2.1^-2 = 2.6, so 0.4), for pictures.</summary>
    static readonly float PostLampAtt = SurvivorUnchained.Args.Num("post-lamp-att", 0.7f), PostLampEnergy = SurvivorUnchained.Args.Num("post-lamp-energy", 0.4f);
    static readonly float FordFlame = SurvivorUnchained.Args.Num("ford-flame", 1.5f);
    /// <summary>--ford-energy K: the ford lamps' light, for pictures. (E7 round 2: 12 with --ford-att 2.3, so the lamp lays a pool
    /// round its pier, the water at 1 m twice as bright as at 4 m, where at 1 and 1.7 the moon's wash drowned it: 1.4x.)</summary>
    static readonly float FordEnergy = SurvivorUnchained.Args.Num("ford-energy", 12f);
    /// <summary>--ford-color HEX, --ford-range M, --ford-att A: the ford lamps' cold light (a pale blue, AgX greys it).</summary>
    static readonly string FordColor = SurvivorUnchained.Args.Get("ford-color") ?? "#8cb9ff";
    /// <summary>--ford-specular S: the ford lamps' glints on the water (E7 round 3: 0.3; at Godot's 0.5 the far lamps' glints
    /// spread to blown white patches on the ripples).</summary>
    static readonly float FordSpecular = SurvivorUnchained.Args.Num("ford-specular", 0.3f);
    static readonly float FordRange = SurvivorUnchained.Args.Num("ford-range", 16f), FordAtt = SurvivorUnchained.Args.Num("ford-att", 2.3f);
    /// <summary>--ford-core H, --ford-wide K, --ford-body K, --ford-core-k K: the ford flame's core start, width, body and core brightness
    /// (a small blue teardrop with a small pale core, not the road lamps' broad bright point).</summary>
    static readonly float FordCore = SurvivorUnchained.Args.Num("ford-core", 0.4f), FordWide = SurvivorUnchained.Args.Num("ford-wide", 2.6f),
        FordBody = SurvivorUnchained.Args.Num("ford-body", 0.3f), FordTilt = SurvivorUnchained.Args.Num("ford-tilt", 0.85f), FordCoreK = SurvivorUnchained.Args.Num("ford-core-k", 2.5f);

    /// <summary>A node's transform in the landmarks' frame (the landmarks stand at the zone's origin).</summary>
    Transform3D InLandmarks(Node3D n)
    {
        var t = n.Transform;
        for (var p = n.GetParent(); p != null && p != Landmarks.Root; p = p.GetParent())
            if (p is Node3D p3) t = p3.Transform * t;
        return t;
    }

    /// <summary>Each lamp holder its flame, in the place of the glowing ball the web game lit it by; the ball's
    /// node stays (its name is what the lights, the Prologue and the cinematics reach for) with its mesh hidden,
    /// and the flame under it, so a light put out puts the flame out with it.</summary>
    void WireLamps(SurvivorUnchained.World.ZoneMeta meta)
    {
        var glowLight = new Dictionary<string, int>();
        for (int i = 0; i < meta.Lights.Count && i < lights.Count; i++)
            foreach (var g in meta.Lights[i].Glow) if (!fireGlow.Contains(g)) glowLight[g] = i;
        // The road's lamps and torches (KayKit pieces swapped in Landmarks): the glow ball nearest the flame.
        foreach (var holder in Landmarks.Holders)
        {
            var kind = (string)holder.GetMeta("lamp");
            if (Lamps.Of(kind) is not Lamps.Info info) continue;
            var at = InLandmarks(holder) * info.Flame;
            string? best = null;
            float bd = 0.8f * 0.8f;
            foreach (var (g, _) in glowLight)
                if (Node(g) is Node3D gn && InLandmarks(gn).Origin.DistanceSquaredTo(at) is float d && d < bd) { bd = d; best = g; }
            if (SurvivorUnchained.Args.Has("lamp-debug"))
                GD.Print($"LAMP {kind} at {at} glow {best ?? "-"} {(best != null ? InLandmarks(Node(best)!).Origin : Vector3.Zero)} meshes {string.Join(",", holder.FindChildren("*", "MeshInstance3D", true, false).Select(m => m.Name + ":" + ((MeshInstance3D)m).VisibilityRangeBegin + "-" + ((MeshInstance3D)m).VisibilityRangeEnd + ":" + ((MeshInstance3D)m).Visible))}");
            bool torch = kind == "torch_mounted";
            if (best == null && torch && OwnProps.For(Data.Id)?.Lit is { } own0 && own0.Exists(p => new Vector2(at.X - p.X, at.Z - p.Y).Length() < 1.2f))
            {
                // A torch of the zone's own (props_own.json "lit", E7b: the Watch-post's): its flame and its own small light.
                var tf = FlameKit.Add(holder, Vector3.Zero, FlameKind.Torch, false, 0.8f, light: true);
                // (props_own.json "lit_light": its pool on the ground under it, E7b r3)
                if (own0 is { } && OwnProps.For(Data.Id)?.LitLight is { } ll && tf.Light is { } tl)
                {
                    if (ll.Color is Color lc) tl.LightColor = lc;
                    if (ll.Range > 0) tl.OmniRange = ll.Range;
                    if (ll.Att > 0) tl.OmniAttenuation = ll.Att;
                    tf.Energy *= ll.Energy;
                    tl.LightEnergy = tf.Energy;
                }
                tf.Transform = InLandmarks(holder).AffineInverse() * new Transform3D(Basis.Identity, at);
                foreach (var c in tf.FindChildren("*", "MeshInstance3D", true, false))
                    if (c is MeshInstance3D card && card.Mesh?.SurfaceGetMaterial(0) is ShaderMaterial fm)
                    {
                        fm.SetShaderParameter("soft", LampSoft);
                        fm.SetShaderParameter("intensity", (float)fm.GetShaderParameter("intensity") * 2f);
                    }
                Lamps.Inner(holder, at + Vector3.Up * FlameKit.Spec(FlameKind.Torch).H * 0.8f * 0.35f, false, FlameKit.Spec(FlameKind.Torch).H * 0.8f * 0.75f);
                tf.Visible = Night;
                Lamps.SetLit(holder, Night);
                ownTorches.Add((holder, tf));
                continue;
            }
            if (best == null) { Lamps.SetLit(holder, false); continue; }
            int li = glowLight[best];
            LampFlame(best, li, at, torch ? FlameKind.Torch : FlameKind.Lamp, false, torch ? 0.8f : HolderLampScale, holder);
            if (!torch) { lights[li].LightColor = new Color(LampColor); lights[li].OmniRange = LampRange; lights[li].OmniAttenuation = LampAtt; }
            specs[li] = specs[li] with { Intensity = specs[li].Intensity * LampEnergy };
            // (Low Ford r1) a lantern hung at head height (the post's, its flame 2.1 m up): at the falloff's 2 her head, half a
            // metre under it, took 18 times the ground's light and blew out white; a flatter falloff, the ground's pool held
            if (kind == "post_lantern") { lights[li].OmniAttenuation = PostLampAtt; specs[li] = specs[li] with { Intensity = specs[li].Intensity * PostLampEnergy }; }
            // A lamp of the zone's own (props_own.json "lamps", by its glow node): the camp's lantern burns amber, not the road's pale warm.
            if (OwnProps.For(Data.Id)?.Lamps.GetValueOrDefault(best) is OwnProps.Lamp own)
            {
                if (own.Color is Color oc) lights[li].LightColor = oc;
                if (own.Range > 0) lights[li].OmniRange = own.Range;
                if (own.Att > 0) lights[li].OmniAttenuation = own.Att;
                // (E8 later) "spec": its specular share (the gate torches' 0.5 caught each cobble's crown, a pool ragged stone by stone)
                if (own.Spec >= 0) lights[li].LightSpecular = own.Spec;
                specs[li] = specs[li] with { Intensity = specs[li].Intensity * own.Energy };
                if (own.Day < 1) dayDim[li] = own.Day;
            }
            lights[li].LightEnergy = specs[li].Intensity / Mathf.Pi * (Night || !dayDim.TryGetValue(li, out var dd0) ? 1 : dd0);
            glowLight.Remove(best);
        }
        // (E9d) the wall lanterns by the doors: a flame and glass in the kit's cage, its light moved into it (ZoneView.Town)
        WireWallLanterns(meta, glowLight);
        // The Low Ford's three: the keeper's lamp-iron (the Warden carries the same) on each pylon, a low blue flame.
        if (meta.Refs.ValueKind == System.Text.Json.JsonValueKind.Object && meta.Refs.TryGetProperty("pylons", out var pylons) && Lamps.Of("ford_lamp") is Lamps.Info ford)
        {
            int k = 0;
            foreach (var p in pylons.EnumerateArray())
            {
                string flame = p.GetProperty("flame").GetString()!;
                int li = p.GetProperty("light").GetInt32();
                if (li < 0 || li >= lights.Count || Lamps.Holder("ford_lamp", coldGlass: true) is not Node3D lamp) continue;
                // "top" is the floor of the web game's iron dish on the pylon (0.1 m over the stone): the dish goes
                // (lit from over it, its metal flared to a white octagon) and the lamp stands on the stone.
                var foot = new Vector3(p.GetProperty("x").GetSingle(), p.GetProperty("top").GetSingle() - 0.1f, p.GetProperty("z").GetSingle());
                foreach (var c in Landmarks.Root.GetChildren())
                    if (c is MeshInstance3D dish && !dish.Name.ToString().StartsWith("kk-") && (dish.Transform * dish.GetAabb()) is var box
                        && new Vector2(box.GetCenter().X - foot.X, box.GetCenter().Z - foot.Z).Length() < 0.3f && box.Position.Y > foot.Y - 0.2f && box.End.Y < foot.Y + 0.6f && box.Size.X < 1.4f)
                        dish.Visible = false;
                lamp.Position = foot;
                if (SurvivorUnchained.Args.Has("lamp-debug"))
                    foreach (var c in Landmarks.Root.GetChildren())
                        if (c is Node3D n3 && new Vector2(n3.Position.X - foot.X, n3.Position.Z - foot.Z).Length() < 2.5f)
                            GD.Print($"FORDDBG {k} foot {foot} near {n3.Name} {n3.GetType().Name} at {n3.Position} vis {n3.Visible} {(n3 is VisualInstance3D vi ? vi.GetAabb().ToString() : "")}");
                lamp.Name = $"ford_lamp-{k++}";
                Landmarks.Root.AddChild(lamp);
                Landmarks.Nodes[lamp.Name] = lamp;
                var at = foot + ford.Flame;
                LampFlame(flame, li, at, FlameKind.Lamp, true, FordFlame, lamp);
                // Its light in the cage with the flame (over it, 0.8 m up, it lit the cap's outside white). The lamp's
                // iron base would shade the stone under it; lamps cast no shadow, so the pylon is kept out of its own
                // lamp's light instead (it flared the stone's top to a pale square): the pylon on a layer of its own.
                foreach (var c in Landmarks.Root.GetChildren())
                    if (!FordPylonLit && c is Node3D pillar && pillar.Name.ToString().StartsWith("kk-halloween-pillar")
                        && new Vector2(pillar.Position.X - foot.X, pillar.Position.Z - foot.Z).Length() < 0.6f)
                        foreach (var m in pillar.FindChildren("*", "GeometryInstance3D", true, false)) ((GeometryInstance3D)m).Layers = LampLayer;
                // E7 round 2: our own pier (OwnProps preset "pylon": painted dressed stone, tools/assets/env_props.py) for the
                // code-made pillar, which read as a flat black slab at night under a capital its lamp flared white; the pier
                // is kept out of its own lamp's light (its top is under the lamp's foot) and shows by the moon.
                if (!SurvivorUnchained.Args.Has("ford-pier-off"))
                    foreach (var c in Landmarks.Root.GetChildren())
                        if (c is Node3D pillar && pillar.Name.ToString().StartsWith("kk-halloween-pillar")
                            && new Vector2(pillar.Position.X - foot.X, pillar.Position.Z - foot.Z).Length() < 0.6f
                            && OwnProps.Fitted("pylon", new Aabb(new Vector3(-0.5f, 0, -0.5f), new Vector3(1, 4.4f, 1))) is Node3D pier)
                        {
                            foreach (var m in pillar.FindChildren("*", "GeometryInstance3D", true, false)) ((GeometryInstance3D)m).Visible = false;
                            pillar.AddChild(pier);
                            // (C03 env fix: the pier casts no key shadow, moon or dawn: a 0.9 m box 4.4 m tall, its shadow crossed
                            // the water unseen and fell on the north bank as a hard dark parallelogram that read as a black slab
                            // lying by the ford (c03 s12, both under the moon and as s12 blends to dawn); it stands in the water,
                            // its foam ring grounds it. '--ford-pier-shadow' casts it, for comparison)
                            foreach (var m in pier.FindChildren("*", "GeometryInstance3D", true, false))
                            {
                                ((GeometryInstance3D)m).Layers = LampLayer;
                                if (!SurvivorUnchained.Args.Has("ford-pier-shadow")) ((GeometryInstance3D)m).CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                            }
                        }
                lights[li].LightCullMask &= ~LampLayer;
                lights[li].LightColor = new Color(FordColor);
                lights[li].LightSpecular = FordSpecular;
                lights[li].OmniRange = FordRange;
                lights[li].OmniAttenuation = FordAtt;
                specs[li] = specs[li] with { At = at + Vector3.Up * FordLightUp, Intensity = specs[li].Intensity * FordEnergy };
                lights[li].Position = specs[li].At;
                lights[li].LightEnergy = specs[li].Intensity / Mathf.Pi;
            }
        }
    }

    void LampFlame(string glow, int light, Vector3 at, FlameKind kind, bool cold, float scale, Node3D holder)
    {
        if (Node(glow) is not Node3D g) return;
        // The ball goes (the node may be the ball's mesh itself, its flame under it, so its mesh is taken, not it hidden).
        if (g is MeshInstance3D self) self.Mesh = null;
        foreach (var c in g.GetChildren()) if (c is GeometryInstance3D m) m.Visible = false;
        var f = FlameKit.Add(g, Vector3.Zero, kind, cold, scale, light: false);
        f.Transform = InLandmarks(g).AffineInverse() * new Transform3D(Basis.Identity, at);
        WireFlame(f, light, at, kind, cold, scale, holder);
    }

    /// <summary>A lamp's flame cards tuned for the play camera, driving its zone light, its holder lit from inside and
    /// lit with the light (LampFlame; ZoneView.Town's night lamps).</summary>
    void WireFlame(Flame f, int light, Vector3 at, FlameKind kind, bool cold, float scale, Node3D holder)
    {
        // In a cage the burner is a hand behind the flame: the kit's soft edge (0.15 m) faded it to nothing.
        foreach (var c in f.FindChildren("*", "MeshInstance3D", true, false))
            if (c is MeshInstance3D card && card.Mesh?.SurfaceGetMaterial(0) is ShaderMaterial fm)
            {
                fm.SetShaderParameter("soft", LampSoft);
                if (kind != FlameKind.Lamp) { fm.SetShaderParameter("intensity", (float)fm.GetShaderParameter("intensity") * 2f); continue; }
                fm.SetShaderParameter("intensity", (float)fm.GetShaderParameter("intensity") * LampFlameK * (cold ? FordFlameK : 1f));
                // From the play camera (23 m, 55 degrees down) an upright card is a sliver: leaned back toward the
                // camera, wider than the sim's tongue, its core band broader, so it reads as a bright point.
                fm.SetShaderParameter("tilt", cold ? FordTilt : LampTilt);
                fm.SetShaderParameter("core_lo", cold ? FordCore : LampCore);
                if (cold) { fm.SetShaderParameter("body_k", FordBody); fm.SetShaderParameter("core_k", FordCoreK); }
                fm.SetShaderParameter("pull", LampPull);
                if (cold) fm.SetShaderParameter("core_blue", FordCoreBlue);
                fm.RenderPriority = 1;
                card.Scale = card.Scale with { X = card.Scale.X * (cold ? FordWide : LampWide) };
            }
        f.Drive(lights[light]);
        // Its iron lit from inside (the zone's light leaves the holder out): the flame's middle, a radius by its size.
        float fh = FlameKit.Spec(kind).H * scale;
        Lamps.Inner(holder, at + Vector3.Up * fh * 0.35f, cold, fh * 0.75f);   // (the zone isn't in the tree yet: its own frame, at its origin)
        lampFlames.Add((light, f));
        driven.Add(light);
        if (!cold) dayLamps.Add(light);
        foreach (var m in holder.FindChildren("*", "GeometryInstance3D", true, false)) { ((GeometryInstance3D)m).Layers = LampLayer; if (SurvivorUnchained.Args.Has("lamp-nocage")) ((GeometryInstance3D)m).Visible = false; }
        lights[light].LightCullMask &= ~LampLayer;
        if (!lampGlass.TryGetValue(light, out var list)) lampGlass[light] = list = new();
        list.Add(holder);
    }

    public Node3D? Node(string name) => Landmarks.Nodes.TryGetValue(name, out var n) ? n : null;

    public bool IsLit(int light) => lit[light];

    /// <summary>A light on or off, its glowing bits and its fire with it.</summary>
    public void SetLit(int light, bool on)
    {
        // --lights-off/--lights-on I,J (pictures): a light held off or on (a lamp's pool with the camp fire out).
        if (ForcedOff.Contains(light)) on = false;
        else if (ForcedOn.Contains(light)) on = true;
        lit[light] = on;
        // (E9d) a lamp held cold by the day: its light, flame and glass out, whatever it was set to (ZoneView.Town)
        if (DayCold(light)) on = false;
        lights[light].Visible = on;
        OfferShadow(light);
        if (flames.TryGetValue(light, out var flame)) flame.Visible = on;
        if (light < Data.Meta.Lights.Count)
            foreach (var g in Data.Meta.Lights[light].Glow) if (Node(g) is Node3D n) n.Visible = on && !fireGlow.Contains(g);
        foreach (var (l, fire) in fires) if (l == light) Burn(fire, on);
        if (lampGlass.TryGetValue(light, out var holders)) foreach (var h in holders) Lamps.SetLit(h, on);
        foreach (var (l, p) in moths) if (l == light) p.Emitting = on && Night;
    }

    static void Burn(Node3D fire, bool on)
    {
        fire.Visible = on;
        foreach (var c in fire.GetChildren()) if (c is GpuParticles3D p) p.Emitting = on;
    }

    /// <summary>The shining light nearest a place, within so far (creation's portrait takes the fire's
    /// light off her face, and lays its own warm edge in its place). Shining, not lit: a light no one
    /// has lit or put out shines as it was made, and creation's campfire, never lit, was passed over,
    /// so the fire still lit her face from below at the close-up, its reflection a white blob as big
    /// as her pupil low on each iris.</summary>
    public OmniLight3D? LightNear(Vector3 at, float within)
    {
        OmniLight3D? best = null;
        float d = within;
        for (int i = 0; i < lights.Count; i++)
        {
            if (!lights[i].IsVisibleInTree()) continue;
            float di = lights[i].GlobalPosition.DistanceTo(at);
            if (di < d) { d = di; best = lights[i]; }
        }
        return best;
    }

    /// <summary>After dark or not: night-only pieces show, moths come to the
    /// lamps, chimney smoke goes dark.</summary>
    public void SetNight(bool on)
    {
        Night = on;
        foreach (var n in Data.Meta.NightNodes) if (Node(n) is Node3D node) node.Visible = on;
        foreach (var (l, p) in moths) p.Emitting = on && lit[l];
        foreach (var c in chimneys) PlumeLook(c, on);
        foreach (var (h, f) in ownTorches) { f.Visible = on; Lamps.SetLit(h, on); }
        foreach (var (li, dk) in dayDim) if (li < lights.Count && li < specs.Count) lights[li].LightEnergy = specs[li].Intensity / Mathf.Pi * (on ? 1 : dk);
        Shadows();
    }

    /// <summary>(lf5p) The zone's own lamps dimmed when it is not night (props_own.json "lamps" "day"): by the light's index.</summary>
    readonly Dictionary<int, float> dayDim = new();

    bool dusk, lampShadows = SurvivorUnchained.Play.Graphics.Current.LampShadows && !SurvivorUnchained.Args.Has("lamp-shadows-off");   // (--lamp-shadows-off: pictures)

    /// <summary>Whether it is dusk (the game's clock): the lamps cast shadows then, as by night.</summary>
    public void SetDusk(bool on)
    {
        dusk = on;
        Shadows();
    }

    /// <summary>The big lamps and fires cast shadows only at dusk and by night
    /// (the owner's call): by day their light is faint beside the sun's, and
    /// in town their shadows were two thirds of every frame's shadow draws.
    /// Never at the lowest quality.</summary>
    /// <summary>(E9d r3) Lights never offered a shadow: the town's braziers (ZoneView.Town.TownFire).</summary>
    readonly HashSet<int> unshadowed = new();
    bool CastsShadow(ZoneData.LightSpec l) => l.Intensity >= 8 && lampShadows && (Night || dusk);

    void Shadows()
    {
        for (int i = 0; i < lights.Count; i++) OfferShadow(i);
    }

    /// <summary>A light that may cast a shadow, and is lit, is offered to the one-shadow arbiter
    /// (ShadowLamp); otherwise withdrawn.</summary>
    void OfferShadow(int i)
    {
        if (i >= specs.Count || i >= lights.Count || i >= lit.Count) return;
        if (lit[i] && CastsShadow(specs[i]) && !unshadowed.Contains(i)) ShadowLamp.Offer(lights[i], 0);
        else ShadowLamp.Withdraw(lights[i]);
    }

    public override void _ExitTree()
    {
        foreach (var l in lights) ShadowLamp.Withdraw(l);
    }

    /// <summary>How far the blight has drawn back (0..1): the ground's veins
    /// and the grass (the Verge's water is the runtime's).</summary>
    public void SetHeal(float heal)
    {
        healed = heal;
        ground.SetShaderParameter("heal", heal);
        grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/heal", heal);
    }

    float healed;

    /// <summary>The kit pieces of a kind within r of a point, taken away in
    /// play (the strongbox carried off, the crates rolled into the stream):
    /// each one's instance collapsed to nothing where it stood.</summary>
    public void HideProps(string id, float x, float z, float r)
    {
        // (our own props, OwnProps, stand one to a node)
        foreach (var n in props.GetChildren().OfType<Node3D>())
            if (n is not MultiMeshInstance3D && n.HasMeta("at1") && n.GetMeta("prop").AsString() == id
                && n.GetMeta("at1").AsVector3() is var o && new Vector2(o.X - x, o.Z - z).Length() < r) n.Visible = false;
        foreach (var mmi in props.GetChildren().OfType<MultiMeshInstance3D>())
        {
            if (!mmi.HasMeta("prop") || mmi.GetMeta("prop").AsString() != id) continue;
            var at = mmi.GetMeta("at").AsGodotArray<Vector3>();
            for (int i = 0; i < at.Count; i++)
                if (new Vector2(at[i].X - x, at[i].Z - z).Length() < r)
                    mmi.Multimesh.SetInstanceTransform(i, new Transform3D(new Basis(Vector3.Zero, Vector3.Zero, Vector3.Zero), at[i]));
        }
    }

    /// <summary>The fires' pits, (x, z, radius, 0), and our props' patches (OwnProps "bare": x, z, radius, how far out
    /// the grass thins, times it): bare of grass (the first four).</summary>
    readonly List<Vector4> pits = new();

    /// <summary>Every plant of the flora within r of a point taken away.</summary>
    static void Bare(Node3D flora, Vector3 at, float r)
    {
        foreach (var mmi in flora.GetChildren().OfType<MultiMeshInstance3D>())
        {
            var mm = mmi.Multimesh;
            for (int i = 0; i < mm.InstanceCount; i++)
            {
                var o = mm.GetInstanceTransform(i).Origin;
                if (new Vector2(o.X - at.X, o.Z - at.Z).Length() < r)
                    mm.SetInstanceTransform(i, new Transform3D(new Basis(Vector3.Zero, Vector3.Zero, Vector3.Zero), o));
            }
        }
    }

    /// <summary>Hide the low landmark pieces within `radius` of a point on
    /// the ground (what a fire's scanned pit replaces).</summary>
    void HideLandmarksNear(Vector3 at, float radius)
    {
        foreach (var n in Landmarks.Root.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi) continue;
            // Not yet in the tree: its place relative to the landmarks' root (at the origin).
            var t = Transform3D.Identity;
            for (Node? p = mi; p != null && p != Landmarks.Root; p = p.GetParent()) if (p is Node3D p3) t = p3.Transform * t;
            var box = t * mi.GetAabb();
            var c = box.GetCenter();
            // Only what lies on the ground (stones, logs), not what hangs over it (a pot).
            // (A stone turned on its side has a box taller than it is: 0.72 m for Lowford's.)
            if (new Vector2(c.X - at.X, c.Z - at.Z).Length() < radius && box.Size.Y < 0.8f && box.Size.X < radius * 2.2f && box.Position.Y < at.Y + 0.25f) mi.Visible = false;
        }
    }

    /// <summary>The meadow round a place, built once; it follows `at` (FollowGrass).</summary>
    public void GrowGrass(Vector2 at, float radius = 40)
    {
        grass?.QueueFree();
        leaves?.QueueFree();
        grass = Grass.Build(Data, at, radius, grassCell);
        if (pits.Count > 0 && grass.Multimesh.Mesh.SurfaceGetMaterial(0) is ShaderMaterial gm)
        {
            var bare = new Vector4[4];
            for (int i = 0; i < Mathf.Min(4, pits.Count); i++) bare[i] = pits[i];
            gm.SetShaderParameter("bare_at", bare);
        }
        grassAt = at;
        grassRadius = radius;
        AddChild(grass);
        // An arena's fallen leaves, following her as its grass does.
        leaves = Grass.Leaves(Data, at, radius, grassCell);
        if (leaves != null) AddChild(leaves);
    }

    float grassCell = 0.3f, grassRadius = 40;
    Vector2 grassAt;

    /// <summary>How far apart the meadow's tufts are (the picture's quality): regrown if it changed.</summary>
    public void GrassCell(float cell)
    {
        if (Mathf.IsEqualApprox(cell, grassCell)) return;
        grassCell = cell;
        if (grass == null) return;
        var centre = (Vector2)grass.Multimesh.Mesh.SurfaceGetMaterial(0).Get("shader_parameter/centre");
        GrowGrass(grassAt, grassRadius);
        FollowGrass(centre);
        if (healed != 0) SetHeal(healed);
    }

    /// <summary>Whether the big lamps may cast shadows (the picture's quality).</summary>
    public void LampShadows(bool on)
    {
        lampShadows = on;
        Shadows();
    }

    /// <summary>The meadow's middle, every frame: the shader moves the tufts.</summary>
    public void FollowGrass(Vector2 at)
    {
        grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);
        leaves?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);
    }

    public override void _Process(double delta)
    {
        time += delta;
        float t = (float)time;
        TownTick();
        if (SurvivorUnchained.Args.Has("lamp-debug") && (lampDebugAt ??= new Queue<float>(System.Array.ConvertAll((SurvivorUnchained.Args.Get("lamp-debug-at") ?? "9").Split(','), x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture)))).Count > 0 && t > lampDebugAt.Peek())
        {
            lampDebugAt.Dequeue();
            {
                var cam = GetViewport().GetCamera3D();
                GD.Print($"CAMDBG {cam?.GlobalPosition} mask {cam?.CullMask} fwd {-cam?.GlobalBasis.Z}");
                for (int q = 0; q < 3; q++)
                    if (Node($"ford_lamp-{q}") is Node3D fl)
                        foreach (var m in fl.FindChildren("*", "MeshInstance3D", true, false))
                            GD.Print($"FORDVIS {q} {m.Name} vit {((MeshInstance3D)m).IsVisibleInTree()} layers {((MeshInstance3D)m).Layers} at {((MeshInstance3D)m).GlobalPosition} range {((MeshInstance3D)m).VisibilityRangeBegin}-{((MeshInstance3D)m).VisibilityRangeEnd} dist {cam?.GlobalPosition.DistanceTo(((MeshInstance3D)m).GlobalPosition)}");
            }
            if (GetViewport().GetCamera3D() is Camera3D fc)
                for (int q = 0; q < 3; q++)
                    if (Node($"ford_lamp-{q}") is Node3D fl)
                    {
                        // The plinth top a hand toward the camera from the iron, and the pylon's face toward the camera 3 m under it.
                        var foot = fl.GlobalPosition;
                        var toCam = new Vector3(fc.GlobalPosition.X - foot.X, 0, fc.GlobalPosition.Z - foot.Z).Normalized();
                        var sb = new System.Text.StringBuilder($"FORDPTS {q} foot {foot}:");
                        foreach (var (nm, p3) in new[] { ("top35", foot + toCam * 0.35f), ("top20s", foot + toCam * 0.2f + toCam.Cross(Vector3.Up) * 0.3f), ("face1", foot + toCam * 0.55f + Vector3.Down * 1f), ("face2", foot + toCam * 0.55f + Vector3.Down * 2f), ("face3", foot + toCam * 0.55f + Vector3.Down * 3f), ("flame", foot + Vector3.Up * 0.33f), ("glass", foot + Vector3.Up * 0.45f + toCam * 0.2f), ("glassL", foot + Vector3.Up * 0.3f + toCam * 0.22f + toCam.Cross(Vector3.Up) * 0.13f), ("glassR", foot + Vector3.Up * 0.3f + toCam * 0.22f - toCam.Cross(Vector3.Up) * 0.13f), ("glassT", foot + Vector3.Up * 0.62f + toCam * 0.22f) })
                            sb.Append($" {nm}={fc.UnprojectPosition(p3).Round()}");
                        GD.Print(sb.ToString());
                    }
            if (GetViewport().GetCamera3D() is Camera3D pc)
                foreach (var (li, _) in lampFlames)
                {
                    var c = lights[li].GlobalPosition;
                    var sb = new System.Text.StringBuilder($"POOLDBG light {li} at {c}:");
                    foreach (var (dx, dz, nm) in new[] { (1f, 0f, "+x"), (-1f, 0f, "-x"), (0f, 1f, "+z"), (0f, -1f, "-z"), (0.7071f, 0.7071f, "+xz"), (-0.7071f, 0.7071f, "-xz"), (0.7071f, -0.7071f, "+x-z"), (-0.7071f, -0.7071f, "-x-z") })
                        foreach (var r in new[] { 0.5f, 1f, 4f })
                        {
                            var p = new Vector3(c.X + dx * r, Mathf.Max(Data.HeightAt(c.X + dx * r, c.Z + dz * r), Data.Meta.Places.TryGetValue("WATER_Y", out var wy) ? wy.GetSingle() : -99f), c.Z + dz * r);
                            var sp = pc.UnprojectPosition(p);
                            sb.Append($" {nm}{r}=({sp.X:0},{sp.Y:0},h{p.Y:0.00})");
                        }
                    GD.Print(sb.ToString());
                }
            foreach (var (li, fl) in lampFlames)
                GD.Print($"LAMPDBG light {li} lit {lit[li]} lvis {lights[li].IsVisibleInTree()} e {lights[li].LightEnergy:0.00} at {lights[li].GlobalPosition} flame {fl.GlobalPosition} fvis {fl.IsVisibleInTree()} scale {fl.GlobalBasis.Scale}");
        }
        // --lamp-trace S (pictures): each lamp light's energy every frame for 5 s from S seconds in (the flicker's measure).
        if (SurvivorUnchained.Args.Has("lamp-trace") && t >= SurvivorUnchained.Args.Num("lamp-trace", 10f) && t < SurvivorUnchained.Args.Num("lamp-trace", 10f) + 5f)
            GD.Print($"LAMPTRACE {t:0.0000} " + string.Join(" ", lampFlames.Select(q => $"{q.Light}={lights[q.Light].LightEnergy:0.00000}")));
        // --near X,Z,R with --lamp-debug (pictures): the landmarks' named nodes within R m of (X, Z), once.
        if (SurvivorUnchained.Args.Get("near") is string near && !nearDone && t > SurvivorUnchained.Args.Num("near-at", 5f))
        {
            nearDone = true;
            var q = System.Array.ConvertAll(near.Split(','), x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture));
            foreach (var (name, n) in Landmarks.Nodes)
                if (n.IsInsideTree() && new Vector2(n.GlobalPosition.X - q[0], n.GlobalPosition.Z - q[1]).Length() < q[2])
                    GD.Print($"NEAR {name} {n.GetType().Name} at {n.GlobalPosition} vis {n.IsVisibleInTree()} {(n is VisualInstance3D vi ? (n.GlobalTransform * vi.GetAabb()).ToString() : "")} kids {string.Join(",", n.GetChildren().Select(c => c.Name + ":" + c.GetType().Name))}");
            if (GetViewport().GetCamera3D() is Camera3D nc)
                foreach (var (name, n) in Landmarks.Nodes)
                    if (n.IsInsideTree() && new Vector2(n.GlobalPosition.X - q[0], n.GlobalPosition.Z - q[1]).Length() < q[2]) GD.Print($"NEARSCREEN {name} {nc.UnprojectPosition(n.GlobalPosition)}");
        }
        // The pump's wheel turns while the pump runs.
        if (!stopped.Contains("pump_wheel") && Node("pump_wheel") is Node3D wheel) wheel.RotateObjectLocal(Vector3.Right, (float)delta * 0.8f);
        // Every lit light's own flicker (the web game's formula).
        for (int i = 0; i < lights.Count; i++)
        {
            if (!lit[i]) continue;
            var l = specs[i];
            // (A lamp's light is flickered by its flame: FlameKit's Flame.Drive, in energy only.)
            if (l.Flicker <= 0 || driven.Contains(i)) continue;
            float ph = phases[i];
            var (level, rate) = levels.TryGetValue(i, out var lv) ? lv : (1f, 1f);
            float ft = t * rate;
            float f = 1 + (Mathf.Sin(ft * 8.3f + ph) * 0.5f + Mathf.Sin(ft * 19.7f + ph * 1.7f) * 0.3f + Mathf.Sin(ft * 3.1f + ph) * 0.2f) * l.Flicker;
            lights[i].LightEnergy = l.Intensity / Mathf.Pi * f * level;
            // Energy only, never position (look bible 10: the light bobbed 4 mm and the shadows swam), unless a
            // cinematic asks a burnt-down fire to sway (SetFire). --fire-trace: the fire's light per frame.
            lights[i].Position = l.At + Vector3.Down * lightDrop.GetValueOrDefault(i);
            if (lightSway.GetValueOrDefault(i) is float sw && sw > 0)
                lights[i].Position += sw * new Vector3(Mathf.Sin(t * 2.3f + ph) * 0.6f + Mathf.Sin(t * 5.9f + ph * 1.3f) * 0.4f,
                    Mathf.Sin(t * 3.7f + ph * 0.7f) * 0.3f, Mathf.Cos(t * 1.9f + ph) * 0.6f + Mathf.Sin(t * 4.7f + ph * 2.1f) * 0.4f);
            if (FireTrace && t >= 6 && t < 11 && fires.Exists(fr => fr.Light == i)) GD.Print($"FIRETRACE {Engine.GetProcessFrames()} {t:0.0000} {lights[i].LightEnergy:0.0000} {lights[i].Position.Y:0.0000}");
        }
    }
}
