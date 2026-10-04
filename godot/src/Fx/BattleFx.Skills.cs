using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Each skill drawn as itself, not as its school: the survivor's blows carry
/// their skill's art and rank (Ev.*.Art, Rank), and this gives each its own
/// body in flight, its own trail, its own release and its own landing, in its
/// school's colour and shape language (docs/team/skills.md):
///
///   steel   warm white, sharp streaks, sparks thrown along the blow, dust;
///   fire    orange, tongues and embers rising, smoke, scorch;
///   frost   pale blue, crystals and glints, mist, rime;
///   storm   blue-white, forks that flicker, crackle;
///   nature  green, spores and leaves, curling wisps;
///   arcane  violet, motes and runes that turn;
///   holy    gold, rays and rings, sigils;
///   shadow  violet-black, wisps that drink, blood-red where it bleeds.
///
/// Every skill grows with its rank (Grow) and its evolution adds a layer of
/// its own. A crowd being hit by several skills at once is kept readable by
/// a budget per frame for the small things (sparks per hit).
/// </summary>
public partial class BattleFx
{
    /// <summary>Trails of what flies, bolts, threads (Ribbons).</summary>
    public readonly Ribbons Ribbons = new();
    int hitBudget;

    /// <summary>How much bigger and brighter a skill is drawn at its rank: a
    /// rank-8 skill a third again its rank-1 self.</summary>
    static float Grow(int rank) => 1 + 0.045f * Math.Clamp(rank - 1, 0, 9);

    static Color Hdr(string hex, float k) { var c = new Color(hex).SrgbToLinear(); return new Color(c.R * k, c.G * k, c.B * k); }

    // The hues the skills use beyond their schools' own (Palette): blood, the
    // Watch's gold edge, fen-light, moonlight.
    static readonly Color Blood = Hdr("#c01a14", 2.2f), BloodDim = Hdr("#4a0806", 1f), OathGold = Hdr("#ffcf6a", 2.6f),
        SteelWhite = Hdr("#f4f0e8", 2.4f), Moon = Hdr("#d8d4ff", 2.6f), FenLight = Hdr("#8affd8", 2.6f), Wind = Hdr("#dff2ec", 1.6f),
        Ember = new(2.6f, 1.15f, 0.3f), EmberDeep = new(1.5f, 0.28f, 0.05f);

    /* ------------------------------------------------------------ impacts -- */

