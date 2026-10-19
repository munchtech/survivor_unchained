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
    public readonly Landmarks Landmarks;
    readonly List<OmniLight3D> lights = new();
    readonly List<float> phases = new();
    readonly List<bool> lit = new();
    /// <summary>Every light's spec: the zone's, then those the runtime set down.</summary>
    readonly List<ZoneData.LightSpec> specs;
    readonly Dictionary<int, MeshInstance3D> flames = new();
    readonly Node3D lightRoot;
    readonly HashSet<string> stopped = new();
    readonly List<(int Light, Node3D Fire)> fires = new();
    readonly HashSet<string> fireGlow = new();
    readonly List<GpuParticles3D> chimneys = new();
    readonly List<(int Light, GpuParticles3D Moths)> moths = new();
    readonly ShaderMaterial ground;
    MultiMeshInstance3D? grass, leaves;
    readonly Node3D props;
    double time;
    public bool Night { get; private set; }

    /// <param name="grassAround">Where to grow the meadow (the web game grows
    /// it round the survivor as they go); null for none.</param>
    public ZoneView(ZoneData z, Vector2? grassAround = null, float grassRadius = 40)
    {
        Data = z;
        Name = $"Zone_{z.Id}";
        Perf.Lap("zone view", true);
        var g = Ground.Build(z);
        ground = (ShaderMaterial)g.Mesh.SurfaceGetMaterial(0);
        AddChild(g);
        AddChild(Water.Build(z));
        if (MistLayers.Build(z) is { } mist) AddChild(mist);
        Perf.Lap("ground and water");
        var flora = Dressing.Flora(z);
        AddChild(flora);
        // Nothing grows in a fire pit: neither the flora nor the meadow (GrowGrass).
        foreach (var f in z.Meta.Fires)
            if (f.Ring)
            {
                pits.Add(new Vector3((float)f.X, (float)f.Z, 0.95f * (float)f.Size));
                Bare(flora, new Vector3((float)f.X, (float)f.Y, (float)f.Z), 0.95f * (float)f.Size);
            }
        Perf.Lap("flora");
        props = Dressing.Props(z);
        AddChild(props);
        Perf.Lap("props");
        Landmarks = new Landmarks(z);
        AddChild(Landmarks.Root);
        // The camp on the Low Ford road, made for its close-ups (Camp.cs).
        if (z.Id == "lowford") AddChild(Camp.Dress(Landmarks.Root));
        Perf.Lap("landmarks");
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

        var meta = z.Meta;
        specs = new List<ZoneData.LightSpec>(z.Lights);
        lightRoot = new Node3D { Name = "Lights" };
        AddChild(lightRoot);
        for (int i = 0; i < meta.Lights.Count; i++) MakeLight(z.Lights[i]);
        var fx = new Node3D { Name = "Fires" };
        AddChild(fx);
        foreach (var f in meta.Fires)
        {
            // The web game's ring of stones round it goes; the fire's own ring takes its place.
            var fat = new Vector3((float)f.X, (float)f.Y, (float)f.Z);
            if (f.Ring) HideLandmarksNear(fat, 0.85f * (float)f.Size);
            var fire = Campfire.Build(fat, (float)f.Size, ring: f.Ring);
            fx.AddChild(fire);
            fires.Add((f.Light, fire));
            if (f.Light >= 0 && f.Light < lights.Count) lights[f.Light].LightCullMask &= ~Campfire.CoalLayer;
            // The web game marks a fire's flame with a glowing ball; here the
            // fire has flames of its own, and the ball would only bloom white.
            if (f.Light >= 0 && f.Light < meta.Lights.Count)
                foreach (var glow in meta.Lights[f.Light].Glow) { fireGlow.Add(glow); if (Node(glow) is Node3D ball) ball.Visible = false; }
        }
        // The lamps: modeled holders with the flame kit's flames in them (Lamps.cs, look bible 10), where
        // the web game hung glowing balls (the road's lanterns, the gate's torches, the ford's three beacons).
        WireLamps(meta);
        foreach (var c in meta.Chimneys)
        {
            var smoke = Campfire.ChimneySmoke();
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
        SetNight(false);
    }

    /// <summary>The zone's lights kept off her own layer (PlayerView.HerLayer: the close view by night), or given back.</summary>
    public void HerUnlit(bool off)
    {
        foreach (var l in lights) l.LightCullMask = off ? l.LightCullMask & ~PlayerView.HerLayer : l.LightCullMask | PlayerView.HerLayer;
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

    /// <summary>A light's shadow softened (its source "size" metres across; 0 is as built, hard):
    /// a cinematic's fire throws soft shadows, not razor spokes.</summary>
    public void SetSize(int light, float size)
    {
        if (light < 0 || light >= lights.Count) return;
        lights[light].LightSize = Mathf.Max(0, size);
    }

    /// <summary>How far a fire's light has sunk toward its coals (SetFire).</summary>
    readonly Dictionary<int, float> lightDrop = new();

    /// <summary>A fire's flames scaled (0: embers only); its embers and smoke stay.</summary>
    public void SetFire(int light, float flames)
    {
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
                lightDrop[light] = at.Y - Mathf.Lerp(fire.Position.Y + 0.18f, at.Y, Mathf.Clamp(flames, 0, 1));
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

    /// <summary>--lamp-energy K, --lamp-color HEX: the road lamps' light, for pictures (pools on the dirt).</summary>
    static readonly float LampEnergy = SurvivorUnchained.Args.Num("lamp-energy", 1.3f);
    // A paler warm than the web game's #ffa860: on the brown dirt that orange read as mud (E2 judges), this as lamplight.
    static readonly string LampColor = SurvivorUnchained.Args.Get("lamp-color") ?? "#ffc890";
    /// <summary>--lamp-soft M, --lamp-flame K: a lamp flame's soft edge and brightness, for pictures.</summary>
    static readonly float LampSoft = SurvivorUnchained.Args.Num("lamp-soft", 0.02f);
    static readonly float LampFlameK = SurvivorUnchained.Args.Num("lamp-flame", 2f);
    /// <summary>--ford-energy K: the ford lamps' light, for pictures.</summary>
    static readonly float FordEnergy = SurvivorUnchained.Args.Num("ford-energy", 1f);

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
            if (best == null) { Lamps.SetLit(holder, false); continue; }
            int li = glowLight[best];
            bool torch = kind == "torch_mounted";
            LampFlame(best, li, at, torch ? FlameKind.Torch : FlameKind.Lamp, false, torch ? 0.8f : 1.1f, holder);
            if (!torch) lights[li].LightColor = new Color(LampColor);
            specs[li] = specs[li] with { Intensity = specs[li].Intensity * LampEnergy };
            lights[li].LightEnergy = specs[li].Intensity / Mathf.Pi;
            glowLight.Remove(best);
        }
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
                lamp.Name = $"ford_lamp-{k++}";
                Landmarks.Root.AddChild(lamp);
                Landmarks.Nodes[lamp.Name] = lamp;
                var at = foot + ford.Flame;
                LampFlame(flame, li, at, FlameKind.Lamp, true, 1.6f, lamp);
                // Its light in the cage with the flame (over it, 0.8 m up, it lit the cap's outside white). The lamp's
                // iron base would shade the stone under it; lamps cast no shadow, so the pylon is kept out of its own
                // lamp's light instead (it flared the stone's top to a pale square): the pylon on a layer of its own.
                foreach (var c in Landmarks.Root.GetChildren())
                    if (c is Node3D pillar && pillar.Name.ToString().StartsWith("kk-halloween-pillar")
                        && new Vector2(pillar.Position.X - foot.X, pillar.Position.Z - foot.Z).Length() < 0.6f)
                        foreach (var m in pillar.FindChildren("*", "GeometryInstance3D", true, false)) ((GeometryInstance3D)m).Layers = LampLayer;
                lights[li].LightCullMask &= ~LampLayer;
                specs[li] = specs[li] with { At = at + Vector3.Up * 0.16f, Intensity = specs[li].Intensity * FordEnergy };
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
        // In a cage the burner is a hand behind the flame: the kit's soft edge (0.15 m) faded it to nothing.
        foreach (var c in f.FindChildren("*", "MeshInstance3D", true, false))
            if (c is MeshInstance3D card && card.Mesh?.SurfaceGetMaterial(0) is ShaderMaterial fm)
            {
                fm.SetShaderParameter("soft", LampSoft);
                fm.SetShaderParameter("intensity", (float)fm.GetShaderParameter("intensity") * LampFlameK);
            }
        f.Drive(lights[light]);
        driven.Add(light);
        foreach (var m in holder.FindChildren("*", "GeometryInstance3D", true, false)) ((GeometryInstance3D)m).Layers = LampLayer;
        lights[light].LightCullMask &= ~LampLayer;
        if (!lampGlass.TryGetValue(light, out var list)) lampGlass[light] = list = new();
        list.Add(holder);
    }

    public Node3D? Node(string name) => Landmarks.Nodes.TryGetValue(name, out var n) ? n : null;

    public bool IsLit(int light) => lit[light];

    /// <summary>A light on or off, its glowing bits and its fire with it.</summary>
    public void SetLit(int light, bool on)
    {
        lit[light] = on;
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
        foreach (var c in chimneys) Campfire.ChimneyLook(c, on);
        Shadows();
    }

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
        if (lit[i] && CastsShadow(specs[i])) ShadowLamp.Offer(lights[i], 0);
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
        foreach (var mmi in props.GetChildren().OfType<MultiMeshInstance3D>())
        {
            if (!mmi.HasMeta("prop") || mmi.GetMeta("prop").AsString() != id) continue;
            var at = mmi.GetMeta("at").AsGodotArray<Vector3>();
            for (int i = 0; i < at.Count; i++)
                if (new Vector2(at[i].X - x, at[i].Z - z).Length() < r)
                    mmi.Multimesh.SetInstanceTransform(i, new Transform3D(new Basis(Vector3.Zero, Vector3.Zero, Vector3.Zero), at[i]));
        }
    }

    /// <summary>The fires' pits, (x, z, radius): bare of grass.</summary>
    readonly List<Vector3> pits = new();

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
            for (int i = 0; i < Mathf.Min(4, pits.Count); i++) bare[i] = new Vector4(pits[i].X, pits[i].Y, pits[i].Z, 0);
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
            lights[i].Position = l.At + new Vector3(0, Mathf.Sin(t * 11 + ph) * 0.03f * l.Flicker - lightDrop.GetValueOrDefault(i), 0);
        }
    }
}
