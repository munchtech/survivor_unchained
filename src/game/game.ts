import * as THREE from 'three';
import { effect } from '@preact/signals';
import type { Renderer, Quality } from '@/render/renderer';
import { CharacterView } from '@/render/characterView';
import { CLOTH } from '@/render/playerView';
import type { CharacterModel } from '@/render/assets';
import { WorldScene } from './scene';
import { HudBridge } from './hudBridge';
import { loadoutFor } from './loadout';
import { actions } from './actions';
import type { ZoneRuntime, Interactable } from './zone';
import { ZONES } from './zones';
import { BarkLayer } from '@/ui/hud/barks';
import {
  screen, overlay, prompt, toast, zoneInfo, slots, creation, fade, hud, levelUp, boss, objectives, announce,
  type CreationDraft, type NoticeKind,
} from '@/ui/store';
import { Input } from '@/core/input';
import { damp } from '@/core/math';
import {
  createCharacter, deriveKit, addToPack, makeItem, type CharacterData, type CreationChoice,
} from '@/rpg/character';
import { ARCHETYPES, BACKGROUNDS } from '@/content/archetypes';
import { ITEMS } from '@/content/items';
import { freshWorld, type WorldState } from '@/world/state';
import { apply, npc, type Ctx, type Notice } from '@/world/logic';
import { Saves } from '@/world/save';
import type { Battle } from '@/sim/battle';
import type { Pickup } from '@/sim/entities';

/* The game: the one object that knows about everything else.
 *
 * It owns the character and the world, decides which zone is loaded and
 * builds each Battle from the character's gear, routes the simulation's
 * events to the interface and the world's memory, runs the interaction
 * prompt, and saves. Modes:
 *
 *   title    the campfire on the Low Ford road, a stranger by the fire
 *   create   the same fire; the survivor you are making stands up beside it
 *   play     a zone, a Battle, the HUD
 *
 * Getting from create to play is one continuous shot: the camera leaves the
 * portrait framing and settles into the game view over the same fire. */

export interface Expedition {
  level: number;
  xp: number;
  weapons: Array<{ id: string; rank: number; evolution: string | null }>;
  boons: Record<string, number>;
  rerolls: number;
  banishes: number;
  hp: number;
}

const TOAST_KIND: Record<Notice['tone'], NoticeKind> = {
  item: 'loot', gold: 'gold', rel: 'relation', journal: 'quest', history: 'world', learn: 'lore',
  faction: 'world', trait: 'level', warn: 'warning', info: 'world',
};

export class Game {
  readonly scene: WorldScene;
  readonly bridge: HudBridge;
  readonly barks: BarkLayer;
  mode: 'title' | 'create' | 'play' = 'title';
  ch: CharacterData | null = null;
  world: WorldState | null = null;
  ctx: Ctx | null = null;
  slot = 0;
  playtime = 0;
  zone: ZoneRuntime | null = null;
  expedition: Expedition | null = null;
  /** The figure by the fire in the title and creation screens. */
  private figure: CharacterView | null = null;
  private figureKey = '';
  private camPos = new THREE.Vector3();
  private camLook = new THREE.Vector3();
  private camPosT = new THREE.Vector3();
  private camLookT = new THREE.Vector3();
  private blend: { pos: THREE.Vector3; quat: THREE.Quaternion; t: number; dur: number } | null = null;
  private near: Interactable | null = null;
  private time = 0;
  private autosaveT = 0;
  /** Dev: a crude player that drives the game (?auto). */
  autopilot: { drive(dt: number): void } | null = null;

  constructor(readonly r: Renderer) {
    this.scene = new WorldScene(r);
    this.barks = new BarkLayer(document.getElementById('stage')!);
    this.bridge = new HudBridge(this.scene, this.barks);
    this.scene.onEvents = (evs) => {
      this.bridge.events(evs);
      this.zone?.events?.(evs);
    };
    this.scene.onStep = (dt) => this.zone?.step?.(dt);
    this.bindActions();
    Input.on((a) => this.onAction(a));
    // The creation screen edits a draft; the figure by the fire follows it.
    effect(() => {
      const d = creation.value;
      if (d && this.mode === 'create') this.dressFigure(d);
    });
  }

  /* ============================================================= title == */

