using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Look;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 B4) The lighting rigs as data: godot/data/look/rigs.json read whole, every rig named FROM something, the
/// presets lit by their rig under cel and left as they are without one.</summary>
public class RigsTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }
    static RigSet Real() => RigSet.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "rigs.json")));

    [Fact]
    public void EveryRigTheBriefNamesIsThereAndSaysWhatItIsFrom()
    {
        var s = Real();
        foreach (var id in new[] { "night_play", "night_town", "day_town", "day_wild", "dawn", "arena_night", "close_night", "close_day", "look" })
            Assert.NotNull(s[id]);
        Assert.All(s.Rigs.Values, r => Assert.False(string.IsNullOrWhiteSpace(r.From)));
        Assert.True(s["close_day"]!.Camera && !s["night_play"]!.Camera);
        // rule 8's ink rig: night (0.42, 0.45, 0.85), day (0.85, 0.6, 0.5)
        Assert.Equal(new[] { 0.42, 0.45, 0.85 }, s["night_town"]!.Ink);
        Assert.Equal(new[] { 0.85, 0.6, 0.5 }, s["day_wild"]!.Ink);
    }

    [Fact]
    public void ABaseIsInheritedAndANullLeavesThePresetItsOwn()
    {
        var s = Real();
        Assert.Equal(s["night_play"]!.Fill.Color, s["night_town"]!.Fill.Color);
        Assert.Null(s["arena_night"]!.Key.Az);
        var place = Atmospheres.Night with { KeyAzimuth = 200, KeyIntensity = 4.7, Rig = "arena_night" };
        var lit = Rigs.Lit(place, s);
        Assert.Equal(200, lit.KeyAzimuth);
        Assert.Equal(s["arena_night"]!.Key.Intensity!.Value * (s["arena_night"]!.Key.Scale ?? 1), lit.KeyIntensity, 9);   // (L1 lead 11, R2: the rig's level, absolute; the place's moon keeps its way)
        Assert.Equal(s["night_play"]!.Rim.Strength, lit.CelRim);
    }

    /// <summary>(L1 lead 11, R2) Levels are the rig's, absolute: under the arena's night rig no place and no mood scales the
    /// moon's key, the sky's light, the environment's or the exposure (the 'moonless' mood cut the Deep Shaw's key x0.55 and
    /// its sky x0.7); a place keeps its moon's way (azimuth, elevation) and a mood its air.</summary>
    [Fact]
    public void NoPlaceAndNoMoodScalesTheArenaNightsLevels()
    {
        var s = Real();
        var rig = s["arena_night"]!;
        Assert.NotNull(rig.Key.Intensity); Assert.NotNull(rig.Fill.Hemi); Assert.NotNull(rig.Fill.Env); Assert.NotNull(rig.Exposure);
        Assert.Null(rig.Fill.SkyScale);   // (a level on the place's own sky light: retired)
        Assert.Equal(1, rig.Key.Scale ?? 1);
        var moods = SurvivorUnchained.Maps.ArenaPlaces.Moods.Select(m => m.Mood).Append("").Append("blight").Append("a mood not written yet").Distinct().ToList();
        Assert.Contains("moonless", moods);
        var ways = new System.Collections.Generic.HashSet<(double, double)>();
        foreach (var people in new[] { "dead", "pack", "kerchiefs", "lamplings" })
            foreach (var mood in moods)
            {
                var place = SurvivorUnchained.Maps.ArenaPlaces.For(new SurvivorUnchained.Maps.MapSpec { Arena = true, People = people, Mood = mood, Theme = mood == "blight" ? "blight" : "" });
                Assert.Equal("arena_night", place.Night.Rig);
                var lit = Rigs.Lit(place.Night, s);
                Assert.Equal(rig.Key.Intensity!.Value, lit.KeyIntensity, 12);
                Assert.Equal(rig.Fill.Hemi!.Value, lit.HemiIntensity, 12);
                Assert.Equal(rig.Fill.Env!.Value, lit.EnvIntensity, 12);
                Assert.Equal(rig.Exposure!.Value, lit.Exposure, 12);
                Assert.Equal(rig.Key.Shadow!.Value, lit.ShadowStrength, 12);
                Assert.Equal(rig.Key.Color, lit.KeyColor);
                // the place keeps its moon's way
                Assert.Equal(place.Night.KeyAzimuth, lit.KeyAzimuth); Assert.Equal(place.Night.KeyElevation, lit.KeyElevation);
                ways.Add((lit.KeyAzimuth, lit.KeyElevation));
            }
        Assert.Equal(4, ways.Count);
        // a mood keeps its air: the moonless night's mist is thicker than the still one's
        var still = SurvivorUnchained.Maps.ArenaPlaces.For(new SurvivorUnchained.Maps.MapSpec { Arena = true, People = "pack", Mood = "still" });
        var dark = SurvivorUnchained.Maps.ArenaPlaces.For(new SurvivorUnchained.Maps.MapSpec { Arena = true, People = "pack", Mood = "moonless" });
        Assert.True(dark.Air.MistDensity > still.Air.MistDensity);
    }

    /// <summary>(L1 lead 11, R3 one shade) A rig whose shadow is a level ("shadow_level") has one shade number: key.shadow,
    /// and the canopy's dapple lands on it (its data agrees and Lit derives it). No day or dawn rig opts in (their shadow
    /// values were tuned on the old switch, and their look must not change).</summary>
    [Fact]
    public void AShadowLevelRigHasOneShadeAndTheDayRigsKeepTheSwitch()
    {
        var s = Real();
        Assert.True(s["arena_night"]!.OneShade);
        foreach (var r in s.Rigs.Values)
        {
            if (r.Id.StartsWith("day") || r.Id.StartsWith("dawn") || r.Camera) Assert.False(r.OneShade, r.Id);
            if (!r.OneShade) continue;
            Assert.NotNull(r.Key.Shadow);
            if (r.Dapple.Strength is { } ds) Assert.Equal(r.Key.Shadow!.Value, ds, 9);
        }
        var place = SurvivorUnchained.Maps.ArenaPlaces.For(new SurvivorUnchained.Maps.MapSpec { Arena = true, People = "pack" });
        var lit = Rigs.Lit(place.Night, s);
        Assert.True(lit.ShadowLevel);
        Assert.Equal(lit.ShadowStrength, lit.DappleStrength, 12);
        Assert.False(Rigs.Lit(Atmospheres.WaystationDay, s).ShadowLevel);
        Assert.False(Rigs.Lit(Atmospheres.LowFordNight, s).ShadowLevel);   // (night_play: not solved at its frames yet)
    }

    [Fact]
    public void TheDaysFiresAreAGlowAndTheNightsBurnWhole()
    {
        var s = Real();
        Assert.True(s["day_town"]!.FireShare < 0.5);
        Assert.Equal(s["day_town"]!.FireShare, s["day_wild"]!.FireShare);
        Assert.Equal(1, s["night_play"]!.FireShare);
        Assert.Equal(s["day_town"]!.Fill.Sky, s["day_wild"]!.Fill.Sky);   // (one day fill: the sky's hue too)
    }

    [Fact]
    public void LitTakesTheRigsNumbersOnceAndLeavesAnUnriggedPreset()
    {
        var s = Real();
        var lit = Rigs.Lit(Atmospheres.WaystationDay, s);
        Assert.True(lit.IsLit);
        Assert.Same(Atmospheres.WaystationDay, lit.Source);
        Assert.Equal(s["day_town"]!.Key.Color, lit.KeyColor);
        Assert.Equal(s["day_town"]!.Fill.Strength, lit.CelFill);
        Assert.Equal(lit, Rigs.Lit(lit, s));
        Assert.Same(Atmospheres.Front, Rigs.Lit(Atmospheres.Front, s));
        Assert.Same(Atmospheres.Dusk, Rigs.Lit(Atmospheres.Dusk, s));
    }

    [Fact]
    public void ABlendIsLitAsTheBlendOfItsRigs()
    {
        var s = Real(); var was = Rigs.Current; Rigs.Current = s;
        try
        {
            var b = Atmospheres.Blend(Atmospheres.LowFordNight, Atmospheres.LowFordDawn, 0.25);
            Assert.NotNull(b.CelTwin);
            var lit = Rigs.Lit(b);
            var want = Atmospheres.Blend(Rigs.Lit(Atmospheres.LowFordNight), Rigs.Lit(Atmospheres.LowFordDawn), 0.25);
            Assert.Equal(want.CelFill, lit.CelFill, 9);
            Assert.Equal(want.KeyColor, lit.KeyColor);
            // the dawning keeps its own key fade on the lit side
            var d = Atmospheres.Dawning(0.5);
            Assert.Equal(0, Rigs.Lit(d).KeyIntensity, 9);
            Assert.True(Rigs.Lit(Atmospheres.Morning(0.5)).IsLit);
        }
        finally { Rigs.Current = was; }
    }

    [Fact]
    public void TheCanopyMaskStandsWhereTheTreesAre()
    {
        var s = Real();
        var m = Rigs.CanopyMask(new[] { (0.0, 0.0, "broadleaf", 1.0), (20.0, 20.0, "fern", 1.0) }, s, 64, 128);
        int At(double x, double z) => m[(int)((z + 32) / 0.5) * 128 + (int)((x + 32) / 0.5)];
        Assert.True(At(0, 0) > 200);
        Assert.Equal(0, At(20, 20));
        Assert.Equal(0, At(-20, 10));
        var (r, u, b) = Rigs.CameraKey(35, 40);
        Assert.True(r > 0 && u > 0 && b > 0);
        Assert.Equal(1, r * r + u * u + b * b, 9);
    }

    /// <summary>(B4r3) By day and at dawn the zones' fires and lamps take the rig's share (rule 3); the night rigs keep
    /// theirs whole; the Look by day has a fill of its own; every grade a rig names exists.</summary>
    [Fact]
    public void FiresShareByDayAndDawnOnly()
    {
        var s = Real();
        Assert.Equal(0.2, s["day_town"]!.FireShare, 6);
        Assert.Equal(0.2, s["day_wild"]!.FireShare, 6);
        Assert.Equal(0.5, s["dawn_waystation"]!.FireShare, 6);
        foreach (var id in new[] { "night_play", "night_town", "night_wild", "arena_night" }) Assert.Equal(1, s[id]!.FireShare, 6);
        Assert.NotNull(s["look_day"]!.Fill.Color);
        foreach (var r in s.Rigs.Values) if (r.Grade is string g) Assert.NotNull(SurvivorUnchained.World.Atmospheres.GradeNamed(g));
    }
    [Fact]
    public void TheTitleIsLitByTheNightRigAndACinematicNightKeepsItsShotsKey()
    {
        // (L1 lead 9, night: the title on the game's night rig, the Look keeping Front; C01's night keeps the cue's moon)
        var s = Real();
        var t = Rigs.Lit(Atmospheres.Title, s);
        Assert.True(t.IsLit);
        Assert.Equal(s["night_play"]!.Key.Color, t.KeyColor);
        Assert.Equal(Atmospheres.Title.KeyAzimuth, t.KeyAzimuth);
        Assert.Same(Atmospheres.Front, Rigs.Lit(Atmospheres.Front, s));
        var shot = Atmospheres.CineNight with { KeyIntensity = 2.38, KeyAzimuth = 250, KeyElevation = 25, Exposure = 0.66 };
        var c = Rigs.Lit(shot, s);
        Assert.Equal(2.38, c.KeyIntensity, 6);
        Assert.Equal(250, c.KeyAzimuth, 6);
        Assert.Equal(0.66, c.Exposure, 6);
        Assert.Equal(s["night_play"]!.Fill.Color, c.CelFillColor);
    }

    // (L1 lead 12, R4 rounds 4-5) Her fire as a field is arena_night's alone. A rig that names none of its keys (ember_smooth,
    // ember_shade, dapple mass/clusters/leaf/leaves; ember_break and ember_brush are retired) hands the air what it did before
    // them: the ramp linear between its stops, cel_pool_shade zero (no opening over her, no leaf cut, the moon's return under a
    // leaf untouched: every round 4-5 shader term sits behind it), the cookie's fans on their first random run, its own give
    // and pool to the number.
    [Fact]
    public void HerFireAsAFieldIsArenaNightsAlone()
    {
        var s = Real();
        foreach (var (id, r) in s.Rigs)
        {
            if (id == "arena_night") continue;
            Assert.True(r.EmberSmooth != true, id);
            Assert.True(r.EmberShade == null, id);
            Assert.True(r.EmberFloor == null, id);   // (L1 l17 p) the floor's tone table is arena_night's alone
            Assert.True(r.HeroPool == null, id);   // (L1 l19 her2) the hero-in-a-pool rule is arena_night's alone: every other rig renders as before
            Assert.True(r.Dapple.Mass == null && r.Dapple.Clusters == null && r.Dapple.Leaf == null && r.Dapple.Leaves == null, id);
        }
        foreach (var place in new[] { Atmospheres.LowFordNight, Atmospheres.WaystationDay })
        {
            var lit = Rigs.Lit(place, s);
            Assert.False(lit.EmberSmooth);
            Assert.Null(lit.EmberShade); Assert.Null(lit.EmberFloor); Assert.Null(lit.HeroPool);
            Assert.Null(lit.DappleMass);
            Assert.Null(lit.DappleLeaf);
            Assert.Null(lit.DappleLeaves);
            Assert.Equal(0.0, (double)lit.DappleClusters);
        }
        var night = Rigs.Lit(Atmospheres.LowFordNight, s);
        Assert.Equal(new[] { 1.0, 0.9, 1.5, 3.25 }, night.EmberGive);
        Assert.Equal(57, night.EmberPool!.Length);
        Assert.Equal(new[] { 1.0, 0.3, 0, 0.54, 255, 136, 6 }, night.EmberPool[..7]);
        Assert.Equal(new[] { 3.4, 0, 170, 130, 180 }, night.EmberPool[^5..]);
        // and the field itself, as written (round 5)
        var a = s["arena_night"]!;
        Assert.True(a.EmberSmooth);
        Assert.Equal(new[] { 1, 1.4, 5.0, 1 }, a.EmberShade);   // (L1 l16 d3) a leaf takes all of her fire (no pink leaf patches); the canopy opens 1.4-5.0 m, read at each leaf cluster's center (CanopyField)
        Assert.Equal(0, (a.EmberFloor!.Length - 9) % 8); Assert.Equal(1.0, a.EmberFloor[^7]);   // (L1 l17 p) her fire on the floor: 9 heads, stops of 8, the moon whole at the last
        // (L1 l19 her2) the hero in her pool: 10 values; the fire's foot BESIDE her and off her feet (at least 0.5 m away), the anchor dark and WARM (red over blue), never black
        var hp4 = a.HeroPool!; Assert.Equal(27, hp4.Length); Assert.True(hp4[6] >= 0.5 && hp4[24] < hp4[6] && hp4[20] > 2 * hp4[2] && hp4[15] > 2 * hp4[20] && hp4[21] > hp4[23] && hp4[14] > 0 && hp4[25] >= 0 && hp4[25] <= 0.6 && hp4[26] >= 0 && hp4[26] <= 0.4);   /* (L1 l20 her4) a LIGHT figure: the anchor a narrow accent (its side edge well past the mid's), a warm mid step between the anchor and the light, the held piece's away edge in m, a material's own hue and value as shares */ Assert.True(a.HeroPool[10] > a.HeroPool[2] && a.HeroPool[15] > 3 * a.HeroPool[10] && a.HeroPool[11] > a.HeroPool[13] && a.HeroPool[16] > a.HeroPool[18] && a.HeroPool[19] >= 1);   /* (L1 l19 her3) her held pieces: a body one step over the anchor, one warm light well over it, a least width */ Assert.True(Math.Sqrt(a.HeroPool[0] * a.HeroPool[0] + a.HeroPool[1] * a.HeroPool[1]) >= 0.5);
        Assert.True(a.HeroPool[2] > 0 && a.HeroPool[3] > a.HeroPool[5] && a.HeroPool[5] > 0);
        Assert.Equal(new[] { 1, 0.9, 2.4, 5.4 }, a.EmberGive);   // (L1 l16 d3 round 2: the moon returns later under her fire, 2.4-5.4 m)
        // (L1 lead 14, D2; l15 d round 2) the canopy as a field: lit fields 1.4-4.2 m, run 0, lit share 0.5, at the field's own cover; no clusters
        Assert.Equal(new[] { 3, 5, 100, 0.48 }, a.Dapple.Mass);
        Assert.Null(a.Dapple.Clusters);
        Assert.Equal(0.5, (double)a.Dapple.Cover!, 6);
    }

    // (L1 lead 12, S3) What stands in the night's light is arena_night's alone: the moon's top band and rim (moon_top), the
    // foes on the ground's fire ramp (foe_fire), their night paint and own shadow (foe_moon). No other rig carries the keys,
    // so cel_s3, crowd_fire, crowd_moon and crowd_shade stay zero under them and every shader term behind those draws nothing.
    [Fact]
    public void WhatStandsIsArenaNightsAlone()
    {
        var s = Real();
        foreach (var (id, r) in s.Rigs)
        {
            if (id == "arena_night") continue;
            Assert.True(r.MoonTop == null && r.FoeFire == null && r.FoeMoon == null, id);
        }
        foreach (var place in new[] { Atmospheres.LowFordNight, Atmospheres.WaystationDay })
        {
            var lit = Rigs.Lit(place, s);
            Assert.Null(lit.MoonTop);
            Assert.Null(lit.FoeFire);
            Assert.Null(lit.FoeMoon);
        }
        var a = s["arena_night"]!;
        Assert.Equal(new[] { 0.32, 60, 175, 235, 0.84, 0.5, 1.5, 0.15 }, a.MoonTop);
        Assert.Equal(new[] { 0.85, 0.41, 0.5, 0.4 }, a.FoeFire);
        Assert.Equal(new[] { 0.028, 1.0, 0.0342, 94, 147, 255, 0.53, 0.66 }, a.FoeMoon);
    }
}
