using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The campaign's Unions (Rpg/UnionJoin.cs; ARPG.md 3.3, BUILD_UNLOCKS.md level 15): the gate, the price paid
/// once, joining and unjoining free after at a lit post only, per layout, and the battle's side. With the lamp-post tests
/// (they read the lamp board's statics).</summary>
[Collection("Balance")]
public class UnionJoinTests(ITestOutputHelper output)
{
    const string Dawn = "dawns_judgement", Pulse = "dawnpulse", Disc = "judgement_disc", Wall = "falling_wall";

    /// <summary>A Warden carrying both halves of Dawn's Judgment at a level, each with its first strand's Turn planned.</summary>
    static CharacterData Ready(int level = UnionJoin.Level, bool turns = true)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        foreach (var s in new[] { Pulse, Disc })
        {
            if (!ch.Skills.Contains(s)) ch.Skills.Add(s);
            if (!ch.Slotted.Contains(s)) ch.Slotted.Add(s);
            if (turns) Turn(ch, s);
        }
        return ch;
    }

    static void Turn(CharacterData ch, string skill)
    {
        var st = Wicks.StrandsOf(skill).First();
        for (int n = 1; n <= Wicks.PerStrand; n++) Assert.Equal(WickNo.None, WickBook.Plan(ch, skill, $"{st.Id}.{n}"));
    }

    /// <summary>Gear into her pack at a rarity (the warden's own weapon item's base); returns it.</summary>
    static ItemInstance Give(CharacterData ch, int rarity, string? def = null)
    {
        var it = Inventory.Make(ch, def ?? Callings.Archetype("warden").Weapons[0], rarity: rarity, seed: (uint)(ch.NextUid + 11));
        it.Rarity = rarity;
        ch.Pack[ch.Pack.IndexOf(null)] = it;
        return it;
    }

    static int Count(CharacterData ch) => ch.Pack.Count(i => i != null);

    [Fact]
    public void Every_union_has_a_price_and_dawns_judgement_costs_two()
    {
        Assert.All(Unions.All, u => Assert.True(u.Price > 0, u.Id));
        Assert.Equal(2, Unions.Find(Dawn)!.Price);
    }

    [Fact]
    public void A_union_opens_at_level_15_with_both_halves_carried_and_both_turns_burning()
    {
        var ch = Ready(UnionJoin.Level - 1);
        Give(ch, 2); Give(ch, 2);
        Assert.Equal(UnionNo.Level, UnionJoin.CanJoin(ch, Dawn));
        ch.Level = UnionJoin.Level;
        Assert.Equal(UnionNo.None, UnionJoin.CanJoin(ch, Dawn));

        // Points held unlit (3 burn: no Turn yet) on either half; unplanned, Light my way lights the suggested strand's Turn.
        var bare = Ready(turns: false);
        Give(bare, 2); Give(bare, 2);
        Assert.Equal(UnionNo.None, UnionJoin.CanJoin(bare, Dawn));
        WickBook.Hold(bare, Pulse, SkillBook.Rank(bare) - 3);
        Assert.Equal(UnionNo.NoTurn, UnionJoin.CanJoin(bare, Dawn));
        bare.Lamps!.Now.Held.Clear();
        WickBook.Hold(bare, Disc, SkillBook.Rank(bare) - 3);
        Assert.Equal(UnionNo.NoTurn, UnionJoin.CanJoin(bare, Dawn));
        bare.Lamps!.Now.Held.Clear();
        Assert.Equal(UnionNo.None, UnionJoin.CanJoin(bare, Dawn));
        bare.Slotted.Remove(Disc);
        Assert.Equal(UnionNo.NotCarried, UnionJoin.CanJoin(bare, Dawn));
        // Not her calling's (one whose halves' circles leave the Warden out, as Butcher's Wheel), and no such union.
        var foreign = Unions.All.First(u => !Weapons.CanCarry("warden", u.Id));
        Assert.Equal(UnionNo.Calling, UnionJoin.CanJoin(ch, foreign.Id));
        Assert.Equal(UnionNo.Unknown, UnionJoin.CanJoin(ch, "no_such_union"));
    }

    [Fact]
    public void The_price_is_rare_gear_from_her_pack_paid_once_and_joining_after_is_free()
    {
        var ch = Ready();
        var common = Give(ch, 1);
        var epic = Give(ch, 3);
        var storied = Give(ch, 5);
        var rare1 = Give(ch, 2);
        var tome = Inventory.Make(ch, SkillBook.Tome(Pulse));
        ch.Pack[ch.Pack.IndexOf(null)] = tome;
        // Common, Storied and a tome (rarity 2, but no gear) never pay: one Rare and one Epic can.
        Assert.Equal(new[] { rare1, epic }, UnionJoin.Payable(ch));
        int before = Count(ch);
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, Dawn));
        Assert.Equal(before - 2, Count(ch));
        Assert.DoesNotContain(rare1, ch.Pack);
        Assert.DoesNotContain(epic, ch.Pack);
        Assert.Contains(common, ch.Pack);
        Assert.Contains(storied, ch.Pack);
        Assert.Contains(tome, ch.Pack);
        Assert.True(UnionJoin.Known(ch, Dawn));
        Assert.Contains(Dawn, UnionJoin.Joined(ch));

        // Unjoined and joined again, with no rares left: free both ways, and it stays learned.
        Assert.Equal(UnionNo.None, UnionJoin.Unjoin(ch, Dawn));
        Assert.Empty(UnionJoin.Joined(ch));
        Assert.Equal(UnionNo.NotJoined, UnionJoin.Unjoin(ch, Dawn));
        Assert.Equal(0, UnionJoin.PriceFor(ch, Unions.Find(Dawn)!));
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, Dawn));
        Assert.Equal(before - 2, Count(ch));
        Assert.Equal(UnionNo.Joined, UnionJoin.Join(ch, Dawn));
    }

    [Fact]
    public void Too_few_rares_refuse_and_named_items_pay_exactly()
    {
        var ch = Ready();
        var r1 = Give(ch, 2);
        Assert.Equal(UnionNo.Price, UnionJoin.Join(ch, Dawn));
        Assert.Contains(r1, ch.Pack);
        var r2 = Give(ch, 2);
        var l3 = Give(ch, 4);
        // Named: the price exactly, each payable; else refused and nothing taken.
        Assert.Equal(UnionNo.Price, UnionJoin.Join(ch, Dawn, [r1.Uid]));
        Assert.Equal(UnionNo.Price, UnionJoin.Join(ch, Dawn, [r1.Uid, "not_hers"]));
        Assert.Equal(3, Count(ch));
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, Dawn, [r1.Uid, l3.Uid]));
        Assert.Equal(new[] { r2 }, ch.Pack.Where(i => i != null));
    }

    [Fact]
    public void Joined_is_per_layout_and_known_is_hers()
    {
        var ch = Ready();
        Give(ch, 2); Give(ch, 2);
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, Dawn));
        var st = LampBook.State(ch);
        st.Active = 1;
        Assert.Empty(UnionJoin.Joined(ch));
        Assert.Empty(UnionJoin.Live(ch));
        // The other layout plans its own wicks: with the Turns lit there too, it joins free (she knows it).
        Turn(ch, Pulse); Turn(ch, Disc);
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, Dawn));
        Assert.Contains(Dawn, UnionJoin.Joined(ch, st.Layouts[0]));
        Assert.Empty(UnionJoin.Joined(ch, st.Layouts[2]));
        // A save keeps both (fields: Json, IncludeFields).
        var back = SurvivorUnchained.Core.Json.Parse<CharacterData>(SurvivorUnchained.Core.Json.Write(ch));
        Assert.Equal([Dawn], back.UnionsKnown);
        Assert.Equal([Dawn], back.Lamps!.Layouts[0].Unions);
        Assert.Empty(back.Lamps.Layouts[2].Unions);
    }

    [Fact]
    public void A_turn_put_out_puts_the_union_to_sleep_but_keeps_it_joined()
    {
        var ch = Ready();
        Give(ch, 2); Give(ch, 2);
        UnionJoin.Join(ch, Dawn);
        Assert.Equal([Dawn], UnionJoin.Live(ch).Select(u => u.Id));
        WickBook.Hold(ch, Disc, SkillBook.Rank(ch) - 3);
        Assert.Empty(UnionJoin.Live(ch));
        Assert.Contains(Dawn, UnionJoin.Joined(ch));
        LampBook.Now(ch).Held.Clear();
        Assert.Single(UnionJoin.Live(ch));
    }

    [Fact]
    public void Unions_are_joined_only_at_a_lit_post_out_of_a_fight()
    {
        var ch = Ready();
        Give(ch, 2); Give(ch, 2);
        var w = new WorldState();
        w.Facts[PostMenu.TravelFact] = true;
        var post = LampPosts.Get("lowford.watch")!;
        // Dark: no bench there.
        Assert.NotNull(PostMenu.ToggleUnion(w, null, post, ch, Dawn));
        Assert.False(UnionJoin.Known(ch, Dawn));
        LampBook.LightPost(w, post.Id);
        Assert.Contains(PostMenu.Options(w, null, post, ch), o => o.Option == PostMenu.Option.Unions && o.Refused == null);
        // Below level 15 the line isn't there at all; without a character, as before.
        ch.Level = UnionJoin.Level - 1;
        Assert.DoesNotContain(PostMenu.Options(w, null, post, ch), o => o.Option == PostMenu.Option.Unions);
        Assert.DoesNotContain(PostMenu.Options(w, null, post), o => o.Option == PostMenu.Option.Unions);
        Assert.Equal("Unions open at level 15", PostMenu.ToggleUnion(w, null, post, ch, Dawn));
        ch.Level = UnionJoin.Level;
        var line = PostMenu.Unions(ch).Single(l => l.Union.Id == Dawn);
        Assert.Equal((false, false, 2, (string?)null), (line.Joined, line.Known, line.Price, line.Refused));
        Assert.Null(PostMenu.ToggleUnion(w, null, post, ch, Dawn));
        Assert.True(UnionJoin.Known(ch, Dawn));
        Assert.True(PostMenu.Unions(ch)[0].Joined);
        Assert.Null(PostMenu.ToggleUnion(w, null, post, ch, Dawn));
        Assert.Empty(UnionJoin.Joined(ch));
    }

    [Fact]
    public void In_a_fight_a_joined_union_holds_both_halves_keys_at_the_better_halfs_rank()
    {
        var ch = Ready();
        Give(ch, 2); Give(ch, 2);
        UnionJoin.Join(ch, Dawn);
        var b = BattleTests.Arena(3, (Pulse, 5), (Disc, 6));
        int sa = b.Weapons.Single(x => x.Id == Pulse).Slot, sb = b.Weapons.Single(x => x.Id == Disc).Slot;
        var put = UnionJoin.Apply(b, ch);
        var u = Unions.Find(Dawn)!;
        var w = Assert.Single(put);
        Assert.Equal(u.Into, w.Id);
        Assert.Equal([u.Into], b.Weapons.Select(x => x.Id));
        Assert.Equal((sa, sb), (w.Slot, w.Slot2));
        Assert.Equal(6, w.Rank);
        // Twice is once.
        Assert.Empty(UnionJoin.Apply(b, ch));
    }

    const double Dt = 1 / 60.0;

    static Enemy Dummy(Battle b, double x, double z)
    {
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = e.RangedT = 999;
        return e;
    }

    static void Pin(Battle b, IList<Enemy> es, IList<(double X, double Z)> at)
    {
        for (int i = 0; i < es.Count; i++) { es[i].X = at[i].X; es[i].Z = at[i].Z; es[i].Vx = es[i].Vz = 0; }
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    static void Run(Battle b, double seconds, Action each, Func<bool>? until = null)
    {
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            each();
            b.Tick(Dt, 0, 0);
            b.Events.Drain();
            if (until?.Invoke() == true) break;
        }
    }

    static double Dealt(Battle b, IList<(double X, double Z)> offs, double seconds, Action<Enemy[], List<(double, double)>>? run = null)
    {
        var p = b.Player;
        var at = offs.Select(o => (p.X + o.X, p.Z + o.Z)).ToList();
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToArray();
        if (run != null) run(es, at);
        else Run(b, seconds, () => Pin(b, es, at));
        return es.Sum(e => e.MaxHp - e.Hp) / seconds;
    }

    static Battle Fight(string a, string c, int rank)
    {
        var b = BattleTests.Arena(21, (a, rank), (c, rank));
        b.Calling = null;
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Player.Facing = Math.PI / 2;
        return b;
    }

    /// <summary>ARPG.md 3.3 (the owner, 13 Nov: "= to both of them or more"): a Union does at least the damage of its two skills
    /// apart at equal gear, in every case, and may do more (no upper band; the lower its gain, the greater its extra effect, a
    /// design rule the harness only logs). Each Warden Union, joined by UnionJoin.Apply at its halves' rank, against its two
    /// halves at that rank, all self-firing, for a minute: a pack of six around her at 4 m, one at 3 m, one at 8 m.</summary>
    [Theory]
    [InlineData(Dawn)]
    [InlineData(Wall)]
    public void A_joined_union_out_damages_its_two_halves_apart_at_equal_rank(string id)
    {
        const int Rank = 6;
        const double Seconds = 60;
        // Pressed skills (Heroic Leap, Shield Charge, Falling Wall) wait for a key: when she is free (no leap, no run), she
        // stands back on her mark and presses each ready key at the nearest dummy. Self-firing skills fire as they do.
        void Pilot(Battle b, Enemy[] es, List<(double X, double Z)> at)
        {
            var p = b.Player;
            double hx = p.X, hz = p.Z;
            for (double t = 0; t < Seconds - 1e-9; t += Dt)
            {
                if (p.Leap == null && b.Art.Rush == null)
                {
                    p.X = hx; p.Z = hz;
                    var near = at.OrderBy(q => (q.X - hx) * (q.X - hx) + (q.Z - hz) * (q.Z - hz)).First();
                    foreach (var w in b.Weapons.Where(w => w.Pressed && w.Timer <= 0).ToList()) b.PressSkill(w.Slot, near.X, near.Z);
                }
                Pin(b, es, at);
                b.Tick(Dt, 0, 0);
                b.Events.Drain();
            }
        }
        var un = Unions.Find(id)!;
        var pack = Enumerable.Range(0, 6).Select(i => (4 * Math.Sin(i * Math.PI / 3), 4 * Math.Cos(i * Math.PI / 3))).ToList();
        var cases = new (string Name, List<(double, double)> Offs)[] { ("a pack of six at 4 m", pack), ("one at 3 m", [(3, 0)]), ("one at 8 m", [(8, 0)]) };
        var ratios = new List<double>();
        foreach (var (name, offs) in cases)
        {
            var h = Fight(un.A, un.B, Rank);
            double a = Dealt(h, offs, Seconds, (es, at) => Pilot(h, es, at));
            var b = Fight(un.A, un.B, Rank);
            var w = Assert.Single(UnionJoin.Apply(b, [un]));
            Assert.Equal(Rank, w.Rank);
            double u = Dealt(b, offs, Seconds, (es, at) => Pilot(b, es, at));
            output.WriteLine($"{name}: {un.A}+{un.B} {a:0.0}/s, {un.Name} joined {u:0.0}/s (x{u / a:0.00}), rank {Rank}");
            Assert.True(u / a >= 1.0, $"{name}: x{u / a:0.00}");
            ratios.Add(u / a);
        }
        output.WriteLine($"{un.Name}: mean x{ratios.Average():0.00}");
    }

    /// <summary>Bladestorm measured, not held (the Warden's own skill since 13 Nov 2026, on its own key beside Sunder; its economy is
    /// the campaign's Resolve; this is the self-firing setup, with the arena's 6 s cooldown): whole cycles, the spin each time
    /// it is ready, held to its end and broken by a fresh press of Sunder's key; out of a storm Sunder's key held, so it swings
    /// as itself. Compared with Cleaver + Sunder apart.</summary>
    [Fact]
    public void Bladestorm_over_whole_cycles_is_measured()
    {
        const int Rank = 6;
        const double Seconds = 60;
        double Union(IList<(double X, double Z)> offs)
        {
            var b = Fight("sunder", "bladestorm", Rank);
            var gr = b.Weapons.Single(x => x.Id == "sunder"); gr.Press = gr.Def.Press; gr.CastSet = CastMode.Press; // (the Warden's held grip)
            var w = b.Weapons.Single(x => x.Id == "bladestorm");
            int bs = b.BreakSlot(w);
            w.Timer = 0;
            var p = b.Player;
            return Dealt(b, offs, Seconds, (es, at) =>
            {
                for (double t = 0; t < Seconds - 1e-9; t += Dt)
                {
                    if (w.Timer <= 0 && !Firing.InStorm(b, w)) { b.HoldSkill(bs, false); b.HoldSkill(w.Slot, true); b.PressSkill(w.Slot, p.X + 2, p.Z); }
                    bool spinning = w.Channeling;
                    b.HoldSkill(w.Slot, spinning);
                    if (!Firing.InStorm(b, w)) b.HoldSkill(bs, true);
                    Pin(b, es, at);
                    b.Tick(Dt, 0, 0);
                    b.Events.Drain();
                    // The break, a fresh press, as the spin ends.
                    if (spinning && !w.Channeling) { b.HoldSkill(bs, false); b.HoldSkill(bs, true); b.PressSkill(bs, p.X, p.Z); b.HoldSkill(bs, false); }
                }
            });
        }
        var pack = Enumerable.Range(0, 6).Select(i => (2.2 * Math.Sin(i * Math.PI / 3), 2.2 * Math.Cos(i * Math.PI / 3))).ToList();
        foreach (var (name, offs) in new (string, List<(double, double)>)[] { ("a pack of six around her", pack), ("one on her lines", [(1.5, 0)]), ("one off her lines", [(0, 1.8)]) })
        {
            double a = Dealt(Fight("sunder", "cleaver", Rank), offs, Seconds), u = Union(offs);
            output.WriteLine($"{name}: cleaver+sunder {a:0.0}/s, bladestorm beside sunder {u:0.0}/s (x{u / a:0.00}), rank {Rank}");
            Assert.True(u > 0);
        }
    }
}
