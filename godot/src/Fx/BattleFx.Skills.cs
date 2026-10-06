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
    int hitBudget, killBudget;
    double lastFall = -1, lastBlocked = -1;

    /// <summary>How much bigger and brighter a skill is drawn at its rank: a
    /// rank-8 skill a third again its rank-1 self.</summary>
    static float Grow(int rank) => 1 + 0.045f * Math.Clamp(rank - 1, 0, 9);

    static Color Hdr(string hex, float k) { var c = new Color(hex).SrgbToLinear(); return new Color(c.R * k, c.G * k, c.B * k); }

    // The hues the skills use beyond their schools' own (Palette): blood, the
    // Watch's gold edge, fen-light, moonlight.
    static readonly Color Blood = Hdr("#c01a14", 2.2f), BloodDim = Hdr("#4a0806", 1f), OathGold = Hdr("#ffcf6a", 2.6f),
        SteelWhite = Hdr("#f4f0e8", 2.4f), Moon = Hdr("#d8d4ff", 2.6f), FenLight = Hdr("#8affd8", 2.6f), Wind = Hdr("#dff2ec", 1.6f),
        Ember = new(2.6f, 1.15f, 0.3f), EmberDeep = new(1.5f, 0.28f, 0.05f), IceDeep = Hdr("#3d9cff", 1.15f);

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
        // Capped and kept in the school's colour: a big blow on a champion threw a white flare
        // two metres across that swallowed the bodies round it.
        float flare = Mathf.Min(1.3f, (0.45f + share * 0.9f) * (e.Crit ? 1.4f : 1) * g);
        Sparks.Spawn(at, Vector3.Zero, e.Crit ? 0.1f : 0.07f, flare, pal.Glow * (e.Crit ? 0.75f : 0.55f), pal.Glow * 0.2f, flare * 0.4f, sprite: Sprites.Of("flare"), spinV: 0);
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
            case "chakram" or "chakram_razor" or "chakram_hail":
                // A cut across the body in the wind's colour (its blood for Razorgale). Held low: a
                // ring of bodies cut at once at her feet summed to a pale glow at her hips.
                Sparks.Spawn(at, Vector3.Zero, 0.13f, 0.6f * g, art == "chakram_razor" ? Blood * 0.7f : art == "chakram_hail" ? Hdr("#9fd8ff", 1.15f) : Hdr("#a8f0d0", 1.1f), null, 0.75f * g, sprite: Sprites.Of("scratch"), spinV: 0);
                break;
            case "disc" or "disc_aegis" or "disc_reckon":
                if (e.Crit) Books.Spawn("gold_flare", at + Vector3.Up * 0.3f, 0.6f * g, 0.3f, new Color(1f, 0.85f, 0.55f, 0.85f), sizeEnd: 1.4f * g);
                Sparks.Spawn(at, Vector3.Zero, 0.18f, 1.1f * g, OathGold, OathGold * 0.2f, 0.3f, sprite: Sprites.Range("star").First + 3 + 1, spinV: 2);
                break;
            case "mote" or "mote_cascade" or "mote_star":
                Sparks.Spawn(at, Vector3.Zero, 0.16f, 0.8f * g, art == "mote_cascade" ? FenLight : Hdr("#e070ff", 2.6f), null, 0.2f, sprite: Sprites.Range("star").First + 2 + 1, spinV: 3);
                break;
            case "shard" or "shard_deep" or "spear_ice":
                // A star of frost where it strikes, blue, gone in a breath.
                Sparks.Spawn(at, Vector3.Zero, 0.22f, 0.45f * g, Hdr("#a8dcff", 1.7f), Hdr("#3d8cff", 0.8f), 0.75f * g, sprite: Sprites.Of("frost_star"), spinV: 1.5f);
                // Where it breaks, the cold takes the ground under the body: a few points of ice.
                Erupt(e.X, e.Z, 0.1f, 0.55f + share * 0.4f, 3 + (int)(share * 4), SpikeKind.Ice, 0.55f * g, 0.6f, IceDeep);
                break;
        }
        // The skill's own burst at the body, small: a moon breaks in violet. (A disc's gold
        // burst at every bounce through a crowd piled into one cream glow; its star is enough.)
        // (Motes and shards hit too often for a filmed burst each: a crowd of them read as
        // one white haze. Their marks above are enough.)
        // Shadow's wisps drink the light (drawn mostly as dark laid over the world, Flipbooks): pale
        // and added, they read as grey smoke.
        var (book, tint) = art switch
        {
            "moon" or "moon_brand" => ("moon_burst", new Color(0.16f, 0.12f, 0.75f, 0.32f)),
            "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark" => ("shadow_wisps", art == "siphon" ? new Color(0.42f, 0.1f, 0.5f, 0.95f) : new Color(0.3f, 0.12f, 0.62f, 0.95f)),
            _ => ((string?)null, Colors.White),
        };
        switch (art)
        {
            case "moon" or "moon_brand":
            {
                // The brand: the crescent stamped on what it struck, cold silver on a dark bed,
                // flaring and gone, and moonfire licking up off it in violet tongues. (Pale violet
                // over the tan dead, with smoke-soft flames and a stardust haze, it read as a lavender
                // puff.)
                var fire = MoonFire(art);
                Smoke.Spawn(at + Vector3.Up * 0.2f, Vector3.Zero, 0.45f, 0.7f * g, new Color(0.03f, 0.02f, 0.07f), null, 1.0f * g, alpha: 0.55f, sprite: -1);
                Sparks.Spawn(new Sparks.P
                {
                    At = at + Vector3.Up * 0.3f, V = Vector3.Up * 0.3f, Life = 0.42f, Size = 0.5f * g, SizeEnd = 0.8f * g, Color = MoonSilver * 1.3f, ColorEnd = new Color(fire.R * 0.25f, fire.G * 0.25f, fire.B * 0.4f),
                    Alpha = 1, Sprite = Sprites.Range("crescent").First + 1, Spin = (R() - 0.5f) * 0.6f + 0.001f, SpinV = 0.001f,
                });
                for (int i = 0; i < 7; i++)
                    MoonTongue(at + new Vector3((R() - 0.5f) * 0.5f, (R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.5f), Vector3.Up * (1.0f + R() * 1.2f) + away * R() * 0.5f, (0.34f + R() * 0.16f) * g, fire);
                break;
            }
            case "umbral" or "ruin" or "siphon":
                // The bolt tearing on through the rank: a violet rent along its line.
                Ribbons.Line(new[] { at - away * 0.7f, at, at + away * 1.0f }, (art == "ruin" ? 0.26f : 0.17f) * g, 0.16f, art == "siphon" ? Hdr("#b040ff", 1f) : Hdr("#7a3cff", 1f), 1.5f, Ribbons.Style.Wisp, new[] { 0f, 1f, 0f });
                break;
        }
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
            case "moon" or "moon_brand":
                // The moon drawn from her hand: a glint of its crescent, cold silver, gone in a breath.
                // (A turning sigil in moonlight's lilac, every cast, read as a lavender blot at her side.)
                Sparks.Spawn(new Sparks.P
                {
                    At = hand + Vector3.Up * 0.1f, Life = 0.2f, Size = 0.32f * g, SizeEnd = 0.5f * g, Color = MoonSilver * 1.2f, ColorEnd = MoonFire(art) * 0.3f,
                    Alpha = 1, Sprite = Sprites.Range("crescent").First + 1, Spin = (float)e.Angle + 0.001f, SpinV = 0.001f,
                });
                break;
            case "mote" or "mote_cascade" or "mote_star":
                // A spell spoken: a turning glyph of light at the hand, in the spell's
                // colour (white, it read as a blob at her feet).
                Sparks.Spawn(hand + Vector3.Up * 0.1f, Vector3.Zero, 0.24f, 0.6f * g, art == "mote_cascade" ? FenLight * 0.45f : Hdr("#c070ff", 1.3f), pal.Glow * 0.1f, 0.75f * g, sprite: Sprites.Of("magic"), spinV: 6);
                break;
            case "cinder" or "living_flame" or "star" or "frostfire":
                // A puff of flame at the hand, orange (white-tinted, it was a cream ball at her side).
                Books.Spawn("fire_blast", hand, 0.4f * g, 0.3f, new Color(1.25f, 0.62f, 0.26f, 0.85f), sizeEnd: 0.85f * g);
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
        if (art is "palm" or "palm_temple" or "palm_storm") { Palm(e); return; }
        float g = Grow(e.Rank);
        float gy = Y(e.X, e.Z);
        var at = V(e.X, gy + 1.0, e.Z);
        float reach = (float)e.Reach;
        float facing = (float)(Math.PI / 2 - e.Angle);
        var pal = Palette.Of(e.School);
        Color core = pal.Core, glow = pal.Glow;
        // The blade's own hue (kept below the tone curve's white-out, so it
        // stays a colour: the edge is the only white), how deep its smear
        // reaches in from the edge, and how fast it crosses its arc.
        Color hue = Hdr("#ff9a30", 1.05f);
        float depth = 0.3f, sweep = 0.085f, drain = 0.17f;
        // A full turn only for a blade that really goes all the way round (the Cleaver's wide chop is not one).
        bool heavy = false, spin = art == "slash_spin" || e.Arc > 5.5;
        switch (art)
        {
            case "slash_steel": core = SteelWhite; glow = OathGold * 0.55f; break;
            case "slash_holy": core = Hdr("#fff6d8", 3f); glow = OathGold; hue = Hdr("#ffc84a", 1.25f); depth = 0.34f; break;
            case "slash_blood": core = Hdr("#ffd0c8", 2.4f); glow = Blood; hue = Hdr("#ff2a1a", 1.15f); depth = 0.34f; break;
            case "slash_heavy": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d8a070", 1.5f); hue = Hdr("#ff5422", 1.05f); depth = 0.44f; sweep = 0.12f; drain = 0.2f; heavy = true; break;
            case "slash_quake": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d89060", 1.6f); hue = Hdr("#ff7026", 1.05f); depth = 0.46f; sweep = 0.12f; drain = 0.2f; heavy = true; break;
            case "slash_spin": core = Hdr("#fff0dc", 2.2f); glow = Hdr("#d8a070", 1.5f); hue = Hdr("#ff5422", 1.05f); depth = 0.36f; sweep = 0.17f; drain = 0.2f; heavy = true; break;
            case "palm" or "palm_temple": core = Hdr("#fff2d0", 2.6f); glow = Hdr("#ffb24a", 1.8f); hue = Hdr("#ffa040", 1.15f); depth = 0.26f; sweep = 0.06f; drain = 0.12f; break;
            case "palm_storm": core = Palette.Of(School.Storm).Core; glow = Palette.Of(School.Storm).Glow; hue = Hdr("#5a96ff", 1.2f); depth = 0.26f; sweep = 0.06f; drain = 0.12f; break;
        }
        mirror = !mirror;
        // The blade's path, cut fast: a hot edge at the reach and the smear of
        // its colour behind it (a painted fan read as a flat disc of beige, and
        // ribbons laid round it showed their joins), with a fainter echo inside
        // it a breath later, as a heavy blade leaves.
        float sweepSpan = spin ? Mathf.Tau * 1.02f : (float)e.Arc * 1.1f;
        float rich = Mathf.Min(g, 1.35f);
        Blades.Add(at, facing, reach, sweepSpan, mirror, sweep, drain, hue * (0.9f + 0.1f * g), depth * rich);
        Blades.Add(at + Vector3.Down * 0.1f, facing, reach * 0.78f, sweepSpan * 0.92f, mirror, sweep * 1.1f, drain * 0.8f, hue * 0.55f, depth * 0.55f * rich, 0.03f);
        if (spin) Blades.Add(at, facing + Mathf.Pi, reach * 0.9f, sweepSpan * 0.6f, mirror, sweep * 0.8f, drain, hue * 0.7f, depth * 0.7f * rich, 0.05f);
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

    /// <summary>Iron Palms: the force of an open hand, not a blade. An outline of a palm in chi
    /// (painted, palm_print) thrown out along the strike, fingers first, swelling as it goes; the
    /// air pushed out in front of it bending the picture; the dust it drives along the ground.
    /// (Drawn as a blade's crescent, a palm read as a sword.)</summary>
    void Palm(Ev.Slash e)
    {
        float g = Grow(e.Rank);
        bool storm = e.Art == "palm_storm";
        float reach = (float)e.Reach;
        var dir = new Vector3(Mathf.Cos((float)e.Angle), 0, Mathf.Sin((float)e.Angle));
        float gy = Y(e.X, e.Z);
        var from = V(e.X, gy + 1.0, e.Z);
        var at = from + dir * reach * 0.45f;
        var chi = storm ? Hdr("#8ab8ff", 1.9f) : Hdr("#ffa838", 1.9f);
        // Fingers along the strike as the eye sees it: the sprite's up turned onto the strike's
        // direction on the screen.
        float turn = 0;
        if (Cam != null)
        {
            var cb = Cam.Camera.GlobalBasis;
            turn = Mathf.Atan2(-dir.Dot(cb.X), dir.Dot(cb.Y));
        }
        float size = Mathf.Min(2.9f, reach * 0.88f) * Mathf.Sqrt(g);
        Sparks.Spawn(new Sparks.P
        {
            At = at, V = dir * reach * 1.6f, Drag = 5, Life = 0.2f, Size = size * 0.7f, SizeEnd = size * 1.08f,
            Color = chi, ColorEnd = new Color(chi.R * 0.2f, chi.G * 0.15f, chi.B * 0.1f), Alpha = 1,
            Sprite = Sprites.Range("palm_print").First + 1, Spin = Mathf.PosMod(turn, Mathf.Tau) + 0.001f, SpinV = 0.001f,
        });
        // The push of air in front of it.
        Waves.Add(at + dir * reach * 0.25f + Vector3.Down * 0.6f, reach * 0.5f, 0.2f, chi, 0.35f);
        // Chi shed off its edges, carried on with the blow.
        var side = new Vector3(-dir.Z, 0, dir.X);
        for (int i = 0; i < (int)(6 * g); i++)
        {
            float k = R() * 2 - 1;
            Sparks.Spawn(at + side * k * size * 0.45f, dir * (3 + R() * 4) + side * k * 1.5f + Vector3.Up * R(), 0.25f + R() * 0.15f, 0.05f, chi, chi * 0.3f, 0.01f, 0, 3,
                sprite: storm && R() < 0.4f ? Sprites.Of("spark") : 0);
        }
        if (storm) Ribbons.Bolt(at, at + dir * reach * 0.6f + side * (R() - 0.5f), 0.05f, 0.1f, chi * 0.6f, 2.2f, 1, 0.3f);
        // The ground under the strike driven out ahead of it.
        double tx = e.X + dir.X * reach * 0.7f, tz = e.Z + dir.Z * reach * 0.7f;
        for (int i = 0; i < 5; i++)
            Smoke.Spawn(V(tx, Y(tx, tz) + 0.15, tz), dir * (2.5f + R() * 2) + side * (R() - 0.5f) * 2 + Vector3.Up * 0.3f, 0.45f, 0.18f, new Color(0.3f, 0.25f, 0.2f), new Color(0.18f, 0.15f, 0.12f), 0.5f, drag: 3, alpha: 0.35f);
    }

    /// <summary>Blades' swings in progress (shaders/blade.gdshader).</summary>
    public readonly Blades Blades = new();

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
                steel.Add(new Transform3D(basis.Scaled(Vector3.One * 1.15f * Mathf.Sqrt(g)), at), art == "arrow_mark" ? new Color(1.2f, 0.75f, 0.55f) : new Color(1f, 0.97f, 0.92f));
                // A thin bright streak behind it, a glint at its head: an arrow is read by
                // its line (a wide pale one read as chalk).
                Ribbons.Feed(key, at, 0.11f * g, 0.13f, art == "arrow_mark" ? Hdr("#ff8a4a", 1f) : Hdr("#ffe8c0", 1f), 2.4f, Ribbons.Style.Steel);
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
                bool butcher = art == "axe_blood";
                float turn = (float)(now * 16 + p.Id), sz = (butcher ? 1.6f : 1.3f) * Mathf.Sqrt(g);
                var basis = new Godot.Basis(Vector3.Up, -turn) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * Godot.Basis.FromScale(Vector3.One * sz);
                axes.Add(new Transform3D(basis, at), Colors.White);
                // The head whirling: arcs of steel round it, so a spinning axe reads as one at a glance.
                Shade(at, 1.1f * sz, 0.35f);
                // (Steel even on the butcher's wheel: arcs in blood red made the four heads one red ring.)
                SpinArcs(at, 0.42f * sz, turn, 0.09f * sz, art == "axe_storm" ? Hdr("#bfe0ff", 1f) : Hdr("#ffe6c8", 1f), butcher ? 2.4f : 2f);
                // The orbit's wake: a curved streak behind each head, as the eye sees a spinning blade.
                // (Its wind thin and cool: pale and wide, four heads' wakes joined into one white hoop round her.)
                if (art == "axe_storm") Ribbons.Feed(key, at, 0.45f * g, 0.16f, Hdr("#7ab8c8", 1f), 0.6f, Ribbons.Style.Wisp);
                else Ribbons.Feed(key, at, 0.4f * g, butcher ? 0.12f : 0.16f, butcher ? Hdr("#a8140c", 1f) : Hdr("#fff0e0", 1f), butcher ? 1.2f : 1.3f, Ribbons.Style.Steel);
                // The butcher's cleavers fling blood off their edges as they turn.
                if (butcher && R() < 0.5f)
                {
                    var outward = new Vector3(at.X - (float)p.X, 0, at.Z - (float)p.Z);
                    Sparks.Spawn(at, (outward.LengthSquared() > 0.01f ? outward.Normalized() : Vector3.Right) * (2 + R() * 2) + Vector3.Up * (1 + R()), 0.5f, 0.06f + R() * 0.04f, Blood, BloodDim, 0.02f, 9);
                }
                return true;
            }
            case "disc" or "disc_aegis" or "disc_reckon":
            {
                float s = 1.1f * Mathf.Sqrt(g) * (art == "disc_reckon" ? 1.15f : 1);
                bool aegis = art == "disc_aegis";
                // The ring itself held below white, so it stays gold and its turning arcs show over it.
                var gold = aegis ? Hdr("#c8dcff", 0.8f) : Hdr("#ffa62e", 0.75f);
                var edge = aegis ? Hdr("#cfe0ff", 1f) : Hdr("#ffc04a", 1f);
                float spin = (float)(now * 16 + p.Id);
                // Its face: a sawblade of sunlight (painted, tools/comfy/fx_sprites.py), turning.
                // Held dim, so its grooves and teeth show rather than a filled sun.
                // Leaving her hand it is held down, so it never blooms over her.
                float off = Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(0.8f, 3f, new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length()));
                Body(at, 1.05f * s, aegis ? "ward_disc" : "sun_disc", gold * (0.6f * off), spin * 1.3f);
                // The sun it carries: a hot gold heart, kept small and coloured (a wide
                // white halo read as a cream doughnut), on a dark bed.
                Shade(at, 1.7f * s, 0.6f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.3f * s), at), (aegis ? Hdr("#f0f6ff", 1.8f) : Hdr("#fff0c0", 1.8f)) * off);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.95f * s), at), (aegis ? Hdr("#9ab8ff", 1.6f) : Hdr("#ffb030", 1.6f)) * (0.1f * off));
                // A blade spinning: arcs of light whipping round its rim, as the eye
                // sees a sawblade turn, and the sun's rays flung off its edge.
                SpinArcs(at, 0.6f * s, spin * 1.6f, 0.1f * s, aegis ? Hdr("#e8f2ff", 1f) : Hdr("#fff0c0", 1f), 3f * off);
                // Its wake: short, so a thrown disc never reads as a beam.
                Ribbons.Feed(key, at, 0.36f * s, 0.13f, edge, 1.5f, Ribbons.Style.Glow);
                if (R() < 0.5f)
                {
                    float a = R() * Mathf.Tau;
                    var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Sparks.Spawn(at + rim * 0.5f * s, new Vector3(-rim.Z, 0, rim.X) * 3.5f + rim * 1.5f + Vector3.Up * 0.5f, 0.22f, 0.06f, Hdr("#ffe8a0", 2f), Hdr("#ff9a20", 1.4f), 0.01f, 0, 3, sprite: R() < 0.3f ? Sprites.Of("star") : 0, spinV: 4);
                }
                return true;
            }
            case "chakram" or "chakram_razor" or "chakram_hail":
            {
                // A thrown blade: dark steel lying flat and spinning, its five hooked teeth honed
                // bright (ChakramMesh, shaders/chakram.gdshader), the wind it rides whipping round
                // its tips. (A pale ring, two in flight, read as a pair of handcuffs; a painted
                // blade facing the eye read as a pale bubble.)
                float s = 0.8f * Mathf.Sqrt(g);
                bool hail = art == "chakram_hail", razor = art == "chakram_razor";
                float spin = (float)(now * 19 + p.Id * 1.7f);
                // The honed edge in the wind's mint (near white, it read as a cut-out of paper).
                var edge = hail ? Hdr("#8ccfff", 1.35f) : razor ? Hdr("#ff9a88", 1.3f) : Hdr("#8ef0c8", 1.35f);
                var gust = hail ? Hdr("#6ab8ff", 1f) : Hdr("#8ce8c4", 1f);
                Shade(at, 1.5f * s, 0.35f);
                // Turned the way its teeth lead (the mesh's angle grows toward its points).
                chakrams.Add(new Transform3D(new Godot.Basis(Vector3.Up, -spin).Scaled(Vector3.One * 1.15f * s), at), edge);
                SpinArcs(at, 0.66f * s, spin, 0.07f * s, gust, 1.4f);
                if (razor && R() < 0.3f) Sparks.Spawn(at, Vector3.Up * 0.4f, 0.45f, 0.05f, Blood, BloodDim, 0.02f, 9);
                if (hail && R() < 0.4f)
                {
                    float a = R() * Mathf.Tau;
                    Sparks.Spawn(at + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * 0.45f * s, -fwd * 0.6f + Vector3.Up * 0.3f, 0.35f, 0.07f, Hdr("#dff4ff", 1.8f), Hdr("#5ab4ff", 1f), 0.02f, 2, 2, sprite: Sprites.Of("star"), spinV: 6);
                }
                // Gale Chakram rides the wind: a thin curl of air behind it (broad and pale, it read as
                // a lance through the blade).
                Ribbons.Feed(key, at - fwd * 0.3f * s, 0.26f * s, 0.14f, new Color(gust.R * 0.45f, gust.G * 0.45f, gust.B * 0.45f), razor ? 0.9f : 0.75f,
                    hail ? Ribbons.Style.Frost : razor ? Ribbons.Style.Steel : Ribbons.Style.Wisp);
                return true;
            }
            case "mote" or "mote_cascade" or "mote_star" or "ember_seeker":
            {
                // A will-o'-the-wisp: a hot point that weaves round its line of flight as it
                // hunts, a short tapering tail, and a dust of sparks it leaves hanging. (A long
                // tail on a straight flight read as a beam.)
                var c = art == "mote_cascade" ? FenLight : art == "mote_star" ? Hdr("#fff0ff", 2.6f) : Hdr("#f4d8ff", 2.2f);
                var gw = art == "mote_cascade" ? Hdr("#3affc0", 1.5f) : Hdr("#b04aff", 1.6f);
                float s = 0.3f * g * (art == "mote_star" ? 1.3f : 1);
                var side = new Vector3(fwd.Z, 0, -fwd.X);
                float ph = (float)now * 15 + p.Id * 2.1f;
                var wob = side * Mathf.Sin(ph) * 0.26f + Vector3.Up * Mathf.Cos(ph) * 0.14f;
                var head = at + wob;
                Shade(head, s * 2.2f, 0.55f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.42f), head), c * 0.8f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.9f), head), gw * 0.16f);
                Ribbons.Feed(key, head, 0.15f * g, 0.11f, new Color(gw.R / 2f, gw.G / 2f, gw.B / 2f), 2.2f, Ribbons.Style.Glow);
                // Its heart a four-pointed star that twinkles as it hunts.
                Sparks.Spawn(head, Vector3.Zero, 0.05f, s * (1.3f + 0.45f * Mathf.Sin((float)now * 40 + p.Id)), c * 0.5f, null, s * 1.1f, sprite: Sprites.Range("star").First + 2 + 1, spinV: 0);
                // The dust it leaves: points of light that hang a moment and wink out.
                trailAcc.TryGetValue(p.Id, out var dust);
                dust += dt * 26;
                while (dust >= 1)
                {
                    dust -= 1;
                    bool star = art == "mote_star" || R() < 0.25f;
                    Sparks.Spawn(head + new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f) * 0.12f, new Vector3(R() - 0.5f, R() * 0.6f, R() - 0.5f) * 0.5f,
                        0.3f + R() * 0.25f, (star ? 0.11f : 0.05f) * g, c * 0.7f, gw * 0.5f, 0.01f, 0, 2.4f, sprite: star ? Sprites.Of("star") : 0, spinV: 5);
                }
                trailAcc[p.Id] = dust;
                return true;
            }
            case "moon" or "moon_brand" or "moonfall":
            {
                // Moonlit flame: a silver crescent wreathed in violet-blue fire streaming off it as
                // it hunts, on a dark bed. (A white orb at its heart read as a pale pill, and a
                // lilac haze round it as grey smoke over the pale dead.)
                float s = 0.75f * g;
                var fire = MoonFire(art);
                Shade(at, s * 2.6f, 0.72f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), fire * 0.16f);
                Body(at, s * 1.45f, "crescent", MoonSilver, (float)now * 2 + p.Id);
                // Its trail a thin streak of flame (half a metre wide, it lay on the ground as a lilac smear).
                Ribbons.Feed(key, at, 0.24f * g, 0.2f, new Color(fire.R * 0.6f, fire.G * 0.6f, fire.B * 0.6f), 2f, Ribbons.Style.Flame);
                trailAcc.TryGetValue(p.Id, out var lick);
                lick += dt * 34;
                while (lick >= 1)
                {
                    lick -= 1;
                    MoonTongue(at + new Vector3((R() - 0.5f) * 0.3f, (R() - 0.3f) * 0.2f, (R() - 0.5f) * 0.3f) * s, -fwd * (0.4f + R() * 0.8f) + Vector3.Up * (0.5f + R() * 0.6f), 0.24f * s + R() * 0.1f * s, fire);
                }
                trailAcc[p.Id] = lick;
                return true;
            }
            case "cinder" or "living_flame" or "star" or "frostfire":
            {
                // A burning coal: flame streaming off it, embers shed behind, a little smoke.
                // Frostfire Comet: a heart of ice in the fire, a tail of frost beside the flame, and
                // frost glinting off it with the embers. (Drawn as Fallen Star's, it had no cold in it
                // at all: a cream streak.)
                bool ice = art == "frostfire", star = art == "star" || ice, small = art == "living_flame";
                float s = (star ? 1.25f : small ? 0.55f : 0.85f) * g;
                // Its heart yellow-hot, not white: past the tone curve's knee a coal read as a cream pill.
                Shade(at, s * 2.2f, 0.5f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.3f), at), ice ? Hdr("#9fd4ff", 1.6f) : star ? Hdr("#ffd890", 2.0f) : Hdr("#ffa840", 1.7f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), Hdr("#ff5a10", 1.6f) * (ice ? 0.14f : 0.2f));
                Body(at, s * 0.75f, "ember_coal", star ? Hdr("#ffb060", 1.6f) : Hdr("#ff7a28", 1.5f), (float)now * 5 + p.Id);
                if (ice) Body(at + Vector3.Up * 0.05f, s * 0.6f, "frost_star", Hdr("#8ac8ff", 1.5f), -(float)now * 4 + p.Id);
                // Its flame streaming back, short and deep orange (long and bright, the coal read as
                // a pale beam behind it).
                Ribbons.Feed(key, at, 0.5f * s, star ? 0.3f : 0.18f, Hdr("#ff6a1a", 1f), 1.5f, Ribbons.Style.Flame);
                // (No frost ribbon beside the flame: its trail drew pale squares along the comet's
                // path even with round glints. Its frost is the glints it sheds and its heart.)
                trailAcc.TryGetValue(p.Id, out var acc);
                acc += dt * (star ? 50 : 30);
                while (acc >= 1)
                {
                    acc -= 1;
                    // (Its filmed flame tinted orange: white-tinted, the coal read as a cream pill.)
                    if (R() < 0.35f) Books.Spawn("fire_loop", at + new Vector3((R() - 0.5f) * 0.1f, 0, (R() - 0.5f) * 0.1f), 0.5f * s, 0.22f, new Color(1.35f, 0.78f, 0.36f, 0.85f), sizeEnd: 0.15f * s, v: Vector3.Up * 0.8f);
                    if (ice && R() < 0.5f)
                        Sparks.Spawn(at, -fwd * (0.4f + R() * 0.8f) + new Vector3((R() - 0.5f) * 1.0f, 0.3f + R() * 0.6f, (R() - 0.5f) * 1.0f), 0.45f + R() * 0.3f, 0.09f + R() * 0.06f, Hdr("#a8dcff", 1.5f), IceDeep * 0.5f, 0.02f, 0.5f, 1.5f, sprite: Sprites.Of("frost_star"), spinV: 4);
                    else Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 1.2f, 0.6f + R(), (R() - 0.5f) * 1.2f), 0.4f + R() * 0.3f, 0.04f + R() * 0.03f, Ember, EmberDeep, 0.01f, -1.2f, 1.5f);
                    if (R() < 0.15f) Smoke.Spawn(at + Vector3.Up * 0.2f, Vector3.Up * 0.6f, 0.9f, 0.25f * s, new Color(0.3f, 0.27f, 0.25f), new Color(0.15f, 0.14f, 0.13f), 0.7f * s, drag: 1, alpha: 0.35f);
                }
                trailAcc[p.Id] = acc;
                return true;
            }
            case "shard" or "shard_deep" or "spear_ice":
            {
                float s = (art == "spear_ice" ? 2.4f : art == "shard_deep" ? 1.2f : 1) * Mathf.Sqrt(g);
                var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2);
                // A cut lance of ice, deep blue with white edges, point first; a short
                // trail of frost glinting behind it (long, it read as a white bar).
                Shade(at, 1.3f * s, 0.55f);
                shards.Add(new Transform3D(basis.Scaled(Vector3.One * 0.85f * s), at), IceDeep with { A = 1 });
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.8f * s), at), Hdr("#4ab0ff", 1.4f) * 0.1f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.16f * s), at + fwd * 0.38f * s), Hdr("#e8f8ff", 2f));
                Ribbons.Feed(key, at - fwd * 0.3f * s, (art == "spear_ice" ? 0.6f : 0.26f) * s, art == "spear_ice" ? 0.3f : 0.15f, Hdr("#5ab8ff", 1f), 2f, Ribbons.Style.Frost);
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
                // Its heart is the dark of the bed under it (a pale core read as a grey puff); only
                // the lantern's soul burns at its middle.
                Shade(at, s * 2.4f, 0.85f);
                if (lantern) orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.5f), at), Hdr("#e8fff4", 3f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.8f), at), rim * 0.16f);
                if (!lantern) Body(at, s * 1.6f, "umbral", art == "siphon" ? Hdr("#c050ff", 1.2f) : Hdr("#9a50ff", 1.2f), (float)now * 3 + p.Id);
                Ribbons.Feed(key, at, 0.5f * s, ruin ? 0.28f : 0.18f, new Color(rim.R / 3, rim.G / 3, rim.B / 3), 1.6f, Ribbons.Style.Wisp);
                // The tether: a coil of the dark wound back to the hand that cast it, twisting as it
                // pays out, and what it takes running back up it to her in her blood's rose. (A
                // single faint wisp of a thread was not seen at all in a crowd.)
                if (art.StartsWith("tether") && b0 != null)
                {
                    var hand = PlayerPos + Vector3.Up * 1.15f;
                    var span = at - hand;
                    float len = Mathf.Max(0.3f, span.Length());
                    var along = span / len;
                    var side = Mathf.Abs(along.Y) < 0.95f ? along.Cross(Vector3.Up).Normalized() : Vector3.Right;
                    var lift = side.Cross(along);
                    const int N = 28;
                    var coil = new Vector3[N + 1];
                    var core = new Vector3[N + 1];
                    var w = new float[N + 1];
                    float turns = Mathf.Max(2, len / 1.2f), tf = (float)now * 9 + p.Id;
                    for (int j = 0; j <= N; j++)
                    {
                        float u = j / (float)N, bell = Mathf.Sin(u * Mathf.Pi);
                        var spine = hand + span * u + Vector3.Up * bell * 0.4f;
                        float ang = u * turns * Mathf.Tau - tf, rad = 0.06f + 0.24f * bell;
                        core[j] = spine;
                        coil[j] = spine + (side * Mathf.Cos(ang) + lift * Mathf.Sin(ang)) * rad;
                        w[j] = 0.35f + 0.65f * bell;
                    }
                    Ribbons.Now(core, 0.05f, Hdr("#3a1460", 1f), 1f, Ribbons.Style.Wisp, w);
                    Ribbons.Now(coil, 0.04f, Hdr("#b47cff", 1.25f), 1.7f, Ribbons.Style.Glow, w);
                    if (R() < 0.6f)
                    {
                        float k = (float)((now * 1.4 + p.Id * 0.37) % 1.0);
                        var back = at - span * k + Vector3.Up * Mathf.Sin(k * Mathf.Pi) * 0.4f;
                        Sparks.Spawn(back, -along * 0.5f, 0.28f, 0.15f, Hdr("#ff6a9a", 1.3f), Hdr("#a0204a", 0.8f), 0.05f, 0, 1);
                    }
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
            case "herd" or "herd_great" or "herd_hunt":
            {
                // Spirit beasts running the crowd down: the wolf (Beasts, the crowd's own) lit
                // green from within, its edges flaking as a spirit's would, a wisp of the wild
                // streaming behind and motes kicked off its feet. (A pale orb with a dotted
                // tail read as a comet, not a herd.)
                herdCrowd ??= SpiritHerd();
                bool hunt = art == "herd_hunt";
                var feet = V(p.X, Y(p.X, p.Z), p.Z);
                float sc = 1.2f * Mathf.Sqrt(g) * (art == "herd_great" ? 1.12f : 1);
                double speed = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
                double rate = herdCrowd.Asset.Pace > 0 ? Math.Clamp(speed / (herdCrowd.Asset.Pace * sc), 0.8, 2.4) : 1.6;
                var basis = new Godot.Basis(Vector3.Up, Mathf.Pi / 2 - Mathf.Atan2((float)p.Vz, (float)p.Vx)) * Godot.Basis.FromScale(Vector3.One * sc);
                // Whole, lit from within (flaking, its edges burned orange and it read as a dark
                // shape in a green streak).
                var tint = hunt ? new Color(0.7f, 1.6f, 0.4f) : new Color(0.45f, 1.5f, 1.0f);
                herdCrowd.Push(new Transform3D(basis, feet), "move", now * rate + p.Id * 0.37, 0, 0, 0, 0, tint, 2.2f);
                // A spirit leaves itself behind as it runs: two fading echoes a stride back, coming
                // apart in flakes (a green wolf alone read as a dyed one, not a spirit).
                for (int k = 1; k <= 2; k++)
                    herdCrowd.Push(new Transform3D(basis, feet - fwd * 0.55f * k * sc), "move", (now - 0.07 * k) * rate + p.Id * 0.37, 0, 0.35f + 0.25f * k, 0, 0, tint * (1.1f - 0.2f * k), 2.6f);
                var wild = hunt ? Hdr("#7aff3a", 1f) : Hdr("#4affa0", 1f);
                Ribbons.Feed(key, feet + Vector3.Up * 0.5f * sc, 0.3f * sc, 0.14f, new Color(wild.R * 0.4f, wild.G * 0.4f, wild.B * 0.4f), 0.9f, Ribbons.Style.Wisp);
                trailAcc.TryGetValue(p.Id, out var kick);
                kick += dt * 22;
                while (kick >= 1)
                {
                    kick -= 1;
                    var off = new Vector3((R() - 0.5f) * 0.6f, 0.1f + R() * 0.5f, (R() - 0.5f) * 0.6f) * sc;
                    if (hunt && R() < 0.5f) MoonTongue(feet + off + Vector3.Up * 0.3f, -fwd * R() + Vector3.Up * (0.8f + R()), 0.35f * sc, Hdr("#6aff2a", 1.3f));
                    else Sparks.Spawn(feet + off, -fwd * (0.5f + R()) + Vector3.Up * (0.6f + R()), 0.5f + R() * 0.3f, 0.05f + R() * 0.04f, wild * 1.4f, wild * 0.3f, 0.01f, -0.4f, 1.5f,
                        sprite: R() < 0.3f ? Sprites.Of("star") : 0, spinV: 3);
                }
                trailAcc[p.Id] = kick;
                return true;
            }
            case "firepot":
                return false;
        }
        return false;
    }

    /// <summary>The spirit beasts of Spirit Herd: the crowd's wolf, drawn as a crowd of its own.</summary>
    VatCrowd? herdCrowd;

    VatCrowd SpiritHerd()
    {
        var c = new VatCrowd(Vat.Of(Visuals.Of("wolf_spirit"), this)) { CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(c);
        return c;
    }

    /// <summary>A spinning disc's arc of light along its rim: from nothing at its tail to its brightest just short of its tip.</summary>
    static readonly float[] DiscArc = { 0f, 0.35f, 0.65f, 0.9f, 1f, 0f };

    /// <summary>Two arcs of light whipping round a spinning blade's rim (a disc,
    /// a chakram, an axe's head), half a turn apart, at `phase` radians.</summary>
    void SpinArcs(Vector3 at, float radius, float phase, float width, Color color, float energy)
    {
        for (int k = 0; k < 2; k++)
        {
            var arc = new Vector3[6];
            for (int j = 0; j < 6; j++)
            {
                float a = phase + k * Mathf.Pi + j * 0.32f;
                arc[j] = at + new Vector3(Mathf.Cos(a), 0.02f, Mathf.Sin(a)) * radius;
            }
            Ribbons.Now(arc, width, color, energy, Ribbons.Style.Steel, DiscArc);
        }
    }

    /// <summary>A painted body for this frame (a sprite of tools/comfy/fx_sprites.py),
    /// `size` across, turned to `turn` radians. It lives one frame: living two, a body in
    /// flight was drawn twice a step apart, a pale double of itself. While the fight is held
    /// (no time passing) the last frame's body stands, and none is added over it.</summary>
    void Body(Vector3 at, float size, string sprite, Color color, float turn)
    {
        if (frameDt <= 0) return;
        Sparks.Spawn(new Sparks.P
        {
            At = at, Life = frameDt * 1.5f, Size = size, SizeEnd = size, Color = color, ColorEnd = color, Alpha = 1,
            Sprite = Sprites.Range(sprite).First + 1, Spin = Mathf.PosMod(turn, Mathf.Tau) + 0.001f, SpinV = 0.001f,
        });
    }

    /// <summary>This frame's step of the fight's clock (0 while it is held).</summary>
    float frameDt = 1f / 60;

    /// <summary>Gale Chakram's blade, flat in the ground's plane round the origin, a metre
    /// across its tips: a ring with five hooked teeth all leading the way it turns (its angle
    /// growing toward each point), thin and two-sided. UV.x runs from its hole (0) to its
    /// edge (1), whatever the edge's shape, for shaders/chakram.gdshader's honed edge.</summary>
    static ArrayMesh ChakramMesh()
    {
        const int N = 240;
        const float Hole = 0.24f, Rim = 0.36f, Tip = 0.52f, Thick = 0.012f;
        static float Edge(float a)
        {
            float f = Mathf.PosMod(a / Mathf.Tau * 5, 1);
            // A tooth's back swelling out to its point, then the hooked cut back in to the rim.
            return f < 0.82f ? Rim + (Tip - Rim) * Mathf.Pow(f / 0.82f, 1.7f) : Tip - (Tip - Rim) * Mathf.SmoothStep(0, 1, (f - 0.82f) / 0.18f);
        }
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        for (int side = 0; side < 2; side++)
        {
            var n = side == 0 ? Vector3.Up : Vector3.Down;
            var lift = n * Thick;
            for (int i = 0; i < N; i++)
            {
                float a0 = i / (float)N * Mathf.Tau, a1 = (i + 1) / (float)N * Mathf.Tau;
                var d0 = new Vector3(Mathf.Cos(a0), 0, Mathf.Sin(a0));
                var d1 = new Vector3(Mathf.Cos(a1), 0, Mathf.Sin(a1));
                Vector3 in0 = d0 * Hole + lift, in1 = d1 * Hole + lift, out0 = d0 * Edge(a0) + lift, out1 = d1 * Edge(a1) + lift;
                void P(Vector3 p, float u) { st.SetNormal(n); st.SetUV(new Vector2(u, 0)); st.AddVertex(p); }
                P(in0, 0); P(out0, 1); P(out1, 1);
                P(in0, 0); P(out1, 1); P(in1, 0);
            }
        }
        return st.Commit();
    }

    /// <summary>Moonbrand's fire: violet-blue, its brand's a deeper violet. Held below the tone
    /// curve's knee so it stays a colour over the pale dead.</summary>
    static Color MoonFire(string art) => art == "moon_brand" ? Hdr("#7a3cff", 1.5f) : Hdr("#5a50ff", 1.5f);

    /// <summary>Moonlight: cold silver-blue. (Silver-lilac read as lavender.)</summary>
    static readonly Color MoonSilver = Hdr("#d2deff", 1.2f);

    /// <summary>A tongue of moonfire: an upright flame (the pack's), rising and gone.</summary>
    void MoonTongue(Vector3 at, Vector3 v, float size, Color fire) =>
        Sparks.Spawn(new Sparks.P
        {
            At = at, V = v, Life = 0.28f + R() * 0.14f, Size = size, SizeEnd = size * 0.35f, Color = fire * 0.85f, ColorEnd = new Color(fire.R * 0.25f, fire.G * 0.2f, fire.B * 0.45f),
            Alpha = 1, Drag = 2.5f, Sprite = Sprites.Range("muzzle").First + 1 + (int)(R() * 4.99f), Spin = (R() - 0.5f) * 0.5f + 0.001f, SpinV = 0.001f,
        });

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
                // No filmed burst: the front, the ice and the cold it rolls out are the blow
                // (the burst, however faint, washed the whole crowd blue-white).
                Waves.Add(ground + Vector3.Up * 0.3f, r * 1.2f, 0.4f, f.Glow, 0.8f);
                // Ice flung low over the ground, and the cold rolling out after it.
                int n = Math.Min(40, (int)(14 * g + r * 3));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, v = r * (1.6f + R() * 1.4f);
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Sparks.Spawn(ground + Vector3.Up * 0.4f + dir * 0.4f, dir * v + Vector3.Up * (0.5f + R() * 1.5f), 0.4f + R() * 0.25f, 0.07f + R() * 0.07f, f.Core, f.Glow * 0.4f, 0.02f, 8, 2.5f, sprite: Sprites.Of("star"), spinV: 9);
                }
                // The cold rolling out low behind the front: thin, so it never hides the crowd.
                for (int i = 0; i < 7; i++)
                {
                    float a = i / 7f * Mathf.Tau + R() * 0.5f;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Smoke.Spawn(ground + Vector3.Up * 0.2f + dir * r * 0.35f, dir * r * 1.3f + Vector3.Up * 0.1f, 0.7f, r * 0.16f, new Color(0.62f, 0.8f, 1f), new Color(0.45f, 0.62f, 0.9f), r * 0.4f, drag: 2.4f, alpha: 0.12f);
                }
                // The front leaves ice standing in it: a ring of crystal points, leaning out, gone in a second.
                Erupt(e.X, e.Z, r * 0.35f, r * 0.95f, 14 + rings * 5, SpikeKind.Ice, 1.0f * g, 0.95f, IceDeep);
                // Rime left on the ground, briefly (held for seconds it was a carpet of white).
                Scars.Add("frost", ground, r * 0.7f, 1.2f, 0);
                Flash(ground + Vector3.Up * 1.2f, f.Light, 6, 0.35f, r * 2.5f);
                return true;
            }
            case "nova_holy" or "nova_dawn" or "nova_sun":
            {
                var h = Palette.Of(School.Holy);
                // Deep gold and thin: wide and bright, its front bloomed to a thick cream ring that
                // was the strongest mark near her while it lasted.
                var gold = Hdr("#ffb84a", 1f);
                AddFront(ground, r, 0.4f, 0.24f * g, gold, 1.7f, Ribbons.Style.Glow, 0.1f);
                for (int k = 1; k < rings; k++) AddFront(ground, r * (1 - 0.18f * k), 0.4f + 0.08f * k, 0.14f, gold, 1.1f, Ribbons.Style.Glow, 0.1f);
                // Dawn's ring itself, filmed (LTX): a thin line of white-gold racing out, the middle left dark.
                Books.Spawn("holy_ring", ground + Vector3.Up * 0.5f, r * 0.7f, 0.45f, new Color(0.6f, 0.38f, 0.12f, 0.5f), flat: true, sizeEnd: r * 2.3f);
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
                // The sigil it leaves, small at her feet (seventy percent of its reach, it was a lit
                // disc of rings over the whole crowd).
                Scars.Add("sigil", ground, Mathf.Min(1.6f, r * 0.35f), art == "nova_sun" ? 3 : 1.2f, 0.6f);
                Flash(ground + Vector3.Up * 1.5f, h.Light, 7, 0.4f, r * 2.5f);
                Books.Spawn("gold_flare", ground + Vector3.Up * 1.4f, r * 0.35f, 0.35f, new Color(1f, 0.85f, 0.55f, 0.8f), sizeEnd: r * 0.9f);
                return true;
            }
            case "nova_blood" or "nova_rend" or "nova_harrow":
            {
                // The arc is swept round at the edge of its reach, twice, crimson in shadow.
                var at = ground + Vector3.Up * 1.0f;
                var glow = art == "nova_harrow" ? Hdr("#9a5cff", 2.4f) : Hdr("#c4142a", 2.4f);
                float facing = R() * Mathf.Tau;
                // A scythe swept all the way round at the edge of its reach: the blade's
                // crescent (Blades), crimson, with a darker one inside it a breath behind.
                var hue = art == "nova_harrow" ? Hdr("#8a4aff", 1.1f) : Hdr("#e01a2a", 1.1f);
                // Swept most of the way round, never closed: a full turn of its hot edge read as a hoop.
                Blades.Add(at, facing, r, Mathf.Tau * 0.82f, false, 0.16f, 0.24f, hue, 0.3f * Mathf.Min(g, 1.3f));
                Blades.Add(at + Vector3.Down * 0.1f, facing + Mathf.Pi, r * 0.8f, Mathf.Tau * 0.62f, false, 0.18f, 0.2f, hue * 0.55f, 0.3f, 0.04f);
                if (rings > 1) Blades.Add(at, facing + Mathf.Pi / 2, r * 0.6f, Mathf.Tau * 0.7f, true, 0.16f, 0.2f, hue * 0.7f, 0.35f, 0.08f);
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
            // The survivor's own marks are quiet: where it will fall, a faint light gathering on the
            // ground as it comes, never a ring (six thin rings round her at once read as the
            // interface's circles, and as a threat).
            var pal = Palette.Of(e.School);
            if (art != "slash_quake")
                Sparks.Spawn(V(e.X, Y(e.X, e.Z) + 0.15, e.Z), Vector3.Zero, (float)e.Delay, r * 0.25f, pal.Glow * 0.12f, pal.Glow * 0.4f, r * 0.9f, alpha: 0.8f);
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
                // Electric blue with a hot thread, never white: at four times a pale blue every bolt
                // and its burst came out white, a blown-out ball where each one landed.
                var col = Hdr("#7aa6ff", 1f);
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 0.45f : small ? 0.18f : 0.3f) * g, clap ? 0.3f : 0.22f, col, 2.6f, small ? 1 : 3, 0.18f);
                // Its glow round the thread, so the strike reads as a blow of light, not a hairline.
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 1.2f : small ? 0.5f : 0.85f) * g, 0.14f, Hdr("#2a50ff", 1f), 1.1f, 0, 0.16f);
                // The fork it throws along the ground where it lands.
                for (int i = 0; i < (clap ? 5 : 3); i++)
                {
                    float a = R() * Mathf.Tau, d = r * (0.9f + R() * 0.8f);
                    double x = e.X + Mathf.Cos(a) * d, z = e.Z + Mathf.Sin(a) * d;
                    Ribbons.Bolt(ground + Vector3.Up * 0.25f, V(x, Y(x, z) + 0.2, z), 0.12f * g, 0.16f, col, 2.6f, 0, 0.3f);
                }
                // The filmed burst only for the clap: under every bolt it filled the ground pale blue.
                Blast(e.X, e.Z, School.Storm, Mathf.Max(1.1f, r) * (clap ? 1.3f : 0.8f), 0.45f, light: !clap);
                Scars.Add("scorch", ground, Mathf.Max(0.6f, r * 0.45f), 3f, 0);
                if (clap) { Waves.Add(ground + Vector3.Up * 0.3f, r * 2.2f, 0.4f, pal.Glow, 1.2f); Cam?.AddTrauma(0.12f); }
                Flash(ground + Vector3.Up * 3, pal.Light, small ? 6 : 12 * g, 0.22f, small ? 8 : 14);
                return;
            }
            case "moonfall":
            {
                // A moon falling: a pale streak down out of the dark, and the burst where it breaks.
                var top = ground + new Vector3(-2.5f, 14, 1.5f);
                // Moonlight cold silver-blue, its breaking a deep violet: pale lilac streaks, stardust
                // and rings read pink-white, a field of lavender hoops.
                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.3f * g, 0.22f, Hdr("#a8bcff", 1f), 2.0f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                // The moon breaks into stardust (filmed, LTX), its light thrown out.
                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.7f, 0.65f, new Color(0.26f, 0.22f, 0.95f, 0.6f), flat: true, sizeEnd: r * 2.0f);
                Flash(ground + Vector3.Up * 1.5f, new Color(0.55f, 0.6f, 1f), 6, 0.3f, r * 3);
                Scars.Add("runes", ground, r * 0.6f, 1.2f, -0.7f);
                AddFront(ground, r * 1.2f, 0.3f, 0.16f * g, Hdr("#6a5aff", 1f), 1.2f, Ribbons.Style.Wisp, 0.2f);
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
        if (sun)
        {
            Ribbons.Line(mid, w * 1.6f, life, col, 1.2f, Ribbons.Style.Glow, even);
            Ribbons.Line(mid, w * 0.45f, life * 0.9f, Hdr("#fff4d8", 1f), 3f, Ribbons.Style.Bolt, even);
        }
        else
        {
            // A lance of the green: a thin bright heart, a deep green haze, and two
            // living vines twisting round it (a wide lime bar read as a laser).
            Ribbons.Line(mid, w * 1.1f, life, Hdr("#1fae4a", 1f), 1.1f, Ribbons.Style.Wisp, even);
            Ribbons.Line(mid, w * 0.3f, life * 0.9f, Hdr("#c8ffb0", 1f), 3f, Ribbons.Style.Bolt, even);
            var axis = (b - a).Normalized();
            var side = axis.Cross(Vector3.Up).Normalized();
            for (int v = 0; v < 2; v++)
            {
                var vine = new Vector3[17];
                var vw = new float[17];
                for (int i = 0; i < 17; i++)
                {
                    float u = i / 16f, turn = u * 7f * Mathf.Pi + v * Mathf.Pi;
                    vine[i] = a.Lerp(b, u) + (side * Mathf.Cos(turn) + Vector3.Up * Mathf.Sin(turn)) * w * 0.55f;
                    vw[i] = i == 0 || i == 16 ? 0 : 1;
                }
                Ribbons.Line(vine, w * 0.22f, life, Hdr("#5aff7a", 1f), 2.2f, Ribbons.Style.Steel, vw);
            }
            for (int i = 0; i < 10; i++)
                Smoke.Spawn(a.Lerp(b, R()), new Vector3((R() - 0.5f) * 2, 0.5f + R(), (R() - 0.5f) * 2), 0.8f + R() * 0.5f, 0.09f, new Color("#3f8a2a"), new Color("#26501a"), 0.07f, gravity: 2, sprite: Sprites.Of("dirt"), spinV: 5);
        }
        if (sun) Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.9f * g, pal.Core * 0.7f, pal.Glow * 0.2f, 0.4f, sprite: Sprites.Of("flare"));
        else Books.Spawn("leaf_burst", a, 1.6f * g, 0.45f, new Color(0.8f, 1.2f, 0.8f, 0.85f), sizeEnd: 0.6f * g);
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

    /// <summary>The cut-crystal look (shaders/crystal.gdshader): ice at facet 1, stone and thorn near 0.</summary>
    static Material Crystal(float emit, float rim, float gloss, float facet)
    {
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/crystal.gdshader") };
        m.SetShaderParameter("emit", emit);
        m.SetShaderParameter("rim", rim);
        m.SetShaderParameter("gloss", gloss);
        m.SetShaderParameter("facet", facet);
        return m;
    }

    /// <summary>An arrow, point down +Z, 0.95 m long about its origin: a dark
    /// shaft, a bright steel head, pale fletching (crossed, both faces), in
    /// vertex colour that the instance's colour tints (a bare stick of steel
    /// read as a stick).</summary>
    static ArrayMesh Arrow()
    {
        var v = new System.Collections.Generic.List<Vector3>();
        var c = new System.Collections.Generic.List<Color>();
        void Tri(Vector3 a, Vector3 b, Vector3 d, Color col) { v.Add(a); v.Add(b); v.Add(d); c.Add(col); c.Add(col); c.Add(col); }
        void Quad(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color col) { Tri(a, b, d, col); Tri(a, d, e, col); }
        var wood = new Color(0.42f, 0.3f, 0.2f);
        var steel = new Color(1.6f, 1.55f, 1.45f);
        var feather = new Color(1f, 0.96f, 0.9f);
        const float W = 0.022f, Z0 = -0.48f, Z1 = 0.3f;
        // The shaft: four sides of a thin box, and the head a four-sided point,
        // each face both ways round (no winding to get wrong at this size).
        var s = new[] { new Vector3(-W, -W, 0), new Vector3(W, -W, 0), new Vector3(W, W, 0), new Vector3(-W, W, 0) };
        for (int i = 0; i < 4; i++)
        {
            var a = s[i]; var b = s[(i + 1) % 4];
            Quad(a with { Z = Z0 }, b with { Z = Z0 }, b with { Z = Z1 }, a with { Z = Z1 }, wood);
            Quad(a with { Z = Z1 }, b with { Z = Z1 }, b with { Z = Z0 }, a with { Z = Z0 }, wood);
        }
        const float H = 0.06f, Tip = 0.47f;
        var hb = new[] { new Vector3(0, -H * 0.5f, Z1), new Vector3(H, 0, Z1), new Vector3(0, H * 0.5f, Z1), new Vector3(-H, 0, Z1) };
        var tip = new Vector3(0, 0, Tip);
        for (int i = 0; i < 4; i++) { Tri(hb[i], hb[(i + 1) % 4], tip, steel); Tri(tip, hb[(i + 1) % 4], hb[i], steel); }
        // Fletching: two crossed vanes at the tail, drawn both ways round.
        const float F = 0.07f, F0 = -0.47f, F1 = -0.3f;
        foreach (var side in new[] { Vector3.Up, Vector3.Right })
        {
            var p = new[] { new Vector3(0, 0, F0) - side * F, new Vector3(0, 0, F1) - side * 0.02f, new Vector3(0, 0, F1) + side * 0.02f, new Vector3(0, 0, F0) + side * F };
            Quad(p[0], p[1], p[2], p[3], feather);
            Quad(p[3], p[2], p[1], p[0], feather);
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = v.ToArray();
        arrays[(int)Mesh.ArrayType.Color] = c.ToArray();
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        var st = new SurfaceTool();
        st.CreateFrom(m, 0);
        st.GenerateNormals();
        return st.Commit();
    }

    /// <summary>A lance of ice in flight: a six-sided crystal, a long point ahead
    /// and a short one behind, one unit long down +Y about its origin (a wedge
    /// read as a white bar).</summary>
    static ArrayMesh IceLance()
    {
        const int Sides = 6;
        var verts = new System.Collections.Generic.List<Vector3>();
        var idx = new System.Collections.Generic.List<int>();
        var front = new Vector3(0, 0.5f, 0);
        var back = new Vector3(0, -0.5f, 0);
        // The widest ring a third of the way back from the front point.
        for (int i = 0; i < Sides; i++)
        {
            float a0 = i / (float)Sides * Mathf.Tau, a1 = (i + 1) / (float)Sides * Mathf.Tau;
            float w0 = i % 2 == 0 ? 0.14f : 0.11f, w1 = (i + 1) % 2 == 0 ? 0.14f : 0.11f;
            var p0 = new Vector3(Mathf.Cos(a0) * w0, -0.18f, Mathf.Sin(a0) * w0);
            var p1 = new Vector3(Mathf.Cos(a1) * w1, -0.18f, Mathf.Sin(a1) * w1);
            int b = verts.Count;
            // Clockwise seen from outside (Godot's front faces).
            verts.Add(front); verts.Add(p0); verts.Add(p1);
            verts.Add(back); verts.Add(p1); verts.Add(p0);
            idx.AddRange(new[] { b, b + 1, b + 2, b + 3, b + 4, b + 5 });
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return m;
    }

    void EnsureSpikes()
    {
        if (iceSpikes != null) return;
        // A five-sided point (ice), a four-sided hook of a thorn, a blunt shard of stone; each one unit tall about its origin.
        Mesh Point(int sides, float top) => new CylinderMesh { TopRadius = top, BottomRadius = 0.5f, Height = 1, RadialSegments = sides, Rings = 1, CapBottom = false };
        iceSpikes = Add(new Batch(Point(5, 0), 400, Crystal(0.35f, 1.6f, 0.05f, 1f), true));
        thornSpikes = Add(new Batch(Point(4, 0), 400, Crystal(0.12f, 1.4f, 0.5f, 0.15f), true));
        stoneSpikes = Add(new Batch(Point(5, 0.12f), 200, Crystal(0.02f, 0.4f, 0.8f, 0.25f), true));
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
        // Ground left burning where a firepot broke or a star fell: fire in its cracks, its edge lit.
        "zone_pyre" or "firepot_ground" or "star_ground" => (Hdr("#ff8a2a", 1.6f), Inside.Embers, 0.2f),
        "zone_blight" or "zone_blight2" or "zone_plague" => (Hdr("#b8e04a", 1.3f), Inside.Veins, 0.04f),
        "zone_thorn" or "zone_bloom" or "zone_root" => (Hdr("#4ec85a", 1.3f), Inside.Roots, 0.03f),
        // Rotwood: the blight grown thorns, its thicket rotten wood in a stain of rot.
        "zone_rot" => (Hdr("#a8c84a", 1.3f), Inside.Roots, 0.03f),
        // Frostfire Comet's: fire in its cracks inside a rim of frost.
        "frostfire_ground" => (Hdr("#8ad0ff", 1.5f), Inside.Embers, 0.2f),
        _ => (Colors.Transparent, Inside.Runes, 0),
    };

    readonly System.Collections.Generic.Dictionary<int, (Mark Edge, Mark Fill)> grounds = new();

    /// <summary>The colour inside a ground: its edge's, but for frostfire's burning inside its frost.</summary>
    static Color FillOf(string art, Color edge) => art == "frostfire_ground" ? Hdr("#ff8a2a", 1.6f) : edge;
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
            // Lit by the colour alone (a decal's emission ignores alpha), so each
            // is premultiplied: the importer bleeds colour into the clear pixels,
            // and a turning fill showed as a glowing square.
            var fillTex = inside switch
            {
                Inside.Runes => Premul(Sprites.Runes(0)),
                // Burning ground is fire in its cracks (a spread of flame was one blob under her).
                Inside.Embers => veinTex,
                Inside.Roots => Premul(GD.Load<Texture2D>("res://art/fx/marks/roots_emit.png")),
                _ => veinTex,
            };
            var fill = Ground(z.X, z.Z, r, fillTex, FillOf(z.Art, edgeCol), 1e6f, 1.0f);
            var edge = Ground(z.X, z.Z, r, rimTex, edgeCol, 1e6f, 2.2f);
            g = (edge, fill);
            grounds[z.Id] = g;
            // Thornbloom bursts up all at once under the crowd: brambles across the whole of it,
            // standing as long as it holds them (a green ring with a few thorns read as any circle).
            if (inside == Inside.Roots)
            {
                float stand = (float)Math.Max(0.6, z.Life - z.Age);
                bool rot = z.Art == "zone_rot";
                Erupt(z.X, z.Z, 0, r * 0.95f, 14 + (int)(r * 7), SpikeKind.Thorn, 1.05f, stand, rot ? Hdr("#6a7a2a", 1f) : Hdr("#3fae4a", 1f));
                Erupt(z.X, z.Z, r * 0.7f, r * 1.0f, 8 + (int)(r * 3), SpikeKind.Thorn, 0.7f, stand, rot ? Hdr("#8a9a3a", 1f) : Hdr("#5ac85a", 1f));
                if (rot) Scars.Add("blight", V(z.X, Y(z.X, z.Z), z.Z), r * 1.05f, stand + 0.6f, 0);
                Books.Spawn("bramble_burst", V(z.X, Y(z.X, z.Z) + 0.15, z.Z), r * 1.1f, 0.9f, new Color(0.8f, 1.1f, 0.75f, 0.85f), flat: true, sizeEnd: r * 2.1f);
                Dust(z.X, z.Z, 8, 2.5f);
            }
            // Blightfield rots the ground it takes: a dark stain of rot under its veins (a bright
            // ring round clean ground read as a circle drawn on it, not a field gone bad).
            if (inside == Inside.Veins)
                Scars.Add("blight", V(z.X, Y(z.X, z.Z), z.Z), r * 1.05f, (float)Math.Max(0.8, z.Life - z.Age) + 0.6f, 0);
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
        // Never louder than a crowd's hostile mark (MECHANICS.md section 2: the enemy's marks are
        // drawn over hers), and half that while a boss is up, so the eye goes to his marks first.
        // (At full strength her thickets' and rots' rims, two or three at once, were the loudest
        // thing at Greymuzzle.) A thicket reads by its thorns, a rot by its stain, not their rims.
        float hush = bossUp ? 0.5f : 1f;
        // (Scaled in its colour: a decal's emission ignores its alpha, so an alpha of a fifth left
        // the rims at full strength.)
        g.Edge.Decal.Modulate = Dim(edgeCol, fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush);
        // The pattern inside, fainter still (the runes least: under her for a whole night, they
        // hid her), turning slowly.
        g.Fill.Decal.Modulate = Dim(FillOf(z.Art, edgeCol), fade * (inside == Inside.Runes ? 0.14f : inside == Inside.Veins ? 0.12f : 0.2f) * hush);
        g.Fill.Decal.Rotation = new Vector3(0, (float)(now * turn + z.Id * 1.7), 0);
        if (inside == Inside.Runes) RuneRing(z.Id, at, r, fade * hush, now);
        else if (inside == Inside.Embers) FirePatch(z.Id, at, r, fade);
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
                    // (Tinted orange: its filmed white heart tinted pale read as cream.)
                    if (R() < 0.3f) Books.Spawn("fire_loop", foot + Vector3.Up * 0.35f, 0.7f, 0.8f, new Color(1.3f, 0.74f, 0.34f, 0.7f), sizeEnd: 0.3f);
                    break;
                case Inside.Veins:
                    // A bubble of the blight rising and breaking, and its fume low over the ground.
                    Sparks.Spawn(foot, Vector3.Up * 0.5f, 0.6f, 0.07f, edgeCol * 0.9f, edgeCol * 0.3f, 0.16f, 0, 1);
                    if (R() < 0.4f) Smoke.Spawn(foot + Vector3.Up * 0.15f, new Vector3((R() - 0.5f) * 0.4f, 0.12f, (R() - 0.5f) * 0.4f), 1.6f, 0.5f, new Color(0.45f, 0.6f, 0.15f), new Color(0.2f, 0.3f, 0.08f), 1.3f, drag: 1, alpha: 0.16f);
                    break;
                case Inside.Roots when R() < 0.35f:
                    // Thorns: brambles break the ground and sink again, here and there.
                    Erupt(x, zz, 0, 0.45f, 3, SpikeKind.Thorn, 0.9f, 1.6f, Hdr("#4ec85a", 1f));
                    Books.Spawn("bramble_burst", foot + Vector3.Up * 0.1f, 1.2f, 1.4f, new Color(0.9f, 1.2f, 0.9f, 0.8f), flat: true, sizeEnd: 1.6f);
                    break;
                default:
                    // Thorns: a green glint where a bramble catches the light.
                    Sparks.Spawn(foot + Vector3.Up * 0.2f, Vector3.Up * 0.3f, 0.5f, 0.1f, pal.Core * 0.6f, pal.Glow * 0.3f, 0.02f, 0, 1, sprite: Sprites.Of("star"), spinV: 2);
                    break;
            }
        }
        return true;
    }

    /// <summary>A decal's colour at a strength: its light scaled in the colour itself (a decal's
    /// emission ignores alpha) and its alpha the same, for what it lays as paint.</summary>
    static Color Dim(Color c, float k) => new(c.R * k, c.G * k, c.B * k, k);

    readonly System.Collections.Generic.Dictionary<int, (MeshInstance3D Mesh, ShaderMaterial Mat)> runeRings = new();

    /// <summary>A hallowed ground's ring of runes in the air at her waist, at its edge, turning
    /// slowly (shaders/rune_ring.gdshader): seen over a packed crowd as its ground is not.</summary>
    void RuneRing(int id, Vector3 ground, float r, float strength, double now)
    {
        if (!runeRings.TryGetValue(id, out var ring))
        {
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/rune_ring.gdshader") };
            // (One seed and one turn for all: a cast laid over the last one crossfades into the same ring.)
            var mesh = new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(2, 2) }, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(mesh);
            runeRings[id] = ring = (mesh, mat);
        }
        ring.Mesh.Visible = true;
        // Runes about half a metre across whatever the reach (an integer, so the band closes).
        ring.Mat.SetShaderParameter("count", Mathf.Max(16, Mathf.Round(Mathf.Tau * r * 0.9f / 0.55f)));
        ring.Mat.SetShaderParameter("lit", strength * 0.5f);
        ring.Mesh.Position = ground + Vector3.Up * 0.95f;
        ring.Mesh.Rotation = new Vector3(0, (float)(-now * 0.18), 0);
        ring.Mesh.Scale = new Vector3(r, 1, r);
    }

    readonly System.Collections.Generic.Dictionary<int, (MeshInstance3D Mesh, ShaderMaterial Mat)> firePatches = new();

    /// <summary>Ground left burning: low tongues of flame standing round its edge and lapping in
    /// (the rise's wall in small, shaders/fire_wall.gdshader), so it burns over a packed crowd's
    /// feet where its embers on the ground are hidden. (A firepot's burst alone was a soft orange
    /// blob.)</summary>
    void FirePatch(int id, Vector3 ground, float r, float strength)
    {
        if (!firePatches.TryGetValue(id, out var patch))
        {
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
            mat.SetShaderParameter("seed", R() * 100);
            mat.SetShaderParameter("segs", 48f);
            mat.SetShaderParameter("cells", Mathf.Max(6, Mathf.Round(Mathf.Tau * r * 0.8f / 0.42f)));
            var mesh = new MeshInstance3D
            {
                Mesh = Kept("firecards48", () => FireCards(48)), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
            };
            AddChild(mesh);
            firePatches[id] = patch = (mesh, mat);
        }
        patch.Mesh.Position = ground - Vector3.Up * 0.05f;
        patch.Mesh.Scale = new Vector3(r * 0.8f, 0.75f + 0.1f * r, r * 0.8f);
        patch.Mat.SetShaderParameter("burn", strength);
    }

    /// <summary>A firepot breaking: a pot of blasting ember, not a ball of fire. The crack of it
    /// (a yellow-hot instant), tongues of flame jetting out from where it broke and stopping short,
    /// its powder thrown out burning, the clay pot's sherds flung out dark and tumbling, char-black
    /// smoke punched up, the air thrown, its light, its scorch. (The school's filmed burst alone was a
    /// soft orange fireball; it is kept small, as the heart of it.)</summary>
    void PotBurst(Ev.Explosion e)
    {
        float r = Mathf.Max(1.2f, (float)e.Radius), gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        var cam = GetViewport()?.GetCamera3D();
        Vector3 right = cam?.GlobalTransform.Basis.X ?? Vector3.Right, up = cam?.GlobalTransform.Basis.Y ?? Vector3.Up;
        Cam?.AddTrauma((float)Math.Min(0.3, 0.08 + e.Power * 0.1));
        // The crack: yellow-hot, never white (a white instant over the pale dead read as a cream disc).
        Sparks.Spawn(ground + Vector3.Up * 0.6f, Vector3.Zero, 0.09f, r * 0.45f, new Color(2.1f, 1.15f, 0.3f), new Color(1.3f, 0.35f, 0.05f), r * 0.85f, alpha: 0.8f);
        // Its heart: the filmed burst, small, quick and deep orange.
        Books.Spawn("fire_blast", ground + Vector3.Up * 0.5f, r * 0.5f, 0.42f, new Color(1.25f, 0.55f, 0.18f, 1), flat: true, sizeEnd: r * 1.15f);
        // Tongues of flame jetting out from where it broke, each turned on the screen along its way.
        int jets = 9 + Math.Min(4, e.Rank / 2);
        float a0 = R() * Mathf.Tau;
        for (int i = 0; i < jets; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / jets * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0.12f, Mathf.Sin(a)).Normalized();
            float sx = dir.Dot(right), sy = dir.Dot(up);
            float hot = 0.85f + R() * 0.3f;
            Sparks.Spawn(new Sparks.P
            {
                At = ground + Vector3.Up * 0.35f + dir * 0.25f * r, V = dir * r * (2.6f + R() * 1.6f), Drag = 6, Life = 0.26f + R() * 0.12f,
                Size = r * (0.3f + R() * 0.12f), SizeEnd = r * (0.62f + R() * 0.2f), Color = new Color(2.0f, 0.92f, 0.26f) * hot, ColorEnd = new Color(0.7f, 0.12f, 0.02f),
                Alpha = 1, Sprite = Sprites.Range("muzzle").First + 1 + (int)(R() * 4.99f), Spin = Mathf.Atan2(-sx, sy) + 0.001f, SpinV = 0.001f,
            });
        }
        // The blasting ember thrown out burning: fast, falling, and some still alight on the ground.
        int n = 20 + (int)(r * 6);
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = r * (2 + R() * 3.5f);
            Sparks.Spawn(ground + Vector3.Up * 0.5f, new Vector3(Mathf.Cos(a) * v, 2.5f + R() * 4.5f, Mathf.Sin(a) * v), 0.5f + R() * 0.6f, 0.05f + R() * 0.05f,
                new Color(2.4f, 1.1f, 0.28f), new Color(1.2f, 0.2f, 0.03f), 0.02f, 11, 1.2f);
        }
        // The pot's sherds: dark fired clay, flung out and tumbling down.
        for (int i = 0; i < 9; i++)
        {
            float a = R() * Mathf.Tau, v = r * (1.4f + R() * 2.2f);
            Smoke.Spawn(ground + Vector3.Up * 0.45f, new Vector3(Mathf.Cos(a) * v, 3 + R() * 3.5f, Mathf.Sin(a) * v), 0.6f + R() * 0.3f, 0.08f + R() * 0.07f,
                new Color(0.2f, 0.09f, 0.05f), new Color(0.12f, 0.06f, 0.04f), -1, gravity: 16, sprite: Sprites.Of("dirt"), spinV: 9);
        }
        // Char-black smoke punched up out of it, soon gone (lingering, it hid the next fight).
        for (int i = 0; i < 4; i++)
            Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.5f, 0.6f + R() * 0.4f, (R() - 0.5f) * r * 0.5f), new Vector3((R() - 0.5f) * 0.8f, 1.6f + R() * 0.8f, (R() - 0.5f) * 0.8f),
                0.75f + R() * 0.35f, r * 0.3f, new Color(0.1f, 0.08f, 0.07f), new Color(0.05f, 0.04f, 0.04f), r * 0.75f, drag: 1.4f, alpha: 0.55f);
        Waves.Add(ground + Vector3.Up * 0.35f, r * 1.6f, 0.3f, Palette.Of(School.Fire).Glow, 1);
        Flash(ground + Vector3.Up * 1.4f, Palette.Of(School.Fire).Light, 8, 0.28f, r * 2.4f + 3);
        Scars.Add("scorch", ground, r * 0.7f, 9);
    }

    /// <summary>Frostfire Comet breaking: fire and frost in one blow, side by side. Its burst half
    /// flame and half frost (the school's fireball alone, six metres across, swallowed her when it
    /// broke at her side), ice standing up round its rim, embers and frost thrown together, a scorch
    /// and a rime left.</summary>
    void FrostfireBurst(Ev.Explosion e)
    {
        float r = Mathf.Max(1.2f, (float)e.Radius), gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        Cam?.AddTrauma((float)Math.Min(0.3, 0.08 + e.Power * 0.1));
        float a = R() * Mathf.Tau;
        var side = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * r * 0.22f;
        Sparks.Spawn(ground + Vector3.Up * 0.8f, Vector3.Zero, 0.08f, r * 0.3f, new Color(1.5f, 1.25f, 1.1f), new Color(0.6f, 0.5f, 0.7f), r * 0.6f, alpha: 0.7f);
        Books.Spawn("fire_blast", ground + Vector3.Up * 0.5f - side, r * 0.4f, 0.5f, new Color(1.25f, 0.55f, 0.18f, 1), flat: true, sizeEnd: r * 0.95f);
        Books.Spawn("frost_burst", ground + Vector3.Up * 0.55f + side, r * 0.42f, 0.6f, new Color(0.5f, 0.75f, 1.15f, 1), flat: true, sizeEnd: r * 1.0f);
        Erupt(e.X, e.Z, r * 0.35f, r * 0.85f, 7 + (int)(r * 2), SpikeKind.Ice, 0.75f, 1.3f, IceDeep);
        for (int i = 0; i < 26; i++)
        {
            float b = R() * Mathf.Tau, v = r * (1.6f + R() * 3);
            var dir = new Vector3(Mathf.Cos(b) * v, 2.5f + R() * 4, Mathf.Sin(b) * v);
            if (i % 2 == 0) Sparks.Spawn(ground + Vector3.Up * 0.5f, dir, 0.5f + R() * 0.5f, 0.05f + R() * 0.04f, new Color(2.4f, 1.1f, 0.28f), new Color(1.2f, 0.2f, 0.03f), 0.02f, 10, 1.3f);
            else Sparks.Spawn(ground + Vector3.Up * 0.5f, dir * 0.8f, 0.55f + R() * 0.4f, 0.08f + R() * 0.05f, Hdr("#a8dcff", 1.5f), IceDeep * 0.4f, 0.02f, 8, 1.6f, sprite: Sprites.Of("frost_star"), spinV: 6);
        }
        for (int i = 0; i < 3; i++)
            Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.5f, 0.5f, (R() - 0.5f) * r * 0.5f), new Vector3(0, 0.9f + R() * 0.5f, 0), 0.9f, r * 0.3f, new Color(0.62f, 0.7f, 0.82f), new Color(0.4f, 0.45f, 0.55f), r * 0.7f, drag: 1.4f, alpha: 0.28f);
        Waves.Add(ground + Vector3.Up * 0.35f, r * 1.5f, 0.32f, Hdr("#8ad0ff", 1.4f), 1);
        Flash(ground + Vector3.Up * 1.4f, new Color("#ffb070"), 7, 0.3f, r * 2.2f + 3);
        Scars.Add("scorch", ground - side, r * 0.5f, 9);
        Scars.Add("frost", ground + side, r * 0.5f, 6);
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {
        if (firePatches.Count > 0)
        {
            var out1 = new System.Collections.Generic.List<int>();
            foreach (var (id, patch) in firePatches)
                if (!alive.Contains(id)) { patch.Mesh.QueueFree(); out1.Add(id); }
            foreach (var id in out1) firePatches.Remove(id);
        }
        if (runeRings.Count > 0)
        {
            var over = new System.Collections.Generic.List<int>();
            foreach (var (id, ring) in runeRings)
                if (!alive.Contains(id)) { ring.Mesh.QueueFree(); over.Add(id); }
            foreach (var id in over) runeRings.Remove(id);
        }
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

    static readonly System.Collections.Generic.Dictionary<Texture2D, Texture2D> premul = new();

    /// <summary>A texture with its colour multiplied by its alpha, for what reads
    /// only its colour (a decal's emission): clear pixels made black.</summary>
    public static Texture2D Premul(Texture2D tex)
    {
        if (premul.TryGetValue(tex, out var done)) return done;
        var img = tex.GetImage();
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        for (int y = 0; y < img.GetHeight(); y++)
            for (int x = 0; x < img.GetWidth(); x++)
            {
                var c = img.GetPixel(x, y);
                img.SetPixel(x, y, new Color(c.R * c.A, c.G * c.A, c.B * c.A, c.A));
            }
        img.GenerateMipmaps();
        return premul[tex] = ImageTexture.CreateFromImage(img);
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
                float a = Mathf.Exp(-Mathf.Pow((r - 0.93f) / 0.014f, 2)) + 0.1f * Mathf.Exp(-Mathf.Pow((r - 0.91f) / 0.04f, 2));
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
            if (e.School == School.Storm)
            {
                // A real arc: a white-hot forking thread in a blue glow that flickers
                // (a lone thread read as a pale string), a crackle where it bites.
                Ribbons.Bolt(a, bb, 0.34f * g, 0.22f, Hdr("#6c9cff", 1f), 4.2f, art == "arc_fork" ? 3 : 2, 0.24f);
                Ribbons.Bolt(a, bb, 0.9f * g, 0.16f, Hdr("#2a5cff", 1f), 1.3f, 0, 0.2f);
                for (int i = 0; i < 4; i++)
                {
                    var tip = bb + new Vector3((R() - 0.5f) * 1.2f, (R() - 0.3f) * 0.8f, (R() - 0.5f) * 1.2f);
                    Ribbons.Bolt(bb, tip, 0.1f * g, 0.12f, Hdr("#9ac0ff", 1f), 3f, 0, 0.35f);
                }
                Sparks.Spawn(bb, Vector3.Zero, 0.12f, 0.75f * g, Hdr("#a8c8ff", 1.6f), Hdr("#3a6aff", 0.6f), 0.3f, sprite: Sprites.Of("spark"), spinV: 0);
                continue;
            }
            Ribbons.Line(new[] { a, (a + bb) / 2 + Vector3.Up * 0.4f, bb }, 0.12f * g, 0.25f, col, 2.2f, Ribbons.Style.Wisp);
            Sparks.Spawn(bb, Vector3.Zero, 0.1f, 0.7f * g, pal.Core * 0.8f, pal.Glow * 0.2f, 0.25f, sprite: Sprites.Of("flare"));
        }
        if (e.School == School.Storm) Flash(V(p[^2], Y(p[^2], p[^1]) + 2, p[^1]), pal.Light, 7 * g, 0.18f, 9);
        return true;
    }
}
