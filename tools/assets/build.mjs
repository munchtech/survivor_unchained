/* Asset pipeline.
 *
 * Source packs are KayKit (CC0, Kay Lousberg - kaylousberg.com). They are not
 * vendored in raw form: clone them next to each other and point ASSET_SRC at
 * the folder (default /tmp/assets):
 *
 *   git clone --depth 1 https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0
 *   git clone --depth 1 https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0
 *   git clone --depth 1 https://github.com/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0
 *   git clone --depth 1 https://github.com/KayKit-Game-Assets/KayKit-Medieval-Hexagon-Pack-1.0
 *   git clone --depth 1 https://github.com/KayKit-Game-Assets/KayKit-Halloween-Bits-1.0
 *
 * What comes out (public/assets):
 *   characters/<id>.glb   skinned meshes only, no clips
 *   anim/humanoid.glb     every clip the game uses, on the shared 41-bone rig
 *   props/<pack>.glb      one file per pack, each prop a named root node, so
 *                         the pack's texture atlas is stored once
 *
 * Everything is meshopt-compressed; the game loads it with MeshoptDecoder. */
import { NodeIO, Document } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { dedup, prune, resample, weld, quantize, meshopt, mergeDocuments, unpartition, reorder } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import fs from 'node:fs';
import path from 'node:path';

const SRC = process.env.ASSET_SRC || '/tmp/assets';
const OUT = path.resolve('public/assets');
const ADV = `${SRC}/KayKit-Character-Pack-Adventures-1.0/addons/kaykit_character_pack_adventures`;
const SKL = `${SRC}/KayKit-Character-Pack-Skeletons-1.0/addons/kaykit_character_pack_skeletons`;
const DUN = `${SRC}/KayKit-Dungeon-Remastered-1.0/addons/kaykit_dungeon_remastered/Assets/gltf`;
const HEX = `${SRC}/KayKit-Medieval-Hexagon-Pack-1.0/addons/kaykit_medieval_hexagon_pack/Assets/gltf`;
const HAL = `${SRC}/KayKit-Halloween-Bits-1.0/addons/kaykit_halloween_bits/Assets/gltf`;

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });

/** The clips the game actually plays. Everything else is dropped. */
const CLIPS = [
  'Idle', 'Unarmed_Idle', '2H_Melee_Idle', 'Idle_B', 'Idle_Combat',
  'Walking_A', 'Walking_B', 'Walking_C', 'Walking_Backwards', 'Walking_D_Skeletons',
  'Running_A', 'Running_B', 'Running_C', 'Running_Strafe_Left', 'Running_Strafe_Right',
  'Dodge_Forward', 'Dodge_Backward', 'Dodge_Left', 'Dodge_Right',
  'Hit_A', 'Hit_B', 'Death_A', 'Death_A_Pose', 'Death_B', 'Death_B_Pose',
  'Death_C_Skeletons', 'Death_C_Pose',
  '1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal',
  '1H_Melee_Attack_Stab', '1H_Melee_Attack_Jump_Chop',
  '2H_Melee_Attack_Chop', '2H_Melee_Attack_Slice', '2H_Melee_Attack_Spin', '2H_Melee_Attack_Spinning',
  'Dualwield_Melee_Attack_Chop', 'Dualwield_Melee_Attack_Slice',
  '1H_Ranged_Shoot', '1H_Ranged_Aiming', '2H_Ranged_Shoot', '2H_Ranged_Aiming',
  'Spellcast_Shoot', 'Spellcast_Raise', 'Spellcasting', 'Spellcast_Long', 'Spellcast_Summon',
  'Throw', 'Block', 'Blocking', 'Block_Hit', 'Cheer', 'Interact', 'PickUp', 'Use_Item',
  'Sit_Chair_Idle', 'Sit_Chair_Down', 'Sit_Chair_StandUp', 'Sit_Floor_Idle', 'Sit_Floor_Down',
  'Lie_Idle', 'Lie_Pose', 'Lie_StandUp',
  'Skeletons_Awaken_Floor', 'Skeletons_Awaken_Floor_Long', 'Skeletons_Inactive_Floor_Pose',
  'Skeletons_Awaken_Standing', 'Spawn_Ground_Skeletons', 'Spawn_Ground', 'Taunt', 'Taunt_Longer',
  'Jump_Full_Short', 'Unarmed_Melee_Attack_Punch_A', 'Unarmed_Melee_Attack_Kick',
];

