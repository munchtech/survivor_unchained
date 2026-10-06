PAIRS = [
('''    /// <summary>The Greeting: a wide sweep of the greataxe, half round him.</summary>
    void Greeting()
    {
        Hold(1.0);
        Cone(4.5, 150, 1.0, 1.4, "The Greeting");
    }''', '''    /// <summary>The Greeting: a wide sweep of the greataxe, half round him.</summary>
    void Greeting(Action? then = null)
    {
        Hold(1.0, then);
        Cone(4.5, 150, 1.0, 1.4, "The Greeting");
    }'''),
('''    void Hook(bool laugh, Action? then = null, double mark = 1.2)
    {''', '''    void Hook(bool laugh, double mark = 1.2, Action? then = null)
    {'''),
('''            Lane(ex, ez, ex + dx * 7, ez + dz * 7, 2.2, mark, 2.0, "The Hook");
            Hold(mark, () => Stuck(then));''', '''            Lane(ex, ez, ex + dx * 7, ez + dz * 7, 2.2, mark, 2.0, "The Hook");
            Hold(mark, () => { if (then != null) then(); else Stuck(null); });'''),
('''    void Chain()
    {
        Hook(laugh: false, mark: 1.3, then: null);
        // The Hook's own Stuck is replaced by the rest of the chain.
        chainNext = true;
    }

    bool chainNext;
''', '''    void Chain() => Hook(laugh: false, mark: 1.3, then: () => Greeting(Charge));
'''),
]
