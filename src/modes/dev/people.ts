import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS, type PresetName } from '@/render/atmosphere';
import { Assets } from '@/render/assets';
import { assemble, peopleClips, preloadPeople, PARTS, type PersonSpec } from '@/render/people';
import { CharacterView, HUMAN_SOCKETS, basis } from '@/render/characterView';
import { preloadArms } from '@/render/arms';

/* Development view: Quaternius people in a row, dressed and animated, beside
 * a KayKit knight for scale. ?dev=people&clip=Idle_Loop&time=day */

export async function peopleDev(r: Renderer, params: URLSearchParams) {
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS[(params.get('time') as PresetName) || 'day']);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x3a3a30, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  r.scene.add(ground);
  const clips = await peopleClips();
  console.log('clips', [...clips.keys()].join(','));
  const specs: PersonSpec[] = [
    { sex: 'male', outfit: PARTS.male.peasant, hair: 'Hair_SimpleParted', beard: true, hairColor: '#3a2618' },
    { sex: 'female', outfit: PARTS.female.peasant, hair: 'Hair_Long', hairColor: '#6a3a1e' },
    { sex: 'male', outfit: [...PARTS.male.ranger, PARTS.male.hood, PARTS.male.pauldron], hairColor: '#1a1410' },
    { sex: 'female', outfit: [...PARTS.female.ranger, PARTS.female.pauldron], hair: 'Hair_Buns', hairColor: '#141010' },
    { sex: 'male', outfit: [PARTS.male.peasant[2], PARTS.male.peasant[3]], hair: 'Hair_Buzzed', beard: true, hairColor: '#8a5a2a' },
    { sex: 'female', outfit: [PARTS.female.peasant[2], PARTS.female.peasant[3]], hair: 'Hair_Long', hairColor: '#2a1a12', figure: Number(new URLSearchParams(location.search).get('figure') ?? 1) },
  ];
  // ?pick=3: only that one (quicker shots).
  if (params.get('pick')) specs.splice(0, specs.length, specs[Number(params.get('pick'))]);
  const mixers: THREE.AnimationMixer[] = [];
  const clipName = params.get('clip') || 'Idle_Loop';
  for (let i = 0; i < specs.length; i++) {
    const { root } = await assemble(specs[i]);
    root.position.set((i - (specs.length - 1) / 2) * 1.2, 0, 0);
    r.scene.add(root);
    const m = new THREE.AnimationMixer(root);
    const c = clips.get(clipName) ?? clips.get('Idle_Loop')!;
    m.clipAction(c).play();
    m.update(0.3 + i * 0.37);
    mixers.push(m);
  }
  // ?view=1: the same people through CharacterView (the game's own verbs:
  // KayKit clip names mapped, a sword socketed in the right hand).
  const views: CharacterView[] = [];
  if (params.get('view')) {
    await Promise.all([preloadPeople(), preloadArms()]);
    // What each figure holds: ?arms=chevalier_sword,mage_staff,... (a "+"
    // adds a left-hand piece: viking_sword+shield_round).
    const kit = (params.get('arms') || 'chevalier_sword,mage_staff,viking_sword+shield_round,crossbow,viking_axe,daggers+dagger_b').split(',');
    for (const m of mixers) m.stopAllAction();
    r.scene.children.filter((c) => c.type === 'Group').forEach((c) => c.removeFromParent());
    specs.forEach((sp, i) => {
      const v = new CharacterView(sp);
      v.root.position.set((i - (specs.length - 1) / 2) * 1.2, 0, 0);
      // ?grip=test: each figure holds it a different way (blade along +Z,
      // -Z, +X, -X of the hand), to find which is right.
      if (params.get('grip') === 'test') {
        const turns = [basis([0, 1, 0], [0, 0, 1]), basis([0, 1, 0], [0, 0, -1]), basis([0, 1, 0], [1, 0, 0]), basis([0, 1, 0], [-1, 0, 0]), basis([0, 0, 1], [1, 0, 0]), basis([0, 0, 1], [-1, 0, 0])];
        HUMAN_SOCKETS['handslot.r'].turn = turns[i % turns.length];
      }
      // ?shield=0..5: try the forearm mount turned each way.
      if (params.get('shield')) {
        const turns = [basis([0, 1, 0], [0, 0, 1]), basis([0, 1, 0], [0, 0, -1]), basis([0, 1, 0], [1, 0, 0]), basis([0, 1, 0], [-1, 0, 0]), basis([1, 0, 0], [0, 1, 0]), basis([-1, 0, 0], [0, 1, 0])];
        HUMAN_SOCKETS['forearm.l'].turn = turns[Number(params.get('shield')) % turns.length];
      }
      const [right, left] = kit[i % kit.length].split(/[+ ]/); // (a URL's + reads as a space)
      v.wield('handslot.r', right);
      if (left) v.wield(left.startsWith('shield') ? 'forearm.l' : 'handslot.l', left);
      r.scene.add(v.root);
      const act = params.get('act');
      if (act) v.loop(act, 0); else v.locomotion(Number(params.get('speed') || 0));
      v.update(0.3 + i * 0.37);
      views.push(v);
    });
  }
  const knight = Assets.character('knight');
  knight.scale.setScalar(0.8);
  knight.position.set(specs.length * 0.6 + 0.6, 0, 0);
  r.scene.add(knight);
  atmo.shadowExtent = 8; atmo.configureShadow(); atmo.follow(0, 0, 0);
  const cam = r.camera;
  const dist = Number(params.get('dist') || 7.5), pitch = THREE.MathUtils.degToRad(Number(params.get('pitch') || 12)), yaw = THREE.MathUtils.degToRad(Number(params.get('yaw') || 0));
  const ly = Number(params.get('ly') || 1.0), cx = Number(params.get('cx') || 0);
  cam.position.set(cx + Math.sin(yaw) * Math.cos(pitch) * dist, ly + Math.sin(pitch) * dist, Math.cos(yaw) * Math.cos(pitch) * dist);
  cam.lookAt(cx, ly, 0);
  // For tools: heights of everything in the row (skinned, as posed).
  (window as unknown as { __people: () => string }).__people = () => r.scene.children.filter((c) => c.type === 'Group' || c === knight).map((c) => {
    c.updateMatrixWorld(true);
    const b = new THREE.Box3().setFromObject(c, true);
    return `${c.name || c.type}@${c.position.x.toFixed(1)}: h=${(b.max.y - b.min.y).toFixed(2)} min=${b.min.y.toFixed(2)}`;
  }).join('\n');
  return (dt: number, t: number) => { for (const m of mixers) m.update(dt); for (const v of views) v.update(dt); atmo.update(t, cam.position); };
}
