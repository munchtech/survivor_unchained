using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Three layouts, each a whole build; the atlas's tier lamps; save v6 (docs/design/CLASS_IDENTITY_AND_TALENTS.md
/// 3.2 "Points", 3.5; Rpg/LampBook.cs, World/Save.cs). On v1's board: the v2-only points are LampPointsV2Tests.</summary>
public sealed class LampLayoutsTests
{
    static CharacterData Make(string calling = "warden")
    {
        var a = Callings.Archetype(calling);
        return Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
    }

    static WorldState Day => new() { Time = TimeOfDay.Day };

    /// <summary>Skills she may carry, other than what creation gave her.</summary>
    static List<string> Carriable(CharacterData ch, int n) =>
        Weapons.All.Keys.Where(id => SkillBook.Carries(ch, id) && !ch.Skills.Contains(id)).OrderBy(id => id).Take(n).ToList();

    [Fact]
    public void A_new_survivor_has_three_equal_layouts()
    {
        var ch = Make();
        var ls = LampBook.State(ch).Layouts;
        Assert.Equal(3, ls.Count);
        Assert.NotEmpty(ch.Slotted);
        foreach (var l in ls)
        {
            Assert.Equal(ls[0].Type, l.Type);
            Assert.Equal(ls[0].Flare, l.Flare);
            Assert.Equal(ls[0].Lit, l.Lit);
            Assert.Equal(ch.Slotted, l.Carried);
            Assert.Empty(l.Wicks);
            Assert.Empty(l.Links);
        }
    }

    [Fact]
    public void A_switch_swaps_the_whole_build_carried_skills_included()
    {
        var ch = Make();
        ch.Level = 20;
        var start = ch.Slotted.ToList();
        var w = Day;
        Assert.True(LampBook.Switch(ch, 2, w, "waystation"));
        // Layout 3 carries something else, plans a wick, picks a link and walks another road.
        var other = Carriable(ch, 2);
        ch.Skills.AddRange(other);
        ch.Slotted = other.ToList();
        LampBook.Now(ch).Wicks["x"] = new() { "x.a1" };
        LampBook.Now(ch).Links["link.a"] = other[0];
        var road = Lamps.RoadsOf("warden").Select(r => r.Id).First(id => id != LampBook.Now(ch).Type);
        Assert.True(LampBook.SetType(ch, road));
        Assert.True(LampBook.Switch(ch, 0, w, "waystation"));
        Assert.Equal(start, ch.Slotted);
        Assert.Empty(LampBook.Now(ch).Wicks);
        Assert.NotEqual(road, LampBook.Now(ch).Type);
        Assert.True(LampBook.Switch(ch, 2, w, "waystation"));
        Assert.Equal(other, ch.Slotted);
        Assert.Equal(road, LampBook.Now(ch).Type);
        Assert.Single(LampBook.Now(ch).Wicks);
        Assert.Equal(other[0], LampBook.Now(ch).Links["link.a"]);
        // A skill since forgotten isn't carried back.
        Assert.True(LampBook.Switch(ch, 1, w, "waystation"));
        ch.Skills.Remove(other[1]);
        Assert.True(LampBook.Switch(ch, 2, w, "waystation"));
        Assert.Equal(new[] { other[0] }, ch.Slotted);
    }

    [Fact]
    public void Layouts_change_by_day_in_town_only()
    {
        var ch = Make();
        Assert.False(LampBook.Switch(ch, 1, new WorldState { Time = TimeOfDay.Night }, "waystation"));
        Assert.False(LampBook.Switch(ch, 1, Day, "verge"));
        Assert.False(LampBook.Switch(ch, 1, Day, null));
        Assert.False(LampBook.Switch(ch, 1, null, "waystation"));
        Assert.False(LampBook.Switch(ch, 1, new WorldState { Time = TimeOfDay.Day, Map = new Chart() }, "waystation"));
        Assert.False(LampBook.Switch(ch, 1, new WorldState { Time = TimeOfDay.Day, Arena = new Arena.ArenaSpec() }, "waystation"));
        Assert.False(LampBook.Switch(ch, 3, Day, "waystation"));
        Assert.Equal(0, LampBook.State(ch).Active);
        Assert.True(LampBook.Switch(ch, 1, new WorldState { Time = TimeOfDay.Dusk }, "waystation"));
        Assert.Equal(1, LampBook.State(ch).Active);
    }

