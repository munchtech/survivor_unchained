using System.Linq;
using System.Text.Json.Nodes;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-wire) What wave 1 left between bd-gear, bd-keys and bd-ranks: gear auto skills in the fight, a set-B
/// weapon's stance, an old save's kindled form, and the harness's survivor carrying every slot the game opens.</summary>
public class BdWireTests
{
    static Journey Warden(int level) => MapSim.Survivor("warden", level, 1, 5);

    [Theory]
    [InlineData(10)]
    [InlineData(12)]
    [InlineData(30)]
    public void The_harness_survivor_fills_every_key_and_auto_slot_the_level_opens(int level)
    {
        var ch = Warden(level).Ch;
        Assert.Equal(SkillBook.KeysAt(level), SkillBook.KeysUsed(ch));
        Assert.Equal(SkillBook.AutosAt(level), SkillBook.AutosUsed(ch));
        var kit = Character.Kit(ch);
        Assert.Equal(SkillBook.SlotsAt(level), kit.Bar.Count(w => ch.Slotted.Contains(w.Id)));
    }

    [Fact]
    public void A_harness_grant_that_runs_itself_takes_an_auto_slot_and_no_key_from_her()
    {
        var j = Warden(30);
        var b = j.StartBattle(true, new SurvivorUnchained.Sim.CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        Assert.Equal(b.KeyCount, b.SlotsUsed);
        var keys = b.Weapons.Where(w => w.Slot < b.KeyCount).Select(w => w.Id).ToList();
        Assert.True(b.RunsItself("thornbloom"));
        var said = SurvivorUnchained.Sim.DevGrants.MakeRoom(b, "thornbloom", null, [TaughtBuilds.Of("warden")!.Grip]);
        Assert.Empty(said);
        SurvivorUnchained.Sim.DevGrants.Apply(b, "thornbloom", null, null, makeRoom: false);
        Assert.True(b.Weapons.Single(w => w.Id == "thornbloom").Slot >= b.KeyCount);
        Assert.Equal(keys, b.Weapons.Where(w => w.Slot < b.KeyCount).Select(w => w.Id).ToList());
    }

    [Fact]
    public void A_worn_auto_unique_puts_its_skill_in_the_bar_running_itself_with_her_auto_slots_full()
    {
        var ch = Warden(12).Ch;
        Assert.Equal(SkillBook.AutosAt(12), SkillBook.AutosUsed(ch));
        Assert.DoesNotContain(Character.Kit(ch).Bar, w => w.Id == "thornbloom");
        ch.Equipment[EquipSlot.Head] = Inventory.Make(ch, "thornwreath");
        var kit = Character.Kit(ch);
        Assert.Contains(("thornbloom", 2), kit.AutoSkills);
        Assert.Contains(("thornbloom", 2), kit.Bar);
        Assert.Contains("thornbloom", kit.Autos);
        // Her own three still run; the keys are untouched.
        Assert.Equal(SkillBook.AutosAt(12), kit.Bar.Count(w => kit.Autos.Contains(w.Id) && ch.Slotted.Contains(w.Id)));
        Assert.Equal(SkillBook.KeysUsed(ch), kit.Bar.Count(w => !kit.Autos.Contains(w.Id)));
        Assert.Contains(Character.DaySkills(ch), w => w.Id == "thornbloom");
    }

    [Fact]
    public void Two_auto_uniques_stack_past_her_three_auto_slots()
    {
        var ch = Warden(12).Ch;
        ch.Equipment[EquipSlot.Head] = Inventory.Make(ch, "thornwreath");
        ch.Equipment[EquipSlot.Body] = Inventory.Make(ch, "firebrands_bandolier");
        var kit = Character.Kit(ch);
        Assert.Contains("thornbloom", kit.Autos);
        Assert.Contains("firepot", kit.Autos);
        Assert.Equal(SkillBook.AutosAt(12) + 2, kit.Autos.Count);
    }

    [Fact]
    public void An_item_auto_skill_already_on_her_bar_keeps_its_place_and_rank()
    {
        var ch = Warden(12).Ch;
        var before = Character.Kit(ch).Bar;
        var (id, rank) = before.First(w => ch.Slotted.Contains(w.Id));
        var bar = Character.Bar(ch, new(), new(), [(id, rank + 3)]);
        Assert.Single(bar, w => w.Id == id);
        Assert.Equal(before.Single(w => w.Id == id), bar.Single(w => w.Id == id));
    }

    [Fact]
    public void A_pressed_only_skill_or_a_union_cannot_run_as_an_item_auto()
    {
        var keyOnly = Weapons.All.Keys.First(Weapons.KeyOnly);
        Assert.False(Character.RunsAsItemAuto(keyOnly));
        Assert.False(Character.RunsAsItemAuto(Unions.All[0].Into));
        Assert.True(Character.RunsAsItemAuto("thornbloom"));
        var ch = Warden(12).Ch;
        var autos = new System.Collections.Generic.HashSet<string>();
        var bar = Character.Bar(ch, new(), autos, [(keyOnly, 1)]);
        Assert.Equal(ch.Slotted.Contains(keyOnly), bar.Any(w => w.Id == keyOnly));
        Assert.DoesNotContain(keyOnly, autos);
    }

    [Theory]
    [InlineData("shield", "shield")]
    [InlineData("sword", "twin_blades")]
    [InlineData("dagger", "twin_blades")]
    [InlineData("mace", "mace")]
    [InlineData("hammer", "mace")]
    [InlineData("totem", null)]
    public void A_weapon_kind_picks_its_stance(string kind, string? stance) => Assert.Equal(stance, Stances.ForKind(kind));

    [Fact]
    public void The_piece_worn_as_her_second_set_picks_her_stance_once_it_opens()
    {
        var ch = Warden(12).Ch;
        ch.Equipment[EquipSlot.Offhand] = Inventory.Make(ch, "watch_shield");
        Assert.Equal("shield", SkillBook.WornStance(ch));
        ch.Stance = "mace";
        Assert.Equal("shield", SkillBook.StanceOf(ch));
        // A second blade: twin blades.
        ch.Equipment[EquipSlot.Offhand] = Inventory.Make(ch, "butchers_cleaver");
        Assert.Equal("twin_blades", SkillBook.StanceOf(ch));
        // Not before the ladder opens it (BUILD_UNLOCKS.md: level 8).
        var young = Warden(7).Ch;
        young.Equipment[EquipSlot.Offhand] = Inventory.Make(young, "watch_shield");
        Assert.Null(SkillBook.StanceOf(young));
    }

    [Fact]
    public void Without_a_stance_weapon_her_stance_falls_back_to_her_choice_then_the_taught_default()
    {
        var ch = Warden(12).Ch;
        ch.Equipment[EquipSlot.Offhand] = null;
        ch.Stance = "";
        Assert.Null(SkillBook.WornStance(ch));
        Assert.Equal(TaughtBuilds.Of("warden")!.Stance!.Default, SkillBook.StanceOf(ch));
        ch.Stance = "mace";
        Assert.Equal("mace", SkillBook.StanceOf(ch));
        ch.Equipment[EquipSlot.Offhand] = Inventory.Make(ch, "storm_totem");
        Assert.Null(SkillBook.WornStance(ch));
        Assert.Equal("mace", SkillBook.StanceOf(ch));
    }

    [Fact]
    public void An_old_save_without_the_kindled_form_loads_with_the_taught_autos_kindled()
    {
        var j = Warden(12);
        var node = JsonNode.Parse(Json.Write(j.ToSave(new SaveLocation { Zone = "waystation" })))!;
        var c = node["character"]!.AsObject();
        Assert.True(c.ContainsKey("autoForm"));
        c.Remove("autoForm");
        c.Remove("bar");
        var back = Saves.Migrate(Json.Parse<SaveData>(node.ToJsonString())).Character;
        var kindled = TaughtBuilds.Of("warden")!.Slots.Where(s => s.Cast == "kindle" && back.Slotted.Contains(s.Skill)).ToList();
        Assert.NotEmpty(kindled);
        Assert.NotEmpty(back.AutoForm);
        foreach (var s in kindled) Assert.True(SkillBook.IsAuto(back, s.Skill), s.Skill);
        Assert.True(SkillBook.KeysUsed(back) <= SkillBook.KeysAt(back.Level));
    }
}
