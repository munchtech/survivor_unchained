"""The boss's bar steps back while the boss stands under it (GameHud.BossAt, Game's frame)."""
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot'
p = W + r'\src\Ui\GameHud.cs'
s = open(p, encoding='utf-8').read()
a = '''    public void Follow(Vector2? at)
    {'''
b = '''    Rect2? bossOnScreen;
    float bossBarA = 1;

    /// <summary>Where the boss himself stands on the screen (his feet to his head; null: none, or off it).
    /// Under his own bar at the top of the picture, the bar steps back so he is seen: with the view
    /// leant toward him a boss far up the screen still stood under his name.</summary>
    public void BossAt(Rect2? body) => bossOnScreen = body;

    public void Follow(Vector2? at)
    {'''
assert s.count(a) == 1, 'follow'
s = s.replace(a, b)
a = '''        TopClear = bossBox.Visible ? bossBox.GetGlobalRect().End.Y + 8 : 118;'''
b = '''        TopClear = bossBox.Visible ? bossBox.GetGlobalRect().End.Y + 8 : 118;
        bool under = bossBox.Visible && bossOnScreen is Rect2 body && bossBox.GetGlobalRect().Grow(6).Intersects(body);
        bossBarA = Mathf.MoveToward(bossBarA, under ? 0.38f : 1, dt * 4);
        bossBox.Modulate = Colors.White with { A = bossBarA };'''
assert s.count(a) == 1, 'topclear'
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)

p = W + r'\src\Game\Game.cs'
s = open(p, encoding='utf-8').read()
a = '''            cam.Toward = zone is StoryNight bn && bn.Now == StoryNight.Stage.Boss && bn.BossScript?.E is { Alive: true } be && be.State != SurvivorUnchained.Sim.EnemyState.Dying
                ? new Vector3((float)be.X, 0, (float)be.Z) : null;'''
b = '''            cam.Toward = zone is StoryNight bn && bn.Now == StoryNight.Stage.Boss && bn.BossScript?.E is { Alive: true } be && be.State != SurvivorUnchained.Sim.EnemyState.Dying
                ? new Vector3((float)be.X, 0, (float)be.Z) : null;
            // (his body on the screen, so his bar can step back from over him)
            hud.BossAt(BossBody());'''
assert s.count(a) == 1, 'toward'
s = s.replace(a, b)
a = '''    int clickI;
'''
b = '''    int clickI;

    /// <summary>The fight's boss on the screen, feet to head (null: no boss, or behind the camera).</summary>
    Rect2? BossBody()
    {
        var script = zone switch { StoryNight sn => sn.BossScript, ArenaRun a => a.BossScript, MapRun m => m.BossScript, _ => null };
        if (script?.E is not { Alive: true } e || scene == null) return null;
        var camera = GetViewport().GetCamera3D();
        float y = (float)scene.HeightAt(e.X, e.Z), tall = 2.6f * (float)(e.Def.Scale ?? 1);
        var feet = new Vector3((float)e.X, y, (float)e.Z);
        var head = feet + Vector3.Up * tall;
        if (camera == null || camera.IsPositionBehind(feet) || camera.IsPositionBehind(head)) return null;
        Vector2 f = camera.UnprojectPosition(feet), h = camera.UnprojectPosition(head);
        float w = Mathf.Max(60, (f.Y - h.Y) * 0.8f);
        return new Rect2(h.X - w / 2, h.Y, w, Mathf.Max(1, f.Y - h.Y));
    }
'''
assert s.count(a) == 1, 'clickI'
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