  showTitle() {
    this.mode = 'title';
    this.leaveZone();
    this.ch = null;
    this.world = null;
    this.expedition = null;
    const z = ZONES.lowford(this);
    this.zone = z;
    this.scene.setZone(z.build);
    this.scene.atmo.set(z.build.atmosphere);
    this.placeFigure('rogue_hooded', { sit: true });
    this.poseCamera('title', true);
    screen.value = 'title';
    overlay.value = null;
    hud.value = null;
    zoneInfo.value = null;
    objectives.value = [];
    slots.value = Saves.slots();
    fade.value = { to: 0, seconds: 1.6 };
  }

  newJourney() {
    this.mode = 'create';
    const draft: CreationDraft = {
      step: 0, name: '', archetype: 'warden', weaponItem: 'worn_oathblade', ability: 'shield_bash', startBoon: 'might',
      background: 'hunter', palette: 'steel', model: 'knight', headgear: true,
    };
    creation.value = draft;
    screen.value = 'create';
    this.poseCamera('create');
  }

  cancelCreation() {
    this.mode = 'title';
    creation.value = null;
    screen.value = 'title';
    this.placeFigure('rogue_hooded', { sit: true });
    this.poseCamera('title');
  }

  /** Put someone by the fire. */
  private placeFigure(model: CharacterModel, o: { sit?: boolean; show?: string[]; tint?: string } = {}) {
    this.figure?.dispose();
    const f = new CharacterView(model);
    const fire = this.fireSpot();
    const y = this.scene.heightAt(fire.x + 1.4, fire.z + 1.0);
    f.root.position.set(fire.x + 1.4, y, fire.z + 1.0);
    f.showOnly(o.show ?? ['Rogue_Cape']);
    if (o.tint) f.tintParts(o.tint, CLOTH);
    if (o.sit) {
      // On the log beside the fire, facing into it.
      const sx = fire.x + 2.05, sz = fire.z - 0.1;
      f.root.position.set(sx + 0.12, this.scene.heightAt(sx, sz) + 0.08, sz);
      f.face(-Math.PI / 2 - 0.12, true);
      f.loop('Sit_Chair_Idle', 0);
    } else {
      f.face(Math.PI * 0.08, true);
      f.loop('Idle', 0);
    }
    this.r.scene.add(f.root);
    this.figure = f;
  }

  private dressFigure(d: CreationDraft) {
    const key = `${d.archetype}|${d.model}|${d.weaponItem}|${d.palette}|${d.headgear}`;
    if (key === this.figureKey && this.figure) return;
    const changedBody = !this.figureKey.startsWith(`${d.archetype}|${d.model}|`);
    this.figureKey = key;
    const lo = loadoutFor({ archetype: d.archetype, weaponItem: d.weaponItem, model: d.model as CharacterModel, palette: d.palette, headgear: d.headgear });
    this.placeFigure(lo.model, { show: lo.show, tint: lo.tint });
    if (changedBody && this.figure) this.figure.act(d.archetype === 'arcanist' ? 'Spellcast_Raise' : d.archetype === 'reaver' ? 'Taunt' : 'Cheer', { speed: 1 });
  }

  private fireSpot() {
    const f = (this.zone as unknown as { fire?: { x: number; z: number } })?.fire;
    return f ?? { x: -10.5, z: 90.5 };
  }

  /** Framings for the title and creation screens, over the fire. */
  private poseCamera(which: 'title' | 'create', snap = false) {
    const f = this.fireSpot();
    const y = this.scene.heightAt(f.x, f.z);
    if (which === 'title') {
      this.camPosT.set(f.x + 7.5, y + 3.2, f.z + 7.8);
      this.camLookT.set(f.x + 0.4, y + 0.9, f.z - 0.4);
    } else {
      // The figure stands to the right of the fire; frame them on the right
      // third, with the fire glowing at the left edge of the portrait.
      this.camPosT.set(f.x + 1.05, y + 1.75, f.z + 7.0);
      this.camLookT.set(f.x + 0.95, y + 1.0, f.z + 0.9);
    }
    if (snap) { this.camPos.copy(this.camPosT); this.camLook.copy(this.camLookT); }
    this.scene.showcase = { pos: this.camPos, look: this.camLook };
  }

  /* ========================================================= new game == */

