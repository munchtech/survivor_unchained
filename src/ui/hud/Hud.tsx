import { useEffect, useRef, useState } from 'preact/hooks';
import { hud, boss, zoneInfo, objectives, prompt, toasts, announcement, subtitle, hint, type HudState, type HudWeapon } from '../store';
import { Glyph, Icon } from '../components/Icon';
import { SCHOOL_UI } from '../palette';
import { Input } from '@/core/input';
import './hud.css';

/* The heads-up display.
 *
 * Arranged so the eye never has to hunt: what can kill you (health, the
 * boss) is where the eye already rests; what you choose (ember, the next
 * level) is at the top edge; what fires by itself (weapons) is a quiet row
 * at the bottom that only lights up when something happens to it; what your
 * hands do (dash, ability) sits under your right thumb. Everything else -
 * the world, the quest, the loot - comes and goes at the edges. */

export function Hud() {
  const h = hud.value;
  return (
    <div class="hud">
      {h && h.combat && <EmberBar h={h} />}
      <BossBar />
      <ZoneCorner />
      <Toasts />
      <Announcement />
      <Subtitle />
      <PromptView />
      <HintCard />
      {h && <Vitals h={h} />}
      {h && h.combat && <Arsenal h={h} />}
      {h && h.combat && <Hands h={h} />}
      {h && h.combat && <Tally h={h} />}
    </div>
  );
}

/* ----------------------------------------------------------------- ember -- */

