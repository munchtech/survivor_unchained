using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Look;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P7 lead 7, main's ruling of 10 Nov) The spark budget's choice (logic/Look/HitBudget.cs, drawn by
/// src/Fx/BattleFx.cs HitSparkBudget): a source over n hits shows n, crits first (nearest her when over n), plain hits
/// nearest the middle (the blade's contact for the held cut); a source of n or fewer is left alone.</summary>
public class HitBudgetTests
{
    const int N = 4;

    static Ev.Hit Hit(double x, double z, bool crit = false, string? art = "slash_heavy", School school = School.Physical) =>
        new() { X = x, Z = z, Crit = crit, Art = art, School = school, Amount = 10, MaxHp = 100, Target = 0 };

    static (HashSet<Ev.Hit> Hushed, List<HitBudget.Tally> Tallies) Choose(IReadOnlyList<CombatEvent> events, double herX = 0, double herZ = 0,
        IReadOnlyDictionary<(string?, School), (double X, double Z)>? contacts = null, int n = N)
    {
        var hushed = new HashSet<Ev.Hit>();
        var tallies = new List<HitBudget.Tally>();
        HitBudget.Choose(events, n, herX, herZ, hushed, tallies, contacts);
        return (hushed, tallies);
    }

    [Fact]
    public void ASourceOfNHitsOrFewerHushesNothingWhateverItsCrits()
    {
        for (int count = 0; count <= N; count++)
            foreach (int crits in new[] { 0, 1, count })
            {
                var hits = Enumerable.Range(0, count).Select(i => Hit(i * 3, 0, crit: i < crits)).ToList<CombatEvent>();
                var (hushed, tallies) = Choose(hits);
                Assert.Empty(hushed);
                Assert.Empty(tallies);
            }
    }

    [Fact]
    public void OverNWithFewerCritsThanPlacesEveryCritShowsAndPlainHitsFillTheRestNearestTheMiddle()
    {
        // Ten in a row at x = 0..9 (the centroid 4.5); the two crits stand at the far ends, the furthest from the middle.
        var hits = Enumerable.Range(0, 10).Select(i => Hit(i, 0, crit: i is 0 or 9)).ToList();
        var (hushed, tallies) = Choose(hits);
        var shown = hits.Where(h => !hushed.Contains(h)).ToList();
        Assert.Equal(N, shown.Count);
        Assert.Contains(hits[0], shown);
        Assert.Contains(hits[9], shown);
        // (x = 4 and x = 5 are the two nearest 4.5)
        Assert.Contains(hits[4], shown);
        Assert.Contains(hits[5], shown);
        Assert.Equal(new HitBudget.Tally("slash_heavy", School.Physical, Struck: 10, Crits: 2, CritsShown: 2, PlainShown: 2, Hushed: 6), Assert.Single(tallies));
    }

    [Fact]
    public void MoreCritsThanPlacesShowsExactlyNAllCritsTheNNearestHer()
    {
        // She stands at x = 100: the crits nearest her are the LAST of the row, far from the row's own middle.
        var hits = new List<Ev.Hit>();
        for (int i = 0; i < 9; i++) hits.Add(Hit(i * 2, 0, crit: true));
        for (int i = 0; i < 6; i++) hits.Add(Hit(8 + i * 0.1, 1));
        var (hushed, tallies) = Choose(hits, herX: 100, herZ: 0);
        var shown = hits.Where(h => !hushed.Contains(h)).ToList();
        Assert.Equal(N, shown.Count);
        Assert.All(shown, h => Assert.True(h.Crit));
        Assert.Equal(new[] { 10.0, 12.0, 14.0, 16.0 }, shown.Select(h => h.X).OrderBy(x => x));
        // (every plain hit is hushed, and the crits past the cap with them)
        Assert.All(hits.Where(h => !h.Crit), h => Assert.Contains(h, hushed));
        Assert.Equal(new HitBudget.Tally("slash_heavy", School.Physical, Struck: 15, Crits: 9, CritsShown: 4, PlainShown: 0, Hushed: 11), Assert.Single(tallies));
    }

    [Fact]
    public void ADotABlockedOrAFlareHitIsNeverCountedOrHushed()
    {
        // Four counted hits and nine that are not: the source is not over, so nothing is hushed.
        var counted = Enumerable.Range(0, N).Select(i => Hit(i, 0)).ToList();
        var others = new List<Ev.Hit>();
        for (int i = 0; i < 3; i++)
        {
            var dot = Hit(20 + i, 0); dot.Dot = true; others.Add(dot);
            var blocked = Hit(30 + i, 0); blocked.Blocked = true; others.Add(blocked);
            var flare = Hit(40 + i, 0, crit: true); flare.ByFlare = true; others.Add(flare);
        }
        var (hushed, tallies) = Choose(counted.Concat(others).ToList());
        Assert.Empty(hushed);
        Assert.Empty(tallies);

        // Two more counted hits put the source over: only counted hits are hushed, and the centroid is theirs alone
        // (x = 0..5, the middle 2.5; the others at x = 20..42 would drag it off the row).
        counted.Add(Hit(4, 0));
        counted.Add(Hit(5, 0));
        (hushed, tallies) = Choose(others.Concat(counted).ToList());
        Assert.Equal(2, hushed.Count);
        Assert.All(others, h => Assert.DoesNotContain(h, hushed));
        Assert.Equal(new[] { 0.0, 5.0 }, hushed.Select(h => h.X).OrderBy(x => x));
        Assert.Equal(6, Assert.Single(tallies).Struck);
        Assert.All(others, h => Assert.False(HitBudget.Counts(h)));
    }

    [Fact]
    public void TwoSourcesInOneFrameAreBudgetedApart()
    {
        // Three of one art and three of another, then three of the first art in another school: nine hits, no source over.
        var a = Enumerable.Range(0, 3).Select(i => Hit(i, 0, art: "slash_heavy")).ToList();
        var c = Enumerable.Range(0, 3).Select(i => Hit(i, 1, art: "watch_bell")).ToList();
        var s = Enumerable.Range(0, 3).Select(i => Hit(i, 2, art: "slash_heavy", school: School.Fire)).ToList();
        var (hushed, tallies) = Choose(a.Concat(c).Concat(s).ToList());
        Assert.Empty(hushed);
        Assert.Empty(tallies);

        // One source over (seven, woven through the other's hits) and one under (two): only the first is cut, to n.
        var big = Enumerable.Range(0, 7).Select(i => Hit(i, 0, art: "slash_heavy")).ToList();
        var small = Enumerable.Range(0, 2).Select(i => Hit(50 + i, 0, art: null)).ToList();
        var frame = new List<Ev.Hit> { big[0], small[0], big[1], big[2], big[3], small[1], big[4], big[5], big[6] };
        (hushed, tallies) = Choose(frame);
        Assert.Equal(3, hushed.Count);
        Assert.All(small, h => Assert.DoesNotContain(h, hushed));
        Assert.Equal(N, big.Count(h => !hushed.Contains(h)));
        var t = Assert.Single(tallies);
        Assert.Equal(("slash_heavy", 7, 3), (t.Art, t.Struck, t.Hushed));

        // Both over: each shows n of its own.
        var more = Enumerable.Range(0, 6).Select(i => Hit(50 + i, 0, art: null)).ToList();
        (hushed, tallies) = Choose(big.Concat(more).ToList());
        Assert.Equal(N, big.Count(h => !hushed.Contains(h)));
        Assert.Equal(N, more.Count(h => !hushed.Contains(h)));
        Assert.Equal(new string?[] { "slash_heavy", null }, tallies.Select(x => x.Art));
    }

    [Fact]
    public void WithAContactGivenPlainHitsRankFromTheContactNotTheCentroid()
    {
        // Ten in a row at x = 0..9: from the centroid (4.5) the four shown are x = 3..6; from a contact at x = 9, x = 6..9.
        var hits = Enumerable.Range(0, 10).Select(i => Hit(i, 0)).ToList();
        var (hushed, _) = Choose(hits);
        Assert.Equal(new[] { 3.0, 4.0, 5.0, 6.0 }, hits.Where(h => !hushed.Contains(h)).Select(h => h.X));

        var contacts = new Dictionary<(string?, School), (double X, double Z)> { [("slash_heavy", School.Physical)] = (9, 0) };
        (hushed, _) = Choose(hits, contacts: contacts);
        Assert.Equal(new[] { 6.0, 7.0, 8.0, 9.0 }, hits.Where(h => !hushed.Contains(h)).Select(h => h.X));

        // Another source's contact is not this one's: back to the centroid.
        contacts = new() { [("watch_bell", School.Physical)] = (9, 0), [("slash_heavy", School.Fire)] = (9, 0) };
        (hushed, _) = Choose(hits, contacts: contacts);
        Assert.Equal(new[] { 3.0, 4.0, 5.0, 6.0 }, hits.Where(h => !hushed.Contains(h)).Select(h => h.X));

        // Crits still rank from HER, not the contact: she at x = 0, six crits, the contact at x = 9.
        var crits = Enumerable.Range(0, 6).Select(i => Hit(i, 0, crit: true)).ToList();
        (hushed, _) = Choose(crits, contacts: new Dictionary<(string?, School), (double X, double Z)> { [("slash_heavy", School.Physical)] = (9, 0) });
        Assert.Equal(new[] { 0.0, 1.0, 2.0, 3.0 }, crits.Where(h => !hushed.Contains(h)).Select(h => h.X));
    }

    [Fact]
    public void TheHeldCutsContactIsItsSlashAndAFrameWithoutOneFallsBackToTheCentroid()
    {
        var hits = Enumerable.Range(0, 10).Select(i => Hit(i, 0)).ToList<CombatEvent>();
        var contacts = new Dictionary<(string?, School), (double X, double Z)>();

        // No slash in the frame, a slash that is not held, one that struck nothing, one of no art: no contact.
        HitBudget.HeldContacts(hits, contacts);
        Assert.Empty(contacts);
        var frame = new List<CombatEvent>(hits)
        {
            new Ev.Slash { Art = "slash_heavy", School = School.Physical, Held = false, Struck = 10, HitX = 9, HitZ = 0 },
            new Ev.Slash { Art = "slash_heavy", School = School.Physical, Held = true, Struck = 0, HitX = 9, HitZ = 0 },
            new Ev.Slash { Art = null, School = School.Physical, Held = true, Struck = 3, HitX = 9, HitZ = 0 },
        };
        HitBudget.HeldContacts(frame, contacts);
        Assert.Empty(contacts);
        var (hushed, _) = Choose(frame, contacts: contacts);
        Assert.Equal(new[] { 3.0, 4.0, 5.0, 6.0 }, hits.Cast<Ev.Hit>().Where(h => !hushed.Contains(h)).Select(h => h.X));

        // The held cut that struck: its hits rank from where the blade met them. A second cut of the source does not move it.
        frame.Insert(0, new Ev.Slash { Art = "slash_heavy", School = School.Physical, Held = true, Struck = 10, HitX = 8, HitZ = 0 });
        frame.Add(new Ev.Slash { Art = "slash_heavy", School = School.Physical, Held = true, Struck = 10, HitX = 0, HitZ = 0 });
        HitBudget.HeldContacts(frame, contacts);
        Assert.Equal((8.0, 0.0), Assert.Single(contacts).Value);
        Assert.Equal(("slash_heavy", School.Physical), contacts.Keys.Single());
        (hushed, _) = Choose(frame, contacts: contacts);
        Assert.Equal(new[] { 6.0, 7.0, 8.0, 9.0 }, hits.Cast<Ev.Hit>().Where(h => !hushed.Contains(h)).Select(h => h.X));
    }

    [Fact]
    public void TiesAndEqualDistancesAreStable()
    {
        // Eight plain hits on ONE spot and eight crits on a ring round her: every distance in its rank is equal.
        var plain = Enumerable.Range(0, 8).Select(_ => Hit(5, 5)).ToList();
        var ring = Enumerable.Range(0, 8).Select(i => Hit(i % 2 == 0 ? 3 : -3, i % 4 < 2 ? 4 : -4, crit: true, art: "watch_bell")).ToList();
        var frame = new List<Ev.Hit>();
        for (int i = 0; i < 8; i++) { frame.Add(plain[i]); frame.Add(ring[i]); }

        var (first, _) = Choose(frame);
        // (a tie goes to the earlier event: the first n of each source show)
        Assert.Equal(plain.Skip(N), plain.Where(first.Contains));
        Assert.Equal(ring.Skip(N), ring.Where(first.Contains));
        for (int run = 0; run < 5; run++)
        {
            var (again, _) = Choose(frame);
            Assert.True(first.SetEquals(again));
        }
        // (and a frame that came between, of another shape, leaves nothing behind)
        Choose(Enumerable.Range(0, 30).Select(i => Hit(i, -i, crit: i % 3 == 0, art: "bladestorm")).ToList());
        Assert.True(first.SetEquals(Choose(frame).Hushed));
    }

    [Fact]
    public void EveryTallyAddsUpAndNoSourceShowsMoreThanN()
    {
        // A crowd cut as it was measured: 107 hits, 25 of them crits, she at the origin, the bodies in an arc before her.
        var rng = new Random(7);
        var hits = Enumerable.Range(0, 107).Select(i => Hit(1 + rng.NextDouble() * 5, rng.NextDouble() * 6 - 3, crit: i % 107 < 25)).ToList();
        var (hushed, tallies) = Choose(hits);
        var t = Assert.Single(tallies);
        Assert.Equal(new HitBudget.Tally("slash_heavy", School.Physical, Struck: 107, Crits: 25, CritsShown: N, PlainShown: 0, Hushed: 103), t);
        Assert.Equal(103, hushed.Count);
        Assert.Equal(t.Struck, t.CritsShown + t.PlainShown + t.Hushed);
        // (the crits shown are the nearest her: none hushed stands nearer than one shown)
        double far = hits.Where(h => h.Crit && !hushed.Contains(h)).Max(h => h.X * h.X + h.Z * h.Z);
        Assert.All(hits.Where(h => h.Crit && hushed.Contains(h)), h => Assert.True(h.X * h.X + h.Z * h.Z >= far));

        // A budget of none hushes all of a source that struck; a negative one reads as none.
        Assert.Equal(107, Choose(hits, n: 0).Hushed.Count);
        Assert.Equal(107, Choose(hits, n: -3).Hushed.Count);
    }

    [Fact]
    public void Shared_shake_is_nothing_for_none_linear_below_the_cap_capped_and_never_falls()
    {
        const float per = 0.0065f, cap = 0.65f;
        Assert.Equal(0f, HitBudget.SharedShake(0, per, cap));
        Assert.Equal(0f, HitBudget.SharedShake(-4, per, cap));
        Assert.Equal(0f, HitBudget.SharedShake(50, 0, cap));
        Assert.Equal(0f, HitBudget.SharedShake(50, per, 0));
        for (int h = 1; h <= 99; h++) Assert.Equal(per * h, HitBudget.SharedShake(h, per, cap), 1e-6f);
        Assert.Equal(cap, HitBudget.SharedShake(100, per, cap), 1e-6f);
        foreach (int h in new[] { 101, 103, 105, 500, 100000 }) Assert.Equal(cap, HitBudget.SharedShake(h, per, cap));
        float was = 0;
        for (int h = 0; h <= 400; h++) { float now = HitBudget.SharedShake(h, per, cap); Assert.True(now >= was, $"fell at {h}"); Assert.InRange(now, 0, cap); was = now; }
    }
}
