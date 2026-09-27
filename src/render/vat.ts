import * as THREE from 'three';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { Assets, type CharacterModel, type PropPack } from './assets';
import { OCCLUDE_PARS } from './flora';

/* Vertex animation textures: how a horde of animated skeletons costs one draw.
 *
 * A skinned character is sampled at load: every clip it needs (walk, strike,
 * fall, rise from the grave...) is played through the real skeleton and the
 * posed position and normal of every vertex, at every frame, is written into
 * two textures. The horde is then an InstancedMesh of the rest geometry whose
 * vertex shader reads its pose from the textures - each instance at its own
 * clip and time, interpolating between frames - so five hundred creatures
 * animate as independently as five, for the price of one mesh.
 *
 * Weapons held in a hand are baked rigidly with the bone they hang from.
 * The skeletons' glowing eyes keep glowing: a per-vertex glow weight rides
 * along as an attribute. Faction colours are a recoloured copy of the
 * model's texture (the Kerchiefs' red is the rogue's green, turned).
 *
 * Per instance the crowd carries: clip start, clip length, current frame,
 * loop flag (aAnim), and flash, dissolve, frozen, burning (aFx), and a tint
 * with an emissive boost (aTint). */

export type AnimRole = 'move' | 'idle' | 'attack' | 'die' | 'rise' | 'hit' | 'cast' | 'windup' | 'burrow';

export interface VatSpec {
  key: string;
  model: CharacterModel | (() => THREE.Group);
  scale: number;
  clips: Partial<Record<AnimRole, string | THREE.AnimationClip>>;
  loops?: Partial<Record<AnimRole, boolean>>;
  /** Optional non-skinned parts of the model to keep (weapons, hats). */
  show?: string[];
  attach?: Array<{ bone: string; pack: PropPack; prop: string; scale?: number; rot?: [number, number, number]; pos?: [number, number, number] }>;
  /** Texture recolour: hue in [0,1) -> new hue, or null to leave it. */
  recolor?: (h: number, s: number, l: number) => [number, number, number] | null;
  fps?: number;
  /** Colour multiplier applied to the whole baked mesh. */
  tint?: THREE.ColorRepresentation;
  /** Shift the model in its own space (before scale), e.g. to centre a long
   *  beast on its collision circle. */
  offset?: [number, number, number];
}

export interface VatClip { start: number; frames: number; fps: number; loop: boolean; duration: number }

export interface VatAsset {
  key: string;
  geometry: THREE.BufferGeometry;
  posTex: THREE.DataTexture;
  norTex: THREE.DataTexture;
  width: number;
  rows: number;
  clips: Partial<Record<AnimRole, VatClip>>;
  map: THREE.Texture | null;
  glowColor: THREE.Color;
  height: number;
  vertexCount: number;
}

const cache = new Map<string, VatAsset>();
const recolorCache = new Map<string, THREE.Texture>();

