using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>A link lamp in a fight (docs/design/LAMPS_V2_RULES.md "Links"): its trigger, its wait, and its count.</summary>
public sealed class LinkRun
{
    public string Lamp = "", Trigger = "";
    public LampEffect Def = null!;
    /// <summary>Its wait (in full by night) and what is left of it.</summary>
    public double Wait, Cd;
    /// <summary>The kills counted toward a `kills` link's next.</summary>
    public int Count;
    public int Fired;
}

/* Lamps v2 in the fight (docs/design/LAMPS_V2_RULES.md, the contract; Classes 18, Phase 2): rites, links, the Hand
 * lamps, the small and notable rules (tags.more, tags.sooner, tags.duration, tags.status, tags.kill_mend) and the
 * blue lamps. Every hook the rest of the fight calls is behind Lamps.Board (a v2 rule is lit): with v1's board
 * nothing here runs, and the fight is v1's to the byte (the Act 1 gate).
 *
 * By night: smalls' numbers run at a quarter (Size, SizeOn); rites, links, Hand lamps and blue prices are rules, so
 * their args are read in full. */
public sealed partial class Battle
{
    /* ------------------------------------------------------------ the sync -- */

    readonly List<(string Mech, LampEffect E)> rites = new();
    readonly List<(LampEffect E, ModWhen? When, StatusKind? Vs)> mores = new();
    /// <summary>The links lit this fight, in the order the board lists them.</summary>
    public readonly List<LinkRun> Links = new();
    LampLoadout? boardFor;
    int boardVersion = -1;
    string? boardCalling;
    bool boardUnhoused;
    bool riteHeavy, riteStone, riteOpening, riteFar, riteGround, riteOnHit;
    Content.Hands.WardenHand? hw;
    Content.Hands.ReaverHand? hr;
    Content.Hands.ArcanistHand? ha;
    Content.Hands.StalkerHand? hs;
    double riteOpenUntil = -1, linkSenseT;
    bool belling;
    int packKills;

    /// <summary>Read the lit v2 rules again when the loadout (or her calling) changed.</summary>
    void BoardSync()
    {
        var l = Lamps;
        if (ReferenceEquals(boardFor, l) && boardVersion == l.Version && ReferenceEquals(boardCalling, Calling) && boardUnhoused == l.Unhoused) return;
        boardFor = l; boardVersion = l.Version; boardCalling = Calling; boardUnhoused = l.Unhoused;
        rites.Clear(); mores.Clear();
        riteHeavy = riteStone = riteOpening = riteFar = riteGround = riteOnHit = false;
        var keep = new Dictionary<string, LinkRun>();
        foreach (var x in Links) keep[x.Lamp] = x;
        Links.Clear();
        if (l.Each.TryGetValue("rite", out var rs))
            foreach (var e in rs)
            {
                string mech = e.Word("mech") ?? "";
                if (mech == "hand") mech = Calling switch { "warden" => "heavy", "reaver" => "bleed", "arcanist" => "ground", "stalker" => "opening", _ => "" };
                switch (mech)
                {
                    case "heavy": riteHeavy = true; break;
                    case "stone": riteStone = riteOnHit = true; break;
                    case "bleed" or "bind" or "mark": riteOnHit = true; break;
                    case "ground": riteGround = true; break;
                    case "opening": riteOpening = true; break;
                    case "far": riteFar = true; break;
                    default: continue;
                }
                rites.Add((mech, e));
            }
        if (l.Each.TryGetValue("tags.more", out var ms))
            foreach (var e in ms)
            {
                ModWhen? when = e.When ?? (e.Word("when") is { } w && Enum.TryParse<ModWhen>(w, true, out var mw) ? mw : null);
                StatusKind? vs = e.Word("vs") is { } v && Enum.TryParse<StatusKind>(v, true, out var sk) ? sk : null;
                mores.Add((e, when, vs));
            }
        if (l.Each.TryGetValue("link", out var ls))
            foreach (var e in ls)
            {
                string key = e.Lamp != "" ? e.Lamp : "link" + Links.Count;
                var run = keep.TryGetValue(key, out var old) ? old : new LinkRun();
                run.Lamp = key;
                run.Def = e;
                run.Trigger = e.Word("trigger") ?? e.Trigger ?? "";
                run.Wait = Math.Max(0.1, e.Arg("wait", 8));
                Links.Add(run);
            }
        // The Hand lamps: hands.json's numbers plus their deltas (in full by night). None, or Unhoused: the file's own.
        hw = null; hr = null; ha = null; hs = null;
        if (!l.Unhoused && l.Each.TryGetValue("hand", out var hl))
        {
            object? h = Calling switch
            {
                "warden" => hw = Json.Clone(Content.Hands.Warden),
                "reaver" => hr = Json.Clone(Content.Hands.Reaver),
                "arcanist" => ha = Json.Clone(Content.Hands.Arcanist),
                "stalker" => hs = Json.Clone(Content.Hands.Stalker),
                _ => null,
            };
            if (h != null)
                foreach (var e in hl)
                    if (e.Args != null)
                        foreach (var (k, v) in e.Args) HandDelta(h, k, v);
        }
    }

