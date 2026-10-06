p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\godot\src\Actors\BossViews.cs'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)


rep('''    readonly Node3D lamp, flame;''', '''    readonly Node3D lamp, flame, grip;''')
rep('''        // The lantern hangs from the left fist.
        var at = new BoneAttachment3D { BoneName = "hand_l" };
        view.Person.Skeleton.AddChild(at);
        lamp = LampIron.Make();
        lamp.Position = new Vector3(0, -0.1f, 0);
        at.AddChild(lamp);''', '''        // The lantern hangs from the left fist by its bail, plumb, whatever the arm
        // does (Hang): the grip is the hand's slot, where a held thing is held.
        var at = new BoneAttachment3D { BoneName = "handslot.l" };
        view.Person.Skeleton.AddChild(at);
        grip = new Node3D();
        at.AddChild(grip);
        lamp = LampIron.Make(Bail);
        AddChild(lamp);''')
rep('''    public void Shine(double dt)
    {
        time += dt;
        Visible = true;''', '''    public void Shine(double dt)
    {
        time += dt;
        Visible = true;
        Hang();''')
rep('''    void Light(double g, float ground)
    {''', '''    /// <summary>The bail's length, ring to fist, in the lamp's own measure.</summary>
    const float Bail = 0.07f;

    /// <summary>The lamp hangs straight down from his fist on its bail, turned with him.</summary>
    void Hang()
    {
        float s = view.Person.Root.Scale.X * view.Scale.X;
        lamp.GlobalTransform = new Transform3D(new Basis(Vector3.Up, GlobalRotation.Y).Scaled(Vector3.One * s),
            grip.GlobalPosition - new Vector3(0, Bail * s, 0));
    }

    void Light(double g, float ground)
    {''')
# the gameplay frame hangs it too
rep('''        double g = Glow * (pose == "sleep" ? 0.35 : 1) * (pose == "dead" ? 0 : 1);
        Light(g, (float)y);''', '''        double g = Glow * (pose == "sleep" ? 0.35 : 1) * (pose == "dead" ? 0 : 1);
        Hang();
        Light(g, (float)y);''')
rep('''    public static Node3D Make()
    {''', '''    /// <summary>The lamp-iron; with a bail, an iron loop up from its ring that long, to hang it by.</summary>
    public static Node3D Make(float bail = 0)
    {''')
rep('''        Iron(new TorusMesh { InnerRadius = 0.022f, OuterRadius = 0.032f, Rings = 12, RingSegments = 6 }, new Vector3(0, 0.0f, 0));
        return lamp;''', '''        Iron(new TorusMesh { InnerRadius = 0.022f, OuterRadius = 0.032f, Rings = 12, RingSegments = 6 }, new Vector3(0, 0.0f, 0));
        if (bail > 0)
        {
            // Two thin rods from the ring's sides up to a hook where the fist closes.
            foreach (int side in new[] { -1, 1 })
                Iron(new BoxMesh { Size = new Vector3(0.007f, bail, 0.007f) }, new Vector3(side * 0.02f, bail / 2 + 0.02f, 0));
            Iron(new BoxMesh { Size = new Vector3(0.05f, 0.008f, 0.008f) }, new Vector3(0, bail + 0.02f, 0));
        }
        return lamp;''')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
