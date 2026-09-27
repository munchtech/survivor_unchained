import * as THREE from 'three';
import { CharacterView } from '@/render/characterView';
import { applyLook, type Loadout } from '@/render/playerView';

/* A portrait of the survivor for the pack and the character sheet: the
 * real model in its real gear, lit like the item photographs, standing in
 * a three-quarter pose. Rendered on demand into a transparent image. */

export function renderPortrait(lo: Loadout, w = 300, h = 420, framing: 'full' | 'bust' = 'full', scale = 1): string | null {
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  let gl: THREE.WebGLRenderer;
  try {
    gl = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
  } catch {
    return null;
  }
  gl.setClearColor(0, 0);
  gl.outputColorSpace = THREE.SRGBColorSpace;
  gl.toneMapping = THREE.ACESFilmicToneMapping;
  gl.toneMappingExposure = 1.1;
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(22, w / h, 0.1, 50);
  if (framing === 'full') {
    cam.position.set(1.6, 1.45, 5.6);
    cam.lookAt(0, 0.95, 0);
  } else {
    // Head and shoulders, a little from below: people you talk to.
    cam.position.set(0.9 * scale, 1.7 * scale, 3.3 * scale);
    cam.lookAt(0, 1.45 * scale, 0);
  }
  const key = new THREE.DirectionalLight(0xffd8a8, 3.4);
  key.position.set(-2.5, 3.5, 3);
  const rim = new THREE.DirectionalLight(0x8ab4ff, 3.0);
  rim.position.set(2.5, 2.5, -3.5);
  const fill = new THREE.HemisphereLight(0xb8c4e0, 0x3a2a1a, 1.0);
  scene.add(key, rim, fill);
  const v = new CharacterView(lo.model, { scale: 0.8 * scale });
  v.showOnly(lo.show);
  applyLook(v, lo);
  v.face(0.35, true);
  v.loop(lo.model === 'mage' || lo.model === 'knight' ? 'Idle' : 'Idle_B', 0);
  v.update(0.8);
  scene.add(v.root);
  gl.render(scene, cam);
  const url = canvas.toDataURL('image/png');
  v.dispose();
  gl.dispose();
  gl.forceContextLoss();
  return url;
}