function recolorTexture(src: THREE.Texture, key: string, fn: NonNullable<VatSpec['recolor']>): THREE.Texture {
  const hit = recolorCache.get(key);
  if (hit) return hit;
  const img = src.image as CanvasImageSource & { width: number; height: number };
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const g = c.getContext('2d')!;
  g.drawImage(img, 0, 0);
  const data = g.getImageData(0, 0, c.width, c.height);
  const col = new THREE.Color();
  const hsl = { h: 0, s: 0, l: 0 };
  for (let i = 0; i < data.data.length; i += 4) {
    col.setRGB(data.data[i] / 255, data.data[i + 1] / 255, data.data[i + 2] / 255, THREE.SRGBColorSpace);
    col.getHSL(hsl, THREE.SRGBColorSpace);
    const r = fn(hsl.h, hsl.s, hsl.l);
    if (!r) continue;
    col.setHSL(r[0], r[1], r[2], THREE.SRGBColorSpace);
    const rgb = { r: 0, g: 0, b: 0 };
    col.getRGB(rgb, THREE.SRGBColorSpace);
    data.data[i] = Math.round(rgb.r * 255); data.data[i + 1] = Math.round(rgb.g * 255); data.data[i + 2] = Math.round(rgb.b * 255);
  }
  g.putImageData(data, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.flipY = src.flipY;
  t.magFilter = src.magFilter;
  t.minFilter = src.minFilter;
  recolorCache.set(key, t);
  return t;
}

export function bakeVat(spec: VatSpec): VatAsset {
  const hit = cache.get(spec.key);
  if (hit) return hit;
  const fps = spec.fps ?? 15;
  const root: THREE.Group = typeof spec.model === 'function' ? spec.model() : SkeletonUtils.clone(Assets.characterTemplate(spec.model)) as THREE.Group;
  // Scale is applied to the baked positions, not the root: a scaled root
  // would count twice against the bind matrices.
  root.updateMatrixWorld(true);
  const bones = new Map<string, THREE.Object3D>();
  root.traverse((o) => { if ((o as THREE.Bone).isBone) bones.set(o.name, o); });

  // Attach props to their bones so they ride the skeleton.
  for (const a of spec.attach ?? []) {
    const bone = bones.get(a.bone);
    if (!bone) continue;
    const o = Assets.prop(a.pack, a.prop);
    o.scale.setScalar(a.scale ?? 1);
    if (a.rot) o.rotation.set(...a.rot);
    if (a.pos) o.position.set(...a.pos);
    o.name = `attach:${a.prop}`;
    bone.add(o);
  }
  root.updateMatrixWorld(true);

  // Parts that make it into the bake.
  interface Part { mesh: THREE.Mesh; skinned: boolean; glow: number; offset: number; count: number }
  const parts: Part[] = [];
  let map: THREE.Texture | null = null;
  const glowColor = new THREE.Color(0, 0, 0);
  let total = 0;
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const skinned = !!(m as THREE.SkinnedMesh).isSkinnedMesh;
    const attached = m.parent?.name.startsWith('attach:') || m.name.startsWith('attach:') || isUnderAttach(m);
    if (!skinned && !attached && !(spec.show ?? []).includes(m.name)) return;
    const mat = (Array.isArray(m.material) ? m.material[0] : m.material) as THREE.MeshStandardMaterial;
    const isGlow = mat.name === 'Glow' || (mat.emissive && mat.emissive.getHex() !== 0 && !mat.map);
    if (isGlow) glowColor.copy(mat.emissive.getHex() ? mat.emissive : mat.color);
    else if (!map && mat.map) map = mat.map;
    const count = m.geometry.getAttribute('position').count;
    parts.push({ mesh: m, skinned, glow: isGlow ? 1 : 0, offset: total, count });
    total += count;
  });

  // The rest geometry: uv, glow weight, index. Positions come from the
  // texture; the attribute is kept (three requires it) as the bind pose.
  const uv = new Float32Array(total * 2);
  const glow = new Float32Array(total);
  // Procedural creatures are coloured per vertex rather than by texture.
  const hasColor = parts.some((p) => !!p.mesh.geometry.getAttribute('color'));
  const color = hasColor ? new Float32Array(total * 3).fill(1) : null;
  const rest = new Float32Array(total * 3);
  const indices: number[] = [];
  for (const p of parts) {
    const g = p.mesh.geometry;
    const puv = g.getAttribute('uv');
    const pcol = g.getAttribute('color');
    for (let i = 0; i < p.count; i++) {
      if (puv) { uv[(p.offset + i) * 2] = puv.getX(i); uv[(p.offset + i) * 2 + 1] = puv.getY(i); }
      if (color && pcol) { color[(p.offset + i) * 3] = pcol.getX(i); color[(p.offset + i) * 3 + 1] = pcol.getY(i); color[(p.offset + i) * 3 + 2] = pcol.getZ(i); }
      glow[p.offset + i] = p.glow;
    }
    if (g.index) for (let i = 0; i < g.index.count; i++) indices.push(g.index.getX(i) + p.offset);
    else for (let i = 0; i < p.count; i++) indices.push(i + p.offset);
  }

  // Frames.
  const mixer = new THREE.AnimationMixer(root);
  const roles = Object.keys(spec.clips) as AnimRole[];
  const clipInfo: Partial<Record<AnimRole, VatClip>> = {};
  let frameCount = 0;
  const clipObjs: Array<{ role: AnimRole; clip: THREE.AnimationClip; frames: number }> = [];
  for (const role of roles) {
    const c = spec.clips[role]!;
    const clip = typeof c === 'string' ? Assets.clip(c) : c;
    const frames = Math.min(48, Math.max(2, Math.round(clip.duration * fps) + 1));
    const loop = spec.loops?.[role] ?? (role === 'move' || role === 'idle' || role === 'burrow' || role === 'cast');
    clipInfo[role] = { start: frameCount, frames, fps: (frames - 1) / clip.duration, loop, duration: clip.duration };
    clipObjs.push({ role, clip, frames });
    frameCount += frames;
  }

  const width = Math.min(4096, total);
  const rows = Math.ceil(total / width);
  const texH = rows * frameCount;
  const pos = new Uint16Array(width * texH * 4);
  const nor = new Uint8Array(width * texH * 4);
  const rootInv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const v = new THREE.Vector3();
  const framePos = new Float32Array(total * 3);
  const frameNor = new Float32Array(total * 3);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
  const toHalf = THREE.DataUtils.toHalfFloat;
  let height = 0;

  let frameIndex = 0;
  for (const { clip, frames } of clipObjs) {
    mixer.stopAllAction();
    const action = mixer.clipAction(clip);
    action.reset().play();
    for (let f = 0; f < frames; f++) {
      mixer.setTime((f / (frames - 1)) * clip.duration * 0.999);
      root.updateMatrixWorld(true);
      for (const p of parts) {
        const m = p.mesh;
        const world = new THREE.Matrix4().multiplyMatrices(rootInv, m.matrixWorld);
        const pa = m.geometry.getAttribute('position');
        for (let i = 0; i < p.count; i++) {
          if (p.skinned) (m as THREE.SkinnedMesh).getVertexPosition(i, v);
          else v.fromBufferAttribute(pa, i);
          v.applyMatrix4(world);
          if (spec.offset) { v.x += spec.offset[0]; v.y += spec.offset[1]; v.z += spec.offset[2]; }
          const k = (p.offset + i) * 3;
          framePos[k] = v.x * spec.scale; framePos[k + 1] = v.y * spec.scale; framePos[k + 2] = v.z * spec.scale;
          if (framePos[k + 1] > height) height = framePos[k + 1];
        }
      }
      // Normals from the posed triangles (area weighted).
      frameNor.fill(0);
      for (let t = 0; t < indices.length; t += 3) {
        const i0 = indices[t], i1 = indices[t + 1], i2 = indices[t + 2];
        a.fromArray(framePos, i0 * 3); b.fromArray(framePos, i1 * 3); c.fromArray(framePos, i2 * 3);
        n.subVectors(c, b).cross(a.clone().sub(b));
        for (const id of [i0, i1, i2]) { frameNor[id * 3] += n.x; frameNor[id * 3 + 1] += n.y; frameNor[id * 3 + 2] += n.z; }
      }
      for (let i = 0; i < total; i++) {
        const row = frameIndex * rows + Math.floor(i / width);
        const col = i % width;
        const tk = (row * width + col) * 4;
        pos[tk] = toHalf(framePos[i * 3]); pos[tk + 1] = toHalf(framePos[i * 3 + 1]); pos[tk + 2] = toHalf(framePos[i * 3 + 2]); pos[tk + 3] = toHalf(1);
        n.set(frameNor[i * 3], frameNor[i * 3 + 1], frameNor[i * 3 + 2]).normalize();
        nor[tk] = Math.round((n.x * 0.5 + 0.5) * 255); nor[tk + 1] = Math.round((n.y * 0.5 + 0.5) * 255); nor[tk + 2] = Math.round((n.z * 0.5 + 0.5) * 255); nor[tk + 3] = 255;
        if (frameIndex === 0) { rest[i * 3] = framePos[i * 3]; rest[i * 3 + 1] = framePos[i * 3 + 1]; rest[i * 3 + 2] = framePos[i * 3 + 2]; }
      }
      frameIndex++;
    }
  }
  mixer.stopAllAction();

  const posTex = new THREE.DataTexture(pos, width, texH, THREE.RGBAFormat, THREE.HalfFloatType);
  posTex.magFilter = posTex.minFilter = THREE.NearestFilter;
  posTex.needsUpdate = true;
  const norTex = new THREE.DataTexture(nor, width, texH, THREE.RGBAFormat, THREE.UnsignedByteType);
  norTex.magFilter = norTex.minFilter = THREE.NearestFilter;
  norTex.needsUpdate = true;

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(rest, 3));
  geometry.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(total * 3).fill(0.5), 3));
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.setAttribute('aGlow', new THREE.BufferAttribute(glow, 1));
  if (color) geometry.setAttribute('color', new THREE.BufferAttribute(color, 3));
  geometry.setIndex(indices);
  geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 1, 0), 3);

  let finalMap: THREE.Texture | null = map;
  if (map && spec.recolor) finalMap = recolorTexture(map, spec.key, spec.recolor);

  const asset: VatAsset = { key: spec.key, geometry, posTex, norTex, width, rows, clips: clipInfo, map: finalMap, glowColor, height, vertexCount: total };
  cache.set(spec.key, asset);
  return asset;
}

