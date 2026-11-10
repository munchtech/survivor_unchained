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

    /// <summary>(P7 take 7) The held cut's stroke is ONE brush stroke laid by the sword: its numbers are there and the
    /// dead takes' are gone; the head is a brush cap ahead of the blade (convex nose, concave inner edge: a fang; the
    /// blade's line is never its edge); its white is its own, by day and by night.</summary>
    [Fact]
    public void TheHeldCutsStrokeIsABrushStrokeWithACap()
    {
        var p = Real();
        foreach (var k in new[] { "grip.lead_frames", "grip.slow", "grip.snap", "grip.min_len", "grip.face", "grip.point", "grip.retract", "grip.shed_at", "grip.shed_to",
            "grip.kink", "grip.kink_run", "grip.link.on", "grip.contact.wait_frames", "grip.contact.k_min", "grip.contact.kill", "grip.contact.by_struck", "grip.contact.grit",
            "grip.press.rise", "grip.press.lift", "grip.press.contact", "grip.press.hold", "grip.press.white", "grip.cap", "grip.cap_rag",
            "grip.fill.lanes", "grip.fill.share", "grip.fill.values_day", "grip.fill.values_night", "grip.fill.gold", "grip.fill.press", "grip.dry_tail", "grip.press.loaded",
            "grip.throw.fly", "grip.throw.dash", "grip.throw.dash_m", "grip.throw.bend", "grip.throw.span", "grip.fill.streak", "grip.fill.tine", "grip.fill.cut", "grip.fill.comb", "grip.fill.dry", "grip.dry_out", "grip.shed_white",
            "grip.splay.out", "grip.splay.tines", "grip.splay.len", "grip.splay.root", "grip.splay.slant", "grip.splay.frames",
            "grip.throw.per_struck", "grip.throw.most", "grip.throw.px", "grip.throw.len", "grip.throw.min", "grip.throw.slant", "grip.throw.frames", "grip.throw.color",
            "grip.white.day", "grip.white.night", "grip.sunder.head", "grip.sunder.max_len", "grip.sunder.flash", "grip.oath.head", "grip.oath.max_len", "grip.oath.flash" })
            Assert.True(p.Has(k), "fx_language.json p7 lacks " + k);
        foreach (var k in new[] { "grip.min_seen", "grip.aspect", "grip.lit", "grip.glow", "grip.short", "grip.band.clumps", "grip.lane.tail", "grip.shed_rim", "grip.shed_push",
            "grip.contact.swell", "grip.contact.white", "grip.contact.frames", "grip.contact.flood", "grip.sunder.core", "grip.sunder.streaks", "grip.oath.taper", "grip.fill.tone", "grip.dry", "grip.waver" })
            Assert.False(p.Has(k), k + ": a dead take's key");
        // the cap: half to the whole of the stroke's width long; convex to its nose near the tip's path; from the nose the
        // leading edge falls back, concave, to BEHIND the blade's line at the inner edge (it crosses the line once)
        var cap = p.All("grip.cap");
        Assert.Equal(6, cap.Length);
        Assert.InRange(cap[0], 0.5f, 1f);
        Assert.InRange(cap[1], 0.1f, 0.45f);
        Assert.InRange(cap[4], 0.3f, 0.9f);
        Assert.Equal(cap[0], GripPaint.CapFront(cap[1], cap), 1e-4f);
        Assert.InRange(GripPaint.CapFront(0, cap), 0.25f * cap[0], 0.9f * cap[0]);
        Assert.True(GripPaint.CapFront(0.5f * cap[1], cap) > 0.5f * (GripPaint.CapFront(0, cap) + cap[0]), "the nose is convex");
        Assert.Equal(-cap[2], GripPaint.CapFront(1, cap), 1e-4f);
        Assert.True(cap[2] >= 0.3f, "the inner edge starts well behind the blade's line");
        float was = cap[0];
        int crossings = 0;
        for (int i = 1; i <= 40; i++)
        {
            float a = cap[1] + (1 - cap[1]) * i / 40f, f = GripPaint.CapFront(a, cap);
            Assert.True(f < was, "the leading edge falls from the nose to the inner edge");
            if (was > 0 && f <= 0) crossings++;
            float chord = cap[0] + (-cap[2] - cap[0]) * i / 40f;
            if (i < 40) Assert.True(f < chord, "the inner edge behind the cap is concave");
            was = f;
        }
        Assert.Equal(1, crossings);
        // leaving: the inner edge retreats (the head closes to a point), never a squared cut
        Assert.True(GripPaint.CapFront(1, cap, 1) < GripPaint.CapFront(1, cap) - 0.5f);
        var rag = p.All("grip.cap_rag");
        Assert.True(rag.Length == 3 && rag[0] >= 3 && rag[0] <= 8 && rag[1] >= 0.015f && rag[1] <= 0.06f, "grip.cap_rag: bristle tips, a few px of variation");
        // the fill: 2-3 close values, the colors' ends tines along the sweep, dry gaps over the last three frames
        foreach (var vk in new[] { "grip.fill.values_day", "grip.fill.values_night" })
        {
            var v = p.All(vk);
            Assert.True(v.Length == 6 && v[1] <= 0.95f && v[4] <= v[1] - 0.05f && v[4] >= 0.7f && v[2] <= 0.9f && v[5] < v[2], vk + ": three values far enough apart to read at 1:1, none dark");
        }
        Assert.InRange(p["grip.fill.lanes"], 6f, 12f);
        Assert.InRange(p.All("grip.fill.gold")[0], 0.15f, 0.3f);
        Assert.True(p.Curve("grip.dry_tail", 0.1f) > 0.1f && p.Curve("grip.dry_tail", 0.1f) < 0.4f, "grip.dry_tail: a few dry gaps in the tail half before the last three frames");
        Assert.True(p.All("grip.fill.tine")[0] >= 0.15f, "grip.fill.tine: the colors interleave");
        float end = 0;
        while (p.Curve("grip.retract", end) < 0.999f && end < 1) end += 1 / 240f;
        Assert.Equal(0f, p.Curve("grip.dry_out", end - 3.5f / 60), 1e-3f);
        Assert.InRange(p.Curve("grip.dry_out", end), 0.5f, 0.75f);
        // its own white, by day and by night
        float[] day = p.All("grip.white.day"), night = p.All("grip.white.night");
        Assert.True(day.Length == 3 && night.Length == 3 && night[1] >= 0.94f && night[2] >= 0.8f, "grip.white: by night whiter than the ring's cream core (sRGB blue 0.59)");
    }

    /// <summary>(P7 take 7) THE PRESS IS LAID, NOT CARRIED: a rib stores its press when it is laid (the brush lands, is
    /// whole, lifts as the blade slows); the contact presses the ribs round the crossing once, where they lie; the thick
    /// section stays there while the head moves on, and only settles with its own age. The tines and the thrown streaks
    /// follow the cut's distinct struck: none for an air cut, a handful for a crowd.</summary>
    [Fact]
    public void TheHeldCutsPressStaysWhereItWasLaid()
    {
        var p = Real();
        var press = new GripPaint.Press(p.All("grip.press.rise"), p.All("grip.press.lift"), p.All("grip.press.contact"), p["grip.press.white"]);
        var hold = p.All("grip.press.hold");
        float fast = press.Lift[1] + 5;
        Assert.Equal(press.Rise[2], GripPaint.Base(0, fast, press), 1e-4f);
        Assert.Equal(1f, GripPaint.Base(press.Rise[0], fast, press), 1e-4f);
        Assert.True(GripPaint.Base(press.Rise[0], press.Lift[0], press) < 0.7f, "the brush lifts as the blade slows");
        Assert.True(hold.Length >= 4 && hold[0] == 1 && hold[1] == 1 && hold[2] == 1 && hold[^1] >= 0.4f && hold[^1] < 1, "grip.press.hold: whole for three drawn frames, then settling, never gone");
        for (int i = 1; i < hold.Length; i++) Assert.True(hold[i] <= hold[i - 1], "a rib's press only thins with its age");
        var ribs = new System.Collections.Generic.List<GripPaint.Rib>();
        var none = new GripPaint.Stamp();
        for (int i = 0; i < 40; i++) GripPaint.Lay(ribs, i / 600.0, 0.05f, 0.05f, fast, 10, press, none);
        var stamp = GripPaint.Strike(ribs, 1.9f, 2f, 10, press);
        int Fattest(int frame) { int b = 0; for (int i = 1; i < ribs.Count; i++) if (GripPaint.At(ribs, ribs[i].At, frame, hold).Press > GripPaint.At(ribs, ribs[b].At, frame, hold).Press) b = i; return b; }
        int at0 = Fattest(10);
        Assert.Equal(1.9f, ribs[at0].S, 0.05f);
        float peak = GripPaint.At(ribs, ribs[at0].At, 10, hold).Press;
        Assert.True(peak > 1.3f && peak <= 1.4f, "the contact raises the press, at most about 1.4x its neighbours");
        // the head moves on (40 more ribs over the next frames, the last ones slow): the thick section has not moved
        for (int i = 40; i < 80; i++) GripPaint.Lay(ribs, i / 600.0, 0.05f, 0.05f, i < 70 ? fast : press.Lift[0], 11 + (i - 40) / 14, press, stamp);
        Assert.Equal(at0, Fattest(12));
        Assert.Equal(peak, GripPaint.At(ribs, ribs[at0].At, 12, hold).Press, 1e-4f);
        Assert.Equal(at0, Fattest(30));
        Assert.True(GripPaint.At(ribs, ribs[at0].At, 30, hold).Press < peak, "it settles with its age");
        // a rib laid after the contact inside its reach is laid pressed; past the reach it is not; both ends are thin
        Assert.True(ribs[42].Raise > 0 && ribs[^1].Raise == 0);
        Assert.True(ribs[0].Base >= 0.5f && ribs[0].Base < 0.8f && ribs[^1].Base < 0.7f && ribs[20].Base > 0.8f, "laid loaded at the start (a comma: the tail's point is the shader's), lifted at the end");
        Assert.True(ribs[0].White == 0 && ribs[at0].White > 1, "the tail is laid amber, the contact white");
        // the splay and the throw, by the cut's DISTINCT struck
        var tn = p.All("grip.splay.tines");
        float crowd = p.All("grip.contact.by_struck")[0], per = p["grip.throw.per_struck"], most = p["grip.throw.most"];
        Assert.Equal(0, GripPaint.Tines(0, tn, crowd));
        Assert.Equal(0, GripPaint.Streaks(0, per, most));
        Assert.Equal((int)tn[0], GripPaint.Tines(1, tn, crowd));
        Assert.Equal((int)tn[1], GripPaint.Tines(40, tn, crowd));
        Assert.Equal(1, GripPaint.Streaks(1, per, most));
        Assert.InRange(GripPaint.Streaks(40, per, most), 4, 7);
        Assert.True(GripPaint.Tines(40, tn, crowd) + GripPaint.Streaks(40, per, most) <= 12, "the shader carries 12 spikes");
        Assert.InRange(p.All("grip.throw.frames").Length, 2, 3);
        var sp = GripPaint.Spikes(stamp, 5, 6, press, p.All("grip.splay.len"), p.All("grip.splay.root"), p.All("grip.splay.slant"), 0.03f, p.All("grip.throw.len"), p.All("grip.throw.slant"), 2.5f, 7f, 1f, 1f, p["grip.throw.span"]);
        Assert.Equal(44, sp.Length);
        for (int i = 0; i < 11; i++)
        {
            float sr = i < 5 ? 1f : p["grip.throw.span"];
            Assert.InRange(sp[i * 4], stamp.S - sr * press.Contact[2], stamp.S + sr * press.Contact[1]);
            Assert.True(sp[i * 4 + 1] <= 3f, "a spike's root is hair-thin (pixels)");
            Assert.True(sp[i * 4 + 1] > 0 && sp[i * 4 + 2] > 0);
            if (i < 5) Assert.True(sp[i * 4 + 2] <= 0.3f, "a tine is short"); else Assert.InRange(sp[i * 4 + 2], 0.9f, 2.5f);
        }
    }

    /// <summary>(take 8, F0) Every literal p7 grip key the held cut's view reads is in the data (a renamed key threw once
    /// a run, and the warm-up after it never ran).</summary>
    [Fact]
    public void EveryGripKeyTheViewReadsIsThere()
    {
        var p = Real();
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        Assert.NotNull(d);
        string src = File.ReadAllText(Path.Combine(d!.FullName, "src", "Fx", "BattleFx.Grip.cs"));
        int n = 0;
        foreach (System.Text.RegularExpressions.Match m in System.Text.RegularExpressions.Regex.Matches(src, "\"(grip\\.[a-z0-9_.]*[a-z0-9_])\""))
        {
            n++;
            Assert.True(p.Has(m.Groups[1].Value), "BattleFx.Grip.cs reads " + m.Groups[1].Value + ": not in fx_language.json p7");
        }
        Assert.True(n > 40, "the scan found the view's keys");
    }

    /// <summary>A band's end at `a` across the width (knots [across, share of the length], straight between).</summary>
    static float At(float[] k, float a)
    {
        for (int i = 2; i < k.Length; i += 2)
            if (a <= k[i]) return k[i - 1] + (k[i + 1] - k[i - 1]) * (a - k[i - 2]) / (k[i] - k[i - 2]);
        return k[^1];
    }
}
