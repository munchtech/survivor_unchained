using System;
using System.IO;
using SurvivorUnchained.Look;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P7 round 3) The skills lead's numbers in fx_language.json "p7" (logic/Look/FxP7.cs): every path the views
/// read is there, and the judge r2's floors hold (rings and smears in their px, stars at most 7-8 spikes, the press 3 frames).</summary>
public class FxP7Tests
{
    static FxP7 Real()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return FxP7.Parse(File.ReadAllText(Path.Combine(d?.FullName ?? Directory.GetCurrentDirectory(), "data", "look", "fx_language.json")));
    }

    [Fact]
    public void EveryPathTheViewsReadIsThere()
    {
        var p = Real();
        foreach (var k in new[] { "glint.px", "glint.frames", "kick.puffs", "kick.px", "kick.life", "leap.ring.lead_px", "leap.ring.trail_px", "leap.ring.arcs",
            "leap.ring.cover", "leap.ring.alpha", "leap.ring.flash_frames", "leap.ring.flash_k", "leap.ribbon.head_px", "leap.ribbon.life", "leap.ribbon.turn_deg",
            "leap.star.spikes", "leap.star.streaks", "leap.star.root_px", "leap.star.reach", "leap.star.hold_frames", "leap.star.step_frames",
            "leap.crack.root_px", "leap.crack.tip_px", "leap.crack.gap", "leap.crack.seam_px", "leap.crack.cool", "leap.dust.puffs", "leap.dust.px", "leap.dust.run", "leap.chunks",
            "charge.crescent.px", "charge.crescent.frames", "charge.ribbon.head_px", "charge.ribbon.life", "charge.star.spikes", "charge.star.px", "charge.star.root_px",
            "charge.star.root_tip", "charge.star.frames", "charge.stop.spikes", "charge.stop.px", "charge.stop.root_px", "charge.stop.lead_px", "charge.stop.trail_px",
            "charge.stop.run", "charge.stop.reach", "charge.ghost.gap", "charge.ghost.life", "charge.plow.gap", "charge.plow.px", "dash.ribbon.head_px", "dash.ribbon.life",
            "dash.shove.lead_px", "dash.shove.trail_px", "dash.shove.run", "dash.shove.puffs", "dash.shove.px", "storm.smear.head_px", "storm.smear.arc_deg", "storm.smear.alpha",
            "storm.seam.px", "storm.ring.lead_px", "storm.ring.trail_px", "storm.ring.run", "storm.star.spikes", "storm.star.px", "storm.star.root_px", "storm.nick.px",
            "storm.nick.frames", "vow.plant.flash_px", "vow.plant.puffs", "vow.dome.rim_px", "vow.dome.flare_px", "vow.dome.flare_s", "vow.store.px", "vow.store.grow",
            "vow.burst.spikes", "vow.burst.px", "vow.burst.root_px", "vow.burst.frames", "vow.burst.lead_px", "vow.burst.trail_px", "vow.burst.run", "vow.burst.light_k", "vow.burst.light_frames", "wave.arc_px", "wave.dust_px", "wave.shed", "wave.open_deg" })
            Assert.True(p.Has(k), "fx_language.json p7 lacks " + k);
    }

    [Fact]
    public void TheJudgesFloorsHold()
    {
        var p = Real();
        Assert.InRange(p["glint.px"], 20, 30);
        Assert.Equal(3, (int)p["glint.frames"]);
        Assert.InRange(p.All("leap.star.spikes")[1], 3, 7);
        Assert.InRange(p["leap.star.root_px"], 1, 25);
        Assert.InRange(p["storm.seam.px"], 1, 4);
        Assert.InRange(p["vow.dome.rim_px"], 6, 8);
        Assert.InRange(p["vow.burst.light_k"], 0, 0.4f);
        Assert.Equal(1.0, (double)p.Curve("leap.ring.cover", 0.4f), 3);
        Assert.Equal(0.55, (double)p.Curve("leap.ring.cover", 0.175f), 3);
        Assert.InRange(p.Count("kick.puffs", 0.999f), 8, 12);
        // (r3 fix 2) a ring is 3-9 painted arcs; its shed dust two-value puffs of 20-60 px; the charge stop an open arc
        Assert.InRange(p["wave.arc_px"], 300, 700);
        Assert.InRange(p.All("wave.dust_px")[0], 20, 40);
        Assert.InRange(p["wave.open_deg"], 120, 300);
    }

    /// <summary>(P7 lead 6, take 5) The held cut's stroke: a comma laid in lanes, three bands, steel first, fingers for a
    /// tail; the contact one chisel of the stroke's own paint, smaller than the stroke's head, never a line or a crown.</summary>
    [Fact]
    public void TheHeldCutsStrokeIsACommaInThreeBands()
    {
        var p = Real();
        foreach (var k in new[] { "grip.lead_frames", "grip.slow", "grip.min_len", "grip.aspect", "grip.tail_px", "grip.point", "grip.glow", "grip.glow_end",
            "grip.lit", "grip.retract", "grip.shed_at", "grip.lane.jitter", "grip.lane.tongue", "grip.lane.point", "grip.lane.gap", "grip.lane.shed",
            "grip.contact.wait_frames", "grip.contact.k_min", "grip.contact.lift", "grip.contact.kill", "grip.contact.crowd", "grip.contact.tears",
            "grip.contact.grit", "grip.contact.kite", "grip.contact.full_frames", "grip.contact.steps", "grip.contact.shards", "grip.contact.fan", "grip.contact.fly", "grip.lane.last",
            "grip.snap", "grip.face", "grip.link.on" })
            Assert.True(p.Has(k), "fx_language.json p7 lacks " + k);
        Assert.Equal(3, p.All("grip.lit").Length);
        Assert.Equal(2, p.All("grip.point").Length);
        Assert.Equal(4, p.All("grip.lane.gap").Length);
        float jit = p.All("grip.lane.jitter")[1];
        var kite = p.All("grip.contact.kite");
        var gold = new System.Collections.Generic.Dictionary<string, float>();
        foreach (var w in new[] { "sunder", "oath" })
        {
            var l = p.All($"grip.{w}.lanes");
            int n = l.Length / 4;
            Assert.True(l.Length % 4 == 0 && n >= 5 && n <= 8, $"grip.{w}.lanes: 5 to 8 lanes of 4");
            float sum = 0, core = 0, mid = 0, edge = 0, longest = 0, shortest = 1;
            var mids = new System.Collections.Generic.HashSet<float>();
            for (int i = 0; i < n; i++)
            {
                float lw = l[i * 4], c = l[i * 4 + 1], m = l[i * 4 + 2], e = l[i * 4 + 3];
                Assert.True(lw >= 0.1f && 0 <= c && c <= m && m <= e && e <= 1 && (c == 0 || c < m) && (m == 0 || m < e), $"grip.{w}.lanes[{i}] out of order");
                sum += lw;
                if (c > 0) core += lw; else if (m > 0) mid += lw; else edge += lw;
                if (m > 0) mids.Add(m);
                longest = Math.Max(longest, e); shortest = Math.Min(shortest, e);
            }
            Assert.InRange(sum, 0.98f, 1.02f);
            // steel first: at the head the core is the widest band; the amber is a lane of its own (never a hairline)
            Assert.True(core > mid && core > edge && edge >= 0.12f, $"grip.{w}: the core is not the widest band, or the amber is a hairline");
            // each band's end is a staircase, the tail is fingers: the longest at least twice the shortest whatever the jitter
            Assert.True(mids.Count >= 3, $"grip.{w}: the bands' ends are not steps");
            Assert.True(longest - jit >= 2 * (shortest + jit), $"grip.{w}: the fingers are too even");
            gold[w] = mid;
            // a comma, not the whole blade's fin
            Assert.InRange(p[$"grip.{w}.head"], 0.3f, 0.75f);
            Assert.InRange(p[$"grip.{w}.taper"], 0.5f, 1f);
            // (lead 7) the contact: one chisel of paint on the blade, never a line (10 px wide or more on one body, 3 to
            // 5 times as long) and, at its largest (a kill), shorter than the stroke's head is wide (a 1.2 m blade)
            float fl = p[$"grip.{w}.flash"];
            float len = (kite[0] + kite[1]) * fl, wide = 2 * kite[2] * fl;
            Assert.True(wide >= 0.115f && len >= 3 * wide && len <= 5 * wide, $"grip.{w}: the mark is a line or a blob");
            Assert.True(len * p["grip.contact.kill"] < p[$"grip.{w}.head"] * 1.2f, $"grip.{w}: the mark outgrows the stroke's head");
            // its chips: short and hard, each smaller than half the mark
            var sh = p.All("grip.contact.shards");
            Assert.True(sh[1] <= 0.5f * (kite[0] + kite[1]) && sh[0] >= 0.08f && sh[2] >= 0.035f && sh[3] <= kite[2] * 1.2f, $"grip.{w}: the chips are not short hard chips");
        }
        Assert.True(kite[0] > 2 * kite[1], "the mark points along the travel");
        // by night the mark is not the brightest thing: its white is under half of it
        Assert.InRange(kite[3], 0.2f, 0.5f);
        // no crown: at most two chips, on the travel, thrown on
        Assert.True(p.All("grip.contact.tears")[1] <= 2 && p["grip.contact.fan"] <= 12 && p["grip.contact.fly"] >= 2 && p["grip.contact.full_frames"] >= 3);
        // a band's end: a long flat slant (two lane widths or more), the skip's a short one; the white leaves as fingers
        var tg = p.All("grip.lane.tongue");
        Assert.True(tg.Length == 2 && tg[0] >= 0.2f && tg[0] <= 0.45f && tg[1] <= 0.15f, "grip.lane.tongue");
        Assert.InRange(p["grip.lane.last"], 0.6f, 1f);
        // the Oathblade's is the thinner stroke, its gold about a sixth of its width
        Assert.True(p["grip.oath.head"] < p["grip.sunder.head"]);
        Assert.InRange(gold["oath"], 0.12f, 0.2f);
        // the link's thread: a brush tail, not a hairline; its point capped by a share of a short stroke
        Assert.InRange(p["grip.tail_px"], 2.5f, 6);
        Assert.InRange(p.All("grip.point")[1], 0.1f, 0.5f);
        // gone 0.15 s after the contact
        Assert.Equal(1.0, (double)p.Curve("grip.retract", 0.15f), 3);
    }
}
