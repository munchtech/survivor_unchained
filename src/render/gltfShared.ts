import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js';

/* A glTF loader whose images are shared by file across every model it
 * loads (an outfit's four parts, a village's hundred wall pieces all paint
 * from the same few sheets): each image is fetched and decoded once, and
 * every texture made from it is a copy over the one source, so the GPU
 * holds it once too.
 *
 * The people's and the kits' sheets are KTX2 (tools/assets/ktx2.py): Basis
 * UASTC, transcoded in a worker to whatever the GPU takes compressed (BC7 on
 * a desktop), a quarter of the memory of the same image decoded. A
 * compressed texture cannot be drawn on a canvas, so an image that the CPU
 * needs to read (a person's colours, for the crowd bake) names a small
 * readable copy in its extras, loaded beside it: readableImage(). */

const BASIS = `${import.meta.env.BASE_URL}assets/basis/`;
let ktx2: KTX2Loader | null = null;

/** Once, before anything loads: what the GPU can take compressed. */
export function initTextures(renderer: THREE.WebGLRenderer) {
  ktx2Loader().detectSupport(renderer);
}

function ktx2Loader() {
  // One loader, so one pool of transcoding workers.
  if (!ktx2) ktx2 = new KTX2Loader().setTranscoderPath(BASIS).setWorkerLimit(4);
  return ktx2;
}

const images = new Map<string, Promise<THREE.Texture>>();
const readable = new WeakMap<object, CanvasImageSource>();
const imageLoader = new THREE.ImageLoader();

/** Pixels the CPU can read for a texture: its readable copy when it is
 *  compressed, else its own image. */
export function readableImage(t: THREE.Texture | null | undefined): CanvasImageSource | undefined {
  if (!t) return undefined;
  const r = readable.get(t.source);
  if (r) return r;
  const img = t.image as CanvasImageSource & { width?: number };
  return img && (img instanceof HTMLImageElement || img instanceof HTMLCanvasElement || img instanceof ImageBitmap) ? img : undefined;
}

export function sharedLoader() {
  const loader = new GLTFLoader();
  loader.setKTX2Loader(ktx2Loader());
  loader.register((parser) => {
    const own = parser.loadImageSource.bind(parser);
    parser.loadImageSource = (index: number, imageLoaderOf: THREE.Loader) => {
      const def = parser.json.images?.[index] as { uri?: string; extras?: { readable?: string } } | undefined;
      const uri = def?.uri;
      if (!uri || uri.startsWith('data:')) return own(index, imageLoaderOf);
      const base = new URL(parser.options.path, location.href);
      const key = new URL(uri, base).href;
      let p = images.get(key);
      if (!p) {
        p = own(index, imageLoaderOf);
        const copy = def?.extras?.readable;
        if (copy) {
          p = Promise.all([p, imageLoader.loadAsync(new URL(copy, base).href)]).then(([t, img]) => {
            readable.set(t.source, img);
            return t;
          });
        }
        images.set(key, p);
      }
      return p.then((t) => t.clone());
    };
    return { name: 'shared_images' };
  });
  return loader;
}
