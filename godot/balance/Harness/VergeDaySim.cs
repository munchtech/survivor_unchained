using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One Verge day fight: a calling at a character level, against one of the Verge's day packs at the
/// level the Verge spawns it (Verge.Level: 1 + (level + day) / 2), with the day loadout a real Act 1 player has
/// by then. Setup: "old" (1/2/3 day slots at 1/4/8, Hands off), "new" (SkillBook.SlotsAt, Hands on), "nohand"
/// (new slots, Hands off). Learned: how many skills she has learned by day (the calling's own first, as
/// SkillBook.Calling picks them); the slots decide how many she carries.</summary>
public sealed record VergeDaySpec(int Seed, string Calling, int Level, int Day, string Pack, string Setup, int Learned, bool Deft = false)
{
    public string Key => $"{Pack}/{Calling}/L{Level}/d{Day}/{Setup}/k{Learned}/s{Seed}" + (Deft ? "/deft" : "");
}

public sealed class VergeDayResult
{
    public VergeDaySpec Spec = null!;
    public bool Cleared;
    public double Seconds, Lost, Low = 1;
    public int Falls, Quaffs, Foes, HandActs, Wave;
    public string Carried = "";
}

/// <summary>The Verge by day, one pack at a time on open ground (Play/Zones/Verge.cs's day spawns: their kinds,
/// counts, mixes, levels and elite leads), fought by the Pilot's hands. A measuring aid: nothing here changes the
/// game's rules (the old slots are her Slotted list cut to the old count; Hands are Battle.HandsOn).</summary>
public static class VergeDaySim
{
    /// <summary>The day slots before Classes 14 (1, 2 at level 4, 3 at level 8).</summary>
    public static int OldSlots(int level) => level >= 8 ? 3 : level >= 4 ? 2 : 1;

    /// <summary>Each pack as Verge.cs spawns it: (kind, count) pairs, the elite lead's kind (or null), its style.</summary>
    public static (List<(string Def, int N)> Foes, string? Elite, SpawnStyle Style) Pack(string pack) => pack switch
    {
        // Pack("wolf", 3-5, mix: wolf_blighted x0.4) while the stream is sick: 4 + round(1.6) = 2.
        "wolves" => (new() { ("wolf", 4), ("wolf_blighted", 2) }, null, SpawnStyle.Walk),
        "boars" => (new() { ("boar", 2) }, null, SpawnStyle.Walk),
        // Pack("footpad", 2-3, mix: pillager x0.3): max(1, round(0.9)) = 1.
        "footpads" => (new() { ("footpad", 3), ("pillager", 1) }, null, SpawnStyle.Walk),
        "lamplings" => (new() { ("lampling", 4) }, null, SpawnStyle.Burrow),
        // From day 2, a quarter of packs have a lead: one more of the kind, a level up, elite.
        "elitewolves" => (new() { ("wolf", 4), ("wolf_blighted", 2) }, "wolf", SpawnStyle.Walk),
        _ => throw new ArgumentException($"--packs {pack}: wolves, boars, footpads, lamplings, elitewolves"),
    };

    public static List<VergeDayResult> Play(VergeDaySpec spec)
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
        // What she has learned by day: the calling's own first, the way SkillBook.Calling picks (its paths, then its kind).
        var grip = Character.Kit(ch).Weapons.Select(w => w.Id).ToHashSet();
        var favours = a.Favours;
        double Own(string id) => (Content.Paths.All.Any(p => p.Callings.Contains(spec.Calling) && p.Weapons.Contains(id)) ? 2 : 0) + Content.Weapons.All[id].Tags.Count(favours.Contains);
        var learn = Content.Weapons.All.Values.Where(w => w.Findable && !grip.Contains(w.Id) && SkillBook.Carries(ch, w.Id) && SkillBook.Meets(ch, w.Id))
            .Select(w => w.Id).OrderByDescending(Own).ThenBy(id => id).Take(spec.Learned).ToList();
        ch.Discovered.AddRange(learn);
        ch.Skills.AddRange(learn);
        int slots = spec.Setup == "old" ? OldSlots(spec.Level) : SkillBook.SlotsAt(spec.Level);
        ch.Slotted.AddRange(learn.Take(slots));