  beginJourney(c: CreationChoice) {
    const seed = Math.floor(Math.random() * 1e9);
    const world = freshWorld(seed);
    const ch = createCharacter(c, world.day, seed);
    // Where you came from decides how the world first reads you.
    const bg = BACKGROUNDS[c.background];
    for (const [f, v] of Object.entries(bg.standing)) world.factions[f] = { id: f, standing: v, strength: 50, flags: {} };
    for (const [id, rel] of Object.entries(bg.npc)) Object.assign(npc(world, id), rel);
    const starter = makeItem(ch, 'health_draught', { qty: 1 });
    addToPack(ch, starter);
    this.ch = ch;
    this.world = world;
    this.ctx = this.makeCtx();
    this.slot = this.freeSlot();
    this.playtime = 0;
    this.expedition = null;
    creation.value = null;
    this.figure?.dispose();
    this.figure = null;
    this.figureKey = '';
    // One shot from the portrait into the game.
    this.startBlend(2.2);
    this.scene.showcase = null;
    this.enterPlay(this.zone!, null, { x: this.fireSpot().x + 1.4, z: this.fireSpot().z + 1.0, facing: Math.PI * 0.08 });
    this.save('new');
  }

  private freeSlot() {
    const used = new Set(Saves.slots().map((s) => s.slot));
    for (let i = 0; i < 3; i++) if (!used.has(i)) return i;
    // All full: the oldest is replaced.
    const list = Saves.slots().sort((a, b) => a.savedAt - b.savedAt);
    return list[0]?.slot ?? 0;
  }

  continueJourney(slot: number) {
    const d = Saves.read(slot);
    if (!d) { toast('warning', 'That journey could not be read.'); return; }
    this.slot = slot;
    this.ch = d.character;
    this.world = d.world;
    this.ctx = this.makeCtx();
    this.playtime = d.playtime;
    this.expedition = (d.ember as Expedition | null | undefined) ?? null;
    fade.value = { to: 1, seconds: 0.5, caption: this.ch.name, sub: `Day ${this.world.day}` };
    setTimeout(() => {
      this.figure?.dispose();
      this.figure = null;
      this.enterZone(d.location.zone, null, { x: d.location.x, z: d.location.z, facing: d.location.facing });
      fade.value = { to: 0, seconds: 1.2 };
    }, 550);
  }

  /* ============================================================ zones == */

  private leaveZone() {
    if (this.zone) this.zone.dispose?.();
    this.zone = null;
    this.scene.clearZone();
    this.barks.clear();
    prompt.value = null;
    boss.value = null;
  }

  /** Travel: fade, build the next zone, arrive. */
  travel(to: string, caption?: string, sub?: string) {
    const from = this.zone?.id ?? null;
    this.captureExpedition();
    this.scene.simPaused = true;
    Input.captured = true;
    fade.value = { to: 1, seconds: 0.8, caption, sub };
    setTimeout(() => {
      this.enterZone(to, from);
      this.save('travel');
      setTimeout(() => {
        fade.value = { to: 0, seconds: 1.4 };
        Input.captured = false;
      }, caption ? 1400 : 200);
    }, 850);
  }

  enterZone(id: string, from: string | null, at?: { x: number; z: number; facing?: number }) {
    this.leaveZone();
    const make = ZONES[id];
    if (!make) throw new Error(`no zone ${id}`);
    const z = make(this);
    this.zone = z;
    this.scene.setZone(z.build);
    this.enterPlay(z, from, at);
  }

  private enterPlay(z: ZoneRuntime, from: string | null, at?: { x: number; z: number; facing?: number }) {
    const ch = this.ch!;
    this.mode = 'play';
    screen.value = 'play';
    overlay.value = null;
    const kit = deriveKit(ch);
    const start = at ?? z.arrival(from);
    const exp = z.combat ? this.expedition : null;
    const b = this.scene.startBattle({
      seed: Math.floor(Math.random() * 1e9), combat: z.combat, stats: kit.stats, start,
      weapons: kit.weapons, triggers: kit.triggers, ability: kit.ability,
      ember: exp ? { level: exp.level, xp: exp.xp } : undefined,
      hp: exp ? Math.min(exp.hp, kit.stats.get('maxHealth')) : undefined,
    }, loadoutFor({ archetype: ch.archetype, weaponItem: ch.equipment.weapon?.def ?? ARCHETYPES[ch.archetype].weapons[0], model: ch.model, palette: ch.palette, headgear: ch.headgear }));
    b.gearIds = kit.gearIds;
    b.gearStatuses = kit.gearStatuses;
    b.rerolls = exp?.rerolls ?? kit.rerolls;
    b.banishes = exp?.banishes ?? 1;
    b.player.revives = kit.revives;
    if (exp) this.restoreExpedition(b, exp);
    else if (z.combat) {
      // A fresh expedition starts with the boon chosen at creation.
      if (ch.startBoon) b.addBoon(ch.startBoon);
      for (let i = 0; i < kit.startLevels; i++) b.gainEmber(b.ember.next);
    }
    this.hookBattle(b);
    z.begin(b);
    zoneInfo.value = { name: z.name, region: z.region, day: this.world!.day, time: z.timeOf?.(this.world!) ?? this.world!.time };
    this.bridge.extra.gold = ch.gold;
    this.world!.facts['player.zone'] = z.id;
  }

