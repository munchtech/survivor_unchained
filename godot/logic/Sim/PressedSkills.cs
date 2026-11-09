using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* Pressed skills (the ARPG turn, the owner 8 Nov): a skill whose "cast" is press or channel waits for its key
 * (Act.Skill1..6, its slot) instead of firing itself; auto skills fire on their cooldown as they always have. The
 * slots are counted, not the weapons: a union holds both its parts' slots and answers either key. */
public sealed partial class Battle
{
    /// <summary>Where the last press aimed, on the ground (the cursor's point, or her facing times the skill's
    /// range): the behaviors read it and clamp it to their own reach.</summary>
    public (double X, double Z)? SkillAim;

    readonly bool[] heldSlots = new bool[Content.Weapons.MaxWeapons];

    /// <summary>Skill slots in use (a union counts two): what MaxWeapons is measured against.</summary>
    public int SlotsUsed
    {
        get { int n = 0; foreach (var w in Weapons) n += Content.Weapons.SlotCost(w.Id); return n; }
    }

    /// <summary>Room for this weapon (its slot cost) among the slots left.</summary>
    public bool HasRoomFor(string id) => SlotsUsed + Content.Weapons.SlotCost(id) <= Content.Weapons.MaxWeapons;

    /// <summary>The weapon on a slot (either of a union's), or null.</summary>
    public WeaponInst? OnSlot(int slot)
    {
        foreach (var w in Weapons) if (w.On(slot)) return w;
        return null;
    }

    /// <summary>The lowest free slots, as many as asked; fewer if the slots run out.</summary>
    List<int> FreeSlots(int count)
    {
        var free = new List<int>(count);
        for (int s = 0; s < Content.Weapons.MaxWeapons && free.Count < count; s++)
            if (OnSlot(s) == null) free.Add(s);
        return free;
    }

    /// <summary>The key on a slot pressed, aimed at a point on the ground: a press skill fires once if ready, a
    /// channel starts. An auto skill ignores it. True when something went off.</summary>
    public bool PressSkill(int slot, double aimX, double aimZ)
    {
        if (!Combat || !Player.Alive || FlareHold > 0) return false;
        if (OnSlot(slot) is not { } w || !w.Pressed) return false;
        SkillAim = (aimX, aimZ);
        return Firing.Press(this, w);
    }

    /// <summary>Whether a slot's key is held, every sim step (a channel runs while it is; a union reads both its
    /// slots).</summary>
    public void HoldSkill(int slot, bool held)
    {
        if (slot < 0 || slot >= heldSlots.Length) return;
        heldSlots[slot] = held;
        foreach (var w in Weapons) w.Held = heldSlots[w.Slot] || (w.Slot2 >= 0 && heldSlots[w.Slot2]);
    }

    /// <summary>A union put in at full rank holding two slots, without its evolutions asked (tests, --grant-union):
    /// its parts go if carried. Null when there is no such union or no room.</summary>
    public WeaponInst? GrantUnion(string union)
    {
        var u = Content.Unions.Find(union);
        if (u == null || Weapons.Exists(w => w.Id == u.Into)) return null;
        Journal('G', union);
        var a = Weapons.Find(w => w.Id == u.A);
        var c = Weapons.Find(w => w.Id == u.B);
        var parts = new[] { a, c }.Where(x => x != null).Select(x => x!.Slot).ToList();
        building++;
        if (a != null) RemoveWeapon(u.A);
        if (c != null) RemoveWeapon(u.B);
        var w = AddWeapon(u.Into, Content.Weapons.MaxRank);
        building--;
        if (w == null) return null;
        if (parts.Count == 2) { w.Slot = Math.Min(parts[0], parts[1]); w.Slot2 = Math.Max(parts[0], parts[1]); }
        else if (parts.Count == 1 && !w.On(parts[0])) { w.Slot2 = Math.Min(w.Slot, w.Slot2); w.Slot = parts[0]; }
        if (w.Slot2 < w.Slot) (w.Slot, w.Slot2) = (w.Slot2, w.Slot);
        Events.Emit(new Ev.Evolve { Weapon = u.Into, Into = u.Id });
        return w;
    }
}
