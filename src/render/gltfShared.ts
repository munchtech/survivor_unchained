import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/* A glTF loader whose images are shared by file across every model it
 * loads (an outfit's four parts, a village's hundred wall pieces all paint
 * from the same few sheets): each image is fetched and decoded once, and
 * every texture made from it is a copy over the one source, so the GPU
 * holds it once too. */

const images = new Map<string, Promise<THREE.Texture>>();

export function sharedLoader() {
  const loader = new GLTFLoader();
  loader.register((parser) => {
    const own = parser.loadImageSource.bind(parser);
    parser.loadImageSource = (index: number, imageLoader: THREE.Loader) => {
      const uri = (parser.json.images?.[index] as { uri?: string } | undefined)?.uri;
      if (!uri || uri.startsWith('data:')) return own(index, imageLoader);
      const key = new URL(uri, new URL(parser.options.path, location.href)).href;
      let p = images.get(key);
      if (!p) { p = own(index, imageLoader); images.set(key, p); }
      return p.then((t) => t.clone());
    };
    return { name: 'shared_images' };
  });
  return loader;
}
