import type { EnvKit } from '@/render/env';
import { floraPieces } from '@/render/scatter';
import { housePieces, WALL_PIECES } from './houses';

/* Every piece of the world's kits a zone builds with, loaded at boot (the
 * zones are built at once, and each texture decoded is memory: the kits'
 * other pieces stay on disk). Add a name here before a zone uses it. */

const PROPS = [
  'Anvil', 'Anvil_Log', 'Bag', 'Banner_1', 'Banner_2', 'Barrel', 'Barrel_Apples', 'Barrel_Holder', 'Bench', 'Bucket_Wooden_1', 'Bucket_Metal', 'Chair_1',
  'Candle_1', 'Candle_2', 'CandleStick_Stand', 'Chest_Wood', 'Crate_Wooden', 'Crate_Metal', 'Dummy', 'FarmCrate_Apple', 'FarmCrate_Carrot', 'FarmCrate_Empty',
  'Lantern_Wall', 'Pot_1', 'Rope_1', 'Stall_Empty', 'Stall_Cart_Empty', 'Stool', 'Table_Large', 'Torch_Metal', 'Vase_2', 'Vase_4', 'Vase_Rubble_Medium',
  'WeaponStand', 'Workbench', 'Pickaxe_Bronze', 'Axe_Bronze', 'Shield_Wooden', 'Sword_Bronze', 'Chain_Coil', 'Cauldron',
];

const VILLAGE = ['Prop_WoodenFence_Single', 'Prop_WoodenFence_Extension1', 'Prop_WoodenFence_Extension2', 'Prop_Wagon', 'Prop_Crate', 'Prop_Brick1', 'Prop_Brick2', 'Prop_Brick3', 'Prop_Support'];

export function envUsed(): Array<[EnvKit, string]> {
  return [
    ...housePieces(), ...WALL_PIECES,
    ...PROPS.map((n) => ['props', n] as [EnvKit, string]),
    ...VILLAGE.map((n) => ['village', n] as [EnvKit, string]),
    ...floraPieces().map((n) => ['nature', n] as [EnvKit, string]),
  ];
}
