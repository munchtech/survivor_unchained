"""The light follows the clock itself, not the turns (run from godot/)."""
p = "src/Game/GameClock.cs"
s = open(p, encoding="utf-8").read()
reps = [
("""/* The day's clock on screen (docs/design/STORY_NIGHTS_AND_TIME.md §2): free play moves it
 * (Journey.PassTime), and each turn is staged here. The light crosses to the next time of day over
 * a minute; dusk is the town's evening call and the night's fight named; nightfall calls it, and""",
"""/* The day's clock on screen (docs/design/STORY_NIGHTS_AND_TIME.md §2): free play moves it
 * (Journey.PassTime), and each turn is staged here. The light is read off the clock itself, each
 * time of day's air crossed into the next over its edges (the dark comes in before the word
 * "night", not after it); dusk is the town's evening call and the night's fight named; nightfall calls it, and"""),
("""    /// <summary>The light between two times of day, crossed over a minute or so.</summary>
    AtmospherePreset? airFrom, airTo;
    double airT, airLen, airGradeT;""",
"""    /// <summary>The light as the clock last set it: whether it was mid-crossing, and when the colour
    /// grade (a lookup table rebuilt) may next be redone.</summary>
    bool airMoving, airDirty = true;
    double airGradeT;"""),
("""    /// <summary>The time of day turns: the light crosses over `seconds`, the lamps and the place
    /// follow, the corner of the screen says so.</summary>
    void Turn(TimeOfDay to, double seconds)
    {
        if (zone == null || scene == null) return;
        airFrom = air.Current;
        airTo = zone.AtmosphereFor(to);
        airT = 0;
        airLen = seconds;
        airGradeT = 0;
        scene.View.SetNight(to == TimeOfDay.Night);""",
"""    /// <summary>The time of day turns: the lamps and the place follow, the corner of the screen says
    /// so (the light is the clock's, BlendAir).</summary>
    void Turn(TimeOfDay to, double seconds)
    {
        if (zone == null || scene == null) return;
        scene.View.SetNight(to == TimeOfDay.Night);"""),
("""    /// <summary>A turn of the light, a frame: the sky and the air every frame, the colour grade
    /// (a lookup table rebuilt) twice a second.</summary>
    void BlendAir(double dt)
    {
        if (airTo == null || airFrom == null) return;
        airT += dt;
        double k = Math.Clamp(airT / Math.Max(0.01, airLen), 0, 1);
        k = k * k * (3 - 2 * k);
        airGradeT -= dt;
        bool grade = airGradeT <= 0 || k >= 1;
        if (grade) airGradeT = 0.5;
        air.Set(Atmospheres.Blend(airFrom, airTo, k), grade);
        if (k >= 1) airTo = null;
    }

    /// <summary>The light set outright (a skip, a new place): any turn under way is dropped.</summary>
    void StopBlend() => airTo = null;""",
"""    /// <summary>The air at a point on the clock: dawn warms into day over its first minute and a
    /// half, day goes gold over the first minute of dusk, and the dark comes in over the last half
    /// minute of dusk and the first of night, so the word "night" lands in the dark. True while
    /// crossing.</summary>
    (AtmospherePreset Air, bool Moving) AirAt(ZoneRuntime z, double s)
    {
        static double K(double s, double a, double b) { double k = Math.Clamp((s - a) / (b - a), 0, 1); return k * k * (3 - 2 * k); }
        AtmospherePreset A(TimeOfDay t) => z.AtmosphereFor(t);
        const double DawnEnds = 30, DayFull = 90, GoldFull = DayClock.DuskAt + 60, DarkFrom = DayClock.NightAt - 30, DarkFull = DayClock.NightAt + 30;
        if (s < DawnEnds) return (A(TimeOfDay.Dawn), false);
        if (s < DayFull) return (Atmospheres.Blend(A(TimeOfDay.Dawn), A(TimeOfDay.Day), K(s, DawnEnds, DayFull)), true);
        if (s < DayClock.DuskAt) return (A(TimeOfDay.Day), false);
        if (s < GoldFull) return (Atmospheres.Blend(A(TimeOfDay.Day), A(TimeOfDay.Dusk), K(s, DayClock.DuskAt, GoldFull)), true);
        if (s < DarkFrom) return (A(TimeOfDay.Dusk), false);
        if (s < DarkFull) return (Atmospheres.Blend(A(TimeOfDay.Dusk), A(TimeOfDay.Night), K(s, DarkFrom, DarkFull)), true);
        return (A(TimeOfDay.Night), false);
    }

    /// <summary>The light, a frame: read off the clock wherever the clock runs; the sky and the air
    /// every frame while it crosses, the colour grade twice a second, nothing while it holds.</summary>
    void BlendAir(double dt)
    {
        if (zone is not { ClockRuns: true } || !Journey.ClockStarted) return;
        DayClock.Sync(World);
        var (a, moving) = AirAt(zone, World.Clock);
        if (!moving && !airMoving && !airDirty) return;
        airGradeT -= dt;
        bool grade = airGradeT <= 0 || !moving || airDirty;
        if (grade) airGradeT = 0.5;
        air.Set(a, grade);
        airMoving = moving;
        airDirty = false;
    }

    /// <summary>The light set outright (a skip, a new place): the clock's air is put back at once.</summary>
    void StopBlend() => airDirty = true;"""),
]
for a, b in reps:
    assert a in s, a[:70]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
