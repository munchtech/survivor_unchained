import { effect } from '@preact/signals';
import type { CombatEvent } from '@/sim/events';
import type { Battle } from '@/sim/battle';
import { audio } from '@/audio/engine';
import { SFX } from '@/audio/sfx';
import { Ambience } from '@/audio/ambience';
import { Music, type Mood } from '@/audio/music';
import { overlay, toasts, announcement, dialogue, boss, screen } from '@/ui/store';

/* Where the game becomes sound.
 *
 * Combat events turn into hits and kills, panned to where they happened
 * and quieter the further off they are; the interface's own signals (an
 * overlay opening, a toast, a line of dialogue) turn into its sounds; and
 * every frame the music is told what kind of moment this is and the
 * ambience what kind of place. Settings persist in the browser. */

const KEY = 'survivor-unchained.sound';

export interface SoundState { zone: string | null; mode: 'title' | 'create' | 'play'; time: string; px: number; pz: number; battle: Battle | null; ambience?: (x: number, z: number) => object }

export class SoundBridge {
  readonly ambience = new Ambience();
  readonly music = new Music();
  private xpStreak = 0;
  private xpT = 0;
  private lastToast = 0;
  private lastAnnounce = 0;
  private lastDialogue = 0;
  private hostilesNear = 0;
  level: 'on' | 'quiet' | 'off' = 'on';

  constructor() {
    try { const v = localStorage.getItem(KEY); if (v === 'quiet' || v === 'off') this.level = v; } catch { /* no storage */ }
    (window as unknown as { __sfx: typeof SFX }).__sfx = SFX;
    // Browsers only allow sound after the player has done something.
    const wake = () => { audio.start(); this.apply(); };
    window.addEventListener('pointerdown', wake, { capture: true });
    window.addEventListener('keydown', wake, { capture: true });
    // The interface: every button ticks under the cursor and clicks.
    document.addEventListener('pointerover', (e) => {
      const el = (e.target as HTMLElement | null)?.closest?.('button, .slot, .card, .choice');
      if (el && !(el as HTMLButtonElement).disabled && !el.contains(e.relatedTarget as Node)) SFX.hover();
    });
    document.addEventListener('click', (e) => {
      const el = (e.target as HTMLElement | null)?.closest?.('button');
      if (el) (el as HTMLButtonElement).disabled ? SFX.deny() : SFX.click();
    }, { capture: true });
    let prevOverlay: string | null = null;
    effect(() => {
      const o = overlay.value;
      if (o === prevOverlay) return;
      if (o && o !== 'dialogue' && o !== 'levelup' && o !== 'death' && o !== 'chapter') SFX.open();
      else if (!o && prevOverlay && prevOverlay !== 'dialogue') SFX.close();
      if (o === 'chapter') SFX.stinger('story');
      prevOverlay = o;
    });
    effect(() => {
      const list = toasts.value;
      const last = list[list.length - 1];
      if (!last || last.id <= this.lastToast) return;
      this.lastToast = last.id;
      switch (last.kind) {
        case 'quest': SFX.quest(); break;
        case 'relation': SFX.rel(!/distrust|dislike|contempt|afraid|-/i.test(last.text + (last.sub ?? ''))); break;
        case 'loot': SFX.loot((last.rarity ?? 0) >= 2); break;
        case 'discovery': SFX.discovery(); break;
        case 'lore': SFX.stinger('story'); break;
        case 'warning': SFX.deny(); break;
      }
    });
    effect(() => {
      const a = announcement.value;
      if (!a || a.id === this.lastAnnounce) return;
      this.lastAnnounce = a.id;
      if (a.tone === 'danger') SFX.stinger(boss.value ? 'boss' : 'danger');
      else if (a.tone === 'zone') SFX.stinger('zone');
      else if (a.tone === 'story') SFX.stinger('story');
      else if (a.tone === 'boon') SFX.stinger('triumph');
    });
    effect(() => {
      const d = dialogue.value;
      if (!d || d.key === this.lastDialogue) return;
      this.lastDialogue = d.key;
      SFX.page();
    });
  }

  set(level: 'on' | 'quiet' | 'off') {
    this.level = level;
    try { localStorage.setItem(KEY, this.level); } catch { /* no storage */ }
    audio.start();
    this.apply();
  }

