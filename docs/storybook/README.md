# The storybook player

Drawn act cinematics (the owner's "storybook", Diablo III's touchstone): painted plates in layers, slow camera moves across them in 2.5D, living touches, ink transitions, scored and voiced through the game's own systems. One JSON file per storybook, `godot/data/storybook/<id>.json`. Code: `godot/logic/Storybook` (format, timing, camera, lens: plain C#, tested), `godot/src/Storybook` (the player), `godot/shaders/storybook`, `godot/src/Game/GameStory.cs` (the hooks).

## Format

```jsonc
{ "id": "sb00", "conversation": "sb_stay_where_they_reach",
  "live": false,                 // a new journey plays it only when true (the default); false while its plates are placeholders (SB00 now). --storybook <id> still plays it
  "canvas": [3200, 1800],        // the plates' reference frame, px (16:9; the 2.39:1 bars crop it)
  "grain": 0.05, "vignette": 0.3, // the finish over everything
  "skip": {"from": 1.5, "hold": 0.8},
  "plates": [ ... ],
  "cues": [ ... ],               // at absolute times
  "end": 89.5 }                  // black after the last plate until then
```

Times are seconds; positions and sizes are canvas px. A plate's own times (camera, grade, layer keys, frames, touches, cues) are from its `at`.

**Plates in time.** A plate's `at` is when its transition in **starts**; the plate before it is drawn on until that transition **ends**. At most two plates are mixed: the newest one coming in over the one it replaces (the first plate comes in over black). A plate with `out` fades to black over the last `out.dur` before its `until`. Gaps between plates are black.

```jsonc
{ "id": "p1", "at": 2.5, "until": 11.0,
  "in":  {"kind": "ink", "dur": 1.6, "origin": [0.42, 0.55], "map": "res://...png", "edge": "#0b0a09", "soft": 0.08},
  "out": {"kind": "fade", "dur": 2.0, "color": "#000000"},
  "camera": [ {"t": 0, "x": 1600, "y": 700, "zoom": 1.08},
              {"t": 8.5, "x": 1700, "y": 1150, "zoom": 1.2, "dolly": 0.12, "rot": 0, "ease": "inout"} ],
  "grade":  [ {"t": 0, "exposure": 1, "tint": "#ffffff", "sat": 1}, {"t": 6, "exposure": 0.8, "tint": "#ffd8b0"} ],
  "layers": [ ... ], "fx": [ ... ], "cues": [ ... ] }
```

**Transitions (`in`).** `cut`; `fade` {dur, color}: a dip through the colour; `dissolve` {dur}; `ink` {dur, origin, map, edge, soft}: the next plate appears where an order map passes a rising threshold, with a dark wet-ink rim at the front (default map: a domain-warped fractal bloom from `origin`, in 0..1 of the screen; a supplied map is grayscale, dark first); `light`: the same, the front warm light glowing a little ahead of itself (`edge` default `#ffc677`); `waterline` {dur, wave}: a wavy surface line sweeps up the frame, the next plate under it, slightly bent, a bright skin at the line.

**Camera.** `x, y`: the canvas point at the screen's centre on the reference plane; `zoom`: lens magnification (1: the canvas width fills the screen width; all layers alike); `dolly`: how far the camera has moved forward, in depth units (near layers grow faster); `rot`: roll, degrees. Unset values carry on from the key before (the first key's: at rest, the canvas centre, zoom 1). Zoom (and layer scale) move in log space, so a push reads at an even pace.

**Keys and eases** (camera, grade, layer keys). A Hermite curve through every key, the speed the same either side of each key; from rest at the first key, to rest at the last; a key that is a peak or a trough is passed at rest and the curve never overshoots. A key's `ease` is for the segment arriving at it: unset passes through at speed; `inout` comes to rest at this key and starts the segment from rest; `in` from rest only; `out` and `stop` to rest at this key only; `linear` not slowed at either end; `hold` stays at the key before, then jumps here (a cut).

**The lens (2.5D).** Each layer is a plane at depth `z` (1: the reference plane; sky 6-20; foreground 0.5-0.9), painted as seen from the camera at rest, so at rest every layer sits at its `pos`. Pinhole: a layer at depth z appears z/(z - dolly) as large, and a pan by (x - W/2) shifts it by (x - W/2)/z on the reference scale. A plane the dolly reaches is held 0.05 ahead of the lens.

**Layers.**

