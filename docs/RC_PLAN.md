# Toward a release candidate

A working list, kept in priority order, from a playthrough on a real GPU
(RTX 5080, 1080p, real time) on 2 October 2026. Ticked items are done and
committed. Each visual change is checked in the running game.

## 1. Light and grade (every scene at once)
- [x] Moonlit nights: a cold key that throws shadows, blue-lifted ambient;
      the arena's night brighter still. Fires as the only warmth.
- [x] A warmer, clearer day; the world's mute and volumetric air thinned for
      a camera looking down.
- [ ] Day still reads flat: ground lit head-on with low-contrast textures.
      Normal-map strength, a lower sun, sharper contact shadows.

## 2. Blade and Ember hit hard (the top priority of the brief)
- [ ] The swing: a crescent with a white-hot edge and speed streaks, not a
      flat cream wedge.
- [ ] Hits land: a white flash on what is struck, a flinch, sparks on
      armour, a short hitstop and a little camera kick on heavy blows and
      crits.
- [ ] Crashing Leap and the other big arts: a fast flash then a crater,
      a dust ring and debris; never a screen-filling flat orange disc.
- [ ] Spells (bolts, chains, novas): a brighter core, a coloured halo,
      a trail; chain lightning that forks and flickers rather than a flat
      white line.
- [ ] Sound under every one of these: a layered impact (transient, body,
      tail), pitched by weight.

## 3. The world
- [ ] The campfire (title, creation, prologue): real flames, embers,
      a flicker on the ground; not a blurred sprite blob. Stones and logs
      given texture.
- [ ] Foliage and roofs between the camera and the survivor fade away.
- [ ] Arena ground: from the high camera it reads as flat mud. Variation,
      paths, scorch and bone, grass that catches the moon.
- [ ] The Waystation: the camera sits so high the roofs fill the frame;
      the "Brannog" sign collides with the zone title.

## 4. Story and structure
- [ ] Play the day story and a night arena through end to end, noting where
      dialogue, choices and their outcomes fall short.

## 5. The woman survivor
- [ ] Check her in a real window: title by the fire, creation, holding the
      staff, a fight. A fuller, more striking figure, in keeping with the
      game's art.

## Housekeeping
- [x] Tests: `Items` published its table before it was whole; four tests
      failed at random on a fast machine.