function EmberBar({ h }: { h: HudState }) {
  const k = Math.min(1, h.ember / Math.max(1, h.emberNext));
  return (
    <div class="ember">
      <div class="ember-medal">
        <span class="ember-lv">{h.level}</span>
      </div>
      <div class="ember-track">
        <div class="ember-fill" style={{ width: `${k * 100}%` }}>
          <div class="ember-head" />
        </div>
        <div class="ember-ticks" />
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- vitals -- */

function Vitals({ h }: { h: HudState }) {
  const k = Math.max(0, Math.min(1, h.hp / h.maxHp));
  const sk = Math.min(1, h.shield / h.maxHp);
  const low = k < 0.35;
  return (
    <div class={`vitals${low ? ' low' : ''}`}>
      {h.statuses.length > 0 && (
        <div class="statuses">
          {h.statuses.map((s) => (
            <div key={s.id} class={`status ${s.tone}`} title={s.label}>
              <Glyph k={s.glyph} size={15} />
              {s.left !== undefined && <span>{Math.ceil(s.left)}</span>}
            </div>
          ))}
        </div>
      )}
      <div class="hp">
        <div class="hp-heart"><Glyph k="heart" size={18} color="#ffb0a8" /></div>
        <div class="hp-bar">
          <div class="hp-trail" style={{ width: `${k * 100}%` }} />
          <div class="hp-fill" style={{ width: `${k * 100}%` }}>
            <div class="hp-sheen" />
          </div>
          {sk > 0 && <div class="hp-shield" style={{ width: `${Math.min(1, sk) * 100}%` }} />}
          <div class="hp-notches" />
          <div class="hp-text">{Math.ceil(h.hp)}<span>{'\u2009/\u2009'}{Math.round(h.maxHp)}</span></div>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- arsenal -- */

function Arsenal({ h }: { h: HudState }) {
  const slots: Array<HudWeapon | null> = [...h.weapons];
  while (slots.length < 6) slots.push(null);
  return (
    <div class="arsenal">
      {h.boons.length > 0 && (
        <div class="boons">
          {h.boons.map((b) => (
            <div key={b.id} class={`boon rb-${rarityIndex(b.rarity)}${b.synergy ? ' syn' : ''}`} title={b.name}>
              <Glyph k={b.glyph} size={17} />
              {b.max > 1 && <span class="boon-rank">{b.rank}</span>}
            </div>
          ))}
        </div>
      )}
      <div class="weapons">
        {slots.map((w, i) => (w ? <WeaponSlot key={w.id} w={w} /> : <div key={`e${i}`} class="wslot empty" />))}
      </div>
    </div>
  );
}

function WeaponSlot({ w }: { w: HudWeapon }) {
  // A pulse on each firing, restarted by re-keying the flash element.
  const prev = useRef(w.ready);
  const [pulse, setPulse] = useState(0);
  useEffect(() => {
    if (w.ready < prev.current - 0.4) setPulse((p) => p + 1);
    prev.current = w.ready;
  }, [w.ready]);
  const color = SCHOOL_UI[w.school];
  const sweep = w.ready < 0.98 ? `conic-gradient(from 0deg, transparent ${w.ready * 360}deg, rgba(4,3,8,0.62) 0)` : 'none';
  return (
    <div class={`wslot${w.evolved ? ' evolved' : ''}${w.canEvolve ? ' can-evolve' : ''}`} style={{ '--sc': color }} title={w.name}>
      <div class="wslot-art">
        <Glyph k={w.glyph} size={30} color={color} glow={w.ready >= 0.98 ? color : undefined} />
      </div>
      <div class="wslot-sweep" style={{ background: sweep }} />
      {pulse > 0 && <div key={pulse} class="wslot-flash" />}
      <div class="wslot-pips">
        {Array.from({ length: w.maxRank }, (_, i) => <i key={i} class={i < w.rank ? 'on' : ''} />)}
      </div>
      {w.evolved && <div class="wslot-star"><Glyph k="arcane" size={11} color="#ffe2a0" /></div>}
    </div>
  );
}

function rarityIndex(r: string) {
  return ({ common: 0, uncommon: 1, rare: 2, epic: 3, legendary: 4 } as Record<string, number>)[r] ?? 0;
}

/* ----------------------------------------------------------------- hands -- */

function Hands({ h }: { h: HudState }) {
  const a = h.ability;
  const readyPrev = useRef(a?.ready ?? 1);
  const [pulse, setPulse] = useState(0);
  useEffect(() => {
    if (a && a.ready >= 1 && readyPrev.current < 1) setPulse((p) => p + 1);
    readyPrev.current = a?.ready ?? 1;
  }, [a?.ready]);
  return (
    <div class="hands">
      <div class="hand">
      <div class="dash">
        <div class="dash-pips">
          {Array.from({ length: h.dash.max }, (_, i) => (
            <div key={i} class={`dash-pip${i < h.dash.charges ? ' on' : ''}`}>
              {i === h.dash.charges && <div class="dash-charge" style={{ height: `${h.dash.recharge * 100}%` }} />}
            </div>
          ))}
        </div>
      </div>
        <div class="hand-key"><span class="key">{Input.keyLabel('dash')}</span> Dash</div>
      </div>
      {h.quick && (
        <div class="hand">
          <div class="quick">
            <div class="quick-art"><Icon k={h.quick.icon} size={40} /></div>
            <span class="quick-qty">{h.quick.qty}</span>
          </div>
          <div class="hand-key"><span class="key">{Input.keyLabel('ultimate')}</span> {h.quick.name}</div>
        </div>
      )}
      {a && (
        <div class="hand">
        <div class={`ability${a.ready >= 1 ? ' ready' : ''}${a.active ? ' active' : ''}`} title={a.name}>
          <div class="ability-ring" style={{ background: `conic-gradient(var(--gold) ${a.ready * 360}deg, rgba(255,255,255,0.06) 0)` }} />
          <div class="ability-face">
            <Glyph k={a.glyph} size={34} color={a.ready >= 1 ? '#ffe6b0' : '#8a7f70'} glow={a.ready >= 1 ? 'rgba(255,170,80,0.8)' : undefined} />
            {a.ready < 1 && <span class="ability-cd">{a.left >= 1 ? Math.ceil(a.left) : a.left.toFixed(1)}</span>}
          </div>
          {pulse > 0 && <div key={pulse} class="ability-flash" />}
        </div>
          <div class="hand-key"><span class="key">{Input.keyLabel('ability')}</span> {a.name}</div>
        </div>
      )}
    </div>
  );
}

/* ----------------------------------------------------------------- tally -- */

function Tally({ h }: { h: HudState }) {
  const m = Math.floor(h.time / 60), s = Math.floor(h.time % 60);
  return (
    <div class="tally">
      <div class="tally-time">{m}:{String(s).padStart(2, '0')}</div>
      <div class="tally-row">
        <span><Glyph k="skull" size={14} color="#cfc3ad" /> {h.kills}</span>
        <span class="gold"><Glyph k="coin" size={14} color="#f3d9a0" /> {h.gold}</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ boss -- */

function BossBar() {
  const b = boss.value;
  if (!b) return null;
  const k = Math.max(0, b.hp / b.maxHp);
  return (
    <div class="bossbar rise-in">
      <div class="boss-name">
        <span class="boss-orn" />
        <div>
          <div class="boss-title">{b.name}</div>
          {b.title && <div class="boss-sub">{b.title}</div>}
        </div>
        <span class="boss-orn r" />
      </div>
      <div class={`boss-track${b.shielded ? ' shielded' : ''}`}>
        <div class="boss-trail" style={{ width: `${k * 100}%` }} />
        <div class="boss-fill" style={{ width: `${k * 100}%` }} />
        {(b.phases ?? []).map((p) => <div key={p} class="boss-phase" style={{ left: `${p * 100}%` }} />)}
      </div>
      {b.channel && (
        <div class="boss-channel">
          <div class="boss-channel-fill" style={{ width: `${b.channel.progress * 100}%` }} />
          <span>{b.channel.label}</span>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------ zone & quests -- */

const TIME_GLYPH = { dawn: 'sun', day: 'sun', dusk: 'sun', night: 'moon' } as const;

function ZoneCorner() {
  const z = zoneInfo.value;
  const obs = objectives.value;
  if (!z && !obs.length) return null;
  return (
    <div class="corner">
      {z && (
        <div class="zone">
          <div class="zone-name">{z.name}</div>
          <div class="zone-sub">
            <Glyph k={TIME_GLYPH[z.time]} size={13} color={z.time === 'night' ? '#b8ccff' : '#ffd890'} />
            <span>{z.time[0].toUpperCase() + z.time.slice(1)}</span>
            <span class="dot">·</span>
            <span>Day {z.day}</span>
            {z.region && <><span class="dot">·</span><span>{z.region}</span></>}
          </div>
        </div>
      )}
      {obs.map((o) => (
        <div key={o.id} class={`objective ${o.tone ?? 'main'}`}>
          <div class="obj-title"><i class="obj-mark" />{o.title}</div>
          {o.steps.map((s, i) => (
            <div key={i} class={`obj-step${s.done ? ' done' : ''}${s.optional ? ' opt' : ''}`}>
              <i class="obj-box" />
              <span>{s.text}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- toasts -- */

const TOAST_GLYPH: Record<string, string> = {
  quest: 'quest', world: 'eye', relation: 'talk', warning: 'skull', lore: 'scroll', level: 'arcane', discovery: 'arcane', gold: 'coin', loot: 'hand',
};

function Toasts() {
  const list = toasts.value;
  return (
    <div class="toasts">
      {list.map((t) => (
        <div key={t.id} class={`toast ${t.kind}${t.rarity !== undefined ? ` rb-${t.rarity}` : ''}`} style={{ animationDuration: `${t.life}s` }}>
          <div class="toast-icon">{t.icon ? <Icon k={t.icon} size={30} /> : <Glyph k={TOAST_GLYPH[t.kind] ?? 'arcane'} size={18} />}</div>
          <div class="toast-body">
            <div class={`toast-text${t.rarity !== undefined ? ` rarity-${t.rarity}` : ''}`}>{t.text}</div>
            {t.sub && <div class="toast-sub">{t.sub}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------- announcement -- */

function Announcement() {
  const a = announcement.value;
  if (!a) return null;
  return (
    <div key={a.id} class={`announce ${a.tone}${a.title.length > 30 ? ' xlong' : a.title.length > 20 ? ' long' : ''}`} style={{ animationDuration: `${a.life}s` }}>
      {a.kicker && <div class="announce-kicker">{a.kicker}</div>}
      <div class="announce-rule" />
      <div class="announce-title">{a.title}</div>
      {a.subtitle && <div class="announce-sub">{a.subtitle}</div>}
      <div class="announce-rule" />
    </div>
  );
}

function Subtitle() {
  const s = subtitle.value;
  if (!s) return null;
  return (
    <div key={s.id} class="subtitle fade-in">
      {s.speaker && <span class="sub-speaker">{s.speaker}</span>}
      <span class="sub-text">{s.text}</span>
    </div>
  );
}

function PromptView() {
  const p = prompt.value;
  if (!p) return null;
  return (
    <div class={`prompt${p.locked ? ' locked' : ''}`}>
      <span class="key big">{p.key}</span>
      <span class="prompt-verb">{p.verb}</span>
      <span class="prompt-target">{p.target}</span>
      {(p.hint || p.locked) && <span class="prompt-hint">{p.locked ?? p.hint}</span>}
    </div>
  );
}

function HintCard() {
  const t = hint.value;
  if (!t) return null;
  return (
    <div key={t.id} class="hint rise-in">
      <div class="hint-head"><Glyph k="scroll" size={15} /> {t.title}</div>
      <div class="hint-text">{t.text}</div>
      {t.keys && t.keys.length > 0 && <div class="hint-keys">{t.keys.map((k) => <span key={k} class="key">{k}</span>)}</div>}
    </div>
  );
}
