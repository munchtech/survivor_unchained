from ed import edit
edit(r"logic\Content\Weapons.cs", [
    ('''Catalysts = ["warding"], Mods = new() { Damage = 2.52, Area = 1.15 }, Art = "nova_frost",''',
     '''Catalysts = ["warding"], Mods = new() { Damage = 2.52, Area = 1.15 }, Art = "nova_ward",'''),
    ('''Set = new() { Status = S(Chill, 1, 5, 3) }, Art = "nova_frost" },''',
     '''Set = new() { Status = S(Chill, 1, 5, 3) }, Art = "nova_zero" },'''),
])
# A storm's blow from the sky that no weapon throws (Skybreak's answer, a blessing's bolt): told to
# the view as a bolt, so it is drawn as one (with no art it was a white pillar sixteen metres tall
# over a ring).
edit(r"logic\Sim\Battle.cs", [
    ('''                    ScheduleStrike(hit.X, hit.Z, fx.Radius, BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Storm, fx.School.AsTag()], 0.3 + i * 0.08, null, Side.Player, depth);''',
     '''                    ScheduleStrike(hit.X, hit.Z, fx.Radius, BaseOf(fx.Damage, fx.Basis, ctx), fx.School, [Tag.Storm, fx.School.AsTag()], 0.3 + i * 0.08, null, Side.Player, depth,
                        art: fx.School == School.Storm ? "sky_bolt" : null);'''),
    ('''    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, tags, delay, weapon, owner, depth) { Credit = credit });
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = school, Delay = delay, Art = weapon?.Art, Rank = weapon?.Rank ?? 0 });''',
     '''    /// <param name="art">How the view draws it when no weapon throws it (only a look).</param>
    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0, string? art = null)
    {
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, tags, delay, weapon, owner, depth) { Credit = credit });
        Events.Emit(new Ev.Strike { X = x, Z = z, Radius = r, School = school, Delay = delay, Art = weapon?.Art ?? art, Rank = weapon?.Rank ?? 0 });'''),
])
