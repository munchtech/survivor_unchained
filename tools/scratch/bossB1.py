import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# --- Events: telegraph kinds, the camera turned, a Break.
edit('logic/Sim/Events.cs', [
("public enum TelegraphShape { Circle, Line, Cone, Ring }",
 """public enum TelegraphShape { Circle, Line, Cone, Ring }

/// <summary>What a telegraph says (docs/bosses/MECHANICS.md section 2), in colour and
/// edge both: a blow is coming here (amber, filled), this ground stays bad
/// (violet, hatched), stand here (pale blue, dashed), this will be solid (grey,
/// a hard edge).</summary>
public enum TelegraphKind { Blow, Ground, Safe, Wall }"""),
("""        public int Id; public TelegraphShape Shape; public double X, Z; public double? X1, Z1; public double Radius;
        public double? Width, Angle, Arc; public double Duration; public bool Hostile;""",
 """        public int Id; public TelegraphShape Shape; public double X, Z; public double? X1, Z1; public double Radius;
        public double? Width, Angle, Arc; public double Duration; public bool Hostile;
        public TelegraphKind Kind;
        /// <summary>A ring's inner edge (a band, not a disc).</summary>
        public double Inner;
        /// <summary>A boss's: drawn above the survivor's own effects, and named over the boss.</summary>
        public bool Boss; public string? Label;"""),
("""    public sealed class Shake : CombatEvent { public double Amount; }""",
 """    public sealed class Shake : CombatEvent { public double Amount; }
    /// <summary>The camera turned to something for a moment (a boss's arrival, its fall).</summary>
    public sealed class Focus : CombatEvent { public double X, Z, Duration; }
    /// <summary>A boss's phase broken: the damage past its mark, shown as one number.</summary>
    public sealed class Break : CombatEvent { public double X, Z, Amount; public int Enemy; }"""),
])

# --- The creature: the gate, the Break, the stagger.
edit('logic/Sim/Entities.cs', [
("""    /// <summary>Raised from a grave by one of its own: it carries no ember (raising is never a farm).</summary>
    public bool Raised;""",
 """    /// <summary>Raised from a grave by one of its own: it carries no ember (raising is never a farm).</summary>
    public bool Raised;
    /// <summary>A boss's gate: health stops here, and what would have gone past it is
    /// its Break (docs/SKILLS_DESIGN.md, "Bosses").</summary>
    public double HpFloor, Overflow;
    /// <summary>A boss's stagger bar (0..1), filled by what would lock a lesser creature;
    /// held while staggered, and resisting it for a while after.</summary>
    public double Stagger, StaggeredT, StaggerResistT;"""),
])

