from ed import edit
edit(r"src\Fx\BattleFx.Story.cs", [
    ("""    // The way out: where, how far, and when it last pulsed.
    Vector3 wayAt;
    float wayReach;
    double waySeen = -10;

    static readonly Color WayCold = new(0.32f, 0.52f, 1.0f);""",
     """    // The way out: where, how far, when it first and last pulsed.
    Vector3 wayAt;
    float wayReach;
    double waySeen = -10, wayFirst = -10;

    static readonly Color WayCold = new(0.2f, 0.4f, 1.0f);"""),
    ("""        wayAt = V(e.X, Y(e.X, e.Z), e.Z);
        wayReach = (float)e.Radius;
        waySeen = time;
        return true;""",
     """        wayAt = V(e.X, Y(e.X, e.Z), e.Z);
        wayReach = (float)e.Radius;
        if (time - waySeen > 3) wayFirst = time;
        waySeen = time;
        return true;"""),
    ("""        // It breathes while its pulse keeps coming (a second and a half after the last).
        float way = (float)Mathf.Clamp(1 - (time - waySeen - 1.3) / 0.6, 0, 1);
        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.9f);""",
     """        // It breathes while its pulse keeps coming (a second and a half after the last), and comes
        // only once the fall has landed, as its prompt does: at the night's peak it ringed her in
        // pale light over the column.
        float way = (float)(Mathf.Clamp(1 - (time - waySeen - 1.3) / 0.6, 0, 1) * Mathf.Clamp((time - wayFirst - 2.4) / 1.2, 0, 1));
        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.5f);"""),
])