        var b = j.StartBattle(true, new CollisionWorld(200), (_, _) => 0, 0, 0, 0, (uint)spec.Seed);
        b.HandsOn = spec.Setup == "new";
        var r0 = new VergeDayResult { Spec = spec, Carried = string.Join("+", b.Weapons.Select(w => $"{w.Id}:{w.Rank}")) };
        VergeDayResult fallen = r0;
        b.Hooks.OnPlayerDeath = _ => { fallen.Falls++; b.Player.Hp = b.MaxHp; b.Player.Iframes = Math.Max(b.Player.Iframes, 2); return true; };
        // The pack, ten metres off in a seeded direction, awake and hunting (Verge: spread 4, leash 22).
        var rng = new Rng((uint)(spec.Seed * 7919 + 29));
        int lvl = Math.Max(1, 1 + (spec.Level + spec.Day) / 2);
        var (foes, elite, style) = Pack(spec.Pack);
        var all = new List<VergeDayResult>();
        // Waves of the same pack in one fight, as a day's walk meets them: her skills' counters (the warden Hand's
        // every-sixth blow) carry from pack to pack; her health is whole again at each (the walk between).
        for (int wave = 0; wave < Waves; wave++)
        {
            var r = wave == 0 ? r0 : new VergeDayResult { Spec = spec, Carried = r0.Carried };
            r.Wave = wave + 1;
            b.Player.Hp = b.MaxHp;
            fallen = r;
            // The pack, ten metres off in a seeded direction, awake and hunting (Verge: spread 4, leash 22).
            double ang = rng.Next() * Math.PI * 2, cx = b.Player.X + Math.Cos(ang) * 10, cz = b.Player.Z + Math.Sin(ang) * 10;
            var pack = new List<Enemy>();
            Enemy? Spawn(string def, int level, bool el)
            {
                double pa = rng.Next() * Math.PI * 2, pd = rng.Next() * 4;
                return b.SpawnEnemy(def, cx + Math.Cos(pa) * pd, cz + Math.Sin(pa) * pd,
                    new Battle.SpawnOpts { Level = level, Elite = el, Style = style, Disposition = Disposition.Hostile, Home = (cx, cz, 22) });
            }
            foreach (var (def, n) in foes) for (int i = 0; i < n; i++) if (Spawn(def, lvl, false) is { } e) pack.Add(e);
            if (elite != null && Spawn(elite, lvl + 1, true) is { } le) pack.Add(le);
            r.Foes = pack.Count;
            int acts0 = b.HandHeavies + b.HandStones + b.HandFrenzies + b.HandGrounds + b.HandPierces + b.HandTrues + b.HandMarks;
            double t = 0, cap = 120, taken0 = b.DamageTaken;
            while (t < cap && pack.Any(e => e.Alive))
            {
                var (mx, mz) = Pilot.Steer(b, spec.Deft);
                if (Pilot.Act(b, j, mx, mz)) r.Quaffs++;
                b.Tick(ArenaSim.Dt, mx, mz);
                b.Events.Drain();
                r.Low = Math.Min(r.Low, b.Player.Hp / Math.Max(1, b.MaxHp));
                t += ArenaSim.Dt;
            }
            r.HandActs = b.HandHeavies + b.HandStones + b.HandFrenzies + b.HandGrounds + b.HandPierces + b.HandTrues + b.HandMarks - acts0;
            r.Cleared = !pack.Any(e => e.Alive);
            r.Seconds = t;
            r.Lost = (b.DamageTaken - taken0) / Math.Max(1, b.MaxHp);
            all.Add(r);
            foreach (var e in pack.Where(e => e.Alive).ToList()) b.KillEnemy(e, false, null);
            // A breath between packs (the walk on): what lingers (zones, shots) goes out.
            for (double s = 0; s < 3; s += ArenaSim.Dt) { b.Tick(ArenaSim.Dt, 0, 0); b.Events.Drain(); }
        }
        return all;
    }

    /// <summary>Packs met in one fight (--waves).</summary>
    public static int Waves = 3;

    static double Median(IEnumerable<double> xs)
    {
        var s = xs.OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s[s.Count / 2];
    }

    /// <summary>One row a calling, stage and pack; per setup: kill time (median s, "+" when some never cleared in
    /// two minutes), health lost (median / worst, of her max: every hit taken, before potions and regen), falls.</summary>
    public static string Report(List<VergeDayResult> rs)
    {
        var setups = rs.Select(r => r.Spec.Setup).Distinct().OrderBy(s => s == "old" ? 0 : s == "new" ? 1 : 2).ToList();
        var sb = new StringBuilder();
        sb.AppendLine("| Calling | Stage | Pack | Foes (lvl) | " + string.Join(" | ", setups.Select(s => $"{s}: kill s / lost med-worst / falls")) + " | new vs old (time, lost) |");
        sb.AppendLine("|---|---|---|---|" + string.Concat(setups.Select(_ => "---|")) + "---|");
        string[] order = ["warden", "reaver", "arcanist", "stalker"];
        string[] packs = ["wolves", "boars", "footpads", "lamplings", "elitewolves"];
        foreach (var g in rs.GroupBy(r => (r.Spec.Calling, r.Spec.Level, r.Spec.Day, r.Spec.Pack, r.Spec.Learned))
                     .OrderBy(g => Array.IndexOf(order, g.Key.Calling)).ThenBy(g => g.Key.Level).ThenBy(g => g.Key.Learned).ThenBy(g => Array.IndexOf(packs, g.Key.Pack)))
        {
            string Cell(List<VergeDayResult> l) => l.Count == 0 ? "-" :
                $"{Median(l.Select(r => r.Seconds)):0.0}{(l.Any(r => !r.Cleared) ? $" ({l.Count(r => !r.Cleared)} uncleared)" : "")} / {100 * Median(l.Select(r => r.Lost)):0}%-{100 * l.Max(r => r.Lost):0}% / {l.Sum(r => r.Falls)}";
            var by = setups.ToDictionary(s => s, s => g.Where(r => r.Spec.Setup == s).ToList());
            string Delta()
            {
                if (!by.TryGetValue("old", out var o) || !by.TryGetValue("new", out var n) || o.Count == 0 || n.Count == 0) return "-";
                double to = Median(o.Select(r => r.Seconds)), tn = Median(n.Select(r => r.Seconds)), lo = Median(o.Select(r => r.Lost)), ln = Median(n.Select(r => r.Lost));
                return $"{Math.Round(100 * (tn / to - 1)):+0;-0;+0}% time, {(lo < 0.005 ? "-" : $"{Math.Round(100 * (ln / lo - 1)):+0;-0;+0}%")} lost";
            }
            int lvl = Math.Max(1, 1 + (g.Key.Level + g.Key.Day) / 2);
            var any = g.First();
            sb.AppendLine($"| {g.Key.Calling} | L{g.Key.Level} d{g.Key.Day} k{g.Key.Learned} | {g.Key.Pack} | {any.Foes} ({lvl}) | " + string.Join(" | ", setups.Select(s => Cell(by[s]))) + $" | {Delta()} |");
        }
        sb.AppendLine();
        sb.AppendLine("Hard packs (a fall, uncleared in two minutes, or over 60% of her health taken), by grip:");
        foreach (var g in rs.Where(r => r.Falls > 0 || !r.Cleared || r.Lost > 0.6).GroupBy(r => (r.Spec.Calling, r.Spec.Level, r.Spec.Learned, r.Spec.Pack, r.Spec.Setup, Grip: r.Carried.Split('+')[0])).OrderBy(g => g.Key.ToString()))
            sb.AppendLine($"- {g.Key.Calling} L{g.Key.Level} k{g.Key.Learned} {g.Key.Pack} {g.Key.Setup} grip {g.Key.Grip}: {g.Count()} of {rs.Count(r => r.Spec.Calling == g.Key.Calling && r.Spec.Level == g.Key.Level && r.Spec.Learned == g.Key.Learned && r.Spec.Pack == g.Key.Pack && r.Spec.Setup == g.Key.Setup && r.Carried.Split('+')[0] == g.Key.Grip)} packs, falls {g.Sum(r => r.Falls)}, uncleared {g.Count(r => !r.Cleared)}, lost up to {100 * g.Max(r => r.Lost):0}%, {g.Max(r => r.Seconds):0} s");
        sb.AppendLine();
        sb.AppendLine("Carried by day (per calling, stage and setup; grip first):");
        foreach (var g in rs.GroupBy(r => (r.Spec.Calling, r.Spec.Level, r.Spec.Learned, r.Spec.Setup)).OrderBy(g => g.Key.ToString()))
            sb.AppendLine($"- {g.Key.Calling} L{g.Key.Level} k{g.Key.Learned} {g.Key.Setup}: {string.Join(" | ", g.Select(r => r.Carried).Distinct())}; Hand acts a fight (median) {Median(g.Select(r => (double)r.HandActs)):0}");
        return sb.ToString();
    }
}
