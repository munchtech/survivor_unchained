using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her rise: a blow that should have ended her does not (Cold, Then Not; Not Yet). It is
/// told in two beats in the world's slowed breath (Game slows it on Ev.Rise), as the
/// blessing's own line has it: "You go cold. Then the ember catches."
///
///   the cold     ice stands at her feet and frost glints on her;
///   the ember    (Cold, Then Not) a coal kindles in her chest and its fire goes out from her
///                over the ground as far as it burns: a ragged front of flame (fire_ring),
///                the ground left smouldering in a ring where it stops;
///   the answer   (Not Yet, the Order's word at the end of a watch) a watch-lamp over her
///                and the watch's hours (a painted dial) held round her, turning back.
///
/// A thin ring at her feet holds while she is untouchable and gutters as that runs out, so
/// the grace can be read without a bar. Every light here stays below the tone curve's knee
/// and is held off her by hero_clear, and no light is thrown on the crowd (a lit crowd of
/// the pale dead goes cream), so she is the thing seen getting up.
/// </summary>
public partial class BattleFx
{
    static readonly Color Rime = Hdr("#a8d8ff", 1.1f), WatchLamp = Hdr("#ffc870", 1.3f), RiseFire = new(1.15f, 0.3f, 0.04f);

    /// <summary>A rise drew this frame: its fire is drawn as the rise, not as a plain blast.</summary>
    bool rose;
    double graceFrom, graceUntil = -1, handFrom = -1;
    bool graceEmber;
    float handAngle;

    void Rise(Ev.Rise e)
    {
        rose = true;
        float gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        // The cold: ice standing at her feet, frost glinting on her. Brief: the fire is coming.
        float cold = e.Ember ? (float)Math.Max(0.06, e.Delay) : 0.11f;
        Erupt(e.X, e.Z, 0.4f, 1.0f, 10, SpikeKind.Ice, 0.45f, cold + 0.12f, IceDeep);
        for (int i = 0; i < 24; i++)
        {
            float a = R() * Mathf.Tau, h = 0.15f + R() * 1.55f, rr = 0.24f + R() * 0.14f;
            var on = ground + new Vector3(Mathf.Cos(a) * rr, h, Mathf.Sin(a) * rr);
            Sparks.Spawn(on, new Vector3(Mathf.Cos(a) * 0.15f, -0.2f, Mathf.Sin(a) * 0.15f), cold + 0.15f + R() * 0.1f, 0.06f + R() * 0.05f, Rime, IceDeep * 0.5f, 0.02f,
                sprite: i % 3 == 0 ? Sprites.Of("frost_star") : Sprites.Of("star"), spinV: 2);
        }
        // Her breath going out of her: cold rolling low over the ground.
        for (int i = 0; i < 6; i++)
        {
            float a = i / 6f * Mathf.Tau + R() * 0.4f;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Smoke.Spawn(ground + Vector3.Up * 0.25f + dir * 0.4f, dir * 2f, 0.45f, 0.45f, new Color(0.5f, 0.62f, 0.8f), new Color(0.35f, 0.45f, 0.62f), 1.1f, drag: 2.6f, alpha: 0.14f);
        }
        Cam?.AddTrauma(0.18f);

        graceFrom = time;
        graceUntil = time + Math.Max(0.5, e.Grace);
        graceEmber = e.Ember;
        var ev = e;
        if (e.Ember)
        {
            pending.Add((time + cold * 0.5, () => Kindle(ev)));
            pending.Add((time + cold, () => Catch(ev)));
        }
        else pending.Add((time + cold, () => Answer(ev)));
    }

    /// <summary>A coal kindling in her chest (small: it is over her).</summary>
    void Kindle(Ev.Rise e)
    {
        var chest = V(e.X, Y(e.X, e.Z) + 1.2, e.Z);
        Sparks.Spawn(chest, Vector3.Zero, 0.12f, 0.1f, RiseFire * 1.4f, RiseFire, 0.35f, sprite: Sprites.Of("ember_coal"), spinV: 1);
    }

