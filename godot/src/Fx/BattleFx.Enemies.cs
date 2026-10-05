using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// What the enemy's own verbs look like (combat's list): a people's rally in
/// its own colour, a summoning circle where its kin will rise, a slam that
/// throws stone, the glint of a haste or a ward on those it lifted, and its
/// bolts and orbs in flight. Danger keeps its own language (amber blow,
/// violet ground, hatched, never filled solid); a people's colour is for what
/// is theirs and not yet a blow, and is never her red or the dead's grey.
/// </summary>
public partial class BattleFx
{
    /// <summary>Each people's colour: the Pack wolf-eye yellow, the Kerchiefs
    /// carmine, the dead grave-green, the lamplings a guttering lamp, the
    /// blight sick yellow-green, the wild moss.</summary>
    static Color People(Faction f) => f switch
    {
        Faction.Pack => Hdr("#d8d040", 1.3f),
        Faction.Kerchief => Hdr("#d0204a", 1.4f),
        Faction.Dead => Hdr("#4ad8a0", 1.3f),
        Faction.Lampling => Hdr("#e8b040", 1.1f),
        Faction.Blight => Hdr("#a8c828", 1.3f),
        Faction.Wild => Hdr("#5ab040", 1.3f),
        _ => Hdr("#a0a8ff", 1.2f),
    };

    /// <summary>A rally: a ring of the people's colour racing out to the edge of
    /// its reach, its band faint on the ground, and motes rising off the one who
    /// called it. (Drawn as a holy band, it read as a white-gold pool of light.)</summary>
    void Rally(Ev.Telegraph e, Color col)
    {
        float r = (float)e.Radius;
        var ground = V(e.X, Y(e.X, e.Z), e.Z);
        AddFront(ground, r, 0.6f, 0.22f, col, 1.6f, Ribbons.Style.Wisp, 0.15f);
        BandMark(e.X, e.Z, e.Inner, r, col * 0.25f, (float)e.Duration, e.Id);
        double bx = e.ByX ?? e.X, bz = e.ByZ ?? e.Z;
        var by = V(bx, Y(bx, bz) + 0.4, bz);
        for (int i = 0; i < 8; i++)
            Sparks.Spawn(by + new Vector3((R() - 0.5f) * 0.8f, 0, (R() - 0.5f) * 0.8f), Vector3.Up * (1.5f + R() * 1.5f), 0.7f + R() * 0.4f, 0.07f, col, col * 0.3f, 0.02f, -0.5f, 1.5f);
    }

    static Texture2D? summonTex;