    [Fact]
    public void A_save_keeps_what_the_active_layout_carries()
    {
        var ch = Make();
        var more = Carriable(ch, 1)[0];
        ch.Skills.Add(more);
        ch.Slotted.Add(more);
        var dir = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "su-saves-" + System.Guid.NewGuid().ToString("N"));
        SaveData back;
        try
        {
            var saves = new Saves(dir);
            Assert.True(saves.Write(1, new SaveData { Character = ch, World = new WorldState() }));
            back = saves.Read(1)!;
        }
        finally { System.IO.Directory.Delete(dir, true); }
        Assert.Equal(6, back.Version);
        Assert.Equal(ch.Slotted, back.Character.Lamps!.Now.Carried);
        Assert.Equal(3, back.Character.Lamps.Layouts.Count);
    }

    [Fact]
    public void Each_new_tiers_first_clear_lights_one_atlas_lamp()
    {
        var w = new WorldState();
        Assert.Equal(0, LampBook.AtlasLit(w));
        Atlas.Complete(w, new Chart { Tier = 1, People = "a" });
        Atlas.Complete(w, new Chart { Tier = 1, People = "b" }); // the same tier, another people: no lamp
        Atlas.Complete(w, new Chart { Tier = 1, People = "a" }); // again: no lamp
        Assert.Equal(1, LampBook.AtlasLit(w));
        Atlas.Complete(w, new Chart { Tier = 3, People = "a" });
        Atlas.Complete(w, new Chart { Tier = 2, People = "b" }); // a lower tier first cleared later still counts
        Assert.Equal(3, LampBook.AtlasLit(w));
        for (int t = 4; t <= 16; t++) Atlas.Complete(w, new Chart { Tier = t, People = "a" });
        Assert.Equal(16, (int)w.Fact("lamps.atlas").Number);
        Assert.Equal(8, LampBook.AtlasLit(w)); // v1 holds eight
    }

    [Fact]
    public void Lamp_posts_give_nothing_on_v1()
    {
        var ch = Make();
        var w = new WorldState();
        int before = LampBook.Earned(ch, w);
        Assert.False(LampBook.RelightPost(w, "act1.post1"));
        Assert.Equal(before, LampBook.Earned(ch, w));
        Assert.Equal(8, LampBook.AtlasLamps);
    }

    /// <summary>A version 5 save (two layouts, no carried lists, lamps lit past the free ones, wick plans, link picks,
    /// a skill her calling can't carry, a full storeroom) loads as version 6.</summary>
    [Fact]
    public void A_version_five_save_loads_as_six()
    {
        var ch = Make();
        ch.Level = 12;
        var lost = Weapons.All.Keys.Where(id => !SkillBook.Carries(ch, id) && Items.Find(SkillBook.Tome(id)) != null).OrderBy(id => id).First();
        var kept = Carriable(ch, 1)[0];
        ch.Skills.AddRange(new[] { lost, kept });
        ch.Slotted.AddRange(new[] { lost, kept });
        var st = LampBook.State(ch);
        foreach (var l in st.Layouts)
        {
            l.Lit.AddRange(Lamps.Next(Lamps.Start("warden")).Where(id => !l.Lit.Contains(id)));
            l.Wicks[kept] = new() { "whatever" };
            l.Links["some.link"] = kept;
        }
        st.Active = 1;
        var world = new WorldState();
        for (int i = 0; i < world.Stash.Count; i++) world.Stash[i] = Inventory.Make(ch, "health_draught", 1);
        var node = JsonNode.Parse(Json.Write(new SaveData { Version = 5, Character = ch, World = world }))!;
        var layouts = node["character"]!["lamps"]!["layouts"]!.AsArray();
        layouts.RemoveAt(2);
        foreach (var l in layouts) l!.AsObject().Remove("carried");

        var d = Saves.Parse(node.ToJsonString())!;
        Assert.Equal(6, d.Version);
        var c = d.Character;
        Assert.Equal(3, c.Lamps!.Layouts.Count);
        Assert.Equal(1, c.Lamps.Active);
        Assert.DoesNotContain(lost, c.Skills);
        Assert.DoesNotContain(lost, c.Slotted);
        Assert.Contains(kept, c.Slotted);
        Assert.Contains(d.World.Stash, it => it?.Def == SkillBook.Tome(lost));
        Assert.Equal(0, d.World.Stash.Count % WorldState.Shelf);
        foreach (var l in c.Lamps.Layouts)
        {
            Assert.Equal(LampBook.Free(c, l).OrderBy(x => x), l.Lit.OrderBy(x => x));
            Assert.Empty(l.Wicks);
            Assert.Empty(l.Links);
            Assert.Equal(c.Slotted, l.Carried);
            Assert.Equal(Lamps.Road(l.Type).Strike, l.Flare);
        }
        Assert.Equal(LampBook.Earned(c, d.World), LampBook.Spare(c, d.World));
    }
}

/// <summary>Lamps v2's points: thirty atlas lamps and the relit lamp-posts. Runs alone (it switches the board).</summary>
[Collection("Balance")]
public sealed class LampPointsV2Tests
{
    static bool HasData => System.IO.File.Exists(System.IO.Path.Combine(DataFiles.Dir, "content", "lamps_v2.json"));

    [Fact]
    public void Thirty_atlas_lamps_and_four_posts_in_act_one()
    {
        if (!HasData) return;
        Lamps.UseV2(true);
        try
        {
            Assert.Equal(30, LampBook.AtlasLamps);
            var w = new WorldState();
            w.Facts["lamps.atlas"] = 40;
            Assert.Equal(30, LampBook.AtlasLit(w));
            Assert.Equal(new[] { "act1.post1", "act1.post2", "act1.post3", "act1.post4" }, Lamps.Posts);

            var a = Callings.Archetype("warden");
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            }, seed: 7);
            var v = new WorldState();
            int before = LampBook.Earned(ch, v);
            Assert.True(LampBook.RelightPost(v, "act1.post2"));
            Assert.False(LampBook.RelightPost(v, "act1.post2"));
            Assert.False(LampBook.RelightPost(v, "act9.post1"));
            Assert.True(v.Fact("lampposts.act1.post2").Truthy);
            Assert.Equal(before + 1, LampBook.Earned(ch, v));
            foreach (var p in Lamps.Posts) LampBook.RelightPost(v, p);
            Assert.Equal(before + 4, LampBook.Earned(ch, v));
        }
        finally { Lamps.UseV2(false); }
    }
}
