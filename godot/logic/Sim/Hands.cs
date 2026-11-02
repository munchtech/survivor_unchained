using System;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The Hands in the fight (docs/design/CLASS_IDENTITY_AND_TALENTS.md 2.2 item 1; numbers in data/content/hands.json).
 * Each works on an empty board: the calling mechanics in *Lamps.cs do nothing until their lamps are lit, so each Hand
 * has a base form of its own (Stones on Shield Arm's defaults, a Frenzy cap of its own) and the lamps deepen it.
 * This is the hot path (every hit of a 300-creature horde): counters live on the weapon or here, nothing allocates
 * per hit but the view's event when a Hand acts. */
public sealed partial class Battle
{
    /// <summary>The Hands on (the harness's --hand 0 turns every one off, to measure them).</summary>
    public static bool Hands = true;
    /// <summary>This fight's Hands, from Hands as it begins (so a test may turn one fight's off without touching others).</summary>
    public bool HandsOn = Hands;

    /// <summary>The weapon whose heavy blow is landing now (in its firing, or as its heavy projectile strikes).</summary>
    internal WeaponInst? HeavyBy;
    /// <summary>The reaver Hand's Frenzy gate; the stalker Hand's window after a dash.</summary>
    double handFrenzyGate, handDashUntil = -1;
    /// <summary>The arcanist Hand's grounds, a ring so the oldest goes out first.</summary>
    GroundZone?[]? handGround;
    int handGroundAt;
    /// <summary>Counters for measurement and tests.</summary>
    public int HandHeavies, HandStones, HandFrenzies, HandGrounds, HandPierces, HandTrues, HandMarks;

    string? handFor;
    int handKind;
    /// <summary>Which Hand is hers (0 none, 1 warden, 2 reaver, 3 arcanist, 4 stalker), read once per calling set.</summary>
    int HandKindNow()
    {
        if (!HandsOn || Lamps.Unhoused) return 0;
        if (!ReferenceEquals(handFor, Calling))
        {
            handFor = Calling;
            handKind = Calling switch { "warden" => 1, "reaver" => 2, "arcanist" => 3, "stalker" => 4, _ => 0 };
        }
        return handKind;
    }
    bool WardenHand => HandKindNow() == 1;
    bool ReaverHand => HandKindNow() == 2;
    bool ArcanistHand => HandKindNow() == 3;
    bool StalkerHand => HandKindNow() == 4;

    void HandEv(HandKind k, double x, double z, int target = -1) =>
        Events.Emit(new Ev.Hand { Kind = k, X = x, Z = z, Target = target });

    /* ---------------------------------------------------------------- warden -- */

    /// <summary>A skill is about to fire (Firing.Tick): counts its blows, and says whether this one is heavy.</summary>
    internal bool HandBeginCast(WeaponInst w)
    {
        w.Casts++;
        // Lamps v2: a heavy rite makes another tag's skill heavy on its own count (Sim/BoardRules.cs).
        if (!WardenHand || !Content.Hands.Heavies(w.Tags)) return Lamps.Board && RiteHeavyNext(w);
        int every = Math.Max(1, HW.Every);
        // The count is of firings, not of attempts: an attempt with nothing in range is not a blow (HandEndCast).
        return (w.HandBlows + 1) % every == 0;
    }

    /// <summary>The firing done: a blow counted only if it fired.</summary>
    internal void HandEndCast(WeaponInst w, bool fired)
    {
        if (!fired) { w.Casts--; return; }
        if (WardenHand && Content.Hands.Heavies(w.Tags)) w.HandBlows++;
        else if (Lamps.Board) RiteHeavyCount(w);
    }

    /// <summary>A heavy blow landed: a creature is stunned and thrown twice as far (HitEnemy doubles the push); a boss staggers.</summary>
    void HandHeavy(Enemy e)
    {
        var h = HW;
        HandHeavies++;
        if (e.Boss) AddStagger(e, h.Stagger);
        else if (e.Alive && e.State != EnemyState.Dying)
        {
            var s = e.Status.Ensure(StatusKind.Stun, 0, 1, 0, 0);
            s.T = Math.Max(s.T, h.Stun);
        }
        HandEv(HandKind.Heavy, e.X, e.Z, e.Id);
        // Oath and Bell: a stagger rings the Watch Bell.
        BellOnStagger();
        if (Lamps.Board) LinkFire("heavy");
    }

    /// <summary>A Holy skill struck a champion: a Stone, once per champion per firing.</summary>
    void HandStone(Enemy e, WeaponInst w)
    {
        long key = ((long)(w.Slot + 1) << 32) | (uint)w.Casts;
        if (e.HandStoneKey == key) return;
        e.HandStoneKey = key;
        HandStones++;
        HandEv(HandKind.Stone, e.X, e.Z, e.Id);
        AddStone(true);
    }

    /// <summary>Shield Arm's number when that lamp is lit; the warden Hand's when it isn't (0 with neither).</summary>
    double WallArg(string arg, double fallback, double hand) =>
        Lamps.Has("shield_arm") ? Lamps.Full("shield_arm", arg, fallback) : WardenHand || (Lamps.Board && RiteStones) ? hand : 0;

    /// <summary>Lamps v2: a stone rite is lit, so the wall answers on the Hand's numbers for whoever lit it.</summary>
    bool RiteStones { get { BoardSync(); return riteStone; } }

    /* ---------------------------------------------------------------- reaver -- */

    double HandFrenzyCap => ReaverHand ? HR.Cap : 0;

    /// <summary>Frenzy's attack speed a stack: the lamp's, never below the Hand's (by night the lamp's runs at a quarter).</summary>
    double FrenzyPer() => Math.Max(Lamps.Size("frenzy", "per", 0.01), ReaverHand ? HR.Per : 0);

    /// <summary>How long a lull before Frenzy fades: the lamp's when lit, else the Hand's.</summary>
    double FrenzyFade() => Lamps.Has("frenzy") ? Lamps.Full("frenzy", "fade", 3) : HR.Fade;

    void HandReaverHit(Enemy e)
    {
        if (!e.Status.Has(StatusKind.Bleed) || Time < handFrenzyGate) return;
        handFrenzyGate = Time + HR.Gate;
        double before = frenzy;
        AddFrenzy(1);
        if (frenzy > before) { HandFrenzies++; HandEv(HandKind.Frenzy, e.X, e.Z, e.Id); }
    }

    /// <summary>Below half health her Area skills reach wider (Firing.AreaOf).</summary>
    public double HandAreaMul(WeaponInst w)
    {
        if (!ReaverHand || !w.Tags.Has(Tag.Area)) return 1;
        var h = HR;
        return Player.Hp < MaxHp * h.Below ? 1 + h.Area : 1;
    }

    /* -------------------------------------------------------------- arcanist -- */

    static readonly Tag[] GroundFire = [Tag.Zone, Tag.Fire], GroundFrost = [Tag.Zone, Tag.Frost], GroundArcane = [Tag.Zone, Tag.Arcane];
    StatusPayload? handChill, handMark;

    /// <summary>A Spell killed: its element's ground where the thing fell, and a mark passed on.</summary>
    void HandArcanistKill(Enemy e, WeaponInst? w)
    {
        if (w == null || !w.Tags.Has(Tag.Spell)) return;
        var h = HA;
        var school = w.School;
        if (Content.Hands.GroundName(school) != null) LayHandGround(e, w, school);
        // The mark passes once; the moon's lamps (moonmarked, cold_moon) pass it their own way and further.
        if (e.Status[StatusKind.Mark] is not { } mark) return;
        if (Lamps.Has("moonmarked") || (Lamps.Has("cold_moon") && e.Status.Has(StatusKind.Frozen))) return;
        var next = NearestUnmarked(e, h.Reach);
        if (next == null) return;
        ApplyStatus(next, new StatusPayload(StatusKind.Mark, 1, mark.Power != 0 ? mark.Power : 1, h.MarkSeconds), 0, 2);
        HandMarks++;
        Events.Emit(new Ev.Chain { Points = [e.X, e.Z, next.X, next.Z], School = School.Arcane });
        HandEv(HandKind.Mark, next.X, next.Z, next.Id);
    }

    /// <summary>The arcanist Hand's ground where a thing fell, of a school (fire, frost or arcane): the Hand's, or a ground rite's.</summary>
    void LayHandGround(Enemy e, WeaponInst w, School school)
    {
        var h = HA;
        {
            handGround ??= new GroundZone?[Math.Max(1, h.Cap)];
            var old = handGround[handGroundAt];
            if (old != null && old.Alive && old.Credit == "hand") Zones.Release(old);
            var zn = SpawnZone(Side.Player, e.X, e.Z, h.Radius, h.Seconds, school == School.Fire ? w.Damage * h.Burn : 0, school);
            if (zn != null)
            {
                zn.Credit = "hand";
                zn.Art = "hand_ground_" + (school == School.Fire ? "fire" : school == School.Frost ? "frost" : "moon");
                if (school == School.Fire) zn.Tags = GroundFire;
                else if (school == School.Frost) { zn.Tags = GroundFrost; zn.Status = handChill ??= new StatusPayload(StatusKind.Chill, 1, h.Chill, h.Seconds); }
                else { zn.Tags = GroundArcane; zn.Status = handMark ??= new StatusPayload(StatusKind.Mark, 1, h.Mark, h.MarkSeconds); }
                handGround[handGroundAt] = zn;
                handGroundAt = (handGroundAt + 1) % handGround.Length;
                HandGrounds++;
                HandEv(HandKind.Ground, e.X, e.Z, e.Id);
            }
        }
    }

    Enemy? NearestUnmarked(Enemy from, double r)
    {
        Spatial.Query(from.X, from.Z, r, q);
        Enemy? best = null;
        double bd = r * r;
        foreach (var id in q)
        {
            var o = Enemies.Items[id];
            if (o == from || !Targetable(o) || o.Status.Has(StatusKind.Mark)) continue;
            double d = (o.X - from.X) * (o.X - from.X) + (o.Z - from.Z) * (o.Z - from.Z);
            if (d <= bd) { bd = d; best = o; }
        }
        return best;
    }

    /* --------------------------------------------------------------- stalker -- */

    /// <summary>hand.stalker.second_wind (the hearth's fourth Hand lamp, v2): a true blow on a champion in the window gives
    /// back a share of a dash, once a dash.</summary>
    bool secondWindSpent;
    void HandSecondWind()
    {
        if (secondWindSpent || !HandRule("hand.stalker.second_wind")) return;
        secondWindSpent = true;
        var p = Player;
        int max = RoundInt(Stats.Get(Stat.DashCharges));
        if (p.DashCharges >= max) return;
        p.DashRecharge += Lamps.Full("hand.stalker.second_wind", "share", 0.25) * Abilities.Dash.Recharge;
        if (p.DashRecharge >= Abilities.Dash.Recharge) { p.DashRecharge = 0; p.DashCharges++; }
    }

    void HandOnDash()
    {
        secondWindSpent = false;
        if (StalkerHand) handDashUntil = Time + Abilities.Dash.Time + HS.Seconds;
    }

    bool HandDashOpen => StalkerHand && Time < handDashUntil;

    /// <summary>The pierce a projectile skill gains just after a dash (Firing.PierceOf).</summary>
    public int HandPierce(WeaponInst w) => HandDashOpen && w.Tags.Has(Tag.Projectile) ? HS.Pierce : 0;

    /// <summary>A projectile loosed with the Hand's pierce: counted, and told to the view.</summary>
    public void HandPierced(Projectile pr) { HandPierces++; HandEv(HandKind.Pierce, pr.X, pr.Z); }

    /// <summary>Just after a dash a blow on a champion strikes true.</summary>
    bool HandTrue(Enemy e, in HitOpts o) => (e.Elite || e.Boss) && HandDashOpen && !o.Dot && !o.Summon && (o.Weapon != null || o.Projectile);

    /* ------------------------------------------------------------- on a hit -- */

    /// <summary>What her Hand does as a blow lands (after its damage; before procs see it).</summary>
    void HandOnHit(Enemy e, in HitOpts o, bool heavy)
    {
        if (heavy) HandHeavy(e);
        switch (HandKindNow())
        {
            case 1:
                if ((e.Elite || e.Boss) && o.Weapon is { } w && !o.Summon && w.Tags.Has(Tag.Holy)) HandStone(e, w);
                // hand.warden.heavy_stone (the hearth's fourth Hand lamp, v2): a heavy blow on a champion lays a stone, once a firing.
                else if (heavy && (e.Elite || e.Boss) && o.Weapon is { } hw && !o.Summon && HandRule("hand.warden.heavy_stone")) HandStone(e, hw);
                break;
            case 2:
                if (!o.Dot && !o.Summon && (o.Weapon != null || o.Projectile)) HandReaverHit(e);
                break;
        }
    }
}
