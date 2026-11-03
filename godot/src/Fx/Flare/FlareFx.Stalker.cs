using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The stalker's Flares' stand-in marks until the next Flare build (vfx12 item 4: the Road's Toll and One Arrow barely
/// showed at the play camera, failing "every press visible"). Each blow marks where it lands, in the calling's palette
/// (her arrows' warm steel #ffe8c0, her daggers' steel white, the Toll's poison green): no new art, the Flare's own bits.
/// The Toll: an X of steel at chest height on each cut, a spray of steel motes and a fleck of venom; the last cut a
/// bigger X and a ring of motes. One Arrow: a line of light down its 30 m, a burst at its end; each split a thinner line.
/// Bits per press: the Toll ~310 (12 cuts), One Arrow ~150 (3 splits; ~240 with 6). Real time, as all the Flare's bits.
/// </summary>
public partial class FlareFx
{
    static readonly Color StSteel = new(2.3f, 2.2f, 2.0f), StSteelEnd = new(1.0f, 0.85f, 0.62f);
    static readonly Color StArrow = new(2.5f, 2.25f, 1.8f), StArrowEnd = new(1.1f, 0.78f, 0.45f);
    static readonly Color StSplit = new(2.3f, 1.6f, 0.85f), StSplitEnd = new(0.9f, 0.42f, 0.18f);
    static readonly Color StVenom = new(0.55f, 1.5f, 0.35f), StVenomEnd = new(0.12f, 0.45f, 0.08f);

    /// <summary>A staged blow of the stalker's (the Toll's "cut", One Arrow's "arrow" and "split").</summary>
    void StalkerBlow(Ev.Flare e)
    {
        switch (e.Part)
        {
            case "cut": TollMark(e); break;
            case "arrow": ArrowMark(e, false); break;
            case "split": ArrowMark(e, true); break;
        }
    }

    void TollMark(Ev.Flare e)
    {
        var p = new Vector3((float)e.TX, (float)HeightAt(e.TX, e.TZ) + 1.1f, (float)e.TZ);
        bool last = e.Last;
        int slashes = last ? 4 : 2;
        float a0 = R() * Mathf.Tau, len = last ? 40 : 30;
        // Her cut's way to it, a thin line of steel from where she stands (the Toll reads as twelve strikes out of her).
        var her = new Vector3((float)e.X, 0, (float)e.Z);
        if (new Vector2(p.X - her.X, p.Z - her.Z).Length() > 1.2f)
            Line(her, new Vector3(p.X, 0, p.Z), 1.05f, 0.5f, StSteel * 0.8f, StSteelEnd * 0.6f, 0.3f, 0.12f, 0.18f);
        glow.Spawn(FlareBits.Kind.Mote, p, Vector3.Zero, last ? 0.55f : 0.4f, last ? 2.6f : 1.8f, StSteelEnd * 0.5f, StSteelEnd * 0.1f, sizeEnd: last ? 3.4f : 2.2f);
        for (int i = 0; i < slashes; i++)
        {
            // A slash: a thread drawn from its head back along its way (flare_bits: len = size + way x 0.08).
            float a = a0 + i * Mathf.Pi / slashes + (R() - 0.5f) * 0.3f;
            var way = new Vector3(Mathf.Cos(a), (i % 2 == 0 ? 0.7f : -0.7f), Mathf.Sin(a)) * len;
            glow.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Thread, At = p + way.Normalized() * 1.1f, Show = way, Life = last ? 0.55f : 0.42f,
                Size = last ? 1.1f : 0.85f, SizeEnd = last ? 0.8f : 0.6f, Color = StSteel, ColorEnd = StSteelEnd,
            });
        }
        int motes = last ? 30 : 14;
        for (int i = 0; i < motes; i++)
            glow.Spawn(FlareBits.Kind.Mote, p, Rand3() * (5 + R() * 5), 0.24f + R() * 0.18f, 0.09f + R() * 0.05f, StSteel, StSteelEnd, sizeEnd: 0.03f, drag: 5);
        for (int i = 0; i < 6; i++)
            glow.Spawn(FlareBits.Kind.Mote, p + Rand3() * 0.3f, Rand3() * 1.6f, 0.5f + R() * 0.25f, 0.14f, StVenom, StVenomEnd, sizeEnd: 0.06f, gravity: 2.5f, drag: 2);
        if (last)
            for (int i = 0; i < 24; i++)
            {
                float a = i * Mathf.Tau / 24;
                glow.Spawn(FlareBits.Kind.Mote, p + Vector3.Down * 0.8f, new Vector3(Mathf.Cos(a), 0.1f, Mathf.Sin(a)) * 11, 0.4f, 0.16f, StSteel, StSteelEnd, sizeEnd: 0.06f, drag: 4);
            }
    }

    /// <summary>A line of light from (from) to (to) at h over the ground: threads a metre apart drawn along it (size: the
    /// thread's; width a quarter of it), each with a soft glow (halo: its share of the colour), fading from (from) first:
    /// life at (from), + grow at (to). Up to 40 threads and 40 motes.</summary>
    void Line(Vector3 from, Vector3 to, float h, float size, Color c, Color ce, float life, float grow, float halo)
    {
        var d = to - from; d.Y = 0;
        float l = d.Length();
        if (l < 0.3f) return;
        var dir = d / l;
        int n = Mathf.Min(40, (int)l + 1);
        for (int i = 0; i < n; i++)
        {
            var q = from + dir * Mathf.Min(l, (i + 1) * (l / n));
            q.Y = (float)HeightAt(q.X, q.Z) + h;
            float k = (float)i / Mathf.Max(1, n - 1);
            glow.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Thread, At = q, Show = dir * 15, Life = life + grow * k,
                Size = size, SizeEnd = size * 0.7f, Color = c, ColorEnd = ce,
            });
            glow.Spawn(FlareBits.Kind.Mote, q, Vector3.Zero, life + grow * k, size * 1.5f, c * halo, ce * (halo * 0.4f));
        }
    }

    void ArrowMark(Ev.Flare e, bool split)
    {
        var from = new Vector3((float)e.X, 0, (float)e.Z);
        var to = new Vector3((float)e.TX, 0, (float)e.TZ);
        var d = to - from;
        float l = d.Length();
        if (l < 0.5f) return;
        var dir = d / l;
        float h = split ? 1.0f : 1.15f;
        Color c = split ? StSplit : StArrow, ce = split ? StSplitEnd : StArrowEnd;
        Line(from, to, h, split ? 0.5f : 0.7f, c, ce, split ? 0.34f : 0.42f, 0.25f, split ? 0.2f : 0.24f);
        var end = from + dir * l;
        end.Y = (float)HeightAt(end.X, end.Z) + h;
        int burst = split ? 8 : 14;
        for (int i = 0; i < burst; i++)
            glow.Spawn(FlareBits.Kind.Mote, end, Rand3() * (4 + R() * 5) + dir * 3, 0.25f + R() * 0.2f, 0.1f + R() * 0.05f, c, ce, sizeEnd: 0.03f, drag: 5);
        if (split)
        {
            // Where it leaves the arrow: a small flare of steel.
            var o = new Vector3(from.X, (float)HeightAt(from.X, from.Z) + h, from.Z);
            for (int i = 0; i < 8; i++)
                glow.Spawn(FlareBits.Kind.Mote, o, Rand3() * (3 + R() * 3), 0.22f + R() * 0.12f, 0.1f, StArrow, StArrowEnd, sizeEnd: 0.03f, drag: 5);
        }
    }
}