  private restoreExpedition(b: Battle, e: Expedition) {
    for (const w of e.weapons) {
      const have = b.weapons.find((x) => x.id === w.id);
      if (!have) b.addWeapon(w.id, w.rank);
      else have.rank = Math.max(have.rank, w.rank);
      if (w.evolution) b.evolve(w.id, w.evolution);
    }
    for (const [id, r] of Object.entries(e.boons)) for (let i = 0; i < r; i++) b.addBoon(id);
    b.events.drain();
  }

  /** The ember build, carried between zones until the survivor rests. */
  captureExpedition() {
    const b = this.scene.battle;
    if (!b || !b.combat) return;
    this.expedition = {
      level: b.ember.level, xp: b.ember.xp,
      weapons: b.weapons.map((w) => ({ id: w.id, rank: w.rank, evolution: w.evolution?.id ?? null })),
      boons: { ...b.boons }, rerolls: b.rerolls, banishes: b.banishes, hp: b.player.hp,
    };
  }

  /* =========================================================== battle == */

  private hookBattle(b: Battle) {
    const zh = this.zone?.hooks ?? {};
    b.hooks = {
      ...zh,
      onKill: (e, byPlayer) => {
        const ch = this.ch!, w = this.world!;
        if (byPlayer) {
          ch.stats.kills++;
          if (e.lastWeapon) ch.mastery[e.lastWeapon] = (ch.mastery[e.lastWeapon] ?? 0) + 1;
          w.bestiary[e.def.id] = (w.bestiary[e.def.id] ?? 0) + 1;
          if (e.boss) ch.stats.bossesSlain++;
        }
        zh.onKill?.(e, byPlayer);
      },
      onPickup: (p: Pickup) => {
        if (zh.onPickup && zh.onPickup(p) === false) return false;
        if ((p.kind === 'item' || p.kind === 'material' || p.kind === 'quest') && p.ref) return this.giveItem(p.ref, Math.max(1, Math.round(p.value)));
        return true;
      },
      onPlayerDeath: (killer) => {
        if (zh.onPlayerDeath?.(killer)) return true;
        this.onDeath(killer?.named?.title ?? killer?.def.name ?? 'the dark');
        return false;
      },
    };
  }

  /** Something picked up in the field. False if there is no room. */
  giveItem(defId: string, qty = 1): boolean {
    const ch = this.ch!;
    const it = makeItem(ch, defId, { qty });
    if (!addToPack(ch, it)) {
      toast('warning', 'Your pack is full', { sub: ITEMS[defId].name });
      return false;
    }
    const def = ITEMS[defId];
    toast('loot', `${def.name}${qty > 1 ? ` ×${qty}` : ''}`, { icon: def.icon, rarity: it.rarity, sub: def.kind === 'material' ? undefined : def.description });
    return true;
  }

  private onDeath(killer: string) {
    const ch = this.ch!;
    ch.stats.deaths++;
    if (this.zone?.onDeath?.(killer)) return;
    // Outside the prologue: the town's shrine (see the Waystation runtime).
    this.expedition = null;
    setTimeout(() => {
      fade.value = { to: 1, seconds: 1.6, caption: 'You fell', sub: `Taken by ${killer}` };
      setTimeout(() => { overlay.value = 'death'; }, 1700);
    }, 1800);
  }

  /* ========================================================= world ===== */

  private makeCtx(): Ctx {
    return {
      world: this.world!, ch: this.ch!,
      notify: (n) => this.notify(n),
      npcName: (id) => NPC_NAMES[id] ?? id,
      questName: (id) => QUEST_NAMES[id] ?? id,
    };
  }

  notify(n: Notice) {
    const kind = TOAST_KIND[n.tone];
    if (n.tone === 'journal') toast('quest', n.text, { life: 6 });
    else if (n.tone === 'item') {
      const def = Object.values(ITEMS).find((d) => n.text.startsWith(d.name));
      toast('loot', n.text, { icon: def?.icon, rarity: def?.rarity });
    } else toast(kind, n.text);
  }

