import sys, json
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# 1. The toll lowers the music and the world's noise, never the fight's (combat: a telegraph under a duck is a blow unheard).
patch('src/Audio/Synth.cs', [
("""    float voiceMusic = 1, voiceAmb = 1, voiceMusicNow = 1, voiceAmbNow = 1;""",
"""    /// <summary>Hold the music and the world's noise down for a while under a moment that must be
    /// heard over them (a Legendary's toll), never the fight's own sounds, which carry its warnings.</summary>
    public void DuckBeds(float k, double seconds)
    {
        bedDuckUntil = Now + seconds;
        bedDuck = k;
    }

    volatile float bedDuck = 1;
    double bedDuckUntil;
    float bedDuckNow = 1;

    float voiceMusic = 1, voiceAmb = 1, voiceMusicNow = 1, voiceAmbNow = 1;"""),
("""            masterNow += (Master - masterNow) * 0.0002f;""",
"""            masterNow += (Master - masterNow) * 0.0002f;
            float bedTo = t < bedDuckUntil ? bedDuck : 1;
            bedDuckNow += (bedTo - bedDuckNow) * (bedTo < bedDuckNow ? 0.00022f : 0.00005f);"""),
("""                float bus = Level[(int)voice.Bus] * (voice.Bus == Bus.Music ? duckNow * voiceMusicNow : voice.Bus == Bus.Amb ? voiceAmbNow : voice.Bus == Bus.Sfx ? sfxDuckNow : 1);""",
"""                float bus = Level[(int)voice.Bus] * (voice.Bus == Bus.Music ? duckNow * voiceMusicNow * bedDuckNow : voice.Bus == Bus.Amb ? voiceAmbNow * bedDuckNow : voice.Bus == Bus.Sfx ? sfxDuckNow : 1);"""),
])
patch('src/Audio/Sfx.cs', [
("""        if (!faint) a.DuckSfx(0.5f, 0.5);
        // On the interface's bus, so the hush does not swallow it.""",
"""        // The hush is the music's and the world's, never the fight's (combat: a warning under a duck is
        // a blow unheard). On the interface's bus, so the toll carries over the horde.
        if (!faint) a.DuckBeds(0.35f, 1.2);"""),
])

# 2. Above 80% health (combat: in a horde she is almost never at full).
patch('logic/Sim/Stats.cs', [
("""public enum ModWhen { Moving, Still, Night, LowHealth, FullHealth, NearBeasts, InBurning, Shapeshifted, AfterDash }""",
"""/// <summary>Healthy: above four fifths of her health (a price paid while it is easy).</summary>
public enum ModWhen { Moving, Still, Night, LowHealth, FullHealth, NearBeasts, InBurning, Shapeshifted, AfterDash, Healthy }"""),
])
patch('logic/Sim/Battle.cs', [
("""        if (p.Hp >= MaxHp - 0.01) condScratch.Add(ModWhen.FullHealth);""",
"""        if (p.Hp >= MaxHp - 0.01) condScratch.Add(ModWhen.FullHealth);
        if (p.Hp > MaxHp * 0.8) condScratch.Add(ModWhen.Healthy);"""),
])

p = root + '/data/content/items.json'
d = json.loads(open(p, encoding='utf-8').read())
fm = d['items']['forty_one_mouths']
fm['mods'] = [{"stat": "damage", "kind": "inc", "value": -0.15, "source": "item", "when": "healthy"}]
d['items']['iron_helm']['mods'][1]['value'] = 8
fm['downside'] = "Above four fifths of your health you deal 15% less."
o = json.dumps(d, indent=1, ensure_ascii=False) + '\n'
o = o.replace('"tags": [\n    "mark"\n   ]', '"tags": ["mark"]')
open(p, 'w', encoding='utf-8', newline='\n').write(o)

