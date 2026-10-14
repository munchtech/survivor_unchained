using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Phase 6a: The Branding (moonweaver, Strike, Clear; docs/design/CLASSES.md §3.6, §7's phase-6 plan). She closes her
 * hand and everything in reach wears a crescent; the brands burst outward from her by distance, the boss's last and
 * hardest, and each death passes a mark on to the next thing standing, which bursts in its turn. The bursts and the
 * passes run on their own clock after the press (Second Brand's echo and The Eye outlive the Strike's 1.1 s).
 * Events (Ev.Flare Blow): "brand" per crescent (TX/TZ, Target; with nothing near, ground points in rings across the
 * reach), "burst" per brand as it goes (Radius its splash; the last of the wave carries the big hitstop), "pass" per
 * passed mark (X/Z where it left, TX/TZ and Target where it lands), "eye" per burst of The Eye. */
public sealed partial class Battle
{
    /// <summary>A brand waiting to burst: on whom (or a ground point), when (seconds of the sim's clock), how hard.</summary>
    sealed class Brand
    {
        public Enemy? On;
        public int Id = -1;
        public double X, Z, At, Share, Radius;
        public bool Boss, Last, Dead, Pass, Done;
        public double FromX, FromZ;
    }

    readonly List<Brand> brands = new();
    /// <summary>Things a mark has passed to this press (each takes one), and how many have passed.</summary>
    readonly HashSet<int> brandPassedTo = new();
    int brandPasses;
    /// <summary>The Eye: the boss whose brand stays open, until when, and how many times it has burst again.</summary>
    Enemy? eyeOn;
    int eyeId = -1, eyeBursts;
    double eyeUntil;
    /// <summary>Second Brand: when the brand comes again (the sim's clock; 0 none), and its strength.</summary>
    double secondBrandAt;

    /// <summary>The brand (its one blow, at "first"): everything in reach is marked and its burst is set by its distance
    /// from her, the boss's last; with nothing near, the crescents print on the ground in rings and burst there.</summary>
    void BrandingBlow(FlareDef f, bool last)
    {
        BrandAll(f, 1, true);
        if (FlareMod("branding.second")) secondBrandAt = Time + f.BeatAt("second", 1.0);
    }

    void BrandAll(FlareDef f, double strength, bool first)
    {
        var p = Player;
        double reach = flareReach, t0 = Time - f.BeatAt("first", 0.45);
        double a = f.BeatAt("burstFirst", 0.75), b = f.BeatAt("burstLast", 1.0), bossAt = f.BeatAt("bossBurst", 1.1);
        double r = f.Arg("burstRadius", 2) * (FlareMod("branding.deep") ? f.Arg("deep", 1.5) : 1) * FlareGrow(f);
        var near = HostilesInRadius(p.X, p.Z, reach).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        var set = new List<Brand>();
        int hitstop = first ? FlareHitstop(f, false) : 0;
        foreach (var e in near.OrderBy(e => Dist(e.X, e.Z, p.X, p.Z)))
        {
            double d = Dist(e.X, e.Z, p.X, p.Z);
            bool boss = e.Boss && FlareCanHurt(e);
            if (e.Boss && !boss) continue;
            ApplyStatus(e, new StatusPayload(StatusKind.Mark, 1, 1, f.Arg("markSeconds", 4)), 0);
            set.Add(new Brand
            {
                On = e, Id = e.Id, X = e.X, Z = e.Z, Boss = boss, Radius = boss ? 0 : r,
                At = t0 + (boss ? bossAt : a + (b - a) * Math.Clamp(d / Math.Max(1, reach), 0, 1)),
                Share = strength * (boss ? f.Arg("bossBurst", 1.5) : f.Arg("burst", 1.5)),
            });
            FlareBlowEvent(f, "brand", false, e.X, e.Z, e, 0, hitstop: hitstop);
            hitstop = 0;
        }
        if (set.Count == 0)
        {
            // Nothing near: crescents print on the ground across her reach, ring by ring, and burst there in the same ripple.
            int rings = (int)f.Arg("emptyRings", 3);
            for (int ring = 1; ring <= rings; ring++)
            {
                double rr = reach * (ring - 0.35) / rings;
                int n = 4 + 4 * ring;
                for (int k = 0; k < n; k++)
                {
                    double ang = flareAngle + Math.PI * 2 * k / n + ring * 0.4;
                    double x = p.X + Math.Cos(ang) * rr, z = p.Z + Math.Sin(ang) * rr;
                    set.Add(new Brand { X = x, Z = z, Radius = r, At = t0 + a + (b - a) * rr / Math.Max(1, reach), Share = 0 });
                    FlareBlowEvent(f, "brand", false, x, z, null, 0, hitstop: hitstop);
                    hitstop = 0;
                }
            }
        }
        // The last word: the boss's burst, or the farthest brand's with no boss.
        if (first && set.Count > 0) set.OrderByDescending(x => x.At).First().Last = true;
        brands.AddRange(set);
    }

    /// <summary>The brands burst on their times, passed marks land, Second Brand comes again; runs after the Strike ends.</summary>
    void TickBrands()
    {
        if (secondBrandAt > 0 && Time >= secondBrandAt && Flare is { Id: "the_branding" } sf)
        {
            secondBrandAt = 0;
            // The echo: brands again where she stands now, its bursts quieter.
            var was0 = credit;
            credit = "flare";
            BrandAll(sf, sf.Arg("secondShare", 0.6), false);
            credit = was0;
        }
        if (brands.Count == 0) return;
        var f = Flare;
        if (f == null) { brands.Clear(); return; }
        var was = credit;
        credit = "flare";
        // In time order: a burst may kill, and a kill passes a mark that lands a hop later.
        foreach (var br in brands.Where(x => !x.Done && Time >= x.At - 1e-9).OrderBy(x => x.At).ToList()) Burst(f, br);
        brands.RemoveAll(x => x.Done);
        credit = was;
    }

    void Burst(FlareDef f, Brand br)
    {
        br.Done = true;
        var host = br.On != null && !br.Dead && br.On.Id == br.Id && br.On.Alive && br.On.State != EnemyState.Dying ? br.On : null;
        double x = host?.X ?? br.X, z = host?.Z ?? br.Z;
        if (br.Pass)
            // The mark arcs from the fallen to the next (the view's thin silver arc), and bursts as it lands.
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Blow, Id = f.Id, X = br.FromX, Z = br.FromZ, TX = x, TZ = z, Target = host?.Id ?? 0, Part = "pass", Clutch = flareClutch, Radius = br.Radius });
        if (host != null && br.Share > 0) FlareHit(host, br.Share, f.School, br.Boss ? 0 : 0.8, Player.X, Player.Z);
        // Its splash takes the lesser things round it; a boss takes only its own brand.
        if (br.Radius > 0 && br.Share > 0)
            ForEachHostileInRadius(x, z, br.Radius, (e, d) =>
            {
                if (e == host || e.Boss || !e.Alive || e.State == EnemyState.Dying) return;
                FlareHit(e, f.Arg("splash", 0.35) * (br.Share / Math.Max(1e-9, f.Arg("burst", 1.5))), f.School, 0.6, x, z);
            });
        if (br.Boss && host != null && FlareMod("branding.eye"))
        {
            eyeOn = host;
            eyeId = host.Id;
            eyeBursts = 0;
            eyeUntil = Time + f.Arg("eyeSeconds", 6);
        }
        FlareBlowEvent(f, "burst", br.Last, x, z, host, br.Boss ? f.Arg("bossRadius", 3) * FlareGrow(f) : br.Radius,
            hitstop: br.Last ? FlareHitstop(f, true) : 0);
    }

    /// <summary>A branded thing fell: its brand's mark passes to the nearest lesser thing still standing within "passRange"
    /// that hasn't taken one this press, which bursts a hop later (and passes again if it falls). The Eye: while the
    /// boss's brand stays open, a marked thing falling near the boss passes its mark to the boss, which bursts again.</summary>
    void BrandOnKilled(Enemy e)
    {
        if (Flare is not { Id: "the_branding", Staged: true } f) return;
        if (eyeOn != null && (Time > eyeUntil || eyeOn.Id != eyeId || !eyeOn.Alive || eyeOn.State == EnemyState.Dying)) eyeOn = null;
        bool branded = false;
        foreach (var br in brands)
            // (a brand stays in the list until the tick it burst in ends: a death by its own burst still passes)
            if (br.On == e && br.Id == e.Id) { br.Dead = true; br.X = e.X; br.Z = e.Z; branded = true; }
        bool inWave = branded || brandPassedTo.Contains(e.Id);
        if (eyeOn != null && e != eyeOn && e.Status.Has(StatusKind.Mark) && eyeBursts < (int)f.Arg("eyeMax", 10)
            && Dist(e.X, e.Z, eyeOn.X, eyeOn.Z) <= f.Arg("eyeRange", 8) * FlareGrow(f))
        {
            eyeBursts++;
            var eye = eyeOn;
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Blow, Id = f.Id, X = e.X, Z = e.Z, TX = eye.X, TZ = eye.Z, Target = eye.Id, Part = "pass", Clutch = flareClutch });
            var was = credit;
            credit = "flare";
            FlareHit(eye, f.Arg("eye", 0.25), f.School, 0, e.X, e.Z);
            credit = was;
            FlareBlowEvent(f, "eye", false, eye.X, eye.Z, eye, f.Arg("bossRadius", 3) * FlareGrow(f), hitstop: (int)f.BeatAt("hitstopEye", 1));
            return;
        }
        if (!inWave || e.Boss || brandPasses >= (int)f.Arg("passMax", 24)) return;
        var next = HostilesInRadius(e.X, e.Z, f.Arg("passRange", 6) * FlareGrow(f))
            .Where(o => o != e && !o.Boss && o.Alive && o.State != EnemyState.Dying && !brandPassedTo.Contains(o.Id) && !brands.Any(b => !b.Done && b.On == o && b.Id == o.Id))
            .OrderBy(o => Dist(o.X, o.Z, e.X, e.Z)).FirstOrDefault();
        if (next == null) return;
        brandPasses++;
        brandPassedTo.Add(next.Id);
        ApplyStatus(next, new StatusPayload(StatusKind.Mark, 1, 1, f.Arg("markSeconds", 4)), 0);
        brands.Add(new Brand
        {
            On = next, Id = next.Id, X = next.X, Z = next.Z, Pass = true, FromX = e.X, FromZ = e.Z,
            At = Time + f.BeatAt("hop", 0.1), Share = f.Arg("pass", 0.75), Radius = f.Arg("burstRadius", 2) * (FlareMod("branding.deep") ? f.Arg("deep", 1.5) : 1) * FlareGrow(f),
        });
    }

    /// <summary>At the press: a new wave of passes (the brands of an earlier press keep their own).</summary>
    void BrandingPress()
    {
        brandPassedTo.Clear();
        brandPasses = 0;
        secondBrandAt = 0;
    }
}
