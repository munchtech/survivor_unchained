import { Uniform, Vector3, Color } from 'three';
import { Effect, BlendFunction } from 'postprocessing';

/* The look of the game, as one pass after tone mapping.
 *
 * Stylized dark fantasy lives or dies on value structure: deep, cool shadows
 * that still hold colour, warm light that reads as fire rather than white, and
 * midtones with enough saturation that a creature's silhouette separates from
 * the ground. Each control below is one of those levers:
 *
 *   lift / gamma / gain   the classic three-way corrector, per channel
 *   shadowTint / highlightTint   split toning, weighted by luminance
 *   saturation / vibrance       vibrance boosts dull colours more than bright ones
 *   contrast              an S-curve in perceptual space around mid grey
 *
 * Presets live in lighting.ts beside the time of day they belong to, so
 * dusk, night and dawn each grade differently. */

const fragment = /* glsl */ `
uniform vec3 uLift;
uniform vec3 uGamma;
uniform vec3 uGain;
uniform vec3 uShadowTint;
uniform vec3 uHighlightTint;
uniform float uSaturation;
uniform float uVibrance;
uniform float uContrast;
uniform float uTintStrength;
uniform float uDamage;
uniform float uDesaturate;

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec3 c = max(inputColor.rgb, 0.0);

  // Work in a perceptual space so the controls behave like a colourist's.
  vec3 p = pow(c, vec3(1.0 / 2.2));

  // Lift / gamma / gain.
  p = uGain * (p + uLift * (1.0 - p));
  p = pow(max(p, 0.0), 1.0 / max(uGamma, vec3(0.01)));

  // Contrast S-curve around 0.5.
  vec3 s = p - 0.5;
  p = 0.5 + s * uContrast / (1.0 + abs(s) * (uContrast - 1.0) * 1.2);

  // Split toning.
  float l = luma(p);
  float sh = 1.0 - smoothstep(0.0, 0.55, l);
  float hi = smoothstep(0.45, 1.0, l);
  p += (uShadowTint - 0.5) * sh * uTintStrength;
  p += (uHighlightTint - 0.5) * hi * uTintStrength;

  // Saturation and vibrance.
  l = luma(p);
  vec3 grey = vec3(l);
  float sat = max(max(p.r, p.g), p.b) - min(min(p.r, p.g), p.b);
  float vib = 1.0 + uVibrance * (1.0 - sat);
  p = mix(grey, p, uSaturation * vib * (1.0 - uDesaturate));

  // Taking damage pulls the edges toward a bruised red.
  vec2 d = uv - 0.5;
  float edge = smoothstep(0.25, 0.75, length(d * vec2(1.4, 1.0)));
  p = mix(p, p * vec3(1.25, 0.55, 0.5) + vec3(0.12, 0.0, 0.0), uDamage * edge);

  outputColor = vec4(pow(clamp(p, 0.0, 1.0), vec3(2.2)), inputColor.a);
}
`;

export interface GradeSettings {
  lift: [number, number, number];
  gamma: [number, number, number];
  gain: [number, number, number];
  shadowTint: string;
  highlightTint: string;
  tintStrength: number;
  saturation: number;
  vibrance: number;
  contrast: number;
}

export class GradeEffect extends Effect {
  constructor() {
    super('GradeEffect', fragment, {
      blendFunction: BlendFunction.SRC,
      uniforms: new Map<string, Uniform>([
        ['uLift', new Uniform(new Vector3(0, 0, 0))],
        ['uGamma', new Uniform(new Vector3(1, 1, 1))],
        ['uGain', new Uniform(new Vector3(1, 1, 1))],
        ['uShadowTint', new Uniform(new Vector3(0.5, 0.5, 0.5))],
        ['uHighlightTint', new Uniform(new Vector3(0.5, 0.5, 0.5))],
        ['uTintStrength', new Uniform(0.2)],
        ['uSaturation', new Uniform(1)],
        ['uVibrance', new Uniform(0)],
        ['uContrast', new Uniform(1)],
        ['uDamage', new Uniform(0)],
        ['uDesaturate', new Uniform(0)],
      ]),
    });
  }

  private tmp = new Color();

  apply(g: GradeSettings) {
    const u = this.uniforms;
    (u.get('uLift')!.value as Vector3).set(...g.lift);
    (u.get('uGamma')!.value as Vector3).set(...g.gamma);
    (u.get('uGain')!.value as Vector3).set(...g.gain);
    this.tmp.set(g.shadowTint);
    (u.get('uShadowTint')!.value as Vector3).set(this.tmp.r, this.tmp.g, this.tmp.b);
    this.tmp.set(g.highlightTint);
    (u.get('uHighlightTint')!.value as Vector3).set(this.tmp.r, this.tmp.g, this.tmp.b);
    u.get('uTintStrength')!.value = g.tintStrength;
    u.get('uSaturation')!.value = g.saturation;
    u.get('uVibrance')!.value = g.vibrance;
    u.get('uContrast')!.value = g.contrast;
  }

  set damage(v: number) { this.uniforms.get('uDamage')!.value = v; }
  set desaturate(v: number) { this.uniforms.get('uDesaturate')!.value = v; }
}