    /// <summary>The painted rune ring (fx_sprites.py's rune_ring), its light as a decal's emission.</summary>
    static Texture2D SummonTexture()
    {
        if (summonTex != null) return summonTex;
        var img = Sprites.Array.GetLayerData(Sprites.Range("rune_ring").First);
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        for (int y = 0; y < img.GetHeight(); y++)
            for (int x = 0; x < img.GetWidth(); x++)
            {
                var c = img.GetPixel(x, y);
                float a = c.R * c.A;
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        img.GenerateMipmaps();
        return summonTex = ImageTexture.CreateFromImage(img);
    }

    /// <summary>Where a people's kin will rise: a circle of runes in their colour,
    /// burning in over the call, and the ground breaking open when they come.</summary>
    void Summoning(Ev.Telegraph e, Color col)
    {
        float r = (float)e.Radius * 1.3f;
        var m = Ground(e.X, e.Z, r, SummonTexture(), col, (float)e.Duration, 1.8f);
        m.Decal.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
        double x = e.X, z = e.Z;
        float life = (float)e.Duration;
        pending.Add((time + life, () =>
        {
            var g = V(x, Y(x, z), z);
            Scars.Add("crack", g, r * 0.9f, 4f, 0);
            Dust(x, z, 6, 2.2f);
            for (int i = 0; i < 6; i++)
                Smoke.Spawn(g + Vector3.Up * 0.2f, new Vector3((R() - 0.5f) * 3, 2.5f + R() * 2, (R() - 0.5f) * 3), 0.6f, 0.08f + R() * 0.06f, new Color("#4a3a2a"), gravity: 12, sprite: Sprites.Of("dirt"), spinV: 5);
            Sparks.Spawn(g + Vector3.Up * 0.3f, Vector3.Zero, 0.25f, r * 1.2f, col * 0.5f, null, r * 1.6f, sprite: Sprites.Range("rune_ring").First + 1, spinV: 1.5f);
        }));
    }

    /// <summary>A slam landing (an enemy's blow of steel or stone): the ground thrown
    /// up in a ring of stone that sinks again, and the dust rolling out over it.</summary>
    void Slammed(double x, double z, float r)
    {
        Erupt(x, z, r * 0.45f, r * 1.0f, 7 + (int)(r * 3), SpikeKind.Stone, 0.55f + r * 0.12f, 0.8f, new Color(0.5f, 0.4f, 0.3f));
        var g = V(x, Y(x, z), z);
        for (int i = 0; i < 12; i++)
        {
            float a = i / 12f * Mathf.Tau + R() * 0.3f;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Smoke.Spawn(g + Vector3.Up * 0.25f + dir * r * 0.5f, dir * r * 2.2f + Vector3.Up * 0.3f, 0.7f, r * 0.18f, new Color(0.42f, 0.34f, 0.26f), new Color(0.3f, 0.25f, 0.2f), r * 0.45f, drag: 2.5f, alpha: 0.4f);
        }
    }

    /// <summary>Hers, got up out of the ground (Gravecall): a grave-sigil of soul-light burning in
    /// where it breaks open, soul-fire licking up off the one climbing out, the earth thrown.
    /// (A puff of dirt and a blue spark, it read as one of the enemy's dead rising.)</summary>
    void Raised(Ev.Spawn e)
    {
        float gy = Y(e.X, e.Z);
        var g = V(e.X, gy, e.Z);
        var m = Ground(e.X, e.Z, 1.1f, SummonTexture(), Soul * 0.8f, 1.1f, 2f);
        m.Decal.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
        m.Grow = true;
        Scars.Add("crack", g, 0.9f, 3f, 0);
        for (int i = 0; i < 8; i++)
            Smoke.Spawn(g + Vector3.Up * 0.15f, new Vector3((R() - 0.5f) * 2.5f, 1.5f + R() * 2, (R() - 0.5f) * 2.5f), 0.6f, 0.09f + R() * 0.06f, new Color("#3a2e22"), gravity: 10, sprite: Sprites.Of("dirt"), spinV: 4);
        for (int i = 0; i < 7; i++)
            MoonTongue(g + new Vector3((R() - 0.5f) * 0.7f, 0.2f + R() * 0.5f, (R() - 0.5f) * 0.7f), Vector3.Up * (1.2f + R() * 1.2f), 0.35f + R() * 0.15f, Soul);
    }

    /// <summary>The soul-light of what is hers (Gravecall's risen): sea-green, never the enemy dead's grey.</summary>
    static readonly Color Soul = Hdr("#3affc8", 1.35f);

    int buffBudget;

    /// <summary>Those a rally has lifted: a haste is speed lines at their heels, a
    /// ward a pale hexagon that winks on them now and then.</summary>
    void Buffs(Battle b)
    {
        buffBudget = 14;
        foreach (var e in b.Enemies.Living())
        {
            // Hers among the dead: a small soul-flame at the breast, so the crowd tells them apart.
            if (e.Disposition == Disposition.Ally && e.Def.Family == Family.Undead)
                Body(V(e.X, Y(e.X, e.Z) + 1.25 * (e.Def.Scale ?? 1), e.Z), 0.42f, "wisp", Soul * 0.8f, (float)time * 2 + e.Id);
            if (buffBudget <= 0) continue;
            if (e.HasteT <= 0 && e.WardT <= 0) continue;
            var col = People(e.Faction);
            var feet = V(e.X, Y(e.X, e.Z) + 0.25, e.Z);
            if (e.HasteT > 0 && R() < 0.25f)
            {
                var back = new Vector3((float)-Math.Cos(e.Facing), 0, (float)-Math.Sin(e.Facing));
                Ribbons.Line(new[] { feet + back * 0.2f, feet + back * 0.7f, feet + back * 1.2f }, 0.08f, 0.18f, col, 2f, Ribbons.Style.Steel, new[] { 1f, 0.6f, 0f });
                buffBudget--;
            }
            if (e.WardT > 0 && R() < 0.06f)
            {
                Sparks.Spawn(feet + Vector3.Up * 1.0f, Vector3.Zero, 0.35f, 0.9f, Hdr("#c8dcff", 1.2f) * 0.6f, null, 1.1f, sprite: Sprites.Range("ward_disc").First + 1, spinV: 0.5f);
                buffBudget--;
            }
        }
    }

    /// <summary>An enemy's bolt or orb in flight, drawn as itself in the danger
    /// language: false for what this does not draw.</summary>
    bool HostileFlight(Projectile p, Vector3 at, float heading, double now)
    {
        long key = p.Id * 7919L + 0x5a5a;
        var fwd = new Vector3(Mathf.Sin(heading), 0, Mathf.Cos(heading));
        switch (p.Art)
        {
            case "bolt_bone":
            {
                // A crossbow bolt with a head of bone, and a thin streak of danger behind it.
                steel.Add(new Transform3D(new Godot.Basis(Vector3.Up, heading).Scaled(Vector3.One * 0.9f), at), new Color(0.85f, 0.78f, 0.65f));
                Ribbons.Feed(key, at, 0.09f, 0.12f, Hdr("#ff4a2a", 1f), 2.2f, Ribbons.Style.Steel);
                return true;
            }
            case "frost_orb":
            {
                // A ball of cold, blue at its heart with a danger rim, glinting as it comes.
                Shade(at, 1.2f, 0.6f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.22f), at), Hdr("#d8f0ff", 1.8f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.75f), at), Hdr("#3a8aff", 1.4f) * 0.25f);
                Body(at, 0.65f, "frost_star", Hdr("#8fd0ff", 1.3f), (float)now * 4 + p.Id);
                SpinArcs(at, 0.42f, (float)now * 12 + p.Id, 0.06f, Palette.HostileRim * 0.5f, 2f);
                Ribbons.Feed(key, at - fwd * 0.2f, 0.28f, 0.16f, Hdr("#5ab8ff", 1f), 1.8f, Ribbons.Style.Frost);
                return true;
            }
        }
        return false;
    }
}
