using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her armor's springs (her-springs): which vertices of a worn piece ride its spring bones (Play/SpringCarry),
/// her warden set's springs read from the springs file onto its index rows (Rpg/ArmorIndex.SpringsFile), and the body
/// capsules they are kept off (Play/BodyCapsules: the upper arm's pooled from its twist and share bones).</summary>
public class SpringCarryTests
{
    /// <summary>A flat plate (a welded grid of quads) hanging from `top` down `len`, `w` wide along X, at depth z.</summary>
    static (Vector3[] Pos, int[] Tris) Plate(float x, float z, float w = 0.1f, float len = 0.2f, int n = 6, float top = 1)
    {
        var pos = new List<Vector3>();
        for (int j = 0; j <= n; j++)
            for (int i = 0; i <= n; i++)
                pos.Add(new Vector3(x - w / 2 + w * i / n, top - len * j / n, z));
        var tris = new List<int>();
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                int a = j * (n + 1) + i, b = a + 1, c = a + n + 1, d = c + 1;
                tris.AddRange(new[] { a, c, b, b, c, d });
            }
        return (pos.ToArray(), tris.ToArray());
    }

    static (Vector3[] Pos, int[] Tris) Join(params (Vector3[] Pos, int[] Tris)[] parts)
    {
        var pos = new List<Vector3>(); var tris = new List<int>();
        foreach (var (p, t) in parts) { int o = pos.Count; pos.AddRange(p); tris.AddRange(t.Select(i => i + o)); }
        return (pos.ToArray(), tris.ToArray());
    }

    static SpringCarry.Seg Link(float x, float z, float reach = 0.06f, float top = 1, float len = 0.2f) =>
        new(new Vector3(x, top, z), new Vector3(x, top - len, z), reach);

    [Fact]
    public void LappetsWhoseRegionsOverlapEachGoWholeToTheirOwnLink()
    {
        // (her skirt's lappets lie 4 cm apart, an under plate between two over ones: each link's reach takes in most
        // of its neighbours, so the plate goes to the link it lies along)
        var (pos, tris) = Join(Plate(0, 0.1f), Plate(0.04f, 0.09f), Plate(0.08f, 0.1f));
        var links = new[] { Link(0, 0.1f), Link(0.04f, 0.09f), Link(0.08f, 0.1f) };
        var (link, share) = SpringCarry.Assign(pos, tris, links, SpringCarry.Rule.Island);
        int per = pos.Length / 3;
        for (int p = 0; p < 3; p++)
            Assert.All(Enumerable.Range(p * per, per), i => { Assert.Equal(p, link[i]); Assert.Equal(1f, share[i]); });
    }

    [Fact]
    public void ARivetOnAPlateRidesItAndTheBodyUnderItStays()
    {
        // (a 1 cm rivet on the plate, and a broad body panel behind it that only its middle passes through the reach)
        var rivet = Plate(0, 0.11f, 0.01f, 0.01f, 1, 0.9f);
        var body = Plate(0, 0.06f, 0.6f, 0.6f, 12, 1.2f);
        var (pos, tris) = Join(Plate(0, 0.1f), rivet, body);
        var (link, _) = SpringCarry.Assign(pos, tris, new[] { Link(0, 0.1f) }, SpringCarry.Rule.Island);
        int plate = 49, riv = rivet.Pos.Length;
        Assert.All(Enumerable.Range(0, plate + riv), i => Assert.Equal(0, link[i]));
        Assert.All(Enumerable.Range(plate + riv, body.Pos.Length), i => Assert.Equal(-1, link[i]));
    }

    [Fact]
    public void BlendRisesFromTheHeadToTheTail()
    {
        var pos = new[] { new Vector3(0, 1, 0.1f), new Vector3(0, 0.9f, 0.1f), new Vector3(0, 0.8f, 0.1f), new Vector3(0.5f, 0.9f, 0.1f) };
        var (link, share) = SpringCarry.Assign(pos, Array.Empty<int>(), new[] { Link(0, 0.1f) }, SpringCarry.Rule.Blend);
        Assert.Equal(new[] { -1, 0, 0, -1 }, link);   // (its head keeps the body's weights; one out of reach none)
        Assert.Equal(0.5, share[1], 3);
        Assert.Equal(1.0, share[2], 3);
    }

    [Fact]
    public void ApplyPutsAWholeIslandOnItsBoneAndSharesABlend()
    {
        // (two vertices of 4 influences: one carried whole, one by half; the link's bind is 7)
        var bones = new[] { 1, 2, 0, 0, 1, 2, 3, 0 };
        var w = new[] { 0.6f, 0.4f, 0, 0, 0.5f, 0.3f, 0.2f, 0 };
        int moved = SpringCarry.Apply(bones, w, 4, new[] { 0, 0 }, new[] { 1f, 0.5f }, new[] { 7 });
        Assert.Equal(2, moved);
        Assert.Equal(new[] { 7, 0, 0, 0 }, bones[..4]);
        Assert.Equal(new[] { 1f, 0, 0, 0 }, w[..4]);
        Assert.Equal(7, bones[7]);   // (into its free slot)
        Assert.Equal(0.5, w[7], 4);
        Assert.Equal(1.0, w[4..].Sum(), 4);
        Assert.Equal(0.25, w[4], 4);
    }

    [Fact]
    public void HerWardenSetTakesItsSpringsFromTheSpringsFile()
    {
        ArmorIndex.Reset();
        var ix = ArmorIndex.Shared;
        var skirt = ix.Find("warden.skirt")!;
        var pauldrons = ix.Find("warden.pauldrons")!;
        Assert.True(skirt.HasSprings && pauldrons.HasSprings);
        Assert.Equal(24, skirt.Springs!.Count);   // (12 steel lappets over 12 dark ones)
        Assert.All(skirt.Springs, s => Assert.Equal("pelvis", s.Parent));
        Assert.Equal(new[] { "trap_l", "trap_r" }, pauldrons.Springs!.Select(s => s.Parent).OrderBy(x => x));
        Assert.All(skirt.Springs.Concat(pauldrons.Springs), s => Assert.True(s.Head[1] > s.Tail[1], $"{s.Bone} hangs down from its head"));
        Assert.StartsWith("ours", skirt.SpringsSource);
        Assert.Equal("island", skirt.Carry!.Rule);
        Assert.Equal(skirt.Springs.Count, skirt.Springs.Select(s => s.Bone).Distinct().Count());
        // (the warden look's own pauldrons, armor/: a chain a side over the cap and its two lames, each link's head its parent's tail)
        var plate = ix.Find("plate_pauldrons_warden")!.Springs!;
        Assert.Equal(6, plate.Count);
        foreach (var l in plate.Where(l => l.Parent.StartsWith("spring_")))
            Assert.Equal(plate.Single(p => p.Bone == l.Parent).Tail, l.Head);
    }

    [Fact]
    public void ARowWithItsOwnSpringsKeepsThem()
    {
        var ix = ArmorIndex.Parse("""[{"id":"warden.skirt","springs":[{"bone":"rnd_0","parent":"pelvis","head":[0,1,0],"tail":[0,0.8,0]}]},{"id":"warden.top"}]""");
        int took = ix.AddSprings("""[{"id":"warden.skirt","source":"ours","springs":[{"bone":"ours_0","parent":"pelvis","head":[0,1,0],"tail":[0,0.8,0]}]},{"id":"warden.top","source":"ours","springs":[{"bone":"t","parent":"spine_03","head":[0,1.4,0],"tail":[0,1.2,0]}],"carry":{"rule":"blend","reach":0.05}}]""");
        Assert.Equal(1, took);
        Assert.Equal("rnd_0", ix.Find("warden.skirt")!.Springs![0].Bone);
        Assert.Null(ix.Find("warden.skirt")!.SpringsSource);
        Assert.Equal("t", ix.Find("warden.top")!.Springs![0].Bone);
        Assert.Equal(SpringCarry.Rule.Blend, SpringCarry.Parse(ix.Find("warden.top")!.Carry!.Rule));
        Assert.Equal(0.05, ix.Find("warden.top")!.Carry!.Reach);
        Assert.Equal(0, ArmorIndex.Parse("""[{"id":"warden.top"}]""", "gear").AddSprings("""[{"id":"warden.top","springs":[]}]"""));   // (never a built body's gear)
    }

    [Fact]
    public void TheUpperArmsCapsulePoolsItsTwistAndShareBones()
    {
        var l = BodyCapsules.Table.Single(r => r.A == "upperarm_l");
        Assert.Equal("lowerarm_l", l.B);
        Assert.Equal(new[] { "upperarm_l", "upperarm_twist_01_l", "upperarm_twist_02_l", "upperarm_twist_03_l", "upperarm_twist_04_l", "upperarm_share_l" }, l.Carry);
        Assert.Contains(BodyCapsules.Table, r => r.A == "upperarm_r" && r.Carry.Contains("upperarm_share_r"));
        Assert.All(BodyCapsules.Table.Where(r => !r.A.StartsWith("upperarm")), r => Assert.Equal(new[] { r.A }, r.Carry));   // (the rest as before)
    }

    [Fact]
    public void ACapsulesRadiusIsItsVerticesEightiethPercentile()
    {
        var d = Enumerable.Range(0, 100).Select(i => 0.04f + i * 0.0002f).Reverse().ToList();
        Assert.Equal(0.04 + 80 * 0.0002, BodyCapsules.Radius(d)!.Value, 5);
        Assert.Null(BodyCapsules.Radius(Enumerable.Repeat(0.05f, 19).ToList()));
        Assert.Equal(BodyCapsules.MinR, BodyCapsules.Radius(Enumerable.Repeat(0.001f, 40).ToList()));
        Assert.Equal(BodyCapsules.MaxR, BodyCapsules.Radius(Enumerable.Repeat(1f, 40).ToList()));
    }
}
