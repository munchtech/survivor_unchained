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
            "vow.burst.spikes", "vow.burst.px", "vow.burst.root_px", "vow.burst.frames", "vow.burst.lead_px", "vow.burst.trail_px", "vow.burst.run", "vow.burst.light_k", "vow.burst.light_frames" })
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
    }
}
