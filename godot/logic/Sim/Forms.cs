using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>A reflex in a fight: its art, its rank, and its own wait (docs/design/CLASSES.md §0).</summary>
public sealed class ReflexRun
{
    public ReflexDef Def = null!;
    public AbilityKind Kind;
    public int Rank = 1;
    /// <summary>Its wait left, and the wait it began (for the arc on the HUD).</summary>
    public double Cd, Full = 1;
    public int Fired;
}

/* The hands after the Lamps (docs/design/CLASSES.md §0, §2.3): the art in hand is the dash
 * form, riding the first dash after its own wait; the calling's other arts are reflexes that
 * fire themselves when their moment comes, each on its own wait. The arts' own code runs both:
 * a reflex borrows the art's wait (p.AbilityCd) while it runs, so an art that shortens its
 * own wait (Rebound, Quickening) shortens the reflex's. */
public sealed partial class Battle
{
    /// <summary>What the lit lamps bring this fight.</summary>
    public LampLoadout Lamps = LampLoadout.None;
    public readonly List<ReflexRun> Reflexes = new();
    /// <summary>The rank the running art is at (a reflex's own while it runs).</summary>
    int rankNow;
    /// <summary>The art runs as the dash's form: it rides the dash's line and leaves its motion be.</summary>
    bool asForm;

    /// <summary>A lamp's rule is lit for this fight.</summary>
    public bool Lamp(string rule) => Lamps.Has(rule);

    /// <summary>The fight's lamps: their facets join the art in hand's, their reflexes wake.</summary>
    public void SetLamps(LampLoadout l, IReadOnlyDictionary<string, int>? ranks = null)
    {
        Lamps = l;
        Facets.UnionWith(l.Facets);
        Reflexes.Clear();
        foreach (var r in l.Reflexes)
            if (Abilities.Find(r.Art) is { } def)
                Reflexes.Add(new ReflexRun { Def = r, Kind = def.Kind, Rank = Math.Clamp(ranks?.GetValueOrDefault(r.Art) ?? 1, 1, Abilities.MaxRank) });
    }

    /// <summary>The art runs this fight, in hand or as a reflex.</summary>
    public bool Runs(AbilityKind kind) => Ability == kind || Reflexes.Any(r => r.Kind == kind);

    /// <summary>The dash form's wait before haste: the Kin's from its lamp, a learned form its art's own.</summary>
    public double FormWait(AbilityKind kind)
    {
        var def = Abilities.All[kind];
        if (Lamps.Kin == def.Id && Lamps.KinWait > 0) return Lamps.KinWait;
        return def.Cooldown;
    }

    /// <summary>The dash form in hand is ready (the dash pip shows it).</summary>
    public bool FormReady => Ability is { } k && Abilities.All[k].Movement && Player.AbilityCd <= 0;

