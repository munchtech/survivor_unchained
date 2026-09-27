import type { Renderer } from '@/render/renderer';
import { PRESETS, type PresetName } from '@/render/atmosphere';
import { WorldScene } from '@/game/scene';
import { buildLowFord } from '@/world/zones/lowford';
import { LOADOUTS } from '@/render/playerView';
import { StatBlock } from '@/sim/stats';
import { Input } from '@/core/input';

/* Walk a zone with nothing in it, for building and screenshots:
 *   ?dev=zone&zone=lowford&x=0&z=80&time=night&camdist=23&pitch=56&yaw=0 */

export function zoneDev(r: Renderer, params: URLSearchParams) {
  const scene = new WorldScene(r);
  const id = params.get('zone') || 'lowford';
  const built = buildLowFord(r.spec.grassDensity);
  void id;
  const zone = built.zone;
  if (params.get('time')) zone.atmosphere = PRESETS[params.get('time') as PresetName];
  scene.setZone(zone);
  const stats = new StatBlock();
  stats.setBase({ maxHealth: 100, moveSpeed: 9, pickupRadius: 2 });
  const x = Number(params.get('x') ?? zone.start.x), z = Number(params.get('z') ?? zone.start.z);
  scene.startBattle({ seed: 1, combat: false, stats, start: { x, z }, weapons: [], ability: null }, LOADOUTS[params.get('class') || 'warden']);
  if (params.get('camdist')) { scene.cam.targetDistance = Number(params.get('camdist')); scene.cam.distance = scene.cam.targetDistance; }
  if (params.get('pitch')) scene.cam.pitch = Number(params.get('pitch')) * Math.PI / 180;
  if (params.get('yaw')) scene.cam.yaw = Number(params.get('yaw')) * Math.PI / 180;
  (window as unknown as { __scene: WorldScene }).__scene = scene;
  return (dt: number) => {
    Input.poll();
    scene.update(dt);
  };
}
