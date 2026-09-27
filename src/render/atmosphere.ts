import * as THREE from 'three';
import { Sky, type SkySettings } from './sky';
import type { GradeSettings } from './grade';
import type { Renderer } from './renderer';
import { lerp } from '@/core/math';

/* Light, air and colour for a moment of the day.
 *
 * A preset is everything that changes together when the hour changes: the
 * key light (moon or sun) and its colour, the fill from the sky, the fog, the
 * sky dome, exposure and the colour grade. Presets blend, so dusk can slide
 * into night over an expedition and dawn can break over a boss's corpse.
 *
 * The key light owns the only shadow map. Its orthographic frustum is small
 * and follows a focus point (the survivor), which is what keeps shadows
 * crisp at the scale characters are drawn at. */

export interface AtmospherePreset {
  sky: SkySettings;
  keyColor: string;
  keyIntensity: number;
  keyElevation: number; // degrees above horizon
  keyAzimuth: number; // degrees, 0 = +x, 90 = +z
  hemiSky: string;
  hemiGround: string;
  hemiIntensity: number;
  envIntensity: number;
  fogColor: string;
  fogDensity: number;
  exposure: number;
  grade: GradeSettings;
}

const NIGHT: AtmospherePreset = {
  sky: { top: '#03050d', horizon: '#18203a', bottom: '#07080c', glow: '#3c5a8c', glowPower: 24, stars: 1, moon: 1 },
  keyColor: '#b8cbf2', keyIntensity: 2.2, keyElevation: 52, keyAzimuth: 128,
  hemiSky: '#3f5780', hemiGround: '#241e16', hemiIntensity: 0.95, envIntensity: 0.6,
  fogColor: '#101a24', fogDensity: 0.0095, exposure: 1.42,
  grade: {
    lift: [0.015, 0.025, 0.04], gamma: [1.0, 1.0, 1.02], gain: [1.03, 1.0, 0.97],
    shadowTint: '#35646e', highlightTint: '#e6a25a', tintStrength: 0.2,
    saturation: 1.1, vibrance: 0.35, contrast: 1.14,
  },
};

/** Night inside walls: the moon is a cold wash, and what light there is
 *  comes from lamps, doorways and braziers. Darker and bluer than the wild
 *  night, which has to stay readable for a fight. */
const NIGHT_TOWN: AtmospherePreset = {
  ...NIGHT,
  sky: { ...NIGHT.sky, glow: '#2c4470' },
  keyColor: '#9fb6e6', keyIntensity: 1.35, keyElevation: 48,
  hemiSky: '#2c3e62', hemiGround: '#1a150f', hemiIntensity: 0.58, envIntensity: 0.4,
  fogColor: '#0b121c', fogDensity: 0.011, exposure: 1.32,
  grade: {
    ...NIGHT.grade,
    lift: [0.01, 0.018, 0.035], shadowTint: '#2a4a66', highlightTint: '#ffa34e', tintStrength: 0.3,
    saturation: 1.08, vibrance: 0.4, contrast: 1.18,
  },
};

const DUSK: AtmospherePreset = {
  sky: { top: '#141a36', horizon: '#b0583a', bottom: '#120c0c', glow: '#ff8a4a', glowPower: 7, stars: 0.25, moon: 0 },
  keyColor: '#ffae70', keyIntensity: 2.3, keyElevation: 18, keyAzimuth: 200,
  hemiSky: '#5a5a90', hemiGround: '#2a1a10', hemiIntensity: 0.7, envIntensity: 0.7,
  fogColor: '#3a2a34', fogDensity: 0.0085, exposure: 1.05,
  grade: {
    lift: [0.03, 0.02, 0.05], gamma: [1.0, 1.0, 1.02], gain: [1.05, 1.0, 0.95],
    shadowTint: '#4a4a8a', highlightTint: '#ffb070', tintStrength: 0.2,
    saturation: 1.1, vibrance: 0.3, contrast: 1.12,
  },
};

