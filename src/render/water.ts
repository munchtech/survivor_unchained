import * as THREE from 'three';
import { noiseTexture } from './noiseTex';

/* Still and slow water: a river ford, a stream, a well.
 *
 * One plane per body of water. The surface is mirror-smooth in the base
 * material (so it picks up the sky from the environment map and a long
 * glint from the moon or sun), and its normal is broken up in the fragment
 * shader by two layers of the shared noise drifting against each other,
 * which is what makes it read as moving water rather than glass. A fresnel
 * term darkens it looking straight down and brightens it at a grazing
 * angle; a `murk` colour decides whether it is clear, peaty or poisoned. */

export interface WaterOpts {
  width: number;
  depth: number;
  color?: string;
  murk?: string;
  flow?: [number, number];
  opacity?: number;
  glow?: number;
  /** The sky it reflects, added at grazing angles. */
  sky?: string;
}

export const waterUniforms = { uTime: { value: 0 } };

export function createWater(o: WaterOpts): THREE.Mesh {
  const geo = new THREE.PlaneGeometry(o.width, o.depth, 1, 1);
  geo.rotateX(-Math.PI / 2);
  const mat = new THREE.MeshStandardMaterial({
    color: o.color ?? '#0e1c20', roughness: 0.06, metalness: 0.0, transparent: true, opacity: o.opacity ?? 0.86,
    envMapIntensity: 1.6, depthWrite: false,
  });
  const flow = o.flow ?? [0.02, 0.35];
  const murk = new THREE.Color(o.murk ?? '#061012');
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = waterUniforms.uTime;
    sh.uniforms.uNoise = { value: noiseTexture() };
    sh.uniforms.uFlow = { value: new THREE.Vector2(...flow) };
    sh.uniforms.uMurk = { value: murk };
    sh.uniforms.uGlow = { value: o.glow ?? 0 };
    sh.uniforms.uSky = { value: new THREE.Color(o.sky ?? '#1c2c3c') };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vWPos;
uniform float uTime;
uniform sampler2D uNoise;
uniform vec2 uFlow;
uniform vec3 uMurk;
uniform float uGlow;
uniform vec3 uSky;
float wh(vec2 p) {
  vec2 a = p * 0.045 + uFlow * uTime * 0.05;
  vec2 b = p * 0.11 - uFlow.yx * uTime * 0.07 + 3.7;
  return texture2D(uNoise, a).g * 0.6 + texture2D(uNoise, b).b * 0.4;
}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  float e = 0.35;
  float h0 = wh(vWPos.xz);
  float hx = wh(vWPos.xz + vec2(e, 0.0));
  float hz = wh(vWPos.xz + vec2(0.0, e));
  vec3 nW = normalize(vec3(-(hx - h0) * 1.3, 1.0, -(hz - h0) * 1.3));
  normal = normalize((viewMatrix * vec4(nW, 0.0)).xyz);
}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  float fres = pow(1.0 - clamp(dot(normalize(vViewPosition), normal), 0.0, 1.0), 3.0);
  diffuseColor.rgb = mix(uMurk, diffuseColor.rgb, 0.35 + fres * 0.65);
  totalEmissiveRadiance += uMurk * uGlow * (0.6 + 0.4 * wh(vWPos.xz * 2.0));
  float ripple = smoothstep(0.52, 0.7, wh(vWPos.xz * 1.7));
  totalEmissiveRadiance += uSky * (0.25 + fres * 1.1 + ripple * 0.35);
}`);
  };
  const m = new THREE.Mesh(geo, mat);
  m.receiveShadow = true;
  m.renderOrder = 2;
  m.name = 'water';
  return m;
}