function isUnderAttach(o: THREE.Object3D) {
  for (let p = o.parent; p; p = p.parent) if (p.name.startsWith('attach:')) return true;
  return false;
}

/* ---------------------------------------------------------------- shader -- */

const VAT_PARS = /* glsl */ `
uniform sampler2D uVatPos;
uniform sampler2D uVatNor;
uniform float uVatWidth;
uniform float uVatRows;
uniform float uVatTime;
attribute vec4 aAnim;   // clip start, clip frames, current frame (float), loop
attribute vec4 aFx;     // flash, dissolve, frozen, burning
attribute vec4 aTint;   // rgb multiply, emissive boost
attribute float aGlow;
varying vec4 vFx;
varying vec4 vTint;
varying float vGlow;
varying vec3 vVatLocal;
ivec2 vatCoord(float frame, int vid) {
  int w = int(uVatWidth);
  int row = int(frame) * int(uVatRows) + vid / w;
  return ivec2(vid - (vid / w) * w, row);
}
`;

const VAT_VERTEX = /* glsl */ `
float vStart = aAnim.x, vLen = max(aAnim.y, 1.0), vFrame = aAnim.z;
float f0 = floor(vFrame);
float fk = vFrame - f0;
float f1 = f0 + 1.0;
if (f1 >= vLen) f1 = aAnim.w > 0.5 ? 0.0 : vLen - 1.0;
f0 = min(f0, vLen - 1.0);
int vid = gl_VertexID;
vec3 p0 = texelFetch(uVatPos, vatCoord(vStart + f0, vid), 0).xyz;
vec3 p1 = texelFetch(uVatPos, vatCoord(vStart + f1, vid), 0).xyz;
vec3 n0 = texelFetch(uVatNor, vatCoord(vStart + f0, vid), 0).xyz * 2.0 - 1.0;
vec3 n1 = texelFetch(uVatNor, vatCoord(vStart + f1, vid), 0).xyz * 2.0 - 1.0;
vec3 vatP = mix(p0, p1, fk);
vec3 vatN = normalize(mix(n0, n1, fk));
vFx = aFx;
vTint = aTint;
vGlow = aGlow;
vVatLocal = vatP;
`;

