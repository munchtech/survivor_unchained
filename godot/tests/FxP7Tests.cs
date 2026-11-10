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

    /// <summary>(P7 lead 7, take 6) The held cut's stroke: a comma in three CONTINUOUS bands (each band's end one ragged
    /// line across the width: 3-4 uneven bristle clumps, never a needle per lane, never even stairs), steel first, 3-5
    /// uneven dry streaks only in the tail of a stroke long enough to carry them; (round 3) the contact is the stroke's
    /// own swell, sized by the bodies struck: no second object in any form.</summary>
    [Fact]
    public void TheHeldCutsStrokeIsACommaInThreeBands()
    {
        var p = Real();
        foreach (var k in new[] { "grip.lead_frames", "grip.slow", "grip.min_len", "grip.aspect", "grip.tail_px", "grip.point", "grip.glow", "grip.glow_end",
            "grip.lit", "grip.retract", "grip.shed_at", "grip.lane.jitter", "grip.lane.tail", "grip.lane.slant", "grip.lane.point", "grip.lane.gap", "grip.lane.shed",
            "grip.contact.wait_frames", "grip.contact.k_min", "grip.contact.kill", "grip.contact.swell", "grip.contact.reach", "grip.contact.flood", "grip.contact.frames",
            "grip.contact.grit", "grip.short", "grip.lane.carry", "grip.shed_rim", "grip.shed_push", "grip.band.back", "grip.band.clumps", "grip.band.uneven", "grip.band.depth", "grip.band.ratio",
            "grip.contact.by_struck", "grip.band.round", "grip.shed_to", "grip.snap", "grip.face", "grip.link.on" })
            Assert.True(p.Has(k), "fx_language.json p7 lacks " + k);
        Assert.Equal(3, p.All("grip.lit").Length);
        Assert.Equal(2, p.All("grip.point").Length);
        Assert.Equal(4, p.All("grip.lane.gap").Length);
        float jit = p.All("grip.lane.jitter")[1];
        var sw = p.All("grip.contact.swell");
        var by = p.All("grip.contact.by_struck");
        // the bands' ends: 3-4 BRISTLE clumps across the width, uneven in width and in depth (each step its own depth,
        // the deepest 3 times the least or more: never even stairs), now and then the longer of two; the sides run along
        // the travel (no slant: no V); a clump's end is rounded by 6 px or more at 75 px a metre (a square 3 px corner
        // read as a digital step)
        var clumps = p.All("grip.band.clumps");
        var depth = p.All("grip.band.depth");
        Assert.True(clumps.Length == 2 && clumps[0] >= 3 && clumps[1] <= 4 && clumps[0] <= clumps[1], "grip.band.clumps: 3 to 4");
        Assert.InRange(p["grip.band.uneven"], 0.4f, 0.8f);
        Assert.True(depth.Length == 2 && depth[0] >= 0.05f && depth[1] >= 3 * depth[0] && depth[1] <= 0.45f, "grip.band.depth");
        Assert.InRange(p["grip.band.ratio"], 1f, 2f);
        Assert.InRange(p["grip.band.round"], 0.08f, 0.16f);
        Assert.InRange(p["grip.band.back"], 0.15f, 0.4f);
        // a short stroke (as the camera sees it) is the comma small: a point for a tail, no streaks until it can carry
        // them, and they are whole before the shortest look's longest stroke
        var shortAt = p.All("grip.short");
        var carry = p.All("grip.lane.carry");
        Assert.True(shortAt.Length == 2 && shortAt[0] < shortAt[1] && carry.Length == 2 && carry[0] < carry[1] && carry[0] >= shortAt[0], "grip.short / grip.lane.carry");
        Assert.True(carry[1] <= Math.Min(p["grip.sunder.max_len"], p["grip.oath.max_len"]), "grip.lane.carry: the streaks never whole");
        // leaving: the gold lies along the inner edge (a third to under two thirds of the thinned width), the white runs on
        var rim = p.All("grip.shed_rim");
        var push = p.All("grip.shed_push");
        Assert.True(rim.Length == 4 && rim[0] >= 0.3f && rim[0] <= 0.6f && rim[1] > 0 && rim[1] <= 0.5f && rim[2] >= 0.05f && rim[2] + rim[3] <= 0.6f, "grip.shed_rim");
        Assert.True(push.Length == 2 && push[0] >= 0.5f && push[0] <= 1 && push[1] >= 0 && push[1] <= push[0], "grip.shed_push");
        // leaving: the stroke thins to a sliver on the tip's path (never a white fan)
        Assert.InRange(p["grip.shed_to"], 0.15f, 0.3f);
        // the tail: streaks across the outer part of the width only, over the paint's last quarter or so
        var tail = p.All("grip.lane.tail");
        Assert.True(tail.Length == 2 && tail[0] >= 0.35f && tail[0] <= 0.6f && tail[1] >= 0.2f && tail[1] <= 0.35f, "grip.lane.tail");
        Assert.InRange(p["grip.lane.slant"], 0.02f, 0.15f);
        foreach (var w in new[] { "sunder", "oath" })
        {
            Assert.False(p.Has($"grip.{w}.lanes"), $"grip.{w}.lanes: the bands are not laid by lanes");
            // each band's end is one line across the whole width, falling from the tip's path in (nested commas),
            // the three in order with room for a tooth between them; steel first: the white is the longest band
            var bands = new[] { p.All($"grip.{w}.core"), p.All($"grip.{w}.mid"), p.All($"grip.{w}.end") };
            float tooth = depth[1] / p[$"grip.{w}.max_len"];
            for (int b = 0; b < 3; b++)
            {
                var k = bands[b];
                int n = k.Length / 2;
                Assert.True(k.Length % 2 == 0 && n >= 2 && n <= 4 && k[0] == 0 && k[^2] == 1, $"grip.{w} band {b}: 2 to 4 knots from 0 to 1 across");
                for (int i = 1; i < n; i++)
                    Assert.True(k[i * 2] > k[i * 2 - 2] && k[i * 2 + 1] < k[i * 2 - 1], $"grip.{w} band {b}: not one falling line");
                // a line across, not along: the comma's slant, never a needle's (under 2 m of length per m of width; the paint's own end is the comma's hem)
                if (b < 2) Assert.True((k[1] - k[^1]) * p[$"grip.{w}.max_len"] <= 2 * p[$"grip.{w}.head"] * 1.2f, $"grip.{w} band {b}: too long a slant");
                if (b > 0)
                    foreach (float at in new[] { 0f, 0.5f, 1f })
                        Assert.True(At(k, at) - At(bands[b - 1], at) >= 0.5f * tooth, $"grip.{w} band {b}: no room under it at {at}");
            }
            Assert.True(bands[2][1] == 1 && bands[0][1] >= 0.45f && bands[0][^1] >= 0.15f, $"grip.{w}: the white is not the body");
            Assert.True(bands[0][1] > bands[1][1] - bands[0][1] && bands[0][1] > 1 - bands[1][1], $"grip.{w}: the core is not the longest band");
            // the tail: 3-5 streaks, uneven in width and in length; the outermost is the longest (the comma's point)
            var st = p.All($"grip.{w}.streaks");
            int sn = st.Length / 2;
            Assert.True(st.Length % 2 == 0 && sn >= 3 && sn <= 5, $"grip.{w}.streaks: 3 to 5");
            float sum = 0, wmin = 1, wmax = 0, kmin = 1;
            for (int i = 0; i < sn; i++)
            {
                sum += st[i * 2]; wmin = Math.Min(wmin, st[i * 2]); wmax = Math.Max(wmax, st[i * 2]); kmin = Math.Min(kmin, st[i * 2 + 1]);
                for (int o = 0; o < i; o++) Assert.True(Math.Abs(st[i * 2 + 1] - st[o * 2 + 1]) >= 0.15f, $"grip.{w}.streaks: two the same length");
            }
            Assert.InRange(sum, 0.98f, 1.02f);
            Assert.True(wmax >= 1.8f * wmin && st[1] == 1 && kmin + jit / tail[1] <= 0.5f, $"grip.{w}.streaks: too even");
            // the hem meets the tail: at the streaks' inner side the paint's own end is about the tail's start
            Assert.InRange(At(bands[2], tail[0]) - (1 - tail[1]), -0.02f, 0.08f);
            // a comma, not the whole blade's fin
            Assert.InRange(p[$"grip.{w}.head"], 0.3f, 0.75f);
            Assert.InRange(p[$"grip.{w}.taper"], 0.5f, 1f);
            // (round 3) the contact is the stroke's own swell: a fifth to a half wider for one body, under twice as wide at the cap
            Assert.InRange((sw[0] + sw[1]) * p[$"grip.{w}.flash"], 0.2f, 0.5f);
            Assert.InRange((sw[0] + sw[1]) * by[1] * p[$"grip.{w}.flash"], 0.5f, 1f);
        }
        // no second object: the mark's keys are gone; the swell is mostly inward (the tip's path stays the clean edge), a
        // local bulge (under a metre and a half end to end, longer toward the tail), 2-3 frames, stepping down
        foreach (var dead in new[] { "mark", "steps", "full_frames", "lift", "kite", "shards" }) Assert.False(p.Has("grip.contact." + dead), "grip.contact." + dead + ": the contact is in the stroke");
        var reach = p.All("grip.contact.reach");
        var frames = p.All("grip.contact.frames");
        Assert.True(sw.Length == 2 && sw[0] > sw[1] && sw[1] > 0, "grip.contact.swell");
        Assert.True(reach.Length == 2 && reach[0] > 0 && reach[0] < reach[1] && reach[0] + reach[1] <= 1.5f, "grip.contact.reach");
        Assert.True(frames.Length is >= 2 and <= 3 && frames[0] == 1 && frames[^1] > 0 && frames[^1] < frames[0], "grip.contact.frames");
        Assert.InRange(p["grip.contact.flood"], 0f, 1f);
        // sized by the bodies struck, capped at 8 to 16 of them; a kill is larger, never past the cap (GripContact clamps)
        Assert.True(by.Length == 2 && by[0] >= 8 && by[0] <= 16 && p["grip.contact.kill"] > 1 && p["grip.contact.kill"] <= by[1], "grip.contact.by_struck");
        // the Oathblade's is the thinner stroke
        Assert.True(p["grip.oath.head"] < p["grip.sunder.head"]);
        // the link's thread: a brush tail, not a hairline; its point capped by a share of a short stroke
        Assert.InRange(p["grip.tail_px"], 2.5f, 6);
        Assert.InRange(p.All("grip.point")[1], 0.1f, 0.5f);
        // gone 0.15 s after the contact
        Assert.Equal(1.0, (double)p.Curve("grip.retract", 0.15f), 3);
    }

    /// <summary>A band's end at `a` across the width (knots [across, share of the length], straight between).</summary>
    static float At(float[] k, float a)
    {
        for (int i = 2; i < k.Length; i += 2)
            if (a <= k[i]) return k[i - 1] + (k[i + 1] - k[i - 1]) * (a - k[i - 2]) / (k[i] - k[i - 2]);
        return k[^1];
    }
}
