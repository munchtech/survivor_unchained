import * as THREE from 'three';
import { CharacterView } from '@/render/characterView';
import type { CollisionWorld } from '@/sim/collision';
import type { BarkLayer } from '@/ui/hud/barks';
import type { LightSource, ZoneKit } from '@/world/zones/kit';
import { dampAngle } from '@/core/math';
import { FOLK_LOOKS, CHILD_LOOKS, WATCH_LOOK, type FolkLook, type FolkLine } from '@/content/folk';
import { SKINS, HAIRS, HAIR_STYLES, outfitFor } from '@/content/looks';
import type { PersonSpec } from '@/render/people';

/* A town's worth of people walking about.
 *
 * The zone gives a graph of places (doors, stalls, the well, the board, the
 * gates, and the lanes between) and says how many should be out at this
 * hour. Each walker picks somewhere to go, walks the lanes to it and does
 * the thing you do there: haggles at a stall, draws a bucket, reads the
 * board, goes indoors for a while. Some walk in twos and talk when they stop.
 * When the hour says fewer, the extra ones head for a door and go home; when
 * it says more, doors open and people come out. Children chase each other
 * round the square by day; after dark a watchman walks the rounds with a
 * torch. None of them blocks the survivor: they step aside. */

export type FolkKind = 'door' | 'stall' | 'well' | 'board' | 'gate' | 'path';
export interface FolkNode { id: string; x: number; z: number; kind: FolkKind; face?: { x: number; z: number }; square?: boolean; tavern?: boolean }
export interface FolkPlan { adults: number; children: number; watch: boolean }

type Role = 'adult' | 'child' | 'watch';

interface Walker {
  id: number;
  view: CharacterView;
  role: Role;
  x: number; z: number; vx: number; vz: number;
  path: FolkNode[];
  dest: FolkNode | null;
  at: FolkNode;
  state: 'walk' | 'busy' | 'inside';
  t: number;
  speed: number;
  leaving: boolean;
  lead: Walker | null;
  side: number;
  carry: string | null;
  barkT: number;
  torch: LightSource | null;
  torchObj: THREE.Object3D | null;
  gone: boolean;
  /** The round a watchman walks, and where on it he is. */
  round: number;
  /** Which way to go round something in the way (+1 left, -1 right), and for how long. */
  detour: number;
  detourT: number;
  /** Closest yet to the next waypoint, and how long since that improved. */
  best: number;
  stuckT: number;
}

const _v = new THREE.Vector3();
const rnd = (a: number, b: number) => a + Math.random() * (b - a);

/** Someone from the town, in the flesh: a man or a woman in the plain
 *  clothes of a look (its colours dye them), with skin, hair and a beard of
 *  their own. The watch wear leathers, a pauldron and a hood; children are
 *  small, with a child's larger head and no figure. */
function folkPerson(role: Role, l: FolkLook): PersonSpec {
  const child = role === 'child';
  const sex = Math.random() < (role === 'watch' ? 0.3 : 0.5) ? 'female' : 'male';
  const hood = role === 'watch' || (!child && l.model === 'rogue_hooded');
  const kind = role === 'watch' ? 'ranger' : l.model === 'rogue_hooded' || Math.random() < 0.2 ? 'ranger' : 'peasant';
  return {
    sex, outfit: outfitFor(sex, kind, { hood, pauldron: role === 'watch' }),
    hair: hood ? null : Math.random() < 0.08 ? null : pick(HAIR_STYLES[sex]),
    beard: sex === 'male' && !child && Math.random() < 0.6,
    hairColor: pick(HAIRS.filter((h) => h.color)).color, skin: pick(SKINS).color || undefined,
    figure: sex === 'female' ? (child ? 0 : rnd(0.6, 1.4)) : undefined,
    head: child ? 1.25 : undefined,
    dye: { cloth: l.tint, under: l.under },
  };
}
const pick = <T,>(a: readonly T[]) => a[Math.floor(Math.random() * a.length)];

export class Folk {
  private walkers: Walker[] = [];
  private adj = new Map<string, FolkNode[]>();
  private spawnT = 0;
  private barkT = 4;
  private said: string[] = [];
  private started = false;
  private nextId = 1;

