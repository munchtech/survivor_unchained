using System;
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
        public float Radius;
        public int Hitstop;
        public OmniLight3D? Light;
    }

    /// <summary>The embers' fall: 0.14 s at 110 m/s along one shared angle (the view lands each 0.14 s after the
    /// fight's blow; the bodies it kills are held standing until it lands).</summary>
    const float Fall = 0.26f, FallSpeed = 80;
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
        if (e.Part != "ember") return;
        var target = new Vector3((float)e.TX, (float)HeightAt(e.TX, e.TZ), (float)e.TZ);
        // The last word lands by her (2 m, toward its pack and away from the eye), so the BOOM is centred at every
        // camera and its ring crosses the whole reach; on a boss or a champion it still lands on it (§1.6). (View
        // only: what it kills where the fight aimed it breaks as the ring crosses it.)
        if (e.Last && !OnToughest(e, b))
        {
            var fwd = -(Cam?.Camera.GlobalBasis.Z ?? Vector3.Forward);
            fwd.Y = 0;
            var off = new Vector3(target.X - at.X, 0, target.Z - at.Z);
            var way = (off.LengthSquared() > 0.01f ? off.Normalized() : Vector3.Zero) + (fwd.LengthSquared() > 0.01f ? fwd.Normalized() : Vector3.Zero) * 0.8f;
            var q = at + (way.LengthSquared() > 0.01f ? way.Normalized() : Vector3.Zero) * 2f;
            target = new Vector3(q.X, (float)HeightAt(q.X, q.Z), q.Z);
        }
        var dir = EmberDir(e.Blow);
        var em = new Ember
        {
            Target = target, Dir = dir, From = target - dir * Fall * FallSpeed, Born = t, LandAt = t + Fall,
            Last = e.Last, Radius = (float)e.Radius, Hitstop = e.Hitstop,
        };
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
        // What stands frozen under its fall breaks as it lands, outward from it.
        if (!em.Last)
            foreach (var d in doomed.Values)
                if (d.At == Held && d.Where.DistanceTo(target) < em.Radius + 0.5f) { d.At = em.LandAt + 0.02 + d.Where.DistanceTo(target) / 30; d.From = target; }
        Cue("ember_fall", target, 1);
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
            float k = Mathf.Clamp((float)((t - em.Born) / Fall), 0, 1);
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
            if (t >= em.LandAt) Land(em);
        }
        // The statues break as their ember lands or the ring crosses them.
        foreach (var d in doomed.Values)
            if (!d.Done && d.Shatter && t >= d.At) { d.Done = true; Shatter(d.Where, d.Scale, d.From, lastAt > 0 && t - lastAt < 1.2); }
        // The ring: sparse tongues of fire along its line, leaning outward as it runs.
        if (lastAt > 0 && t - lastAt > 0.01 && t - lastAt < 0.62)
        {
            double s = t - lastAt;
            float rr = RingAt(s, ringMax), speed = (RingAt(s + 0.02, ringMax) - rr) / 0.02f;
            for (int i = 0, n = (int)(dt * 120 + R()); i < n; i++)
            {
                float a = R() * Mathf.Tau;
                var way = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                var p = boomAt + way * rr;
                if (new Vector2(p.X - at.X, p.Z - at.Z).Length() > reach - 0.5f) continue;
                p.Y = (float)HeightAt(p.X, p.Z) + 0.05f;
                glow.Spawn(FlareBits.Kind.Tongue, p, way * (1.2f + speed * 0.1f) + Vector3.Up * (2.6f + R() * 2), 0.16f + R() * 0.12f, 0.24f + R() * 0.2f, new Color(1.1f, 0.5f, 0.13f), new Color(0.65f, 0.1f, 0.02f), drag: 3);
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
                if (d.At == Held) { d.At = t + RingTime(d.Where.DistanceTo(p)); d.From = p; }
        }
        if (!firstLanded) { firstLanded = true; Shots.Want("b7_ember1", 1 / 60.0); Shots.Want("b8_embers", 0.2); }
        if (em.Last) { Shots.Want("b9_last", 1 / 60.0); Shots.Want("c1_last5", 5 / 60.0); Shots.Want("c1w_wave", 0.3); Shots.Want("c2_ret1", 1); Shots.Want("c3_ret3", 3); Shots.Want("c4_ret6", 5.5); }
        marks.Add(new Vector4(p.X, p.Z, em.Radius * (em.Last ? 0.8f : 0.9f), (float)t));
        if (marks.Count > 30) marks.RemoveAt(0);
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

    /// <summary>The last word (FLARE_LOOK §2.2): a short flash, a column of fire driven straight up out of it with
    /// white-hot jets, its dark smoke after, the ice blown out of the crater, and the ring. Told by its shape,
    /// size and motion, not by more light (§1.6 has no headroom).</summary>
    void LastWord(Vector3 p)
    {
        // The flash: four frames at its peak, under the knee.
        glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * 0.8f, Vector3.Zero, 0.07f, 2.6f, new Color(1.0f, 0.62f, 0.26f), new Color(0.5f, 0.12f, 0.02f));
        // The column: billows driven up hard, narrow at the root, swelling as they climb and cool.
        for (int i = 0; i < 20; i++)
        {
            float a = R() * Mathf.Tau, o = R() * R();
            var v = new Vector3(Mathf.Cos(a) * (0.6f + 2.2f * o), 7 + R() * 15, Mathf.Sin(a) * (0.6f + 2.2f * o));
            glow.Spawn(FlareBits.Kind.Fire, p + Vector3.Up * (0.2f + R() * 0.6f), v, 0.4f + R() * 0.35f, 0.6f + R() * 0.35f, new Color(1.15f, 0.52f, 0.14f), new Color(0.75f, 0.18f, 0.03f), sizeEnd: 1.5f + R() * 1.1f, drag: 2.2f, lift: 1.5f);
        }
        // White-hot jets up its heart: the column's spine.
        for (int i = 0; i < 12; i++)
        {
            var v = new Vector3((R() - 0.5f) * 3, 26 + R() * 18, (R() - 0.5f) * 3);
            glow.Spawn(FlareBits.Kind.Streak, p + Vector3.Up * (0.3f + R()), v, 0.1f + R() * 0.12f, 0.3f + R() * 0.15f, new Color(1.2f, 0.66f, 0.24f), drag: 3);
        }
        // Its root: tongues turned out along the ground, and the ice thrown out of the crater, hot.
        for (int i = 0; i < 8; i++)
        {
            float a = i / 8f * Mathf.Tau + R() * 0.5f;
            var v = new Vector3(Mathf.Cos(a) * (5 + R() * 3), 2.5f + R() * 2, Mathf.Sin(a) * (5 + R() * 3));
            glow.Spawn(FlareBits.Kind.Tongue, p + Vector3.Up * 0.2f, v, 0.25f + R() * 0.12f, 0.4f + R() * 0.2f, new Color(1.15f, 0.5f, 0.14f), new Color(0.7f, 0.16f, 0.03f), drag: 4);
        }
        shards.Burst(p + Vector3.Up * 0.2f, 34, 13, 0.18f, new Color(0, 0, 0, 0), 1);
        for (int i = 0; i < 30; i++)
            glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * (0.3f + R() * 2), new Vector3((R() - 0.5f) * 8, 8 + R() * 12, (R() - 0.5f) * 8), 0.7f + R() * 0.6f, 0.05f, new Color(1.4f, 0.7f, 0.22f), new Color(0.6f, 0.12f, 0.02f), gravity: 7, drag: 0.6f);
        // Its smoke: a dark column boiling up after the fire, lit from under by it.
        for (int i = 0; i < 10; i++)
        {
            float a = R() * Mathf.Tau;
            var v = new Vector3(Mathf.Cos(a) * (0.5f + R() * 1.5f), 4 + R() * 5, Mathf.Sin(a) * (0.5f + R() * 1.5f));
            bed.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Puff, At = p + Vector3.Up * (1 + R() * 2), V = v, Life = 1.5f + R() * 0.8f, Size = 1.0f + R() * 0.5f,
                SizeEnd = 3.0f + R() * 1.4f, Color = new Color(0.1f, 0.075f, 0.06f, 0.6f), ColorEnd = new Color(0.12f, 0.11f, 0.1f, 0.25f),
                Drag = 1.4f, Lift = 0.9f, Swirl = 1.2f, Seed = R(), Wind = SteamWind * 0.8f,
            });
        }
        SpendLight(p + Vector3.Up * 3f, new Color(1f, 0.6f, 0.25f), 20 * (banked ? 1.25f : 1));
        spendLight.OmniRange = reach * 1.3f;
        Cam?.Jolt(Vector3.Up, (0.6f + (banked ? 0.1f : 0)) * Motion);
        Cue("ember_last", p, 1);
        Rumble(1, 0.6f, 0.4f);
        HudDim(0);
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
        shards.Burst(w + Vector3.Up * 0.9f * scale, (int)(8 * scale), ring ? 6.5f : 5f, 0.16f * scale, new Color(0.32f, 0.3f, 0.27f, 0.6f), 0.9f, away);
        scars.Spawn(new FlareBits.P { Kind = FlareBits.Kind.Scar, At = w + Vector3.Up * 0.04f, Life = 4.4f + R(), Size = (0.8f + R() * 0.35f) * scale, Color = new Color(0.02f, 0.016f, 0.013f, 0.9f) });
        // (The dust small, faint and cold: at 1.6 m and pale, 250 of them at once laid a grey sheet over the crowd.)
        bed.Spawn(FlareBits.Kind.Puff, w + Vector3.Up * 0.7f, Vector3.Up * 0.6f + away * 1.2f, 0.6f, 0.25f * scale, new Color(0.2f, 0.3f, 0.43f, 0.12f), sizeEnd: 0.7f * scale, drag: 2);
        // One spark each (three, over 240 statues, were orange confetti over the char: s1a).
        for (int i = 0; i < 1; i++)
            glow.Spawn(FlareBits.Kind.Mote, w + Vector3.Up * (0.3f + R() * 1.2f) * scale, away * (1 + R() * 2) + new Vector3(R() - 0.5f, 1.5f + R() * 2, R() - 0.5f), 0.5f + R() * 0.5f, 0.05f, new Color(1.25f, 0.6f, 0.18f), new Color(0.5f, 0.1f, 0.02f), drag: 1.5f);
    }
}