    /// <summary>A Hand lamp's delta on one of hands.json's numbers ("every", "per_level" or "perLevel").</summary>
    static void HandDelta(object h, string key, double v)
    {
        string want = key.Replace("_", "").ToLowerInvariant();
        foreach (var f in h.GetType().GetFields())
        {
            if (f.Name.ToLowerInvariant() != want) continue;
            if (f.FieldType == typeof(int)) f.SetValue(h, (int)f.GetValue(h)! + (int)Math.Round(v));
            else if (f.FieldType == typeof(double)) f.SetValue(h, (double)f.GetValue(h)! + v);
            return;
        }
    }

    /// <summary>Her Hand's numbers this fight: hands.json's, deepened by her Hand lamps.</summary>
    internal Content.Hands.WardenHand HW { get { if (!Lamps.Board) return Content.Hands.Warden; BoardSync(); return hw ?? Content.Hands.Warden; } }
    internal Content.Hands.ReaverHand HR { get { if (!Lamps.Board) return Content.Hands.Reaver; BoardSync(); return hr ?? Content.Hands.Reaver; } }
    internal Content.Hands.ArcanistHand HA { get { if (!Lamps.Board) return Content.Hands.Arcanist; BoardSync(); return ha ?? Content.Hands.Arcanist; } }
    internal Content.Hands.StalkerHand HS { get { if (!Lamps.Board) return Content.Hands.Stalker; BoardSync(); return hs ?? Content.Hands.Stalker; } }

    /// <summary>A Hand lamp's own rule (hand.{calling}.{slug}): lit, and her Hand on.</summary>
    bool HandRule(string rule) => Lamps.Board && HandKindNow() != 0 && Lamps.Has(rule);

    double SmallSize => Lamps.Night ? Content.Lamps.NightSize : 1;

    static bool Covers(LampEffect e, string skill, Tag[]? tags) => LampLoadout.Covers(e, skill, tags);

    bool RiteOn(string mech, WeaponInst w, out LampEffect? rite)
    {
        foreach (var (m, e) in rites)
            if (m == mech && Covers(e, w.Def.Id, w.Tags)) { rite = e; return true; }
        rite = null;
        return false;
    }

    /* ------------------------------------------------------- heavy (rite) -- */

