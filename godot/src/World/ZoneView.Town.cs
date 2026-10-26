using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// (E9d) The town's light and life: the wall lanterns by every door (the kit's Lantern_Wall, where the web game
/// hung a glowing ball beside the cage) get glass, a flame in the cage and their light moved into it; the lamps
/// burn at dawn, dusk and by night and stand cold by day (Atmosphere.TownLit); the chimneys smoke in soft
/// plumes lit by the key (shaders/chimney_smoke). The lit windows are kit.gdshader's (town_lit).
/// </summary>
public partial class ZoneView
{
    /// <summary>The lights of the lamps (posts, wall lanterns) that go cold by day.</summary>
    readonly HashSet<int> dayLamps = new();
    bool lampsDay;
    /// <summary>--town-lamps-day: the lamps burn by day too (the old look), for pictures.</summary>
    static readonly bool LampsAllDay = SurvivorUnchained.Args.Has("town-lamps-day");
    /// <summary>--wall-lamp-energy K, --wall-lamp-range M: a wall lantern's light (the data's 4.5 over 8 m).</summary>
    static readonly float WallLampEnergy = SurvivorUnchained.Args.Num("wall-lamp-energy", 1.6f), WallLampRange = SurvivorUnchained.Args.Num("wall-lamp-range", 4.2f);
    /// <summary>The kit's Lantern_Wall cage in its own frame: its middle, the flame's foot (m).</summary>
    static readonly Vector3 CageMid = new(0, 0.29f, 0.808f), CageFoot = new(0, 0.13f, 0.808f);

    /// <summary>The wall lanterns: each light whose glowing ball hangs by a Lantern_Wall copy (within 1.1 m of its cage)
    /// takes a flame in the cage, a glass in it, and its light at the cage.</summary>
    void WireWallLanterns(ZoneMeta meta, Dictionary<string, int> unwired)
    {
        var cages = new List<(Vector3 Mid, Vector3 Foot, float Scale, MultiMeshInstance3D Mmi)>();
        foreach (var mmi in props.FindChildren("*", "MultiMeshInstance3D", true, false).OfType<MultiMeshInstance3D>())
        {
            if (mmi.GetMeta("prop", "").AsString() != "props/Lantern_Wall" || mmi.Multimesh is not MultiMesh mm) continue;
            var to = InZone(mmi);
            for (int i = 0; i < mm.InstanceCount; i++)
            {
                var at = to * mm.GetInstanceTransform(i);
                cages.Add((at * CageMid, at * CageFoot, at.Basis.Scale.Y, mmi));
            }
        }
        if (cages.Count == 0) return;
        foreach (var (g, li) in unwired.ToList())
        {
            if (Node(g) is not Node3D ball || li >= lights.Count) continue;
            var bp = InLandmarks(ball).Origin;
            int best = -1;
            float bd = 1.1f;
            for (int c = 0; c < cages.Count; c++) if (cages[c].Mid.DistanceTo(bp) is float d && d < bd) { bd = d; best = c; }
            if (best < 0) continue;
            var (mid, foot, s, mmi) = cages[best];
            // the cage's glass: a six-sided pane set inside its bars, the lamps' own lit glass
            var holder = new Node3D { Name = "wall_lamp_" + g };
            var glass = new MeshInstance3D
            {
                Name = "glass",
                Mesh = new CylinderMesh { TopRadius = 0.118f * s, BottomRadius = 0.112f * s, Height = 0.29f * s, RadialSegments = 6, Rings = 1, CapTop = false, CapBottom = false },
                MaterialOverride = Lamps.GlassOf(false),
                CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                Position = mid,
            };
            holder.AddChild(glass);
            Landmarks.Root.AddChild(holder);
            LampFlame(g, li, foot, FlameKind.Lamp, false, LampScale * 0.85f * s, holder);
            // the kit's cages (one MultiMesh, every door's) out of the lamps' light: lit from inside they flared pale
            mmi.Layers |= LampLayer;
            lights[li].LightColor = new Color(LampColor);
            lights[li].OmniRange = WallLampRange;
            lights[li].OmniAttenuation = LampAtt;
            specs[li] = specs[li] with { At = mid, Intensity = specs[li].Intensity * WallLampEnergy };
            lights[li].Position = mid;
            lights[li].LightEnergy = specs[li].Intensity / Mathf.Pi;
            unwired.Remove(g);
        }
    }