```jsonc
{ "id": "sky", "image": "res://art/storybook/sb00/p1/sky.png",
  "pos": [0, 0],          // top-left on the canvas at rest
  "scale": 1,             // image px to canvas px (a half-size image: 2)
  "z": 6, "blend": "mix|add|screen|multiply", "opacity": 1,
  "pivot": [x, y],        // canvas px its keys scale and turn about (default: its centre)
  "repeat": false, "size": [w, h],   // repeat: the image wraps over size (for scroll)
  "keys":   [ {"t": 5.0, "dx": 0, "dy": 0, "scale": 1, "rot": 0, "opacity": 1, "ease": "inout"} ],
  "frames": [ {"t": 0, "image": "a.png"}, {"t": 3.2, "image": "b.png", "fade": 0.4} ],
  "touch":  [ {"kind": "flicker", ...} ] }
```

With the first key after 0, the layer is at rest (and its own opacity) at 0. `frames` are drawn key poses crossfaded over `fade` (both full through the middle, so an opaque layer never dips). A placeholder card: `"color": "#14110d", "label": "P1 · Long ago"` (and `size`, default the canvas) instead of an image. `screen` is approximate (premultiplied, by the colour's own lightness).

## Touches

Each touch at most once a layer; masks and maps are images the size of the layer's image (white: full effect). Lengths are canvas px; times are the plate's.

| kind | parameters (defaults) | what it is for |
|---|---|---|
| `flicker` | rate 7, amount 0.25, seed 0 | brightness by three octaves of noise (never a sine): fire and lamp layers, usually `blend: add` |
| `sway` | mask, amp 4 px, freq 0.35, dir [1, 0], scale 220 px | low-frequency noise displacement, mostly along `dir`, a little across it: cloth, weed, banners, flame tongues |
| `water` | mask, amp 1.5 px, freq 1.4, scale 36 px | finer, faster displacement inside a mask: a trembling surface, a reflection |
| `ripple` | centers [[x, y], ...] (canvas px, up to 8), start 0, period 3, speed 60 px/s, amp 2 px, rings 3, gap 22 px, reach 260 px, squash 1 (0.3: rings seen at a low angle), light 0.25, mask | expanding rings, a faint highlight and a little refraction, fading with radius and over the period; repeating |
| `reveal` | map, t0 0, t1 1, soft 0.08, invert false | the layer appears where a grayscale order map (dark first) passes a threshold moving t0 to t1; `invert`: it goes instead (a crack through frost, a glow narrowing to a line and going out, light draining into the ground) |
| `scroll` | speed [x, y] px/s | moves the image (needs `repeat` and `size`): mist bands, flowing water |

## Particles and mist (`fx`)

```jsonc
{"kind": "particles", "preset": "smoke", "at": [x, y], "area": [w, h], "z": 0.8,
 "rate": 6, "life": 5, "speed": [25, 50], "dir": [0, -1], "spread": 14, "gravity": [0, -6],
 "size": [70, 120], "grow": 2.4, "color": ["#5e5852a0", "#3a363200"], "additive": false,
 "wobble": 0.5, "damping": 0, "burst": [2.0, 5.0], "count": 24, "seed": 1, "texture": "res://..."}
{"kind": "mist", "rect": [x, y, w, h], "z": 0.9, "color": "#b8c4cc", "density": 0.5, "speed": [12, 0], "scale": 260, "seed": 0}
```

Presets (every number above overrides): `smoke` (soft puffs, rising slowly, spreading, fading), `sparks` (tiny, bright, gravity, short life, additive; `burst` times fire `count` at once), `motes` (glowing dabs rising slowly with wobble), `bubbles` (rising fast), `drips` (long drops falling), `ash`, `snow`. Particles parallax with their `z` like a layer, already in their steady state when the plate appears, and are the same every run (a fixed seed). They draw with small soft dabs made procedurally (an uneven brush edge), or a `texture` the lead supplies. Fx are drawn among the layers by depth.

## Cues

`{"at": 0.8, "do": ...}`, in time order; at the same moment, the file's own cues before its plates', each in the order written.

| do | parameters | |
|---|---|---|
| `line` | id, tag, linger 0.7 | `<conversation>.<id>` (an id with a dot is a full id from another conversation) through CineLines and the VoiceOver: its take when there is one, else silent for the reading pace; its subtitle for that long, but never past the screen's next black (the end black, a gap between plates, or a plate's `out` fade to black with nothing over it): it is gone by then. `tag` labels that line only; untagged lines are unlabelled roman; a sung line is italic |
| `say` | text, speaker, sung, italic, dur | a subtitle with no take (cut at the next black, as a line's) |
| `sfx` | name, gain 1, pan 0 | the game's named cinematic sounds (`Sfx.Cine`) |
| `sound` | file, id, gain dB, pan, fade s, loop | a sound file on its own player (panned on its own small bus) |
| `stop` | id, fade 0.3 | |
| `music` | mood (`silence`, `night`, ...; `game` hands it back), intensity 0.5, over | the game's score |
| `bus` | lowpass Hz, gain dB, over s | a low-pass and a level on the way out of everything (the master bus) while it plays: the underwater muffle, the well at the end. Removed when it ends |

The bars are CinemaBars at 2.39:1, fully in from the first frame.

**Skip.** Hold interact or pause (the CinemaBars ring): from `skip.from` (1.5 s) on a first view, at once once seen. The profile flag is the storybook's id in `Settings.SeenCinematics` (`seen.sb00`), set when it first starts. A skip cuts to black, fades every sound over 0.15 s (and drops the synth's tails) and ends as skipped. `--sb-skip-at S` does the same skip at storybook time S (the hold's own path, the first-view rule aside), for scripted checks.

## Running it

SB00 is not live (`"live": false`) until its painted plates are in: a new journey goes straight to C01, and `--storybook sb00` still plays it alone. The rest of this section describes it once live.

In the game, SB00 opens a new journey when `godot/data/storybook/sb00.json` exists: creation confirmed, its last frame holds 0.5 s and fades to black over 0.8 s with the title music; SB00 plays from black (nothing 3D is drawn under it); at its end the zone is entered under the black and C01 takes the bars already in; the frames the zone takes to stand up are already silence, so C01's shot 1 loses that long of its opening silence (at most 1.2 s, down to 1.3 s: its drops stay), and the log says so (`storybook: the zone stood up in ...`). Played to its end, it sets the journey fact `sb00.ended`, and C01's shot 1 (by its `durs` and a `when` on the cue) loses `water_close` and is 2.5 s (less the load, above), its drops timed from its end (first drop 1.2 s in); the rest of C01 is as written. Skipped, C01 plays exactly as written. `--nocine` goes without it; a quick start goes without it unless `--cines` (then it plays first, over black). Without the file everything plays as before.

For pictures and checks (Windows; `--resolution` holds for runs with `--sb-shots` or `--write-movie`, as for `--shot` and `--perf`, whatever the saved Fullscreen setting; `G` = `C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe`; `dotnet build` first, the shoot doesn't rebuild C#; new art needs `"$G" --headless --path godot --import`):

```sh
# play one alone over black and quit at its end
"$G" --path godot --resolution 1920x1080 -- --storybook sb00
# frames at those seconds (godot/.shots/sb_<id>_<t>.png, full resolution), quitting after the last; start late with --sb-from
"$G" --path godot --resolution 1920x1080 --fixed-fps 30 -- --storybook test_plates --sb-shots 0.8,5.5,8.9 --sb-from 0
# a capture with sound for the cut's judge (Movie Maker: fixed 30 fps, the picture and the mix written together);
# --vo on: voice-over is off by default (26 Oct), and without it no take plays (the subtitles still show)
"$G" --path godot --resolution 1920x1080 --write-movie C:/temp/sb00.avi --fixed-fps 30 -- --storybook sb00 --vo on
# Storybook 3's ink section in one go (wire, build, import, 14 frames, the 56-89.5 s capture, the sheet): bash tools/storybook/sb3_shoot.sh <round>
# the C01 seam and the skip, scripted (once SB00 is live; a quick start into the prologue; the log prints wall times at SB00's end and C01's start)
"$G" --path godot --resolution 1280x720 -- --quick --cines --sb-from 80 --perf
"$G" --path godot --resolution 1280x720 -- --quick --cines --sb-from 20 --sb-skip-at 25
# ffmpeg is not on PATH: use imageio_ffmpeg's copy (FF=$(python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"))
"$FF" -i C:/temp/sb00.avi -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k C:/temp/sb00.mp4
```

The storybook keeps its own clock (the frame's delta) and every shader animates from it, so with a fixed frame rate the same second gives the same frame. New art: `python tools/storybook/make_test_plates.py` shows how `.import` files are written for storybook art (VRAM compressed, BPTC high quality, mipmaps); use its `write_import` for real plates.

**Cost.** Each drawn plate renders into its own SubViewport at the screen's size (2D only); a full-screen composite mixes two of them and adds the grade, grain and vignette. Only plates being drawn exist; a plate's textures start loading on a thread 3 s before it is drawn and are let go when it is freed.

## Provenance

(The lead's: every plate's painting, its prompt, seed and model hashes; see `tools/storybook/gen.py`.)
