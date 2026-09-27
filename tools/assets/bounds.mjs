/* Measure every prop and character: axis-aligned bounds at rest, written to
 * src/content/generated/bounds.json. World layout and collision footprints
 * are sized from these rather than guessed. */
import { NodeIO, getBounds } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import fs from 'node:fs';

await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const out = {};
const r3 = (v) => v.map((n) => Math.round(n * 1000) / 1000);
for (const pack of fs.readdirSync('public/assets/props')) {
  const doc = await io.read(`public/assets/props/${pack}`);
  const name = pack.replace('.glb', '');
  out[name] = {};
  for (const node of doc.getRoot().getDefaultScene().listChildren()) {
    const b = getBounds(node);
    out[name][node.getName()] = { min: r3(b.min), max: r3(b.max) };
  }
}
out.characters = {};
for (const f of fs.readdirSync('public/assets/characters')) {
  const doc = await io.read(`public/assets/characters/${f}`);
  const b = getBounds(doc.getRoot().getDefaultScene());
  out.characters[f.replace('.glb', '')] = { min: r3(b.min), max: r3(b.max) };
}
fs.writeFileSync('src/content/generated/bounds.json', JSON.stringify(out, null, 1));
console.log(JSON.stringify(out.characters));
for (const k of ['building_tavern_blue', 'building_home_A_blue', 'building_blacksmith_blue', 'building_church_blue', 'building_market_blue', 'building_well_blue', 'wall_straight', 'wall_straight_gate']) console.log(k, JSON.stringify(out.hex_buildings[k]));
for (const k of ['trees_A_large', 'tree_single_A', 'rock_single_A', 'mountain_A', 'barrel', 'tent', 'crate_A_big']) console.log(k, JSON.stringify(out.hex_nature[k]));
for (const k of ['barrel_large', 'wall', 'table_long', 'torch_lit', 'chest']) console.log(k, JSON.stringify(out.dungeon[k]));
for (const k of ['tree_dead_large', 'tree_pine_orange_large', 'shrine', 'crypt', 'gravestone', 'lantern_standing', 'fence', 'coffin']) console.log(k, JSON.stringify(out.halloween[k]));
