using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Balance;

/// <summary>One walk of the Low Ford Road by day (H4 item 10): a calling at the level the night leaves her, from C04 A's
/// hand-back to the gate, by one pair of hands (human, careless: Harness/Human.cs; deft, plain: the Pilot's).</summary>
public sealed record LowfordDaySpec(int Seed, string Calling, int Level, string Bot)
{
    public string Key => $"{Calling}/L{Level}/{Bot}/s{Seed}";
}

public sealed class LowfordDayResult
{
    public LowfordDaySpec Spec = null!;
    public bool Reached, PostLit, BoxOpened;
    public double Seconds, Low = 1;
    public int Falls, Quaffs, Tells;
    /// <summary>Each beat: when it began (woke, rang), ended (down), and her lowest health inside it.</summary>
    public readonly Dictionary<string, (double Start, double End, double Low)> Beats = new();
}

/// <summary>The stretch as the game lays it (DayStretch from data/content/day_stretch.json on the Low Ford's own ground and
/// colliders), walked as a player walks it: up the road, fighting what wakes, the strongbox once its keepers are down,
/// the dark lamp relit, then the gate. A measuring aid: the game's rules are untouched.</summary>
public static class LowfordDaySim
{
    public static LowfordDayResult Play(LowfordDaySpec spec)
    {
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[spec.Seed % a.Weapons.Count], Ability = a.Abilities[0],
        }, (uint)spec.Seed);
        var ch = j.Ch;
        while (ch.Level < spec.Level) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": ch.Attributes.Wits += ch.Points; break; case "stalker": ch.Attributes.Finesse += ch.Points; break; default: ch.Attributes.Might += ch.Points; break; }
        ch.Points = 0;
        // The Watch Chest's two draughts (the night's), as the Prologue gives them.
        j.GiveItem("health_draught", 2);
        var s = DayStretch.For("lowford")!;
        var meta = ZoneMeta.Load("lowford");
        var b = j.StartBattle(true, meta.Collision(), (_, _) => 0, s.From[0], s.From[1], -Math.PI / 2, (uint)spec.Seed);
        b.Collision.RemoveTagged("gate");
        foreach (var t in Enumerable.Range(0, 3)) b.Collision.RemoveTagged($"pylon:{t}");
        var r = new LowfordDayResult { Spec = spec };
        b.Hooks.OnPlayerDeath = _ => { r.Falls++; b.Player.Hp = b.MaxHp; b.Player.Iframes = Math.Max(b.Player.Iframes, 2); return true; };
        var d = new DayStretch(s, b, new Dictionary<string, Fact>(), spec.Level, 1);
        d.Told = (_, _, _) => r.Tells++;
        d.Place();
        var post = s.Get("post");
        var boxAt = s.Get("strongbox");
        var box = boxAt != null ? b.SpawnPickup(PickupKind.Chest, boxAt.X, boxAt.Z, 1, "day_strongbox") : null;
        if (box != null) { box.Vx = box.Vz = 0; box.Persistent = true; }
        var human = spec.Bot is "human" or "careless" ? new Human(spec.Seed, spec.Bot == "careless") : null;
        bool deft = spec.Bot == "deft";
        var lows = new Dictionary<string, double>();
        double t0 = b.Time, cap = 600;
        while (b.Time - t0 < cap)
        {
            var p = b.Player;
            bool keepersDown = s.Get("kerchiefs") is not { } kb || d.Done(kb.Id);
            (double X, double Z) to = !r.PostLit && post != null && p.Z < post.Z + 14 && keepersDown ? (post.X + 1.4, post.Z)
                : box is { Alive: true, Ref: "day_strongbox" } bx && keepersDown ? (bx.X, bx.Z)
                : Math.Abs(p.X) > 3 ? (1, p.Z - 1.5) : (0, s.GateZ - 6);
            var (mx, mz) = human != null ? human.Steer(b, null, onward: to) : Pilot.Steer(b, deft, null, onward: to);
            if (human != null ? human.Act(b, j, mx, mz, null) : Pilot.Act(b, j, mx, mz)) r.Quaffs++;
            b.Tick(ArenaSim.Dt, mx, mz);
            d.Tick(ArenaSim.Dt);
            b.Events.Drain();
            double hp = p.Hp / Math.Max(1, b.MaxHp);
            r.Low = Math.Min(r.Low, hp);
            foreach (var (id, woke) in d.WokeAt)
                if (!d.DownAt.ContainsKey(id) || d.DownAt[id] >= b.Time - ArenaSim.Dt) lows[id] = Math.Min(lows.GetValueOrDefault(id, 1), hp);
            if (post != null && !r.PostLit && Math.Sqrt((p.X - post.X) * (p.X - post.X) + (p.Z - post.Z) * (p.Z - post.Z)) < post.R)
                r.PostLit = true;
            if (box != null && !r.BoxOpened && (!box.Alive || box.Ref != "day_strongbox")) r.BoxOpened = true;
            if (p.Z < s.GateZ) { r.Reached = true; break; }
        }
        r.Seconds = b.Time - t0;
        if (!r.Reached) Console.Error.WriteLine($"{spec.Key}: stuck at ({b.Player.X:0.0},{b.Player.Z:0.0}) post {r.PostLit} box {r.BoxOpened} up {string.Join(",", d.Packs.Keys.Select(k => k + ":" + d.Standing(k).Count))}");
        foreach (var (id, woke) in d.WokeAt)
            r.Beats[id] = (woke - t0, d.DownAt.TryGetValue(id, out var dn) ? dn - t0 : double.NaN, lows.GetValueOrDefault(id, 1));
        return r;
    }

    static double Median(IEnumerable<double> xs)
    {
        var s = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s[s.Count / 2];
    }

    static double Pct(IEnumerable<double> xs, double q)
    {
        var s = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s[Math.Clamp((int)(q * s.Count), 0, s.Count - 1)];
    }

    /// <summary>One row a calling, level and hands: reached, time (median, p90), falls (runs with one / total), lowest
    /// health (median / worst), and per beat its time (woke to down, median) and her lowest health in it (median / worst).</summary>
    public static string Report(List<LowfordDayResult> rs)
    {
        var beats = DayStretch.For("lowford")!.Beats.Where(x => x.Kind is "pack" or "ring").Select(x => x.Id).ToList();
        var sb = new StringBuilder();
        sb.AppendLine("| Calling | Hands | Runs | Reached | Time s (med / p90) | Falls (runs / total) | Low (med / worst) | " + string.Join(" | ", beats.Select(x => $"{x}: s / low med-worst")) + " | Post, box |");
        sb.AppendLine("|---|---|---|---|---|---|---|" + string.Concat(beats.Select(_ => "---|")) + "---|");
        string[] hands = ["human", "careless", "deft", "plain"];
        foreach (var g in rs.GroupBy(r => (r.Spec.Calling, r.Spec.Level, r.Spec.Bot)).OrderBy(g => g.Key.Calling).ThenBy(g => g.Key.Level).ThenBy(g => Array.IndexOf(hands, g.Key.Bot)))
        {
            var l = g.ToList();
            string Beat(string id)
            {
                var bs = l.Where(r => r.Beats.ContainsKey(id)).Select(r => r.Beats[id]).ToList();
                if (bs.Count == 0) return "-";
                return $"{Median(bs.Select(x => x.End - x.Start)):0} / {100 * Median(bs.Select(x => x.Low)):0}%-{100 * bs.Min(x => x.Low):0}%";
            }
            sb.AppendLine($"| {g.Key.Calling} L{g.Key.Level} | {g.Key.Bot} | {l.Count} | {l.Count(r => r.Reached)} | {Median(l.Select(r => r.Seconds)):0} / {Pct(l.Select(r => r.Seconds), 0.9):0} | " +
                $"{l.Count(r => r.Falls > 0)} / {l.Sum(r => r.Falls)} | {100 * Median(l.Select(r => r.Low)):0}% / {100 * l.Min(r => r.Low):0}% | " + string.Join(" | ", beats.Select(Beat)) +
                $" | {l.Count(r => r.PostLit)}, {l.Count(r => r.BoxOpened)} |");
        }
        return sb.ToString();
    }
}