  constructor(private opts: {
    parent: THREE.Object3D;
    nodes: FolkNode[];
    edges: Array<[string, string]>;
    col: CollisionWorld;
    kit: ZoneKit;
    barks: BarkLayer | null;
    heightAt: (x: number, z: number) => number;
    /** How many should be out, now. */
    plan: () => FolkPlan;
    /** Is it dark? (torches, and the tavern draws people). */
    dark: () => boolean;
    /** What the town is saying, now: lines whose conditions hold. */
    lines: (role: Role) => FolkLine[];
    /** The watch's round, as node ids. */
    round: string[];
  }) {
    const byId = new Map(opts.nodes.map((n) => [n.id, n]));
    for (const n of opts.nodes) this.adj.set(n.id, []);
    for (const [a, b] of opts.edges) {
      const na = byId.get(a), nb = byId.get(b);
      if (!na || !nb) continue;
      this.adj.get(a)!.push(nb);
      this.adj.get(b)!.push(na);
    }
  }

  get count() { return this.walkers.length; }

  /** For tools: lanes that run through something solid (sampled every 0.4 m). */
  validate() {
    const bad: string[] = [];
    const byId = new Map(this.opts.nodes.map((n) => [n.id, n]));
    for (const n of this.opts.nodes) if (this.opts.col.blocked(n.x, n.z, 0.3, true)) bad.push(`node ${n.id} (${n.x.toFixed(1)},${n.z.toFixed(1)})`);
    for (const [a, b] of this.opts.edges) {
      const na = byId.get(a), nb = byId.get(b);
      if (!na || !nb) { bad.push(`edge ${a}-${b}: missing node`); continue; }
      const len = Math.hypot(nb.x - na.x, nb.z - na.z), n = Math.ceil(len / 0.4);
      for (let i = 1; i < n; i++) {
        const x = na.x + ((nb.x - na.x) * i) / n, z = na.z + ((nb.z - na.z) * i) / n;
        if (this.opts.col.blocked(x, z, 0.3, true)) { bad.push(`edge ${a}-${b} at (${x.toFixed(1)},${z.toFixed(1)})`); break; }
      }
    }
    return bad;
  }

  /** For tools: where everyone is and what they are doing. */
  debugState() {
    return this.walkers.map((w) => ({ id: w.id, x: +w.x.toFixed(1), z: +w.z.toFixed(1), role: w.role, state: w.state, dest: w.dest?.id ?? null, at: w.at.id, lead: !!w.lead, leaving: w.leaving, v: +Math.hypot(w.vx, w.vz).toFixed(2), path: w.path.map((n) => n.id).join('>'), t: +w.t.toFixed(1) }));
  }

  /* ------------------------------------------------------------ people -- */

  private make(role: Role, at: FolkNode, look?: FolkLook): Walker {
    const l = look ?? (role === 'child' ? pick(CHILD_LOOKS) : role === 'watch' ? WATCH_LOOK : pick(FOLK_LOOKS));
    const view = new CharacterView(folkPerson(role, l), { scale: 0.8 * (l.scale ?? 1) });
    this.opts.parent.add(view.root);
    const w: Walker = {
      id: this.nextId++, view, role, x: at.x + rnd(-0.6, 0.6), z: at.z + rnd(-0.6, 0.6), vx: 0, vz: 0,
      path: [], dest: null, at, state: 'walk', t: 0,
      speed: role === 'child' ? rnd(3.3, 3.9) : role === 'watch' ? 1.25 : rnd(1.35, 1.8),
      leaving: false, lead: null, side: 1, carry: null, barkT: rnd(8, 30), torch: null, torchObj: null, gone: false, round: 0, detour: 1, detourT: 0, best: Infinity, stuckT: 0,
    };
    view.heading = Math.random() * Math.PI * 2;
    view.face(view.heading, true);
    if (role === 'watch') {
      w.torchObj = view.socket('handslot.l', 'dungeon', 'torch_lit', { scale: 0.9 });
      w.torch = this.opts.kit.source(w.x, 2.2, w.z, 0xffa050, 5.5, 10, 0.22);
    }
    this.walkers.push(w);
    return w;
  }

