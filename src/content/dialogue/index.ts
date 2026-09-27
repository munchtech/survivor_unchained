import type { Conversation } from '@/world/dialogue';
import { TOWN_CONVOS } from './town';

/* Every conversation in the game, by the id of whoever holds it. */
export const CONVOS: Record<string, Conversation> = { ...TOWN_CONVOS };