async function finish(doc, file, { keepAnim = false } = {}) {
  await doc.transform(
    dedup(),
    prune({ keepLeaves: true, keepAttributes: false }),
    ...(keepAnim ? [resample({ tolerance: 1e-4 })] : []),
    unpartition(),
    reorder({ encoder: MeshoptEncoder }),
    quantize({ quantizePosition: 14, quantizeNormal: 10, quantizeTexcoord: 12 }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  fs.mkdirSync(path.dirname(file), { recursive: true });
  await io.write(file, doc);
  const kb = (fs.statSync(file).size / 1024).toFixed(0);
  console.log(`  ${path.relative(process.cwd(), file)}  ${kb} KB`);
}

/** Samplers keep their accessors alive after the animation that owned them
 *  is gone, so they have to be disposed explicitly or prune() keeps every
 *  keyframe in the file. */
function disposeAnimation(a) {
  for (const s of a.listSamplers()) s.dispose();
  for (const c of a.listChannels()) c.dispose();
  a.dispose();
}
function stripAnimations(doc) {
  for (const a of doc.getRoot().listAnimations()) disposeAnimation(a);
}

/* ---------------------------------------------------------- characters -- */
console.log('characters');
const CHARS = {
  knight: `${ADV}/Characters/gltf/Knight.glb`,
  barbarian: `${ADV}/Characters/gltf/Barbarian.glb`,
  mage: `${ADV}/Characters/gltf/Mage.glb`,
  rogue: `${ADV}/Characters/gltf/Rogue.glb`,
  rogue_hooded: `${ADV}/Characters/gltf/Rogue_Hooded.glb`,
  skeleton_minion: `${SKL}/Characters/gltf/Skeleton_Minion.glb`,
  skeleton_warrior: `${SKL}/Characters/gltf/Skeleton_Warrior.glb`,
  skeleton_mage: `${SKL}/Characters/gltf/Skeleton_Mage.glb`,
  skeleton_rogue: `${SKL}/Characters/gltf/Skeleton_Rogue.glb`,
};
for (const [id, file] of Object.entries(CHARS)) {
  const doc = await io.read(file);
  stripAnimations(doc);
  await finish(doc, `${OUT}/characters/${id}.glb`);
}

/* ---------------------------------------------------------- animations -- */
console.log('animations');
{
  // The skeleton pack carries every adventurer clip plus its own (rising,
  // spawning, taunting), all on the same rig.
  const doc = await io.read(CHARS.skeleton_minion);
  const adv = await io.read(CHARS.knight);
  const have = new Set(doc.getRoot().listAnimations().map((a) => a.getName()));
  const missing = adv.getRoot().listAnimations().map((a) => a.getName()).filter((n) => CLIPS.includes(n) && !have.has(n));
  if (missing.length) console.log('  (clips only on adventurers, not merged):', missing.join(', '));
  for (const a of doc.getRoot().listAnimations()) if (!CLIPS.includes(a.getName())) disposeAnimation(a);
  for (const m of doc.getRoot().listMeshes()) m.dispose();
  for (const s of doc.getRoot().listSkins()) s.dispose();
  for (const t of doc.getRoot().listTextures()) t.dispose();
  for (const m of doc.getRoot().listMaterials()) m.dispose();
  const kept = doc.getRoot().listAnimations().map((a) => a.getName());
  const absent = CLIPS.filter((c) => !kept.includes(c));
  if (absent.length) console.log('  requested but absent:', absent.join(', '));
  await finish(doc, `${OUT}/anim/humanoid.glb`, { keepAnim: true });
}

/* --------------------------------------------------------------- props -- */
/** Merge many single-prop .gltf files into one document, one root node per
 *  prop, named after its file. */
async function pack(name, files) {
  const out = new Document();
  out.createBuffer();
  const scene = out.createScene(name);
  for (const [propName, file] of files) {
    const doc = await io.read(file);
    stripAnimations(doc);
    const root = doc.getRoot();
    // Wrap the prop's scene in one named node before merging.
    const s = root.listScenes()[0];
    const wrap = doc.createNode(propName);
    for (const child of s.listChildren()) { s.removeChild(child); wrap.addChild(child); }
    s.addChild(wrap);
    const map = mergeDocuments(out, doc);
    const mergedScene = map.get(s);
    for (const child of mergedScene.listChildren()) { mergedScene.removeChild(child); scene.addChild(child); }
    mergedScene.dispose();
  }
  out.getRoot().setDefaultScene(scene);
  // One buffer is enough.
  const buffers = out.getRoot().listBuffers();
  for (const b of buffers.slice(1)) {
    for (const acc of out.getRoot().listAccessors()) if (acc.getBuffer() === b) acc.setBuffer(buffers[0]);
    b.dispose();
  }
  await finish(out, `${OUT}/props/${name}.glb`);
}

function listDir(dir, filter = () => true) {
  // The dungeon pack ships '.gltf.glb'; the others ship '.gltf' + '.bin'.
  return fs.readdirSync(dir).filter((f) => /\.gltf(\.glb)?$/.test(f) && filter(f))
    .map((f) => [f.replace(/\.gltf(\.glb)?$/, ''), path.join(dir, f)]);
}

console.log('props');
await pack('hex_buildings', [
  ...listDir(`${HEX}/buildings/neutral`),
  ...listDir(`${HEX}/buildings/blue`),
  ...listDir(`${HEX}/buildings/red`, (f) => /home|tower|barracks|watchtower|tavern/.test(f)),
]);
await pack('hex_nature', [
  ...listDir(`${HEX}/decoration/nature`),
  ...listDir(`${HEX}/decoration/props`),
]);
await pack('dungeon', listDir(DUN));
await pack('halloween', listDir(HAL));
await pack('adventure_items', [
  ...listDir(`${ADV}/Assets/gltf`),
  ...listDir(`${SKL}/Assets/gltf`),
]);

/* ------------------------------------------------------------- licence -- */
fs.writeFileSync(`${OUT}/LICENSE-KayKit.txt`, fs.readFileSync(`${SRC}/KayKit-Character-Pack-Adventures-1.0/LICENSE.txt`));
console.log('done');