  private remove(w: Walker) {
    w.gone = true;
    w.view.dispose();
    w.view.root.removeFromParent();
    if (w.torch) this.opts.kit.setLit(w.torch, false);
    for (const f of this.walkers) if (f.lead === w) { f.lead = null; f.leaving = true; this.goHome(f); }
  }

  /* -------------------------------------------------------------- ways -- */

  private nearest(x: number, z: number, filter?: (n: FolkNode) => boolean) {
    let best: FolkNode | null = null, bd = Infinity;
    for (const n of this.opts.nodes) {
      if (filter && !filter(n)) continue;
      const d = Math.hypot(n.x - x, n.z - z);
      if (d < bd) { bd = d; best = n; }
    }
    return best!;
  }

  /** The lanes from one place to another (breadth first; the town is small). */
  private route(from: FolkNode, to: FolkNode): FolkNode[] {
    if (from === to) return [to];
    const prev = new Map<string, FolkNode | null>([[from.id, null]]);
    const q = [from];
    while (q.length) {
      const n = q.shift()!;
      if (n === to) break;
      for (const m of this.adj.get(n.id) ?? []) if (!prev.has(m.id)) { prev.set(m.id, n); q.push(m); }
    }
    if (!prev.has(to.id)) return [to];
    const out: FolkNode[] = [];
    for (let n: FolkNode | null = to; n && n !== from; n = prev.get(n.id) ?? null) out.unshift(n);
    return out;
  }

  private send(w: Walker, dest: FolkNode) {
    const from = this.nearest(w.x, w.z);
    w.path = this.route(from, dest);
    // Do not walk back to a node you are already past.
    if (w.path.length > 1 && Math.hypot(from.x - w.x, from.z - w.z) < 3) w.path = w.path[0] === from ? w.path.slice(1) : w.path;
    w.dest = dest;
    w.state = 'walk';
    w.best = Infinity; w.stuckT = 0;
  }

  private goHome(w: Walker) {
    const dark = this.opts.dark();
    // Home is the nearest door; strangers leave by a gate.
    const door = this.nearest(w.x, w.z, (n) => n.kind === 'door' || (!dark && n.kind === 'gate'));
    this.send(w, door);
  }

  /** Somewhere to go next, by what there is to do at this hour. */
  private errand(w: Walker) {
    const dark = this.opts.dark();
    if (w.role === 'child') {
      const sq = this.opts.nodes.filter((n) => n.square && n !== w.at);
      this.send(w, pick(sq));
      return;
    }
    if (w.role === 'watch') {
      const r = this.opts.round;
      w.round = (w.round + 1) % r.length;
      const n = this.opts.nodes.find((m) => m.id === r[w.round]);
      if (n) this.send(w, n);
      return;
    }
    const weight = (n: FolkNode) => {
      if (n === w.at) return 0;
      switch (n.kind) {
        case 'stall': return dark ? 0 : 3;
        case 'well': return dark ? 0.2 : 1.6;
        case 'board': return 1.2;
        case 'door': return n.tavern ? (dark ? 5 : 0.8) : dark ? 1.4 : 0.35;
        case 'gate': return dark ? 0 : 0.25;
        default: return 0;
      }
    };
    const pool = this.opts.nodes.map((n) => [n, weight(n)] as const).filter(([, v]) => v > 0);
    let r = Math.random() * pool.reduce((s, [, v]) => s + v, 0);
    for (const [n, v] of pool) { r -= v; if (r <= 0) { this.send(w, n); return; } }
    this.send(w, pool[0][0]);
  }

