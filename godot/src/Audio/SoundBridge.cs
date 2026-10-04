using System;
using System.Collections.Generic;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Sound;

/// <summary>What the game is, this frame, as far as sound cares.</summary>
public readonly record struct SoundState(string Mode, string? Zone, TimeOfDay Time, double Px, double Pz, Battle? Battle,
    bool Boss, string? Overlay, Func<double, double, AmbienceMix>? Ambience, Func<double, double, string?>? MusicMood);

/// <summary>
/// Where the game becomes sound (the web game's game/soundBridge.ts).
/// Combat events turn into hits and kills, panned to where they happened and
/// quieter the further off they are; the interface's own moments (a screen
/// opening, a toast, a line of dialogue) turn into its sounds; and every
/// frame the music is told what kind of moment this is and the ambience
/// what kind of place.
/// </summary>
public sealed class SoundBridge
{
    readonly Synth a;
    public readonly Ambience Ambience;
    public readonly Music Music;
    int xpStep, swellTier = -1;
    double xpT, hostilesNear, beatT, sweepT, swellT, now;
    /// <summary>The player's kills in the last second and a half, for the swell (S-08).</summary>
    readonly Queue<double> recent = new();
    static readonly int[] SwellAt = [15, 40, 80, 150];
    /// <summary>A crowd melted past a threshold (0..3): the world's response (a kick, a rumble).</summary>
    public Action<int>? Swelled;
    string? prevOverlay;

    /// <summary>A cinematic's music, over whatever the moment would choose (null: none).</summary>
    public Mood? CineMood;
    public double CineIntensity;

    public SoundBridge(Synth a)
    {
        this.a = a;
        Ambience = new Ambience(a);
        Music = new Music(a);
    }

    /// <summary>Combat events, panned and attenuated from the survivor's position.</summary>
    public void Events(IReadOnlyList<CombatEvent> evs, Battle? b)
    {
        if (!a.Live) return;
        double px = b?.Player.X ?? 0, pz = b?.Player.Z ?? 0;
        Sfx.Where At(double x, double z)
        {
            double d = Math.Sqrt((x - px) * (x - px) + (z - pz) * (z - pz));
            return new Sfx.Where(Math.Clamp((x - px) / 18, -0.8, 0.8), Math.Max(0, 1 - d / 32));
        }
        int stones = 0, fell = 0;
        foreach (var e in evs)
        {
            switch (e)
            {
                case Ev.Hit h when !h.Dot:
                    if (h.Blocked) Sfx.Blocked(At(h.X, h.Z)); else Sfx.Hit(h.School, h.Crit, At(h.X, h.Z));
                    break;
                case Ev.Kill k when k.Def != "mirror":
                    Sfx.Kill(k.Family, k.Elite, k.Boss, At(k.X, k.Z));
                    if (k.ByPlayer) { fell++; recent.Enqueue(now); }
                    break;
                case Ev.PlayerHit ph:
                    if (ph.Dodged) Sfx.Dodge(); else if (ph.Blocked) Sfx.Blocked(); else Sfx.Hurt(ph.Dot ? ph.Amount * 0.4 : ph.Amount);
                    break;
                case Ev.ShieldHit sh: Sfx.Blocked(); if (sh.Broke) Sfx.Shatter(); break;
                case Ev.PlayerHeal hl when hl.Amount > 8: Sfx.Heal(); break;
                case Ev.PlayerDeath: Sfx.Death(); break;
                case Ev.Explosion ex: Sfx.Explosion(ex.Power, At(ex.X, ex.Z)); break;
                case Ev.Nova n: Sfx.Nova(n.School); break;
                case Ev.Slash s: Sfx.Swing(At(s.X, s.Z)); break;
                case Ev.Muzzle m: Sfx.Shoot(m.School, At(m.X, m.Z)); break;
                case Ev.Dash: Sfx.Dash(); break;
                case Ev.PerfectDodge: Sfx.Perfect(); break;
                case Ev.Ability ab: Sfx.Art(ab.Id); break;
                case Ev.Spawn sp: Sfx.Spawn(sp.Style, At(sp.X, sp.Z)); break;
                case Ev.LevelUp: Sfx.LevelUp(b != null && LevelUp.BlessingNext(b)); break;
                case Ev.Evolve ev when !ev.Chest: Sfx.Evolve(); break;
                case Ev.Victory: Sfx.Fall(); break;
                case Ev.Pickup p:
                    switch (p.Kind)
                    {
                        case PickupKind.Ember: stones++; break;
                        case PickupKind.Gold: Sfx.Gold(); break;
                        case PickupKind.Heal: Sfx.Heal(); break;
                        // (A chest sounds as it opens: ChestCeremony.)
                        case PickupKind.Relic: Sfx.Loot(true); break;
                        case PickupKind.Magnet: Sfx.Lodestone(); sweepT = 3; xpStep = Math.Max(xpStep, 8); break;
                    }
                    break;
                case Ev.Sound snd when snd.Id == "door": Sfx.Door(); break;
                case Ev.Sound snd when snd.Id.StartsWith("tell"): Sfx.Tell(snd.Id); break;
            }
        }
        // The stones taken this frame are one voice, a step or a few up the ladder (S-02).
        if (stones > 0)
        {
            bool nearFull = b != null && b.EmberNext > 0 && b.EmberXp / b.EmberNext > 0.85;
            Sfx.Xp(xpStep, stones, nearFull, sweepT > 0);
            xpStep += Math.Min(stones, 3);
            xpT = 0.8;
        }
        // A crowd going down together is heard as one; past each threshold in a second and a half,
        // a swell, a step higher for each higher threshold, never the same one twice in the window.
        if (fell >= 4) Sfx.CrowdFall(fell);
        while (recent.Count > 0 && now - recent.Peek() > 1.5) recent.Dequeue();
        int tier = -1;
        for (int i = 0; i < SwellAt.Length; i++) if (recent.Count >= SwellAt[i]) tier = i;
        if (tier >= 0 && (swellT <= 0 || tier > swellTier))
        {
            Sfx.Swell(tier);
            Swelled?.Invoke(tier);
            swellTier = tier;
            swellT = 1.5;
        }
    }

