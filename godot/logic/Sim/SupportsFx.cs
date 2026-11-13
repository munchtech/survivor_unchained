using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* (bd-sockets) Support gems in the fight: what a skill's open sockets add (Rpg/Supports.EffectsFor) is worn on its
 * WeaponInst as numbers (folded into Mods) and a SupportFx (stun, bleed, block, echo). Worn again from scratch each time:
 * the old fold comes off first, so a rank change or a refresh never compounds. */
public sealed partial class Battle
{
    /// <summary>Skill id and its rank in the fight to the summed effects of the gems socketed in it.</summary>
    public Func<string, int, IReadOnlyDictionary<string, double>>? SupportSource;

    public void WearSupports(Func<string, int, IReadOnlyDictionary<string, double>>? source)
    {
        SupportSource = source;
        foreach (var w in Weapons) RewearSupport(w);
    }

    public void RewearSupport(WeaponInst w)
    {
        if (w.Support != null) Marks.Unfold(w.Mods, w.Support.Mods);
        w.Support = null;
        var eff = SupportSource?.Invoke(w.Id, w.Rank);
        if (eff == null || eff.Count == 0) return;
        var fx = new SupportFx();
        foreach (var (k, v) in eff)
            switch (k)
            {
                case "damage": fx.Mods.Damage = Math.Max(0.1, 1 + v); break;
                case "area": fx.Mods.Area = Math.Max(0.1, 1 + v); break;
                case "cooldown": fx.Mods.Cooldown *= Math.Max(0.1, 1 + v); break;
                case "speed": fx.Mods.Cooldown /= Math.Max(0.1, 1 + v); break;
                case "stun": fx.Stun = v; break;
                case "bleed": fx.Bleed = v; break;
                case "block": fx.Block = v; break;
                case "echo": fx.Echo = (int)Math.Round(v); break;
            }
        w.Support = fx;
        Marks.Fold(w.Mods, fx.Mods);
    }
}