/** Patch a material to read its vertices from the VAT. Used for the colour
 *  pass and for the shadow pass (the silhouette must match). */
function patchVat(mat: THREE.Material, asset: VatAsset, depthOnly: boolean) {
  const uniforms = {
    uVatPos: { value: asset.posTex },
    uVatNor: { value: asset.norTex },
    uVatWidth: { value: asset.width },
    uVatRows: { value: asset.rows },
    uVatTime: { value: 0 },
    uGlowColor: { value: asset.glowColor.clone().multiplyScalar(2.2) },
  };
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader.replace('#include <common>', `#include <common>\n${VAT_PARS}`);
    // The colour pass computes normals before positions; the shadow pass
    // has no normal step at all, so the pose is read wherever comes first.
    // (The depth shader does contain beginnormal_vertex - inside an #ifdef
    // for displacement maps - so this keys off the pass, not the text.)
    if (!depthOnly) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <beginnormal_vertex>', `${VAT_VERTEX}\nvec3 objectNormal = vatN;\n#ifdef USE_TANGENT\nvec3 objectTangent = vec3(1.0, 0.0, 0.0);\n#endif`)
        .replace('#include <begin_vertex>', 'vec3 transformed = vatP;');
    } else {
      shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', `${VAT_VERTEX}\nvec3 transformed = vatP;`);
    }
    if (depthOnly) {
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying vec4 vFx;\nvarying vec3 vVatLocal;')
        .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
if (vFx.y > 0.0) {
  float n = fract(sin(dot(floor(vVatLocal * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
  if (n < vFx.y) discard;
}`);
      return;
    }
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
uniform vec3 uGlowColor;
uniform float uVatTime;
varying vec4 vFx;
varying vec4 vTint;
varying float vGlow;
varying vec3 vVatLocal;
${OCCLUDE_PARS}`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
// Dissolve: the dead go back to the dark in ragged flakes.
float dn = fract(sin(dot(floor(vVatLocal * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
if (vFx.y > 0.0 && dn < vFx.y) discard;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
diffuseColor.rgb *= vTint.rgb;
// Frozen: pale, icy, a little translucent-looking.
diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.62, 0.82, 1.0) * (0.55 + dot(diffuseColor.rgb, vec3(0.33))), vFx.z * 0.75);`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
totalEmissiveRadiance += uGlowColor * vGlow;
// A struck creature flares warm at the rim rather than going white.
float rimF = 1.0 - clamp(dot(normalize(normal), normalize(vViewPosition)), 0.0, 1.0);
totalEmissiveRadiance += vec3(1.0, 0.78, 0.55) * vFx.x * (0.18 + rimF * rimF * 1.1);
totalEmissiveRadiance += vec3(1.0, 0.42, 0.1) * vFx.w * (0.45 + 0.35 * sin(vVatLocal.y * 9.0 + uVatTime * 11.0));
totalEmissiveRadiance += diffuseColor.rgb * vTint.a;
// Ember at the dissolve's edge.
if (vFx.y > 0.0) totalEmissiveRadiance += vec3(1.0, 0.45, 0.12) * smoothstep(vFx.y + 0.12, vFx.y, dn) * 3.0;`);
  };
  mat.customProgramCacheKey = () => `vat-${depthOnly ? 'd' : 'c'}`;
  return uniforms;
}

/** One kind of creature, drawn as many times as there are of it. */
export class VatCrowd {
  readonly mesh: THREE.InstancedMesh;
  private anim: THREE.InstancedBufferAttribute;
  private fx: THREE.InstancedBufferAttribute;
  private tint: THREE.InstancedBufferAttribute;
  private uniforms: { uVatTime: { value: number } };
  private depthUniforms: { uVatTime: { value: number } };
  count = 0;
  readonly asset: VatAsset;

  constructor(asset: VatAsset, readonly capacity: number) {
    this.asset = asset;
    const geo = asset.geometry.clone();
    this.anim = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4), 4);
    this.fx = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4), 4);
    this.tint = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4).fill(1), 4);
    this.anim.setUsage(THREE.DynamicDrawUsage);
    this.fx.setUsage(THREE.DynamicDrawUsage);
    this.tint.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aAnim', this.anim);
    geo.setAttribute('aFx', this.fx);
    geo.setAttribute('aTint', this.tint);
    const mat = new THREE.MeshStandardMaterial({
      map: asset.map, roughness: 0.78, metalness: 0.05,
      vertexColors: !!asset.geometry.getAttribute('color'), flatShading: !asset.map,
    });
    this.uniforms = patchVat(mat, asset, false);
    this.mesh = new THREE.InstancedMesh(geo, mat, capacity);
    const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
    this.depthUniforms = patchVat(depth, asset, true);
    this.mesh.customDepthMaterial = depth;
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  }

  begin() { this.count = 0; }

  /** Add one creature this frame. `t` is seconds into the role's clip. */
  push(matrix: THREE.Matrix4, role: AnimRole, t: number, flash: number, dissolve: number, frozen: number, burning: number, tint: THREE.Color, glow = 0) {
    if (this.count >= this.capacity) return;
    const i = this.count++;
    this.mesh.setMatrixAt(i, matrix);
    const clip = this.asset.clips[role] ?? this.asset.clips.move ?? this.asset.clips.idle!;
    let frame = t * clip.fps;
    if (clip.loop) frame = frame % clip.frames;
    else frame = Math.min(frame, clip.frames - 1);
    this.anim.setXYZW(i, clip.start, clip.frames, frame, clip.loop ? 1 : 0);
    this.fx.setXYZW(i, flash, dissolve, frozen, burning);
    this.tint.setXYZW(i, tint.r, tint.g, tint.b, glow);
  }

  end(time: number) {
    this.mesh.count = this.count;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.anim.needsUpdate = true;
    this.fx.needsUpdate = true;
    this.tint.needsUpdate = true;
    this.uniforms.uVatTime.value = time;
    this.depthUniforms.uVatTime.value = time;
  }

  clipDuration(role: AnimRole) {
    const c = this.asset.clips[role];
    return c ? c.duration : 1;
  }
}