  /** What you do when you get there. */
  private arrive(w: Walker, n: FolkNode) {
    w.at = n;
    w.dest = null;
    if (w.lead) return; // a companion does what the other one does
    if (w.leaving && (n.kind === 'door' || n.kind === 'gate')) { this.hideGroup(w, true); return; }
    switch (n.kind) {
      case 'door':
        // In for a while; out again later, or not.
        w.state = 'inside'; w.t = rnd(8, 28);
        this.hideGroup(w, false);
        return;
      case 'gate':
        if (Math.random() < 0.6) { this.hideGroup(w, true); return; }
        break;
      case 'stall':
        w.state = 'busy'; w.t = rnd(6, 13);
        if (w.role === 'adult') w.view.act('Interact', { speed: 0.8 });
        return;
      case 'well':
        w.state = 'busy'; w.t = rnd(4.5, 7);
        w.view.act('PickUp', { speed: 0.7 });
        setTimeout(() => { if (!w.gone && !w.carry) { w.carry = 'bucket_water'; w.view.socket('handslot.r', 'hex_nature', 'bucket_water', { scale: 1.6, offset: [0, -0.18, 0] }); } }, 1400);
        return;
      case 'board':
        w.state = 'busy'; w.t = rnd(4, 9);
        return;
      default:
        if (w.role === 'child') {
          w.state = 'busy'; w.t = rnd(0.4, 2.2);
          if (Math.random() < 0.35) w.view.act('Cheer', { speed: 1.2 });
          return;
        }
        if (w.role === 'watch') { w.state = 'busy'; w.t = rnd(2, 5); return; }
    }
    this.errand(w);
  }

  /** In through a door (for a while, or for good), with whoever walks with you. */
  private hideGroup(w: Walker, forGood: boolean) {
    for (const f of [w, ...this.walkers.filter((m) => m.lead === w)]) {
      if (forGood) { f.gone = true; continue; }
      f.state = 'inside'; f.t = w.t;
      f.view.root.visible = false;
      if (f.carry) { f.carry = null; f.view.socket('handslot.r', null, null); }
    }
  }

  private spawn(role: Role, px: number, pz: number, scatter: boolean) {
    const dark = this.opts.dark();
    let at: FolkNode;
    if (scatter) {
      // Already out and about when you arrive: anywhere but under your feet.
      const pool = this.opts.nodes.filter((n) => (role === 'child' ? n.square : role === 'watch' ? this.opts.round.includes(n.id) : n.kind !== 'door') && Math.hypot(n.x - px, n.z - pz) > 7);
      at = pick(pool.length ? pool : this.opts.nodes);
    } else {
      // Out of a door (or in at a gate by day), preferably not in your face.
      const pool = this.opts.nodes.filter((n) => (n.kind === 'door' || (!dark && n.kind === 'gate')) && Math.hypot(n.x - px, n.z - pz) > 6);
      at = pick(pool.length ? pool : this.opts.nodes);
      if (role === 'child') at = pick(this.opts.nodes.filter((n) => n.square));
    }
    const w = this.make(role, at);
    if (role === 'watch') w.round = Math.max(0, this.opts.round.indexOf(at.id));
    if (role === 'child') {
      const friend = this.make('child', at);
      friend.lead = w; friend.side = 0;
      friend.x += 1.5;
    } else if (role === 'adult' && Math.random() < 0.3) {
      const friend = this.make('adult', at);
      friend.lead = w; friend.side = Math.random() < 0.5 ? -1 : 1;
      friend.speed = w.speed;
    }
    this.errand(w);
    if (scatter && w.path.length > 1) {
      // Somewhere along the way already.
      const k = Math.floor(Math.random() * (w.path.length - 1));
      const a = k === 0 ? at : w.path[k - 1], b = w.path[k], t = Math.random();
      w.x = a.x + (b.x - a.x) * t; w.z = a.z + (b.z - a.z) * t;
      w.path = w.path.slice(k);
      for (const f of this.walkers) if (f.lead === w) { f.x = w.x + 0.9; f.z = w.z; }
    }
  }

  /* ------------------------------------------------------------ update -- */

  update(dt: number, px: number, pz: number) {
    const plan = this.opts.plan();
    this.walkers = this.walkers.filter((w) => { if (w.gone) { if (w.view.root.parent) this.remove(w); return false; } return true; });
    // Keep the numbers to the hour.
    const leaders = (r: Role) => this.walkers.filter((w) => w.role === r && !w.lead && !w.leaving);
    const want: Record<Role, number> = { adult: plan.adults, child: plan.children > 0 ? 1 : 0, watch: plan.watch ? 1 : 0 };
    this.spawnT -= dt;
    for (const role of ['adult', 'child', 'watch'] as const) {
      const have = leaders(role);
      if (!this.started) { for (let i = have.length; i < want[role]; i++) this.spawn(role, px, pz, true); continue; }
      if (have.length < want[role] && this.spawnT <= 0) { this.spawn(role, px, pz, false); this.spawnT = rnd(3, 7); }
      if (have.length > want[role]) {
        // The one furthest from you goes home first.
        const w = have.sort((a, b) => Math.hypot(b.x - px, b.z - pz) - Math.hypot(a.x - px, a.z - pz))[0];
        w.leaving = true;
        if (w.state !== 'inside') this.goHome(w);
        else w.gone = true;
      }
    }
    this.started = true;
    this.barkT -= dt;
    for (const w of this.walkers) this.step(w, dt, px, pz);
  }

