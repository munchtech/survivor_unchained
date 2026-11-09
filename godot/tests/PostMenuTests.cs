using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A lit lamp-post's menu (Play/PostMenu.cs; ARPG.md section 2 'Lamp-posts', 3.5, 7.3) and the doors' posts lighting
/// themselves (Play/Zones/LampRise.Doors). Runs with the lamp-post tests (they switch the lamp board).</summary>
[Collection("Balance")]
public class PostMenuTests
{
    static Journey New()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
    }

    static Battle Fight(double x, double z)
    {
        var b = new Battle(new BattleSetup { Seed = 1, Collision = new CollisionWorld(400), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
        b.Player.X = x; b.Player.Z = z;
        return b;
    }

    static string Foe() => Enemies.All.Values.First(d => d.Faction == Faction.Pack).Id;

    static LampPosts.Post P(string id) => LampPosts.Get(id)!;

    [Fact]
    public void There_is_no_travel_before_the_night_is_over()
    {
        var w = new WorldState();
        LampBook.LightPost(w, "lowford.watch");
        LampBook.LightPost(w, "lowford.bank");
        Assert.Empty(PostMenu.Travel(w, P("lowford.watch")));
        var opts = PostMenu.Options(w, null, P("lowford.watch")).Select(o => o.Option).ToList();
        Assert.DoesNotContain(PostMenu.Option.Travel, opts);
        Assert.Equal(new[] { PostMenu.Option.Tier, PostMenu.Option.Lamps, PostMenu.Option.Leave }, opts);
        w.Facts[PostMenu.TravelFact] = true;
        Assert.Equal(PostMenu.Option.Travel, PostMenu.Options(w, null, P("lowford.watch"))[0].Option);
    }

    [Fact]
    public void Travel_lists_only_lit_posts_and_not_the_one_she_stands_at()
    {
        var w = new WorldState();
        w.Facts[PostMenu.TravelFact] = true;
        LampBook.LightPost(w, "lowford.watch");
        LampBook.LightPost(w, "lowford.bank");
        LampBook.LightPost(w, "verge.entry");
        var groups = PostMenu.Travel(w, P("lowford.watch"));
        // Her own zone first, each zone under its name; the door (unlit) and her own post left out; the town's lit from the start.
        Assert.Equal(new[] { "lowford", "waystation", "verge" }, groups.Select(g => g.Zone));
        Assert.Equal("The Low Ford Road", groups[0].Name);
        Assert.Equal(new[] { "lowford.bank", "waystation.square", "verge.entry" }, groups.SelectMany(g => g.Posts).Select(p => p.Id));
        // In a fight, travel is refused.
        var b = Fight(9.5, 36.99);
        b.SpawnEnemy(Foe(), 12, 37);
        Assert.NotNull(PostMenu.TravelRefused(b, P("lowford.watch")));
        Assert.Null(PostMenu.TravelRefused(Fight(9.5, 36.99), P("lowford.watch")));
    }

    [Fact]
    public void Tier_three_is_locked_until_act_one_is_done()
    {
        var w = new WorldState();
        var tiers = PostMenu.Tiers(w);
        Assert.Equal(new[] { 1, 2, 3, 4 }, tiers.Select(t => t.N));
        Assert.True(tiers[1].Current);
        Assert.False(tiers[2].Open);
        Assert.Equal("Opens after Act 1", tiers[2].Opens);
        Assert.Equal("Opens after the campaign", tiers[3].Opens);
        Assert.Contains("×2.5 health", tiers[2].Numbers);
        Assert.False(PostMenu.SetTier(w, null, false, 3));
        w.Facts["act1.done"] = true;
        Assert.True(PostMenu.Tiers(w)[2].Open);
        Assert.True(PostMenu.SetTier(w, null, false, 3));
        Assert.True(PostMenu.Tiers(w)[2].Current);
    }

    [Fact]
    public void A_tier_change_rescales_a_living_foe_and_not_an_ally()
    {
        var w = new WorldState();
        w.Facts["act1.done"] = true;
        var b = Fight(0, 0);
        var foe = b.SpawnEnemy(Foe(), 5, 0)!;
        var ally = b.SpawnEnemy(Foe(), -5, 0, new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally })!;
        foe.Hp = foe.MaxHp / 2;
        double max = foe.MaxHp, hp = foe.Hp, dmg = foe.Damage, allyMax = ally.MaxHp;
        Assert.True(PostMenu.SetTier(w, b, true, 3));
        var t = WorldTiers.Get(3);
        Assert.Equal(max * t.Health, foe.MaxHp, 6);
        Assert.Equal(hp * t.Health, foe.Hp, 6);
        Assert.Equal(dmg * t.Damage, foe.Damage, 6);
        Assert.Equal(allyMax, ally.MaxHp, 6);
        Assert.Equal((t.Health, t.Damage, t.Kit), (b.WorldHealth, b.WorldDamage, b.KitDamageMul));
        // Back down to I: scaled by new over old.
        Assert.True(PostMenu.SetTier(w, b, true, 1));
        Assert.Equal(max * WorldTiers.Get(1).Health, foe.MaxHp, 6);
        // A fight off the tiers (an arena) is left alone.
        var arena = Fight(0, 0);
        var f2 = arena.SpawnEnemy(Foe(), 5, 0)!;
        double m2 = f2.MaxHp;
        Assert.True(PostMenu.SetTier(w, arena, false, 3));
        Assert.Equal(m2, f2.MaxHp, 6);
    }

    [Fact]
    public void The_lamps_open_at_a_lit_post_out_of_a_fight_and_close_in_one()
    {
        var w = new WorldState { Time = TimeOfDay.Day };
        var post = P("lowford.watch");
        var b = Fight(post.X, post.Z);
        // Unlit: no bench; and the field is not a town.
        Assert.False(PostMenu.LampsOpen(w, b, post));
        Assert.False(LampBook.LayoutsOpen(w, "lowford", null));
        LampBook.LightPost(w, post.Id);
        Assert.True(PostMenu.LampsOpen(w, b, post));
        Assert.True(LampBook.LayoutsOpen(w, "lowford", post.Id));
        // A post of another zone opens nothing here.
        Assert.False(LampBook.LayoutsOpen(w, "verge", post.Id));
        b.SpawnEnemy(Foe(), post.X + 3, post.Z);
        Assert.False(PostMenu.LampsOpen(w, b, post));
        Assert.NotNull(PostMenu.Options(w, b, post).Single(o => o.Option == PostMenu.Option.Lamps).Refused);
        // A town is open as it was.
        Assert.True(LampBook.LayoutsOpen(w, "waystation", null));
    }

    [Fact]
    public void A_door_post_lights_itself_when_she_comes_to_it()
    {
        var j = New();
        j.World.Facts["prologue.done"] = true;
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), (_, _) => 0, 0, -100, 0, 9);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        foreach (var e in b.Enemies.Living().ToList()) e.Alive = false;
        var door = LampPosts.All.Single(p => p.Door);
        Assert.False(LampBook.PostLit(j.World, door.Id));
        // Far off: nothing.
        b.Player.X = door.X + 20; b.Player.Z = door.Z;
        LampRise.Doors(zone, b);
        Assert.False(LampBook.PostLit(j.World, door.Id));
        // In a fight at the door: not yet.
        b.Player.X = door.X + 4; b.Player.Z = door.Z;
        var foe = b.SpawnEnemy(Foe(), door.X + 2, door.Z)!;
        LampRise.Doors(zone, b);
        Assert.False(LampBook.PostLit(j.World, door.Id));
        // The fight over, within reach: it lights, her rise point, with its toast.
        foe.Alive = false;
        LampRise.Doors(zone, b);
        Assert.True(LampBook.PostLit(j.World, door.Id));
        Assert.Equal(door.Id, LampBook.LastPost(j.World, door.Zone)!.Id);
        Assert.Contains(host.Toasts, t => t.Text.Contains(door.Name));
        // And once lit, its menu is offered where the Light was.
        Assert.True(zone.Interactables.Single(i => i.Id == LampRise.MenuPrefix + door.Id).When!());
    }
}
