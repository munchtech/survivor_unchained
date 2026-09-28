import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS, type PresetName } from '@/render/atmosphere';
import { Assets } from '@/render/assets';
import { assemble, peopleClips, PARTS, type PersonSpec } from '@/render/people';

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
  return (dt: number, t: number) => { for (const m of mixers) m.update(dt); atmo.update(t, cam.position); };
}
