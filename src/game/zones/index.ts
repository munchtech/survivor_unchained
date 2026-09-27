import type { Game } from '../game';
import type { ZoneRuntime } from '../zone';
import { prologue } from './prologue';

/* Every place the survivor can be, by id. */
export const ZONES: Record<string, (g: Game) => ZoneRuntime> = {
  lowford: prologue,
};
