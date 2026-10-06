p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\GameHud.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""    /// <summary>The console's middle: the globe at its left, the art's ring at its right.</summary>
    const float ConsoleX = 600, ConsoleW = 720;""", """    /// <summary>The console's span: as wide as the skills it holds (six places by night, what is carried by day),
    /// the globe at its left end, the art's ring at its right.</summary>
    float consoleX = 600, consoleW = 720;
    int consolePlaces = 6;
    Control consolePlate = null!, arsenal = null!, hands = null!;""")
rep("""        var plate = new Panel { Position = new Vector2(ConsoleX, 1080 - 98), Size = new Vector2(ConsoleW, 130), MouseFilter = Control.MouseFilterEnum.Ignore };
        plate.AddThemeStyleboxOverride("panel", UiArt.Frame("console", OrnateBox.Make(OrnateBox.Kind.Plate, 0)));
        combat.AddChild(plate);
        globe = new Globe(66) { Position = new Vector2(ConsoleX - 150, 1080 - 156) };""", """        var plate = new Panel { Position = new Vector2(consoleX, 1080 - 98), Size = new Vector2(consoleW, 130), MouseFilter = Control.MouseFilterEnum.Ignore };
        plate.AddThemeStyleboxOverride("panel", UiArt.Frame("console", OrnateBox.Make(OrnateBox.Kind.Plate, 0)));
        combat.AddChild(plate);
        consolePlate = plate;
        globe = new Globe(66) { Position = new Vector2(consoleX - 150, 1080 - 156) };""")
rep("""        statuses.Position = new Vector2(ConsoleX - 150, 1080 - 156 - 40);""", """        statuses.Position = new Vector2(consoleX - 150, 1080 - 156 - 40);""")
rep("""        col.Position = new Vector2(ConsoleX, 1080 - 14 - 150);
        col.Size = new Vector2(ConsoleW, 150);""", """        col.Position = new Vector2(consoleX, 1080 - 14 - 150);
        col.Size = new Vector2(consoleW, 150);
        arsenal = col;""")
rep("""        h.Position = new Vector2(ConsoleX + ConsoleW + 14, 1080 - 14 - 150);
        h.Size = new Vector2(460, 150);
        combat.AddChild(h);""", """        h.Position = new Vector2(consoleX + consoleW + 14, 1080 - 14 - 150);
        h.Size = new Vector2(460, 150);
        combat.AddChild(h);
        hands = h;""")
rep("""        var at = b.Combat ? new Vector2(ConsoleX - 150, 1080 - 156) : new Vector2(30, 1080 - 30 - globe.Size.Y);""", """        var at = b.Combat ? new Vector2(consoleX - 150, 1080 - 156) : new Vector2(30, 1080 - 30 - globe.Size.Y);""")
rep("""        // At night the empty places promise six; by day there are only what is carried.
        int empties = weapons.GetChildren().OfType<EmptySlot>().Count(), want = ember ? Math.Max(0, 6 - b.Weapons.Count) : 0;""", """        // At night the empty places promise six; by day there are only what is carried, and the console fits them.
        int empties = weapons.GetChildren().OfType<EmptySlot>().Count(), want = ember ? Math.Max(0, 6 - b.Weapons.Count) : 0;
        int places = Math.Max(2, b.Weapons.Count + want);
        if (places != consolePlaces)
        {
            consolePlaces = places;
            consoleW = Math.Max(300, places * 77 + 70);
            consoleX = (1920 - consoleW) / 2;
            consolePlate.Position = new Vector2(consoleX, 1080 - 98);
            consolePlate.Size = new Vector2(consoleW, 130);
            arsenal.Position = new Vector2(consoleX, 1080 - 14 - 150);
            arsenal.Size = new Vector2(consoleW, 150);
            hands.Position = new Vector2(consoleX + consoleW + 14, 1080 - 14 - 150);
            globe.Position = new Vector2(consoleX - 150, 1080 - 156);
            statuses.Position = globe.Position + new Vector2(0, -40);
        }""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