    /// <summary>A heavy rite on this skill (one the warden's Hand doesn't already make heavy): is this firing its heavy one?</summary>
    bool RiteHeavyNext(WeaponInst w)
    {
        BoardSync();
        if (!riteHeavy || !RiteOn("heavy", w, out var r)) return false;
        int every = Math.Max(1, (int)Math.Round(r!.Arg("every", HW.Every)));
        // (M3 MR 3) a chained cut is a share of a blow: the light cut's weight, as the Hand's count (Hands.HandBeginCast)
        // (M3 J12: a block's answer is a whole blow)
        return Sim.Blows.Completes(w.RiteBlows, w.RitePart, every, w.WholeCast ? 1 : w.BlowWeight);
    }

    void RiteHeavyCount(WeaponInst w)
    {
        if (riteHeavy && RiteOn("heavy", w, out _)) Sim.Blows.CountFirstWhole(ref w.RiteBlows, ref w.RitePart, w.CutW);
    }

    /* ----------------------------------------------------------- the blow -- */

    /// <summary>Before a blow's damage: blue.kindled_frost freezes a chilled thing that fire strikes (so Fire on Ice shatters it).</summary>
    void BoardBeforeHit(Enemy e, School school, Tag[] tags, in HitOpts o)
    {
        if (!Lamp("blue.kindled_frost") || e.Boss || o.Dot) return;
        if (school != School.Fire && !tags.Has(Tag.Fire)) return;
        var s = e.Status;
        if (!s.Has(StatusKind.Chill) || s.Has(StatusKind.Frozen) || e.ThawT > 0) return;
        s.Remove(StatusKind.Chill);
        s[StatusKind.Frozen] = new StatusSlot(e.Elite ? 0.9 : 1.7, 1, 0, 0);
        if (e.State == EnemyState.Casting || e.State == EnemyState.Windup) Interrupt(e);
        Events.Emit(new Ev.Status { Target = e.Id, Kind = StatusKind.Frozen, X = e.X, Z = e.Z });
    }

    /// <summary>What the v2 lamps make a blow: tags.more and the blues' "harder" and "softer".</summary>
    double BoardDamageMul(Enemy e, School school, Tag[] tags, in HitOpts o)
    {
        BoardSync();
        var l = Lamps;
        double m = 1;
        string skill = o.Weapon?.Def.Id ?? "";
        bool hers = o.Weapon != null || o.Projectile;
        if (mores.Count > 0)
        {
            double more = 0;
            foreach (var (fx, when, vs) in mores)
            {
                if (!Covers(fx, skill, tags)) continue;
                if (when is { } w && !Stats.IsActive(w)) continue;
                if (vs is { } k && !e.Status.Has(k)) continue;
                more += fx.Arg("more");
            }
            m *= 1 + more * SmallSize;
        }
        if (l.Has("blue.vigil") && tags.Has(Tag.Spell) && Stones >= l.Full("blue.vigil", "stones", 3)) m *= 1 + l.Full("blue.vigil", "more", 0.3) * GiftSize;
        if (l.Has("blue.feral") && (tags.Has(Tag.Nature) || school == School.Nature) && Player.Moving) m *= 1 + l.Full("blue.feral", "more", 0.4) * GiftSize;
        if (l.Has("blue.pyre_walker") && inBurning) m *= 1 + l.Full("blue.pyre_walker", "more", 0.25) * GiftSize;
        if (l.Has("blue.kindled_frost") && hers && (school == School.Frost || tags.Has(Tag.Frost))) m *= 1 - l.Full("blue.kindled_frost", "softer", 0.25);
        if (l.Has("blue.lightning_rod") && (e.Elite || e.Boss) && (tags.Has(Tag.Storm) || tags.Has(Tag.Chain))) m *= 1 + l.Full("blue.lightning_rod", "more", 0.4) * GiftSize;
        if (l.Has("blue.long_watch") && hers && !o.Summon)
        {
            double d = Dist(e.X, e.Z, Player.X, Player.Z);
            if (d > l.Full("blue.long_watch", "far", 10)) m *= 1 + l.Full("blue.long_watch", "more", 0.35) * GiftSize;
            else if (d < l.Full("blue.long_watch", "near", 4)) m *= 1 - l.Full("blue.long_watch", "less", 0.35);
        }
        if (l.Has("blue.pack_remembers") && o.Summon)
            m *= 1 + Math.Min(l.Full("blue.pack_remembers", "cap", 0.4), packKills * l.Full("blue.pack_remembers", "per", 0.02)) * GiftSize;
        return m;
    }