const DAWN: AtmospherePreset = {
  sky: { top: '#3b5a8f', horizon: '#f2b48a', bottom: '#2a2220', glow: '#ffd2a0', glowPower: 6, stars: 0, moon: 0 },
  keyColor: '#ffd1a0', keyIntensity: 2.8, keyElevation: 22, keyAzimuth: 20,
  hemiSky: '#8aa0d0', hemiGround: '#3a2a1a', hemiIntensity: 0.85, envIntensity: 0.85,
  fogColor: '#a89aa0', fogDensity: 0.0065, exposure: 1.0,
  grade: {
    lift: [0.02, 0.02, 0.04], gamma: [1.0, 1.0, 1.0], gain: [1.04, 1.01, 0.97],
    shadowTint: '#56709a', highlightTint: '#ffc88a', tintStrength: 0.16,
    saturation: 1.06, vibrance: 0.3, contrast: 1.1,
  },
};

const DAY: AtmospherePreset = {
  sky: { top: '#2f5fa8', horizon: '#b8cde0', bottom: '#3a3530', glow: '#fff1d6', glowPower: 10, stars: 0, moon: 0 },
  keyColor: '#fff0da', keyIntensity: 3.2, keyElevation: 48, keyAzimuth: 55,
  hemiSky: '#9ab8e6', hemiGround: '#4a3a28', hemiIntensity: 0.95, envIntensity: 0.9,
  fogColor: '#9fb0c0', fogDensity: 0.0045, exposure: 0.95,
  grade: {
    lift: [0.01, 0.015, 0.03], gamma: [1.0, 1.0, 1.0], gain: [1.02, 1.01, 0.99],
    shadowTint: '#4a6a9a', highlightTint: '#ffe0b0', tintStrength: 0.12,
    saturation: 1.05, vibrance: 0.25, contrast: 1.08,
  },
};

export const PRESETS = { night: NIGHT, nightTown: NIGHT_TOWN, dusk: DUSK, dawn: DAWN, day: DAY } as const;
export type PresetName = keyof typeof PRESETS;

function mixHex(a: string, b: string, t: number) {
  return '#' + new THREE.Color(a).lerp(new THREE.Color(b), t).getHexString();
}
function mixTriple(a: [number, number, number], b: [number, number, number], t: number): [number, number, number] {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
}

export function blendPresets(a: AtmospherePreset, b: AtmospherePreset, t: number): AtmospherePreset {
  return {
    sky: {
      top: mixHex(a.sky.top, b.sky.top, t), horizon: mixHex(a.sky.horizon, b.sky.horizon, t),
      bottom: mixHex(a.sky.bottom, b.sky.bottom, t), glow: mixHex(a.sky.glow, b.sky.glow, t),
      glowPower: lerp(a.sky.glowPower, b.sky.glowPower, t), stars: lerp(a.sky.stars, b.sky.stars, t),
      moon: lerp(a.sky.moon, b.sky.moon, t),
    },
    keyColor: mixHex(a.keyColor, b.keyColor, t), keyIntensity: lerp(a.keyIntensity, b.keyIntensity, t),
    keyElevation: lerp(a.keyElevation, b.keyElevation, t), keyAzimuth: lerp(a.keyAzimuth, b.keyAzimuth, t),
    hemiSky: mixHex(a.hemiSky, b.hemiSky, t), hemiGround: mixHex(a.hemiGround, b.hemiGround, t),
    hemiIntensity: lerp(a.hemiIntensity, b.hemiIntensity, t), envIntensity: lerp(a.envIntensity, b.envIntensity, t),
    fogColor: mixHex(a.fogColor, b.fogColor, t), fogDensity: lerp(a.fogDensity, b.fogDensity, t),
    exposure: lerp(a.exposure, b.exposure, t),
    grade: {
      lift: mixTriple(a.grade.lift, b.grade.lift, t), gamma: mixTriple(a.grade.gamma, b.grade.gamma, t),
      gain: mixTriple(a.grade.gain, b.grade.gain, t),
      shadowTint: mixHex(a.grade.shadowTint, b.grade.shadowTint, t),
      highlightTint: mixHex(a.grade.highlightTint, b.grade.highlightTint, t),
      tintStrength: lerp(a.grade.tintStrength, b.grade.tintStrength, t),
      saturation: lerp(a.grade.saturation, b.grade.saturation, t),
      vibrance: lerp(a.grade.vibrance, b.grade.vibrance, t),
      contrast: lerp(a.grade.contrast, b.grade.contrast, t),
    },
  };
}

