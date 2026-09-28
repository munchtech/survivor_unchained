import * as THREE from 'three';

/* Taking the shine off the KayKit colours.
 *
 * The packs are painted in toy colours: pillar-box red roofs, sky-blue
 * trim, candy-bright props. A grim world wants them worn: each atlas is
 * copied once at load with its colour pulled toward grey, a little dirt
 * mixed in (a sour, brownish tint) and the highlights brought down. Effects
 * are untouched (they are emissive or additive, not textured), so fire,
 * blood and magic keep all their colour against a duller world.
 *
 * The same grade is applied to the colours a player dyes their clothes, so
 * a chosen red sits in the world like everything else does. */

export interface Grime { desat: number; tint: [number, number, number]; gain: number }

/** Props and buildings, and people (a little gentler: faces and skin). */
export const WORLD_GRIME: Grime = { desat: 0.42, tint: [0.96, 0.9, 0.8], gain: 0.9 };
export const PEOPLE_GRIME: Grime = { desat: 0.3, tint: [0.97, 0.92, 0.84], gain: 0.93 };

/** Grade one sRGB byte triple in place. */
export function grimePixel(px: Uint8ClampedArray | number[], i: number, g: Grime) {
  const r = px[i], gg = px[i + 1], b = px[i + 2];
  const l = 0.2126 * r + 0.7152 * gg + 0.0722 * b;
  px[i] = Math.min(255, (r + (l - r) * g.desat) * g.tint[0] * g.gain);
  px[i + 1] = Math.min(255, (gg + (l - gg) * g.desat) * g.tint[1] * g.gain);
  px[i + 2] = Math.min(255, (b + (l - b) * g.desat) * g.tint[2] * g.gain);
}

const cache = new Map<string, THREE.Texture>();

/** A graded copy of a texture (cached; the original if it has no image yet). */
export function grimeTexture(tex: THREE.Texture, g: Grime): THREE.Texture {
  if (tex.userData.grimed) return tex;
  const key = `${tex.uuid}|${g.desat}|${g.tint.join(',')}|${g.gain}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const img = tex.image as (CanvasImageSource & { width: number; height: number }) | undefined;
  if (!img || !img.width) return tex;
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0);
  const data = ctx.getImageData(0, 0, c.width, c.height);
  for (let i = 0; i < data.data.length; i += 4) grimePixel(data.data, i, g);
  ctx.putImageData(data, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.flipY = tex.flipY;
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = tex.wrapS; t.wrapT = tex.wrapT;
  t.magFilter = tex.magFilter; t.minFilter = tex.minFilter;
  t.anisotropy = tex.anisotropy;
  t.userData.grimed = true;
  t.userData.shared = true; // lives in the cache, not in any one zone
  cache.set(key, t);
  return t;
}

/** Grade a flat material colour (linear) the same way. */
export function grimeColor(c: THREE.Color, g: Grime) {
  const s = c.clone().convertLinearToSRGB();
  const px = [s.r * 255, s.g * 255, s.b * 255];
  grimePixel(px, 0, g);
  c.setRGB(px[0] / 255, px[1] / 255, px[2] / 255).convertSRGBToLinear();
}