  private step(w: Walker, dt: number, px: number, pz: number) {
    const v = w.view;
    if (w.lead && w.lead.gone) { w.lead = null; w.leaving = true; this.goHome(w); }
    const lead = w.lead;
    if (w.state === 'inside' || (lead && lead.state === 'inside')) {
      v.root.visible = false;
      if (lead) { w.x = lead.x; w.z = lead.z; w.state = 'inside'; return; }
      w.t -= dt;
      if (w.t <= 0) {
        if (w.leaving) { w.gone = true; return; }
        v.root.visible = true;
        w.state = 'walk';
        for (const f of this.walkers) if (f.lead === w) { f.state = 'walk'; f.view.root.visible = true; f.x = w.x + 0.6; f.z = w.z; }
        this.errand(w);
      }
      return;
    }
    v.root.visible = true;
    // Where this one wants to be.
    let tx = w.x, tz = w.z, face: number | null = null, speed = w.speed;
    if (lead) {
      const lh = Math.hypot(lead.vx, lead.vz) > 0.2 ? Math.atan2(lead.vx, lead.vz) : lead.view.heading;
      if (w.side === 0) {
        // A child chasing: straight at the other one.
        tx = lead.x - Math.sin(lh) * 1.3; tz = lead.z - Math.cos(lh) * 1.3;
        speed = lead.speed * 1.05;
      } else {
        tx = lead.x + Math.cos(lh) * 0.95 * w.side; tz = lead.z - Math.sin(lh) * 0.95 * w.side;
        speed = lead.speed * 1.15;
      }
      if (lead.state === 'busy') face = Math.atan2(lead.x - w.x, lead.z - w.z);
    } else if (w.state === 'busy') {
      w.t -= dt;
      const f = w.at.face;
      if (f) face = Math.atan2(f.x - w.x, f.z - w.z);
      // Two walking together talk while they stop.
      const friend = this.walkers.find((m) => m.lead === w);
      if (friend && w.at.kind !== 'stall' && w.at.kind !== 'well') face = Math.atan2(friend.x - w.x, friend.z - w.z);
      if (w.t <= 0) {
        if (w.at.kind === 'stall' && Math.random() < 0.4 && w.role === 'adult') { w.t = rnd(3, 6); v.act('Interact', { speed: 0.8 }); }
        else if (w.leaving) this.goHome(w);
        else this.errand(w);
      }
    } else if (w.path.length) {
      const n = w.path[0];
      tx = n.x; tz = n.z;
      const d = Math.hypot(n.x - w.x, n.z - w.z);
      // Not getting any closer (someone in the way, a crate): give up on
      // this waypoint after a while and take the next.
      if (d < w.best - 0.2) { w.best = d; w.stuckT = 0; } else w.stuckT += dt;
      if (d < (w.path.length > 1 ? 1.2 : 0.45) || w.stuckT > 4) {
        w.path.shift();
        w.best = Infinity; w.stuckT = 0;
        if (!w.path.length) this.arrive(w, n);
      }
    } else if (w.state === 'walk') {
      this.arrive(w, w.dest ?? w.at);
    }
    // Steering: toward the target, around the survivor and each other.
    let dx = tx - w.x, dz = tz - w.z;
    const dist = Math.hypot(dx, dz);
    let want = w.state === 'busy' && !lead ? 0 : Math.min(speed, dist * (lead ? 1.8 : 3));
    if (lead && dist < 0.25) want = 0;
    let ax = dist > 1e-3 ? (dx / dist) * want : 0, az = dist > 1e-3 ? (dz / dist) * want : 0;
    if (want > 0.2) {
      // Something solid just ahead: turn along it, the same way each time
      // until clear, so nobody dithers against a crate.
      const col = this.opts.col, ux = ax / want, uz = az / want;
      w.detourT -= dt;
      // (A thinner probe than the body, so sliding along a wall reads as free.)
      if (col.blocked(w.x + ux * 0.75, w.z + uz * 0.75, 0.18, true)) {
        if (w.detourT <= 0) w.detour = Math.random() < 0.5 ? 1 : -1;
        w.detourT = 0.8;
        for (const a of [0.5, 0.9, 1.3, 1.7, 2.2]) {
          const ang = a * w.detour, c = Math.cos(ang), sn = Math.sin(ang);
          const rx = ux * c - uz * sn, rz = ux * sn + uz * c;
          if (!col.blocked(w.x + rx * 0.75, w.z + rz * 0.75, 0.18, true)) { ax = rx * want; az = rz * want; break; }
        }
      }
    }
    const pdx = w.x - px, pdz = w.z - pz, pd = Math.hypot(pdx, pdz);
    if (pd < 1.7 && pd > 1e-3) {
      // Step aside: away from you, and to the side if you are in the way.
      const push = (1.7 - pd) * 3.2;
      ax += (pdx / pd) * push; az += (pdz / pd) * push;
      if (want > 0.3 && (ax * -pdx + az * -pdz) > 0) { ax += (-pdz / pd) * 1.2; az += (pdx / pd) * 1.2; }
    }
    for (const o of this.walkers) {
      if (o === w || o.state === 'inside' || o === lead || o.lead === w) continue;
      const ox = w.x - o.x, oz = w.z - o.z, od = Math.hypot(ox, oz);
      if (od < 0.85 && od > 1e-3) { ax += (ox / od) * (0.85 - od) * 4; az += (oz / od) * (0.85 - od) * 4; }
    }
    const k = Math.min(1, dt * 6);
    w.vx += (ax - w.vx) * k; w.vz += (az - w.vz) * k;
    w.x += w.vx * dt; w.z += w.vz * dt;
    const p = { x: w.x, z: w.z };
    this.opts.col.resolve(p, 0.32);
    w.x = p.x; w.z = p.z;
    const sp = Math.hypot(w.vx, w.vz);
    v.locomotion(sp);
    const heading = sp > 0.3 ? Math.atan2(w.vx, w.vz) : face ?? (pd < 4 ? Math.atan2(px - w.x, pz - w.z) : v.heading);
    v.heading = dampAngle(v.heading, heading, 6, dt);
    v.face(v.heading);
    const y = this.opts.heightAt(w.x, w.z);
    v.root.position.set(w.x, y, w.z);
    v.update(dt);
    if (w.torch && w.torchObj) {
      // The light goes where the torch goes.
      w.torchObj.updateWorldMatrix(true, false);
      w.torchObj.getWorldPosition(_v);
      w.torch.x = _v.x; w.torch.y = _v.y + 0.5; w.torch.z = _v.z;
      this.opts.kit.setLit(w.torch, this.opts.dark());
      w.torchObj.visible = this.opts.dark();
    }
    this.bark(w, dt, pd, y);
  }

  /** Something said as you pass: the town's opinion, or the weather. */
  private bark(w: Walker, dt: number, pd: number, y: number) {
    w.barkT -= dt;
    if (!this.opts.barks || pd > 4.2 || pd < 1 || w.barkT > 0 || this.barkT > 0 || w.lead) return;
    const lines = this.opts.lines(w.role).filter((l) => !this.said.includes(l.text));
    if (!lines.length) return;
    // News first, while it is fresh.
    const news = lines.filter((l) => l.when || l.died);
    const pool = news.length && Math.random() < 0.7 ? news : lines;
    const line = pick(pool);
    this.said.push(line.text);
    if (this.said.length > 8) this.said.shift();
    w.barkT = rnd(40, 80);
    this.barkT = rnd(7, 13);
    this.opts.barks.speech(line.text, undefined, w.x, y + 0.2, w.z, () => (w.gone || w.state === 'inside' ? null : { x: w.x, y: this.opts.heightAt(w.x, w.z) + 0.2, z: w.z }));
  }

  dispose() {
    for (const w of this.walkers) if (!w.gone) this.remove(w);
    this.walkers = [];
  }
}
