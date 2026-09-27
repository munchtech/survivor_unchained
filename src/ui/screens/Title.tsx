import { useEffect, useState } from 'preact/hooks';
import { slots, type SlotView } from '../store';
import { actions } from '@/game/actions';
import { Input } from '@/core/input';
import { ARCHETYPES } from '@/content/archetypes';
import { Glyph } from '../components/Icon';
import './title.css';

/* The title: a fire on the Low Ford road, someone sitting by it, and the
 * name of the game carved over the dark. The menu is short on purpose. */

const ZONE_NAMES: Record<string, string> = { lowford: 'The Low Ford Road', waystation: 'The Waystation', verge: 'Thornhollow Verge' };

function ago(t: number) {
  const s = (Date.now() - t) / 1000;
  if (s < 90) return 'just now';
  if (s < 3600) return `${Math.round(s / 60)} minutes ago`;
  if (s < 86400) return `${Math.round(s / 3600)} hours ago`;
  return `${Math.round(s / 86400)} days ago`;
}

export function Title() {
  const list = slots.value;
  const latest = [...list].sort((a, b) => b.savedAt - a.savedAt)[0] as SlotView | undefined;
  const [panel, setPanel] = useState<'none' | 'load' | 'settings' | 'credits'>('none');
  const [quality, setQuality] = useState(() => actions.quality());
  const [sound, setSound] = useState(() => actions.soundLevel());
  const items: Array<{ id: string; label: string; sub?: string; act: () => void; primary?: boolean }> = [];
  if (latest) items.push({ id: 'continue', label: 'Continue', sub: `${latest.name} · ${ARCHETYPES[latest.archetype as keyof typeof ARCHETYPES]?.name ?? ''} ${latest.level} · Day ${latest.day}`, act: () => actions.continueJourney(latest.slot), primary: true });
  items.push({ id: 'new', label: 'New Journey', act: () => actions.newJourney(), primary: !latest });
  if (list.length) items.push({ id: 'load', label: 'Journeys', act: () => setPanel(panel === 'load' ? 'none' : 'load') });
  items.push({ id: 'settings', label: 'Settings', act: () => setPanel(panel === 'settings' ? 'none' : 'settings') });
  items.push({ id: 'credits', label: 'Credits', act: () => setPanel(panel === 'credits' ? 'none' : 'credits') });
  const [focus, setFocus] = useState(0);

  useEffect(() => Input.on((a) => {
    if (a === 'up') setFocus((f) => (f + items.length - 1) % items.length);
    else if (a === 'down') setFocus((f) => (f + 1) % items.length);
    else if (a === 'confirm') items[focus]?.act();
    else if (a === 'cancel') setPanel('none');
    else return;
    return true;
  }), [focus, items.length, panel]);

  return (
    <div class="title-screen">
      <div class="title-shade" />
      <div class="title-brand">
        <div class="brand-kicker">A tale of the Ember Watch</div>
        <h1 class="brand">
          <span class="brand-1">Survivor</span>
          <span class="brand-2">Unchained</span>
        </h1>
        <div class="brand-rule"><i /></div>
        <div class="brand-tag">The run ends. The story doesn't.</div>
      </div>
      <nav class="title-menu">
        {items.map((it, i) => (
          <button key={it.id} class={`tm-item${it.primary ? ' primary' : ''}${focus === i ? ' focus' : ''}`}
            onMouseEnter={() => setFocus(i)} onClick={it.act} style={{ animationDelay: `${300 + i * 90}ms` }}>
            <span class="tm-mark" />
            <span class="tm-label">{it.label}</span>
            {it.sub && <span class="tm-sub">{it.sub}</span>}
          </button>
        ))}
      </nav>
      {panel === 'load' && (
        <div class="title-panel panel fade-in">
          <div class="tp-head title-cap">Journeys</div>
          {list.map((s) => (
            <div key={s.slot} class={`slot${s.alive ? '' : ' fallen'}`}>
              <div class="slot-emblem"><Glyph k={s.archetype === 'warden' ? 'shield' : s.archetype === 'reaver' ? 'axe' : s.archetype === 'arcanist' ? 'staff' : 'bow'} size={22} /></div>
              <div class="slot-body">
                <div class="slot-name">{s.name}</div>
                <div class="slot-sub">{ARCHETYPES[s.archetype as keyof typeof ARCHETYPES]?.name} {s.level} · Day {s.day} · {ZONE_NAMES[s.zone] ?? s.zone}</div>
                <div class="slot-when">{s.alive ? `Saved ${ago(s.savedAt)}` : 'Fallen'}</div>
              </div>
              <button class="btn small primary" onClick={() => actions.continueJourney(s.slot)}>Resume</button>
              <button class="btn small" title="Forget this journey" onClick={() => { if (confirm(`Forget ${s.name}'s journey? This cannot be undone.`)) actions.deleteSlot(s.slot); }}>✕</button>
            </div>
          ))}
        </div>
      )}
      {panel === 'settings' && (
        <div class="title-panel panel fade-in">
          <div class="tp-head title-cap">Settings</div>
          <div class="tp-row">
            <span>Picture</span>
            <div class="seg">
              {(['low', 'medium', 'high'] as const).map((q) => <button key={q} class={`btn small${quality === q ? ' on' : ''}`} onClick={() => { actions.setQuality(q); setQuality(q); }}>{q}</button>)}
            </div>
          </div>
          <div class="tp-row">
            <span>Sound</span>
            <div class="seg">
              {(['on', 'quiet', 'off'] as const).map((l) => <button key={l} class={`btn small${sound === l ? ' on' : ''}`} onClick={() => { actions.setSound(l); setSound(l); }}>{l}</button>)}
            </div>
          </div>
          <div class="tp-note">Lower settings trade shadow detail, grass and ambient occlusion for speed.</div>
        </div>
      )}
      {panel === 'credits' && (
        <div class="title-panel panel fade-in credits">
          <div class="tp-head title-cap">Credits</div>
          <p>Characters, creatures and props: <b>KayKit</b> by Kay Lousberg (CC0).</p>
          <p>World, lore and combat roots: <b>The Ember Watch</b>.</p>
          <p>Typefaces: Cinzel, Alegreya, Alegreya Sans (OFL).</p>
          <p>Music, ambience and sound: made in code, played live.</p>
          <p>Built with Three.js, postprocessing, N8AO and Preact.</p>
        </div>
      )}
      <div class="title-foot">Beta — the first chapter</div>
    </div>
  );
}
