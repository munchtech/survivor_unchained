import * as THREE from 'three';

/* The sky dome. The game camera looks down steeply enough that the sky is
 * almost never in frame; what the dome really does is light the world: it is
 * rendered into a PMREM environment map that every PBR surface samples for
 * its ambient and specular, so a cold night sky makes metal read cold and a
 * dawn sky warms every rooftop. It is seen directly in character creation,
 * in the title and when the camera tilts up for a moment of drama. */

const vertex = /* glsl */ `
varying vec3 vDir;
void main() {
  vDir = normalize(position);
  vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  gl_Position = p.xyww; // pinned to the far plane
}
`;

const fragment = /* glsl */ `
uniform vec3 uTop;
uniform vec3 uHorizon;
uniform vec3 uBottom;
uniform vec3 uGlow;
uniform vec3 uLightDir;
uniform float uGlowPower;
uniform float uStars;
uniform float uMoon;
uniform float uTime;
varying vec3 vDir;

float hash(vec3 p) {
  p = fract(p * 0.3183099 + 0.1);
  p *= 17.0;
  return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
  vec3 i = floor(x), f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),
                 mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
                 mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}

void main() {
  vec3 d = normalize(vDir);
  float h = d.y;
  vec3 col = h > 0.0
    ? mix(uHorizon, uTop, pow(smoothstep(0.0, 1.0, h), 0.55))
    : mix(uHorizon, uBottom, smoothstep(0.0, 0.35, -h));

  // Glow around the light, flattened toward the horizon like real haze.
  float cosA = max(dot(d, normalize(uLightDir)), 0.0);
  col += uGlow * pow(cosA, uGlowPower) * (0.6 + 0.4 * (1.0 - abs(h)));
  col += uGlow * 0.25 * pow(1.0 - abs(h), 6.0);

  // Stars: sparse hashed points, twinkling, fading into the haze.
  if (uStars > 0.0 && h > 0.0) {
    vec3 sp = d * 420.0;
    vec3 cell = floor(sp);
    float r = hash(cell);
    if (r > 0.9965) {
      vec3 center = cell + 0.5 + (vec3(hash(cell + 1.3), hash(cell + 2.7), hash(cell + 4.1)) - 0.5) * 0.6;
      float dd = length(sp - center);
      float tw = 0.6 + 0.4 * sin(uTime * (1.0 + r * 6.0) + r * 40.0);
      col += vec3(0.85, 0.9, 1.0) * smoothstep(0.35, 0.0, dd) * tw * uStars * smoothstep(0.02, 0.3, h) * 3.0;
    }
  }

  // Moon disc with a soft, cratered face.
  if (uMoon > 0.0) {
    float m = dot(d, normalize(uLightDir));
    float disc = smoothstep(0.99955, 0.99975, m);
    float face = 0.78 + 0.22 * noise(d * 900.0);
    col = mix(col, vec3(1.25, 1.22, 1.12) * face * 2.2, disc * uMoon);
  }

  // Thin high cloud banding, very faint.
  float c = noise(vec3(d.xz / max(h, 0.08) * 1.6, uTime * 0.01));
  col = mix(col, col * 0.82 + uGlow * 0.05, smoothstep(0.55, 0.85, c) * smoothstep(0.0, 0.25, h) * 0.5);

  gl_FragColor = vec4(col, 1.0);
}
`;

export interface SkySettings {
  top: string;
  horizon: string;
  bottom: string;
  glow: string;
  glowPower: number;
  stars: number;
  moon: number;
}

export class Sky {
  readonly mesh: THREE.Mesh;
  readonly material: THREE.ShaderMaterial;

  constructor() {
    this.material = new THREE.ShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        uTop: { value: new THREE.Color() },
        uHorizon: { value: new THREE.Color() },
        uBottom: { value: new THREE.Color() },
        uGlow: { value: new THREE.Color() },
        uLightDir: { value: new THREE.Vector3(0, 1, 0) },
        uGlowPower: { value: 8 },
        uStars: { value: 0 },
        uMoon: { value: 0 },
        uTime: { value: 0 },
      },
    });
    this.mesh = new THREE.Mesh(new THREE.SphereGeometry(1000, 48, 24), this.material);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = -1000;
  }

  apply(s: SkySettings, lightDir: THREE.Vector3) {
    const u = this.material.uniforms;
    (u.uTop.value as THREE.Color).set(s.top);
    (u.uHorizon.value as THREE.Color).set(s.horizon);
    (u.uBottom.value as THREE.Color).set(s.bottom);
    (u.uGlow.value as THREE.Color).set(s.glow);
    u.uGlowPower.value = s.glowPower;
    u.uStars.value = s.stars;
    u.uMoon.value = s.moon;
    (u.uLightDir.value as THREE.Vector3).copy(lightDir);
  }

  update(t: number, center: THREE.Vector3) {
    this.material.uniforms.uTime.value = t;
    this.mesh.position.copy(center);
  }
}
