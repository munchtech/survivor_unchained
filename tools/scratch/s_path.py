PAIRS = [
('''                if (nav == null || navT <= 0 && (Math.Abs(wx - navX) + Math.Abs(wz - navZ) > 2 || openedAt != zone.BeatIx * 10 + (int)zone.Now))
                {
                    nav = new NavField(map, b, wx, wz, zone.Place.Bounds());
                    (navX, navZ, navT, openedAt) = (wx, wz, 0.5, zone.BeatIx * 10 + (int)zone.Now);
                }
                var pl = b.Player;
                if (Math.Abs(wx - pl.X) + Math.Abs(wz - pl.Z) < 2) way = (wx, wz);
                else
                {
                    // On down the way, three metres ahead (a way point at her feet, pressed to a wall, is
                    // no reason to stand still).
                    var (ox, oz) = nav.Onward(pl.X, pl.Z);
                    double dx = ox - pl.X, dz = oz - pl.Z, dl = Math.Sqrt(dx * dx + dz * dz);
                    if (dl < 0.2) { dx = wx - pl.X; dz = wz - pl.Z; dl = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz)); }
                    way = (pl.X + dx / dl * 3, pl.Z + dz / dl * 3);
                }''',
'''                var pl = b.Player;
                bool replan = nav == null || navT <= 0 && (Math.Abs(wx - navX) + Math.Abs(wz - navZ) > 2 || openedAt != zone.BeatIx * 10 + (int)zone.Now);
                // Pushed well off her way, or no nearer in three seconds: the way again from where she is.
                if (!replan && path.Count > 0 && (pathI < path.Count && Math.Abs(path[pathI].X - pl.X) + Math.Abs(path[pathI].Z - pl.Z) > 5 || t - progressT > 3)) replan = true;
                if (replan)
                {
                    if (nav == null || Math.Abs(wx - navX) + Math.Abs(wz - navZ) > 0.5 || openedAt != zone.BeatIx * 10 + (int)zone.Now) nav = new NavField(map, b, wx, wz, zone.Place.Bounds());
                    (navX, navZ, navT, openedAt) = (wx, wz, 0.5, zone.BeatIx * 10 + (int)zone.Now);
                    path = nav.Path(pl.X, pl.Z);
                    pathI = 0;
                    progressT = t;
                    bestToGo = double.MaxValue;
                }
                double toGo = Math.Abs(wx - pl.X) + Math.Abs(wz - pl.Z);
                if (toGo < bestToGo - 0.5) { bestToGo = toGo; progressT = t; }
                if (toGo < 2 || path.Count == 0) way = (wx, wz);
                else
                {
                    // Down the way she planned: past the points she has reached, toward the furthest still in a
                    // straight line from her, three metres ahead. (The field's slope alone flipped from one side
                    // of her to the other in a neck, and she stood there for minutes.)
                    while (pathI < path.Count - 1 && Math.Abs(path[pathI].X - pl.X) + Math.Abs(path[pathI].Z - pl.Z) < 1.2) pathI++;
                    int best = pathI;
                    for (int k = pathI; k < Math.Min(path.Count, pathI + 14); k++) if (nav!.Clear(pl.X, pl.Z, path[k].X, path[k].Z)) best = k;
                    double dx = path[best].X - pl.X, dz = path[best].Z - pl.Z, dl = Math.Sqrt(dx * dx + dz * dz);
                    if (dl < 0.2) { dx = wx - pl.X; dz = wz - pl.Z; dl = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz)); }
                    way = (pl.X + dx / dl * 3, pl.Z + dz / dl * 3);
                }'''),
('''        int openedAt = -1;''', '''        int openedAt = -1;
        var path = new List<(double X, double Z)>();
        int pathI = 0;
        double progressT = 0, bestToGo = double.MaxValue;'''),
]