    public void Toast(Toast t)
    {
        switch (t.Kind)
        {
            case ToastKind.Quest: Sfx.Quest(); break;
            case ToastKind.Relation:
                var words = (t.Text + (t.Sub ?? "")).ToLowerInvariant();
                bool bad = words.Contains("distrust") || words.Contains("dislike") || words.Contains("contempt") || words.Contains("afraid") || words.Contains('-');
                Sfx.Rel(!bad);
                break;
            case ToastKind.Loot: Sfx.Loot((t.Rarity ?? 0) >= 2); break;
            case ToastKind.Lore: Sfx.Discovery(); break;
            case ToastKind.Warning: Sfx.Deny(); break;
        }
    }

    public void Announce(Announcement an, bool boss)
    {
        switch (an.Kind)
        {
            case "danger": Sfx.Stinger(boss ? "boss" : "danger"); break;
            case "zone": Sfx.Stinger("zone"); break;
            case "story": Sfx.Stinger("story"); break;
            case "boon": Sfx.Stinger("triumph"); break;
        }
    }

    /// <summary>A new line of a conversation: a page turned.</summary>
    public void Line() => Sfx.Page();

    double stepX, stepZ, strode;

    /// <summary>What the survivor's feet fall on, zone by zone.</summary>
    static string Ground(string? zone) => zone switch { "waystation" => "concrete", "lowford" => "dirt", _ => "grass" };

    public void Update(double dt, SoundState s)
    {
        // Footsteps: one a stride, while walking in the world.
        double moved = Math.Sqrt((s.Px - stepX) * (s.Px - stepX) + (s.Pz - stepZ) * (s.Pz - stepZ));
        stepX = s.Px; stepZ = s.Pz;
        if (s.Mode == "play" && s.Overlay == null && moved < 3)
        {
            strode += moved;
            if (strode > 1.7) { strode = 0; Sfx.Step(Ground(s.Zone)); }
        }
        now += dt;
        xpT -= dt;
        if (xpT <= 0) xpStep = 0;
        sweepT -= dt;
        if ((swellT -= dt) <= 0) swellTier = -1;
        // Screens opening and closing.
        var o = s.Overlay;
        if (o != prevOverlay)
        {
            if (o != null && o is not ("dialogue" or "draft" or "chapter" or "chest")) Sfx.Open();
            else if (o == null && prevOverlay is not (null or "dialogue" or "chest")) Sfx.Close();
            if (o == "chapter") Sfx.Stinger("story");
            prevOverlay = o;
        }
        // What kind of moment is this?
        var b = s.Battle;
        int hostile = 0;
        if (b != null && s.Mode == "play")
            foreach (var e in b.Enemies.Items)
                if (e.Alive && e.Disposition == Disposition.Hostile && Math.Abs(e.X - s.Px) < 20 && Math.Abs(e.Z - s.Pz) < 20
                    && (e.X - s.Px) * (e.X - s.Px) + (e.Z - s.Pz) * (e.Z - s.Pz) < 400) hostile++;
        hostilesNear += (hostile - hostilesNear) * Math.Min(1, dt * (hostile > hostilesNear ? 2 : 0.35));
        Mood mood;
        if (s.Mode is "title" or "create") mood = Mood.Title;
        else if (s.Boss) mood = Mood.Boss;
        else if (hostilesNear > 4) mood = Mood.Combat;
        else if (s.MusicMood?.Invoke(s.Px, s.Pz) != null) mood = Mood.Mystery;
        else if (s.Zone == "waystation") mood = s.Time == TimeOfDay.Night ? Mood.Night : Mood.Town;
        else if (s.Time == TimeOfDay.Night || s.Zone == "lowford") mood = Mood.Night;
        else mood = Mood.Explore;
        // A cinematic scores itself: its mood and intensity, silence included.
        if (CineMood is Mood cm) mood = cm;
        Music.Set(mood);
        Music.Intensity = CineMood != null ? CineIntensity : s.Boss ? 1 : Math.Min(1, hostilesNear / 18);
        // Close to the end, your own heart: faster the worse it gets.
        double hp = b != null && s.Mode == "play" && b.Combat && b.Player.Alive && o == null ? b.Player.Hp / b.MaxHp : 1;
        if (hp < 0.3)
        {
            beatT -= dt;
            if (beatT <= 0)
            {
                double urgency = 1 - hp / 0.3;
                Sfx.Heartbeat(urgency);
                beatT = 1.05 - urgency * 0.4;
            }
        }
        else beatT = 0;
        // A chest opening has the room: the score steps well back for its jingle.
        a.DuckMusic(o == "dialogue" ? 0.55f : o == "chest" ? 0.3f : o != null && o != "draft" ? 0.7f : 1);
        Music.Update(dt);
        Ambience.Set(s.Mode == "play" && s.Ambience != null ? s.Ambience(s.Px, s.Pz) : s.Mode == "title" ? TitleAir : new AmbienceMix());
        Ambience.Update(dt);
    }

    /// <summary>The title's fire on the Low Ford road: wind, the fire, crickets.</summary>
    static readonly AmbienceMix TitleAir = new() { Wind = 0.5, Fire = 0.8, Crickets = 0.4, Owl = 0.3 };
}