  /** Cycle the sound setting from the pause menu. */
  cycle() {
    this.level = this.level === 'on' ? 'quiet' : this.level === 'quiet' ? 'off' : 'on';
    try { localStorage.setItem(KEY, this.level); } catch { /* no storage */ }
    audio.start();
    this.apply();
    return this.level;
  }

  private apply() {
    audio.setLevel('master', this.level === 'on' ? 0.85 : this.level === 'quiet' ? 0.35 : 0);
  }

  /** Combat events, panned and attenuated from the survivor's position. */
  events(evs: CombatEvent[], b: Battle | null) {
    if (!audio.ready) return;
    const px = b?.player.x ?? 0, pz = b?.player.z ?? 0;
    const at = (x: number, z: number) => {
      const d = Math.hypot(x - px, z - pz);
      return { pan: Math.max(-0.8, Math.min(0.8, (x - px) / 18)), near: Math.max(0, 1 - d / 32) };
    };
    for (const e of evs) {
      switch (e.t) {
        case 'hit': if (!e.dot) (e.blocked ? SFX.blocked(at(e.x, e.z)) : SFX.hit(e.school, e.crit, at(e.x, e.z))); break;
        case 'kill': SFX.kill(e.family, e.elite, e.boss, at(e.x, e.z)); break;
        case 'playerHit': if (e.dodged) SFX.dodge(); else if (e.blocked) SFX.blocked(); else SFX.hurt(e.amount); break;
        case 'playerHeal': if (e.amount > 8) SFX.heal(); break;
        case 'playerDeath': SFX.death(); break;
        case 'explosion': SFX.explosion(e.power, at(e.x, e.z)); break;
        case 'nova': SFX.nova(e.school); break;
        case 'slash': SFX.swing(at(e.x, e.z)); break;
        case 'muzzle': SFX.shoot(e.school, at(e.x, e.z)); break;
        case 'dash': SFX.dash(); break;
        case 'ability': SFX.bash(); break;
        case 'spawn': SFX.spawn(e.style, at(e.x, e.z)); break;
        case 'levelUp': SFX.levelUp(); break;
        case 'evolve': SFX.evolve(); break;
        case 'pickup':
          if (e.kind === 'ember') { this.xpStreak++; this.xpT = 0.7; SFX.xp(this.xpStreak); }
          else if (e.kind === 'gold') SFX.gold();
          else if (e.kind === 'heal') SFX.heal();
          else if (e.kind === 'chest' || e.kind === 'relic') SFX.loot(true);
          else if (e.kind === 'magnet') SFX.dash();
          break;
        case 'sound':
          if (e.id === 'door') SFX.door();
          break;
      }
    }
  }

  update(dt: number, s: SoundState) {
    this.xpT -= dt;
    if (this.xpT <= 0) this.xpStreak = 0;
    // What kind of moment is this?
    const b = s.battle;
    let hostile = 0;
    if (b && s.mode === 'play') {
      b.enemies.forEach((e) => { if (e.alive && e.disposition === 'hostile' && Math.hypot(e.x - s.px, e.z - s.pz) < 20) hostile++; });
    }
    this.hostilesNear += (hostile - this.hostilesNear) * Math.min(1, dt * (hostile > this.hostilesNear ? 2 : 0.35));
    let mood: Mood = 'silence';
    if (screen.value === 'title' || s.mode === 'title' || s.mode === 'create') mood = 'title';
    else if (boss.value) mood = 'boss';
    else if (this.hostilesNear > 4) mood = 'combat';
    else if (s.zone === 'waystation') mood = s.time === 'night' ? 'night' : 'town';
    else if (s.time === 'night' || s.zone === 'lowford') mood = 'night';
    else mood = 'explore';
    this.music.set(mood);
    this.music.intensity = boss.value ? 1 : Math.min(1, this.hostilesNear / 18);
    const o = overlay.value;
    audio.duckMusic(o === 'dialogue' ? 0.55 : o && o !== 'levelup' ? 0.7 : 1);
    this.music.update(dt);
    this.ambience.set((s.ambience?.(s.px, s.pz) ?? {}) as never);
    this.ambience.update(dt);
  }
}
