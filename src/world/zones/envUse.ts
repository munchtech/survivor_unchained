import type { EnvKit } from '@/render/env';
import { floraPieces } from '@/render/scatter';
import { housePieces, WALL_PIECES } from './houses';

/* Every piece of the world's kits a zone builds with, loaded at boot (the
 * zones are built at once, and each texture decoded is memory: the kits'
 * other pieces stay on disk). Add a name here before a zone uses it. */

const PROPS = [
  'Anvil_Log', 'Bag', 'Barrel', 'Barrel_Apples', 'Barrel_Holder', 'Bench', 'Bucket_Wooden_1', 'Bucket_Metal', 'Chair_1',
  'Candle_1', 'Candle_2', 'Chest_Wood', 'Crate_Wooden', 'Dummy', 'FarmCrate_Apple', 'FarmCrate_Carrot', 'FarmCrate_Empty',
  'Lantern_Wall', 'Pot_1', 'Rope_1', 'Stool', 'Table_Large', 'Torch_Metal', 'Vase_2', 'Vase_4', 'Vase_Rubble_Medium',
  'WeaponStand', 'Workbench', 'Chain_Coil',
];

const VILLAGE = ['Prop_WoodenFence_Single', 'Prop_WoodenFence_Extension1', 'Prop_Wagon', 'Prop_Brick2', 'Prop_Brick3'];

export function envUsed(): Array<[EnvKit, string]> {
  return [
    ...housePieces(), ...WALL_PIECES,
    ...PROPS.map((n) => ['props', n] as [EnvKit, string]),
    ...VILLAGE.map((n) => ['village', n] as [EnvKit, string]),
    ...floraPieces().map((n) => ['nature', n] as [EnvKit, string]),
  ];
}
