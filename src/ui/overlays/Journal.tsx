import { useState } from 'preact/hooks';
import { character, worldView, rev } from '../store';
import { actions } from '@/game/actions';
import { QUESTS } from '@/content/quests';
import { NPCS } from '@/content/npcs';
import { ENEMIES } from '@/content/enemies';
import { SYNERGY_PAIRS } from '@/content/discoveries';
import { attitude } from '@/world/logic';
import type { NpcState } from '@/world/state';
import { Glyph } from '../components/Icon';
import './journal.css';

/* The journal: what you are doing, who you know, what you have done, and
 * what you have learned. Written like a book because it is one - the
 * survivor's own - and every line in it is the world's memory, read back. */

type Tab = 'quests' | 'people' | 'deeds' | 'codex';

export function Journal() {
  void rev.value;
  const [tab, setTab] = useState<Tab>('quests');
  const ch = character.value, w = worldView.value;
  if (!ch || !w) return null;
  return (
    <div class="inv-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="journal rise-in">
        <div class="jr-tabs">
          {(['quests', 'people', 'deeds', 'codex'] as Tab[]).map((t) => (
            <button key={t} class={`jr-tab${tab === t ? ' on' : ''}`} onClick={() => setTab(t)}>
              {{ quests: 'Journal', people: 'People', deeds: 'Deeds', codex: 'Codex' }[t]}
            </button>
          ))}
          <button class="btn small jr-close" onClick={() => actions.closeOverlay()}><span class="key">J</span> Close</button>
        </div>
        <div class="jr-book parchment">
          {tab === 'quests' && <Quests />}
          {tab === 'people' && <People />}
          {tab === 'deeds' && <Deeds />}
          {tab === 'codex' && <Codex />}
        </div>
      </div>
    </div>
  );
}

function Quests() {
  const w = worldView.value!;
  const list = Object.values(w.quests).filter((q) => q.status !== 'unknown' && QUESTS[q.id]);
  const [sel, setSel] = useState<string | null>(list.find((q) => q.status === 'active')?.id ?? list[0]?.id ?? null);
  const q = sel ? w.quests[sel] : null;
  const def = q ? QUESTS[q.id] : null;
  return (
    <div class="jr-two">
      <div class="jr-list">
        {(['active', 'resolved', 'failed'] as const).map((st) => {
          const qs = list.filter((x) => (st === 'active' ? x.status === 'active' : st === 'resolved' ? x.status === 'resolved' : x.status === 'failed' || x.status === 'abandoned'));
          if (!qs.length) return null;
          return (
            <div key={st}>
              <div class="jr-group">{{ active: 'Under way', resolved: 'Done', failed: 'Lost' }[st]}</div>
              {qs.map((x) => (
                <button key={x.id} class={`jr-item${sel === x.id ? ' on' : ''}${QUESTS[x.id].mystery ? ' mystery' : ''}`} onClick={() => setSel(x.id)}>
                  <Glyph k={QUESTS[x.id].mystery ? 'eye' : 'quest'} size={14} /> {QUESTS[x.id].name}
                </button>
              ))}
            </div>
          );
        })}
        {!list.length && <p class="jr-empty">Nothing written yet.</p>}
      </div>
      <div class="jr-page">
        {q && def ? (
          <>
            <h2>{def.name}</h2>
            <p class="jr-summary">{def.summary}</p>
            <div class="jr-rule" />
            {q.entries.map((e, i) => <p key={e} class="jr-entry" style={{ animationDelay: `${i * 40}ms` }}>{def.entries[e] ?? e}</p>)}
            {q.outcome && def.outcomes?.[q.outcome] && <p class="jr-outcome">{def.outcomes[q.outcome]}</p>}
            {q.startedDay && <div class="jr-meta">Begun on day {q.startedDay}</div>}
          </>
        ) : <p class="jr-empty">Choose an entry.</p>}
      </div>
    </div>
  );
}

function feel(v: number) {
  const k = (v + 100) / 200;
  return <div class="feel"><div class="feel-mid" /><div class="feel-dot" style={{ left: `${k * 100}%` }} /></div>;
}

function People() {
  const w = worldView.value!;
  const met = Object.values(NPCS).filter((d) => w.npcs[d.id]?.flags.met);
  if (!met.length) return <p class="jr-empty">You have not met anyone yet.</p>;
  return (
    <div class="jr-people">
      {met.map((d) => {
        const s = w.npcs[d.id] as NpcState;
        const heard = s.memories.map((m) => w.history.find((h) => h.id === m)).filter(Boolean);
        return (
          <div key={d.id} class="person">
            <div class="person-head">
              <div class="person-name">{d.name}</div>
              <div class="person-role">{d.role}{s.alive ? '' : ' · dead'}</div>
              <div class="person-att">{attitude(s)}</div>
            </div>
            <div class="person-axes">
              <span>Trust</span>{feel(s.trust)}
              <span>Warmth</span>{feel(s.affection)}
              <span>Respect</span>{feel(s.respect)}
              <span>Fear</span>{feel(s.fear)}
            </div>
            {heard.length > 0 && <div class="person-heard">Knows that you {heard.map((h) => h!.text).join('; ')}.</div>}
          </div>
        );
      })}
    </div>
  );
}

function Deeds() {
  const w = worldView.value!, ch = character.value!;
  return (
    <div class="jr-deeds">
      <h2>What the world remembers</h2>
      {w.history.length === 0 && <p class="jr-empty">Nothing, yet. Give it time.</p>}
      {w.history.map((h) => {
        const knowers = Object.values(w.npcs).filter((n) => n.memories.includes(h.id)).map((n) => NPCS[n.id]?.name).filter(Boolean);
        return (
          <div key={h.id} class="deed">
            <div class="deed-day">Day {h.day}</div>
            <div class="deed-text">You {h.text}.</div>
            <div class="deed-who">{knowers.length ? `Known to ${knowers.join(', ')}` : h.spread > 0 ? 'Word has not got round yet.' : 'Nobody saw.'}</div>
          </div>
        );
      })}
      <div class="jr-rule" />
      <div class="jr-stats">
        <span>Days on the road <b>{w.day}</b></span>
        <span>Creatures slain <b>{ch.stats.kills}</b></span>
        <span>Falls <b>{ch.stats.deaths}</b></span>
        <span>Gold earned <b>{ch.stats.goldEarned}</b></span>
      </div>
    </div>
  );
}

function Codex() {
  const w = worldView.value!;
  const seen = Object.entries(w.bestiary).filter(([id]) => ENEMIES[id]);
  return (
    <div class="jr-two">
      <div class="jr-codex">
        <h2>Bestiary</h2>
        {seen.length === 0 && <p class="jr-empty">Nothing put down yet.</p>}
        {seen.map(([id, n]) => (
          <div key={id} class="beast">
            <div class="beast-name">{ENEMIES[id].name} <span>× {n}</span></div>
            <div class="beast-note">{ENEMIES[id].note}</div>
          </div>
        ))}
      </div>
      <div class="jr-codex">
        <h2>Discoveries</h2>
        {SYNERGY_PAIRS.map((d) => {
          const found = w.codex.includes(d.id);
          return (
            <div key={d.id} class={`beast${found ? '' : ' unknown'}`}>
              <div class="beast-name">{found ? d.name : '???'}</div>
              <div class="beast-note">{found ? d.description : d.hint}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
