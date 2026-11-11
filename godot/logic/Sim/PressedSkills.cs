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

    /// <summary>(M3 MR 3) When a spin union's second key was last pressed out of a storm (its half's swing asked): the
    /// grip's meter reads a key pressed every step as a key held (Sim/GripMeter.cs).</summary>
    public double HalfPressAt { get; private set; } = double.NegativeInfinity;

    readonly bool[] heldSlots = new bool[Content.Weapons.MaxWeapons];
    /// <summary>When each key last went down (NaN: never told; a press then is fresh): a fresh press against a grip held,
    /// or a press buffered, from before.</summary>
    readonly double[] downAt = Enumerable.Repeat(double.NaN, Content.Weapons.MaxWeapons).ToArray();

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
        if (LocalHitStopOn && Player.HitStop.Held) return false;
        if (!Combat || !Player.Alive || FlareHold > 0) return false;
        if (OnSlot(slot) is not { } w) return false;
        // A kindled skill's key (campaign): its live press (now, riposte, flare, command).
        if (!w.Pressed) { if (!w.KindledNow) return false; SkillAim = (aimX, aimZ); return KindledPress(w); }
        SkillAim = (aimX, aimZ);
        // Bladestorm (a spin union): its first key (its part A's, the Cleaver's) spins; its second (the Sunder's), pressed
        // fresh in the storm or within its BreakWindow after, breaks it (a grip held, or a press buffered, from before the
        // storm began never does), and out of a storm swings Sunder.
        if (w.Behavior == WeaponBehavior.Spin && w.Slot2 >= 0 && slot == w.Slot2)
        {
            bool fresh = double.IsNaN(downAt[slot]) || downAt[slot] >= w.StormAt;
            if (Firing.InStorm(this, w)) return fresh && Firing.SpinBreak(this, w);
            HalfPressAt = Time;
            return Firing.SwingHalf(this, w);
        }
        return Firing.Press(this, w);
    }

    /// <summary>Whether a slot's key is held, every sim step (a channel runs while it is; a union reads both its
    /// slots).</summary>
    /// <summary>HoldSkill with the aim this step (the cursor's point): a held skill repeats at it.</summary>
    public void HoldSkill(int slot, bool held, double aimX, double aimZ)
    {
        SkillAim = (aimX, aimZ);
        HoldSkill(slot, held);
    }

    public void HoldSkill(int slot, bool held)
    {
        if (slot < 0 || slot >= heldSlots.Length) return;
        if (held && !heldSlots[slot]) downAt[slot] = Time;
        heldSlots[slot] = held;
        // (A spin is held on its first key only: its second is the break, and out of a storm its other half's swing.)
        foreach (var w in Weapons)
        {
            bool spin = w.Behavior == WeaponBehavior.Spin;
            w.Held = heldSlots[w.Slot] || (w.Slot2 >= 0 && !spin && heldSlots[w.Slot2]);
            w.Held2 = spin && w.Slot2 >= 0 && heldSlots[w.Slot2];
        }
    }

    /// <summary>A union put in at full rank holding two slots, without its evolutions asked (tests, --grant-union):
    /// its parts go if carried. Null when there is no such union or no room.</summary>
    public WeaponInst? GrantUnion(string union)
    {
        var u = Content.Unions.Find(union);
        if (u == null || Weapons.Exists(w => w.Id == u.Into)) return null;
        var a = Weapons.Find(w => w.Id == u.A);
        var c = Weapons.Find(w => w.Id == u.B);
        // (M3 round 4) No room for it once its parts give up their keys: refused before a part is taken (it took the part,
        // then failed: a veteran grant of Bladestorm on six full keys left the Warden without her Sunder).
        int freed = (a != null ? Content.Weapons.SlotCost(u.A) : 0) + (c != null ? Content.Weapons.SlotCost(u.B) : 0);
        if (SlotsUsed - freed + Content.Weapons.SlotCost(u.Into) > Content.Weapons.MaxWeapons) return null;
        Journal('G', union);
        int sa = a?.Slot ?? -1, sb = c?.Slot ?? -1;
        building++;
        if (a != null) RemoveWeapon(u.A);
        if (c != null) RemoveWeapon(u.B);
        var w = AddWeapon(u.Into, Content.Weapons.MaxRank);
        building--;
        if (w == null) return null;
        // Slot is part A's key, Slot2 part B's (Bladestorm: A the Cleaver's, held to spin; B the Sunder's, the break); a
        // part not carried takes a free key, the lowest.
        int[] free = [w.Slot, w.Slot2];
        if (sa >= 0 && sb >= 0) (w.Slot, w.Slot2) = (sa, sb);
        else if (sa >= 0) (w.Slot, w.Slot2) = (sa, free.Where(s => s != sa).Min());
        else if (sb >= 0) (w.Slot, w.Slot2) = (free.Where(s => s != sb).Min(), sb);
        // Its parts' lit lamps come with it, as a union made at a lamp-post keeps them (a spin's: each on its own half).
        if (a != null || c != null) CarryTurns(w, a, c);
        Events.Emit(new Ev.Evolve { Weapon = u.Into, Into = u.Id });
        return w;
    }
}