    /// <summary>The rites that make a blow strike true: an opening after a dash, a far blow one time in four.</summary>
    double BoardCritAdd(Enemy e, in HitOpts o)
    {
        BoardSync();
        if ((!riteOpening && !riteFar) || o.Weapon is not { } w || o.Dot || o.Summon) return 0;
        double add = 0;
        if (riteOpening && Time < riteOpenUntil && RiteOn("opening", w, out _)) add += 1;
        if (riteFar && RiteOn("far", w, out var far) && Dist(e.X, e.Z, Player.X, Player.Z) > far!.Arg("range", 8)) add += far.Arg("chance", 0.25);
        return add;
    }

    /// <summary>blue.feral's price: she can't strike true.</summary>
    bool BoardNoTrue => Lamp("blue.feral");

    /// <summary>After a blow lands: the rites that ride it, tags.status, and the blues that read a struck thing.</summary>
    /// <param name="dmg">(M3 MR 3) The BLOW's damage (a cut's hit is a share of it): what its statuses are sized on.</param>
    /// <param name="cw">The hit's weight (a chained cut's share of its blow; 1 otherwise). The caller holds statusW at
    /// it for the call, so every ApplyStatus here builds and rolls as the cut's.</param>
    void BoardOnHit(Enemy e, School school, Tag[] tags, in HitOpts o, double dmg, bool heavy, bool crit, double cw)
    {
        BoardSync();
        var l = Lamps;
        if (!e.Alive || e.State == EnemyState.Dying) return;
        var w = o.Weapon;
        bool blow = w != null && !o.Dot && !o.Summon;
        if (blow && riteOnHit)
            foreach (var (mech, r) in rites)
            {
                if (!Covers(r, w!.Def.Id, w.Tags)) continue;
                switch (mech)
                {
                    case "stone":
                        if (e.Elite || e.Boss) HandStone(e, w);
                        break;
                    case "bleed":
                        ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, r.Arg("share", 0.3), 3), dmg, o.Depth + 1);
                        break;
                    case "bind":
                        // once a firing (a chain's cuts: once a written blow's worth, WeaponInst.FiringKey)
                        if (w.RiteBound == w.FiringKey) break;
                        w.RiteBound = w.FiringKey;
                        double sec = r.Arg("seconds", 1) * (e.Elite || e.Boss ? 0.5 : 1);
                        // (counted once a written blow already: it lands whole, not as the cut's share)
                        statusW = 1;
                        ApplyStatus(e, new StatusPayload(StatusKind.Bound, 1, 1, sec), dmg, o.Depth + 1);
                        statusW = cw;
                        break;
                    case "mark":
                        ApplyStatus(e, new StatusPayload(StatusKind.Mark, 1, 1, r.Arg("seconds", 4)), dmg, o.Depth + 1);
                        break;
                }
                if (!e.Alive) return;
            }
        // tags.status: skills with the tags inflict a status (the chance a small's size).
        if (blow && l.Each.TryGetValue("tags.status", out var sts))
            foreach (var fx in sts)
            {
                if (!Covers(fx, w!.Def.Id, w.Tags)) continue;
                StatusKind? k = fx.Status ?? (fx.Word("status") is { } ws && Enum.TryParse<StatusKind>(ws, true, out var sk) ? sk : null);
                if (k is not { } kind) continue;
                // (M3 MR 3) on a cut the chance is weighed the way ApplyStatus weighs its own: hard control by the cut's
                // share (as many a minute), every other kind so the cuts of one blow's worth compound to the blow's
                // chance; what lands then builds cw x chance / roll of a blow (hard control: whole). At weight 1: as it was.
                double chance = fx.Arg("chance", 0.1) * SmallSize;
                bool hard = kind is StatusKind.Stun or StatusKind.Fear or StatusKind.Charm;
                double roll = cw == 1 ? chance : hard ? chance * cw : Sim.Blows.Chance(chance, cw);
                if (Rng.Next() >= roll) continue;
                if (cw != 1) statusW = hard || roll <= 0 ? 1 : cw * Math.Min(1, chance) / Math.Min(1, roll);
                ApplyStatus(e, new StatusPayload(kind, 1, 1, fx.Arg("seconds", 3)), dmg, o.Depth + 1);
                statusW = cw;
            }
        // blue.unsetting_sun: holy skills sear what they strike.
        if (blow && l.Has("blue.unsetting_sun") && (w!.Tags.Has(Tag.Holy) || w.School == School.Holy))
            ApplyStatus(e, new StatusPayload(StatusKind.Sear, 1, GiftSize, l.Full("blue.unsetting_sun", "seconds", 3)), dmg, o.Depth + 1);
        var bleed = e.Status[StatusKind.Bleed];
        // blue.butchers_block: a heavy blow on a bleeding thing bursts the bleed, all its damage at once.
        if (heavy && bleed != null && bleed.T > 0 && l.Has("blue.butchers_block"))
        {
            double all = bleed.Power * bleed.T * l.Full("blue.butchers_block", "share", 1);
            e.Status.Remove(StatusKind.Bleed);
            if (all > 0) HitEnemy(e, all, School.Physical, DotBleedBurst, new HitOpts { NoCrit = true, NoProcs = true, Dot = true, Credit = "butchers_block" });
            return;
        }
        // blue.poachers_mercy: a blow that strikes true on a bleeding thing doubles its bleed (once a second a thing).
        // (M3 MR 3: a true strike is rolled a cut, so on a chain it doubles as a blow's share; no draw at weight 1.
        // The draw comes last: a cut that could not double takes none. The gate a cut sets runs 1 s x its weight, as an
        // icd a cut starts does (docs/balance/chain_weight.md): cuts 0.70 s apart pass it as blows 1.6 s apart pass 1 s.)
        if (crit && bleed != null && bleed.T > 0 && l.Has("blue.poachers_mercy") && Time - e.PoachedAt >= e.PoachedFor && (cw == 1 || Rng.Next() < cw))
        {
            e.PoachedAt = Time;
            e.PoachedFor = 1 * cw;
            bleed.Power *= 1 + (l.Full("blue.poachers_mercy", "mul", 2) - 1) * GiftSize;
        }
    }

    static readonly Tag[] DotBleedBurst = [Tag.Dot, Tag.Physical];

    /// <summary>A status landed on a creature: blue.tethered_stars makes the Bound count as Marked.</summary>
    void BoardAfterStatus(Enemy e, StatusPayload p)
    {
        if (p.Kind != StatusKind.Bound || !Lamp("blue.tethered_stars")) return;
        var b = e.Status[StatusKind.Bound];
        if (b == null) return;
        var m = e.Status[StatusKind.Mark];
        if (m == null || m.T < b.T) e.Status[StatusKind.Mark] = new StatusSlot(b.T, 1, m?.Power is > 0 ? m.Power : 1, 0.5);
    }

    /* ------------------------------------------------------------ a kill -- */

    void BoardOnKill(Enemy e, WeaponInst? weapon, bool credited)
    {
        BoardSync();
        var l = Lamps;
        if (!credited || e.Disposition == Disposition.Ally) return;
        var w = weapon ?? WeaponById(e.LastWeapon);
        packKills++;
        // A ground rite: the arcanist Hand's ground where it fell, of the skill's element (fire for any other).
        if (riteGround && w != null && RiteOn("ground", w, out _))
            LayHandGround(e, w, Content.Hands.GroundName(w.School) != null ? w.School : School.Fire);
        if (w != null && l.Each.TryGetValue("tags.kill_mend", out var km))
        {
            double share = 0;
            foreach (var fx in km) if (Covers(fx, w.Def.Id, w.Tags)) share += fx.Arg("share");
            if (share > 0) HealPlayer(MaxHp * share * SmallSize, "kill_mend", true);
        }
        if (w != null && l.Has("blue.mourners_debt") && (w.Tags.Has(Tag.Shadow) || w.School == School.Shadow))
            HealPlayer(MaxHp * l.Full("blue.mourners_debt", "share", 0.01) * GiftSize, "mourners_debt", true);
        if (l.Has("blue.unsetting_sun") && e.Status.Has(StatusKind.Sear))
            HealPlayer(MaxHp * l.Full("blue.unsetting_sun", "mend", 0.003) * GiftSize, "unsetting_sun", true);
        // blue.tethered_stars: a Bound thing that dies binds the two nearest.
        if (l.Has("blue.tethered_stars") && e.Status.Has(StatusKind.Bound))
        {
            int n = (int)l.Full("blue.tethered_stars", "count", 2);
            double sec = l.Full("blue.tethered_stars", "seconds", 2) * GiftSize;
            var near = HostilesInRadius(e.X, e.Z, 8);
            near.Remove(e);
            near.Sort((a, b) => ((a.X - e.X) * (a.X - e.X) + (a.Z - e.Z) * (a.Z - e.Z)).CompareTo((b.X - e.X) * (b.X - e.X) + (b.Z - e.Z) * (b.Z - e.Z)));
            for (int i = 0; i < Math.Min(n, near.Count); i++) ApplyStatus(near[i], new StatusPayload(StatusKind.Bound, 1, 1, sec), 0, 2);
        }
        if (Links.Count > 0)
        {
            if (e.Elite || e.Boss) LinkFire("champion_kill", 0, e);
            LinkFire("kills", 0, e);
            LinkFire("status_kill", 0, e);
        }
    }

    /* ---------------------------------------------------------- the skills -- */

    /// <summary>A skill's wait: tags.sooner, blue.unspun, and the slower prices (tethered_stars, unsetting_sun by night).</summary>
    public double BoardCooldownMul(WeaponInst w)
    {
        if (!Lamps.Board) return 1;
        var l = Lamps;
        double m = 1 - Math.Min(0.9, l.SizeOn("tags.sooner", "sooner", w.Def.Id, w.Tags));
        if (l.Has("blue.unspun") && (w.Tags.Has(Tag.Arcane) || w.School == School.Arcane)) m *= 1 - l.Full("blue.unspun", "sooner", 0.3) * GiftSize;
        if (l.Has("blue.tethered_stars") && w.Tags.Has(Tag.Spell)) m *= 1 + l.Full("blue.tethered_stars", "slower", 0.2);
        if (l.Has("blue.unsetting_sun") && l.Night && (w.Tags.Has(Tag.Holy) || w.School == School.Holy)) m *= 1 + l.Full("blue.unsetting_sun", "slower", 0.2);
        return m;
    }

    /// <summary>tags.duration: what the skill leaves lasts longer.</summary>
    public double BoardDurationMul(WeaponInst w) => Lamps.Board ? 1 + Lamps.SizeOn("tags.duration", "inc", w.Def.Id, w.Tags) : 1;

    /// <summary>A skill fired: blue.unspun's price (each arcane firing costs a share of health, never the last of it).</summary>
    public void BoardAfterFire(WeaponInst w, bool fired)
    {
        if (!fired || !Lamp("blue.unspun") || !(w.Tags.Has(Tag.Arcane) || w.School == School.Arcane)) return;
        var p = Player;
        p.Hp = Math.Max(1, p.Hp - MaxHp * Lamps.Full("blue.unspun", "cost", 0.01));
    }

    /// <summary>blue.lightning_rod: storm and chain skills strike the nearest champion first.</summary>
    public Enemy? RodTarget(WeaponInst w, double x, double z, double r)
    {
        if (!Lamp("blue.lightning_rod") || !(w.Tags.Has(Tag.Storm) || w.Tags.Has(Tag.Chain))) return null;
        return NearestHostile(x, z, r, e => e.Elite || e.Boss);
    }

    /* -------------------------------------------------------------- on her -- */

    /// <summary>May she be mended now? blue.mourners_debt: by nothing but shadow's kills; blue.drowned_lung: not while still.</summary>
    bool BoardMends(string source)
    {
        var l = Lamps;
        if (l.Has("blue.mourners_debt") && source != "mourners_debt") return false;
        if (l.Has("blue.drowned_lung") && !Player.Moving) return false;
        return true;
    }

    /// <summary>blue.pyre_walker: burning ground never harms her.</summary>
    bool BoardGroundSpares(School school) => school == School.Fire && Lamp("blue.pyre_walker");

    /// <summary>blue.lightning_rod's price: missiles strike her harder.</summary>
    double BoardMissileMul() => Lamp("blue.lightning_rod") ? 1 + Lamps.Full("blue.lightning_rod", "missiles", 0.25) : 1;

    /// <summary>A lamp's block chance under the blues: Feral never blocks; Bell and Blade's window is shorter.</summary>
    double BoardBlockChance(double chance)
    {
        if (Lamp("blue.feral")) return 0;
        if (Lamp("blue.bell_and_blade")) chance *= 1 - Lamps.Full("blue.bell_and_blade", "shorter", 0.3);
        return chance;
    }

    /// <summary>A block (lamp's or Warding light's): links on blocks; Bell and Blade counts it a perfect dash.</summary>
    void BoardOnBlock(Enemy? from)
    {
        BoardSync();
        LinkFire("block");
        if (belling || !Lamp("blue.bell_and_blade")) return;
        belling = true;
        try { PerfectDodge(from); } finally { belling = false; }
    }

    /// <summary>A perfect dash: Bell and Blade counts it a block.</summary>
    void BoardOnPerfect(Enemy? from)
    {
        if (belling || !Lamp("blue.bell_and_blade")) return;
        belling = true;
        try { FlareOnBlock(from); Fire(TriggerEvent.Block, new ProcCtx { X = Player.X, Z = Player.Z }); OnBlocked(0, from); }
        finally { belling = false; }
    }

    void BoardOnDash()
    {
        BoardSync();
        var p = Player;
        if (Lamp("blue.bell_and_blade")) p.DodgeWindow *= 1 - Lamps.Full("blue.bell_and_blade", "shorter", 0.3);
        if (riteOpening)
        {
            double sec = 0;
            foreach (var (m, e) in rites) if (m == "opening") sec = Math.Max(sec, e.Arg("seconds", HS.Seconds));
            riteOpenUntil = Time + Abilities.Dash.Time + sec;
        }
        LinkFire("dash");
    }

    /// <summary>A blow reached her health: links on a big blow, and on falling below half.</summary>
    void BoardOnHurt(double dmg, double hpBefore)
    {
        if (Links.Count == 0) return;
        LinkFire("hurt", dmg / MaxHp);
        if (hpBefore >= MaxHp * 0.5 && Player.Hp < MaxHp * 0.5) LinkFire("low");
    }

    /* ------------------------------------------------------------- links -- */

    /// <summary>A link's wait left, 0..1 (0: ready; 1: just fired), for the HUD's arc. 0 for a lamp not lit as a link.</summary>
    public double LinkWait(string lampId)
    {
        if (Lamps.Board) BoardSync();
        foreach (var l in Links) if (l.Lamp == lampId) return Clamp(l.Cd / l.Wait, 0, 1);
        return 0;
    }

    /// <summary>The skill a link fires: her pick if she carries it; else Light my way's, the carried skill sharing the most
    /// tags with the link's (ties to the order she carries them). Null when she carries nothing: the link sleeps.</summary>
    public WeaponInst? LinkSkill(string lampId)
    {
        if (Lamps.Board) BoardSync();
        foreach (var l in Links) if (l.Lamp == lampId) return LinkSkill(l);
        return null;
    }

    WeaponInst? LinkSkill(LinkRun l) => LinkPick(Weapons, Lamps.Links.TryGetValue(l.Lamp, out var pick) ? pick : null, l.Def.Tags);

    /// <summary>The rule LinkSkill fires by, for any carried list (the Lamps screen's LampBook.LinkPick reads it too): the
    /// pick if carried, else the most tags shared with the hint, ties to the order carried; null when nothing is carried.</summary>
    public static WeaponInst? LinkPick(IReadOnlyList<WeaponInst> carried, string? pick, Tag[]? hint)
    {
        if (pick != null)
            foreach (var w in carried) if (w.Id == pick || w.Def.Id == pick) return w;
        WeaponInst? best = null;
        int bestN = -1;
        foreach (var w in carried)
        {
            int n = 0;
            if (hint != null) foreach (var t in hint) if (w.Tags.Has(t)) n++;
            if (n > bestN) { bestN = n; best = w; }
        }
        return best;
    }

    void LinkFire(string trigger, double value = 0, Enemy? dead = null)
    {
        foreach (var l in Links)
        {
            if (l.Trigger != trigger) continue;
            switch (trigger)
            {
                case "hurt" when value < l.Def.Arg("share", 0.15): continue;
                case "kills":
                    if (++l.Count < Math.Max(1, (int)l.Def.Arg("count", 10))) continue;
                    if (l.Cd > 0) { l.Count--; continue; }
                    l.Count = 0;
                    break;
                case "status_kill":
                    StatusKind? k = l.Def.Status ?? (l.Def.Word("status") is { } ws && Enum.TryParse<StatusKind>(ws, true, out var sk) ? sk : null);
                    if (dead == null || k is not { } kind || !dead.Status.Has(kind)) continue;
                    break;
            }
            if (l.Cd > 0) continue;
            RunLink(l);
        }
    }

    void RunLink(LinkRun l)
    {
        var p = Player;
        if (!Combat || !p.Alive) return;
        var w = LinkSkill(l);
        if (w == null) return;
        // The wait starts before the echo: its blows may kill, and a kill link must not fire itself again inside them.
        l.Cd = l.Wait;
        if (!Firing.Echo(this, w)) { l.Cd = 0; return; }
        l.Fired++;
        Events.Emit(new Ev.Link { Lamp = l.Lamp, Skill = w.Id, X = p.X, Z = p.Z });
    }

    /// <summary>The links' waits, and the triggers that are states (a crowd round her, standing still), 4 times a second.</summary>
    void BoardTick(double dt)
    {
        BoardSync();
        if (Links.Count == 0) return;
        foreach (var l in Links) l.Cd = Math.Max(0, l.Cd - dt);
        if ((linkSenseT -= dt) > 0) return;
        linkSenseT = 0.25;
        var p = Player;
        if (!p.Alive) return;
        foreach (var l in Links)
        {
            if (l.Cd > 0) continue;
            bool go = l.Trigger switch
            {
                "crowd" => CrowdOf(l.Def.Arg("radius", 4)) >= (int)l.Def.Arg("count", 8),
                "still" => !p.Moving && p.StillT >= l.Def.Arg("seconds", 1),
                _ => false,
            };
            if (go) RunLink(l);
        }
    }

    int CrowdOf(double radius)
    {
        int n = 0;
        ForEachHostileInRadius(Player.X, Player.Z, radius, (e, _) => { if (!e.Decoy) n++; });
        return n;
    }
}
