import * as THREE from 'three';

/* KayKit people are drawn chibi: a head nearly as wide as the shoulders, a
 * short body on stubby legs. For a grimmer world they are brought nearer to
 * life through their own bones: the head smaller, the torso and the legs
 * longer. The animation writes the bones every frame, so this is applied
 * after every pose, in the live figures (the survivor, the townsfolk,
 * bosses) and in the baked crowds alike.
 *
 * A bone stretched along its length stretches its children too; where a
 * child should not be (the chest over a longer spine, a foot under a longer
 * shin) the child takes the inverse back. Longer legs would put the feet
 * through the ground, so the figure is lifted by what they gained, measured
 * once per model in its rest pose. Anything worn on the head (a helm, a
 * hood) is parented to the bone and shrinks with it. */

export const PROPORTIONS = { head: 0.6, torso: 1.25, legs: 1.8 };

type BoneGet = (name: string) => THREE.Object3D | undefined;

export function applyProportions(bones: Map<string, THREE.Object3D> | BoneGet, p = PROPORTIONS) {
  const get: BoneGet = typeof bones === 'function' ? bones : (n) => bones.get(n);
  const head = get('head');
  if (head) head.scale.setScalar(p.head);
  const spine = get('spine'), chest = get('chest');
  if (spine && chest) { spine.scale.set(1, p.torso, 1); chest.scale.set(1, 1 / p.torso, 1); }
  for (const side of ['l', 'r']) {
    const upper = get(`upperleg${side}`) ?? get(`upperleg.${side}`);
    const foot = get(`foot${side}`) ?? get(`foot.${side}`);
    if (upper) upper.scale.set(1, p.legs, 1);
    if (foot) foot.scale.set(1, 1 / p.legs, 1);
  }
}

/** How far to lift a figure so its longer legs stand on the ground: the
 *  drop of its lowest foot bone once the proportions are applied, in the
 *  model's own (unscaled) space. The root must be in its rest pose. */
export function legLift(root: THREE.Object3D, bones: Map<string, THREE.Object3D>, p = PROPORTIONS) {
  const feet = [...bones.entries()].filter(([n]) => /^(foot|toes)/.test(n)).map(([, b]) => b);
  if (!feet.length) return 0;
  const inv = new THREE.Matrix4();
  const low = () => {
    root.updateMatrixWorld(true);
    inv.copy(root.matrixWorld).invert();
    let y = Infinity;
    for (const f of feet) y = Math.min(y, new THREE.Vector3().setFromMatrixPosition(f.matrixWorld).applyMatrix4(inv).y);
    return y;
  };
  const saved = [...bones.values()].map((b) => b.scale.clone());
  const before = low();
  applyProportions(bones, p);
  const after = low();
  [...bones.values()].forEach((b, i) => b.scale.copy(saved[i]));
  root.updateMatrixWorld(true);
  return Math.max(0, before - after);
}
