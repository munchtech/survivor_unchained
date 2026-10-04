using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The horde on screen (the web game's render/crowd.ts): every creature the
/// fight has, drawn each frame from the simulation into one batch per kind
/// (Vat.cs: baked vertex animation, so a kind is one draw however many there
/// are). Which clip a creature plays, and how far into it, is decided here;
/// the simulation only says what it is doing. The dead lie where they fell
/// for a while, then the ground takes them back.
/// </summary>
public partial class CrowdView : Node3D
{
    const double RiseTime = 1.1;
    const double CorpseLie = 16, CorpseSink = 3;
    /// <summary>The most bodies left lying (fewer at the lower qualities).</summary>
    public int CorpseMax = 160;
    bool shadows = true;
    /// <summary>Whether the crowd casts shadows (not at the lowest quality).</summary>
    public bool Shadows
    {
        get => shadows;
        set
        {
            shadows = value;
            foreach (var c in crowds.Values) c.CastShadow = value ? GeometryInstance3D.ShadowCastingSetting.On : GeometryInstance3D.ShadowCastingSetting.Off;
        }
    }

    /// <summary>A creature's own walk clock and heading, kept between frames.</summary>
    sealed class Gait
    {
        public double Seed, Phase, Facing;
        public bool Walking;
        public bool Seen;
    }

    sealed record Corpse(string Visual, float X, float Z, float Facing, float Scale, Color Tint, float Glow, double Born);

    readonly Dictionary<string, VatCrowd> crowds = new();
    readonly Dictionary<int, Gait> gaits = new();
    readonly List<Corpse> corpses = new();
    readonly HashSet<(int, double)> laidOut = new();
    Battle? battle;
    double time, dt;
    int living;

    public CrowdView() { Name = "Crowd"; }

    /// <summary>How many are standing, and lying (for the log).</summary>
    public (int Living, int Dead) Counts => (living, corpses.Count);

    /// <summary>Bake the kinds a place will have ahead (behind the fade), so
    /// the first wolf does not hitch the frame.</summary>
    public void Prepare(IEnumerable<string> visuals)
    {
        foreach (var v in visuals) if (!v.StartsWith("view:")) Crowd(v);
    }

    VatCrowd Crowd(string visual)
    {
        if (crowds.TryGetValue(visual, out var c)) return c;
        c = new VatCrowd(Vat.Of(Visuals.Of(visual), this));
        if (!shadows) c.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
        AddChild(c);
        crowds[visual] = c;
        return c;
    }

    public void Update(Battle b, Func<double, double, double> heightAt, double now)
    {
        if (b != battle)
        {
            battle = b;
            gaits.Clear();
            corpses.Clear();
            laidOut.Clear();
        }
        dt = Math.Clamp(now - time, 0, 0.1);
        time = now;
        foreach (var c in crowds.Values) c.Begin();
        foreach (var g in gaits.Values) g.Seen = false;
        living = 0;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Def.Visual.StartsWith("view:", StringComparison.Ordinal)) continue;
            Draw(e, heightAt);
        }
        // The dead after the living.
        DrawCorpses(heightAt);
        foreach (var c in crowds.Values) c.End();
        // Whatever the fight let go of forgets its gait.
        if (gaits.Count > 2 * living + 64)
        {
            var gone = new List<int>();
            foreach (var (id, g) in gaits) if (!g.Seen) gone.Add(id);
            foreach (var id in gone) gaits.Remove(id);
        }
    }

    void Draw(Enemy e, Func<double, double, double> heightAt)
    {
        // Its body already lies where it fell: the fight lets it go shortly.
        if (laidOut.Contains((e.Id, e.Seed))) return;
        var crowd = Crowd(e.Def.Visual);
        var asset = crowd.Asset;
        if (!gaits.TryGetValue(e.Id, out var g) || g.Seed != e.Seed)
            gaits[e.Id] = g = new Gait { Seed = e.Seed, Phase = e.Seed * 7, Facing = e.Facing };
        g.Seen = true;
        string role = "idle";
        double t = e.AnimT, y = heightAt(e.X, e.Z);
        float dissolve = 0;
        double speed = Math.Sqrt(e.Vx * e.Vx + e.Vz * e.Vz);
        // Walking or standing, with a margin between the two, so a creature
        // jostled at the edge of walking pace does not flicker between clips.
        g.Walking = speed > (g.Walking ? 0.2 : 0.45);
        switch (e.State)
        {
            case EnemyState.Rising:
                role = "rise";
                t = e.AnimT * (asset.Duration("rise") / RiseTime);
                break;
            case EnemyState.Dying:
            {
                // Burst apart: nothing is left to fall (the gore threw it).
                if (e.Burst) return;
                role = "die";
                t = e.DieT * Math.Max(1, asset.Duration("die") / (Ai.DieTime * 0.62));
                // Summons fade; the rest fall and stay.
                if (e.Disposition == Disposition.Ally) dissolve = Smooth(e.DieT, Ai.DieTime * 0.55, Ai.DieTime);
                else if (e.DieT >= Ai.DieTime - 0.12) { LayOut(e, g.Facing); return; }
                break;
            }
            case EnemyState.Burrowed:
                role = "burrow";
                y -= 0.25;
                t = time + e.Seed * 3;
                break;
            case EnemyState.Surfacing:
                role = "rise";
                t = (0.55 - e.StateT) * 1.2;
                break;
            case EnemyState.Windup:
                role = "windup";
                t = time;
                break;
            case EnemyState.Casting:
                role = asset.Clips.ContainsKey("cast") ? "cast" : "windup";
                t = time;
                break;
            case EnemyState.Lunging:
                role = "move";
                t = time * 1.8 + e.Seed * 5;
                break;
            default:
                if (e.Anim == EnemyAnim.Attack && e.AnimT < asset.Duration("attack")) { role = "attack"; t = e.AnimT; }
                else if (g.Walking)
                {
                    // Its own walk clock, run faster or slower with its pace:
                    // time times pace would leap to a new pose at every change of speed.
                    // A walk whose pace is known keeps its feet on the ground at any size and speed.
                    role = "move";
                    double size = (e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual);
                    g.Phase += dt * (asset.Pace > 0
                        ? Math.Clamp(speed / (asset.Pace * size), 0.5, 1.8)
                        : Math.Clamp(speed / Math.Max(0.5, e.Def.Speed), 0.6, 1.6));
                    t = g.Phase;
                }
                else { role = "idle"; t = time + e.Seed * 9; }
                break;
        }
        // Turned toward where it is going when it walks, toward what it wants
        // when it stands or strikes; never in a single frame.
        bool free = e.State == EnemyState.Active && e.Anim != EnemyAnim.Attack;
        double aim = g.Walking && free ? Math.Atan2(e.Vz, e.Vx) : e.Facing;
        if (e.State != EnemyState.Dying)
        {
            double turn = Math.Atan2(Math.Sin(aim - g.Facing), Math.Cos(aim - g.Facing));
            g.Facing += turn * Math.Min(1, dt * (free ? 9 : 18));
        }
        float sc = (float)(e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual);
        // Struck: a squash, and a flinch along the blow, gone with the flash.
        float f = e.State == EnemyState.Dying ? 0 : (float)e.Flash;
        var at = new Vector3((float)(e.X + e.LastDx * f * 0.14), (float)y, (float)(e.Z + e.LastDz * f * 0.14));
        var basis = new Godot.Basis(Vector3.Up, (float)(Math.PI / 2 - g.Facing)) * Godot.Basis.FromScale(new Vector3(sc * (1 + f * 0.1f), sc * (1 - f * 0.1f), sc * (1 + f * 0.1f)));
        float frozen = e.Status.Has(StatusKind.Frozen) ? 1 : e.Status[StatusKind.Chill] is { } chill ? (float)Math.Min(0.5, chill.Stacks * 0.09) : 0;
        float burning = e.Status.Has(StatusKind.Burn) ? 1 : 0;
        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        // A kind's own colour on a shared rig, and a champion's Signs (combat's, agreed with animation).
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);
        if (e.Elite) { glow = Math.Max(glow, 0.05f); tint *= new Color(1.08f, 1.02f, 0.92f); }
        if (e.Named != null) { glow = 0.25f; tint *= new Color(1.3f, 0.75f, 0.6f); }
        if (e.Disposition == Disposition.Neutral && !e.Provoked) tint *= new Color(0.95f, 0.95f, 0.95f);
        crowd.Push(new Transform3D(basis, at), role, t, f, dissolve, frozen, burning, tint, glow);
        living++;
    }

    static float Smooth(double x, double lo, double hi)
    {
        double k = Math.Clamp((x - lo) / (hi - lo), 0, 1);
        return (float)(k * k * (3 - 2 * k));
    }

    /// <summary>The body stays where it fell when the fight lets it go.</summary>
    void LayOut(Enemy e, double facing)
    {
        if (!laidOut.Add((e.Id, e.Seed))) return;
        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);
        corpses.Add(new Corpse(e.Def.Visual, (float)e.X, (float)e.Z, (float)facing, (float)(e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual), tint, glow * 0.3f, time));
        while (corpses.Count > CorpseMax) corpses.RemoveAt(0);
    }

    void DrawCorpses(Func<double, double, double> heightAt)
    {
        corpses.RemoveAll(c => time - c.Born >= CorpseLie + CorpseSink);
        foreach (var c in corpses)
        {
            var crowd = Crowd(c.Visual);
            double age = time - c.Born;
            float sink = Smooth(age, CorpseLie, CorpseLie + CorpseSink);
            var at = new Vector3(c.X, (float)heightAt(c.X, c.Z) - sink * 1.1f * c.Scale, c.Z);
            var basis = new Godot.Basis(Vector3.Up, Mathf.Pi / 2 - c.Facing) * Godot.Basis.FromScale(Vector3.One * c.Scale);
            // Dead flesh greys a little as it lies.
            var tint = c.Tint * (1 - (float)Math.Min(0.25, age * 0.02));
            tint.A = 1;
            crowd.Push(new Transform3D(basis, at), "die", crowd.Asset.Duration("die") * 0.999, 0, sink > 0.6f ? (sink - 0.6f) * 2.5f : 0, 0, 0, tint, c.Glow);
        }
    }

    public override void _ExitTree()
    {
        corpses.Clear();
        gaits.Clear();
    }
}