    /// <summary>The form rides this dash, along its line. True when the form carried her itself
    /// (a charge, a haul, a leap, a blink): the dash's own motion is not run.</summary>
    bool DashForm(double dx, double dz)
    {
        var p = Player;
        if (!Combat || Ability is not { } kind) return false;
        var def = Abilities.All[kind];
        if (!def.Movement) return false;
        // The second dash while an echo lives steps back into it, whatever the wait.
        if (kind == AbilityKind.EchoStep && Art.EchoT > 0) { Recall(); return true; }
        if (p.AbilityCd > 0) return false;
        double angle = Math.Atan2(dz, dx);
        p.AbilityCd = FormWait(kind) * Stats.Get(Stat.AbilityCooldown) * Abilities.RankHaste(ArtRank);
        Art.Struck.Clear();
        var was = credit;
        credit = "art";
        asForm = true;
        bool moved = false, used = true;
        double x0 = p.X, z0 = p.Z;
        switch (kind)
        {
            case AbilityKind.BullRush:
                // To the lamp: a 6 m charge behind a barrier of 15% of health (Iron Hide 25%).
                Art.Barrier = MaxHp * (Has("iron_hide") ? 0.25 : 0.15);
                Barrier(Art.Barrier, 4);
                StartRush(AbilityKind.BullRush, dx, dz, 6, 0.27);
                p.SlowT = 0; p.SlowF = 1;
                Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 1.2 });
                moved = true;
                break;
            case AbilityKind.Grapple:
                used = Grapple(def, dx, dz, angle);
                moved = used;
                break;
            case AbilityKind.Leap: Leap(def, dx, dz, angle); moved = true; break;
            case AbilityKind.Blink: Blink(def, dx, dz, angle, ArtPower); moved = true; break;
            // Vault springs the way the dash goes (the lamp's text): the caltrops stay where she left.
            case AbilityKind.Vault: { double vax = -dx, vaz = -dz; StalkerVaultAim(ref vax, ref vaz); Vault(def, dx, dz, vax, vaz, angle, ArtPower); moved = true; break; }
            // The rest ride the dash: its own step carries her.
            case AbilityKind.MirrorStep: MirrorStep(def, dx, dz, angle); break;
            case AbilityKind.Sprint: Sprint(def, angle); break;
            case AbilityKind.WraithWalk: WraithWalk(def, angle); break;
            case AbilityKind.CinderTrail: CinderTrail(def, angle); break;
            case AbilityKind.EchoStep: EchoStep(def, angle); break;
            default: used = false; break;
        }
        asForm = false;
        credit = was;
        if (!used) { p.AbilityCd = 0; return false; }
        Art.CdFull = Math.Max(0.1, p.AbilityCd);
        ArtXp += 1;
        Art.HotT = 3;
        Art.HotKills = 0;
        Fire(TriggerEvent.Ability, new ProcCtx { X = p.X, Z = p.Z });
        return moved;
    }

    /* ---------------------------------------------------------- reflexes -- */

    double reflexSenseT, spellWindowT;
    int spellsInWindow, spellStruck;
    double lastSpellAt = -1;
    string? lastSpellBy;

    void TickReflexes(double dt)
    {
        if (Reflexes.Count == 0 || !Player.Alive) return;
        foreach (var r in Reflexes) r.Cd = Math.Max(0, r.Cd - dt);
        if ((spellWindowT -= dt) <= 0) spellsInWindow = 0;
        if ((reflexSenseT -= dt) > 0) return;
        reflexSenseT = 0.1;
        var p = Player;
        foreach (var r in Reflexes)
        {
            if (r.Cd > 0) continue;
            var a = r.Def.Args;
            bool go = r.Def.Trigger switch
            {
                "crowd" => Crowd(Arg(a, "radius", 2.5), (int)Arg(a, "count", 3), true),
                "swarm" => Crowd(Arg(a, "radius", 5), (int)Arg(a, "count", 10), false),
                "low" => p.Hp < MaxHp * Arg(a, "below", 0.3333),
                "every" => true,
                _ => false,
            };
            if (go) RunReflex(r);
        }
    }

    static double Arg(Dictionary<string, double>? a, string k, double fallback) => a != null && a.TryGetValue(k, out var v) ? v : fallback;

    /// <summary>Enough of the horde close, or (for the bash) a champion close.</summary>
    bool Crowd(double radius, int count, bool champion)
    {
        var p = Player;
        int n = 0;
        bool champ = false;
        ForEachHostileInRadius(p.X, p.Z, radius, (e, _) => { if (e.Decoy) return; n++; if (e.Elite || e.Boss) champ = true; });
        return n >= count || (champion && champ);
    }

    /// <summary>A moment some reflexes answer: a big blow, a dire one, a champion's blow, a perfect dash, spells.</summary>
    void Reflex(string trigger, double share = 0)
    {
        foreach (var r in Reflexes)
        {
            if (r.Cd > 0 || r.Def.Trigger != trigger) continue;
            if (trigger is "big_blow" or "dire" && share < Arg(r.Def.Args, "share", 0)) continue;
            RunReflex(r);
        }
    }

    /// <summary>A blow reached her (after the shield): the reflexes that answer blows.</summary>
    void ReflexOnBlow(double dmg, Enemy? from)
    {
        if (Reflexes.Count == 0) return;
        double share = dmg / MaxHp;
        Reflex("big_blow", share);
        Reflex("dire", share);
        if (from is { } e && (e.Elite || e.Boss)) Reflex("swarm");
    }

    /// <summary>A spell of hers landed: three in a second wake Spellward. A spell striking many at once counts once.</summary>
    void OnSpellHit(string? by)
    {
        // The same spell striking more in the same moment: counted once, but three struck fill the Flare (Kindling).
        if (Time == lastSpellAt && by == lastSpellBy) { if (++spellStruck == 3) FlareOnSpell(3); return; }
        lastSpellAt = Time; lastSpellBy = by; spellStruck = 1;
        if (Reflexes.Count == 0) return;
        if (spellsInWindow == 0) spellWindowT = 1;
        spellsInWindow++;
        foreach (var r in Reflexes)
            if (r.Def.Trigger == "spells" && spellsInWindow >= (int)Arg(r.Def.Args, "count", 3) && r.Cd <= 0) { RunReflex(r); spellsInWindow = 0; }
    }

    void RunReflex(ReflexRun r)
    {
        var p = Player;
        if (!Combat || !p.Alive) return;
        double keep = p.AbilityCd;
        int rk = rankNow;
        double wait = r.Def.Wait;
        if (r.Kind == AbilityKind.RedTide && Lamp("red_tide.second")) wait = Lamps.Full("red_tide.second", "wait", wait);
        p.AbilityCd = wait * Stats.Get(Stat.AbilityCooldown) * Abilities.RankHaste(r.Rank);
        rankNow = r.Rank;
        var def = Abilities.All[r.Kind];
        // Toward the nearest thing that hunts her; with none, the way she faces.
        var t = NearestHostile(p.X, p.Z, 12);
        double angle = t != null ? Math.Atan2(t.Z - p.Z, t.X - p.X) : Math.Atan2(Math.Cos(p.Facing), Math.Sin(p.Facing));
        var was = credit;
        credit = "art";
        bool used = r.Kind switch
        {
            AbilityKind.ShieldBash => ShieldBash(def, angle, ArtPower),
            AbilityKind.Bulwark => Bulwark(def, angle),
            AbilityKind.Warcry => Warcry(def, angle, ArtPower),
            AbilityKind.TimeSlip => TimeSlip(def, angle, ArtPower),
            AbilityKind.MarkPrey => MarkPrey(def, angle),
            AbilityKind.SmokeBomb => SmokeBomb(def, angle, ArtPower),
            AbilityKind.RedTide => RedTide(def),
            AbilityKind.Spellward => Spellward(def),
            _ => false,
        };
        credit = was;
        r.Cd = used ? p.AbilityCd : Math.Max(0.5, Math.Min(p.AbilityCd, 0.5));
        r.Full = Math.Max(0.1, r.Cd);
        if (used) r.Fired++;
        p.AbilityCd = keep;
        rankNow = rk;
        if (used) Events.Emit(new Ev.Reflex { Art = def.Id, X = p.X, Z = p.Z });
    }

    bool RedTide(AbilityDef def)
    {
        var p = Player;
        HealPlayer(MaxHp * 0.1, "red tide");
        AddBuff("red_tide", Stat.Damage, 0.3, ModKind.More, 4, 1);
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Radius = 4 });
        return true;
    }

    bool Spellward(AbilityDef def)
    {
        var p = Player;
        double share = Lamp("spellward.thick") ? Lamps.Full("spellward.thick", "barrier", 0.15) : Arg(Reflexes.FirstOrDefault(r => r.Kind == AbilityKind.Spellward)?.Def.Args, "barrier", 0.1);
        Barrier(MaxHp * share, 5);
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Radius = 1.5 });
        return true;
    }

    /// <summary>Halve (or end) the wait of an art that runs, in hand or as a reflex.</summary>
    void HastenArt(AbilityKind kind, double factor)
    {
        if (Ability == kind) Player.AbilityCd *= factor;
        foreach (var r in Reflexes) if (r.Kind == kind) r.Cd *= factor;
    }
}
