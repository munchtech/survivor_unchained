using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her auto-attacks' shared hit kit (SKILL_VFX_STUDY §6 item 2): what every body her
/// Oathblade, Disc or Shield Bash strikes shows. Steel sparks off the body, flung
/// along the blow (one pooled spark batch, never a node per hit; capped per swing);
/// the struck rim is the crowd's own (CrowdView: Battle sets the body's Flash, the
/// VAT shader lights its rim and decays it in a few frames); and a 2 to 3 frame
/// hitstop on the first hit of a swing only (WorldScene asks FirstHitStop).
///
/// The Oathblade's sweep beats (dev only, --aa-beats): on her 3rd, 5th and 7th
/// swing a frame at +1 and +3 drawn frames and one as the first hit's hitstop
/// lands; one plain frame mid-fight (half a second after the 4th swing).
/// </summary>
public partial class BattleFx
{
    /// <summary>The Oathblade and its evolutions (skills.json oathblade: slash_steel, slash_holy, slash_blood).</summary>
    public static bool IsOath(string? art) => art is "slash_steel" or "slash_holy" or "slash_blood";

    /// <summary>The hitstop a blow asks for as the first hit of its swing (seconds; 0 none) and how long after
    /// the blow it lands (the blade meeting the body, not the swing's first frame). Her auto-attacks' arts only:
    /// the Disc and Shield Bash add theirs here.</summary>
    public static (double Len, double Delay) FirstHitStop(Ev.Hit h) =>
        h.Dot || h.ByFlare || h.Blocked ? (0, 0) : IsOath(h.Art) ? (0.042, 0.03) : (0, 0);

    /* ------------------------------------------------------- the sweep -- */

    // Her Oathblade's gold, its evolutions' hues (linear, near 1 so the tone curve keeps them a colour;
    // the white-hot edge is the shader's), and the sparks off what they strike.
    static readonly Color OathSteel = Hdr("#ffb83a", 1.15f), OathHoly = Hdr("#ffd772", 1.2f), OathBlood = Hdr("#ff2a1a", 1.15f);
    static Color OathHue(string art) => art switch { "slash_holy" => OathHoly, "slash_blood" => OathBlood, _ => OathSteel };
    static Color OathSpark(string art) => art == "slash_blood" ? Blood : art == "slash_holy" ? OathGold : Ember;

    // The swing in flight (for the struck's sparks: flung on along the blade's path), and how many full kits it has thrown.
    Vector3 oathAt;
    bool oathMirror;
    int oathKits;
    /// <summary>Full kits (sparks and contact) per swing; the rest of a crowd struck get two sparks.</summary>
    const int OathKits = 6;

    /// <summary>The Oathblade's sweep: ONE gold crescent leaving her blade, its leading edge white-hot, light only
    /// (it lights the ground, never darkens it), gone in 6 frames; a faint gold pool on the ground under it for 3.</summary>
    void OathSweep(Ev.Slash e, Vector3 at, float facing, float reach, float g)
    {
        string art = e.Art ?? "";
        float rich = Mathf.Min(g, 1.35f);
        oathAt = at; oathMirror = mirror; oathKits = 0;
        var hue = OathHue(art);
        OathBlades.Add(at, facing, reach, (float)e.Arc * 1.1f, mirror, 0.055f, 0.045f, hue * (0.9f + 0.1f * g), 0.4f * rich);
        // The pool: under the middle of the arc, warm and faint, the decal's box shallow so it lights the ground only.
        var mid = new Vector3(Mathf.Cos((float)e.Angle), 0, Mathf.Sin((float)e.Angle)) * reach * 0.55f;
        var m = Ground(e.X + mid.X, e.Z + mid.Z, reach * 0.55f, glowTex!, hue with { A = 1 }, 0.05f, 0.9f);
        m.Decal.Size = new Vector3(reach * 1.1f, 0.6f, reach * 1.1f);
        // The Watch's oath along the edge of a ranked Oathblade: a few gold glints that hang.
        if (e.Rank >= 5 && art != "slash_blood")
            for (int i = 0; i < 4; i++)
            {
                float a = (float)e.Angle + (float)e.Arc * (R() - 0.5f);
                var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + rim * reach * 0.95f, Vector3.Up * 0.4f, 0.5f, 0.12f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
    }

    /// <summary>The shared hit kit at a struck body (`at`, chest height; `away` the blow's way, flat):
    /// steel sparks white-hot cooling to `spark`, flung on along the blow and the blade's path, and a
    /// 3-frame contact star. `full` false (past the swing's cap, or the frame's hit budget spent) throws
    /// two sparks only. The rim is the crowd's own struck flash; the hitstop is FirstHitStop's.
    /// The Disc and Shield Bash call this with their own `spark` hue.</summary>
    public void HitKit(Vector3 at, Vector3 away, Color spark, float g, bool crit, bool full = true)
    {
        full = full && oathKits++ < OathKits;
        // Along the blade's path at this body (the swing's tangent there), so sparks fly on with the cut.
        var rim = at - oathAt; rim.Y = 0;
        var along = rim.LengthSquared() > 0.01f ? new Vector3(-rim.Z, 0, rim.X).Normalized() * (oathMirror ? -1 : 1) : Vector3.Zero;
        int n = full ? (crit ? 9 : 6) : 2;
        for (int i = 0; i < n; i++)
        {
            var v = away * (3 + R() * 4) + along * (3 + R() * 4) + new Vector3((R() - 0.5f) * 3, 1.2f + R() * 2.5f, (R() - 0.5f) * 3);
            Sparks.Spawn(at + Vector3.Up * (R() - 0.5f) * 0.3f, v, 0.14f + R() * 0.12f, 0.035f + R() * 0.02f, SteelWhite, spark, 0.008f, 9, 2.5f);
        }
        if (full) Sparks.Spawn(at, Vector3.Zero, 0.05f, (crit ? 0.4f : 0.24f) * g, SteelWhite * 0.5f, SteelWhite * 0.1f, 0.12f, sprite: Sprites.Of("flare"), spinV: 0);
    }

    /* --------------------------------------------------------- the beats -- */

    static readonly bool AaBeats = Args.Has("aa-beats");
    int oathSwings, beatHitFor;

    void BeatSwing(Ev.Slash e)
    {
        if (!AaBeats) return;
        oathSwings++;
        if (oathSwings is 3 or 5 or 7)
        {
            Shots.WantFrames($"s{oathSwings}_f1", 1);
            Shots.WantFrames($"s{oathSwings}_f3", 3);
            beatHitFor = oathSwings;
        }
        else beatHitFor = 0;
        if (oathSwings == 4) Shots.Want("mid", 0.5);
        GD.Print($"[aa-beats] swing {oathSwings} t={time:F2} angle={e.Angle:F2} arc={e.Arc:F2} reach={e.Reach:F2}");
    }

    void BeatHit(Ev.Hit e)
    {
        if (AaBeats && oathSwings == 5 && b0 != null) GD.Print($"[aa-beats] hit at dx={e.X - b0.Player.X:F2} dz={e.Z - b0.Player.Z:F2} angle={Math.Atan2(e.Z - b0.Player.Z, e.X - b0.Player.X):F2}");
        if (!AaBeats || beatHitFor == 0) return;
        // (the frame the first hit's hitstop holds: its delay is 0.03 s, two frames on)
        Shots.WantFrames($"s{beatHitFor}_hit", 2);
        beatHitFor = 0;
    }
}
