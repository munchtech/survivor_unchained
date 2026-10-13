using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* Burns Twice (FLARE_LOOK §4): a fire lit on ice burns twice. The web lights and the light streams up into her staff
 * (the Draw), its head burns amber with a blue heart (the Hold); she drives the butt down and the ford's frost glazes
 * the whole reach in 0.4 s from her outward, fingered, the world's colour coming back cold behind it; she looks up and
 * twelve embers fall out of the night at one shared angle, each a molten streak with a smoke trail (the first few
 * carrying moving lights), and each impact throws turned tongues of flame, real ice shards, steam and char on the wet
 * frost, and shatters the frozen round it; the last lands on the toughest in reach with the full BOOM. Then steam
 * rises in columns, the frost melts back from its edges to wet and charred ground, the web glows under the melt and
 * sinks dark, and by six seconds the scars are gone. All of its art is its own (the owner: "flares should be unique"). */
public partial class FlareFx
{
    sealed class Ember
    {
        public Vector3 From, Target, Dir;
        public double Born, LandAt;
        public bool Landed, Last, Lit;
        /// <summary>Dropped on the fight's aim, falling for its blow: lands on the frame the blow comes (the hitstop,
        /// sound and kills on its landing frame), steered to where the blow fell if its target died meanwhile.</summary>
        public bool Aimed;
        /// <summary>Its fall's length: the aim's lead (lamps.json burns_twice "aim") or the view's own.</summary>
        public float FallT = Fall;
        public float Radius;
        public int Hitstop;
        public OmniLight3D? Light;
    }

    /// <summary>The embers' fall: 0.14 s at 110 m/s along one shared angle (the view lands each 0.14 s after the
    /// fight's blow; the bodies it kills are held standing until it lands).</summary>
    const float Fall = 0.26f, FallSpeed = 80;
    /// <summary>The fight's aim comes this long before its blow (lamps.json burns_twice beat "aim").</summary>
    const float AimFall = 0.2f;
    int embersLit;
    bool firstLanded;
    bool calledDown;

    /// <summary>The shared angle: out of the night from the upper left of the screen, never a vertical bar.</summary>
    Vector3 EmberDir(int i)
    {
        var right = Cam?.Camera.GlobalBasis.X ?? Vector3.Right;
        var fwd = -(Cam?.Camera.GlobalBasis.Z ?? Vector3.Forward);
        right.Y = 0; fwd.Y = 0;
        right = right.Normalized(); fwd = fwd.Normalized();
        var dir = Vector3.Down + right * 0.55f + fwd * 0.18f;
        // Called Down: a converging sheaf, each from its own side of the sky.
        if (calledDown)
        {
            float a = i * 2.39996f;
            dir = Vector3.Down + (right * Mathf.Cos(a) + fwd * Mathf.Sin(a)) * 0.6f;
        }
        return dir.Normalized();
    }

    void BurnsBlow(Ev.Flare e, Battle b)
    {
        if (e.Part == "frost")
        {
            // The butt meets the ground: the spend of the first beat.
            spendAt = t;
            calledDown = b.Lamps.FlareMods.Contains("burns.called_down");
            Hitstop(e.Hitstop);
            Cam?.Jolt(Vector3.Up, 0.2f * Motion);
            // A cold, low bounce light, no flash: its shadows throw every body outward along the ground.
            SpendLight(at + Vector3.Up * 0.6f, new Color(0.42f, 0.66f, 1f), 3.2f);
            Cue("frost", at, 1);
            Shots.Want("b4_frost0", 1 / 60.0);
            Shots.Want("b5_frost1", 0.1);
            Shots.Want("b6_frost3", 0.3);
            Rumble(0.6f, 0.3f, 0.12f);
            // The ice crackles up round her feet as it goes.
            for (int i = 0; i < 40; i++)
            {
                var p = at + new Vector3((R() - 0.5f) * 3, 0.05f, (R() - 0.5f) * 3);
                glow.Spawn(FlareBits.Kind.Mote, p, Vector3.Up * (0.5f + R()), 0.5f + R() * 0.4f, 0.03f + R() * 0.03f, new Color(0.45f, 0.75f, 1.2f), new Color(0.1f, 0.25f, 0.5f), drag: 2);
            }
            return;
        }
        if (e.Part == "aim") { Drop(e, b, aimed: true); return; }
        if (e.Part == "shove") { Shove(e, b); return; }
        if (e.Part != "ember") return;
        // The ember the aim dropped lands now, where the blow fell (classes: it may bend up to ~5.5 m off its aim when
        // its target died); without an aim (older data), it falls now and lands a fall later.
        var aimed = embers.FirstOrDefault(x => x.Aimed && !x.Landed);
        if (aimed != null)
        {
            aimed.Aimed = false;
            aimed.Target = WhereFalls(e, b);
            aimed.Hitstop = e.Hitstop;
            aimed.Radius = (float)e.Radius;
            aimed.LandAt = t;
            DoomUnder(aimed);
            return;
        }
        Drop(e, b, aimed: false);
    }

