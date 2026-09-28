import type { Battle } from '@/sim/battle';
import type { CombatEvent } from '@/sim/events';
import { draft, choose, earnedBranches, buildTags, draftLevel, blessingNext } from '@/sim/levelup';
import { schoolOf, artOf } from '@/sim/weapons';
import { WEAPON_MAX_RANK } from '@/content/weapons';
import { BOONS } from '@/content/boons';
import { ABILITIES, DASH } from '@/content/abilities';
import { SYNERGY_PAIRS } from '@/content/discoveries';
import { hud, levelUp, overlay, toast, announce, tickUi, type HudState, type HudStatus } from '@/ui/store';
import type { BarkLayer } from '@/ui/hud/barks';
import type { WorldScene } from './scene';
import { Input } from '@/core/input';

/* Between the fight and the interface.
 *
 * Folds the battle into the HUD's plain shapes a dozen times a second,
 * turns the event stream into words (announcements, discoveries, shouts
 * over heads), and runs the level-up draft: when the ember rises, the fight
 * holds its breath for a beat, then stops, and the cards come up. */

const HUD_HZ = 12;

export class HudBridge {
  private acc = 1;
  private pendingT = 0;
  /** Extra HUD fields the game supplies (gold carried, quick slot). */
  extra: { gold?: number; quick?: HudState['quick'] } = {};
  /** Level-up drafts can be suppressed (a cutscene, the tutorial's own). */
  draftsEnabled = true;
  /** Shown on the next draft only (the tutorial's first level). */
  draftTip: string | null = null;
  onDraftClosed: () => void = () => {};

  constructor(private scene: WorldScene, private barks: BarkLayer | null) {}

  get battle(): Battle | null { return this.scene.battle; }

  update(dt: number) {
    tickUi(dt);
    const b = this.battle;
    if (this.barks) this.barks.update(dt, this.scene.r.camera, this.scene.r.width, this.scene.r.height);
    if (!b) { hud.value = null; return; }
    this.acc += dt;
    if (this.acc >= 1 / HUD_HZ) {
      this.acc = 0;
      hud.value = this.snapshot(b);
    }
    // The draft: a short beat after the level flare, then time stops.
    if (this.draftsEnabled && b.draftOwed && !levelUp.value && overlay.value === null && b.player.alive) {
      this.pendingT += dt;
      if (this.pendingT > 0.35) { this.pendingT = 0; this.openDraft(); }
    } else this.pendingT = 0;
  }

  private snapshot(b: Battle): HudState {
    const p = b.player;
    const statuses: HudStatus[] = [];
    if (p.burnT > 0) statuses.push({ id: 'burn', label: 'Burning', glyph: 'flame', tone: 'bad', left: p.burnT });
    if (p.poisonT > 0) statuses.push({ id: 'poison', label: 'Poisoned', glyph: 'plague', tone: 'bad', left: p.poisonT });
    if (p.slowT > 0 && p.slowF < 1) statuses.push({ id: 'slow', label: 'Slowed', glyph: 'boot', tone: 'bad', left: p.slowT });
    if (p.shield > 0) statuses.push({ id: 'shield', label: 'Shielded', glyph: 'aegis', tone: 'good', left: p.shieldT });
    if (p.bulwarkT > 0) statuses.push({ id: 'bulwark', label: 'Bulwark', glyph: 'shield', tone: 'good', left: p.bulwarkT });
    if (p.invisibleT > 0) statuses.push({ id: 'hidden', label: 'Unseen', glyph: 'smoke', tone: 'good', left: p.invisibleT });
    if (b.worldRate < 1) statuses.push({ id: 'slip', label: 'Time Slip', glyph: 'hourglass', tone: 'good', left: b.worldRateT });
    for (const [id, bf] of b.buffs) statuses.push({ id: `buff:${id}`, label: id, glyph: id === 'warcry' ? 'howl' : 'arcane', tone: 'good', left: bf.t });

    const ab = b.ability ? ABILITIES[b.ability] : null;
    const abCd = ab ? ab.cooldown * b.stats.get('abilityCooldown') : 1;
    const maxDash = Math.round(b.stats.get('dashCharges'));
    return {
      combat: b.combat,
      hp: p.hp, maxHp: b.maxHp, shield: p.shield,
      level: b.ember.level, ember: b.ember.xp, emberNext: b.ember.next,
      weapons: b.weapons.map((w) => ({
        id: w.id, name: w.evolution?.name ?? w.def.name, glyph: artOf(w), school: schoolOf(w),
        rank: w.rank, maxRank: WEAPON_MAX_RANK, evolved: !!w.evolution, ready: b.weaponReady(w),
        canEvolve: !w.evolution && w.rank >= WEAPON_MAX_RANK && earnedBranches(b, w.id).length > 0,
      })),
      boons: Object.entries(b.boons).filter(([, r]) => r > 0).map(([id, r]) => {
        const d = BOONS[id];
        return { id, name: d?.name ?? id, glyph: d?.icon ?? 'arcane', rank: r, max: d?.max ?? 1, synergy: d?.kind === 'blessing', rarity: d?.rarity ?? 'common' };
      }),
      dash: { charges: p.dashCharges, max: maxDash, recharge: Math.min(1, p.dashRecharge / DASH.recharge) },
      ability: ab ? { id: ab.id, name: ab.name, glyph: ab.icon, ready: 1 - p.abilityCd / Math.max(0.01, abCd), left: p.abilityCd, active: p.bulwarkT > 0 || p.invisibleT > 0 || !!p.leap } : null,
      gold: (this.extra.gold ?? 0) + b.goldGained,
      kills: b.killCount,
      time: b.time,
      statuses,
      quick: this.extra.quick ?? null,
    };
  }

