using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The zones as the web game exported them (tools/godot/export_zone.mjs):
/// they load, their colliders come back with their ids, and what the runtime
/// reaches for is there.</summary>
public class ZoneTests
{
    public static readonly TheoryData<string> Ids = new() { "lowford", "waystation", "verge" };

    [Theory]
    [MemberData(nameof(Ids))]
    public void A_zone_loads_whole(string id)
    {
        var z = ZoneMeta.Load(id);
        Assert.Equal(id, z.Id);
        var h = Heightfield.Load(z);
        Assert.Equal(z.Res * z.Res, h.Heights.Length);
        Assert.InRange(z.Bound, 10, z.Size / 2);
        Assert.InRange(z.Start.X, -z.Bound, z.Bound);
        Assert.InRange(z.Start.Z, -z.Bound, z.Bound);
        Assert.NotEmpty(z.Lights);
        foreach (var f in z.Fires) Assert.InRange(f.Light, 0, z.Lights.Count - 1);
        foreach (var m in z.Moths) Assert.InRange(m, 0, z.Lights.Count - 1);
        // Heights are the ground's: finite, and the start is on it.
        Assert.All(h.Heights, v => Assert.True(float.IsFinite(v)));
        Assert.InRange(h.HeightAt(z.Start.X, z.Start.Z), -20, 40);
    }

    [Theory]
    [MemberData(nameof(Ids))]
    public void Colliders_come_back_with_their_ids(string id)
    {
        var z = ZoneMeta.Load(id);
        var w = z.Collision();
        var all = w.All().OrderBy(c => c.Id).ToList();
        Assert.Equal(z.Colliders.Count, all.Count);
        Assert.Equal(z.Colliders.Select(c => c.Id), all.Select(c => c.Id));
        // The start is clear to stand on.
        Assert.False(w.Blocked(z.Start.X, z.Start.Z, 0.4, includeSoft: false));
        // A new one follows on from the last.
        Assert.Equal(all[^1].Id + 1, w.AddCircle(0, 0, 1).Id);
    }

    [Fact]
    public void The_verge_brambles_are_colliders_the_runtime_can_burn()
    {
        var z = ZoneMeta.Load("verge");
        var w = z.Collision();
        var brambles = z.Refs.GetProperty("brambles").EnumerateArray().ToList();
        Assert.NotEmpty(brambles);
        foreach (var b in brambles)
        {
            int cid = b.GetProperty("collider").GetInt32();
            var c = w.All().Single(x => x.Id == cid);
            Assert.InRange(c.X - b.GetProperty("x").GetDouble(), -3, 3);
            w.Remove(cid);
        }
        Assert.Equal(z.Colliders.Count - brambles.Count, w.All().Count);
        var post = z.Refs.GetProperty("postFire").GetInt32();
        Assert.InRange(post, 0, z.Lights.Count - 1);
        Assert.Contains(z.Paths.Keys, k => k == "VROAD");
        var v = z.Place("V", "vault");
        Assert.Equal(-106, v.X);
    }

    [Fact]
    public void Lowford_has_its_pylons_and_waystation_its_doors()
    {
        var lf = ZoneMeta.Load("lowford");
        Assert.Equal(3, lf.Refs.GetProperty("pylons").GetArrayLength());
        var ws = ZoneMeta.Load("waystation");
        Assert.True(ws.Refs.GetProperty("doors").ValueKind is System.Text.Json.JsonValueKind.Array or System.Text.Json.JsonValueKind.Object);
        Assert.True(ws.Chimneys.Count > 0);
    }

    [Theory]
    [InlineData("lowford", "night")]
    [InlineData("waystation", "day")]
    [InlineData("verge", "day")]
    public void The_presets_light_from_where_the_web_games_did(string id, string preset)
    {
        // The port's presets are graded for Godot's renderer and no longer
        // match the web game's numbers, but the light still has to come from
        // where it did: the zones were laid out and their props placed under it.
        var web = ZoneMeta.Load(id).Atmosphere;
        var port = Atmospheres.ByName(preset);
        Assert.Equal(web.KeyAzimuth, port.KeyAzimuth);
        Assert.InRange(port.KeyElevation, web.KeyElevation - 4, web.KeyElevation + 4);
    }

    [Fact]
    public void Presets_blend_in_linear_light()
    {
        Assert.Equal("#ff0000", Atmospheres.Hex(1, 0, 0));
        var mid = Atmospheres.Blend(Atmospheres.Night, Atmospheres.Day, 0.5);
        // Halfway between #000000 and #ffffff in linear light is #bcbcbc.
        var a = Atmospheres.Night with { KeyColor = "#000000" };
        var b = Atmospheres.Day with { KeyColor = "#ffffff" };
        Assert.Equal("#bcbcbc", Atmospheres.Blend(a, b, 0.5).KeyColor);
        Assert.Equal((Atmospheres.Night.KeyElevation + Atmospheres.Day.KeyElevation) / 2, mid.KeyElevation);
        Assert.Equal(Json.Write(Atmospheres.Dawn), Json.Write(Atmospheres.Blend(Atmospheres.Night, Atmospheres.Dawn, 1)));
    }
}
