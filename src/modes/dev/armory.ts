import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS } from '@/render/atmosphere';
import { ARMS, arm, preloadArms } from '@/render/arms';

/* Development view: every weapon model normalised (grip at the red dot,
 * shaft up +Y, width along +X), standing in a row with a 1 m rod for scale.
 * ?dev=armory (&yaw=90: each turned about its shaft, to see the thickness) */

export async function armoryDev(r: Renderer, params: URLSearchParams) {
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS.day);
  r.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(40, 40).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x3a3a34 })));
  await preloadArms();
  const ids = Object.keys(ARMS);
  ids.forEach((id, i) => {
    const o = arm(id)!;
    o.position.set((i - (ids.length - 1) / 2) * 0.62, 0.9, 0);
    o.rotation.y = THREE.MathUtils.degToRad(Number(params.get('yaw') ?? 0));
    r.scene.add(o);
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.03), new THREE.MeshBasicMaterial({ color: 0xff2020 }));
    dot.position.copy(o.position);
    r.scene.add(dot);
  });
  const rod = new THREE.Mesh(new THREE.BoxGeometry(0.02, 1, 0.02), new THREE.MeshBasicMaterial({ color: 0x40a0ff }));
  rod.position.set((ids.length / 2 + 0.2) * 0.62, 0.5, 0);
  r.scene.add(rod);
  atmo.shadowExtent = 6; atmo.configureShadow(); atmo.follow(0, 0, 0);
  r.camera.position.set(0, 1.1, 6.4);
  r.camera.lookAt(0, 1.05, 0);
  (window as unknown as { __arms: string }).__arms = ids.join(',');
  return (_dt: number, t: number) => atmo.update(t, r.camera.position);
}
