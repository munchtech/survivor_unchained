using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The horde on screen (the web game's render/crowd.ts): a body for every
/// creature the fight has, refilled every frame from the simulation. Which
/// clip a creature plays, and how far into it, is decided here; the
/// simulation only says what it is doing. The dead lie where they fell for
/// a while, then the ground takes them back.
///
/// Every body is its own skeleton here, pooled by kind of creature (the
/// web game bakes each kind to vertex-animation textures and draws a kind
/// in one call; that comes with the real creatures).
/// </summary>
public partial class CrowdView : Node3D
{
    const double RiseTime = 1.1;
    const double CorpseLie = 16, CorpseSink = 3;
    const int CorpseMax = 48;
    /// <summary>How many of one kind are drawn at once, nearest first.</summary>
    const int PerKind = 90;

    sealed class Body
    {
        public required Visuals.Spec Spec;
        public required Node3D Root;
        public PersonView? Person;
        public BeastRig? Beast;
        public readonly List<StandardMaterial3D> Mats = new();
        public int Enemy = -1;
        public double Seed = double.NaN;
        public string Clip = "";
        public double Phase, Facing;
        public bool Walking, Attacking, Corpse, Dying;
        public double Born;
        public Vector3 At;
    }

    readonly Dictionary<string, List<Body>> pools = new();
    readonly Dictionary<int, Body> byEnemy = new();
    readonly List<Body> corpses = new();
    readonly HashSet<int> seen = new();
    /// <summary>The dead already laid out (by pool slot, and the seed of who was in it).</summary>
    readonly Dictionary<int, double> laidOut = new();
    Battle? battle;
    double time, dt;

    public CrowdView() { Name = "Crowd"; }

    /// <summary>Build a few of each kind ahead (behind the fade), so the
    /// first wolf does not hitch the frame.</summary>
    public void Prepare(IEnumerable<string> visuals)
    {
        foreach (var v in visuals)
        {
            if (v.StartsWith("view:")) continue;
            var pool = Pool(v);
            while (pool.Count < 4) Release(Make(v));
        }
    }

    List<Body> Pool(string visual)
    {
        if (!pools.TryGetValue(visual, out var p)) pools[visual] = p = new List<Body>();
        return p;
    }

    Body Make(string visual)
    {
        var spec = Visuals.Of(visual);
        Body b;
        if (spec.Person != null)
        {
            var pv = new PersonView(spec.Person, spec.Arms, 0.8 * spec.Scale);
            b = new Body { Spec = spec, Root = pv, Person = pv };
            foreach (var mi in pv.Person.Meshes)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is StandardMaterial3D m) { m.EmissionEnabled = true; m.Emission = Colors.Black; b.Mats.Add(m); }
        }
        else
        {
            var rig = new BeastRig(spec.Beast ?? Colors.Gray, spec.Scale);
            b = new Body { Spec = spec, Root = rig, Beast = rig };
            b.Mats.AddRange(rig.Mats);
        }
        b.Root.Visible = false;
        AddChild(b.Root);
        Pool(visual).Add(b);
        return b;
    }

    Body? Acquire(string visual)
    {
        var pool = Pool(visual);
        int busy = 0;
        foreach (var b in pool)
        {
            if (b.Enemy < 0 && !b.Corpse) return b;
            if (b.Enemy >= 0) busy++;
        }
        // Full: the oldest corpse of this kind gets up for the living.
        if (busy >= PerKind) return null;
        foreach (var c in corpses)
            if (c.Spec.Key == visual) { corpses.Remove(c); c.Corpse = false; return c; }
        return Make(visual);
    }

    void Release(Body b)
    {
        if (b.Enemy >= 0 && byEnemy.TryGetValue(b.Enemy, out var mine) && mine == b) byEnemy.Remove(b.Enemy);
        b.Enemy = -1;
        b.Seed = double.NaN;
        b.Corpse = b.Dying = b.Attacking = false;
        b.Clip = "";
        b.Root.Visible = false;
    }

    public void Update(Battle b, Func<double, double, double> heightAt, double now)
    {
        if (b != battle)
        {
            battle = b;
            foreach (var pool in pools.Values) foreach (var body in pool) Release(body);
            corpses.Clear();
            byEnemy.Clear();
            laidOut.Clear();
        }
        dt = Math.Clamp(now - time, 0, 0.1);
        time = now;
        seen.Clear();
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Def.Visual.StartsWith("view:")) continue;
            Draw(e, heightAt);
        }
        // Whatever the fight let go of without a death to show goes back.
        var gone = new List<Body>();
        foreach (var (id, body) in byEnemy) if (!seen.Contains(id)) gone.Add(body);
        foreach (var body in gone) Release(body);
        DrawCorpses(heightAt);
    }

    void Draw(Enemy e, Func<double, double, double> heightAt)
    {
        // Its body already lies where it fell: the fight lets it go shortly.
        if (laidOut.TryGetValue(e.Id, out var was) && was == e.Seed) return;
        if (!byEnemy.TryGetValue(e.Id, out var body) || body.Seed != e.Seed)
        {
            if (body != null) Release(body);
            body = Acquire(e.Def.Visual);
            if (body == null) return;
            body.Enemy = e.Id;
            body.Seed = e.Seed;
            body.Phase = e.Seed * 7;
            body.Facing = e.Facing;
            byEnemy[e.Id] = body;
        }
        seen.Add(e.Id);
        var clips = body.Spec.Clips;
        double y = heightAt(e.X, e.Z);
        double speed = Math.Sqrt(e.Vx * e.Vx + e.Vz * e.Vz);
        // Walking or standing, with a margin between the two, so a creature
        // jostled at the edge of walking pace does not flicker between clips.
        body.Walking = speed > (body.Walking ? 0.2 : 0.45);
        double sc = e.Def.Scale ?? 1;
        string clip;
        double rate = 1;
        bool once = false;
        switch (e.State)
        {
            case EnemyState.Rising:
                clip = clips.Rise;
                once = true;
                rate = ClipLength(body, clip) / RiseTime;
                break;
            case EnemyState.Dying:
                // Burst apart: nothing is left to fall (the gore threw it).
                if (e.Burst) { body.Root.Visible = false; return; }
                clip = clips.Die;
                once = true;
                rate = Math.Max(1, ClipLength(body, clip) / (Ai.DieTime * 0.62));
                if (e.Disposition != Disposition.Ally && e.DieT >= Ai.DieTime - 0.12) { LayOut(body, e, y); return; }
                break;
            case EnemyState.Burrowed:
                clip = clips.Idle;
                y -= 1.3 * sc;
                break;
            case EnemyState.Surfacing:
                clip = clips.Rise;
                once = true;
                y -= Math.Clamp(e.StateT / 0.55, 0, 1) * 0.6 * sc;
                break;
            case EnemyState.Windup:
                clip = clips.Windup;
                break;
            case EnemyState.Casting:
                clip = clips.Cast ?? clips.Windup;
                break;
            case EnemyState.Lunging:
                clip = clips.Move;
                rate = 1.8;
                break;
            default:
                if (e.Anim == EnemyAnim.Attack && e.AnimT < ClipLength(body, clips.Attack))
                {
                    clip = clips.Attack;
                    once = true;
                    // A new swing starts the clip over.
                    if (!body.Attacking || e.AnimT < dt * 1.5) body.Clip = "";
                    body.Attacking = true;
                }
                else if (body.Walking)
                {
                    // Its walk run faster or slower with its pace.
                    clip = clips.Move;
                    rate = Math.Clamp(speed / Math.Max(0.5, e.Def.Speed), 0.6, 1.6);
                    body.Phase += dt * rate;
                }
                else clip = clips.Idle;
                break;
        }
        if (clip != clips.Attack) body.Attacking = false;
        // Turned toward where it is going when it walks, toward what it wants
        // when it stands or strikes; never in a single frame.
        bool free = e.State == EnemyState.Active && e.Anim != EnemyAnim.Attack;
        double aim = body.Walking && free ? Math.Atan2(e.Vz, e.Vx) : e.Facing;
        if (e.State != EnemyState.Dying)
        {
            double turn = Math.Atan2(Math.Sin(aim - body.Facing), Math.Cos(aim - body.Facing));
            body.Facing += turn * Math.Min(1, dt * (free ? 9 : 18));
        }
        // Struck: a squash and a flinch along the blow, gone with the flash.
        double f = e.State == EnemyState.Dying ? 0 : e.Flash;
        body.Root.Visible = true;
        body.Root.Position = new Vector3((float)(e.X + e.LastDx * f * 0.14), (float)y, (float)(e.Z + e.LastDz * f * 0.14));
        body.Root.Rotation = new Vector3(0, (float)(Math.PI / 2 - body.Facing), 0);
        body.Root.Scale = new Vector3((float)(sc * (1 + f * 0.1)), (float)(sc * (1 - f * 0.1)), (float)(sc * (1 + f * 0.1)));
        Play(body, clip, rate, once, e);
        Glow(body, e, f);
    }

    static double ClipLength(Body b, string clip)
    {
        if (b.Beast != null) return BeastRig.Length(clip);
        var lib = People.Clips();
        var name = People.Resolve(clip);
        return lib.HasAnimation(name) ? lib.GetAnimation(name).Length : 1;
    }

    void Play(Body b, string clip, double rate, bool once, Enemy e)
    {
        if (b.Beast != null)
        {
            double t = clip == b.Spec.Clips.Move ? b.Phase : clip == b.Spec.Clips.Die ? e.DieT * rate : e.State == EnemyState.Rising ? e.AnimT * rate : time + e.Seed * 9;
            if (clip == b.Spec.Clips.Attack) t = e.AnimT;
            b.Beast.Pose(clip, t);
            return;
        }
        var anim = b.Person!.Person.Anim;
        if (clip != b.Clip)
        {
            var name = People.Resolve(clip);
            b.Clip = clip;
            anim.Play(name, once ? 0.1 : 0.25, 1);
            // A crowd that does not all step in time.
            if (!once) anim.Seek((e.Seed * 13.7) % Math.Max(0.1, anim.CurrentAnimationLength), true);
        }
        anim.SpeedScale = (float)rate;
    }

    void Glow(Body b, Enemy e, double flash)
    {
        // A hit flashes warm; frost blues, fire reddens; the named burn.
        var c = new Color(1f, 0.78f, 0.55f) * (float)(flash * 0.9);
        if (e.Status.Has(StatusKind.Frozen)) c += new Color(0.25f, 0.45f, 0.7f);
        else if (e.Status[StatusKind.Chill] is { } chill) c += new Color(0.1f, 0.2f, 0.35f) * (float)Math.Min(1, chill.Stacks * 0.18);
        if (e.Status.Has(StatusKind.Burn)) c += new Color(0.5f, 0.16f, 0.02f) * (0.7f + 0.3f * Mathf.Sin((float)time * 13));
        if (e.Named != null) c += new Color(0.35f, 0.08f, 0.04f);
        else if (e.Elite) c += new Color(0.06f, 0.05f, 0.03f);
        if (e.Def.Visual == "risen_ally") c += new Color(0.04f, 0.12f, 0.06f);
        else if (e.Def.Visual == "wolf_spirit") c += new Color(0.3f, 0.4f, 0.6f);
        foreach (var m in b.Mats) m.Emission = c;
    }

    /// <summary>The body stays where it fell when the fight lets it go.</summary>
    void LayOut(Body b, Enemy e, double y)
    {
        laidOut[e.Id] = e.Seed;
        if (byEnemy.TryGetValue(b.Enemy, out var mine) && mine == b) byEnemy.Remove(b.Enemy);
        b.Enemy = -1;
        b.Corpse = true;
        b.Born = time;
        b.At = new Vector3((float)e.X, (float)y, (float)e.Z);
        foreach (var m in b.Mats) m.Emission = Colors.Black;
        if (b.Beast != null) b.Beast.Pose(b.Spec.Clips.Die, 99);
        corpses.Add(b);
        if (corpses.Count > CorpseMax) { var old = corpses[0]; corpses.RemoveAt(0); Release(old); }
    }

    void DrawCorpses(Func<double, double, double> heightAt)
    {
        for (int i = corpses.Count - 1; i >= 0; i--)
        {
            var c = corpses[i];
            double age = time - c.Born;
            if (age > CorpseLie + CorpseSink) { corpses.RemoveAt(i); Release(c); continue; }
            double k = Math.Clamp((age - CorpseLie) / CorpseSink, 0, 1);
            double sink = k * k * (3 - 2 * k);
            float sc = c.Root.Scale.Y;
            c.Root.Position = c.At with { Y = (float)(heightAt(c.At.X, c.At.Z) - sink * 1.1 * sc) };
        }
    }

    public override void _ExitTree()
    {
        corpses.Clear();
        byEnemy.Clear();
    }
}