    /// <summary>Where an ember lands: the fight's blow, except the last word, which lands by her (2 m, toward its pack
    /// and away from the eye) so the BOOM is centred at every camera and its ring crosses the whole reach; on a boss or
    /// a champion it still lands on it (§1.6). (View only: what it kills where the fight aimed it breaks as the ring
    /// crosses it.)</summary>
    Vector3 WhereFalls(Ev.Flare e, Battle b)
    {
        var target = new Vector3((float)e.TX, (float)HeightAt(e.TX, e.TZ), (float)e.TZ);
        if (e.Last && !OnToughest(e, b))
        {
            var fwd = -(Cam?.Camera.GlobalBasis.Z ?? Vector3.Forward);
            fwd.Y = 0;
            var off = new Vector3(target.X - at.X, 0, target.Z - at.Z);
            var way = (off.LengthSquared() > 0.01f ? off.Normalized() : Vector3.Zero) + (fwd.LengthSquared() > 0.01f ? fwd.Normalized() : Vector3.Zero) * 0.8f;
            var q = at + (way.LengthSquared() > 0.01f ? way.Normalized() : Vector3.Zero) * 2f;
            target = new Vector3(q.X, (float)HeightAt(q.X, q.Z), q.Z);
        }
        return target;
    }

    /// <summary>An ember starts its fall: on the fight's aim (it lands when the blow comes), or on the blow itself.</summary>
    void Drop(Ev.Flare e, Battle b, bool aimed)
    {
        var target = WhereFalls(e, b);
        var dir = EmberDir(e.Blow);
        var em = new Ember
        {
            Target = target, Dir = dir, From = target - dir * (aimed ? AimFall : Fall) * FallSpeed, Born = t, LandAt = t + Fall, FallT = aimed ? AimFall : Fall,
            Last = e.Last, Radius = (float)e.Radius, Hitstop = e.Hitstop, Aimed = aimed,
        };
        if (aimed) em.LandAt = double.MaxValue;
        // The first four carry moving lights (two of them shadowed), so the shadows swing as they fall.
        if (embersLit < 4)
        {
            em.Lit = true;
            em.Light = new OmniLight3D { LightColor = new Color(1f, 0.5f, 0.16f), LightEnergy = 0, OmniRange = 10, ShadowEnabled = embersLit < 2 };
            AddChild(em.Light);
            em.Light.GlobalPosition = em.From;
            embersLit++;
        }
        embers.Add(em);
        if (!aimed) DoomUnder(em);
        Cue("ember_fall", target, 1);
    }

    /// <summary>The BOOM's shock on what still stands (classes' "shove": TX/TZ its rest point, Radius how far, 0 for a
    /// boss, which only staggers): the fight slides the body; the view gives the slide its weight, a skid of
    /// churned frost and char from its feet along the way and a few sparks blown off its blast side.</summary>
    void Shove(Ev.Flare e, Battle b)
    {
        if (e.Target < 0 || e.Target >= b.Enemies.Items.Length || b.Enemies.Items[e.Target] is not { Alive: true } foe) return;
        var from = new Vector3((float)foe.X, (float)HeightAt(foe.X, foe.Z), (float)foe.Z);
        var to = new Vector3((float)e.TX, from.Y, (float)e.TZ);
        var way = new Vector3(to.X - from.X, 0, to.Z - from.Z);
        float far = way.Length();
        if (far < 0.05f)
        {
            // A boss, or one rooted: it rocks where it stands, a ring of churned frost round its feet.
            for (int i = 0; i < 10; i++)
            {
                float a = i / 10f * Mathf.Tau + R() * 0.4f;
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                bed.Spawn(FlareBits.Kind.Puff, from + o * 1.1f * (float)(foe.Def.Scale ?? 1) + Vector3.Up * 0.15f, o * 2.4f + Vector3.Up * 0.3f, 0.7f + R() * 0.3f, 0.35f, new Color(0.11f, 0.1f, 0.1f, 0.4f), sizeEnd: 1.1f, drag: 3);
            }
            return;
        }
        way /= far;
        int n = Math.Clamp((int)(far * 2.5f), 2, 8);
        for (int i = 0; i < n; i++)
        {
            // Kicked up from its feet and carried along its slide (it settles at 9 a second: Ai.cs).
            var p = from + way * (R() * 0.5f) + Vector3.Up * 0.1f;
            bed.Spawn(FlareBits.Kind.Puff, p, way * far * (1.2f + 1.6f * i / n) + Vector3.Up * (0.3f + R() * 0.4f), 0.6f + R() * 0.4f, 0.3f + R() * 0.1f, new Color(0.11f, 0.1f, 0.095f, 0.45f), sizeEnd: 0.9f, drag: 2.5f);
        }
        for (int i = 0; i < 2; i++)
            glow.Spawn(FlareBits.Kind.Mote, from + Vector3.Up * (0.6f + R()), way * (4 + R() * 3) + Vector3.Up * (1 + R()), 0.4f + R() * 0.3f, 0.04f, new Color(1.3f, 0.62f, 0.2f), new Color(0.5f, 0.1f, 0.02f), drag: 1.8f);
    }