# 3. Armour's make curve softer at the top (combat: a full Heartwrought set was ~75% reduction).
patch('logic/Rpg/Loot.cs', [
("""    /// <summary>A base's numbers the make never scales (a shield's block rank, speed).</summary>""",
"""    /// <summary>A stat's own make curve where the general one is too steep for it (armour saturates).</summary>
    public Dictionary<string, List<double>> Curves = new();
    /// <summary>A base's numbers the make never scales (a shield's block rank, speed).</summary>"""),
("""        var make = MakeOf(Math.Clamp(level ?? 1, 1, Rules.MaxLevel));
        double mult = Rules.MakeMult[(int)make];
        if (BaseOf(def) is { Mods: { } mods })
            foreach (var m in mods)
                o.Add(m.Value > 0 && !Rules.Unscaled.Contains(m.Stat) ? m with { Value = m.Value * mult } : m);""",
"""        var make = MakeOf(Math.Clamp(level ?? 1, 1, Rules.MaxLevel));
        if (BaseOf(def) is { Mods: { } mods })
            foreach (var m in mods)
                o.Add(m.Value > 0 && !Rules.Unscaled.Contains(m.Stat) ? m with { Value = m.Value * Mult(make, m.Stat) } : m);"""),
("""    /* ----------------------------------------------------------- power -- */""",
"""    /// <summary>What the make multiplies a stat by: its own curve, or the general one.</summary>
    public static double Mult(Make make, string stat) =>
        (Rules.Curves.TryGetValue(stat, out var c) ? c : Rules.MakeMult)[(int)make];

    /// <summary>A piece's rules at its make: a flat number in them (a lamp's flare, black water's
    /// bite) grows as its base's numbers do, so a deep copy is not a toy (combat's ask). Rules
    /// reading the blow or the weapon already grow with what they read.</summary>
    public static List<TriggerDef> Triggers(ItemDef def, int? level)
    {
        double k = Mult(MakeOf(Math.Clamp(level ?? 1, 1, Rules.MaxLevel)), "trigger");
        if (def.Triggers == null) return new();
        if (k == 1) return def.Triggers;
        Effect Scale(Effect e) => e switch
        {
            Effect.Nova n when n.Basis == Basis.Flat => n with { Damage = n.Damage * k },
            Effect.Explode x when x.Basis == Basis.Flat => x with { Damage = x.Damage * k },
            Effect.Zone z when z.Basis == Basis.Flat => z with { Dps = z.Dps * k },
            Effect.Strike s when s.Basis == Basis.Flat => s with { Damage = s.Damage * k },
            Effect.Missiles m when m.Basis == Basis.Flat => m with { Damage = m.Damage * k },
            Effect.Chain c when c.Basis == Basis.Flat => c with { Damage = c.Damage * k },
            _ => e,
        };
        return def.Triggers.Select(t => new TriggerDef { On = t.On, Chance = t.Chance, Icd = t.Icd, When = t.When, Text = t.Text, Effects = t.Effects.Select(Scale).ToArray() }).ToList();
    }

    /* ----------------------------------------------------------- power -- */"""),
])
patch('logic/Rpg/Character.cs', [
("""            foreach (var t in def.Triggers ?? new()) kit.Triggers.Add((t, $"item:{it.Uid}"));""",
"""            foreach (var t in Drops.Triggers(def, it.Level)) kit.Triggers.Add((t, $"item:{it.Uid}"));"""),
])
patch('data/content/loot.json', [
("""  "unscaled": ["block", "moveSpeed"],""",
"""  "_curves": "A stat's own make curve where the general one is too steep: armour saturates (armour / (armour + 20)), so a full Heartwrought set at x5.5 was about 75% reduction (combat). 'trigger' scales a piece's flat rule damage (Kell's Lamp by day).",
  "curves": { "armor": [1, 1.8, 2.8, 3.4, 4.0], "trigger": [1, 1.8, 2.8, 4.0, 5.5] },
  "unscaled": ["block", "moveSpeed"],"""),
])
print("ok")
