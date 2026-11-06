# P4 clip specs (`specs/<clip>.json`)

A P4 clip is one spec. Its file name is the clip's game name, and a packed P4 clip replaces the bridge clip of that name on B.
The commands are in `tools/anim/p4.py` (`gen`, `takes`, `build`, `check`). The core is Marionette `tools/motion/`.

| key | what |
|---|---|
| `kind` | `idle` or `gait`: which bible measures apply (`motion/measures.py` `idle()` or `gait()`) |
| `rules` | the bible rules the clip answers to (text) |
| `bands` | `{measure: [lo, hi]}`: the numbers a take is scored against (`measures.score`, 0 = all in band). `build` prints pass or MISS for each |
| `gen.engine` | `kimodo` (MotionBricks is not wired yet) |
| `gen.prompts` | one sentence each (Kimodo reads a full stop as the next prompt) |
| `gen.seconds`, `gen.seeds` (one per prompt, cycled), `gen.takes` (per prompt) | |
| `gen.root2d` | the Root2D path, built from numbers by `motion/paths.py`: `{kind: sway, travel, period, ease, overshoot, start}` or `{kind: straight, speed, ramp}`, plus `every` (constrain every k-th frame) |
| `post.loop`, `post.inplace` | as `motion retarget` |
| `post.cycle_s` | `[min, max]` seconds for the loop length (for idles, whole sway cycles) |
| `post.gait`, `post.duty` | the generated-gait foot lock (`footlock.gait_windows`). Each stance is pinned whole. `duty` is the share of the stride the ball is down; the belt is the stance's own ground speed |
| `post.game_speed` | the speed the game moves her at (m/s), so playback scale = game_speed / the clip's `speed_mps` |
| `post.crop` | optional `[a, b]` source frames used first |
| `source`, `bvh`, `sha1`, `take_score` | written by `takes`: the best take, imported to `src/<clip>.npz` (committed, because generation is not reproducible) |
| `notes` | free text |

`specs/<clip>.takes.json` logs every take's measures and score, best first.

Kimodo runs in two passes (`motion/kimodo_run.py`). `encode` loads only the text encoder (about 16 GB of RAM on the CPU), and only when 18 GB are free. It writes each prompt once into the embedding cache (`KIMODO_CACHE`). `generate` then loads only the diffusion model (about 3 GB of VRAM) and reads the cache. A prompt missing from the cache is an error; Llama is never loaded silently.

A gait's built clip carries `speed_mps`, its locked stance speed. P4Pack writes it as the animation's `speed` meta, and on B the game plays the gait at that speed (`P4Overlay.Speed`).