  /* ---------------------------------------------------------- the draft -- */

  openDraft() {
    const b = this.battle;
    if (!b) return;
    this.scene.simPaused = true;
    Input.captured = true;
    overlay.value = 'levelup';
    this.present(draft(b, b.stats.get('luck') >= 1.5 ? 4 : 3));
  }

  private present(offers: ReturnType<typeof draft>) {
    const b = this.battle!;
    const tags = buildTags(b) as Set<string>;
    const tip = this.draftTip ?? undefined;
    this.draftTip = null;
    levelUp.value = {
      tip,
      level: draftLevel(b),
      milestone: blessingNext(b),
      offers,
      fits: offers.map((o) => o.kind === 'rank' || o.kind === 'evolve' ? [] : o.tags.filter((t) => tags.has(t))),
      rerolls: b.rerolls,
      banishes: b.banishes,
      queued: b.pendingLevels + b.pendingBlessings.length - 1,
      pick: (i) => {
        const o = offers[i];
        if (!o) return;
        choose(b, o);
        if (o.kind === 'weapon') toast('level', `${o.title} joins your arsenal`);
        if (b.draftOwed) this.present(draft(b, offers.length));
        else this.closeDraft();
      },
      reroll: () => {
        if (b.rerolls <= 0) return;
        b.rerolls--;
        this.present(draft(b, offers.length));
      },
      banish: (i) => {
        const o = offers[i];
        if (!o || b.banishes <= 0 || o.kind === 'evolve') return;
        b.banishes--;
        b.bannedCards.add(o.id);
        this.present(draft(b, offers.length));
      },
    };
  }

  closeDraft() {
    levelUp.value = null;
    overlay.value = null;
    this.scene.simPaused = false;
    Input.captured = false;
    Input.clearLatches();
    this.onDraftClosed();
  }

  /* ------------------------------------------------------------- events -- */

  events(evs: CombatEvent[]) {
    const b = this.battle;
    for (const e of evs) {
      switch (e.t) {
        case 'announce':
          announce(e.title, e.subtitle, e.tone ?? 'info', e.subtitle && e.subtitle.length > 60 ? 5 : 3.6, e.kicker);
          break;
        case 'discovery': {
          // The battle announces it; the feed keeps the record a while longer.
          const d = SYNERGY_PAIRS.find((x) => x.id === e.id);
          if (d) toast('discovery', d.name, { sub: 'A new discovery, remembered in the codex', life: 9 });
          break;
        }
        case 'bark':
          if (!this.barks) break;
          if (e.speaker) this.barks.speech(e.text, e.speaker, e.x, this.scene.heightAt(e.x, e.z), e.z);
          else this.barks.alert(e.text, e.x, this.scene.heightAt(e.x, e.z), e.z);
          break;
        case 'playerHit':
          if (e.dodged && this.barks && b) this.barks.alert('Dodged', b.player.x, this.scene.heightAt(b.player.x, b.player.z), b.player.z, 'alert dodge');
          break;
      }
    }
  }
}
