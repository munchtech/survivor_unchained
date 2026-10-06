R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'

def edit(path, pairs):
    p = R + '\\' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:70])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Game\Game.cs', [(
    '''        scene.Update(dt);
        {''',
    '''        scene.Update(dt);
        // The survivor's place on screen, for the health drawn under them.
        if (Mode == "play" && Battle is { } fb2)
        {
            var at = new Vector3((float)fb2.Player.X, (float)scene.HeightAt(fb2.Player.X, fb2.Player.Z), (float)fb2.Player.Z);
            hud.Follow(camera.IsPositionBehind(at) ? null : camera.UnprojectPosition(at));
        }
        {'''), (
    '''            hud.Frame(Battle, ch.Gold, Inventory.Count(ch, "health_draught"), (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));''',
    '''            hud.Frame(Battle, ch.Gold, Inventory.Count(ch, "health_draught"), (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));
            hud.MapFrame(MiniView());'''), (
    '''    double tourT = 2;''',
    '''    /// <summary>What the corner map shows now: by day and on the story's roads, not in an arena.</summary>
    MinimapView? MiniView()
    {
        if (zone == null || scene == null || zone is ArenaRun || Battle is not { } b || inTransit) return null;
        float extent = MapScreen.Extent(scene.Data.Meta);
        var seen = World.Zone(zone.Id).TryGetValue("seen", out var f) && f.Str is { Length: Journey.FogN * Journey.FogN } s ? s : new string('0', Journey.FogN * Journey.FogN);
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        var marks = zone.MapMarks().Where(m => m.Kind != MarkKind.Place && (m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)))
            .Select(m => new MiniMark(m.X, m.Z, m.Kind, m.Label)).ToList();
        if (World.Corpse is { } corpse && corpse.Zone == zone.Id) marks.Add(new MiniMark(corpse.X, corpse.Z, MarkKind.Danger, "Your belongings"));
        return new MinimapView(zone.Id, MapScreen.Drawing(scene.Data), extent, seen, Journey.FogN, marks, b.Player.X, b.Player.Z, b.Player.Facing, zone.TimeOf(World) == TimeOfDay.Night);
    }

    double tourT = 2;''')])

edit(r'Ui\MapScreen.cs', [(
    '''    static float Extent(World.ZoneMeta m) =>''',
    '''    public static float Extent(World.ZoneMeta m) =>'''), (
    '''    /// <summary>The zone drawn on paper, once per zone.</summary>
    static ImageTexture Drawing(ZoneData z)''',
    '''    /// <summary>The zone drawn on paper, once per zone (the map and the corner map share it).</summary>
    public static ImageTexture Drawing(ZoneData z)''')])

edit(r'Game\Settings.cs', [(
    '''    public bool Fullscreen = true;''',
    '''    public bool Fullscreen = true;
    /// <summary>The survivor's health drawn under them in a night's fight.</summary>
    public bool UnderBar = true;''')])
print('done')
