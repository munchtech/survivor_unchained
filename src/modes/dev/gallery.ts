import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS, type PresetName } from '@/render/atmosphere';
import { Assets, CHARACTER_IDS, type PropPack } from '@/render/assets';

/* Development view: every prop in a pack laid out on a grid, or every
 * character in a row playing a clip, under a chosen time of day. Used to
 * judge assets and lighting in screenshots: ?dev=gallery&pack=hex_buildings */

export function gallery(r: Renderer, params: URLSearchParams) {
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS[(params.get('time') as PresetName) || 'day']);
  const pack = params.get('pack') || 'characters';
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: 0x2a3322, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  r.scene.add(ground);

  const mixers: THREE.AnimationMixer[] = [];
  let names: string[] = [];
  const spacing = Number(params.get('spacing') || 3);
  if (pack === 'characters') {
    names = [...CHARACTER_IDS];
    const clip = params.get('clip') || 'Idle';
    names.forEach((n, i) => {
      const c = Assets.character(n as never);
      c.position.set((i - names.length / 2) * 1.6, 0, 0);
      r.scene.add(c);
      const m = new THREE.AnimationMixer(c);
      m.clipAction(Assets.clip(clip)).play();
      m.update(0.4 + i * 0.1);
      mixers.push(m);
    });
  } else {
    names = Assets.propNames(pack as PropPack).filter((n) => !params.get('filter') || n.includes(params.get('filter')!));
    const cols = Math.ceil(Math.sqrt(names.length));
    names.forEach((n, i) => {
      const o = Assets.prop(pack as PropPack, n);
      const x = (i % cols) - cols / 2, z = Math.floor(i / cols) - cols / 2;
      o.position.set(x * spacing, 0, z * spacing);
      r.scene.add(o);
    });
    console.log('gallery', names.map((n, i) => `${i}:${n}`).join(' '));
  }
  const extent = pack === 'characters' ? 8 : Math.ceil(Math.sqrt(names.length)) * spacing;
  atmo.shadowExtent = extent;
  atmo.configureShadow();
  atmo.follow(0, 0, 0);
  const cam = r.camera;
  const dist = Number(params.get('dist') || extent * 1.1);
  const pitch = THREE.MathUtils.degToRad(Number(params.get('pitch') || 50));
  const yaw = THREE.MathUtils.degToRad(Number(params.get('yaw') || 0));
  cam.position.set(Math.sin(yaw) * Math.cos(pitch) * dist, Math.sin(pitch) * dist + (pack === 'characters' ? 1 : 0), Math.cos(yaw) * Math.cos(pitch) * dist);
  cam.lookAt(0, pack === 'characters' ? 1 : 0, 0);
  return (dt: number, t: number) => {
    for (const m of mixers) m.update(dt);
    atmo.update(t, cam.position);
  };
}
