using System;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>NPC 18 (Brannoc): a working idle gives way to the talk stand (npcs.json talkIdle, NpcDef.Stand) while they
/// talk or she is close, so a talk never opens on the smith's back and raised arm; his hammer is our own prop.</summary>
[Collection("LoreKit")]
public class SmithStandTests
{
    [Fact]
    public void Stand_rules()
    {
        Assert.Equal("Idle", new NpcDef { Idle = "1H_Melee_Attack_Chop" }.Stand);
        Assert.Null(new NpcDef { Idle = "Idle_FoldArms_Loop" }.Stand);
        Assert.Equal("Idle_B", new NpcDef { Idle = "Sweep", TalkIdle = "Idle_B" }.Stand);
        Assert.Null(new NpcDef { Idle = "Idle", TalkIdle = "Idle" }.Stand);
        var b = Lore.Npcs["brannoc"];
        Assert.Equal("Idle", b.TalkIdle);
        Assert.Equal("smith_hammer", b.Arms!.Right);
    }

    [Fact]
    public void Smith_stops_when_close_or_talking_and_faces_her()
    {
        var def = new NpcDef { Id = "smith", Idle = "1H_Melee_Attack_Chop", TalkIdle = "Idle", Spot = new Spot { X = 0, Z = 0, Facing = Math.PI } };
        var a = new NpcActor(def, new FakeLook(ZoneMeta.Load("waystation")), new Random(1));
        a.Update(0.1, 0, 10);
        Assert.Equal("1H_Melee_Attack_Chop", a.Pose);
        a.Update(0.1, 0, 3);     // close: the stand
        Assert.Equal("Idle:talk", a.Pose);
        a.Update(0.1, 0, 4.2);   // inside the hysteresis: still standing
        Assert.Equal("Idle:talk", a.Pose);
        a.Update(0.1, 0, 6);     // away: back to work
        Assert.Equal("1H_Melee_Attack_Chop", a.Pose);
        a.Talking = true;        // a talk from afar: the stand, turned straight to her (not damped from his back)
        a.Update(0.1, 0, 6);
        Assert.Equal("Idle:talk", a.Pose);
        Assert.Equal(0, a.Heading, 3);
    }

    [Fact]
    public void Hammer_row_names_our_own_file()
    {
        Assert.Equal("res://art/weapons/smith_hammer.glb", WeaponsData.ResPath("res://art/weapons/smith_hammer.glb"));
        Assert.Equal("res://assets/weapons/mace.glb", WeaponsData.ResPath("mace"));
        var dir = AppContext.BaseDirectory;
        while (dir != null && !System.IO.File.Exists(System.IO.Path.Combine(dir, "art/weapons/weapons.json"))) dir = System.IO.Path.GetDirectoryName(dir);
        Assert.NotNull(dir);
        var row = WeaponsData.Parse(System.IO.File.ReadAllText(System.IO.Path.Combine(dir!, "art/weapons/weapons.json"))).Find(r => r.Id == "smith_hammer");
        Assert.NotNull(row);
        Assert.Equal(WeaponKind.Blunt, row!.Kind);
        Assert.True(System.IO.File.Exists(System.IO.Path.Combine(dir!, "art/weapons/smith_hammer.glb")));
    }
}