    /// <summary>What stands frozen under an ember's fall breaks as it lands, outward from it.</summary>
    void DoomUnder(Ember em)
    {
        if (em.Last) return;
        foreach (var d in doomed.Values)
            if (d.At == Held && d.Where.DistanceTo(em.Target) < em.Radius + 0.5f) { d.At = em.LandAt + 0.02 + d.Where.DistanceTo(em.Target) / 30; d.From = em.Target; }
    }

    /// <summary>Whether the fight's last word falls on a boss or a champion (it lands on it, not by her).</summary>
    static bool OnToughest(Ev.Flare e, Battle b) =>
        e.Target >= 0 && e.Target < b.Enemies.Items.Length && b.Enemies.Items[e.Target] is { Alive: true } x && (x.Boss || x.Elite)
        && (x.X - e.TX) * (x.X - e.TX) + (x.Z - e.TZ) * (x.Z - e.TZ) < 1;

    void BurnsTick(float dt)
    {
        var head = Head();
        double sinceSpend = spendAt < 0 ? -1 : t - spendAt;
        // ---- The Draw and the Hold: the web lights from her outward, the light runs up into the staff.
        float draw = Mathf.Min(1, (float)t / 0.22f);
        if (sinceSpend < 0)
        {
            look.X = Mathf.Min(1, (float)t / 0.12f);
            web.X = draw;
            web.Y = 1;
            web.Z = draw * (reach + 3);
            float motes = (clutch ? 2 : 1) * (banked ? 2 : 1) * (t < 0.3 ? 220 : 70);
            for (int i = 0, n = (int)(motes * dt + R()); i < n; i++)
            {
                float rr = Mathf.Sqrt(R()) * reach * draw, a = R() * Mathf.Tau;
                var p = at + new Vector3(Mathf.Cos(a) * rr, 0, Mathf.Sin(a) * rr);
                p.Y = (float)HeightAt(p.X, p.Z) + 0.05f;
                glow.Spawn(new FlareBits.P
                {
                    Kind = R() < 0.12f ? FlareBits.Kind.Thread : FlareBits.Kind.Mote, At = p, V = Vector3.Up * (2 + R() * 2),
                    Life = 1.4f, Size = 0.05f + R() * 0.05f, SizeEnd = 0.03f, Color = new Color(1.2f, 0.5f, 0.14f), ColorEnd = new Color(1.4f, 0.75f, 0.35f),
                    Home = head, Pull = 70 + rr * 4,
                });
            }
            // The staff's head: an amber flame with a blue heart, the brightest thing on the screen (under the knee).
            float hold = Mathf.SmoothStep(0, 1, (float)t / 0.22f);
            headLight.GlobalPosition = head;
            headLight.LightColor = new Color(1f, 0.58f, 0.24f);
            headLight.LightEnergy = 3.5f * hold * (clutch ? 1.15f : 1);
            // (Read from the arena's height: a flame half a metre tall over a steady core, its heart blue.)
            for (int i = 0, n = (int)(dt * 70 + R()); i < n; i++)
                glow.Spawn(FlareBits.Kind.Tongue, head + Rand3() * 0.06f, Vector3.Up * (1.6f + R()) + Rand3() * 0.3f, 0.28f + R() * 0.18f, (0.16f + 0.16f * hold) * (0.7f + 0.6f * R()), new Color(1.1f, 0.5f, 0.15f), new Color(0.6f, 0.12f, 0.02f), lift: 1);
            glow.Spawn(FlareBits.Kind.Mote, head, Vector3.Zero, 0.04f, 0.55f * hold, new Color(0.9f, 0.45f, 0.13f));
            glow.Spawn(FlareBits.Kind.Mote, head, Vector3.Zero, 0.04f, 0.16f * hold, clutch ? new Color(0.75f, 0.9f, 1.25f) : new Color(0.4f, 0.66f, 1.2f));
            // At night her one breath smokes as she draws it.
            if (Night && t > 0.12 && t < 0.12 + dt)
                bed.Spawn(FlareBits.Kind.Puff, Her + new Vector3(0, 1.62f, 0) - (Cam?.Camera.GlobalBasis.Z ?? Vector3.Zero) * 0.15f, Vector3.Up * 0.25f, 1.2f, 0.12f, new Color(0.7f, 0.72f, 0.75f, 0.35f), sizeEnd: 0.5f, drag: 1.5f);
            return;
        }
        // ---- The frost: the front races to the reach in 0.4 s; colour returns behind it, cold.
        float front = (float)(reach + 3) * Mathf.Ease(Mathf.Min(1, (float)sinceSpend / 0.4f), 0.6f);
        frost.X = front;
        frost.W = (float)sinceSpend;
        frost.Y = 1;
        look.Y = front + (float)Math.Max(0, sinceSpend - 0.4) * 45;
        look.X = Mathf.Max(0, 1 - Mathf.Max(0, (float)sinceSpend - 0.45f) / 0.5f);
        look.Z = lastAt > 0 ? Mathf.Max(0, 1 - (float)(t - lastAt) / 0.4f) * 0.4f : embers.Count > 0 ? Mathf.Max(0.35f, 1 - embers.Count / 12f) : 1;
        headLight.LightEnergy = Mathf.MoveToward(headLight.LightEnergy, 0, dt * 8);
        // The web goes faint under the ice; after the last ember it glows under the melt and sinks dark.
        if (lastAt < 0)
        {
            web.X = Mathf.MoveToward(web.X, 0.3f, dt * 3);
            web.Y = 1;
        }
        else
        {
            double r = t - lastAt;
            web.X = r < 0.3 ? Mathf.Lerp(0.3f, 0.85f, (float)r / 0.3f) : Mathf.Max(0, 0.85f - (float)(r - 0.3) / 2.2f * 0.85f);
            web.Y = Mathf.Max(0, 1 - (float)r / 2.0f);
            frost.Z = (float)(reach + 4) * Mathf.Ease(Mathf.Clamp((float)(r - 0.4) / 3.4f, 0, 1), 1.6f);
            frost.Y = Mathf.Clamp(1 - (float)(r - 3.8) / 0.8f, 0, 1);
        }
        // ---- The embers.
        foreach (var em in embers)
        {
            if (em.Landed) continue;
            float k = Mathf.Clamp((float)((t - em.Born) / em.FallT), 0, em.Aimed ? 0.97f : 1);
            var pos = em.From.Lerp(em.Target, k);
            if (em.Light != null)
            {
                em.Light.GlobalPosition = pos + Vector3.Up * 0.3f;
                em.Light.LightEnergy = 5 * Mathf.SmoothStep(0.35f, 0.7f, k);
            }
            glow.Spawn(FlareBits.Kind.Streak, pos, em.Dir * FallSpeed, 0.05f, 0.55f, new Color(1.25f, 0.62f, 0.2f));
            for (int i = 0; i < 4; i++)
            {
                var sp = pos - em.Dir * (FallSpeed * dt * R());
                bed.Spawn(FlareBits.Kind.Puff, sp, -em.Dir * 1.5f + Rand3() * 0.4f, 1.1f + R() * 0.9f, 0.35f, new Color(0.09f, 0.08f, 0.075f, 0.55f), sizeEnd: 1.4f + R(), drag: 2.5f, lift: 0.3f);
            }
            // The eye darkens for the last two frames before the last word: the BOOM's punch is the dark before it.
            if (em.Last && t - em.Born >= em.FallT - 2.2 / 60) Dip(LessFlash ? 0.85f : 0.68f);
            if (t >= em.LandAt) Land(em);
        }
        if (colT >= 0) { colT += dt; Column(dt); }
        // The statues break as their ember lands or the ring crosses them.
        foreach (var d in doomed.Values)
            if (!d.Done && d.Shatter && t >= d.At) { d.Done = true; Shatter(d.Where, d.Scale, d.From, lastAt > 0 && t - lastAt < 1.2); }
        // The ring: sparse tongues of fire on its line, leaning outward, running with it and soon gone. (At a tenth
        // of its speed and a quarter second long they fell behind it as a soft orange band: s2e.)
        if (lastAt > 0 && t - lastAt > 0.01 && t - lastAt < 0.66)
        {
            double s = t - lastAt;
            float rr = RingAt(s, ringMax), speed = (RingAt(s + 0.02, ringMax) - rr) / 0.02f;
            for (int i = 0, n = (int)(dt * 170 + R()); i < n; i++)
            {
                float a = R() * Mathf.Tau;
                var way = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                var p = boomAt + way * (rr - 0.05f);
                if (new Vector2(p.X - at.X, p.Z - at.Z).Length() > reach - 0.5f) continue;
                p.Y = (float)HeightAt(p.X, p.Z) + 0.05f;
                glow.Spawn(FlareBits.Kind.Tongue, p, way * (speed + 1) + Vector3.Up * (2.4f + R() * 2.4f), 0.08f + R() * 0.07f, 0.2f + R() * 0.16f, new Color(1.1f, 0.52f, 0.14f), new Color(0.7f, 0.12f, 0.02f));
            }
        }
        // ---- The Return: steam off every scar. Not contrails (t5): each column is fed in gusts from a tight spot,
        // leaves fast and slows, snakes on its own eddies, leans downwind more the higher it climbs, and spreads
        // and thins until it breaks up. By day fewer puffs, so it never reads as a pale sheet.
        for (int c = 0; c < marks.Count; c++)
        {
            var m = marks[c];
            float age = (float)(t - m.W);
            if (age < 0) continue;
            float seed = (c * 0.6180339f) % 1f;
            float gust = 0.3f + 1.4f * Mathf.Clamp(0.5f + 0.5f * Mathf.Sin(age * (2.1f + seed * 1.7f) + seed * 9f) + 0.35f * Mathf.Sin(age * 5.3f + seed * 4f), 0, 1);
            float rate = 26 * Mathf.Exp(-age * 0.55f) * gust * (Night ? 1 : 0.6f);
            float lean = 0.7f + 0.8f * seed;
            float r0 = Mathf.Abs(m.Z);
            for (int i = 0, n = (int)(rate * dt + R()); i < n; i++)
            {
                var p = new Vector3(m.X + (R() - 0.5f) * r0 * 0.3f, 0, m.Y + (R() - 0.5f) * r0 * 0.3f);
                p.Y = (float)HeightAt(p.X, p.Z) + 0.1f;
                float up = 1.8f + R() * 2.2f;
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Puff, At = p, V = new Vector3((R() - 0.5f) * 0.5f, up, (R() - 0.5f) * 0.5f),
                    Life = 2.4f + R() * 1.6f, Size = 0.28f + R() * 0.12f, SizeEnd = 1.5f + R() * 1.1f,
                    Color = Night ? new Color(0.6f, 0.63f, 0.67f, 0.2f) : new Color(0.5f, 0.5f, 0.52f, 0.15f), ColorEnd = Night ? new Color(0.62f, 0.64f, 0.68f, 0.07f) : new Color(0.52f, 0.52f, 0.54f, 0.04f),
                    Drag = 0.55f, Lift = 0.45f, Swirl = 1.5f, Seed = seed + R() * 0.12f, Wind = SteamWind * lean,
                });
            }
        }
    }

    /// <summary>The night air the steam leans on (m/s²): one way across the whole field.</summary>
    static readonly Vector3 SteamWind = new(1.0f, 0, 0.45f);

    /// <summary>An ember lands. The eleven before the last are told small and sharp (a flash of fire that dies to
    /// embers within a quarter second, turned jets, ice shards, steam, sparks, char on the wet frost), so the last
    /// word reads as its own shape: a column of fire driven straight up out of a short flash, and the ring.</summary>
    void Land(Ember em)
    {
        em.Landed = true;
        var p = em.Target;
        Hitstop(em.Hitstop);
        if (em.Last)
        {
            lastAt = t; boomAt = p;
            ringMax = reach + new Vector2(p.X - at.X, p.Z - at.Z).Length() + 1.5f;
            // Every statue still standing breaks as the ring crosses it, outward from the blast.
            foreach (var d in doomed.Values)
                if (d.At == Held) { d.At = t + RingTime(d.Where.DistanceTo(p)) + CrackHold(); d.From = p; }
        }
        if (!firstLanded) { firstLanded = true; Shots.Want("b7_ember1", 1 / 60.0); Shots.Want("b8_embers", 0.2); }
        if (em.Last) { Shots.Want("b9_last", 1 / 60.0); Shots.Want("c1_last5", 5 / 60.0); Shots.Want("c1a_p10", 0.1); Shots.Want("c1w_wave", 0.3); Shots.Want("c2_ret1", 1); Shots.Want("c3_ret3", 3); Shots.Want("c4_ret6", 5.5); }
        marks.Add(new Vector4(p.X, p.Z, em.Radius * (em.Last ? 0.8f : 0.9f), (float)t));
        if (marks.Count > 30) marks.RemoveAt(0);
        // (The last word's own light, if it carried one, goes with the flash: left on, it lit the char orange to
        // the end of the Return, s5a.)
        if (em.Last && em.Light != null)
        {
            var l = em.Light;
            GetTree().CreateTween().TweenProperty(l, "light_energy", 0f, 0.12f).SetEase(Tween.EaseType.Out);
            GetTree().CreateTimer(0.15).Timeout += () => { if (IsInstanceValid(l)) l.QueueFree(); };
            em.Light = null;
        }
        if (em.Last) LastWord(p);
        else
        {
            // A flash of fire, gone to embers within a quarter second.
            for (int i = 0; i < 5; i++)
            {
                float a = R() * Mathf.Tau, o = R();
                var v = new Vector3(Mathf.Cos(a) * (1 + 2.5f * o), 1.2f + R() * 2.5f, Mathf.Sin(a) * (1 + 2.5f * o));
                glow.Spawn(FlareBits.Kind.Fire, p + Vector3.Up * (0.15f + R() * 0.3f), v, 0.2f + R() * 0.12f, 0.38f + R() * 0.2f, new Color(1.15f, 0.5f, 0.13f), new Color(0.8f, 0.22f, 0.04f), sizeEnd: 0.9f + R() * 0.4f, drag: 5, lift: 2);
            }
            // Turned jets of flame thrown out along the ground.
            for (int i = 0, n = 3 + (int)(R() * 4); i < n; i++)
            {
                float a = R() * Mathf.Tau;
                var v = new Vector3(Mathf.Cos(a) * (3 + R() * 2), 2.2f + R() * 1.5f, Mathf.Sin(a) * (3 + R() * 2));
                glow.Spawn(FlareBits.Kind.Tongue, p + Vector3.Up * 0.15f, v, 0.2f + R() * 0.1f, 0.22f + R() * 0.12f, new Color(1.15f, 0.5f, 0.14f), new Color(0.7f, 0.16f, 0.03f), drag: 5);
            }
            shards.Burst(p + Vector3.Up * 0.1f, 9, 7, 0.2f, new Color(0, 0, 0, 0), 1);
            // Steam: thin wisps, not a few cotton balls.
            for (int i = 0; i < 10; i++)
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Puff, At = p + Vector3.Up * 0.3f, V = new Vector3((R() - 0.5f) * 4, 2f + R() * 3f, (R() - 0.5f) * 4),
                    Life = 1.1f + R() * 1.0f, Size = 0.4f, SizeEnd = 1.2f + R(), Color = new Color(0.62f, 0.65f, 0.7f, 0.2f),
                    ColorEnd = new Color(0.62f, 0.65f, 0.7f, 0.08f), Drag = 2.4f, Lift = 1.5f, Swirl = 1.2f, Seed = R(), Wind = SteamWind * 0.6f,
                });
            // Sparks, never soot (t10: black flecks over the fire).
            for (int i = 0; i < 16; i++)
                glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * 0.2f, new Vector3((R() - 0.5f) * 9, 3 + R() * 6, (R() - 0.5f) * 9), 0.45f + R() * 0.45f, 0.04f, new Color(1.4f, 0.7f, 0.22f), new Color(0.6f, 0.12f, 0.02f), gravity: 9);
            if (em.Light != null)
            {
                em.Light.LightEnergy = 11;
                em.Light.OmniRange = 9;
                var l = em.Light;
                GetTree().CreateTween().TweenProperty(l, "light_energy", 0f, 0.25f).SetEase(Tween.EaseType.Out);
                GetTree().CreateTimer(0.3).Timeout += () => { if (IsInstanceValid(l)) l.QueueFree(); };
                em.Light = null;
            }
            else SpendLightAt(p, 8);
            Cam?.Jolt(Vector3.Up, 0.12f * Motion);
            Cue("ember_land", p, 1);
            Rumble(0, 0.35f, 0.03f);
        }
    }

    /// <summary>The last word (FLARE_LOOK §2.2): ONE event bigger than any ember (judge 2, s4). The eye darkened for
    /// two frames before it (BurnsTick); a torn 3 m ground flash, a low light on the statues' rims round it; one
    /// pillar of fire at its full height in 0.15 s under a dark cap lit from below, jets of flame thrown out along
    /// the ground with a spray of sparks (FlareFx.Boom), the ice blown out of the crater, and the ring. Told by
    /// its shape, size and motion, not by more light (§1.6 has no headroom).</summary>
    void LastWord(Vector3 p)
    {
        colT = 0;
        BoomStart(p);
        // The flash's hot point, low at the root (the ground's flash and the pillar carry the size).
        glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * 0.4f, Vector3.Zero, 0.06f, 1.3f, new Color(1.0f, 0.62f, 0.26f), new Color(0.5f, 0.12f, 0.02f));
        shards.Burst(p + Vector3.Up * 0.2f, 34, 13, 0.18f, new Color(0, 0, 0, 0), 1);
        // Sparks: up the pillar, and a spray thrown out low along the jets.
        for (int i = 0; i < 24; i++)
            glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * (0.3f + R() * 2), new Vector3((R() - 0.5f) * 5, 10 + R() * 14, (R() - 0.5f) * 5), 0.6f + R() * 0.5f, 0.05f, new Color(1.4f, 0.7f, 0.22f), new Color(0.6f, 0.12f, 0.02f), gravity: 9, drag: 0.8f);
        for (int i = 0; i < 70; i++)
        {
            var d = jets[(int)(R() * jetN) % Math.Max(1, jetN)];
            var v = d * (9 + R() * 13) + new Vector3((R() - 0.5f) * 4, 1.5f + R() * 4.5f, (R() - 0.5f) * 4);
            glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * 0.3f, v, 0.4f + R() * 0.45f, 0.045f, new Color(1.4f, 0.72f, 0.24f), new Color(0.6f, 0.12f, 0.02f), gravity: 9, drag: 1.2f);
        }
        SpendLight(p + Vector3.Up * 3f, new Color(1f, 0.6f, 0.25f), 20 * (banked ? 1.25f : 1));
        spendLight.OmniRange = reach * 1.3f;
        Cam?.Jolt(Vector3.Up, (0.6f + (banked ? 0.1f : 0)) * Motion);
        Cue("ember_last", p, 1);
        Rumble(1, 0.6f, 0.4f);
        HudDim(0);
    }

    /// <summary>Real seconds since the last word landed (its pillar runs on the particles' clock); -1: none.</summary>
    double colT = -1;

    /// <summary>The last word's particles round its pillar (FlareFx.Boom has the shapes): fire licking at its root,
    /// the cap's smoke going on as the cap thins, and the stem's smoke standing after the fire, leaning downwind.</summary>
    void Column(float dt)
    {
        float c = (float)colT;
        BoomTick(c, (float)(t - lastAt), dt);
        if (c > 1.4f || Simmed) return;
        var p = boomAt;
        const float H = PillarH;
        // Its root: fire licking round the pillar's foot.
        if (c < 0.5f)
            for (int i = 0, n = (int)(40 * dt + R()); i < n; i++)
            {
                float a = R() * Mathf.Tau;
                var way = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                glow.Spawn(FlareBits.Kind.Fire, p + way * (0.6f + R() * 0.5f) + Vector3.Up * 0.2f, way * (1 + R() * 1.5f) + Vector3.Up * (2 + R() * 3),
                    0.25f + R() * 0.12f, 0.4f + R() * 0.15f, new Color(1.1f, 0.5f, 0.14f), new Color(0.7f, 0.15f, 0.03f), sizeEnd: 0.9f, drag: 3);
            }
        // The head: the cap's smoke goes on rolling out and up as the cap thins.
        if (c > 0.5f && c < 1.2f)
        {
            float k = (c - 0.5f) / 0.7f, rise = H + 1.6f + 0.8f * k;
            for (int i = 0, n = (int)(50 * (1 - k) * dt + R()); i < n; i++)
            {
                float a = R() * Mathf.Tau;
                var way = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Smoke, At = p + Vector3.Up * (rise + (R() - 0.3f) * 1.0f) + way * (1.0f + R() * 2.0f),
                    V = way * (1.5f + R() * 1.5f) + Vector3.Up * (1.5f + R() * 2), Life = 1.8f + R() * 0.8f, Size = 1.2f + R() * 0.4f, SizeEnd = 2.8f + R() * 1.0f,
                    Color = new Color(0.1f, 0.085f, 0.075f, 0.6f), ColorEnd = new Color(0.13f, 0.12f, 0.11f, 0.2f),
                    Drag = 1.8f, Lift = 0.3f, Swirl = 0.9f, Seed = R(), Wind = SteamWind * 0.7f,
                });
            }
        }
        // The stem: the fire's smoke after it, dark, standing as a column as the fire goes, leaning downwind.
        if (c > 0.35f && c < 1.1f)
            for (int i = 0, n = (int)(40 * dt + R()); i < n; i++)
            {
                float h = 0.4f + R() * H * 0.85f;
                bed.Spawn(new FlareBits.P
                {
                    Kind = FlareBits.Kind.Smoke, At = p + new Vector3((R() - 0.5f) * 0.9f, h, (R() - 0.5f) * 0.9f),
                    V = new Vector3((R() - 0.5f) * 0.8f, 2.5f + R() * 3, (R() - 0.5f) * 0.8f), Life = 1.5f + R() * 0.9f, Size = 0.7f + R() * 0.3f, SizeEnd = 1.8f + R() * 0.8f,
                    Color = new Color(0.08f, 0.065f, 0.055f, 0.6f), ColorEnd = new Color(0.11f, 0.1f, 0.095f, 0.2f),
                    Drag = 1.2f, Lift = 0.4f, Swirl = 1.1f, Seed = R(), Wind = SteamWind * (0.4f + h / H * 0.6f),
                });
            }
    }

    /// <summary>A short unshadowed flash at an unlit ember's impact.</summary>
    void SpendLightAt(Vector3 p, float energy)
    {
        var l = new OmniLight3D { LightColor = new Color(1f, 0.5f, 0.16f), LightEnergy = energy, OmniRange = 9 };
        AddChild(l);
        l.GlobalPosition = p + Vector3.Up * 1.2f;
        GetTree().CreateTween().TweenProperty(l, "light_energy", 0f, 0.25f).SetEase(Tween.EaseType.Out).SetTrans(Tween.TransitionType.Expo);
        GetTree().CreateTimer(0.3).Timeout += () => { if (IsInstanceValid(l)) l.QueueFree(); };
    }

    /// <summary>A statue breaks: its ice flies out away from what broke it (hot from the fire), a small scorch where
    /// it stood, sparks lift, a breath of frost dust. Never a body that just goes.</summary>
    void Shatter(Vector3 w, float scale, Vector3 from, bool ring)
    {
        var away = new Vector3(w.X - from.X, 0, w.Z - from.Z);
        away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector3.Zero;
        if (ring)
        {
            // The ring's burst (judge 2, s4: even, still confetti): the ice thrown out along the line's way,
            // stretched by its speed and lit orange through its faces, landing a metre or three on and cooling grey.
            shards.Burst(w + Vector3.Up * 0.9f * scale, (int)(5 * scale + R() * 2), 7.5f, 0.16f * scale, new Color(0.32f, 0.3f, 0.27f, 0.6f), 1.3f, away, thrown: true);
            // The line flares where it crosses a body.
            glow.Spawn(FlareBits.Kind.Fire, w + Vector3.Up * 0.45f * scale + away * 0.25f, away * 3.5f + Vector3.Up * 2.0f, 0.12f + R() * 0.05f, 0.26f * scale, new Color(0.95f, 0.38f, 0.09f), new Color(0.55f, 0.08f, 0.02f), sizeEnd: 0.6f * scale, drag: 3);
            if (R() < 0.5f)
                glow.Spawn(FlareBits.Kind.Tongue, w + Vector3.Up * 0.5f * scale, away * 5 + Vector3.Up * (3.5f + R() * 2), 0.1f + R() * 0.06f, (0.26f + R() * 0.1f) * scale, new Color(1.1f, 0.5f, 0.14f), new Color(0.65f, 0.12f, 0.02f), drag: 2);
            // A short breath of steam off the hot ice.
            bed.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Puff, At = w + Vector3.Up * 0.8f * scale, V = Vector3.Up * 1.6f + away * 1.4f,
                Life = 0.7f + R() * 0.3f, Size = 0.3f * scale, SizeEnd = 1.1f * scale, Color = new Color(0.62f, 0.65f, 0.7f, 0.2f),
                ColorEnd = new Color(0.62f, 0.65f, 0.7f, 0.0f), Drag = 2.2f, Lift = 0.8f, Swirl = 1.0f, Seed = R(), Wind = SteamWind * 0.5f,
            });
        }
        else shards.Burst(w + Vector3.Up * 0.9f * scale, (int)(8 * scale), 5f, 0.16f * scale, new Color(0.32f, 0.3f, 0.27f, 0.6f), 0.9f, away);
        scars.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Scar, At = w + Vector3.Up * 0.04f, Life = 4.4f + R(), Size = (0.8f + R() * 0.35f) * scale, Color = new Color(0.02f, 0.016f, 0.013f, 0.9f) });
        // (The dust small, faint and cold: at 1.6 m and pale, 250 of them at once laid a grey sheet over the crowd.)
        if (!ring) bed.Spawn(FlareBits.Kind.Puff, w + Vector3.Up * 0.7f, Vector3.Up * 0.6f + away * 1.2f, 0.6f, 0.25f * scale, new Color(0.2f, 0.3f, 0.43f, 0.12f), sizeEnd: 0.7f * scale, drag: 2);
        // One spark each (three, over 240 statues, were orange confetti over the char: s1a).
        glow.Spawn(FlareBits.Kind.Mote, w + Vector3.Up * (0.3f + R() * 1.2f) * scale, away * (1 + R() * 2) + new Vector3(R() - 0.5f, 1.5f + R() * 2, R() - 0.5f), 0.5f + R() * 0.5f, 0.05f, new Color(1.25f, 0.6f, 0.18f), new Color(0.5f, 0.1f, 0.02f), drag: 1.5f);
    }
}
