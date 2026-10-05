using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Looks a night's story asks for, read from its state (Game sets what they read):
///
///   the way out   where a won night lets her go: a band of cold light lying on the ground,
///                 breathing (a pulsing cream decal with a hard edge read as a hoop);
///   a fed fire    a story night's deadfall alight: flame standing the length of the dead tree,
///                 embers going up, and its flames sinking and smoking as its burning runs out (feed
///                 it). Its reach is its own light's (a flat disc of firelight out to the reach read as
///                 an orange circle painted on the ground);
///   a panting wolf "His age" and "She missed": the old wolf's breath smoking thick and pale in
///                 the cold, a puff with each pant, inside the opening's ring.
/// </summary>
public partial class BattleFx
{
    /// <summary>A story night's deadfalls, and the zone's fires (each deadfall burns at two, its
    /// light's), for the fed fires' look. Null where there are none.</summary>
    public IReadOnlyList<Deadfall>? Deadfalls;
    public IReadOnlyList<SurvivorUnchained.World.FireDef>? FireSpots;

    // The way out: where, how far, when it first and last pulsed.
    Vector3 wayAt;
    float wayReach;
    double waySeen = -10, wayFirst = -10;

    static readonly Color WayCold = new(0.2f, 0.4f, 1.0f);

    /// <summary>The way out's pulse (ArenaRun: a ring, unnamed, nobody's): drawn as its band of
    /// light instead of a decal. False for any other mark.</summary>
    bool WayOut(Ev.Telegraph e)
    {
        if (e.Hostile || e.Id != -1 || e.Shape != TelegraphShape.Ring || e.Faction != null || e.Kind != TelegraphKind.Blow || e.Label != null) return false;
        wayAt = V(e.X, Y(e.X, e.Z), e.Z);
        wayReach = (float)e.Radius;
        if (time - waySeen > 3) wayFirst = time;
        waySeen = time;
        return true;
    }

    /* ------------------------------------------------------------ fed fires -- */

    sealed class FireLook
    {
        public MeshInstance3D Mesh = null!;
        public ShaderMaterial Mat = null!;
        public float Burn, Ember, Smoke;
        public double Lit;
    }

    readonly Dictionary<int, FireLook> fireLooks = new();

    /// <summary>Each deadfall's fire this frame: its flames the length of the tree, by how much
    /// burning it has left; its embers; its smoke as it gutters; and a flare when it is fed.</summary>
    void StepDeadfalls(float dt)
    {
        if (Deadfalls == null || FireSpots == null)
        {
            if (fireLooks.Count > 0) { foreach (var f in fireLooks.Values) f.Mesh.QueueFree(); fireLooks.Clear(); }
            return;
        }
        foreach (var d in Deadfalls)
        {
            if (d.Light < 0) continue;
            // Its two fires (the trunk's and the brash's): the tree runs between them.
            Vector3? a = null, c = null;
            foreach (var s in FireSpots)
                if (s.Light == d.Light) { var p = new Vector3((float)s.X, (float)s.Y, (float)s.Z); if (a == null) a = p; else { c = p; break; } }
            if (a is not { } p0) continue;
            var p1 = c ?? p0 + new Vector3(0.01f, 0, 0);
            if (!fireLooks.TryGetValue(d.Light, out var look))
            {
                var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
                mat.SetShaderParameter("seed", R() * 100);
                mat.SetShaderParameter("segs", 48f);
                var mesh = new MeshInstance3D
                {
                    Mesh = Kept("firecards48", () => FireCards(48)), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                    CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
                };
                AddChild(mesh);
                fireLooks[d.Light] = look = new FireLook { Mesh = mesh, Mat = mat, Lit = d.Lit };
            }
            // Fed: lit, or fed again before it went out. It takes with a rush.
            if (d.Lit > look.Lit + 1) Fed(p0, p1);
            look.Lit = d.Lit;
            // Full while it has more than six seconds in it, then sinking toward out; a fire just
            // lit takes a moment to stand up.
            float want = d.Burning ? Mathf.Clamp((float)d.Lit / 6f, 0, 1) : 0;
            want = want > 0 ? 0.25f + 0.75f * want : 0;
            look.Burn += (want - look.Burn) * Mathf.Min(1, dt * (want > look.Burn ? 2.5f : 1.2f));
            var mid = (p0 + p1) / 2;
            var along = p1 - p0;
            float len = Mathf.Max(0.5f, along.Length());
            float turn = Mathf.Atan2(along.Z, along.X);
            look.Mesh.Visible = look.Burn > 0.02f;
            if (!look.Mesh.Visible) continue;
            // The ring of cards pressed flat to a line along the trunk and a little past each end, so
            // its flames stand up out of the tree. (Half a metre across, it was a hoop of flame round
            // the log with the log lying cold inside it.)
            float reachAlong = len / 2 + 0.45f, reachAcross = 0.1f;
            look.Mesh.Position = new Vector3(mid.X, Y(mid.X, mid.Z) - 0.05f, mid.Z);
            look.Mesh.Basis = new Godot.Basis(Vector3.Up, -turn) * Godot.Basis.FromScale(new Vector3(reachAlong, 0.9f + 1.9f * look.Burn, reachAcross));
            look.Mat.SetShaderParameter("cells", Mathf.Max(8, Mathf.Round(Mathf.Tau * Mathf.Sqrt((reachAlong * reachAlong + reachAcross * reachAcross) / 2) / 0.4f)));
            look.Mat.SetShaderParameter("burn", Mathf.Clamp(look.Burn * 1.1f, 0, 1));
            // Embers going up off the length of it.
            look.Ember += dt * 22 * look.Burn;
            while (look.Ember >= 1)
            {
                look.Ember -= 1;
                var at = p0 + along * R() + new Vector3((R() - 0.5f) * 0.5f, 0.3f + R() * 0.6f, (R() - 0.5f) * 0.5f);
                Sparks.Spawn(at, new Vector3((R() - 0.5f) * 0.6f, 1.6f + R() * 2.2f, (R() - 0.5f) * 0.6f), 1.0f + R() * 1.2f, 0.035f + R() * 0.035f, Ember, EmberDeep, 0.01f, -0.3f, 0.8f);
            }
            // Guttering (four seconds left or less): smoke rising thicker as the flame sinks.
            float gutter = d.Burning && d.Lit < 4 ? 1 - (float)d.Lit / 4f : 0;
            look.Smoke += dt * 5 * gutter;
            while (look.Smoke >= 1)
            {
                look.Smoke -= 1;
                var at = p0 + along * R() + new Vector3((R() - 0.5f) * 0.4f, 0.5f, (R() - 0.5f) * 0.4f);
                Smoke.Spawn(at, new Vector3((R() - 0.5f) * 0.3f, 0.9f + R() * 0.5f, (R() - 0.5f) * 0.3f), 1.8f, 0.35f, new Color(0.13f, 0.11f, 0.1f), new Color(0.07f, 0.06f, 0.06f), 1.3f, drag: 0.6f, alpha: 0.4f);
            }
        }
    }

