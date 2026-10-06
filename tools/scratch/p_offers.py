PAIRS = [
("""/// <summary>Who lives in a map: the rank and file (weighted), the boss, and
/// the gear that answers them (slayers, resistances).</summary>
public sealed record Denizens(string Id, string Name, (string Def, double Weight)[] Horde, string Boss, string BossName, string BossTitle, string[] Lean,
    (string Def, double Weight, double From)[] Arena, string Champion);""",
"""/// <summary>Who lives in a map: the rank and file (weighted), the boss, and
/// the gear that answers them (slayers, resistances). In an arena: its kinds by the minute
/// they may join (Arena), its champion, the Signs its champions wear from the first, and the
/// stretches of the night (Stretches).</summary>
public sealed record Denizens(string Id, string Name, (string Def, double Weight)[] Horde, string Boss, string BossName, string BossTitle, string[] Lean,
    (string Def, double Weight, double From)[] Arena, string Champion, string[] Signs, Stretch[] Stretches);

/// <summary>A stretch of an arena's night (docs/SKILLS_DESIGN.md, "Encounters"): at its minute of a
/// thirty-minute night, a miniboss comes wearing the stretch's verb; the kinds that carry the verb
/// (Joins) join the horde only once it has come (or a little after its minute, if it was held
/// back), and champions may wear its Signs from then. The owner: "mechanics that ramp along with the
/// level time and don't appear till certain mini bosses and minion types show up".</summary>
public sealed record Stretch(double At, string Miniboss, string[] Joins, string[] Signs);"""),
("""        new("pack", "the Pack", new[] { ("wolf", 5.0), ("wolf_blighted", 2.0), ("boar", 1.0) }, "boss_pack", "The Pack-Mother", "Alpha of the Deep Wood", ["wolfbane", "of_the_wolf"],
            [("wolf", 5, 0), ("boar", 2, 4), ("wolf_blighted", 3, 9)], "wolf_alpha"),
        new("dead", "the Risen", new[] { ("risen", 5.0), ("risen_warrior", 2.0), ("risen_archer", 2.0), ("grave_caller", 0.4) }, "boss_dead", "The Barrow Lord", "Who Would Not Lie Down", ["gravebane", "of_the_grave", "hallowed"],
            [("risen", 5, 0), ("risen_archer", 2, 3), ("risen_warrior", 3, 7), ("grave_caller", 0.6, 13)], "barrow_knight"),
        new("lamplings", "the Lamplings", new[] { ("lampling", 5.0), ("lampling_sapper", 1.5) }, "boss_lamplings", "The Ganger", "Foreman of the Deep Dig", ["lampsnuffer", "of_the_salamander"],
            [("lampling", 5, 0), ("lampling_sapper", 3.5, 4)], "lampling"),
        new("kerchiefs", "the Kerchiefs", new[] { ("footpad", 5.0), ("pillager", 2.0), ("bruiser", 1.2) }, "boss_kerchiefs", "The Red Hand", "Warlord of the Ravine", ["watchmans", "sturdy"],
            [("footpad", 5, 0), ("pillager", 2.5, 4), ("bruiser", 2, 9)], "enforcer"),""",
"""        // Each night's stretches at 3, 7, 12, 16 and 22 minutes: just after the experience lead's
        // releases (ArenaPacing), one verb each, shown first on a miniboss.
        new("pack", "the Pack", new[] { ("wolf", 5.0), ("wolf_blighted", 2.0), ("boar", 1.0) }, "boss_pack", "The Pack-Mother", "Alpha of the Deep Wood", ["wolfbane", "of_the_wolf"],
            [("wolf", 5, 0), ("boar", 2, 3), ("wolf_runner", 2.5, 7), ("wolf_blighted", 3, 12), ("boar_slurry", 1.5, 16), ("wolf_howler", 0.4, 22)], "wolf_alpha",
            ["swift"],
            [
                new(3, "mb_old_tusk", ["boar"], ["ironbound"]),                    // the charge
                new(7, "mb_whitethroat", ["wolf_runner"], []),                     // the ring
                new(12, "mb_blight_mother", ["wolf_blighted"], ["volatile", "brood"]), // the burst
                new(16, "mb_outflow_sow", ["boar_slurry"], ["kindled"]),           // the slurry
                new(22, "mb_caller", ["wolf_howler"], ["bannered"]),               // the howl
            ]),
        new("dead", "the Risen", new[] { ("risen", 5.0), ("risen_warrior", 2.0), ("risen_archer", 2.0), ("grave_caller", 0.4) }, "boss_dead", "The Barrow Lord", "Who Would Not Lie Down", ["gravebane", "of_the_grave", "hallowed"],
            [("risen", 5, 0), ("risen_archer", 2, 3), ("risen_warrior", 3, 7), ("legionary", 1.5, 7), ("bone_heap", 1.5, 12), ("drowned", 1.2, 16), ("grave_caller", 0.6, 22), ("risen_bell", 0.4, 22)], "barrow_knight",
            ["ironbound"],
            [
                new(3, "mb_old_quarrel", ["risen_archer"], []),                    // the volley
                new(7, "mb_decurion", ["risen_warrior", "legionary"], ["shielded"]), // the shield line
                new(12, "mb_the_heap", ["bone_heap"], ["brood"]),                 // the heap
                new(16, "mb_drowned_reeve", ["drowned"], ["rimed"]),              // the cold
                new(22, "mb_ford_bell", ["grave_caller", "risen_bell"], ["gravebound", "bannered"]), // the bell
            ]),
        new("lamplings", "the Lamplings", new[] { ("lampling", 5.0), ("lampling_sapper", 1.5) }, "boss_lamplings", "The Ganger", "Foreman of the Deep Dig", ["lampsnuffer", "of_the_salamander"],
            [("lampling", 5, 0), ("lampling_wick", 3, 3), ("lampling_sapper", 3.5, 7), ("lampling_lamp", 1.5, 12), ("lampling_fuse", 1.2, 16)], "lampling",
            ["swift"],
            [
                new(3, "mb_wick_mother", ["lampling_wick"], []),                   // the swarm from below
                new(7, "mb_bombardier", ["lampling_sapper"], ["kindled"]),         // the pots
                new(12, "mb_lamplighter", ["lampling_lamp"], ["ironbound"]),       // the fans of flame
                new(16, "mb_fuse_boss", ["lampling_fuse"], ["volatile"]),          // the crates
                new(22, "mb_gaffer", [], ["brood"]),                               // the ground opens
            ]),
        new("kerchiefs", "the Kerchiefs", new[] { ("footpad", 5.0), ("pillager", 2.0), ("bruiser", 1.2) }, "boss_kerchiefs", "The Red Hand", "Warlord of the Ravine", ["watchmans", "sturdy"],
            [("footpad", 5, 0), ("pillager", 2.5, 3), ("levy_pike", 2, 7), ("bruiser", 1.5, 12), ("levy_crossbow", 1.5, 16), ("kerchief_drummer", 0.3, 22)], "enforcer",
            ["swift"],
            [
                new(3, "mb_firepot_nan", ["pillager"], ["kindled"]),               // the pots
                new(7, "mb_pike_captain", ["levy_pike"], []),                      // the pikes
                new(12, "mb_barn_door", ["bruiser"], ["shielded", "ironbound"]),   // the wall
                new(16, "mb_levy_sergeant", ["levy_crossbow"], []),                // the volley
                new(22, "mb_drum_major", ["kerchief_drummer"], ["bannered"]),      // the drum
            ]),"""),
]
