import * as THREE from 'three';
import type { CharacterModel } from './assets';
import { grimePixel, PEOPLE_GRIME } from './grime';
import { keep } from './dispose';

/* Dyeing a character's clothes.
 *
 * Each KayKit character is textured from one palette atlas: 8 x 4 swatches,
 * each 128 x 256 px, each a vertical gradient that does the shading. The
 * parts of the model sample swatches by colour: the Warden's tabard and
 * cloak share the red one, the Arcanist's robe the purple, the Stalker's
 * hood and cloak the green. So a look is not a tint over the whole model
 * (that darkens metal and leather with the cloth, and cannot make red into
 * blue); it is a copy of the atlas with the cloth swatches repainted,
 * keeping each gradient's light and dark, and given to the parts that wear
 * it. The cloak gets its own copy, so it can differ from the tunic. */

/** [column 0-7, row 0-3] of a 128 x 256 swatch. */
export type Swatch = [number, number];

/** Which swatches on each model are which: cloth that a calling's colours
 *  repaint, the cloak, skin and hair. Worked out from the parts' UVs. */
export const SWATCHES: Record<CharacterModel, Record<string, Swatch[]>> = {
  knight: { plate: [[3, 0], [2, 1], [7, 0]], cloth: [[0, 1]], trim: [[1, 1]], under: [[7, 1]], leather: [[6, 0]], cloak: [[0, 1]], skin: [[0, 0]], hair: [[1, 0]] },
  barbarian: { cloth: [[0, 1], [1, 1]], fur: [[7, 1], [7, 2]], cloak: [[7, 0]], skin: [[0, 0]], hair: [[1, 0]] },
  mage: { cloth: [[0, 1], [1, 1]], under: [[7, 1]], trim: [[5, 0]], cloak: [[2, 1]], skin: [[0, 0], [7, 2]], hair: [[1, 0]] },
  rogue: { cloth: [[1, 1]], under: [[0, 1]], cloak: [[1, 1]], skin: [[0, 0]], hair: [[1, 0]] },
  rogue_hooded: { cloth: [[1, 1]], under: [[0, 1]], cloak: [[1, 1]], skin: [[0, 0]], hair: [[1, 0]] },
  skeleton_minion: {}, skeleton_warrior: {}, skeleton_mage: {}, skeleton_rogue: {},
};

/** What to paint: slot name (as in SWATCHES) to a colour. */
export type Paint = Record<string, string>;

const cache = new Map<string, THREE.Texture>();

function sourcePixels(base: THREE.Texture): ImageData | null {
  const img = base.image as (CanvasImageSource & { width: number; height: number }) | undefined;
  if (!img || !img.width) return null;
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const g = c.getContext('2d', { willReadFrequently: true })!;
  g.drawImage(img, 0, 0);
  return g.getImageData(0, 0, c.width, c.height);
}

/** The model's atlas with these slots repainted (cached: many people can
 *  wear the same colours). The original if there is nothing to paint. */
export function paintedAtlas(base: THREE.Texture, model: CharacterModel, paint: Paint): THREE.Texture {
  const slots = SWATCHES[model] ?? {};
  const jobs = Object.entries(paint).filter(([slot, col]) => col && slots[slot]?.length);
  if (!jobs.length) return base;
  const key = `${model}|${jobs.map(([s, c]) => `${s}=${c}`).sort().join(',')}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const data = sourcePixels(base);
  if (!data) return base;
  const W = data.width, H = data.height, sw = W / 8, sh = H / 4;
  const px = data.data;
  const target = new THREE.Color();
  const lum = (i: number) => 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2];
  const meanOf = ([cx, cy]: Swatch) => {
    const x0 = Math.round(cx * sw), y0 = Math.round(cy * sh), x1 = Math.round((cx + 1) * sw), y1 = Math.round((cy + 1) * sh);
    let sum = 0, n = 0;
    for (let y = y0; y < y1; y += 4) for (let x = x0; x < x1; x += 4) { sum += lum((y * W + x) * 4); n++; }
    return Math.max(1, sum / Math.max(1, n));
  };
  for (const [slot, col] of jobs) {
    target.set(col);
    // Paint in sRGB bytes: the atlas is sRGB, and so are the colours we choose.
    const tr = Math.round(target.r * 255), tg = Math.round(target.g * 255), tb = Math.round(target.b * 255);
    // A slot of several swatches keeps their brightness relative to the
    // first (a plate's light and dark steel stay light and dark).
    const means = slots[slot].map(meanOf);
    slots[slot].forEach(([cx, cy], si) => {
      const x0 = Math.round(cx * sw), y0 = Math.round(cy * sh), x1 = Math.round((cx + 1) * sw), y1 = Math.round((cy + 1) * sh);
      // The swatch's middle brightness becomes the chosen colour (scaled by
      // how bright this swatch was beside the first); its lighter and darker
      // ends stay lighter and darker by the same proportion.
      const rel = means[si] / means[0];
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
        const i = (y * W + x) * 4;
        const k = (lum(i) / means[si]) * rel;
        px[i] = Math.min(255, tr * k); px[i + 1] = Math.min(255, tg * k); px[i + 2] = Math.min(255, tb * k);
        // The atlas it paints into is already worn (grime.ts); so is the dye.
        grimePixel(px, i, PEOPLE_GRIME);
      }
    });
  }
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  c.getContext('2d')!.putImageData(data, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.flipY = base.flipY;
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = base.wrapS; t.wrapT = base.wrapT;
  t.magFilter = base.magFilter; t.minFilter = base.minFilter;
  t.anisotropy = base.anisotropy;
  keep(t); // lives in the cache, not in any one zone
  cache.set(key, t);
  return t;
}
