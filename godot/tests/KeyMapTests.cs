using System.Linq;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 §1 (docs/design/M4_HUD.md): the six skill keys, the two presets, the pad, the seat order.</summary>
public class KeyMapTests
{
    [Fact]
    public void TheDefaultsPutTheSkillsOnTheMouseAndOneToFour()
    {
        var k = KeyMap.Defaults;
        Assert.Equal(new[] { "Mouse0" }, k[Act.Skill1]);
        Assert.Equal(new[] { "Mouse2" }, k[Act.Skill2]);
        Assert.Equal(new[] { "Digit1", "Digit2", "Digit3", "Digit4" }, KeyMap.Skills[2..].Select(s => k[s].Single()));
        // the Flare gave RMB up and keeps Q
        Assert.Equal(new[] { "KeyQ" }, k[Act.Flare]);
        foreach (var s in KeyMap.Skills) Assert.Contains(s, KeyMap.Rebindable);
    }

    [Fact]
    public void NoPlayKeyMeansTwoThings()
    {
        Assert.Empty(KeyMap.Collisions(KeyMap.Fresh()));
        var q = KeyMap.Fresh();
        KeyMap.ApplyPreset(q, 1);
        Assert.Empty(KeyMap.Collisions(q));
        Assert.Empty(KeyMap.PadCollisions());
    }

    [Fact]
    public void EveryPlayActionKeepsAKey()
    {
        foreach (var preset in new[] { 0, 1 })
        {
            var k = KeyMap.Fresh();
            KeyMap.ApplyPreset(k, preset);
            foreach (var a in KeyMap.PlayActs) Assert.True(k[a].Length > 0, $"{a} keyless in preset {preset}");
        }
        // and the play actions the pad presses in a fight each have a button (the book's tabs are reached through View)
        foreach (var a in KeyMap.Skills.Concat(new[] { Act.Dash, Act.Flare, Act.Draught, Act.Interact, Act.Pause, Act.Inventory, Act.Answer, Act.Experience }))
            Assert.True(KeyMap.Pad.ContainsKey(a), $"{a} has no pad button");
    }

    [Fact]
    public void QerfMovesTheFlareTheDraughtAndInteract()
    {
        var k = KeyMap.Fresh();
        KeyMap.ApplyPreset(k, 1);
        Assert.Equal(new[] { "KeyQ", "KeyE", "KeyR", "KeyF" }, KeyMap.Skills[2..].Select(s => k[s].Single()));
        Assert.Equal(new[] { "Mouse0" }, k[Act.Skill1]);
        Assert.Equal(new[] { "Mouse2" }, k[Act.Skill2]);
        Assert.Equal(new[] { "Digit1" }, k[Act.Flare]);
        Assert.Equal(new[] { "Digit2" }, k[Act.Draught]);
        Assert.Equal(new[] { "KeyG" }, k[Act.Interact]);
        // and back
        KeyMap.ApplyPreset(k, 0);
        Assert.Equal(KeyMap.Fresh().Where(kv => KeyMap.Rebindable.Contains(kv.Key)).Select(kv => (kv.Key, string.Join(",", kv.Value))),
            k.Where(kv => KeyMap.Rebindable.Contains(kv.Key)).Select(kv => (kv.Key, string.Join(",", kv.Value))));
    }

    [Fact]
    public void ARebindSwapsRatherThanStrandsAnAction()
    {
        var k = KeyMap.Fresh();
        // Skill3 onto Q: the Flare loses its only key and takes Skill3's old 1
        Assert.True(KeyMap.Rebind(k, Act.Skill3, "KeyQ"));
        Assert.Equal(new[] { "KeyQ" }, k[Act.Skill3]);
        Assert.Equal(new[] { "Digit1" }, k[Act.Flare]);
        Assert.Empty(KeyMap.Collisions(k));
        // a skill may take a mouse button; nothing else may
        Assert.True(KeyMap.Rebind(k, Act.Skill1, "Mouse1"));
        Assert.False(KeyMap.Rebind(k, Act.Dash, "Mouse0"));
        // the menus' keys stay theirs; the digits only for the skills, the Flare and the Draught
        Assert.False(KeyMap.Rebind(k, Act.Skill4, "Escape"));
        Assert.False(KeyMap.Rebind(k, Act.Map, "Digit3"));
        Assert.True(KeyMap.Rebind(k, Act.Draught, "Digit3"));
        foreach (var a in KeyMap.PlayActs) Assert.True(k[a].Length > 0, $"{a} keyless");
        Assert.Empty(KeyMap.Collisions(k));
    }