export class Atmosphere {
  readonly sky = new Sky();
  readonly key: THREE.DirectionalLight;
  readonly hemi: THREE.HemisphereLight;
  readonly fog: THREE.FogExp2;
  private envScene = new THREE.Scene();
  private envSky = new Sky();
  private pmrem: THREE.PMREMGenerator;
  private envTarget: THREE.WebGLRenderTarget | null = null;
  current: AtmospherePreset = NIGHT;
  private lightDir = new THREE.Vector3();
  private focus = new THREE.Vector3();
  shadowExtent = 26;

  constructor(private r: Renderer) {
    this.key = new THREE.DirectionalLight(0xffffff, 1);
    this.key.castShadow = true;
    this.key.shadow.bias = -0.0004;
    this.key.shadow.normalBias = 0.035;
    this.key.shadow.radius = 3;
    this.hemi = new THREE.HemisphereLight(0xffffff, 0x000000, 1);
    this.fog = new THREE.FogExp2(0x000000, 0.01);
    r.scene.add(this.key, this.key.target, this.hemi, this.sky.mesh);
    r.scene.fog = this.fog;
    this.envScene.add(this.envSky.mesh);
    this.pmrem = new THREE.PMREMGenerator(r.gl);
    this.configureShadow();
  }

  configureShadow() {
    const s = this.key.shadow;
    const size = this.r.spec.shadowMapSize;
    s.mapSize.set(size, size);
    const cam = s.camera as THREE.OrthographicCamera;
    const e = this.shadowExtent;
    cam.left = -e; cam.right = e; cam.top = e; cam.bottom = -e;
    cam.near = 1; cam.far = 220;
    cam.updateProjectionMatrix();
    if (s.map) { s.map.dispose(); (s as unknown as { map: null }).map = null; }
  }

  set(p: AtmospherePreset, rebuildEnv = true) {
    this.current = p;
    const el = THREE.MathUtils.degToRad(p.keyElevation);
    const az = THREE.MathUtils.degToRad(p.keyAzimuth);
    this.lightDir.set(Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az)).normalize();
    this.key.color.set(p.keyColor);
    this.key.intensity = p.keyIntensity;
    this.hemi.color.set(p.hemiSky);
    this.hemi.groundColor.set(p.hemiGround);
    this.hemi.intensity = p.hemiIntensity;
    this.fog.color.set(p.fogColor);
    this.fog.density = p.fogDensity;
    this.r.exposure = p.exposure;
    this.r.grade.apply(p.grade);
    this.sky.apply(p.sky, this.lightDir);
    this.r.scene.environmentIntensity = p.envIntensity;
    if (rebuildEnv) this.rebuildEnvironment();
    this.placeKey();
  }

  /** Re-render the sky into the environment map. Costs a few milliseconds;
   *  call it when the preset changes meaningfully, not every frame. */
  rebuildEnvironment() {
    this.envSky.apply(this.current.sky, this.lightDir);
    // Stars and the moon disc would sparkle on every glossy surface.
    this.envSky.material.uniforms.uStars.value = 0;
    this.envSky.material.uniforms.uMoon.value = 0;
    const old = this.envTarget;
    this.envTarget = this.pmrem.fromScene(this.envScene, 0.04);
    this.r.scene.environment = this.envTarget.texture;
    old?.dispose();
  }

  /** Keep the shadow frustum centred on what matters, snapped to texels so
   *  shadow edges do not shimmer as the survivor walks. */
  follow(x: number, y: number, z: number) {
    this.focus.set(x, y, z);
    this.placeKey();
  }

  private placeKey() {
    const cam = this.key.shadow.camera as THREE.OrthographicCamera;
    const texel = (cam.right - cam.left) / this.key.shadow.mapSize.x;
    // Snap in light space: project the focus onto the light's right/up axes.
    const fwd = this.lightDir.clone().negate();
    const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
    const up = new THREE.Vector3().crossVectors(right, fwd).normalize();
    const r = Math.round(this.focus.dot(right) / texel) * texel;
    const u = Math.round(this.focus.dot(up) / texel) * texel;
    const f = this.focus.dot(fwd);
    const snapped = right.multiplyScalar(r).add(up.multiplyScalar(u)).add(fwd.multiplyScalar(f));
    this.key.target.position.copy(snapped);
    this.key.position.copy(snapped).addScaledVector(this.lightDir, 110);
    this.key.target.updateMatrixWorld();
  }

  update(t: number, cameraPos: THREE.Vector3) {
    this.sky.update(t, cameraPos);
  }
}