edit('logic/Sim/Battle.cs', [
# Spawning: a boss by the arena's say, not only by its kind.
("""        public bool Elite;
        public string? Tag;""",
 """        public bool Elite;
        /// <summary>A boss whatever its kind (the arena's ruler is its people's champion made boss).</summary>
        public bool Boss;
        public string? Tag;"""),
("""        e.Boss = def.Boss;""", """        e.Boss = def.Boss || o.Boss;"""),
("""        e.ThawT = 0;
        e.Raised = false;""",
 """        e.ThawT = 0;
        e.Raised = false;
        e.HpFloor = e.Overflow = e.Stagger = e.StaggeredT = e.StaggerResistT = 0;"""),
# The gate.
("""        double before = e.Hp;
        e.Hp -= dmg;""",
 """        double before = e.Hp;
        e.Hp -= dmg;
        // A boss's gate: it stops at its phase's mark; the rest is its Break.
        if (e.HpFloor > 0 && e.Hp < e.HpFloor) { e.Overflow += e.HpFloor - e.Hp; e.Hp = e.HpFloor; }"""),
# Staggered, a boss takes a quarter more.
("""        if (e.Boss || e.Elite) dmg *= o.BossDamage ?? o.Weapon?.Def.BossDamage ?? 1;""",
 """        if (e.Boss || e.Elite) dmg *= o.BossDamage ?? o.Weapon?.Def.BossDamage ?? 1;
        if (e.StaggeredT > 0) dmg *= 1.25;"""),
# Knockback into a boss fills its stagger instead.
("""        if (o.Knockback != 0 && !e.Boss && e.Def.Behavior != Behavior.Stationary)""",
 """        if (o.Knockback != 0 && e.Boss) AddStagger(e, 0.004 * o.Knockback * st.Get(Stat.Knockback));
        if (o.Knockback != 0 && !e.Boss && e.Def.Behavior != Behavior.Stationary)"""),
# The hit hook (a boss's weakness breaks its channel).
("""        if (e.Hp <= 0 && e.Alive && e.State != EnemyState.Dying) KillEnemy(e, true, o.Weapon, depth);
        else ArtOnHit(e);
        return dmg;""",
 """        if (e.Boss) Hooks.OnBossHit?.Invoke(e, school, dmg);
        if (e.Hp <= 0 && e.Alive && e.State != EnemyState.Dying) KillEnemy(e, true, o.Weapon, depth);
        else ArtOnHit(e);
        return dmg;"""),
# Five chill stacks stagger a boss rather than freezing it.
("""                if (cur.Stacks >= 5 && !e.Boss && e.ThawT <= 0)""",
 """                if (cur.Stacks >= 5 && e.Boss) { cur.Stacks = 2; AddStagger(e, 0.12); }
                if (cur.Stacks >= 5 && !e.Boss && e.ThawT <= 0)"""),
# Stuns, fear and charm fill a boss's stagger.
("""            case StatusKind.Stun:
            case StatusKind.Fear:
            case StatusKind.Charm:
                if (e.Boss && p.Kind != StatusKind.Stun) return;""",
 """            case StatusKind.Stun:
            case StatusKind.Fear:
            case StatusKind.Charm:
                // A boss is not locked: what would lock it fills its stagger bar instead.
                if (e.Boss) { AddStagger(e, p.Kind == StatusKind.Stun ? 0.06 + 0.12 * dur : 0.08); return; }"""),
("""        if (e.ThawT > 0) e.ThawT -= dt;
    }""",
 """        if (e.ThawT > 0) e.ThawT -= dt;
        if (e.StaggeredT > 0) e.StaggeredT -= dt;
        if (e.StaggerResistT > 0) e.StaggerResistT -= dt;
    }

    /// <summary>A boss's stagger bar fills (a quarter as fast while it resists);
    /// full, the boss is held for 3 s, taking a quarter more, whatever it was
    /// doing broken, and then resists for 15 s.</summary>
    public void AddStagger(Enemy e, double amount)
    {
        if (!e.Boss || e.StaggeredT > 0 || !e.Alive) return;
        e.Stagger += amount * (e.StaggerResistT > 0 ? 0.25 : 1) * Rules.StaggerTaken;
        if (e.Stagger < 1) return;
        e.Stagger = 0;
        e.StaggeredT = 3;
        e.StaggerResistT = 18;
        e.State = EnemyState.Stunned;
        e.StateT = 3;
        e.Vx = e.Vz = 0;
        Hooks.OnBossStagger?.Invoke(e);
        Events.Emit(new Ev.Announce { Title = "Staggered", Tone = Tone.Boon });
        Events.Emit(new Ev.Shake { Amount = 0.25 });
    }"""),
# Hooks.
("""    /// <summary>Something damaged a tagged collider (a barrel, a bramble wall, a ward).</summary>
    public Action<string, int, School, double, double, double>? OnHitProp;""",
 """    /// <summary>Something damaged a tagged collider (a barrel, a bramble wall, a ward).</summary>
    public Action<string, int, School, double, double, double>? OnHitProp;
    /// <summary>A boss was hit (its school and the damage), for a weakness that breaks a channel.</summary>
    public Action<Enemy, School, double>? OnBossHit;
    /// <summary>A boss's stagger bar filled.</summary>
    public Action<Enemy>? OnBossStagger;"""),
])