    /// <summary>Cold, Then Not: the fire going out from her as far as it burns, a ragged front
    /// of flame racing over the ground (shaders/fire_ring.gdshader), burning down where it
    /// stops, the ground left smouldering in a ring.</summary>
    void Catch(Ev.Rise e)
    {
        float gy = Y(e.X, e.Z), r = (float)Math.Max(2, e.Radius);
        var ground = V(e.X, gy, e.Z);
        // Fast, so the crowd it burns is lit as it goes (its burning lands at once).
        Waves.Add(ground + Vector3.Up * 0.4f, r * 1.1f, FireRun, RiseFire, 0.6f);
        StartFire(ground, r);
        // The ember climbing her as she gets up: a few sparks wound up round her.
        for (int i = 0; i < 18; i++)
        {
            float a = i * 0.7f, h = i / 18f;
            var from = ground + new Vector3(Mathf.Cos(a) * 0.5f, 0.1f + h * 0.4f, Mathf.Sin(a) * 0.5f);
            var round = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a));
            Sparks.Spawn(from, round * 2f + Vector3.Up * (2.2f + h * 2), 0.5f + R() * 0.3f, 0.04f + R() * 0.02f, Ember, EmberDeep, 0.01f, -1, 0.8f);
        }
        // Embers thrown up off the wall of fire where it stops.
        int n = Math.Min(48, (int)(Mathf.Tau * r * 0.8f));
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, d = r * (0.85f + R() * 0.15f);
            double x = e.X + Mathf.Cos(a) * d, z = e.Z + Mathf.Sin(a) * d;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            pending.Add((time + FireRun * (0.7f + R() * 0.5f), () => Sparks.Spawn(V(x, Y(x, z) + 0.3, z), dir * (0.5f + R()) + Vector3.Up * (1.5f + R() * 2.5f),
                0.8f + R() * 0.8f, 0.035f + R() * 0.025f, Ember, EmberDeep, 0.01f, -0.6f, 1.2f)));
        }
        Scars.Add("scorch", ground, 1.4f, 6, 0);
        // The ring of ground it leaves smouldering, laid as the fire burns down.
        pending.Add((time + FireRun, () => Scars.Add("smoulder", ground, r * 1.05f, 7, 0)));
        // Its light low over the ground (the fire's, not hers), and soon gone.
        Flash(ground + Vector3.Up * 0.5f, new Color("#ff6a1a"), 5, 0.4f, r * 1.4f);
        Cam?.AddTrauma(0.4f);
    }

    const float FireRun = 0.3f, FireDown = 1.3f;
    /// <summary>How much of the fire square's half-width its front runs to (its tongues reach past it).</summary>
    const float FireRoom = 1.12f;
    /// <summary>Not Yet's dial: its outer ring's radius, and how high in the air it is held.</summary>
    const float Dial = 2.7f, DialUp = 1.0f;
    /// <summary>The rise's fire: where from, how far, since when; drawn on one square.</summary>
    (Vector3 At, float R, double From)? fire;
    MeshInstance3D? fireMesh;
    ShaderMaterial? fireMat;

    void StartFire(Vector3 at, float r)
    {
        if (fireMesh == null)
        {
            fireMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_ring.gdshader") };
            fireMesh = new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(2, 2) }, MaterialOverride = fireMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(fireMesh);
        }
        // Just over the ground: the dead stand in it, their feet hidden in the flame.
        fireMesh.Position = at + Vector3.Up * 0.22f;
        fireMesh.Scale = new Vector3(r * FireRoom, 1, r * FireRoom);
        fireMat!.SetShaderParameter("seed", R() * 100);
        // The front about two thirds of a metre deep, whatever its reach.
        fireMat.SetShaderParameter("width", 0.65f / (r * FireRoom));
        fireMesh.Visible = true;
        fire = (at, r, time);
        StepFire();
    }

    /// <summary>The fire's front running out (eased, as a blast's air is), then burning down
    /// where it stopped while the char behind it cools.</summary>
    void StepFire()
    {
        if (fire is not var (_, _, from) || fireMesh == null || fireMat == null) return;
        float t = (float)(time - from);
        if (t > FireRun + FireDown) { fire = null; fireMesh.Visible = false; return; }
        float k = Mathf.Clamp(t / FireRun, 0, 1), ease = 1 - (1 - k) * (1 - k) * (1 - k);
        float down = Mathf.Clamp((t - FireRun) / FireDown, 0, 1);
        fireMat.SetShaderParameter("front", (0.03f + 0.97f * ease) / FireRoom);
        fireMat.SetShaderParameter("fade", 1 - down * down);
        fireMat.SetShaderParameter("cool", down);
    }

    /// <summary>Not Yet: the Order's answer. A watch-lamp held over her; the watch's twelve
    /// hours on the ground round her, and its hand wound back.</summary>
    void Answer(Ev.Rise e)
    {
        float gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        var lamp = ground + Vector3.Up * 2.5f;
        Sparks.Spawn(lamp, Vector3.Up * 0.25f, 1.1f, 0.3f, WatchLamp * 0.7f, WatchLamp * 0.25f, 0.45f, sprite: Sprites.Of("light"));
        Sparks.Spawn(lamp, Vector3.Up * 0.25f, 1.1f, 0.8f, new Color(0.45f, 0.3f, 0.1f), new Color(0.15f, 0.09f, 0.03f), 1.1f, alpha: 0.6f);
        // The dial: the watch's hours painted in lamplight (marks.py's watch_dial2), held flat in
        // the air round her at the waist, turning back as a clock never does, its hand wound
        // back over it (StepRise). (On the ground, under a packed crowd, it was not seen.)
        Books.Spawn("watch_dial", ground + Vector3.Up * DialUp, Dial * 2 / 0.82f * 0.94f, 1.6f, new Color(1.7f, 1.4f, 1.05f, 1), flat: true, sizeEnd: Dial * 2 / 0.82f,
            angle: R() * Mathf.Tau, spin: -0.9f);
        handAngle = R() * Mathf.Tau;
        handFrom = time;
        // The cold lets go of her: the ice at her feet breaks outward.
        for (int i = 0; i < 18; i++)
        {
            float a = R() * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Sparks.Spawn(ground + Vector3.Up * (0.3f + R() * 0.8f) + dir * 0.4f, dir * (3 + R() * 3) + Vector3.Up * (1 + R() * 2), 0.4f + R() * 0.2f, 0.07f + R() * 0.05f, Rime, IceDeep * 0.5f, 0.02f, 10, 2,
                sprite: Sprites.Of("star"), spinV: 8);
        }
        Waves.Add(ground + Vector3.Up * 0.4f, Dial * 1.3f, 0.45f, WatchLamp, 0.6f);
        // The lamp's light falls on her ground, not across the crowd.
        Flash(lamp, new Color("#ffcf8a"), 5, 1.1f, 5);
        Cam?.AddTrauma(0.25f);
    }

    /// <summary>What a rise draws each frame: the watch's hand winding back, and the grace's
    /// ring at her feet while she is untouchable.</summary>
    void StepRise(Battle b, float dt)
    {
        StepFire();
        var p = b.Player;
        if (!p.Alive) { graceUntil = -1; handFrom = -1; return; }
        float gy = Y(p.X, p.Z);
        if (handFrom >= 0)
        {
            // Three hours wound back over its first third of a second, then held as it fades.
            float k = (float)((time - handFrom) / 0.35);
            if (k >= 3) handFrom = -1;
            else
            {
                // Angles in the ground's plane run clockwise on screen, so back is down.
                float a = handAngle - Mathf.Tau / 12 * 3 * Mathf.SmoothStep(0, 1, Mathf.Min(1, k));
                float fade = k < 1 ? 1 : 1 - (k - 1) / 2;
                var c = V(p.X, gy + DialUp, p.Z);
                var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Ribbons.Now(new[] { c + dir * 0.6f, c + dir * 1.4f, c + dir * 2.15f }, 0.13f, WatchLamp, 1.6f * fade, Ribbons.Style.Glow, new[] { 0.6f, 1f, 0.2f });
            }
        }
        if (time < graceUntil)
        {
            float left = (float)(graceUntil - time), into = (float)(time - graceFrom);
            // In over a breath; steady; guttering over its last half second.
            float energy = Mathf.Min(1, into / 0.15f) * (left > 0.6f ? 1 : (0.45f + 0.55f * Mathf.Abs(Mathf.Sin(left * 26))) * left / 0.6f);
            var col = graceEmber ? RiseFire : WatchLamp * 0.8f;
            const int N = 40;
            var pts = new Vector3[N + 1];
            for (int j = 0; j <= N; j++)
            {
                float a = j / (float)N * Mathf.Tau;
                pts[j] = V(p.X + Mathf.Cos(a) * 0.8f, gy + 0.08, p.Z + Mathf.Sin(a) * 0.8f);
            }
            Ribbons.Now(pts, 0.07f, col, energy, graceEmber ? Ribbons.Style.Flame : Ribbons.Style.Glow);
            // The ember's grace breathes a few sparks off the ring.
            if (graceEmber && R() < 0.35f)
            {
                float a = R() * Mathf.Tau;
                Sparks.Spawn(V(p.X + Mathf.Cos(a) * 0.8f, gy + 0.15, p.Z + Mathf.Sin(a) * 0.8f), new Vector3(0, 1.2f + R(), 0), 0.5f, 0.035f, Ember * energy, EmberDeep, 0.01f, -0.5f, 1.5f);
            }
        }
    }
}