/// <summary>A four-legged stand-in (a wolf, a boar) until the real
/// creatures come: a body, a head, four legs, moved by hand.</summary>
public partial class BeastRig : Node3D
{
    public readonly List<StandardMaterial3D> Mats = new();
    readonly Node3D body, head;
    readonly Node3D[] legs = new Node3D[4];
    readonly float s;

    public BeastRig(Color color, double scale)
    {
        var fur = new StandardMaterial3D { AlbedoColor = color, Roughness = 0.9f, EmissionEnabled = true, Emission = Colors.Black, RimEnabled = true, Rim = 0.4f, RimTint = 0.4f };
        var dark = new StandardMaterial3D { AlbedoColor = color.Darkened(0.45f), Roughness = 0.9f, EmissionEnabled = true, Emission = Colors.Black };
        Mats.Add(fur);
        Mats.Add(dark);
        s = (float)scale;
        body = new Node3D { Position = new Vector3(0, 0.62f * s, 0) };
        AddChild(body);
        body.AddChild(new MeshInstance3D { Mesh = new CapsuleMesh { Radius = 0.24f * s, Height = 1.15f * s, Material = fur }, Rotation = new Vector3(Mathf.Pi / 2, 0, 0) });
        head = new Node3D { Position = new Vector3(0, 0.14f * s, 0.62f * s) };
        body.AddChild(head);
        head.AddChild(new MeshInstance3D { Mesh = new SphereMesh { Radius = 0.17f * s, Height = 0.3f * s, Material = fur } });
        head.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.12f, 0.1f, 0.26f) * s, Material = dark }, Position = new Vector3(0, -0.04f * s, 0.2f * s) });
        for (int i = 0; i < 2; i++)
            head.AddChild(new MeshInstance3D { Mesh = new PrismMesh { Size = new Vector3(0.08f, 0.14f, 0.05f) * s, Material = dark }, Position = new Vector3((i == 0 ? -0.08f : 0.08f) * s, 0.16f * s, -0.02f * s) });
        body.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.03f * s, BottomRadius = 0.07f * s, Height = 0.5f * s, Material = fur }, Position = new Vector3(0, 0.05f * s, -0.72f * s), Rotation = new Vector3(-1.1f, 0, 0) });
        for (int i = 0; i < 4; i++)
        {
            legs[i] = new Node3D { Position = new Vector3((i % 2 == 0 ? -0.13f : 0.13f) * s, -0.08f * s, (i < 2 ? 0.36f : -0.36f) * s) };
            body.AddChild(legs[i]);
            legs[i].AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.06f * s, BottomRadius = 0.04f * s, Height = 0.56f * s, Material = dark }, Position = new Vector3(0, -0.26f * s, 0) });
        }
    }

    public static double Length(string clip) => clip switch { "attack" => 0.6, "die" => 0.9, "run" => 0.5, _ => 1.1 };

    /// <summary>A pose for a moment in a clip.</summary>
    public void Pose(string clip, double t)
    {
        float T = (float)t;
        body.Rotation = Vector3.Zero;
        head.Rotation = Vector3.Zero;
        switch (clip)
        {
            case "run":
            {
                float w = T * Mathf.Tau * 2.2f;
                for (int i = 0; i < 4; i++) legs[i].Rotation = new Vector3(Mathf.Sin(w + (i is 0 or 3 ? 0 : Mathf.Pi)) * 0.7f, 0, 0);
                body.Rotation = new Vector3(Mathf.Sin(w * 2) * 0.05f, 0, 0);
                break;
            }
            case "attack":
            {
                float k = Mathf.Clamp(T / 0.6f, 0, 1);
                float lunge = Mathf.Sin(k * Mathf.Pi);
                body.Rotation = new Vector3(0.25f * lunge, 0, 0);
                head.Rotation = new Vector3(0.5f * lunge, 0, 0);
                for (int i = 0; i < 4; i++) legs[i].Rotation = new Vector3((i < 2 ? -0.6f : 0.4f) * lunge, 0, 0);
                break;
            }
            case "die":
            {
                // Over onto its side, legs gone slack.
                float k = Mathf.Clamp(T / 0.9f, 0, 1);
                body.Rotation = new Vector3(0, 0, k * Mathf.Pi / 2);
                body.Position = body.Position with { Y = Mathf.Lerp(0.62f, 0.25f, k) * s };
                for (int i = 0; i < 4; i++) legs[i].Rotation = new Vector3(0.3f * k * (i % 2 == 0 ? 1 : -1), 0, 0);
                return;
            }
            default:
            {
                // Breathing, the head up and turning.
                body.Rotation = new Vector3(Mathf.Sin(T * 2.1f) * 0.02f, 0, 0);
                head.Rotation = new Vector3(Mathf.Sin(T * 0.7f) * 0.1f, Mathf.Sin(T * 0.43f) * 0.35f, 0);
                for (int i = 0; i < 4; i++) legs[i].Rotation = Vector3.Zero;
                break;
            }
        }
        body.Position = body.Position with { Y = 0.62f * s };
    }
}