  /** Apply world effects with notices (quests, dialogue, zone scripts). */
  apply(e: Parameters<typeof apply>[0]) {
    if (this.ctx) apply(e, this.ctx);
  }

  save(_reason: string) {
    const ch = this.ch, w = this.world, b = this.scene.battle;
    if (!ch || !w || !this.zone) return;
    if (b) this.captureExpedition();
    const p = b?.player;
    Saves.write(this.slot, {
      playtime: this.playtime, character: ch, world: w,
      location: { zone: this.zone.id, x: p?.x ?? 0, z: p?.z ?? 0, facing: p?.facing ?? 0 },
      ember: this.expedition,
    });
  }

  /* ======================================================= interaction == */

  private updateInteraction() {
    const b = this.scene.battle;
    const z = this.zone;
    if (!b || !z || overlay.value || !b.player.alive) { prompt.value = null; this.near = null; return; }
    const p = b.player;
    let best: Interactable | null = null, bd = 1e9;
    for (const it of z.interactables) {
      if (it.when && !it.when()) continue;
      const d = Math.hypot(it.x - p.x, it.z - p.z);
      if (d < it.r && d < bd) { bd = d; best = it; }
    }
    this.near = best;
    if (!best) { if (prompt.value) prompt.value = null; return; }
    const locked = best.locked?.() ?? null;
    const cur = prompt.value;
    const next = { key: Input.keyLabel('interact'), verb: best.verb, target: best.name, hint: best.hint?.(), locked: locked ?? undefined };
    if (!cur || cur.target !== next.target || cur.verb !== next.verb || cur.hint !== next.hint || cur.locked !== next.locked) prompt.value = next;
  }

  private onAction(a: string): boolean | void {
    if (this.mode !== 'play') return;
    if (levelUp.value) return;
    const ov = overlay.value;
    if (a === 'pause' && !ov) { this.openOverlay('pause'); return true; }
    if ((a === 'cancel' || a === 'pause') && ov && ov !== 'death' && ov !== 'dialogue' && ov !== 'chapter') { this.closeOverlay(); return true; }
    if (ov) {
      if ((a === 'inventory' && ov === 'inventory') || (a === 'character' && ov === 'character') || (a === 'journal' && ov === 'journal')) { this.closeOverlay(); return true; }
      return;
    }
    if (a === 'inventory') { this.openOverlay('inventory'); return true; }
    if (a === 'character') { this.openOverlay('character'); return true; }
    if (a === 'journal') { this.openOverlay('journal'); return true; }
    if (a === 'interact' && this.near) {
      const locked = this.near.locked?.();
      if (locked) { toast('warning', locked); return true; }
      this.near.act();
      return true;
    }
    if (a === 'ultimate') { this.quaff(); return true; }
  }

  /** R: drink a health draught. */
  private quaff() {
    const b = this.scene.battle, ch = this.ch;
    if (!b || !ch || !b.player.alive) return;
    const i = ch.pack.findIndex((p) => p?.def === 'health_draught');
    if (i < 0) { toast('warning', 'No draughts left'); return; }
    if (b.player.hp >= b.maxHp - 0.5) { toast('warning', 'You are unhurt'); return; }
    const it = ch.pack[i]!;
    it.qty--;
    if (it.qty <= 0) ch.pack[i] = null;
    b.healPlayer(b.maxHp * (ITEMS.health_draught.consumable?.heal ?? 0.4), 'draught');
  }

  openOverlay(o: 'inventory' | 'character' | 'journal' | 'pause' | 'dialogue' | 'shop' | 'rest') {
    overlay.value = o;
    this.scene.simPaused = true;
    Input.captured = true;
    prompt.value = null;
  }

  closeOverlay() {
    overlay.value = null;
    this.scene.simPaused = false;
    Input.captured = false;
    Input.clearLatches();
    // Gear may have changed: the running battle picks it up next zone; the
    // HUD shows the pack now.
    this.bridge.extra.gold = this.ch?.gold ?? 0;
  }

  /* ============================================================ frame == */

  private startBlend(dur: number) {
    this.blend = { pos: this.r.camera.position.clone(), quat: this.r.camera.quaternion.clone(), t: 0, dur };
  }

  /** Cutscene-style camera pose over the game (the boss waking, dawn). */
  poseShowcase(pos: THREE.Vector3 | null, look?: THREE.Vector3) {
    if (!pos) {
      if (this.scene.showcase) this.startBlend(1.4);
      this.scene.showcase = null;
      return;
    }
    this.camPosT.copy(pos);
    this.camLookT.copy(look!);
    if (!this.scene.showcase) { this.camPos.copy(this.r.camera.position); this.camLook.copy(this.camLookT); }
    this.scene.showcase = { pos: this.camPos, look: this.camLook };
  }

