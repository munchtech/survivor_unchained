import type { Game } from './game';
import { Input } from '@/core/input';
import { levelUp, overlay } from '@/ui/store';
import { ROAD, LOWFORD } from '@/world/zones/lowford';

/* A crude player, for testing: walks the prologue from the fire to the
 * gate, fights on the way, opens the chest, takes the first card of every
 * draft, and fights the Warden by staying near a lit lamp so its charges
 * run into it. It is not good at the game. It proves the game can be
 * finished, and gives screenshots something to look at. */

export class Autopilot {
  private wp = 1;
  private dashT = 0;
  private abilityT = 0;
  private log: string[] = [];
  private lastStage = '';
  private t = 0;
  private orbit = 0;
  private stuckT = 0;
  private lastX = 0;
  private lastZ = 0;
  private sideT = 0;
  private side = 1;

  constructor(private g: Game) {}

  get report() { return this.log; }

  drive(dt: number) {
    const g = this.g;
    this.t += dt;
    const lu = levelUp.value;
    if (lu) { lu.pick(0); return; }
    if (overlay.value && overlay.value !== 'levelup') { if (overlay.value !== 'chapter') g.closeOverlay(); return; }
    const b = g.scene.battle;
    const z = g.zone;
    if (!b || !z || !b.player.alive) return;
    const d = z.debug?.() ?? {};
    const stage = String(d.stage ?? '');
    if (stage !== this.lastStage) { this.log.push(`${this.t.toFixed(0)}s ${stage} lvl${b.ember.level} hp${Math.round(b.player.hp)} kills${b.killCount}`); this.lastStage = stage; }
    const p = b.player;
    let tx = p.x, tz = p.z;
    const L = LOWFORD;
    // Where to go.
    if (stage === 'wake' || stage === 'rising' || stage === 'ambush') {
      const cx = stage === 'ambush' ? L.cart.x - 4 : L.camp.x, cz = stage === 'ambush' ? L.cart.z + 6 : L.camp.z;
      this.orbit += dt * 0.35;
      tx = cx + Math.cos(this.orbit) * 7; tz = cz + Math.sin(this.orbit) * 6;
    } else if (stage === 'post' && d.knight) {
      const k = d.knight as { x: number; z: number };
      this.orbit += dt * 0.5;
      tx = k.x + Math.cos(this.orbit) * 5; tz = k.z + Math.sin(this.orbit) * 5;
    } else if (stage === 'post' && !d.chestOpened) {
      tx = L.chest.x - 1.4; tz = L.chest.z + 0.6;
      if (Math.hypot(p.x - tx, p.z - tz) < 1.6) Input.press('interact');
    } else if (stage === 'barrow' && d.caller) {
      const c = d.caller as { x: number; z: number };
      tx = c.x + 3; tz = c.z;
      if (Math.hypot(p.x - c.x, p.z - c.z) < 6 && this.abilityT <= 0) { Input.press('ability'); this.abilityT = 2; }
    } else if (stage === 'boss') {
      // Stand near a lit lamp, on the far side from the Warden.
      const pylons = (d.pylons as Array<{ x: number; z: number; lit: boolean }>).filter((q) => q.lit);
      const wx = d.wardenX as number, wz = d.wardenZ as number;
      if (pylons.length && wx !== null) {
        pylons.sort((a, c) => Math.hypot(a.x - p.x, a.z - p.z) - Math.hypot(c.x - p.x, c.z - p.z));
        const q = pylons[0];
        const ax = q.x - wx, az = q.z - wz, al = Math.hypot(ax, az) || 1;
        tx = q.x + (ax / al) * 2.2; tz = q.z + (az / al) * 2.2;
        if (d.wardenMode === 'charge' && Math.hypot(p.x - q.x, p.z - q.z) < 4) {
          // Step aside at the last moment.
          const sx = -az / al, sz = ax / al;
          tx = p.x + sx * 5; tz = p.z + sz * 5;
          if (this.dashT <= 0) { Input.moveX = sx; Input.moveZ = sz; Input.press('dash'); this.dashT = 1; }
        }
      } else if (wx !== null) {
        const ax = p.x - wx, az = p.z - wz, al = Math.hypot(ax, az) || 1;
        const a = Math.atan2(az, ax) + 0.6;
        tx = wx + Math.cos(a) * 8; tz = wz + Math.sin(a) * 8;
        void al;
      }
      if (d.wardenMode === 'channel' && this.abilityT <= 0 && wx !== null && Math.hypot(p.x - wx, p.z - wz) < 6) { Input.press('ability'); this.abilityT = 3; }
      if (d.wardenMode === 'channel' && wx !== null) { tx = wx + 2.5; tz = wz + 2.5; }
    } else if (stage === 'intro' || stage === 'victory') {
      tx = p.x; tz = p.z;
    } else {
      // Follow the road north.
      while (this.wp < ROAD.length - 1 && ROAD[this.wp][1] > p.z - 3) this.wp++;
      tx = ROAD[this.wp][0]; tz = ROAD[this.wp][1];
    }
    // Keep off the crowd.
    let rx = 0, rz = 0, near = 0;
    b.enemies.forEach((e) => {
      if (!e.alive || e.state === 'dying' || e.disposition !== 'hostile') return;
      const dx = p.x - e.x, dz = p.z - e.z, dd = Math.hypot(dx, dz);
      if (dd < 4.5 && dd > 0.01) { rx += (dx / dd) * (4.5 - dd); rz += (dz / dd) * (4.5 - dd); }
      if (dd < 2.2) near++;
    });
    let mx = tx - p.x + rx * 1.4, mz = tz - p.z + rz * 1.4;
    // Wedged on something: sidestep for a moment.
    this.stuckT += dt;
    if (this.stuckT > 3) {
      if (Math.hypot(p.x - this.lastX, p.z - this.lastZ) < 1 && Math.hypot(tx - p.x, tz - p.z) > 2) { this.sideT = 1.5; this.side = -this.side; }
      this.stuckT = 0; this.lastX = p.x; this.lastZ = p.z;
    }
    if (this.sideT > 0) {
      this.sideT -= dt;
      const l = Math.hypot(mx, mz) || 1;
      mx = mx / l - (mz / l) * 1.5 * this.side; mz = mz / l + (mx / l) * 1.5 * this.side;
    }
    const m = Math.hypot(mx, mz);
    if (m > 0.3) { mx /= m; mz /= m; } else { mx = mz = 0; }
    Input.moveX = mx; Input.moveZ = mz;
    this.dashT -= dt; this.abilityT -= dt;
    if (near >= 5 && this.dashT <= 0) { Input.press('dash'); this.dashT = 1.2; }
    if (p.hp < b.maxHp * 0.35) Input.press('ultimate');
  }
}
