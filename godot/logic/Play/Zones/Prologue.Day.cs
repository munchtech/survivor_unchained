using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* The Low Ford Road by day (H4 item 10, gate N18; the owner, 3 Nov: "a daytime tutorial could be helpful - so a zone
 * outside of town after the tutorial bit, we just load into it out of the cinematic - this zone tho will be a permanent
 * one that can get reset like any diablo type zone"). From C04 A's hand-back on the north bank to the Waystation's gate:
 * the day stretch (data/content/day_stretch.json, DayStretch) with its lessons, one at a time and never on a fight's
 * first second: a boar's charge (dash out of the line), a Kerchief captain (point at your target), the road lamp
 * (Lamps v2's act1.post1, relit for good), the Kerchiefs' strongbox, and a wolf ring at the gate (the Flare's save).
 * Its packs and strongbox come back each day (data/content/zone_resets.json, ZoneReset); the lamp never goes dark again. */
public sealed partial class Prologue
{
    DayStretch? day;
    /// <summary>--stage day: the run begins at C04 A (the Warden down, the ember about to go out), for the stretch's proof.</summary>
    public bool DayStart;
    /// <summary>The strongbox on the ground (laid once the cinematic's gather is done), and its seed.</summary>
    Pickup? box;
    /// <summary>The first boar charge's blow while it is on the ground (its lesson freezes on it).</summary>
    Battle.EnemyBlow? chargeBlow;
    Enemy? chargeFrom;
    /// <summary>When the last of the stretch's fights ended (game seconds): the day's words wait 2.5 s after it.</summary>
    double dayFightEnd = -99;
    const double AfterFight = 2.5;

    DayStretch.Beat? DayBeat(string id) => DayStretch.For(Id)?.Get(id);

    void AddDay()
    {
        if (DayBeat("post") is not { Post: { } postId } pb) return;
        Interactables.Add(new()
        {
            Id = "post", X = pb.X, Z = pb.Z, R = pb.R, Verb = "Relight", Name = "Road lamp",
            When = () => day != null && Lamps.V2 && !LampBook.PostLit(W, postId),
            Locked = () => B != null && Crowd(pb.X, pb.Z, 9) > 0 ? "Not with them on you" : null,
            Act = () => RelightRoadLamp(pb),
        });
    }

    /// <summary>The stretch laid out for today (its reset rule applied first): the packs still up, the lamp dark or lit.</summary>
    void StartDay()
    {
        if (day != null || B == null || DayStretch.For(Id) is not { } spec) return;
        ZoneReset.Apply(W, Id);
        day = new DayStretch(spec, B, W.Zone(Id), G.Journey.Ch.Level, W.Day) { Held = () => G.Teaching != null };
        // Up again on the road, not back at the camp across the river.
        checkpoint = new XZ(spec.From[0], spec.From[1]);
        day.Woke = bt => PaceNotes.Enqueue($"day woke {bt.Id} t={B!.Time:0.0} hp={B.Player.Hp:0}/{B.MaxHp:0} at=({B.Player.X:0.0},{B.Player.Z:0.0})");
        day.Down = bt =>
        {
            dayFightEnd = B!.Time;
            PaceNotes.Enqueue($"day down {bt.Id} t={B.Time:0.0} hp={B.Player.Hp:0}/{B.MaxHp:0}");
            G.Save("day");
        };
        day.Told = (bt, e, blow) =>
        {
            PaceNotes.Enqueue($"day tell {bt.Id} {blow.Tell} t={B!.Time:0.0}");
            if (bt.Id == "boars" && !G.Taught("day_charge")) { chargeBlow = blow; chargeFrom = e; }
        };
        day.Ringed = bt => PaceNotes.Enqueue($"day ring {bt.Id} t={B!.Time:0.0} foes={day.Standing(bt.Id).Count} flare={B.FlareMeter:0}");
        day.Place();
        foreach (var pb in day.Of("post")) if (pb.Light >= 0) G.Look.SetLit(pb.Light, LampBook.PostLit(W, pb.Post!));
        PaceNotes.Enqueue($"day start t={B.Time:0.0} day={W.Day} packs={string.Join(",", day.Packs.Keys)} box={!day.Done("strongbox")}");
    }

    /// <summary>--stage day: the night over as C03 leaves it (the Warden down, his heart taken, the night's lessons owed),
    /// and C04 A played from the north bank, as HeartGone runs it.</summary>
    void BeginDay(Battle b)
    {
        W.Facts["prologue.woke"] = true;
        G.SetAtmosphere(Atmospheres.LowFordNight);
        for (int i = 0; i < pylons.Count; i++) { litPylons[i] = false; G.Look.SetLit(pylons[i].Light, false); }
        ai.Mode = "dead"; wardenGone = true;
        wardenView.Hide();
        // What the night left her: the Watch Chest's, and a night's lessons to pay at dawn.
        chestOpened = true;
        G.Apply("""[{ "give": "padded_jerkin", "rarity": 1 }, { "give": "health_draught", "qty": 2 }, { "gold": 15 }]""");
        if (W.NightLessons <= 0) W.NightLessons = 500;
        var bank = DayStretch.For(Id) is { } s ? (X: s.From[0] + 0.55, Z: s.From[1] + 14) : (X: 1.0, Z: -49.0);
        b.Player.X = bank.X; b.Player.Z = bank.Z; b.Player.Facing = -Math.PI / 2;
        wardenInCine = false;
        Taken(toast: false);
        dawnK = 0.287;
        Dawnbreak(said: false);
        FirstLight(false, onward: true);
    }

    /// <summary>The day's tracker: the road, and the stretch's optional lines.</summary>
    void DayObjective()
    {
        var steps = new List<Step> { new("Walk up the road to the Waystation") };
        if (DayBeat("post") is { Post: { } pid } && Lamps.V2) steps.Add(new("Relight the road lamp", true, LampBook.PostLit(W, pid)));
        if (day != null && DayBeat("strongbox") != null) steps.Add(new("Find the Kerchiefs' strongbox", true, day.Done("strongbox")));
        G.SetObjectives([new Tracked("pro", "The Road North", TrackTone.Tutorial, steps)]);
    }

    /// <summary>The day's words and lessons wait for calm: no fight on, none about to start (a resting pack within
    /// its waking distance and 6 m more), and 2.5 s after the last one ended.</summary>
    bool DayCalm()
    {
        if (day == null || B == null) return true;
        if (day.Fighting || B.Time - dayFightEnd < AfterFight) return false;
        var p = B.Player;
        foreach (var bt in day.Of("pack"))
            if (!day.DownAt.ContainsKey(bt.Id) && !day.WokeAt.ContainsKey(bt.Id) && day.Packs.ContainsKey(bt.Id) && Dist(p.X, p.Z, bt.X, bt.Z) < bt.Wake + bt.Spread + 6) return false;
        return true;
    }

    void DayTick(double dt)
    {
        if (day == null || B == null) return;
        day.Tick(dt);
        // The strongbox, once the cinematic's gather has been (it would have brought it to her feet).
        if (box == null && dawnK >= 1 && !day.Done("strongbox") && DayBeat("strongbox") is { } sb)
        {
            box = B.SpawnPickup(PickupKind.Chest, sb.X, sb.Z, 1, "day_strongbox");
            if (box != null) { box.Vx = box.Vz = 0; box.Persistent = true; }
        }
    }

    bool OnDayPickup(Pickup k)
    {
        if (k.Kind == PickupKind.Chest && k.Ref == "day_strongbox" && B != null) OpenBox(k.X, k.Z);
        return true;
    }

    /// <summary>The Kerchiefs' strongbox: gear at her level and a little better, and their gold, laid out round it.</summary>
    void OpenBox(double x, double z)
    {
        if (day == null || B == null || DayBeat("strongbox") is not { } sb) return;
        day.MarkDone(sb.Id);
        box = null;
        var loot = G.Journey.Drops(new DropCtx
        {
            Source = DropSource.Strongbox, Level = G.Journey.Ch.Level + 1, People = "kerchiefs", Luck = B.Stats.Get(Stat.Luck), R = G.Rng.NextDouble,
        });
        var shown = new List<ChestItem>();
        foreach (var l in loot)
        {
            double a = G.Rng.NextDouble() * Math.Tau, d = 1.2 + G.Rng.NextDouble() * 1.6;
            double px = x + Math.Cos(a) * d, pz = z + Math.Sin(a) * d;
            if (B.Spill(l with { Persistent = true }, px, pz) is { } pk) { px = pk.X; pz = pk.Z; }
            if (l.Ref == null || l.Kind == PickupKind.Material) continue;
            var def = Items.Find(l.Ref);
            shown.Add(new ChestItem(ChestItemKind.Gear, def?.Id ?? l.Ref, def?.Name ?? l.Ref, def?.Icon ?? "chest", 0, 0,
                (Rarity)Math.Clamp(l.Rarity ?? 0, 0, 4), null, null, px, pz));
        }
        for (int i = 0; i < Math.Max(1, sb.Gold / 4); i++)
            B.SpawnPickup(PickupKind.Gold, x + (G.Rng.NextDouble() - 0.5) * 2.5, z + (G.Rng.NextDouble() - 0.5) * 2.5, Math.Max(1, sb.Gold / Math.Max(1, sb.Gold / 4)));
        G.Chest(new ChestOpened(x, z, 1, shown, "The Kerchiefs' strongbox", 1));
        PaceNotes.Enqueue($"day box t={B.Time:0.0} items={shown.Count}");
        DayObjective();
    }

    /// <summary>The road lamp relit (Lamps v2's post): for good, a lamp for her board, and the board's lesson after it.</summary>
    void RelightRoadLamp(DayStretch.Beat pb)
    {
        if (B == null || !LampBook.RelightPost(W, pb.Post!)) return;
        if (pb.Light >= 0) G.Look.SetLit(pb.Light, true);
        lampEventAt = B.Time;
        B.Events.Emit(new Ev.Nova { X = pb.X, Z = pb.Z, Radius = 2.2, School = School.Fire, Duration = 0.9 });
        G.Toast(new Toast(ToastKind.World, "The road lamp burns again", "It will not go dark again. A lamp for your board.", Life: 6));
        PaceNotes.Enqueue($"day post t={B.Time:0.0} lamps={LampBook.PostLamps(W)}");
        DayObjective();
        G.Save("post");
        G.After(1.2, () => PacedTip("lampboard", "The Lamp board",
            $"Each dark lamp-post you relight is a lamp to spend.{NL}Press {{key:{Key("lamps")}}} to open your *Lamp board* and light one.", null, 12));
    }

    /// <summary>The stretch's three lessons (TUTORIAL_COPY's plain words), each once a profile.</summary>
    void DayCallouts()
    {
        if (day == null || B == null) return;
        var p = B.Player;
        // The charge: the first boar's lane on the ground, frozen a beat into its windup.
        if (chargeBlow != null && (chargeBlow.T <= 0.25 || chargeFrom is not { Alive: true } || G.Taught("day_charge"))) chargeBlow = null;
        if (chargeBlow is { } cb && cb.T < cb.Delay - 0.2)
            Teach("day_charge", CalloutKind.Freeze, "Charge",
                $"{Key("dash")}: dash out of its line.{NL}Once it runs, it can't turn.",
                new Aim
                {
                    World = () => chargeBlow is { } lb ? Lane(lb) : [], Safe = true,
                    Ring = () => chargeFrom is { Alive: true } cf ? [Up(cf.X, cf.Z, 0.6)] : [], RingRadius = 1.0,
                }, "dash", overHint: true, patience: 0.6, urgent: true, markInk: "#ff3b3b");
        // The captain: on first sight, before his pack is on her or a beat after it is.
        if (DayBeat("kerchiefs") is { } kb && day.Captain(kb.Id) is { } cap && Dist(cap.X, cap.Z, p.X, p.Z) < 15
            && (!day.WokeAt.TryGetValue(kb.Id, out var kw) || B.Time - kw > 1.5))
            Teach("day_hover", CalloutKind.Freeze, "Pick your target",
                $"Point at the captain (mouse, or the right stick):{NL}your blows go to him first. He rallies the rest.",
                new Aim
                {
                    World = () => day?.Captain(kb.Id) is { } c ? [Up(c.X, c.Z, 1.0)] : [], Safe = true,
                    Ring = () => day?.Captain(kb.Id) is { } c ? [Up(c.X, c.Z, 0.15)] : [], RingRadius = 1.1,
                }, patience: 8, urgent: true);
        // The ring: the wolves on its band, the Flare full; frozen before they rush.
        if (day.RingAt >= 0 && B.Time - day.RingAt < 1.3 && DayBeat("wolves") is { } wb)
        {
            if (B.Flare is { } fl && B.FlareReady)
                Teach("day_flare", CalloutKind.Freeze, fl.Name, $"{Key("flare")}: your Flare. It clears the ring.",
                    new Aim { Hud = "art", World = () => day?.Standing(wb.Id).Select(e => Up(e.X, e.Z, 0.6)).ToList() ?? [], Each = true }, "flare", overHint: true, patience: 1.2, urgent: true);
            else
                Teach("day_gap", CalloutKind.Freeze, "The ring", $"{Key("dash")}: out through the gap before they close.", Aim.At("dash"), "dash", overHint: true, patience: 1.2, urgent: true);
        }
    }

    /// <summary>A lane's points on the ground, nearest her first (the arrow lands where she stands in it).</summary>
    IReadOnlyList<(double X, double Y, double Z)> Lane(Battle.EnemyBlow lb)
    {
        var p = B!.Player;
        var pts = new List<(double X, double Y, double Z)>();
        double len = Dist(lb.X, lb.Z, lb.X1, lb.Z1);
        for (double s = 1.5; s < len; s += 1.5)
        {
            double k = s / len;
            pts.Add(Up(lb.X + (lb.X1 - lb.X) * k, lb.Z + (lb.Z1 - lb.Z) * k, 0.1));
        }
        return pts.OrderBy(q => Dist(q.X, q.Z, p.X, p.Z)).ToList();
    }

    /// <summary>Where a sensible player goes next on the stretch (the autopilot's day): a waking pack fought where it
    /// stands, the strongbox once its keepers are down, the dark lamp, then the gate. Press: the prompt to answer there.</summary>
    public (double X, double Z, string? Press)? DayGoal()
    {
        if (day == null || B == null) return null;
        var p = B.Player;
        Enemy? near = null; double nd = 16;
        foreach (var (id, _) in day.Packs)
        {
            if (!day.WokeAt.ContainsKey(id) || day.DownAt.ContainsKey(id)) continue;
            foreach (var e in day.Standing(id)) { double d = Dist(e.X, e.Z, p.X, p.Z); if (d < nd) { nd = d; near = e; } }
        }
        if (near != null) return (near.X, near.Z, null);
        bool kerchiefsDown = DayBeat("kerchiefs") is not { } kb || day.Done(kb.Id);
        if (box is { Alive: true } bx && kerchiefsDown) return (bx.X, bx.Z, null);
        if (DayBeat("post") is { Post: { } pid } pb && Lamps.V2 && !LampBook.PostLit(W, pid) && p.Z < pb.Z + 14) return (pb.X + 1.4, pb.Z, "post");
        // Up the road (its next point north), then through the gate.
        var gate = L("gate");
        return (gate.X, ExitZ - 6, null);
    }
}
