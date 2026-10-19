# 1d. Water and shore

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\04_water_shore.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** water that shows its depth and its edges: the bed in the shallows, dark in the deep, foam wherever it touches something, a flow you can read, and the moon's or the lamps' light in it.

Tier 2. The ford is the Prologue's set piece: three cinematics (C02, C03, C04 A) and the Warden fight happen in or beside it, so its water is on screen for minutes.

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Titan Quest II, play camera ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_3ad166efac3643159ba951f8a4f302cb9adf751b.1920x1080.jpg)) | The shallows show the bed and darken with depth. Foam lines the rocks and the shore, and wet stone darkens at the waterline. |
| Titan Quest II ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_92c90785127ec754416c2fca3e086d6edcb55831.1920x1080.jpg)) | A stream at the play camera. White water marks where it runs fast over the stones, and the banks blend into it with no hard edge. |
| Kena ([Steam](https://store.steampowered.com/app/1954200), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1954200/ss_a7521a54970aee953dad96d1acedbaa3a927e4d5.1920x1080.jpg)) | Still water at night under mist. Small lights glow in the haze and the far shore fades. Simple water, dressed by light and mist. |
| The Witcher 3 ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_9436c0e2632ea9e2db315fc3483d8f9ff3facc8d.1920x1080.jpg)) | Wading at night. The waterline cuts each figure, and the dark water takes the light's color. |
| The Witcher 3 ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_19c03c2b997d3a393fc629fd42f55ddb4a3d8dd0.1920x1080.jpg)) | Calm water mirrors the dusk sky, broken by ripples and by the boat's wake. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/play_33.jpg` (the ford at the play camera) | One flat blue plane, with no depth, bed, flow or shore. The white egg lamps are its brightest points. |
| `frames/c03_s12.jpg` (C03 s12) | A flat tiled plane with a hard edge against the terrain. No shore, foam or flow. |
| `frames/c04a_sa1.jpg` (C04 A sa1) | Milky water with no reflection. The stones have no wake and no wet line. |

## The trick

1. Color from depth: read the scene depth under the surface. Clear over the bed in the shallows (0-0.4 m), tinted and dark past about 1.5 m.
2. Shore and contact foam from the depth difference (Sea of Thieves): a soft band where the water meets land, stones and legs. It also hides the edge.
3. A flow map (Valve: two layers half a phase apart): the river runs downstream and bends round the stones. One painted texture for the ford.
4. Reflections: screen-space on the water only, falling back to the area's probe. At night the lamps and the moon streak across it.
5. Wet banks: a band of darker, smoother terrain and stone just above the waterline. At night, mist lies low on the water.

## DONE means (at the play and close-up cameras, at 1:1)

- No visible line where water meets land, at any camera.
- From the play camera the ford reads as shallow where you can cross (the bed shows) and dark where it is deep.
- The flow's direction reads within two seconds of play, and every stone and wading leg has a ring of foam.
- The lamps and the moon reflect as streaks. Actors in the water show a waterline and ripples (C02 s7, s11).
- Cost: one water material for every river and pond (page 2's budget).

Owners: The tutorial environment lead (the water shader, shore and contact foam, the ford's flow map, wet banks); cinematics (wading depth, mist and reflections per shot).

## Sources
- Shore foam by depth comparison: "It is also added around objects that intersect the water surface within a camera centered window using depth buffer comparisons" (Ang, [The Technical Art of Sea of Thieves, SIGGRAPH 2018](https://history.siggraph.org/wp-content/uploads/2022/09/2018-Talks-Ang_The-Technical-Art-of-Sea-of-Thieves.pdf)).
- Flow maps: "Each layer is offset half a phase so we can hide the restart for each layer" (Vlachos, [Water Flow in Portal 2, SIGGRAPH 2010](https://cdn.fastly.steamstatic.com/apps/valve/2010/siggraph2010_vlachos_waterflow.pdf)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