# Shaped blows from the enemy side: a telegraph, a delay, a hit on the survivor that a dash can slip.
s = open('logic/Sim/Battle.cs', encoding='utf-8').read()
anchor = """    /* ======================================================= projectiles == */"""
assert s.count(anchor) == 1
blows = '''    /// <summary>A blow the enemy side has marked on the ground: where, what shape,
    /// how long until it lands, and what it does then.</summary>
    public sealed class EnemyBlow
    {
        public TelegraphShape Shape;
        public TelegraphKind Kind = TelegraphKind.Blow;
        public double X, Z, X1, Z1, Radius, Inner, Width = 1, Angle, Arc;
        public double Delay, T, Damage;
        public School School = School.Physical;
        public string Source = "";
        public Enemy? From;
        /// <summary>Slowed by it (a fraction of pace, for a time).</summary>
        public double Slow, SlowFor;
        public string? Label;
        /// <summary>What it leaves, or does besides, when it lands.</summary>
        public Action<Battle>? After;
        public bool Hit(double x, double z, double r)
        {
            double dx = x - X, dz = z - Z, d = Math.Sqrt(dx * dx + dz * dz);
            switch (Shape)
            {
                case TelegraphShape.Circle: return d <= Radius + r * 0.5;
                case TelegraphShape.Ring: return d <= Radius + r * 0.5 && d >= Inner - r * 0.5;
                case TelegraphShape.Cone:
                {
                    if (d > Radius + r * 0.5) return false;
                    if (d < 0.6) return true;
                    double a = Math.Atan2(dz, dx) - Angle;
                    while (a > Math.PI) a -= Math.PI * 2;
                    while (a < -Math.PI) a += Math.PI * 2;
                    return Math.Abs(a) <= Arc / 2;
                }
                default:
                {
                    double lx = X1 - X, lz = Z1 - Z, len2 = lx * lx + lz * lz;
                    double t = len2 > 0 ? Math.Clamp((dx * lx + dz * lz) / len2, 0, 1) : 0;
                    double px = X + lx * t - x, pz = Z + lz * t - z;
                    return Math.Sqrt(px * px + pz * pz) <= Width / 2 + r * 0.5;
                }
            }
        }
    }

    readonly List<EnemyBlow> blows = new();
    int blowIds = 1;
    public IReadOnlyList<EnemyBlow> Blows => blows;

    /// <summary>Mark a blow and let it land after its delay: it hurts the survivor
    /// if they are still in its shape (a blow slipped by a dash in time is a
    /// perfect dodge), and only them.</summary>
    public EnemyBlow Blow(EnemyBlow b)
    {
        b.T = b.Delay;
        blows.Add(b);
        Events.Emit(new Ev.Telegraph
        {
            Id = 900000 + blowIds++, Shape = b.Shape, Kind = b.Kind, X = b.X, Z = b.Z, X1 = b.X1, Z1 = b.Z1, Radius = b.Radius, Inner = b.Inner,
            Width = b.Width, Angle = b.Angle, Arc = b.Arc, Duration = b.Delay, Hostile = true, Boss = b.From?.Boss == true, Label = b.Label,
        });
        return b;
    }

    void UpdateBlows(double dt)
    {
        for (int i = blows.Count - 1; i >= 0; i--)
        {
            var b = blows[i];
            b.T -= dt;
            if (b.T > 0) continue;
            blows.RemoveAt(i);
            var p = Player;
            if (b.Damage > 0 || b.Slow > 0)
            {
                double cx = b.Shape == TelegraphShape.Line ? (b.X + b.X1) / 2 : b.X, cz = b.Shape == TelegraphShape.Line ? (b.Z + b.Z1) / 2 : b.Z;
                if (b.Kind == TelegraphKind.Blow) Events.Emit(new Ev.Explosion { X = cx, Z = cz, Radius = Math.Max(1.2, b.Shape == TelegraphShape.Line ? b.Width : b.Radius * 0.6), School = b.School, Power = 0.8 });
                if (p.Alive && b.Hit(p.X, p.Z, p.Radius))
                {
                    if (b.Damage > 0) HurtPlayer(b.Damage, b.School, b.Source, b.From, telegraphed: true);
                    if (b.Slow > 0 && p.Iframes <= 0.45) SlowPlayer(b.Slow, b.SlowFor);
                }
            }
            b.After?.Invoke(this);
        }
    }

'''
s = s.replace(anchor, blows + anchor)
old_tick = """    void UpdateStrikes(double dt)
    {"""
assert s.count(old_tick) == 1
open('logic/Sim/Battle.cs', 'w', encoding='utf-8').write(s)
print('ok')