    [Fact]
    public void AnOldSaveGivesTheFlaresRmbToTheSkill()
    {
        var k = KeyMap.Fresh();
        k[Act.Flare] = ["KeyQ", "Mouse2"];
        var said = KeyMap.Sanitize(k);
        Assert.Equal(new[] { "KeyQ" }, k[Act.Flare]);
        Assert.Single(said);
        // an action an old save left only a skill's key gets its defaults back
        k[Act.Draught] = ["Digit1"];
        k[Act.Skill3] = ["Digit1"];
        KeyMap.Sanitize(k);
        Assert.Equal(new[] { "KeyR" }, k[Act.Draught]);
        Assert.Empty(KeyMap.Collisions(k));
    }

    [Fact]
    public void ThePadIsTheDesignsLayout()
    {
        var p = KeyMap.Pad;
        Assert.Equal(new[] { "A", "X", "RB", "RT", "Y", "B" }, KeyMap.Skills.Select(s => p[s].Single()));
        Assert.Equal("LB", p[Act.Dash].Single());
        Assert.Equal("LT", p[Act.Flare].Single());
        Assert.Equal("D-pad up", p[Act.Draught].Single());
        Assert.Equal("A", p[Act.Interact].Single());
        Assert.Equal("D-pad down", p[Act.Experience].Single());
    }

    [Fact]
    public void TheSeatsShowTheKeyboardLeftAndTheMouseRight()
    {
        Assert.Equal(new[] { 2, 3, 4, 5, 0, 1 }, KeyMap.SeatSlot);
        // a permutation: every slot on one seat, and SeatOf its inverse
        Assert.Equal(Enumerable.Range(0, 6), KeyMap.SeatSlot.OrderBy(x => x));
        for (int s = 0; s < 6; s++) Assert.Equal(s, KeyMap.SeatSlot[KeyMap.SeatOf(s)]);
        // seats 0-2 left of the coin hold 1, 2, 3 (Skill3-5); seat 3 right of it holds 4; then LMB and RMB
        Assert.Equal(new[] { "Digit1", "Digit2", "Digit3", "Digit4", "Mouse0", "Mouse2" }, KeyMap.SeatSlot.Select(s => KeyMap.Defaults[KeyMap.Skills[s]].Single()));
    }

    [Fact]
    public void A_null_entry_in_the_bindings_file_keeps_its_default_and_the_rest_still_load()
    {
        // (Codex audit SU-011: {"up":null} used to throw past every later entry)
        var saved = System.Text.Json.JsonSerializer.Deserialize<System.Collections.Generic.Dictionary<string, string?[]?>>(
            "{\"up\":null,\"left\":[null],\"down\":[],\"dash\":[\"KeyF\"],\"preset\":null}")!;
        var keys = KeyMap.Fresh();
        Assert.Null(KeyMap.LoadSaved(saved, keys));
        Assert.Equal(KeyMap.Defaults[Act.Up], keys[Act.Up]);
        Assert.Equal(KeyMap.Defaults[Act.Left], keys[Act.Left]);
        Assert.Equal(KeyMap.Defaults[Act.Down], keys[Act.Down]);
        Assert.Equal(new[] { "KeyF" }, keys[Act.Dash]);
        Assert.Equal(1, KeyMap.LoadSaved(new() { ["preset"] = ["1"] }, keys));
    }
}