  update(dt: number) {
    this.time += dt;
    Input.poll();
    if (this.autopilot && this.mode === 'play') this.autopilot.drive(dt);
    if (this.mode === 'play') {
      this.playtime += dt;
      this.updateInteraction();
      this.autosaveT += dt;
      if (this.autosaveT > 90 && !overlay.value) { this.autosaveT = 0; this.save('auto'); }
      if (this.ch) {
        const q = this.ch.pack.filter((p) => p?.def === 'health_draught').reduce((n, p) => n + (p?.qty ?? 0), 0);
        this.bridge.extra.quick = q > 0 ? { icon: 'potion', name: 'Draught', qty: q } : null;
        this.bridge.extra.gold = this.ch.gold;
      }
    }
    // Showcase camera: drift toward its target, breathing a little.
    if (this.scene.showcase) {
      const breathe = Math.sin(this.time * 0.35) * 0.08;
      this.camPos.x = damp(this.camPos.x, this.camPosT.x + breathe, 1.8, dt);
      this.camPos.y = damp(this.camPos.y, this.camPosT.y + breathe * 0.5, 1.8, dt);
      this.camPos.z = damp(this.camPos.z, this.camPosT.z, 1.8, dt);
      this.camLook.x = damp(this.camLook.x, this.camLookT.x, 2.2, dt);
      this.camLook.y = damp(this.camLook.y, this.camLookT.y, 2.2, dt);
      this.camLook.z = damp(this.camLook.z, this.camLookT.z, 2.2, dt);
    }
    this.zone?.frame?.(dt);
    this.figure?.update(dt);
    this.scene.update(dt);
    // Blend from a held pose into wherever the live camera now is.
    if (this.blend) {
      const bl = this.blend;
      bl.t += dt;
      const k = Math.min(1, bl.t / bl.dur);
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      const cam = this.r.camera;
      cam.position.lerpVectors(bl.pos, cam.position.clone(), e);
      cam.quaternion.slerpQuaternions(bl.quat, cam.quaternion.clone(), e);
      if (k >= 1) this.blend = null;
    }
    this.bridge.update(dt);
  }

  /* ========================================================== actions == */

  private bindActions() {
    Object.assign(actions, {
      newJourney: () => this.newJourney(),
      cancelCreation: () => this.cancelCreation(),
      beginJourney: (c: CreationChoice) => this.beginJourney(c),
      continueJourney: (slot: number) => this.continueJourney(slot),
      deleteSlot: (slot: number) => { Saves.remove(slot); slots.value = Saves.slots(); },
      setQuality: (q: Quality) => { this.r.setQuality(q); },
      resume: () => this.closeOverlay(),
      saveNow: () => { this.save('manual'); toast('world', 'Journey saved'); },
      quitToTitle: () => { this.save('quit'); fade.value = { to: 1, seconds: 0.6 }; setTimeout(() => this.showTitle(), 650); },
      openOverlay: (o: 'inventory' | 'character' | 'journal' | 'pause') => this.openOverlay(o),
      closeOverlay: () => this.closeOverlay(),
      rise: () => this.zone && this.enterZone(this.zone.id, null),
    });
  }

  hasZone(id: string) { return !!ZONES[id]; }

  announceZone() {
    const z = this.zone;
    if (z) announce(z.name, z.region, 'zone', 4.2);
  }
}

/* Names for notices; the full cast lives with the town's content. */
export const NPC_NAMES: Record<string, string> = {
  vonnra: 'Vonnra', maeca: 'Maeca', chid: 'Chid', rav: 'Rav', holloway: 'Captain Holloway', harlan: 'Harlan Coyle',
  pell: 'Pell Varrow', wenna: 'Old Wenna', tam: 'Tam', brannoc: 'Brannoc', rook: 'Mother Rook', keegan: 'Professor Keegan', jory: 'Jory',
  redcowl: 'Redcowl', greymuzzle: 'Greymuzzle', grimtunnel: 'Grimtunnel',
};
export const QUEST_NAMES: Record<string, string> = {
  prologue: 'The Low Ford', beasts: 'The Beast Problem', caravan: 'The Missing Caravan', vault: 'The Sealed Vault', below: 'The Thing Below',
};
