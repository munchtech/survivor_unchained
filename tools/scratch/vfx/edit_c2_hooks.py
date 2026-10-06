from ed import edit
edit(r"src\Fx\BattleFx.cs", [
    ("""                case Ev.Telegraph e:
                {
                    if (DigMark(e)) break;
""", """                case Ev.Telegraph e:
                {
                    if (WayOut(e) || DigMark(e)) break;
                    Winded(e);
"""),
    ("""        StepDig(fdt);
        Projectiles(b, fdt, now);
""", """        StepDig(fdt);
        StepDeadfalls(fdt);
        StepPanting(fdt);
        Projectiles(b, fdt, now);
"""),
])
edit(r"src\Fx\BattleFx.Loot.cs", [
    ("""            Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, s.Motes""", """            Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, s.Motes"""),
    ("""        lootLight!.End();
        for (int i = lampsLit; i < lootLamps.Length; i++) lootLamps[i].Visible = false;""", """        StoryLights();
        lootLight!.End();
        for (int i = lampsLit; i < lootLamps.Length; i++) lootLamps[i].Visible = false;"""),
])
edit(r"src\Game\Game.cs", [
    ("""        scene.Fx.Boss = zone switch { ArenaRun ar => ar.BossScript, MapRun mr => mr.BossScript, StoryNight sn => sn.BossScript, _ => null };
""", """        scene.Fx.Boss = zone switch { ArenaRun ar => ar.BossScript, MapRun mr => mr.BossScript, StoryNight sn => sn.BossScript, _ => null };
        // A story night's deadfalls and where they burn, for the look of a fed fire.
        scene.Fx.Deadfalls = zone is StoryNight dn ? dn.Fires : null;
        scene.Fx.FireSpots = scene.Fx.Deadfalls != null ? scene.View.Data.Meta.Fires : null;
"""),
])
