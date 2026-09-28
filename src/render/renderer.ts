import * as THREE from 'three';
import {
  EffectComposer, RenderPass, EffectPass, BloomEffect, ToneMappingEffect, ToneMappingMode,
  SMAAEffect, SMAAPreset, VignetteEffect, NoiseEffect, BlendFunction, ChromaticAberrationEffect,
} from 'postprocessing';
import { N8AOPostPass } from 'n8ao';
import { GradeEffect } from './grade';

/* The frame: one WebGL context, one scene graph, and the post chain that
 * gives it the look.
 *
 *   render -> ambient occlusion -> [bloom, tone map, grade, vignette]
 *          -> [SMAA, grain, a breath of chromatic aberration]
 *
 * Bloom runs on the HDR frame before tone mapping with a high threshold, so
 * only things that are actually emissive (embers, spells, lanterns, eyes)
 * glow - the ground never blooms. */

export type Quality = 'low' | 'medium' | 'high';

export interface QualitySpec {
  pixelRatio: number;
  shadowMapSize: number;
  ao: boolean;
  aoHalfRes: boolean;
  bloom: boolean;
  grassDensity: number;
  /** Without ambient occlusion the picture reads lighter and flatter; a
   *  touch less exposure keeps the mood. */
  exposureScale: number;
}

export const QUALITY: Record<Quality, QualitySpec> = {
  low: { pixelRatio: 1, shadowMapSize: 1024, ao: false, aoHalfRes: true, bloom: true, grassDensity: 0.35, exposureScale: 0.88 },
  medium: { pixelRatio: 1.5, shadowMapSize: 2048, ao: true, aoHalfRes: true, bloom: true, grassDensity: 0.7, exposureScale: 1 },
  high: { pixelRatio: 2, shadowMapSize: 4096, ao: true, aoHalfRes: false, bloom: true, grassDensity: 1, exposureScale: 1 },
};

export class Renderer {
  readonly gl: THREE.WebGLRenderer;
  readonly composer: EffectComposer;
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  readonly grade = new GradeEffect();
  readonly bloom: BloomEffect;
  readonly vignette: VignetteEffect;
  readonly chroma: ChromaticAberrationEffect;
  private renderPass: RenderPass;
  private ao: N8AOPostPass | null = null;
  private post: EffectPass;
  private finish: EffectPass;
  private toneMapping: ToneMappingEffect;
  quality: Quality;
  spec: QualitySpec;
  width = 1;
  height = 1;

  constructor(private host: HTMLElement, quality: Quality = 'high') {
    this.quality = quality;
    this.spec = QUALITY[quality];
    this.gl = new THREE.WebGLRenderer({
      antialias: false, stencil: false, depth: true, powerPreference: 'high-performance',
      preserveDrawingBuffer: false,
    });
    this.gl.outputColorSpace = THREE.SRGBColorSpace;
    this.gl.toneMapping = THREE.NoToneMapping;
    this.gl.shadowMap.enabled = true;
    this.gl.shadowMap.type = THREE.PCFShadowMap;
    this.gl.info.autoReset = false;
    host.appendChild(this.gl.domElement);
    this.gl.domElement.id = 'view';

    this.camera = new THREE.PerspectiveCamera(34, 16 / 9, 0.5, 1400);

    this.composer = new EffectComposer(this.gl, { frameBufferType: THREE.HalfFloatType, multisampling: 0 });
    this.renderPass = new RenderPass(this.scene, this.camera);
    this.composer.addPass(this.renderPass);

    this.bloom = new BloomEffect({
      mipmapBlur: true, luminanceThreshold: 0.9, luminanceSmoothing: 0.25, intensity: 1.35, radius: 0.72,
    });
    this.toneMapping = new ToneMappingEffect({ mode: ToneMappingMode.AGX });
    this.vignette = new VignetteEffect({ offset: 0.32, darkness: 0.62 });
    // SMAA and chromatic aberration are both convolutions and cannot share a
    // pass, so the fringe rides with the grade and SMAA finishes alone.
    this.chroma = new ChromaticAberrationEffect({ offset: new THREE.Vector2(0.0006, 0.0004), radialModulation: true, modulationOffset: 0.35 });
    this.post = new EffectPass(this.camera, this.bloom, this.toneMapping, this.grade, this.vignette, this.chroma);
    this.composer.addPass(this.post);

    const grain = new NoiseEffect({ blendFunction: BlendFunction.OVERLAY, premultiply: false });
    grain.blendMode.opacity.value = 0.055;
    this.finish = new EffectPass(this.camera, new SMAAEffect({ preset: SMAAPreset.HIGH }), grain);
    this.composer.addPass(this.finish);

    this.applyQuality();
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  setQuality(q: Quality) {
    this.quality = q;
    this.spec = QUALITY[q];
    this.applyQuality();
    this.exposure = this.baseExposure;
    this.resize();
  }

  private applyQuality() {
    const s = this.spec;
    if (s.ao && !this.ao) {
      this.ao = new N8AOPostPass(this.scene, this.camera, this.width, this.height);
      const c = this.ao.configuration;
      c.aoRadius = 1.6;
      c.distanceFalloff = 0.8;
      c.intensity = 2.4;
      c.color = new THREE.Color(0x07060a);
      c.gammaCorrection = false;
      this.ao.setQualityMode('Medium');
      this.composer.addPass(this.ao, 1);
    } else if (!s.ao && this.ao) {
      this.composer.removePass(this.ao);
      this.ao.dispose();
      this.ao = null;
    }
    if (this.ao) this.ao.configuration.halfRes = s.aoHalfRes;
    this.bloom.blendMode.opacity.value = s.bloom ? 1 : 0;
  }

  resize() {
    const w = this.host.clientWidth || window.innerWidth;
    const h = this.host.clientHeight || window.innerHeight;
    this.width = w;
    this.height = h;
    const dpr = Math.min(window.devicePixelRatio || 1, this.spec.pixelRatio);
    this.gl.setPixelRatio(dpr);
    this.gl.setSize(w, h, false);
    this.gl.domElement.style.width = `${w}px`;
    this.gl.domElement.style.height = `${h}px`;
    this.composer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  render(dt: number) {
    this.gl.info.reset();
    this.composer.render(dt);
  }

  private baseExposure = 1;
  set exposure(v: number) {
    // The AgX operator reads the renderer's exposure.
    this.baseExposure = v;
    this.gl.toneMappingExposure = v * this.spec.exposureScale;
  }
}
