import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS, type PresetName } from '@/render/atmosphere';
import { envModel, envBounds, preloadEnv, type EnvKit } from '@/render/env';

/* Development view: pieces of a world kit in a labelled grid, each on a
 * marked tile (a red stick shows its +Z, the way it faces), to judge them
 * and learn their sizes. ?dev=env&kit=village&filter=Wall&cols=8&time=day
 * (&names=a,b,c for exactly those). */

export async function envDev(r: Renderer, params: URLSearchParams) {
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS[(params.get('time') as PresetName) || 'day']);
  const kit = (params.get('kit') || 'village') as EnvKit;
  const manifest = await (await fetch(`${import.meta.env.BASE_URL}assets/env/manifest.json`)).json() as Record<string, Record<string, unknown>>;
  const filter = params.get('filter');
  let names = params.get('names')?.split(',') ?? Object.keys(manifest[kit]).filter((n) => !filter || new RegExp(filter, 'i').test(n));
  names = names.slice(0, Number(params.get('max') || 64));
  await preloadEnv(names.map((n) => [kit, n] as [EnvKit, string]));
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: 0x3a3a34, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  r.scene.add(ground);
  // Spacing from the biggest piece shown.
  let span = 2;
  for (const n of names) { const b = envBounds(kit, n); if (b) span = Math.max(span, b.max.x - b.min.x, b.max.z - b.min.z); }
  const gap = Number(params.get('gap') || span + 1.2);
  const cols = Number(params.get('cols') || Math.ceil(Math.sqrt(names.length)));
  names.forEach((n, i) => {
    const x = (i % cols - (cols - 1) / 2) * gap, z = (Math.floor(i / cols) - (Math.ceil(names.length / cols) - 1) / 2) * gap;
    const o = envModel(kit, n);
    o.position.set(x, 0, z);
    o.rotation.y = THREE.MathUtils.degToRad(Number(params.get('yaw') || 0));
    r.scene.add(o);
    const stick = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 0.8), new THREE.MeshBasicMaterial({ color: 0xff3020 }));
    stick.position.set(x, 0.03, z + 0.4);
    r.scene.add(stick);
    r.scene.add(label(n, x, z + gap * 0.42));
  });
  atmo.shadowExtent = gap * cols * 0.6; atmo.configureShadow(); atmo.follow(0, 0, 0);
  const cam = r.camera;
  const rows = Math.ceil(names.length / cols);
  const dist = Number(params.get('dist') || Math.max(cols, rows) * gap * 1.05);
  const pitch = THREE.MathUtils.degToRad(Number(params.get('pitch') || 45));
  const cyaw = THREE.MathUtils.degToRad(Number(params.get('cyaw') || 0));
  cam.position.set(Math.sin(cyaw) * Math.cos(pitch) * dist, Math.sin(pitch) * dist, Math.cos(cyaw) * Math.cos(pitch) * dist);
  cam.lookAt(0, Number(params.get('ly') || 1), 0);
  return (_dt: number, t: number) => atmo.update(t, cam.position);
}

function label(text: string, x: number, z: number) {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 64;
  const g = c.getContext('2d')!;
  g.fillStyle = 'rgba(0,0,0,0.6)';
  g.fillRect(0, 0, 512, 64);
  g.fillStyle = '#fff';
  g.font = 'bold 30px sans-serif';
  g.textAlign = 'center';
  g.fillText(text, 256, 44);
  const t = new THREE.CanvasTexture(c);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false }));
  s.scale.set(3.2, 0.4, 1);
  s.position.set(x, 0.3, z);
  return s;
}

/** ?dev=house: houses from the builder, a row of them (&w=6&d=8&storeys=plaster,timber). */
export async function houseDev(r: Renderer, params: URLSearchParams) {
  const { buildHouse, housePieces } = await import('@/world/zones/houses');
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS[(params.get('time') as PresetName) || 'day']);
  await preloadEnv(housePieces());
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: 0x3a3a34, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  r.scene.add(ground);
  const specs = params.get('w') ? [{ w: Number(params.get('w')), d: Number(params.get('d') || 8), storeys: (params.get('storeys') || 'plaster,plaster').split(',') as never, windows: 0.6, shutters: true, chimney: true, seed: 3 }] : [
    { w: 4, d: 6, storeys: ['plaster'], windows: 0.5, chimney: true, seed: 1 },
    { w: 6, d: 8, storeys: ['stone', 'plaster'], windows: 0.6, shutters: true, chimney: true, seed: 2 },
    { w: 8, d: 12, storeys: ['stone', 'plaster', 'plaster'], windows: 0.7, shutters: true, chimney: true, seed: 3 },
    { w: 6, d: 6, storeys: ['stone'], windows: 0.4, seed: 4 },
  ];
  let x = 0;
  const widths = specs.map((s) => s.w + 4);
  const total = widths.reduce((a, b) => a + b, 0);
  x = -total / 2;
  specs.forEach((sp, i) => {
    const h = buildHouse(sp as never).root;
    h.position.set(x + widths[i] / 2, 0, 0);
    h.rotation.y = THREE.MathUtils.degToRad(Number(params.get('yaw') || 0));
    r.scene.add(h);
    x += widths[i];
  });
  atmo.shadowExtent = 30; atmo.configureShadow(); atmo.follow(0, 0, 0);
  const cam = r.camera;
  const dist = Number(params.get('dist') || 38), pitch = THREE.MathUtils.degToRad(Number(params.get('pitch') || 28)), cyaw = THREE.MathUtils.degToRad(Number(params.get('cyaw') || 20));
  cam.position.set(Math.sin(cyaw) * Math.cos(pitch) * dist, Math.sin(pitch) * dist, Math.cos(cyaw) * Math.cos(pitch) * dist);
  cam.lookAt(0, Number(params.get('ly') || 4), 0);
  return (_dt: number, t: number) => atmo.update(t, cam.position);
}
