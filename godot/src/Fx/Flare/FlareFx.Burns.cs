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
        Cue("ember_fall", target, 1);
    }

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
        for (int i = pendingShatters.Count - 1; i >= 0; i--)
            if (t >= pendingShatters[i].At) { var s = pendingShatters[i]; Shatter(s.Where, s.Scale); pendingShatters.RemoveAt(i); }
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

    /// <summary>An ember lands: turned tongues of flame, ice shards, steam, sparks and soot, the char on the wet frost.</summary>
    void Land(Ember em)
    {
        em.Landed = true;
        var p = em.Target;
        Hitstop(em.Hitstop);
        if (em.Last) { lastAt = t; boomAt = p; }
        if (!firstLanded) { firstLanded = true; Shots.Want("b7_ember1", 1 / 60.0); Shots.Want("b8_embers", 0.2); }
        if (em.Last) { Shots.Want("b9_last", 1 / 60.0); Shots.Want("c1_last5", 5 / 60.0); Shots.Want("c1w_wave", 0.3); Shots.Want("c2_ret1", 1); Shots.Want("c3_ret3", 3); Shots.Want("c4_ret6", 5.5); }
        marks.Add(new Vector4(p.X, p.Z, em.Radius * (em.Last ? 1.15f : 0.9f), (float)t));
        if (marks.Count > 30) marks.RemoveAt(0);
        float big = em.Last ? 1.6f : 1;
        // A fireball of churning billows thrown out and up off the ice (rays read as a firework: 13 October).
        for (int i = 0; i < (em.Last ? 32 : 12); i++)
        {
            float a = R() * Mathf.Tau, out_ = R();
            var v = new Vector3(Mathf.Cos(a) * (1.5f + 4 * out_), 1.5f + R() * 4, Mathf.Sin(a) * (1.5f + 4 * out_)) * big;
            glow.Spawn(FlareBits.Kind.Fire, p + Vector3.Up * (0.2f + R() * 0.4f), v, 0.45f + R() * 0.35f, (0.5f + R() * 0.4f) * big, new Color(1.15f, 0.5f, 0.13f), new Color(0.8f, 0.22f, 0.04f), sizeEnd: (1.3f + R() * 0.7f) * big * (em.Last ? 1.4f : 1), drag: 4, lift: 2.5f);
        }
        // A few short tongues licking up out of it, turned along their way.
        for (int i = 0; i < (em.Last ? 8 : 4); i++)
        {
            float a = R() * Mathf.Tau;
            var v = new Vector3(Mathf.Cos(a), 2.2f + R() * 1.5f, Mathf.Sin(a)) * (2 + R() * 2) * big;
            glow.Spawn(FlareBits.Kind.Tongue, p + Vector3.Up * 0.2f, v, 0.3f + R() * 0.15f, (0.25f + R() * 0.2f) * big, new Color(1.15f, 0.5f, 0.14f), new Color(0.7f, 0.16f, 0.03f), drag: 4);
        }
        shards.Burst(p + Vector3.Up * 0.1f, em.Last ? 18 : 9, 7.5f * big, 0.2f, new Color(0, 0, 0, 0), 1);
        // Steam: many thin wisps, not a few cotton balls.
        for (int i = 0; i < 16; i++)
            bed.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Puff, At = p + Vector3.Up * 0.3f, V = new Vector3((R() - 0.5f) * 5, 2f + R() * 3f, (R() - 0.5f) * 5) * big,
                Life = 1.2f + R() * 1.2f, Size = 0.45f, SizeEnd = (1.4f + R()) * big, Color = new Color(0.62f, 0.65f, 0.7f, 0.22f),
                ColorEnd = new Color(0.62f, 0.65f, 0.7f, 0.1f), Drag = 2.4f, Lift = 1.5f, Swirl = 1.2f, Seed = R(), Wind = SteamWind * 0.6f,
            });
        for (int i = 0; i < 22; i++)
            glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Up * 0.2f, new Vector3((R() - 0.5f) * 10, 3 + R() * 7, (R() - 0.5f) * 10) * big, 0.5f + R() * 0.5f, 0.045f, new Color(1.4f, 0.7f, 0.22f), new Color(0.6f, 0.12f, 0.02f), gravity: 9);
        for (int i = 0; i < 10; i++)
            bed.Spawn(FlareBits.Kind.Soot, p + Vector3.Up * 0.2f, new Vector3((R() - 0.5f) * 8, 2 + R() * 4, (R() - 0.5f) * 8), 0.8f + R() * 0.5f, 0.07f, new Color(0.03f, 0.025f, 0.02f, 0.9f), gravity: 10);
        if (em.Light != null)
        {
            em.Light.LightEnergy = em.Last ? 22 : 14;
            em.Light.OmniRange = 11;
            var l = em.Light;
            GetTree().CreateTween().TweenProperty(l, "light_energy", 0f, 0.35f).SetEase(Tween.EaseType.Out);
            GetTree().CreateTimer(0.4).Timeout += () => { if (IsInstanceValid(l)) l.QueueFree(); };
            em.Light = null;
        }
        else if (!em.Last) SpendLightAt(p, 12);
        if (em.Last)
        {
            // The last word: the full BOOM on the toughest thing in reach.
            SpendLight(p + Vector3.Up * 2.5f, new Color(1f, 0.6f, 0.25f), 20 * (banked ? 1.25f : 1));
            spendLight.OmniRange = reach * 1.3f;
            // The shock: frost dust and ice blown outward along the ground in a ring, so the room is cleared.
            for (int i = 0; i < 56; i++)
            {
                float a = i / 56f * Mathf.Tau + R() * 0.1f;
                var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                bed.Spawn(FlareBits.Kind.Puff, p + dir * 0.8f + Vector3.Up * 0.3f, dir * (15 + R() * 6) + Vector3.Up * (0.5f + R()), 0.9f + R() * 0.5f, 0.6f, new Color(0.55f, 0.6f, 0.66f, 0.3f), sizeEnd: 2.4f, drag: 2.6f, lift: 0.3f);
            }
            shards.Burst(p + Vector3.Up * 0.2f, 40, 16, 0.14f, new Color(0, 0, 0, 0), 0.4f);
            Cam?.Jolt(Vector3.Up, (0.6f + (banked ? 0.1f : 0)) * Motion);
            Cue("ember_last", p, 1);
            Rumble(1, 0.6f, 0.4f);
            HudDim(0);
        }
        else
        {
            Cam?.Jolt(Vector3.Up, 0.12f * Motion);
            Cue("ember_land", p, 1);
            Rumble(0, 0.35f, 0.03f);
        }
    }

    /// <summary>A short unshadowed flash at an unlit ember's impact.</summary>
    void SpendLightAt(Vector3 p, float energy)
    {
        var l = new OmniLight3D { LightColor = new Color(1f, 0.5f, 0.16f), LightEnergy = energy, OmniRange = 10 };
        AddChild(l);
        l.GlobalPosition = p + Vector3.Up * 1.2f;
        GetTree().CreateTween().TweenProperty(l, "light_energy", 0f, 0.3f).SetEase(Tween.EaseType.Out).SetTrans(Tween.TransitionType.Expo);
        GetTree().CreateTimer(0.35).Timeout += () => { if (IsInstanceValid(l)) l.QueueFree(); };
    }

    /// <summary>A frozen body shatters: its ice flies (tinted a little by its paint), a puff of frost dust, sparks lift.</summary>
    void Shatter(Vector3 w, float scale)
    {
        shards.Burst(w + Vector3.Up * 0.8f * scale, (int)(6 * scale), 4.5f, 0.13f * scale, new Color(0.32f, 0.3f, 0.27f, 0.6f), 0.5f);
        // (The dust small, faint and cold: at 1.6 m and pale, 250 of them at once laid a grey sheet over the crowd.)
        bed.Spawn(FlareBits.Kind.Puff, w + Vector3.Up * 0.7f, Vector3.Up * 0.6f, 0.7f, 0.25f * scale, new Color(0.2f, 0.3f, 0.43f, 0.13f), sizeEnd: 0.65f * scale, drag: 2);
        for (int i = 0; i < 6; i++)
            glow.Spawn(FlareBits.Kind.Mote, w + Vector3.Up * (0.4f + R()), new Vector3((R() - 0.5f) * 0.6f, 1 + R() * 1.5f, (R() - 0.5f) * 0.6f), 1.2f + R(), 0.04f, new Color(1.1f, 0.48f, 0.14f), new Color(0.4f, 0.08f, 0.02f), drag: 0.8f);
    }
}
