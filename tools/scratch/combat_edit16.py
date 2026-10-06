W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'src\Ui\GameHud.cs', [
('''    string bossMarks = "";
    ColorRect? bossStagger;''',
'''    string bossMarks = "";
    ColorRect? bossStagger, bossStaggerGroove;'''),
('''        // The stagger bar: a thin line under the health, filled by what would lock a lesser creature.
        if (bossStagger == null)
        {
            bossStagger = new ColorRect { Color = Hex("#e8c860"), Position = new Vector2(0, 17), Size = new Vector2(0, 4), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossTrack.AddChild(bossStagger);
        }
        bossStagger.Visible = bar.IsBoss && bar.Stagger > 0;
        bossStagger.Size = new Vector2(w * (float)Math.Clamp(bar.Stagger, 0, 1), 4);''',
'''        // The stagger bar: a thin line under the health, filled by what would lock a lesser
        // creature. Its groove shows from the first second, so the player learns it is there.
        // (It sat inside the health track, which clips, and was never seen.)
        if (bossStagger == null)
        {
            bossStaggerGroove = new ColorRect { Color = Hex("#1a1410") with { A = 0.85f }, Position = new Vector2(1, 76), Size = new Vector2(w, 5), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStaggerGroove);
            bossStagger = new ColorRect { Color = Hex("#e8c860"), Position = new Vector2(1, 76), Size = new Vector2(0, 5), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStagger);
        }
        bossStaggerGroove!.Visible = bar.IsBoss;
        bossStagger.Visible = bar.IsBoss && bar.Stagger > 0;
        bossStagger.Size = new Vector2(w * (float)Math.Clamp(bar.Stagger, 0, 1), 5);'''),
])

# no stagger while untouchable (a phase's turn, laid down, going down the hole)
edit(r'logic\Sim\Battle.cs', [
('''        if (!e.Boss || e.StaggeredT > 0 || !e.Alive) return;''',
'''        // Untouchable (a phase turning, laid down, going down the hole) is not staggerable:
        // a stagger spent there was a quarter more damage nobody could deal.
        if (!e.Boss || e.StaggeredT > 0 || !e.Alive || e.TakenMul <= 0) return;'''),
])
print("ok")
