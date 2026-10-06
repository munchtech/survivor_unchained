p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1f5623590e09883\godot\src\Audio\SoundBridge.cs'
s = open(p, encoding='utf-8').read()


def sub(old, new):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new)


sub('''    int xpStreak;
    double xpT, hostilesNear, beatT;''', '''    int xpStep, swellTier = -1;
    double xpT, hostilesNear, beatT, sweepT, swellT, now;
    /// <summary>The player's kills in the last second and a half, for the swell (S-08).</summary>
    readonly Queue<double> recent = new();
    static readonly int[] SwellAt = [15, 40, 80, 150];
    /// <summary>A crowd melted past a threshold (0..3): the world's response (a kick, a rumble).</summary>
    public Action<int>? Swelled;''')
sub('''        foreach (var e in evs)
        {
            switch (e)
            {''', '''        int stones = 0, fell = 0;
        foreach (var e in evs)
        {
            switch (e)
            {''')
sub('''                case Ev.Kill k when k.Def != "mirror": Sfx.Kill(k.Family, k.Elite, k.Boss, At(k.X, k.Z)); break;''',
    '''                case Ev.Kill k when k.Def != "mirror":
                    Sfx.Kill(k.Family, k.Elite, k.Boss, At(k.X, k.Z));
                    if (k.ByPlayer) { fell++; recent.Enqueue(now); }
                    break;''')
sub('''                case Ev.LevelUp: Sfx.LevelUp(); break;''', '''                case Ev.LevelUp: Sfx.LevelUp(b != null && LevelUp.BlessingNext(b)); break;''')
sub('''                        case PickupKind.Ember: xpStreak++; xpT = 0.7; Sfx.Xp(xpStreak); break;''', '''                        case PickupKind.Ember: stones++; break;''')
sub('''                        case PickupKind.Magnet: Sfx.Dash(); break;''', '''                        case PickupKind.Magnet: Sfx.Lodestone(); sweepT = 3; xpStep = Math.Max(xpStep, 8); break;''')
sub('''                case Ev.Sound snd when snd.Id.StartsWith("tell"): Sfx.Tell(snd.Id); break;
            }
        }
    }''', '''                case Ev.Sound snd when snd.Id.StartsWith("tell"): Sfx.Tell(snd.Id); break;
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
    }''')
sub('''        xpT -= dt;
        if (xpT <= 0) xpStreak = 0;''', '''        now += dt;
        xpT -= dt;
        if (xpT <= 0) xpStep = 0;
        sweepT -= dt;
        if ((swellT -= dt) <= 0) swellTier = -1;''')
open(p, 'w', encoding='utf-8').write(s)
print("ok")