    /// <summary>A blow landing on a body, drawn by what struck it: the white
    /// instant of contact (larger for a heavier share of its life, larger
    /// still for a critical), then what that kind of blow throws.</summary>
    void Impact(Ev.Hit e, Vector3 at)
    {
        var school = e.School;
        var pal = Palette.Of(school);
        string art = e.Art ?? "";
        float share = e.MaxHp > 0 ? Mathf.Clamp((float)(e.Amount / e.MaxHp), 0, 1) : 0.2f;
        float g = Grow(e.Rank);
        bool rich = hitBudget > 0;
        hitBudget--;
        var away = new Vector3((float)e.Dx, 0, (float)e.Dz);
        if (away.LengthSquared() < 0.01f) away = Vector3.Forward;
        away = away.Normalized();
        // The instant: a flare at the point of contact.
        float flare = (0.45f + share * 0.9f) * (e.Crit ? 1.6f : 1) * g;
        Sparks.Spawn(at, Vector3.Zero, e.Crit ? 0.12f : 0.08f, flare, pal.Core * (e.Crit ? 1.1f : 0.8f), pal.Glow * 0.3f, flare * 0.4f, sprite: Sprites.Of("flare"), spinV: 0);
        if (!rich) return;
        // The skill's own mark at the body: an arrow's line carried through it, a knife's
        // cut, a disc's star of gold, a mote's violet star, a shard's frost star.
        switch (art)
        {
            case "arrow" or "arrow_mark":
                Ribbons.Line(new[] { at - away * 0.5f, at + away * 0.3f, at + away * 1.1f }, 0.16f * g, 0.12f, Hdr("#ffd8a0", 1f), 2.4f, Ribbons.Style.Steel, new[] { 0f, 1f, 0f });
                break;
            case "dagger" or "dagger_blood" or "dagger_flurry":
                Sparks.Spawn(at, Vector3.Zero, 0.16f, 0.7f * g, art == "dagger_blood" ? Blood : SteelWhite * 0.8f, null, 0.8f * g, sprite: Sprites.Of("scratch"), spinV: 0);
                break;
            case "disc" or "disc_aegis" or "disc_reckon":
                Sparks.Spawn(at, Vector3.Zero, 0.18f, 1.1f * g, OathGold, OathGold * 0.2f, 0.3f, sprite: Sprites.Range("star").First + 3 + 1, spinV: 2);
                break;
            case "mote" or "mote_cascade" or "mote_star":
                Sparks.Spawn(at, Vector3.Zero, 0.16f, 0.8f * g, art == "mote_cascade" ? FenLight : Hdr("#e070ff", 2.6f), null, 0.2f, sprite: Sprites.Range("star").First + 2 + 1, spinV: 3);
                break;
            case "shard" or "shard_deep" or "spear_ice":
                Sparks.Spawn(at, Vector3.Zero, 0.2f, 0.9f * g, Hdr("#bfe8ff", 2.4f), null, 0.3f, sprite: Sprites.Range("star").First + 1, spinV: 1);
                // Where it breaks, the cold takes the ground under the body: a few points of ice.
                Erupt(e.X, e.Z, 0.1f, 0.55f + share * 0.4f, 3 + (int)(share * 4), SpikeKind.Ice, 0.55f * g, 0.6f, Hdr("#8fd8ff", 1.3f));
                break;
        }
        // The skill's own burst at the body, small: a mote breaks in violet, a disc in gold, a shard in rime.
        var (book, tint) = art switch
        {
            "mote" or "mote_cascade" or "mote_star" or "moon" or "moon_brand" => ("arcane_burst", new Color(1.2f, 1.1f, 1.3f, 0.9f)),
            "disc" or "disc_aegis" or "disc_reckon" => ("holy_burst", new Color(1.2f, 1.1f, 0.85f, 0.9f)),
            "shard" or "shard_deep" or "spear_ice" => ("frost_burst", new Color(0.55f, 0.8f, 1.3f, 0.9f)),
            "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark" => ("shadow_burst", new Color(1.3f, 1.2f, 1.4f, 0.9f)),
            _ => ((string?)null, Colors.White),
        };
        if (book != null) Books.Spawn(book, at, 0.25f * g, 0.3f, tint, sizeEnd: (0.55f + share * 0.5f) * g);
        int n = (e.Crit ? 7 : 3) + (int)(share * 6);
        switch (school)
        {
            case School.Physical:
            {
                // Steel on flesh and bone: hot sparks thrown on along the blow.
                for (int i = 0; i < n; i++)
                {
                    var v = (away * (5 + R() * 6) + new Vector3((R() - 0.5f) * 5, 1.5f + R() * 3, (R() - 0.5f) * 5));
                    Sparks.Spawn(at, v, 0.18f + R() * 0.2f, 0.04f + R() * 0.03f, SteelWhite, Ember, 0.01f, 9, 2);
                }
                break;
            }
            case School.Fire:
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (2 + R() * 3) + new Vector3((R() - 0.5f) * 3, 2 + R() * 3, (R() - 0.5f) * 3), 0.4f + R() * 0.4f, 0.05f + R() * 0.05f, Ember, EmberDeep, 0.01f, -1.5f, 1.5f);
                break;
            case School.Frost:
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (3 + R() * 4) + new Vector3((R() - 0.5f) * 4, 1 + R() * 3, (R() - 0.5f) * 4), 0.35f + R() * 0.3f, 0.06f + R() * 0.06f, pal.Core, pal.Glow * 0.5f, 0.02f, 12, 1, sprite: Sprites.Of("star"), spinV: 8);
                break;
            case School.Storm:
                // A crackle: a short fork jumping off the body.
                Ribbons.Bolt(at, at + new Vector3((R() - 0.5f) * 1.6f, R() * 0.8f, (R() - 0.5f) * 1.6f), 0.06f, 0.1f, pal.Glow * 0.6f, 2.4f, 0, 0.4f);
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, new Vector3((R() - 0.5f) * 9, R() * 4, (R() - 0.5f) * 9), 0.12f + R() * 0.1f, 0.035f, pal.Core, pal.Glow, 0.01f, 6, 4);
                break;
            case School.Holy:
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (1 + R() * 2) + new Vector3((R() - 0.5f) * 2, 1.5f + R() * 2, (R() - 0.5f) * 2), 0.5f + R() * 0.4f, 0.07f + R() * 0.05f, pal.Core, pal.Glow, 0.01f, -0.5f, 2, sprite: R() < 0.4f ? Sprites.Of("star") : 0, spinV: 3);
                break;
            case School.Shadow:
            {
                bool blood = art.Contains("blood") || art.Contains("rend") || art.Contains("grave");
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at + new Vector3((R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.3f), away * (0.5f + R()) + Vector3.Up * (0.8f + R() * 1.4f),
                        0.55f + R() * 0.4f, 0.09f + R() * 0.06f, blood ? Blood : pal.Core, blood ? BloodDim : pal.Dim, 0.02f, -0.6f, 1.6f);
                break;
            }
            case School.Nature:
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (1 + R() * 2) + new Vector3((R() - 0.5f) * 3, 1 + R() * 2, (R() - 0.5f) * 3), 0.6f + R() * 0.4f, 0.06f + R() * 0.05f, pal.Core, pal.Glow * 0.5f, 0.02f, 1.5f, 2.2f);
                break;
            default:
                // Arcane: motes thrown off that hang and wink out.
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (1 + R() * 2.5f) + new Vector3((R() - 0.5f) * 3.5f, 0.5f + R() * 2.5f, (R() - 0.5f) * 3.5f), 0.45f + R() * 0.35f, 0.06f + R() * 0.05f, pal.Core, pal.Glow, 0.01f, -0.3f, 3.5f, sprite: R() < 0.35f ? Sprites.Of("star") : 0, spinV: 5);
                break;
        }
    }

    /* ------------------------------------------------------------ release -- */

    /// <summary>A skill leaving the hand: a small flourish of its own where it
    /// starts, so a volley reads as loosed and a spell as cast.</summary>
    void Release(Ev.Muzzle e)
    {
        float gy = Y(e.X, e.Z);
        var dir = new Vector3(Mathf.Cos((float)e.Angle), 0, Mathf.Sin((float)e.Angle));
        var hand = V(e.X, gy + 1.15, e.Z) + dir * 0.55f;
        var pal = Palette.Of(e.School);
        string art = e.Art ?? "";
        float g = Grow(e.Rank);
        switch (art)
        {
            case "arrow" or "arrow_mark" or "arrow_rain":
                // The string's snap: a pale streak forward and a puff of grit.
                Sparks.Spawn(hand, dir * 6, 0.07f, 0.35f * g, SteelWhite * 0.6f, null, 0.1f, sprite: Sprites.Of("light"));
                break;
            case "mote" or "mote_cascade" or "mote_star" or "moon" or "moon_brand":
                // A spell spoken: a turning glyph of light at the hand.
                Sparks.Spawn(hand + Vector3.Up * 0.1f, Vector3.Zero, 0.26f, 0.85f * g, (art.StartsWith("moon") ? Moon : art == "mote_cascade" ? FenLight : pal.Core) * 0.7f, pal.Glow * 0.2f, 0.9f * g, sprite: Sprites.Of("magic"), spinV: 6);
                break;
            case "cinder" or "living_flame" or "star":
                Books.Spawn("fire_blast", hand, 0.5f * g, 0.35f, new Color(1.4f, 1.4f, 1.4f, 0.9f), sizeEnd: 1.1f * g);
                for (int i = 0; i < 6; i++) Sparks.Spawn(hand, dir * (2 + R() * 3) + new Vector3((R() - 0.5f) * 2, 1 + R() * 2, (R() - 0.5f) * 2), 0.4f, 0.05f, Ember, EmberDeep, 0.01f, -1, 1.5f);
                break;
            case "shard" or "shard_deep" or "spear_ice":
                for (int i = 0; i < 6; i++) Sparks.Spawn(hand, dir * (1 + R() * 2) + new Vector3((R() - 0.5f) * 1.5f, R(), (R() - 0.5f) * 1.5f), 0.45f, 0.18f, pal.Glow * 0.15f, pal.Dim * 0.05f, 0.5f, 0, 2, 0.5f);
                Sparks.Spawn(hand, Vector3.Zero, 0.12f, 0.5f * g, pal.Core * 0.6f, null, 0.15f, sprite: Sprites.Of("star"), spinV: 4);
                break;
            case "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark":
                for (int i = 0; i < 5; i++) Sparks.Spawn(hand, dir * R() + Vector3.Up * (0.5f + R()), 0.5f, 0.14f, pal.Core * 0.6f, pal.Dim, 0.02f, -0.5f, 2);
                break;
            case "dagger" or "dagger_blood" or "dagger_flurry" or "disc" or "disc_aegis" or "disc_reckon" or "chakram" or "chakram_razor" or "chakram_hail":
                Sparks.Spawn(hand, dir * 3, 0.06f, 0.25f * g, SteelWhite * 0.4f, null, 0.05f, sprite: Sprites.Of("light"));
                break;
        }
    }

    /* -------------------------------------------------------------- blades -- */

    /// <summary>A blade's swing (and a palm's strike): the crescent of the
    /// swing in the skill's colours, sparks struck off its edge as it goes,
    /// grit kicked up under it; a cleaver's chop splits the ground where it
    /// ends; a full turn is a ring.</summary>
    void Swing(Ev.Slash e)
    {
        string art = e.Art ?? "";
        float g = Grow(e.Rank);
        float gy = Y(e.X, e.Z);
        var at = V(e.X, gy + 1.0, e.Z);
        float reach = (float)e.Reach;
        float facing = (float)(Math.PI / 2 - e.Angle);
        var pal = Palette.Of(e.School);
        Color core = pal.Core, glow = pal.Glow;
        float life = 0.22f;
        bool heavy = false, spin = e.Arc > 3;
        switch (art)
        {
            case "slash_steel": core = SteelWhite; glow = OathGold * 0.55f; break;
            case "slash_holy": core = Hdr("#fff6d8", 3f); glow = OathGold; break;
            case "slash_blood": core = Hdr("#ffd0c8", 2.4f); glow = Blood; break;
            case "slash_heavy": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d8a070", 1.5f); life = 0.26f; heavy = true; break;
            case "slash_quake": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d89060", 1.6f); life = 0.26f; heavy = true; break;
            case "slash_spin": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d8a070", 1.5f); life = 0.3f; heavy = true; break;
            case "palm" or "palm_temple": core = Hdr("#fff2d0", 2.6f); glow = Hdr("#ffb24a", 1.8f); life = 0.16f; break;
            case "palm_storm": core = Palette.Of(School.Storm).Core; glow = Palette.Of(School.Storm).Glow; life = 0.16f; break;
        }
        mirror = !mirror;
        // The blade's path, swept fast: a hot edge at the reach and a wake behind
        // it, drawn as it goes (a painted fan read as a flat disc of beige).
        float sweepSpan = spin ? Mathf.Tau * 1.05f : (float)e.Arc * 1.1f, start = (float)e.Angle - (mirror ? -1 : 1) * sweepSpan / 2;
        float dirSign = mirror ? -1 : 1;
        float swing = heavy ? 0.13f : 0.09f;
        sweeps.Add(new Sweep
        {
            C = at, R = reach, A0 = start, Span = sweepSpan * dirSign, Life = swing, Edge = core, Wake = glow,
            W = heavy ? 0.5f : 0.38f, G = g, Key = ++sweepKey * 2,
        });
        if (spin)
            sweeps.Add(new Sweep
            {
                C = at, R = reach * 0.8f, A0 = start + Mathf.Pi, Span = sweepSpan * dirSign, Life = swing * 1.1f, Edge = core, Wake = glow,
                W = 0.4f, G = g, Key = ++sweepKey * 2,
            });
        // Sparks struck off the edge, flung along the swing.
        int n = Math.Min(14, (int)(5 * g) + (heavy ? 4 : 0));
        float a0 = (float)e.Angle - (float)e.Arc / 2, span = spin ? Mathf.Tau : (float)e.Arc;
        for (int i = 0; i < n; i++)
        {
            float t = R(), a = a0 + span * t;
            var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var tan = new Vector3(-rim.Z, 0, rim.X) * (mirror ? -1 : 1);
            Sparks.Spawn(at + rim * reach * (0.75f + R() * 0.25f) + Vector3.Up * (R() - 0.5f) * 0.4f, tan * (4 + R() * 4) + rim * 2 + Vector3.Up * (1 + R() * 2),
                0.16f + R() * 0.18f, 0.035f + R() * 0.02f, core, glow * 0.6f, 0.01f, 7, 2.5f);
        }
        // Grit under the blade where it passes nearest the ground.
        if (heavy)
        {
            float mid = (float)e.Angle;
            var tip = new Vector3(Mathf.Cos(mid), 0, Mathf.Sin(mid)) * reach * 0.8f;
            double tx = e.X + tip.X, tz = e.Z + tip.Z;
            Dust(tx, tz, 8, 3.5f * g);
            Cam?.AddTrauma(0.05f);
            if (art != "slash_spin")
            {
                // The chop bites the ground: a crack where it ends, a few clods thrown.
                Scars.Add("crack", V(tx, Y(tx, tz), tz), 0.9f * g, 4f, 0);
                for (int i = 0; i < 5; i++)
                    Smoke.Spawn(V(tx, Y(tx, tz) + 0.2, tz), new Vector3((R() - 0.5f) * 3, 2.5f + R() * 2.5f, (R() - 0.5f) * 3), 0.6f, 0.1f + R() * 0.08f, new Color("#4a3a2a"), gravity: 14, sprite: Sprites.Of("dirt"), spinV: 4);
            }
        }
        else if (R() < 0.5f) Dust(e.X + Math.Cos(e.Angle) * reach * 0.6, e.Z + Math.Sin(e.Angle) * reach * 0.6, 2, 1.8f);
        // The Watch's oath along the edge of a ranked Oathblade: a few gold glints that hang.
        if (art is "slash_steel" or "slash_holy" && e.Rank >= 5)
            for (int i = 0; i < 4; i++)
            {
                float a = a0 + span * R();
                var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + rim * reach * 0.95f, Vector3.Up * 0.4f, 0.5f, 0.12f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
    }

    /// <summary>A blade's swing in progress: its tip carried round the arc
    /// over its life, a ribbon behind the edge and a wider, fainter one behind
    /// the flat, fed several points a frame so the curve stays round.</summary>
    struct Sweep
    {
        public Vector3 C;
        public float R, A0, Span, Life, Age, W, G;
        public Color Edge, Wake;
        public long Key;
    }

    readonly System.Collections.Generic.List<Sweep> sweeps = new();
    long sweepKey = 1L << 40;

    void StepSweeps(float dt)
    {
        for (int i = sweeps.Count - 1; i >= 0; i--)
        {
            var s = sweeps[i];
            float t0 = s.Age / s.Life;
            s.Age += dt;
            float t1 = Mathf.Min(1, s.Age / s.Life);
            if (t0 >= 1) { sweeps.RemoveAt(i); continue; }
            sweeps[i] = s;
            const int Sub = 6;
            for (int k = 1; k <= Sub; k++)
            {
                float t = Mathf.Lerp(t0, t1, k / (float)Sub);
                // Fast out of the wind-up, slowing through the follow.
                float e = 1 - (1 - t) * (1 - t);
                float a = s.A0 + s.Span * e;
                var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                float ago = (1 - k / (float)Sub) * dt;
                Ribbons.Feed(s.Key, s.C + dir * s.R * 0.97f, 0.14f * s.G, 0.12f, new Color(s.Edge.R / 3, s.Edge.G / 3, s.Edge.B / 3), 3f, Ribbons.Style.Steel, ago);
                Ribbons.Feed(s.Key + 1, s.C + dir * s.R * 0.74f, s.R * s.W * s.G, 0.1f, new Color(s.Wake.R / 3, s.Wake.G / 3, s.Wake.B / 3), 1.3f, Ribbons.Style.Wisp, ago);
            }
        }
    }

    /* -------------------------------------------------------- in the air -- */

    /// <summary>A projectile of the survivor's, drawn as its skill: its body
    /// (a mesh for what is thrown or shot, light for what is cast), its trail
    /// and what it sheds. False for what this does not draw (the caller's
    /// plain glow).</summary>
    bool Flight(Projectile p, Vector3 at, float heading, double now, float dt)
    {
        string art = p.Art;
        float g = Grow(p.Rank);
        var pal = Palette.Of(p.School);
        long key = p.Id * 7919L + (long)(p.Art.GetHashCode() & 0xffff);
        var fwd = new Vector3(Mathf.Sin(heading), 0, Mathf.Cos(heading));
        switch (art)
        {
            case "arrow" or "arrow_mark":
            {
                var basis = new Godot.Basis(Vector3.Up, heading);
                steel.Add(new Transform3D(basis, at), art == "arrow_mark" ? new Color(1.2f, 0.8f, 0.6f) : new Color(0.9f, 0.88f, 0.82f));
                // A pale streak behind it: an arrow is read by its line, not its shaft.
                Ribbons.Feed(key, at, 0.2f * g, 0.18f, art == "arrow_mark" ? Hdr("#ff9a5a", 1f) : Hdr("#fff4e0", 1f), 2.2f, Ribbons.Style.Steel);
                if (art == "arrow_mark") Sparks.Spawn(at, Vector3.Zero, 0.05f, 0.35f, Hdr("#ff7a3a", 2.2f), null, 0.2f);
                return true;
            }
            case "dagger" or "dagger_blood" or "dagger_flurry":
            {
                var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * new Godot.Basis(Vector3.Up, (float)(now * 9 + p.Id));
                daggers.Add(new Transform3D(basis, at), Colors.White);
                var c = art == "dagger_blood" ? Hdr("#ff4a3a", 1f) : Hdr("#fff4e0", 1f);
                Ribbons.Feed(key, at, 0.22f * g, 0.16f, c, art == "dagger_flurry" ? 2.8f : 2.3f, Ribbons.Style.Steel);
                return true;
            }
            case "axe" or "axe_blood" or "axe_storm":
            {
                var basis = new Godot.Basis(Vector3.Up, -(float)(now * 16 + p.Id)) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * Godot.Basis.FromScale(Vector3.One * 1.3f * Mathf.Sqrt(g));
                axes.Add(new Transform3D(basis, at), Colors.White);
                // The orbit's wake: a curved streak behind each head, as the eye sees a spinning blade.
                if (art == "axe_storm") Ribbons.Feed(key, at, 0.75f * g, 0.22f, Wind, 0.9f, Ribbons.Style.Wisp);
                else Ribbons.Feed(key, at, 0.4f * g, 0.16f, art == "axe_blood" ? Hdr("#ff3a2a", 1f) : Hdr("#fff0e0", 1f), art == "axe_blood" ? 1.8f : 1.3f, Ribbons.Style.Steel);
                if (art == "axe_blood" && R() < 0.25f) Sparks.Spawn(at, Vector3.Up * 0.5f, 0.5f, 0.06f, Blood, BloodDim, 0.02f, 9);
                return true;
            }
            case "disc" or "disc_aegis" or "disc_reckon":
            {
                float s = 1.1f * Mathf.Sqrt(g) * (art == "disc_reckon" ? 1.15f : 1);
                var gold = art == "disc_aegis" ? Hdr("#e8f0ff", 1.4f) : OathGold * 0.5f;
                rings.Add(new Transform3D(new Godot.Basis(Vector3.Up, (float)(now * 16)).Scaled(Vector3.One * s), at), gold);
                // The sun it carries: a hot core in a wide warm halo, and a gold wake.
                Shade(at, 1.9f * s, 0.55f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.5f * s), at), pal.Core * 0.7f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 1.15f * s), at), pal.Glow * 0.12f);
                Ribbons.Feed(key, at, 0.55f * s, 0.3f, art == "disc_aegis" ? Hdr("#cfe0ff", 1f) : Hdr("#ffd27a", 1f), 2f, Ribbons.Style.Glow);
                if (R() < 0.3f) Sparks.Spawn(at, new Vector3((R() - 0.5f), 0.6f, (R() - 0.5f)), 0.5f, 0.07f, pal.Core, pal.Glow, 0.01f, -0.4f, 1.5f, sprite: Sprites.Of("star"), spinV: 4);
                return true;
            }
            case "chakram" or "chakram_razor" or "chakram_hail":
            {
                float s = 0.8f * Mathf.Sqrt(g);
                var tint = art == "chakram_hail" ? Palette.Of(School.Frost).Glow * 0.5f : new Color(0.9f, 0.95f, 0.92f);
                Shade(at, 1.4f * s, 0.5f);
                rings.Add(new Transform3D(new Godot.Basis(Vector3.Up, (float)(now * 22)).Scaled(Vector3.One * s), at), tint);
                // Gale Chakram rides the wind: a pale curl of air behind it.
                Ribbons.Feed(key, at, 0.55f * s, 0.25f, art == "chakram_hail" ? Hdr("#bfe6ff", 1f) : Hdr("#e8f8f0", 1f), art == "chakram_razor" ? 1.6f : 1.1f,
                    art == "chakram_hail" ? Ribbons.Style.Frost : art == "chakram_razor" ? Ribbons.Style.Steel : Ribbons.Style.Wisp);
                return true;
            }
            case "mote" or "mote_cascade" or "mote_star" or "ember_seeker":
            {
                // A will-o'-the-wisp: a hot point that wavers, and the line of its hunting behind it.
                var c = art == "mote_cascade" ? FenLight : art == "mote_star" ? Hdr("#fff0ff", 3f) : pal.Core;
                var gw = art == "mote_cascade" ? Hdr("#3affc0", 2f) : pal.Glow;
                float s = 0.3f * g * (art == "mote_star" ? 1.3f : 1);
                var wob = new Vector3(Mathf.Sin((float)now * 23 + p.Id), Mathf.Sin((float)now * 17 + p.Id * 3) * 0.6f, Mathf.Cos((float)now * 19 + p.Id)) * 0.06f;
                Shade(at + wob, s * 2.6f, 0.6f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.55f), at + wob), c);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 2.4f), at + wob), gw * 0.2f);
                Ribbons.Feed(key, at + wob, 0.22f * g, 0.24f, new Color(gw.R / 2.2f, gw.G / 2.2f, gw.B / 2.2f), 2.6f, Ribbons.Style.Glow);
                // Its heart a four-pointed star that twinkles as it hunts.
                Sparks.Spawn(at + wob, Vector3.Zero, 0.05f, s * (1.5f + 0.4f * Mathf.Sin((float)now * 40 + p.Id)), c * 0.6f, null, s * 1.2f, sprite: Sprites.Range("star").First + 2 + 1, spinV: 0);
                if (art == "mote_star" && R() < 0.4f) Sparks.Spawn(at, Vector3.Zero, 0.25f, 0.28f * g, c * 0.5f, null, 0.05f, sprite: Sprites.Of("star"), spinV: 6);
                else if (R() < 0.2f) Sparks.Spawn(at, new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f), 0.35f, 0.05f, c, gw, 0.01f, 0, 2);
                return true;
            }
            case "moon" or "moon_brand" or "moonfall":
            {
                float s = 0.75f * g;
                Shade(at, s * 2.4f, 0.6f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.6f), at), Moon);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 2.2f), at), Hdr("#9a7aff", 1f) * 0.25f);
                Sparks.Spawn(at, Vector3.Zero, 0.06f, s * 1.1f, Moon * 0.35f, null, s * 1.1f, sprite: Sprites.Of("twirl"), spinV: 0);
                Ribbons.Feed(key, at, 0.45f * g, 0.36f, Hdr("#b8a8ff", 1f), 2.2f, Ribbons.Style.Glow);
                return true;
            }
            case "cinder" or "living_flame" or "star":
            {
                // A burning coal: flame streaming off it, embers shed behind, a little smoke.
                bool star = art == "star", small = art == "living_flame";
                float s = (star ? 1.25f : small ? 0.55f : 0.85f) * g;
                Shade(at, s * 2.2f, 0.45f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.45f), at), star ? Hdr("#fff4e0", 4f) : Hdr("#ffe0a0", 3.5f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.9f), at), Hdr("#ff6a1a", 2f) * 0.22f);
                Ribbons.Feed(key, at, 0.55f * s, star ? 0.4f : 0.28f, Hdr("#ff8a2a", 1f), 2.4f, Ribbons.Style.Flame);
                if (p.Weapon == "frostfire_comet") Ribbons.Feed(key ^ 0x55aa, at + Vector3.Up * 0.05f, 0.35f * s, 0.35f, Hdr("#a8dcff", 1f), 2f, Ribbons.Style.Frost);
                trailAcc.TryGetValue(p.Id, out var acc);
                acc += dt * (star ? 50 : 30);
                while (acc >= 1)
                {
                    acc -= 1;
                    if (R() < 0.35f) Books.Spawn("fire_loop", at + new Vector3((R() - 0.5f) * 0.1f, 0, (R() - 0.5f) * 0.1f), 0.5f * s, 0.22f, new Color(1.5f, 1.5f, 1.5f, 0.85f), sizeEnd: 0.15f * s, v: Vector3.Up * 0.8f);
                    Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 1.2f, 0.6f + R(), (R() - 0.5f) * 1.2f), 0.4f + R() * 0.3f, 0.04f + R() * 0.03f, Ember, EmberDeep, 0.01f, -1.2f, 1.5f);
                    if (R() < 0.15f) Smoke.Spawn(at + Vector3.Up * 0.2f, Vector3.Up * 0.6f, 0.9f, 0.25f * s, new Color(0.3f, 0.27f, 0.25f), new Color(0.15f, 0.14f, 0.13f), 0.7f * s, drag: 1, alpha: 0.35f);
                }
                trailAcc[p.Id] = acc;
                return true;
            }
            case "shard" or "shard_deep" or "spear_ice":
            {
                float s = (art == "spear_ice" ? 2.4f : art == "shard_deep" ? 1.2f : 1) * Mathf.Sqrt(g);
                var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2);
                Shade(at, 1.3f * s, 0.55f);
                shards.Add(new Transform3D(basis.Scaled(Vector3.One * s), at), pal.Glow * 0.6f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.9f * s), at), pal.Glow * 0.12f);
                Ribbons.Feed(key, at, (art == "spear_ice" ? 0.7f : 0.34f) * s, art == "spear_ice" ? 0.45f : 0.24f, Hdr("#7cc8ff", 1f), 2.2f, Ribbons.Style.Frost);
                // Glints of frost shed behind it (not smoke: puffs in a line read as litter).
                if (R() < 0.35f) Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 0.6f, (R() - 0.5f) * 0.4f, (R() - 0.5f) * 0.6f), 0.35f, 0.07f, Hdr("#dff4ff", 2.2f), Hdr("#5ab4ff", 1.2f), 0.02f, 2, 2, sprite: Sprites.Of("star"), spinV: 6);
                return true;
            }
            case "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark":
            {
                // Shadow: a dark heart with a violet rim, and a wisp that drinks the light behind it.
                bool ruin = art == "ruin", lantern = p.Weapon == "soul_lantern";
                float s = (ruin ? 0.8f : 0.55f) * g;
                var rim = lantern ? Hdr("#b8ffe0", 2.2f) : art == "siphon" ? Hdr("#d070ff", 2.4f) : pal.Glow;
                Shade(at, s * 2.4f, 0.75f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.5f), at), lantern ? Hdr("#e8fff4", 3f) : pal.Core * 0.7f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.8f), at), rim * 0.2f);
                Ribbons.Feed(key, at, 0.62f * s, ruin ? 0.55f : 0.42f, new Color(rim.R / 3, rim.G / 3, rim.B / 3), 1.6f, Ribbons.Style.Wisp);
                // The tether: a thread back to the hand that cast it.
                if (art.StartsWith("tether") && b0 != null)
                {
                    var hand = V(b0.Player.X, Y(b0.Player.X, b0.Player.Z) + 1.15, b0.Player.Z);
                    var mid = (hand + at) / 2 + Vector3.Up * 0.3f + new Vector3(Mathf.Sin((float)now * 7 + p.Id), 0, Mathf.Cos((float)now * 6 + p.Id)) * 0.25f;
                    Ribbons.Now(new[] { hand, (hand + mid) / 2, mid, (mid + at) / 2, at }, 0.07f, Hdr("#b080ff", 1f), 1.6f, Ribbons.Style.Wisp, new[] { 0.3f, 0.8f, 1f, 0.8f, 0.5f });
                }
                if (R() < 0.35f) Smoke.Spawn(at, -fwd * 0.3f + Vector3.Up * 0.2f, 0.6f, 0.2f * s, pal.Dim * 2f, pal.Dim, 0.45f * s, drag: 1.5f, alpha: 0.45f);
                return true;
            }
            case "crescent_holy":
            {
                // Oathkeeper's thrown crescent: a sweep of gold flying flat, edge first.
                var side = new Vector3(fwd.Z, 0, -fwd.X);
                var pts = new Vector3[7];
                var w = new float[7];
                for (int i = 0; i < 7; i++)
                {
                    float u = i / 6f * 2 - 1;
                    pts[i] = at + side * u * 1.1f * g - fwd * (u * u) * 0.55f * g;
                    w[i] = 1 - u * u * 0.85f;
                }
                Ribbons.Now(pts, 0.32f * g, Hdr("#ffd27a", 1f), 2.6f, Ribbons.Style.Glow, w);
                Ribbons.Feed(key, at, 0.9f * g, 0.18f, Hdr("#ffb84a", 1f), 0.9f, Ribbons.Style.Glow);
                return true;
            }
            case "firepot":
                return false;
        }
        return false;
    }

    /// <summary>A dark soft bed under a bright core (drawn first), so it shows over the pale dead.</summary>
    void Shade(Vector3 at, float size, float a) =>
        shades.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * size), at), new Color(0.02f, 0.015f, 0.035f, a));

    /// <summary>The battle being drawn (for what is drawn relative to the survivor).</summary>
    Battle? b0;

    /* ------------------------------------------------------ rings of light -- */

    /// <summary>A ring racing out over the ground, drawn as a ribbon round its
    /// edge (sharp where a decal is soft): dawn's ring, a frost front, the
    /// lip of a blast.</summary>
    struct Front
    {
        public Vector3 At;
        public float Radius, Life, Age, Width, Energy, Start;
        public Color Color;
        public Ribbons.Style Style;
    }

    readonly System.Collections.Generic.List<Front> fronts = new();

    void AddFront(Vector3 at, float radius, float life, float width, Color color, float energy, Ribbons.Style style = Ribbons.Style.Glow, float start = 0.15f)
    {
        if (fronts.Count < 48) fronts.Add(new Front { At = at, Radius = radius, Life = life, Width = width, Color = color, Energy = energy, Style = style, Start = start });
    }

    void StepFronts(float dt)
    {
        for (int i = fronts.Count - 1; i >= 0; i--)
        {
            var f = fronts[i];
            f.Age += dt;
            if (f.Age >= f.Life) { fronts.RemoveAt(i); continue; }
            fronts[i] = f;
            float k = f.Age / f.Life, ease = 1 - (1 - k) * (1 - k) * (1 - k);
            float r = f.Radius * (f.Start + (1 - f.Start) * ease);
            const int N = 56;
            var pts = new Vector3[N + 1];
            var w = new float[N + 1];
            for (int j = 0; j <= N; j++)
            {
                float a = j / (float)N * Mathf.Tau;
                double x = f.At.X + Mathf.Cos(a) * r, z = f.At.Z + Mathf.Sin(a) * r;
                pts[j] = V(x, Y(x, z) + 0.25, z);
                w[j] = 1;
            }
            Ribbons.Now(pts, f.Width * (1 - 0.5f * k), f.Color, f.Energy * (1 - k) * (k < 0.08f ? k / 0.08f : 1), f.Style, w);
        }
    }

    /* --------------------------------------------------------------- novas -- */

    /// <summary>A skill that bursts out from the survivor, drawn as itself:
    /// Hoarfrost a front of rime racing over the ground with ice thrown low
    /// and cold rolling after; Dawnpulse a ring of dawn with rays and a sigil
    /// burned in the ground; Reaving Arc a scythe of shadow swept round, the
    /// blood it takes drawn back in.</summary>
    bool Pulse(Ev.Nova e)
    {
        string art = e.Art ?? "";
        float r = (float)e.Radius, g = Grow(e.Rank);
        float gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        int rings = Math.Max(1, e.Rings ?? 1);
        switch (art)
        {
            case "nova_frost":
            {
                var f = Palette.Of(School.Frost);
                var ice = Hdr("#9fe0ff", 1f);
                AddFront(ground, r, 0.45f, 0.5f * g, ice, 2.2f, Ribbons.Style.Frost);
                if (rings > 1) AddFront(ground, r * 0.7f, 0.55f, 0.3f, ice, 1.4f, Ribbons.Style.Frost);
                Books.Spawn("frost_burst", ground + Vector3.Up * 0.4f, r * 0.9f, 0.55f, new Color(0.5f, 0.75f, 1.2f, 0.85f), flat: true, sizeEnd: r * 2.1f);
                Waves.Add(ground + Vector3.Up * 0.3f, r * 1.2f, 0.4f, f.Glow, 0.8f);
                // Ice flung low over the ground, and the cold rolling out after it.
                int n = Math.Min(40, (int)(14 * g + r * 3));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, v = r * (1.6f + R() * 1.4f);
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Sparks.Spawn(ground + Vector3.Up * 0.4f + dir * 0.4f, dir * v + Vector3.Up * (0.5f + R() * 1.5f), 0.4f + R() * 0.25f, 0.07f + R() * 0.07f, f.Core, f.Glow * 0.4f, 0.02f, 8, 2.5f, sprite: Sprites.Of("star"), spinV: 9);
                }
                for (int i = 0; i < 10; i++)
                {
                    float a = i / 10f * Mathf.Tau + R() * 0.4f;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Smoke.Spawn(ground + Vector3.Up * 0.3f + dir * r * 0.3f, dir * r * 1.4f + Vector3.Up * 0.2f, 0.9f, r * 0.25f, new Color(0.78f, 0.9f, 1f), new Color(0.6f, 0.75f, 0.95f), r * 0.6f, drag: 2.2f, alpha: 0.22f);
                }
                // The front leaves ice standing in it: a ring of crystal points, leaning out, gone in a second.
                Erupt(e.X, e.Z, r * 0.35f, r * 0.95f, 14 + rings * 5, SpikeKind.Ice, 1.0f * g, 0.95f, Hdr("#8fd8ff", 1.3f));
                Scars.Add("frost", ground, r * 0.85f, 3.5f, 0);
                Flash(ground + Vector3.Up * 1.2f, f.Light, 6, 0.35f, r * 2.5f);
                return true;
            }
            case "nova_holy" or "nova_dawn" or "nova_sun":
            {
                var h = Palette.Of(School.Holy);
                var gold = Hdr("#ffd27a", 1f);
                AddFront(ground, r, 0.4f, 0.42f * g, gold, 3f, Ribbons.Style.Glow, 0.1f);
                for (int k = 1; k < rings; k++) AddFront(ground, r * (1 - 0.18f * k), 0.4f + 0.08f * k, 0.22f, gold, 1.8f, Ribbons.Style.Glow, 0.1f);
                Books.Spawn("holy_burst", ground + Vector3.Up * 0.5f, r * 0.6f, 0.45f, new Color(1.1f, 1.0f, 0.75f, 0.8f), flat: true, sizeEnd: r * 1.5f);
                // Rays: short strokes of light thrown outward along the ground.
                int n = 10 + rings * 4;
                for (int i = 0; i < n; i++)
                {
                    float a = (i + R() * 0.5f) / n * Mathf.Tau;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    var from = ground + Vector3.Up * 0.4f + dir * r * 0.25f;
                    Ribbons.Line(new[] { from, from + dir * r * 0.4f, from + dir * r * 0.8f }, 0.16f * g, 0.25f, gold, 2.2f, Ribbons.Style.Glow, new[] { 0f, 1f, 0f });
                }
                for (int i = 0; i < 12; i++)
                {
                    float a = R() * Mathf.Tau, d = r * (0.3f + R() * 0.7f);
                    Sparks.Spawn(ground + new Vector3(Mathf.Cos(a) * d, 0.3f, Mathf.Sin(a) * d), Vector3.Up * (1 + R() * 1.5f), 0.7f + R() * 0.4f, 0.08f, h.Core, h.Glow, 0.02f, -0.4f, 1.5f, sprite: R() < 0.5f ? Sprites.Of("star") : 0, spinV: 3);
                }
                Scars.Add("sigil", ground, r * 0.7f, art == "nova_sun" ? 3 : 1.4f, 0.6f);
                Flash(ground + Vector3.Up * 1.5f, h.Light, 7, 0.4f, r * 2.5f);
                return true;
            }
            case "nova_blood" or "nova_rend" or "nova_harrow":
            {
                // The arc is swept round at the edge of its reach, twice, crimson in shadow.
                var at = ground + Vector3.Up * 1.0f;
                var core = Hdr("#ffb0c0", 2.4f);
                var glow = art == "nova_harrow" ? Hdr("#9a5cff", 2.4f) : Hdr("#c4142a", 2.4f);
                float facing = R() * Mathf.Tau;
                Hits.Arc(at, facing, r, 0.28f, false, core, glow);
                Hits.Arc(at, facing + Mathf.Pi, r, 0.28f, false, core, glow);
                if (rings > 1) Hits.Arc(at, facing + Mathf.Pi / 2, r * 0.75f, 0.32f, true, core, glow * 0.7f);
                AddFront(ground, r, 0.3f, 0.3f * g, new Color(glow.R / 3, glow.G / 3, glow.B / 3), 1.8f, Ribbons.Style.Wisp, 0.6f);
                // What it takes, drawn back in to the survivor.
                int n = Math.Min(30, (int)(12 * g));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, d = r * (0.75f + R() * 0.3f);
                    var from = ground + new Vector3(Mathf.Cos(a) * d, 0.8f + R() * 0.6f, Mathf.Sin(a) * d);
                    Sparks.Spawn(from, (at - from) * (1.6f + R() * 0.6f), 0.55f, 0.09f + R() * 0.05f, art == "nova_harrow" ? Palette.Of(School.Shadow).Core : Blood, BloodDim, 0.03f, 0, 0.5f);
                }
                for (int i = 0; i < 6; i++)
                    Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r, 0.5f, (R() - 0.5f) * r), Vector3.Up * 0.4f, 0.8f, r * 0.25f, new Color(0.25f, 0.06f, 0.1f), new Color(0.1f, 0.02f, 0.05f), r * 0.5f, drag: 1.5f, alpha: 0.4f);
                Flash(at, glow, 5, 0.3f, r * 2);
                return true;
            }
        }
        return false;
    }

    /* ------------------------------------------------------ from the sky -- */

    /// <summary>A blow that falls (a storm's bolt, a moon, a rain of arrows,
    /// the ground split ahead of a chop): marked faintly while it comes, drawn
    /// as itself when it lands.</summary>
    bool Fall(Ev.Strike e)
    {
        string art = e.Art ?? "";
        if (art is not ("storm_bolt" or "storm_clap" or "storm_eye" or "arc_sky" or "moonfall" or "arrow_rain" or "slash_quake")) return false;
        float r = (float)e.Radius;
        if (e.Delay > 0.05)
        {
            // The survivor's own marks are quiet: a thin ring, so they never read as a threat.
            var pal = Palette.Of(e.School);
            if (art != "slash_quake") Ring(e.X, e.Z, r, pal.Glow * 0.35f, (float)e.Delay, true);
            var ev = e;
            pending.Add((time + e.Delay, () => Landing(ev)));
        }
        else Landing(e);
        return true;
    }

    void Landing(Ev.Strike e)
    {
        string art = e.Art ?? "";
        float r = (float)e.Radius, g = Grow(e.Rank);
        float gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        var pal = Palette.Of(e.School);
        switch (art)
        {
            case "storm_bolt" or "storm_clap" or "storm_eye" or "arc_sky":
            {
                bool clap = art == "storm_clap", small = art == "arc_sky";
                var top = ground + new Vector3((R() - 0.5f) * 3, small ? 9 : 16, (R() - 0.5f) * 3);
                var col = Hdr("#8ab4ff", 1f);
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 0.55f : small ? 0.22f : 0.38f) * g, clap ? 0.3f : 0.22f, col, 4f, small ? 1 : 3, 0.18f);
                // The fork it throws along the ground where it lands.
                for (int i = 0; i < (clap ? 5 : 3); i++)
                {
                    float a = R() * Mathf.Tau, d = r * (0.9f + R() * 0.8f);
                    double x = e.X + Mathf.Cos(a) * d, z = e.Z + Mathf.Sin(a) * d;
                    Ribbons.Bolt(ground + Vector3.Up * 0.25f, V(x, Y(x, z) + 0.2, z), 0.12f * g, 0.16f, col, 2.6f, 0, 0.3f);
                }
                Blast(e.X, e.Z, School.Storm, Mathf.Max(1.1f, r) * (clap ? 1.3f : 1), 0.55f, light: small);
                if (clap) { Waves.Add(ground + Vector3.Up * 0.3f, r * 2.2f, 0.4f, pal.Glow, 1.2f); Cam?.AddTrauma(0.12f); }
                Flash(ground + Vector3.Up * 3, pal.Light, small ? 6 : 12 * g, 0.22f, small ? 8 : 14);
                return;
            }
            case "moonfall":
            {
                // A moon falling: a pale streak down out of the dark, and the burst where it breaks.
                var top = ground + new Vector3(-2.5f, 14, 1.5f);
                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.45f * g, 0.25f, Hdr("#c8b8ff", 1f), 2.6f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                Blast(e.X, e.Z, School.Arcane, Mathf.Max(1.2f, r), 0.6f);
                AddFront(ground, r * 1.3f, 0.35f, 0.25f * g, Hdr("#c8b8ff", 1f), 2.2f, Ribbons.Style.Glow, 0.2f);
                return;
            }
            case "arrow_rain":
            {
                // A fistful of arrows coming down at a slant, each a streak, and the grit they throw.
                var slant = new Vector3(1.2f, -6, 0.6f).Normalized();
                for (int i = 0; i < 5; i++)
                {
                    var hit = ground + new Vector3((R() - 0.5f) * r * 1.6f, 0.1f, (R() - 0.5f) * r * 1.6f);
                    Ribbons.Line(new[] { hit - slant * 3.5f, hit - slant * 1.5f, hit }, 0.08f, 0.16f, Hdr("#fff4e0", 1f), 2.2f, Ribbons.Style.Steel, new[] { 0f, 0.7f, 1f });
                    Sparks.Spawn(hit + Vector3.Up * 0.2f, Vector3.Up * 2 + new Vector3(R() - 0.5f, 0, R() - 0.5f) * 3, 0.25f, 0.05f, SteelWhite, Ember, 0.01f, 9, 2);
                }
                Dust(e.X, e.Z, 8, 3f);
                return;
            }
            case "slash_quake":
            {
                // Bonesplitter: the ground split open ahead of the chop, stones thrown up.
                Scars.Add("crack", ground, r * 1.1f * g, 6f, 0);
                Erupt(e.X, e.Z, 0.2f, r * 0.9f, 7, SpikeKind.Stone, 0.9f * g, 0.9f, new Color(0.55f, 0.42f, 0.3f));
                Blast(e.X, e.Z, School.Physical, r, 0.6f);
                for (int i = 0; i < 10; i++)
                    Smoke.Spawn(ground + Vector3.Up * 0.3f, new Vector3((R() - 0.5f) * 4, 3 + R() * 4, (R() - 0.5f) * 4), 0.8f, 0.12f + R() * 0.1f, new Color("#5a4632"), gravity: 16, sprite: Sprites.Of("dirt"), spinV: 5);
                Cam?.AddTrauma(0.1f);
                return;
            }
        }
    }

    /* --------------------------------------------------------------- beams -- */

    /// <summary>A beam drawn as a lance of living light: a wide haze, a
    /// burning core, a flare at each end, and what it sheds along its length.</summary>
    bool Lance(Ev.Beam e)
    {
        string art = e.Art ?? "";
        if (!art.StartsWith("beam")) return false;
        float g = Grow(e.Rank);
        float y = Y(e.X0, e.Z0) + 1.2f;
        var a = V(e.X0, y, e.Z0);
        var b = V(e.X1, Y(e.X1, e.Z1) + 1.2, e.Z1);
        bool sun = art == "beam_sun";
        var col = sun ? Hdr("#ffd27a", 1f) : Hdr("#7aff5a", 1f);
        var pal = Palette.Of(sun ? School.Holy : School.Nature);
        float life = (float)Math.Max(0.2, e.Duration), w = (float)e.Width * g;
        var mid = new Vector3[9];
        for (int i = 0; i < 9; i++) mid[i] = a.Lerp(b, i / 8f);
        var even = new float[9];
        for (int i = 0; i < 9; i++) even[i] = i == 0 ? 0.3f : i == 8 ? 0.2f : 1;
        Ribbons.Line(mid, w * 1.6f, life, col, 1.2f, sun ? Ribbons.Style.Glow : Ribbons.Style.Flame, even);
        Ribbons.Line(mid, w * 0.45f, life * 0.9f, sun ? Hdr("#fff4d8", 1f) : Hdr("#e0ffd0", 1f), 3f, Ribbons.Style.Bolt, even);
        Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.9f * g, pal.Core * 0.7f, pal.Glow * 0.2f, 0.4f, sprite: Sprites.Of("flare"));
        Sparks.Spawn(b, Vector3.Zero, life * 0.6f, 0.7f * g, pal.Core * 0.5f, pal.Glow * 0.2f, 0.3f, sprite: Sprites.Of("flare"));
        for (int i = 0; i < 14; i++)
        {
            var at = a.Lerp(b, R());
            Sparks.Spawn(at, new Vector3((R() - 0.5f) * 1.5f, 0.5f + R(), (R() - 0.5f) * 1.5f), 0.6f + R() * 0.4f, 0.07f, pal.Core, pal.Glow, 0.02f, sun ? -0.4f : 1.5f, 2, sprite: sun && R() < 0.4f ? Sprites.Of("star") : 0, spinV: 3);
        }
        Flash(a.Lerp(b, 0.4f), pal.Light, 6, life, 12);
        return true;
    }

    /* -------------------------------------------------------------- spikes -- */

    /// <summary>What grows out of the ground for a moment: ice (Hoarfrost's
    /// front, a shard breaking), thorns (the brambles), stone (the ground a
    /// chop splits). Real shapes, lit, so they stand up out of the ground
    /// from the high camera as no flat picture can; each grows in a breath,
    /// stands, and sinks back.</summary>
    enum SpikeKind { Ice, Thorn, Stone }

    struct Spike
    {
        public Vector3 At;
        public Godot.Basis Turn;
        public float H, W, Age, Life;
        public SpikeKind Kind;
        public Color Color;
    }

    readonly System.Collections.Generic.List<Spike> spikes = new();
    Batch? iceSpikes, thornSpikes, stoneSpikes;

    void EnsureSpikes()
    {
        if (iceSpikes != null) return;
        Material Crystal(float emit, float rim, float gloss)
        {
            var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/crystal.gdshader") };
            m.SetShaderParameter("emit", emit);
            m.SetShaderParameter("rim", rim);
            m.SetShaderParameter("gloss", gloss);
            return m;
        }
        // A five-sided point (ice), a four-sided hook of a thorn, a blunt shard of stone; each one unit tall, its base at its origin.
        Mesh Point(int sides, float top) => new CylinderMesh { TopRadius = top, BottomRadius = 0.5f, Height = 1, RadialSegments = sides, Rings = 1, CapBottom = false };
        iceSpikes = Add(new Batch(Point(5, 0), 400, Crystal(0.45f, 2.6f, 0.05f), true));
        thornSpikes = Add(new Batch(Point(4, 0), 400, Crystal(0.12f, 1.4f, 0.5f), true));
        stoneSpikes = Add(new Batch(Point(5, 0.12f), 200, Crystal(0.02f, 0.4f, 0.8f), true));
    }

    /// <summary>A ring of spikes round (x, z) between radii r0 and r1, leaning out.</summary>
    void Erupt(double x, double z, float r0, float r1, int n, SpikeKind kind, float height, float life, Color color)
    {
        EnsureSpikes();
        for (int i = 0; i < n && spikes.Count < 900; i++)
        {
            float a = (i + R() * 0.8f) / n * Mathf.Tau, d = Mathf.Lerp(r0, r1, Mathf.Sqrt(R()));
            double sx = x + Mathf.Cos(a) * d, sz = z + Mathf.Sin(a) * d;
            var outward = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            float lean = (kind == SpikeKind.Stone ? 0.5f : 0.35f) + R() * 0.35f;
            // Leaning out from the middle, turned about itself.
            var axis = outward.Cross(Vector3.Up).Normalized();
            var turn = new Godot.Basis(axis, -lean) * new Godot.Basis(Vector3.Up, R() * Mathf.Tau);
            float h = height * (0.55f + R() * 0.6f) * (1.1f - 0.3f * (d - r0) / Mathf.Max(0.01f, r1 - r0));
            spikes.Add(new Spike
            {
                At = V(sx, Y(sx, sz) - 0.05, sz), Turn = turn, H = h, W = h * (kind == SpikeKind.Thorn ? 0.16f : kind == SpikeKind.Stone ? 0.5f : 0.3f),
                Life = life * (0.85f + R() * 0.3f), Kind = kind, Color = color, Age = -R() * 0.06f,
            });
        }
    }

    void StepSpikes(float dt)
    {
        if (iceSpikes == null) return;
        iceSpikes.Begin(); thornSpikes!.Begin(); stoneSpikes!.Begin();
        for (int i = spikes.Count - 1; i >= 0; i--)
        {
            var s = spikes[i];
            s.Age += dt;
            if (s.Age >= s.Life) { spikes.RemoveAt(i); continue; }
            spikes[i] = s;
            if (s.Age < 0) continue;
            // Up in a tenth of a second (overshooting a little), standing, then sinking back.
            float up = Mathf.Min(1, s.Age / 0.1f), grow = up < 1 ? 1 - (1 - up) * (1 - up) : 1;
            float sink = Mathf.Clamp((s.Age - (s.Life - 0.3f)) / 0.3f, 0, 1);
            float h = s.H * grow * (1 + 0.08f * Mathf.Sin(Mathf.Min(1, s.Age / 0.18f) * Mathf.Pi)), w = s.W * (0.6f + 0.4f * grow);
            var basis = s.Turn * Godot.Basis.FromScale(new Vector3(w, h, w));
            var at = s.At + Vector3.Down * s.H * sink * 0.9f + basis.Y * 0.5f;
            var c = s.Color with { A = 1 - sink };
            var batch = s.Kind == SpikeKind.Ice ? iceSpikes : s.Kind == SpikeKind.Thorn ? thornSpikes : stoneSpikes;
            batch.Add(new Transform3D(basis, at), c);
        }
        iceSpikes.End(); thornSpikes.End(); stoneSpikes.End();
    }

    /* -------------------------------------------------------------- ground -- */

    /// <summary>How each of the survivor's grounds looks: its colour, the
    /// pattern that lives inside it, and what rises from it. The rule (agreed
    /// with the experience director): no fill, a lit edge, a sparse living
    /// pattern inside at a third of strength at most, the creatures and the
    /// survivor always drawn over it, and never her red or the risen's grey.</summary>
    enum Inside { Runes, Veins, Roots, Embers }

    static (Color Edge, Inside Inside, float Turn) GroundLook(string art) => art switch
    {
        "zone_holy" or "zone_sanct" => (Hdr("#ffcf6a", 1.5f), Inside.Runes, 0.25f),
        "zone_pyre" => (Hdr("#ff8a2a", 1.6f), Inside.Embers, 0.2f),
        "zone_blight" or "zone_blight2" or "zone_plague" => (Hdr("#b8e04a", 1.3f), Inside.Veins, 0.04f),
        "zone_thorn" or "zone_bloom" or "zone_root" => (Hdr("#4ec85a", 1.3f), Inside.Roots, 0.03f),
        _ => (Colors.Transparent, Inside.Runes, 0),
    };

    readonly System.Collections.Generic.Dictionary<int, (Mark Edge, Mark Fill)> grounds = new();
    static Texture2D? rimTex, veinTex;

    /// <summary>A ground of the survivor's drawn to the rule above; false for
    /// one this does not know (drawn as before).</summary>
    bool SkillGround(GroundZone z, double now)
    {
        var (edgeCol, inside, turn) = GroundLook(z.Art);
        if (edgeCol.A == 0) return false;
        rimTex ??= RimTexture();
        veinTex ??= VeinTexture();
        float r = (float)z.Radius;
        if (!grounds.TryGetValue(z.Id, out var g) || !g.Edge.Active)
        {
            var fillTex = inside switch
            {
                Inside.Runes => Sprites.Runes(1),
                Inside.Embers => Sprites.Burning,
                Inside.Roots => GD.Load<Texture2D>("res://art/fx/marks/roots_emit.png"),
                _ => veinTex,
            };
            var fill = Ground(z.X, z.Z, r, fillTex, edgeCol, 1e6f, 1.0f);
            var edge = Ground(z.X, z.Z, r, rimTex, edgeCol, 1e6f, 2.2f);
            g = (edge, fill);
            grounds[z.Id] = g;
        }
        float fade = (float)Math.Clamp(Math.Min(z.Age / 0.25, (z.Life - z.Age) / 0.5), 0, 1);
        float breathe = 0.85f + 0.15f * Mathf.Sin((float)now * 2.4f + z.Id);
        var at = V(z.X, heightAt(z.X, z.Z), z.Z);
        foreach (var m in new[] { g.Edge, g.Fill })
        {
            m.T = 0;
            m.Decal.Position = at;
            m.Decal.Size = new Vector3(r * 2, 4, r * 2);
        }
        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe };
        // The pattern inside: a third of the edge's strength at most, turning slowly.
        g.Fill.Decal.Modulate = edgeCol with { A = fade * 0.32f };
        g.Fill.Decal.Rotation = new Vector3(0, (float)(now * turn + z.Id * 1.7), 0);
        // What lives in it, sparse.
        var pal = Palette.Of(Palette.OfArt(z.Art));
        if (R() < 0.12f + 0.03f * r)
        {
            float a = R() * Mathf.Tau, d = r * Mathf.Sqrt(R()) * 0.92f;
            double x = z.X + Mathf.Cos(a) * d, zz = z.Z + Mathf.Sin(a) * d;
            var foot = V(x, Y(x, zz) + 0.1, zz);
            switch (inside)
            {
                case Inside.Runes:
                    Sparks.Spawn(foot, Vector3.Up * (1 + R()), 1.1f, 0.08f, pal.Core * 0.8f, pal.Glow * 0.4f, 0.02f, 0, 0.5f, sprite: R() < 0.3f ? Sprites.Of("star") : 0, spinV: 2);
                    break;
                case Inside.Embers:
                    Sparks.Spawn(foot, Vector3.Up * (1.5f + R()), 0.8f, 0.06f, Ember, EmberDeep, 0.01f, -1, 1);
                    if (R() < 0.3f) Books.Spawn("fire_loop", foot + Vector3.Up * 0.35f, 0.7f, 0.8f, new Color(1.3f, 1.3f, 1.3f, 0.7f), sizeEnd: 0.3f);
                    break;
                case Inside.Veins:
                    // A bubble of the blight rising and breaking, and its fume low over the ground.
                    Sparks.Spawn(foot, Vector3.Up * 0.5f, 0.6f, 0.07f, edgeCol * 0.9f, edgeCol * 0.3f, 0.16f, 0, 1);
                    if (R() < 0.4f) Smoke.Spawn(foot + Vector3.Up * 0.15f, new Vector3((R() - 0.5f) * 0.4f, 0.12f, (R() - 0.5f) * 0.4f), 1.6f, 0.5f, new Color(0.45f, 0.6f, 0.15f), new Color(0.2f, 0.3f, 0.08f), 1.3f, drag: 1, alpha: 0.16f);
                    break;
                case Inside.Roots when R() < 0.35f:
                    // Thorns: brambles break the ground and sink again, here and there.
                    Erupt(x, zz, 0, 0.45f, 3, SpikeKind.Thorn, 0.9f, 1.6f, Hdr("#4ec85a", 1f));
                    break;
                default:
                    // Thorns: a green glint where a bramble catches the light.
                    Sparks.Spawn(foot + Vector3.Up * 0.2f, Vector3.Up * 0.3f, 0.5f, 0.1f, pal.Core * 0.6f, pal.Glow * 0.3f, 0.02f, 0, 1, sprite: Sprites.Of("star"), spinV: 2);
                    break;
            }
        }
        return true;
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {
        if (grounds.Count == 0) return;
        var gone = new System.Collections.Generic.List<int>();
        foreach (var (id, g) in grounds)
            if (!alive.Contains(id))
            {
                g.Edge.Active = false; g.Edge.Decal.Visible = false;
                g.Fill.Active = false; g.Fill.Decal.Visible = false;
                gone.Add(id);
            }
        foreach (var id in gone) grounds.Remove(id);
    }

    /// <summary>A lit edge and nothing inside it: a thin bright band, soft both ways.</summary>
    static Texture2D RimTexture()
    {
        const int N = 256;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v);
                float a = Mathf.Exp(-Mathf.Pow((r - 0.93f) / 0.022f, 2)) + 0.25f * Mathf.Exp(-Mathf.Pow((r - 0.9f) / 0.06f, 2));
                a = r > 0.985f ? 0 : Mathf.Clamp(a, 0, 1);
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>The blight's veins: thin branching lines in a ring-faded disc
    /// (ridges of layered noise), sparse, so the ground shows through.</summary>
    static Texture2D VeinTexture()
    {
        const int N = 256;
        var noise = new FastNoiseLite { NoiseType = FastNoiseLite.NoiseTypeEnum.Perlin, Frequency = 0.022f, FractalOctaves = 3, Seed = 7 };
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v);
                float n = Mathf.Abs(noise.GetNoise2D(x, y));
                float vein = Mathf.Clamp(1 - n / 0.06f, 0, 1);
                float a = vein * vein * Mathf.Clamp((0.9f - r) / 0.15f, 0, 1);
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /* ---------------------------------------------------------- lightning -- */

    /// <summary>Lightning leaping from body to body: each leg a forking bolt
    /// that flickers, a flare where it lands.</summary>
    bool Leap(Ev.Chain e)
    {
        var p = e.Points;
        if (p.Length < 4) return true;
        string art = e.Art ?? "";
        var pal = Palette.Of(e.School);
        float g = Grow(e.Rank);
        Color col = e.School switch
        {
            School.Storm => Hdr("#8ab4ff", 1f),
            School.Nature => Hdr("#8aff6a", 1f),
            School.Holy => Hdr("#ffd27a", 1f),
            School.Shadow => Hdr("#a070ff", 1f),
            _ => new Color(pal.Glow.R / 3, pal.Glow.G / 3, pal.Glow.B / 3),
        };
        for (int k = 0; k + 3 < p.Length; k += 2)
        {
            var a = V(p[k], Y(p[k], p[k + 1]) + 1.5, p[k + 1]);
            var bb = V(p[k + 2], Y(p[k + 2], p[k + 3]) + 1.3, p[k + 3]);
            if (e.School == School.Storm) Ribbons.Bolt(a, bb, 0.22f * g, 0.2f, col, 3.2f, art == "arc_fork" ? 2 : 1, 0.22f);
            else Ribbons.Line(new[] { a, (a + bb) / 2 + Vector3.Up * 0.4f, bb }, 0.12f * g, 0.25f, col, 2.2f, Ribbons.Style.Wisp);
            Sparks.Spawn(bb, Vector3.Zero, 0.1f, 0.7f * g, pal.Core * 0.8f, pal.Glow * 0.2f, 0.25f, sprite: Sprites.Of("flare"));
        }
        if (e.School == School.Storm) Flash(V(p[^2], Y(p[^2], p[^1]) + 2, p[^1]), pal.Light, 7 * g, 0.18f, 9);
        return true;
    }
}
