declare module 'n8ao' {
  import type { Scene, Camera, Color } from 'three';
  import type { Pass } from 'postprocessing';
  export class N8AOPostPass extends Pass {
    constructor(scene: Scene, camera: Camera, width?: number, height?: number);
    configuration: {
      aoRadius: number; distanceFalloff: number; intensity: number; color: Color;
      gammaCorrection: boolean; halfRes: boolean; aoSamples: number; denoiseSamples: number;
      denoiseRadius: number; screenSpaceRadius: boolean; depthAwareUpsampling: boolean;
      transparencyAware: boolean; accumulate: boolean;
    };
    setQualityMode(mode: 'Performance' | 'Low' | 'Medium' | 'High' | 'Ultra'): void;
  }
}