    /// <summary>A deadfall taking: flame running the length of it, embers thrown up, its light.</summary>
    void Fed(Vector3 a, Vector3 b)
    {
        for (int i = 0; i < 40; i++)
        {
            var at = a + (b - a) * R() + Vector3.Up * 0.4f;
            Sparks.Spawn(at, new Vector3((R() - 0.5f) * 2.5f, 3 + R() * 4, (R() - 0.5f) * 2.5f), 0.8f + R() * 0.6f, 0.05f, Ember, EmberDeep, 0.01f, 3, 1.2f);
        }
        Flash((a + b) / 2 + Vector3.Up * 1.5f, new Color("#ff9a40"), 8, 0.8f, 9);
    }

    /// <summary>The way out's band of light, drawn in loot's batch as loot's light is (EndLoot).</summary>
    void StoryLights()
    {
        // It breathes while its pulse keeps coming (a second and a half after the last), and comes
        // only once the fall has landed, as its prompt does: at the night's peak it ringed her in
        // pale light over the column.
        float way = (float)(Mathf.Clamp(1 - (time - waySeen - 1.3) / 0.6, 0, 1) * Mathf.Clamp((time - wayFirst - 2.4) / 1.2, 0, 1));
        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.5f);
    }

    /* ------------------------------------------------------- a panting wolf -- */

    readonly List<(Enemy E, double Until, float Beat)> panting = new();

    /// <summary>An opening that is a wolf winded ("His age", "She missed"): his breath smokes while
    /// it lasts. (Combat's ask: "A pale-blue ring is round him, his breath smokes thick.")</summary>
    void Winded(Ev.Telegraph e)
    {
        if (e.Label is not ("His age" or "She missed") || b0 == null) return;
        Enemy? who = null;
        double best = 9;
        foreach (var o in b0.Enemies.Living())
        {
            if (!o.Boss && o.Named == null) continue;
            double dd = (o.X - e.X) * (o.X - e.X) + (o.Z - e.Z) * (o.Z - e.Z);
            if (dd < best) { best = dd; who = o; }
        }
        if (who != null) panting.Add((who, time + e.Duration, 0));
    }

    void StepPanting(float dt)
    {
        for (int i = panting.Count - 1; i >= 0; i--)
        {
            var (e, until, beat) = panting[i];
            if (time > until || !e.Alive) { panting.RemoveAt(i); continue; }
            beat += dt;
            // A pant every third of a second: each a puff of breath, thick and pale in the cold,
            // out of his jaws and rolling up and away.
            if (beat >= 0.3f)
            {
                beat -= 0.3f;
                float sc = (float)(e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual);
                var fwd = new Vector3(Mathf.Cos((float)e.Facing), 0, Mathf.Sin((float)e.Facing));
                var head = V(e.X, Y(e.X, e.Z), e.Z) + fwd * 0.62f * sc + Vector3.Up * 0.48f * sc;
                // (Two small puffs a pant were lost on the ground from thirty metres up.)
                for (int k = 0; k < 3; k++)
                    Smoke.Spawn(head + fwd * 0.12f * sc, fwd * (0.8f + R() * 0.6f) * sc + new Vector3((R() - 0.5f) * 0.4f, 0.45f + R() * 0.35f, (R() - 0.5f) * 0.4f),
                        1.1f + R() * 0.5f, 0.2f * sc, new Color(0.86f, 0.92f, 1.0f), new Color(0.62f, 0.68f, 0.8f), 0.75f * sc, drag: 1.8f, alpha: 0.6f);
            }
            panting[i] = (e, until, beat);
        }
    }
}
