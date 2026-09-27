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
import { SoundBridge } from './soundBridge';
import { mapImage, fogImage } from '@/ui/mapArt';

/** The fog-of-war grid on each zone's map, cells per side. */
const FOG_N = 48;
import {
  screen, overlay, prompt, toast, zoneInfo, slots, creation, fade, hud, levelUp, boss, objectives, announce,
  character, worldView, touch, dialogue, shopView, restView, subtitle, mapView, type CreationDraft, type NoticeKind,
} from '@/ui/store';
import { SHOPS, type ShopDef } from '@/content/shops';
import { RULES, SOCIAL } from '@/content/rules';
import { advanceDay } from '@/world/simulation';
import { PRESETS } from '@/render/atmosphere';
import { test } from '@/world/logic';
import type { ItemInstance } from '@/rpg/character';
import { DialogueRunner, type Presented } from '@/world/dialogue';
import { attitude } from '@/world/logic';
import { CONVOS } from '@/content/dialogue';
import { NPCS, OUTSIDERS, SPEAKERS } from '@/content/npcs';
import { QUESTS } from '@/content/quests';
import { renderPortrait } from '@/ui/portrait';
import { Input } from '@/core/input';
import { damp } from '@/core/math';
import {
  createCharacter, deriveKit, addToPack, makeItem, equip, unequip, findItem, slotFor, fitsSlot, itemName, gainXp,
  type CharacterData, type CreationChoice,
} from '@/rpg/character';
import { EQUIP_SLOTS, type EquipSlot } from '@/content/items';
import { ARCHETYPES, BACKGROUNDS, TRAITS } from '@/content/archetypes';
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
  private fogT = 0;
  readonly sound = new SoundBridge();
  /** Dev: a crude player that drives the game (?auto). */
  autopilot: { drive(dt: number): void } | null = null;

  constructor(readonly r: Renderer) {
    this.scene = new WorldScene(r);
    this.barks = new BarkLayer(document.getElementById('stage')!);
    this.bridge = new HudBridge(this.scene, this.barks);
    this.scene.onEvents = (evs) => {
      this.bridge.events(evs);
      this.sound.events(evs, this.scene.battle);
      this.zone?.events?.(evs);
      for (const e of evs) {
        // The codex remembers every pairing ever found, for every survivor.
        if (e.t === 'discovery' && this.world && !this.world.codex.includes(e.id)) this.world.codex.push(e.id);
      }
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
    character.value = null;
    worldView.value = null;
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
    world.facts['beasts.population'] = 60;
    const starter = makeItem(ch, 'health_draught', { qty: 1 });
    addToPack(ch, starter);
    this.ch = ch;
    this.world = world;
    character.value = ch;
    worldView.value = world;
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
    character.value = d.character;
    worldView.value = d.world;
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
    subtitle.value = null;
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
    // Travel paused the world for the fade; a new place starts running.
    this.scene.simPaused = false;
    const kit = deriveKit(ch);
    const start = at ?? z.arrival(from);
    const exp = z.combat ? this.expedition : null;
    const b = this.scene.startBattle({
      seed: Math.floor(Math.random() * 1e9), combat: z.combat, stats: kit.stats, start,
      weapons: kit.weapons, triggers: kit.triggers, ability: kit.ability,
      ember: exp ? { level: exp.level, xp: exp.xp } : undefined,
      hp: exp ? Math.min(exp.hp, kit.stats.get('maxHealth')) : undefined,
    }, this.loadout());
    this.gearWeapons = new Set(kit.weapons.map((w) => w.id));
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
          // The survivor grows too, more slowly than the ember.
          const levels = gainXp(ch, e.def.xp * (e.boss ? 3 : e.elite ? 2 : 1));
          if (levels > 0) {
            announce(`Level ${ch.level}`, ch.traitPicks > 0 ? 'A new trait can be chosen (C)' : 'Attribute points to spend (C)', 'boon', 3.2, 'You grow stronger');
            touch();
          }
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
    touch();
    return true;
  }

  private onDeath(killer: string) {
    const ch = this.ch!;
    ch.stats.deaths++;
    if (this.zone?.onDeath?.(killer)) return;
    const w = this.world!, b = this.scene.battle, z = this.zone!;
    const p = b?.player;
    const k = p?.lastKiller ?? null;
    // Your gold stays where you fell; one thing you carried goes with
    // whatever killed you, and it is not the same creature any more.
    const gold = Math.floor(ch.gold / 2);
    ch.gold -= gold;
    const pool = ch.pack.map((it, i) => ({ it, i })).filter((x) => x.it && !['quest', 'consumable'].includes(ITEMS[x.it.def].kind));
    const pick = pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
    if (pick) ch.pack[pick.i] = null;
    w.corpse = { zone: z.id, x: p?.x ?? 0, z: p?.z ?? 0, gold, items: [], day: w.day, killer, heroName: ch.name };
    if (k && !k.boss && k.def.id !== 'grimtunnel') {
      const title = `${nemesisName(k.def.family)}, Who Took Your Light`;
      w.nemesis = { zone: z.id, def: k.def.id, title, level: k.level + 2, carries: pick ? [pick.it!] : [], heroName: ch.name, killed: false };
    }
    ch.conditions = ch.conditions.filter((c) => c.id !== 'rested');
    this.apply([
      { condition: { id: 'wounded', days: 2, note: `You fell in ${z.name}` } },
      { if: { not: { trait: 'risen_once' } }, then: { trait: 'risen_once' } },
      { history: { id: `fell_${w.day}_${ch.stats.deaths}`, text: `fell in ${z.name} to ${killer}`, tags: ['death'], spread: 2, sentiment: { respect: -3 }, reactions: { chid: { affection: 10 } } } },
      { set: { 'player.just_died': true } },
    ]);
    this.expedition = null;
    setTimeout(() => {
      fade.value = { to: 1, seconds: 1.8, caption: 'You fell', sub: `Taken by ${killer}` };
      setTimeout(() => {
        this.enterZone('waystation', 'death');
        this.save('death');
        setTimeout(() => {
          fade.value = { to: 0, seconds: 2 };
          setTimeout(() => this.talk('chid'), 1600);
        }, 1400);
      }, 2400);
    }, 1500);
  }

  /* ========================================================= world ===== */

  private makeCtx(): Ctx {
    return {
      world: this.world!, ch: this.ch!,
      notify: (n) => this.notify(n),
      npcName: (id) => NPC_NAMES[id] ?? id,
      questName: (id) => QUEST_NAMES[id] ?? id,
      entryText: (q, e) => `${QUESTS[q]?.name ?? q}: ${QUESTS[q]?.entries[e] ?? 'journal updated'}`,
    };
  }

  notify(n: Notice) {
    const kind = TOAST_KIND[n.tone];
    if (n.tone === 'journal') {
      // "Quest: what you learned" reads as a title and a line.
      const i = n.text.indexOf(': ');
      if (i > 0 && !n.text.startsWith('New')) toast('quest', n.text.slice(0, i), { sub: n.text.slice(i + 2), life: 8 });
      else toast('quest', n.text, { life: 6 });
    }
    else if (n.tone === 'item') {
      const def = Object.values(ITEMS).find((d) => n.text.startsWith(d.name));
      toast('loot', n.text, { icon: def?.icon, rarity: def?.rarity });
    } else toast(kind, n.text);
  }

  /** Apply world effects with notices (quests, dialogue, zone scripts). */
  apply(e: Parameters<typeof apply>[0]) {
    if (this.ctx) apply(e, this.ctx);
    touch();
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
      if ((a === 'inventory' && ov === 'inventory') || (a === 'character' && ov === 'character') || (a === 'journal' && ov === 'journal') || (a === 'map' && ov === 'map')) { this.closeOverlay(); return true; }
      return;
    }
    if (a === 'inventory') { this.openOverlay('inventory'); return true; }
    if (a === 'character') { this.openOverlay('character'); return true; }
    if (a === 'journal') { this.openOverlay('journal'); return true; }
    if (a === 'map') { this.openMap(); return true; }
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

  /* ============================================================== map == */

  /** Mark the ground around the survivor as walked, on the zone's fog grid. */
  private walk(dt: number) {
    const b = this.scene.battle, z = this.zone, w = this.world;
    if (!b || !z || !w || this.mode !== 'play') return;
    this.fogT -= dt;
    if (this.fogT > 0) return;
    this.fogT = 0.4;
    const extent = this.scene.zone?.map?.extent ?? (this.scene.zone?.collision.bound ?? 100) * 2;
    const zs = (w.zones[z.id] ??= {});
    let seen = typeof zs.seen === 'string' && zs.seen.length === FOG_N * FOG_N ? zs.seen : '0'.repeat(FOG_N * FOG_N);
    const p = b.player, r = 30, c = extent / FOG_N;
    const i0 = Math.floor((p.x - r) / c + FOG_N / 2), i1 = Math.floor((p.x + r) / c + FOG_N / 2);
    const j0 = Math.floor((p.z - r) / c + FOG_N / 2), j1 = Math.floor((p.z + r) / c + FOG_N / 2);
    let changed = false;
    const arr = seen.split('');
    for (let j = Math.max(0, j0); j <= Math.min(FOG_N - 1, j1); j++) for (let i = Math.max(0, i0); i <= Math.min(FOG_N - 1, i1); i++) {
      const cx = (i + 0.5 - FOG_N / 2) * c, cz = (j + 0.5 - FOG_N / 2) * c;
      if (arr[j * FOG_N + i] === '0' && Math.hypot(cx - p.x, cz - p.z) < r) { arr[j * FOG_N + i] = '1'; changed = true; }
    }
    if (changed) { seen = arr.join(''); zs.seen = seen; }
  }

  openMap() {
    const z = this.zone, build = this.scene.zone, b = this.scene.battle, w = this.world;
    if (!z || !build || !b || !w) return;
    this.fogT = 0;
    this.walk(0);
    const art = mapImage(build);
    const zs = w.zones[z.id] ?? {};
    const seen = typeof zs.seen === 'string' ? zs.seen : '0'.repeat(FOG_N * FOG_N);
    const c = w.corpse && w.corpse.zone === z.id ? w.corpse : null;
    mapView.value = {
      zone: z.id, name: z.name, region: z.region ?? '', image: art.url, fog: fogImage(seen, FOG_N), extent: art.extent, seen, n: FOG_N,
      marks: z.mapMarks?.() ?? [],
      player: { x: b.player.x, z: b.player.z, facing: b.player.facing },
      corpse: c ? { x: c.x, z: c.z, label: `${c.heroName}'s belongings` } : undefined,
    };
    this.openOverlay('map');
  }

  openOverlay(o: 'inventory' | 'character' | 'journal' | 'pause' | 'dialogue' | 'shop' | 'rest' | 'stash' | 'chapter' | 'map') {
    overlay.value = o;
    this.scene.simPaused = true;
    Input.captured = true;
    prompt.value = null;
  }

  closeOverlay() {
    if (overlay.value === 'shop') shopView.value = null;
    if (overlay.value === 'rest' && restView.value?.phase === 'report') { this.finishRest(); return; }
    overlay.value = null;
    this.scene.simPaused = false;
    Input.captured = false;
    Input.clearLatches();
    // Gear may have changed: the running battle picks it up next zone; the
    // HUD shows the pack now.
    this.bridge.extra.gold = this.ch?.gold ?? 0;
  }

  /* ============================================================= gear == */

  equipItem(uid: string, slot?: string) {
    const ch = this.ch;
    if (!ch) return;
    const loc = findItem(ch, uid);
    if (!loc) return;
    const def = ITEMS[loc.item.def];
    let target = (slot as EquipSlot | undefined) ?? slotFor(def);
    if (!target) return;
    // Rings go to whichever hand is free.
    if (!slot && target === 'ring1' && ch.equipment.ring1 && !ch.equipment.ring2) target = 'ring2';
    if (!fitsSlot(def, target)) return;
    if (!equip(ch, loc.item, target)) { toast('warning', 'No room in your pack for what you are wearing'); return; }
    toast('loot', `Wearing ${itemName(loc.item)}`, { icon: def.icon, rarity: loc.item.rarity });
    this.refreshKit();
  }

  unequipSlot(slot: string) {
    const ch = this.ch;
    if (!ch || !EQUIP_SLOTS.includes(slot as EquipSlot)) return;
    if (slot === 'weapon') { toast('warning', 'You will not walk this road unarmed'); return; }
    if (!unequip(ch, slot as EquipSlot)) { toast('warning', 'Your pack is full'); return; }
    this.refreshKit();
  }

  useItem(uid: string) {
    const ch = this.ch, b = this.scene.battle;
    if (!ch) return;
    const loc = findItem(ch, uid);
    if (!loc || loc.where !== 'pack') return;
    const def = ITEMS[loc.item.def];
    if (def.kind !== 'consumable' || !def.consumable) { this.equipItem(uid); return; }
    const c = def.consumable;
    if (c.heal && b) {
      if (b.player.hp >= b.maxHp - 0.5) { toast('warning', 'You are unhurt'); return; }
      b.healPlayer(b.maxHp * c.heal, 'draught');
    }
    for (const cure of c.cure ?? []) {
      if (cure === 'poisoned' && b) b.player.poisonT = 0;
      ch.conditions = ch.conditions.filter((x) => x.id !== cure);
    }
    loc.item.qty--;
    if (loc.item.qty <= 0) ch.pack[loc.index as number] = null;
    toast('world', `${def.name} used`);
    touch();
  }

  dropItem(uid: string) {
    const ch = this.ch;
    if (!ch) return;
    const loc = findItem(ch, uid);
    if (!loc || loc.where !== 'pack') return;
    const def = ITEMS[loc.item.def];
    if (def.kind === 'quest') { toast('warning', 'You might need that'); return; }
    ch.pack[loc.index as number] = null;
    toast('world', `Left behind: ${itemName(loc.item)}`);
    touch();
  }

  /** Gear changed: fold it into the running fight at once. */
  refreshKit() {
    const ch = this.ch, b = this.scene.battle;
    touch();
    if (!ch || !b) return;
    const kit = deriveKit(ch);
    const fromKit = (src: string) => src.startsWith('item:') || src === 'attributes' || src.startsWith('trait:') || src.startsWith('cond:');
    b.stats.removeWhere(fromKit);
    b.stats.setBase(kit.stats.getBase());
    b.stats.addAll(kit.stats.list().filter((m) => fromKit(m.source)));
    b.triggers = b.triggers.filter((t) => !t.source.startsWith('item:') && !t.source.startsWith('trait:'));
    for (const t of kit.triggers) b.addTrigger(t.def, t.source);
    const kitIds = new Set(kit.weapons.map((w) => w.id));
    for (const id of this.gearWeapons) if (!kitIds.has(id)) b.removeWeapon(id);
    for (const w of kit.weapons) if (!b.weapons.some((x) => x.id === w.id)) b.addWeapon(w.id, w.rank);
    this.gearWeapons = kitIds;
    b.gearIds = kit.gearIds;
    b.gearStatuses = kit.gearStatuses;
    b.player.hp = Math.min(b.player.hp, b.maxHp);
    this.scene.setLoadout(this.loadout());
  }

  private gearWeapons = new Set<string>();

  loadout() {
    const ch = this.ch!;
    return loadoutFor({ archetype: ch.archetype, weaponItem: ch.equipment.weapon?.def ?? ARCHETYPES[ch.archetype].weapons[0], model: ch.model, palette: ch.palette, headgear: ch.headgear });
  }

  /* ======================================================= dialogue == */

  private runner: DialogueRunner | null = null;
  private talkNpc: string | null = null;
  private dlgKey = 0;
  private portraits = new Map<string, string | null>();
  private camSaved: number | null = null;

  talk(id: string) {
    const convo = CONVOS[id];
    if (!convo || !this.ctx) return;
    const runner = new DialogueRunner(convo, this.ctx);
    const p = runner.start();
    if (!p) return;
    this.runner = runner;
    this.talkNpc = id;
    const actor = this.zone?.actors?.get(id);
    const b = this.scene.battle;
    if (actor && b) {
      actor.talking = true;
      actor.gesture();
      const y = this.scene.heightAt(actor.x, actor.z);
      this.scene.cam.focusOverride = new THREE.Vector3((actor.x + b.player.x) / 2, y + 1, (actor.z + b.player.z) / 2);
      this.camSaved = this.scene.cam.targetDistance;
      this.scene.cam.targetDistance = 12.5;
      // Face the person you are talking to.
      b.player.facing = Math.atan2(actor.x - b.player.x, actor.z - b.player.z);
    }
    this.openOverlay('dialogue');
    this.present(p);
    touch();
  }

  private portraitOf(id: string) {
    if (!this.portraits.has(id)) {
      const d = NPCS[id] ?? OUTSIDERS[id];
      this.portraits.set(id, d ? renderPortrait({ model: d.model, show: d.show, attackClips: [], heavyClip: '', tint: d.tint }, 190, 228, 'bust', d.scale ?? 1) : null);
    }
    return this.portraits.get(id) ?? null;
  }

  private present(p: Presented) {
    const id = this.talkNpc!;
    const d = NPCS[id] ?? OUTSIDERS[id];
    const sp = SPEAKERS[id];
    const s = this.world ? npc(this.world, id) : null;
    dialogue.value = {
      npc: id, name: d?.name ?? sp?.name ?? id, title: d?.title ?? sp?.title ?? '', portrait: this.portraitOf(id), glyph: sp?.glyph,
      mood: s && (d || id === 'greymuzzle' || id === 'snib') ? attitude(s) : '', speaker: p.speaker === 'player' ? 'player' : p.speaker === 'narrator' ? 'narrator' : 'npc',
      text: p.text, key: ++this.dlgKey,
      choices: p.choices.map((c) => ({ index: c.index, text: c.text, enabled: c.enabled, locked: c.locked, badge: c.badge, ends: c.ends, action: c.action })),
      canContinue: p.choices.length === 0,
    };
  }

  chooseDialogue(i: number) {
    const r = this.runner;
    if (!r) return;
    const res = r.choose(i);
    touch();
    if (res.action) {
      const keepTalking = this.dialogueAction(res.action);
      if (!keepTalking) { this.endDialogue(); return; }
    }
    if (res.next) this.present(res.next);
    else if (!res.action) this.endDialogue();
    else if (r.node) { const p = r.present(); if (p) this.present(p); }
  }

  advanceDialogue() {
    const r = this.runner;
    if (!r) return;
    const p = r.advance();
    touch();
    if (p) this.present(p);
    else this.endDialogue();
  }

  endDialogue() {
    const actor = this.talkNpc ? this.zone?.actors?.get(this.talkNpc) : null;
    if (actor) actor.talking = false;
    this.scene.cam.focusOverride = null;
    if (this.camSaved !== null) { this.scene.cam.targetDistance = this.camSaved; this.camSaved = null; }
    this.runner = null;
    this.talkNpc = null;
    dialogue.value = null;
    if (overlay.value === 'dialogue') this.closeOverlay();
    this.save('talk');
  }

  /** Services a conversation opens. Returns true to stay in the conversation. */
  private dialogueAction(a: string): boolean {
    const ch = this.ch!, w = this.world!;
    const from = this.talkNpc ?? '';
    switch (a) {
      case 'trade':
      case 'sell':
        this.endDialogue();
        this.openShop(from);
        return false;
      case 'stash':
        this.endDialogue();
        this.openOverlay('stash');
        return false;
      case 'rest':
        this.endDialogue();
        this.openRest();
        return false;
      case 'fortune':
        this.endDialogue();
        this.save('chapter');
        this.openOverlay('chapter');
        return false;
      case 'sellpelts': {
        const pelts = this.countOf('wolf_pelt'), hides = this.countOf('boar_hide');
        if (!pelts && !hides) { toast('warning', 'You have nothing he wants'); return true; }
        this.apply([
          { take: 'wolf_pelt', qty: pelts }, { take: 'boar_hide', qty: hides }, { gold: pelts * 8 + hides * 6 },
          { add: { 'beasts.pelts_sold': pelts } }, { quest: { id: 'beasts', entry: 'pelts_sold' } },
          { history: { id: 'sold_pelts', text: 'sold wolf pelts to Brannoc', tags: ['beasts', 'trade'], spread: 1, reactions: { maeca: { affection: -10 } } } },
        ]);
        return true;
      }
      case 'bounty': {
        const pelts = this.countOf('wolf_pelt');
        if (!pelts) return true;
        const sold = Number(w.facts['beasts.pelts_sold'] ?? 0) > 0;
        this.apply([
          { take: 'wolf_pelt', qty: pelts }, { gold: pelts * 5 }, { set: { 'beasts.bounty_claimed': true } }, { quest: { id: 'beasts', entry: 'bounty_claimed' } },
          { rel: { npc: 'holloway', respect: Math.min(15, pelts * 2) } },
        ]);
        if (sold) this.apply({ history: { id: 'double_dipped', text: 'sold pelts to Brannoc and claimed Holloway\'s bounty on the same wolves', tags: ['greed', 'beasts'], spread: 2, reactions: { holloway: { trust: -30 }, brannoc: { trust: -20 } } } });
        return true;
      }
      case 'reforge': {
        const wpn = ch.equipment.weapon;
        if (!wpn) return true;
        if (wpn.rarity >= 4) { toast('warning', 'Brannoc: "There is nothing more I can do to that."'); return true; }
        const cost = 40 * (wpn.rarity + 1);
        if (ch.gold < cost) { toast('warning', `Reforging costs ${cost} gold`); return true; }
        ch.gold -= cost;
        wpn.rarity++;
        (wpn.history ??= []).push(`Reforged by Brannoc, day ${w.day}`);
        toast('loot', `${itemName(wpn)} reforged`, { icon: ITEMS[wpn.def].icon, rarity: wpn.rarity, sub: 'It starts every expedition a rank higher.' });
        this.refreshKit();
        return true;
      }
    }
    return true;
  }

  private countOf(def: string) {
    return this.ch!.pack.reduce((n, p) => n + (p?.def === def ? p.qty : 0), 0);
  }

  /* ============================================================ shops == */

  openShop(id: string) {
    const def = SHOPS[id];
    const w = this.world, ch = this.ch;
    if (!def || !w || !ch) { toast('world', 'They have nothing to sell you'); return; }
    let st = w.shops[id];
    if (!st || w.day >= st.restockDay) {
      st = { stock: this.rollStock(def), restockDay: w.day + def.restockDays, priceMult: 1 };
      w.shops[id] = st;
    }
    shopView.value = { id, name: def.name, npc: id };
    this.openOverlay('shop');
    touch();
  }

  private rollStock(def: ShopDef): ItemInstance[] {
    const out: ItemInstance[] = [];
    for (const l of def.lines) {
      if (l.when && !test(l.when, this.ctx!)) continue;
      if (l.chance !== undefined && Math.random() > l.chance) continue;
      if (!ITEMS[l.id]) continue;
      out.push(makeItem(this.ch, l.id, { qty: l.qty ?? 1, rarity: l.rarity }));
    }
    return out;
  }

  /** How much a seller likes you, as a price multiplier. */
  private priceMod(npcId: string) {
    const s = this.world ? npc(this.world, npcId) : null;
    let m = 1;
    if (s) {
      if (s.trust >= 30 || s.affection >= 30) m *= 0.9;
      if (s.trust <= -30) m *= 1.25;
      if (s.fear >= 40) m *= 0.85;
    }
    if (this.ch?.traits.includes('silver_tongue')) m *= 0.9;
    if (npcId === 'harlan' && s?.flags.discount) m *= 0.8;
    return m;
  }

  private unitValue(it: ItemInstance) {
    const def = ITEMS[it.def];
    return def.value * (1 + 0.6 * Math.max(0, it.rarity - def.rarity)) * (1 + 0.15 * it.affixes.length);
  }

  priceOf(uid: string, side: 'buy' | 'sell'): number | null {
    const sv = shopView.value, w = this.world, ch = this.ch;
    if (!sv || !w || !ch) return null;
    const def = SHOPS[sv.id];
    if (side === 'buy') {
      const it = w.shops[sv.id]?.stock.find((x) => x.uid === uid);
      return it ? Math.max(1, Math.ceil(this.unitValue(it) * def.markup * this.priceMod(sv.npc))) : null;
    }
    const it = ch.pack.find((x) => x?.uid === uid);
    if (!it) return null;
    const kind = ITEMS[it.def].kind;
    if (def.buys !== 'all' && !def.buys.includes(kind)) return null;
    if (kind === 'quest' && def.buys !== 'all' && sv.id !== 'vonnra') return null;
    return Math.max(1, Math.floor(this.unitValue(it) * def.pays / Math.max(0.8, this.priceMod(sv.npc)))) * it.qty;
  }

  buy(uid: string) {
    const sv = shopView.value, w = this.world, ch = this.ch;
    if (!sv || !w || !ch) return;
    const st = w.shops[sv.id];
    const i = st?.stock.findIndex((x) => x.uid === uid) ?? -1;
    if (i < 0) return;
    const it = st.stock[i];
    const price = this.priceOf(uid, 'buy')!;
    if (ch.gold < price) { toast('warning', `That costs ${price} gold`); return; }
    const one = it.qty > 1 ? { ...it, uid: `i${ch.nextUid++}`, qty: 1, affixes: [...it.affixes] } : it;
    if (!addToPack(ch, one)) { toast('warning', 'Your pack is full'); return; }
    ch.gold -= price;
    if (it.qty > 1) it.qty--; else st.stock.splice(i, 1);
    toast('loot', `Bought ${itemName(one)}`, { icon: ITEMS[one.def].icon, rarity: one.rarity, sub: `−${price} gold` });
    touch();
  }

  sell(uid: string) {
    const sv = shopView.value, w = this.world, ch = this.ch;
    if (!sv || !w || !ch) return;
    const price = this.priceOf(uid, 'sell');
    if (price === null) { toast('warning', 'They will not buy that'); return; }
    const i = ch.pack.findIndex((x) => x?.uid === uid);
    const it = ch.pack[i]!;
    ch.pack[i] = null;
    ch.gold += price;
    ch.stats.goldEarned += price;
    w.shops[sv.id]?.stock.push(it);
    if (it.def === 'wolf_pelt' && sv.id === 'brannoc') this.apply([{ add: { 'beasts.pelts_sold': it.qty } }, { quest: { id: 'beasts', entry: 'pelts_sold' } }]);
    toast('gold', `Sold ${itemName(it)}${it.qty > 1 ? ` ×${it.qty}` : ''}`, { sub: `+${price} gold` });
    touch();
  }

  /* ============================================================ stash == */

  toStash(uid: string) {
    const ch = this.ch, w = this.world;
    if (!ch || !w) return;
    const i = ch.pack.findIndex((x) => x?.uid === uid);
    const j = w.stash.indexOf(null);
    if (i < 0) return;
    if (j < 0) { toast('warning', 'The storeroom is full'); return; }
    w.stash[j] = ch.pack[i];
    ch.pack[i] = null;
    touch();
  }

  fromStash(uid: string) {
    const ch = this.ch, w = this.world;
    if (!ch || !w) return;
    const j = w.stash.findIndex((x) => x?.uid === uid);
    if (j < 0) return;
    if (!addToPack(ch, w.stash[j]!)) { toast('warning', 'Your pack is full'); return; }
    w.stash[j] = null;
    touch();
  }

  /* ============================================================= rest == */

  openRest() {
    const w = this.world!, ch = this.ch!;
    const rook = npc(w, 'rook');
    const cost = rook.affection >= 30 || rook.trust >= 40 ? 0 : 5;
    restView.value = { phase: 'choose', day: w.day, lines: [], canNight: w.time !== 'night', cost, afford: ch.gold >= cost };
    this.openOverlay('rest');
  }

  rest(mode: 'sleep' | 'night') {
    const w = this.world!, ch = this.ch!, rv = restView.value;
    if (!rv) return;
    if (mode === 'night') {
      w.time = 'night';
      this.closeRest();
      fade.value = { to: 1, seconds: 0.8, caption: 'Nightfall', sub: `Day ${w.day}` };
      setTimeout(() => {
        this.scene.atmo.set(PRESETS.night);
        if (zoneInfo.value) zoneInfo.value = { ...zoneInfo.value, time: 'night' };
        fade.value = { to: 0, seconds: 1.2 };
        this.save('night');
      }, 1400);
      return;
    }
    if (!rv.afford) return;
    ch.gold -= rv.cost;
    const hadEmber = !!this.expedition || (this.scene.battle?.ember.level ?? 1) > 1;
    const report = advanceDay(this.ctx!, RULES, SOCIAL);
    w.time = 'day';
    this.expedition = null;
    const b = this.scene.battle;
    if (b) b.player.hp = b.maxHp;
    const lines = [...report.lines];
    // The talk of the town: who heard what, overnight.
    const byEvent = new Map<string, string[]>();
    for (const h of report.heard) {
      if (!NPC_NAMES[h.npc]) continue;
      const l = byEvent.get(h.event) ?? [];
      l.push({ holloway: 'Holloway', harlan: 'Harlan', pell: 'Pell', keegan: 'Keegan' }[h.npc] ?? NPC_NAMES[h.npc]);
      byEvent.set(h.event, l);
    }
    for (const [id, who] of [...byEvent].slice(0, 2)) {
      const ev = w.history.find((h) => h.id === id);
      if (!ev) continue;
      const names = who.length === 1 ? who[0] : `${who.slice(0, -1).join(', ')} and ${who[who.length - 1]}`;
      lines.push(`By breakfast, ${names} had heard that you ${ev.text}.`);
    }
    if (hadEmber) lines.push('The ember went out while you slept. Whatever you became out there, you will have to become again.');
    if (!lines.length) lines.push('A quiet night. Rook\'s bread is hot, and nobody died.');
    fade.value = { to: 1, seconds: 0.9 };
    setTimeout(() => {
      restView.value = { ...rv, phase: 'report', day: w.day, lines };
      this.scene.atmo.set(PRESETS.day);
      if (zoneInfo.value) zoneInfo.value = { ...zoneInfo.value, time: 'day', day: w.day };
      touch();
      this.save('rest');
    }, 950);
  }

  finishRest() {
    this.closeRest();
    fade.value = { to: 0, seconds: 1.4 };
  }

  private closeRest() {
    restView.value = null;
    if (overlay.value === 'rest') this.closeOverlay();
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
      this.walk(dt);
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
    // Speech bubbles and names step back during a conversation.
    const quiet = overlay.value === 'dialogue' ? '0' : '1';
    if (this.barks.root.style.opacity !== quiet) this.barks.root.style.opacity = quiet;
    this.scene.update(dt);
    {
      const b = this.scene.battle;
      const f = b ? b.player : this.scene.showcase?.look ?? this.scene.cam.focus;
      const time = (this.world && this.zone?.timeOf?.(this.world)) ?? this.world?.time ?? 'night';
      this.sound.update(dt, { zone: this.zone?.id ?? null, mode: this.mode, time, px: f.x, pz: f.z, battle: b, ambience: this.zone?.ambience });
    }
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
      setQuality: (q: Quality) => { this.r.setQuality(q); try { localStorage.setItem('survivor-unchained.quality', q); } catch { /* no storage */ } },
      resume: () => this.closeOverlay(),
      saveNow: () => { this.save('manual'); toast('world', 'Journey saved'); },
      cycleSound: () => this.sound.cycle(),
      setSound: (l: 'on' | 'quiet' | 'off') => this.sound.set(l),
      quality: () => this.r.quality,
      soundLevel: () => this.sound.level,
      quitToTitle: () => { this.save('quit'); fade.value = { to: 1, seconds: 0.6 }; setTimeout(() => this.showTitle(), 650); },
      openOverlay: (o: 'inventory' | 'character' | 'journal' | 'pause') => this.openOverlay(o),
      closeOverlay: () => this.closeOverlay(),
      rise: () => this.zone && this.enterZone(this.zone.id, null),
      equipItem: (uid: string, slot?: string) => this.equipItem(uid, slot),
      unequip: (slot: string) => this.unequipSlot(slot),
      useItem: (uid: string) => this.useItem(uid),
      dropItem: (uid: string) => this.dropItem(uid),
      choose: (i: number) => this.chooseDialogue(i),
      advance: () => this.advanceDialogue(),
      buy: (_shop: string, uid: string) => this.buy(uid),
      sell: (uid: string) => this.sell(uid),
      stash: (uid: string) => this.toStash(uid),
      unstash: (uid: string) => this.fromStash(uid),
      rest: (mode: 'sleep' | 'night') => this.rest(mode),
      finishRest: () => this.finishRest(),
      priceOf: (uid: string, side: 'buy' | 'sell') => this.priceOf(uid, side),
      spendPoint: (a: 'might' | 'finesse' | 'wits' | 'resolve') => {
        const ch = this.ch;
        if (!ch || ch.points <= 0) return;
        ch.points--;
        ch.attributes[a]++;
        this.refreshKit();
      },
      pickTrait: (id: string) => {
        const ch = this.ch;
        if (!ch || ch.traitPicks <= 0 || ch.traits.includes(id)) return;
        ch.traitPicks--;
        ch.traits.push(id);
        toast('level', `You have become: ${TRAITS[id]?.name ?? id}`);
        this.refreshKit();
      },
    });
  }

  hasZone(id: string) { return !!ZONES[id]; }

  announceZone() {
    const z = this.zone;
    if (z) announce(z.name, z.region, 'zone', 4.2);
  }
}

/** What the thing that killed you is called now. */
function nemesisName(family: string) {
  const names: Record<string, string[]> = {
    wolf: ['Ash-Fang', 'Hollow-Eye', 'Old Greyback', 'Split-Ear'],
    boar: ['Old Tusk', 'the Hedge-Breaker'],
    kerchief: ['Red Wat', 'Knuckles Marro', 'Sly Dell'],
    lampling: ['Wick', 'Soot-Tooth'],
    undead: ['the Unburied', 'the Drowned Watchman'],
  };
  const list = names[family] ?? ['the Thing in the Wood'];
  return list[Math.floor(Math.random() * list.length)];
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