    Transform3D InZone(Node3D n)
    {
        var t = n.Transform;
        for (var p = n.GetParent(); p is Node3D q && p != this; p = p.GetParent()) t = q.Transform * t;
        return t;
    }

    /// <summary>The lamps follow the light: cold by day (no flame, dark glass, no light), burning when the town is lit.</summary>
    void TownTick()
    {
        if (Data.Id != "waystation" || LampsAllDay) return;
        bool day = SurvivorUnchained.View.Atmosphere.TownLit < 0.5f;
        if (day == lampsDay) return;
        lampsDay = day;
        foreach (var li in dayLamps) SetLit(li, lit[li]);
    }

    /// <summary>Whether a light is a lamp held cold by the day.</summary>
    bool DayCold(int light) => lampsDay && dayLamps.Contains(light);

    /// <summary>A chimney's plume: soft puffs rising, bent by the wind, opening and fading over 8 s (about 4 m up and
    /// 3 m downwind), lit by the key on one side (shaders/chimney_smoke). No shadow.</summary>
    public static GpuParticles3D Plume()
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.15f,
            Direction = new Vector3(0.15f, 1, 0.05f).Normalized(), Spread = 6, InitialVelocityMin = 0.75f, InitialVelocityMax = 0.95f,
            DampingMin = 0.08f, DampingMax = 0.12f, Gravity = new Vector3(0.16f, 0.02f, 0.05f),
            ScaleMin = 0.75f, ScaleMax = 1.0f, ScaleCurve = CurveOf((0, 0.7f), (0.35f, 1.9f), (1, 3.6f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -8, AngularVelocityMax = 8,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.6f, TurbulenceNoiseScale = 2.5f, TurbulenceInfluenceMin = 0.02f, TurbulenceInfluenceMax = 0.05f,
        };
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/chimney_smoke.gdshader") };
        var smoke = new GpuParticles3D
        {
            Name = "Chimney", Amount = 22, Lifetime = 8, ProcessMaterial = p, Preprocess = 8,
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = mat },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            VisibilityAabb = new Aabb(new Vector3(-3, -1, -3), new Vector3(9, 9, 6)),
        };
        PlumeLook(smoke, false);
        return smoke;
    }

    /// <summary>--smoke-density K: the plumes' cover, for pictures.</summary>
    static readonly float SmokeDensity = SurvivorUnchained.Args.Num("smoke-density", 0.55f);

    /// <summary>A plume by day (pale, warm where the key lights it) or by night (dark, thin).</summary>
    public static void PlumeLook(GpuParticles3D smoke, bool night)
    {
        if (smoke.DrawPass1 is not QuadMesh { Material: ShaderMaterial m }) { Campfire.ChimneyLook(smoke, night); return; }
        m.SetShaderParameter("lit_col", night ? new Color("#4a505e") : new Color("#e2dcd2"));
        m.SetShaderParameter("shade_col", night ? new Color("#22252e") : new Color("#77797f"));
        m.SetShaderParameter("density", SmokeDensity * (night ? 0.7f : 1f));
        m.SetShaderParameter("warm_key", night ? 0f : 0.55f);
        ((ParticleProcessMaterial)smoke.ProcessMaterial).ColorRamp = RampOf((0, new Color(1, 1, 1, 0)), (0.08f, new Color(1, 1, 1, 0.85f)), (0.45f, new Color(0.97f, 0.97f, 0.98f, 0.55f)), (1, new Color(0.94f, 0.95f, 0.97f, 0)));
    }

    static GradientTexture1D RampOf(params (float At, Color C)[] stops)
    {
        var g = new Gradient { Offsets = stops.Select(s => s.At).ToArray(), Colors = stops.Select(s => s.C).ToArray() };
        return new GradientTexture1D { Gradient = g };
    }

    static CurveTexture CurveOf(params (float At, float V)[] pts)
    {
        var c = new Curve { MaxValue = 8 };
        foreach (var (at, v) in pts) c.AddPoint(new Vector2(at, v));
        return new CurveTexture { Curve = c };
    }
}
