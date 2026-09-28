import * as THREE from 'three';

/* A rim of light on every body: the survivor, the people, the horde. It is
 * what keeps a fight readable when the ground and the foe are the same dark
 * (a wolf on night grass): the edge of each figure turned from the camera
 * catches the moon, or the sky, and the silhouette reads. Strong and cold at
 * night, faint by day; the atmosphere's preset sets it (render/atmosphere.ts). */

/** rgb: the rim's colour, w: its strength. */
export const bodyRim = { value: new THREE.Vector4(0.55, 0.65, 0.9, 0) };

export const BODY_RIM_PARS = /* glsl */ `
uniform vec4 uBodyRim;`;

/** After emissive: the edge facing away from the camera, and more on the
 *  upper body than the feet (the light is the sky's). */
export const BODY_RIM = /* glsl */ `
{
  vec3 vN = normalize(normal);
  float f = 1.0 - clamp(dot(vN, normalize(vViewPosition)), 0.0, 1.0);
  float up = 0.55 + 0.45 * dot(vN, normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz));
  totalEmissiveRadiance += uBodyRim.rgb * (uBodyRim.w * f * f * f * up);
}`;

/** Give a material the rim (once; chains any shader changes it has). */
export function withBodyRim<M extends THREE.Material>(mat: M): M {
  if (mat.userData.bodyRim) return mat;
  mat.userData.bodyRim = true;
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    prev.call(mat, sh, r);
    sh.uniforms.uBodyRim = bodyRim;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>\n${BODY_RIM_PARS}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>\n${BODY_RIM}`);
  };
  const key = mat.customProgramCacheKey();
  mat.customProgramCacheKey = () => `${key}|rim`;
  return mat;
}
