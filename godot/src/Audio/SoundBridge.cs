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
    int xpStreak;
    double xpT, hostilesNear, beatT;
    string? prevOverlay;

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
        foreach (var e in evs)
        {
            switch (e)
            {
                case Ev.Hit h when !h.Dot:
                    if (h.Blocked) Sfx.Blocked(At(h.X, h.Z)); else Sfx.Hit(h.School, h.Crit, At(h.X, h.Z));
                    break;
                case Ev.Kill k: Sfx.Kill(k.Family, k.Elite, k.Boss, At(k.X, k.Z)); break;
                case Ev.PlayerHit ph:
                    if (ph.Dodged) Sfx.Dodge(); else if (ph.Blocked) Sfx.Blocked(); else Sfx.Hurt(ph.Amount);
                    break;
                case Ev.ShieldHit sh: Sfx.Blocked(); if (sh.Broke) Sfx.Shatter(); break;
                case Ev.PlayerHeal hl when hl.Amount > 8: Sfx.Heal(); break;
                case Ev.PlayerDeath: Sfx.Death(); break;
                case Ev.Explosion ex: Sfx.Explosion(ex.Power, At(ex.X, ex.Z)); break;
                case Ev.Nova n: Sfx.Nova(n.School); break;
                case Ev.Slash s: Sfx.Swing(At(s.X, s.Z)); break;
                case Ev.Muzzle m: Sfx.Shoot(m.School, At(m.X, m.Z)); break;
                case Ev.Dash: Sfx.Dash(); break;
                case Ev.Ability: Sfx.Bash(); break;
                case Ev.Spawn sp: Sfx.Spawn(sp.Style, At(sp.X, sp.Z)); break;
                case Ev.LevelUp: Sfx.LevelUp(); break;
                case Ev.Evolve: Sfx.Evolve(); break;
                case Ev.Pickup p:
                    switch (p.Kind)
                    {
                        case PickupKind.Ember: xpStreak++; xpT = 0.7; Sfx.Xp(xpStreak); break;
                        case PickupKind.Gold: Sfx.Gold(); break;
                        case PickupKind.Heal: Sfx.Heal(); break;
                        case PickupKind.Chest or PickupKind.Relic: Sfx.Loot(true); break;
                        case PickupKind.Magnet: Sfx.Dash(); break;
                    }
                    break;
                case Ev.Sound snd when snd.Id == "door": Sfx.Door(); break;
            }
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

    public void Update(double dt, SoundState s)
    {
        xpT -= dt;
        if (xpT <= 0) xpStreak = 0;
        // Screens opening and closing.
        var o = s.Overlay;
        if (o != prevOverlay)
        {
            if (o != null && o is not ("dialogue" or "draft" or "chapter")) Sfx.Open();
            else if (o == null && prevOverlay is not (null or "dialogue")) Sfx.Close();
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
        Music.Set(mood);
        Music.Intensity = s.Boss ? 1 : Math.Min(1, hostilesNear / 18);
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
        a.DuckMusic(o == "dialogue" ? 0.55f : o != null && o != "draft" ? 0.7f : 1);
        Music.Update(dt);
        Ambience.Set(s.Mode == "play" && s.Ambience != null ? s.Ambience(s.Px, s.Pz) : s.Mode == "title" ? TitleAir : new AmbienceMix());
        Ambience.Update(dt);
    }

    /// <summary>The title's fire on the Low Ford road: wind, the fire, crickets.</summary>
    static readonly AmbienceMix TitleAir = new() { Wind = 0.5, Fire = 0.8, Crickets = 0.4, Owl = 0.3 };
}
