p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot\src\Actors\Visuals.cs"
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


rep('''    const string GroundSlam = "Slam";''', '''    const string GroundSlam = "Slam";
    /// <summary>A crossbow's aim (FolkClips.Crowd): down on one knee and the stock to the cheek; and the
    /// shot that ends it, the kick and the rise.</summary>
    static Clips Kneels(Clips c) => c with { Aim = "KneelAim", Shot = "KneelShot" };''')
rep('''                new Held { Right = "crossbow" }, Shamble("Pistol_Idle_Loop", "Pistol_Shoot", "Pistol_Idle_Loop", cast: Rally)),''',
    '''                new Held { Right = "crossbow" }, Kneels(Shamble("Pistol_Idle_Loop", "Pistol_Shoot", "Pistol_Idle_Loop", cast: Rally))),''')
rep('''            // A bruiser: bare-chested behind a round shield, an axe.''', '''            // A levy crossbowman: the pillager's red hood, a crossbow, and the kneel to shoot.
            "kerchief_crossbow" => new(visual, P(Sex.Male, "ranger", hood: true, beard: true, hairColor: "#3a2618", skin: "#c4945e", cloth: Kerchief),
                new Held { Right = "crossbow" }, Kneels(Fight("Jog_Fwd_Loop", "Pistol_Idle_Loop", "Pistol_Shoot", "Pistol_Idle_Loop", cast: null))),
            // A bruiser: bare-chested behind a round shield, an axe.''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
