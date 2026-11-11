using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The save slots never lose a journey (Codex audit SU-004, SU-005): a save from a newer
/// build is refused and left as it is; a broken or half-null slot never breaks the list.</summary>
[Collection("Balance")]
public sealed class SaveSlotTests : IDisposable
{
    readonly string dir = Path.Combine(Path.GetTempPath(), "su-saves-" + Guid.NewGuid().ToString("N"));

    public void Dispose() { if (Directory.Exists(dir)) Directory.Delete(dir, true); }

    static SaveData Journey(string name)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = name, Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        return new SaveData { Character = ch, World = new WorldState { Day = 3 }, Location = new SaveLocation { Zone = "lowford" } };
    }

    [Fact]
    public void A_save_from_a_newer_build_is_refused_and_left_untouched()
    {
        var saves = new Saves(dir);
        Assert.True(saves.Write(0, Journey("Ashe")));
        var path = Path.Combine(dir, "slot0.json");
        var raw = File.ReadAllText(path).Replace($"\"version\":{Saves.Version}", $"\"version\":{Saves.Version + 1}");
        Assert.Contains($"\"version\":{Saves.Version + 1}", raw);
        File.WriteAllText(path, raw);

        Assert.Throws<NewerSaveException>(() => Saves.Parse(raw));
        Assert.Null(saves.Read(0));
        // Listed as a newer build's, under its name; never moved aside or rewritten.
        var s = Assert.Single(saves.Slots());
        Assert.True(s.Newer);
        Assert.Equal("Ashe", s.Name);
        Assert.Equal(raw, File.ReadAllText(path));
        Assert.Empty(Directory.GetFiles(dir, "slot0.json.broken.*"));
    }

    [Fact]
    public void A_null_nested_list_is_recovered_and_healthy_slots_still_list()
    {
        var saves = new Saves(dir);
        Assert.True(saves.Write(0, Journey("Ashe")));
        Assert.True(saves.Write(1, Journey("Brin")));
        var path = Path.Combine(dir, "slot1.json");
        var raw = File.ReadAllText(path);
        var nulled = System.Text.RegularExpressions.Regex.Replace(raw, "\"pack\":\\[[^\\]]*\\]", "\"pack\":null");
        Assert.Contains("\"pack\":null", nulled);
        File.WriteAllText(path, nulled);

        var back = saves.Read(1)!;
        Assert.NotNull(back.Character.Pack);
        Assert.Equal(new[] { "Ashe", "Brin" }, saves.Slots().Select(s => s.Name).ToArray());
    }

    [Fact]
    public void A_slot_migration_cannot_take_is_set_aside_and_the_others_still_list()
    {
        var saves = new Saves(dir);
        Assert.True(saves.Write(0, Journey("Ashe")));
        // Valid JSON whose character is a bare object with a null equipment: whatever throws, one
        // bad slot is set aside and never breaks the title's list.
        File.WriteAllText(Path.Combine(dir, "slot2.json"), "{\"version\":6,\"character\":{\"pack\":[null],\"equipment\":null,\"stats\":null},\"world\":{\"stash\":null,\"shops\":{\"x\":null}}}");
        var list = saves.Slots();
        Assert.Equal("Ashe", Assert.Single(list).Name);
    }

    [Fact]
    public void A_write_that_fails_leaves_the_old_file_whole()
    {
        // (SU-010: settings and bindings truncated their only copy before writing)
        Directory.CreateDirectory(dir);
        var path = Path.Combine(dir, "settings.json");
        File.WriteAllText(path, "old");
        Directory.CreateDirectory(path + ".tmp");   // the beside-file can't be written
        Assert.False(AtomicFile.Write(path, "new"));
        Assert.Equal("old", File.ReadAllText(path));
        Directory.Delete(path + ".tmp");
        Assert.True(AtomicFile.Write(path, "new"));
        Assert.Equal("new", File.ReadAllText(path));
    }
}
