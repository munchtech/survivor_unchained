import { useEffect, useRef } from 'preact/hooks';
import { creation, type CreationDraft } from '../store';
import { actions } from '@/game/actions';
import { ARCHETYPES, BACKGROUNDS, type ArchetypeId, type BackgroundId } from '@/content/archetypes';
import { ITEMS } from '@/content/items';
import { WEAPONS } from '@/content/weapons';
import { ABILITIES, type AbilityKind } from '@/content/abilities';
import { BOONS, START_BLESSINGS } from '@/content/boons';
import { Glyph, Icon } from '../components/Icon';
import { SCHOOL_UI } from '../palette';
import { SKINS, HAIRS, HAIR_STYLES } from '@/content/looks';
import { Input } from '@/core/input';
import type { CharacterModel } from '@/render/assets';
import './create.css';

/* Making the survivor, by the fire.
 *
 * Four steps, each a question the world will ask again later:
 *   I    Calling   how do you fight?
 *   II   Arms      with what, and what do your hands do?
 *   III  Origin    where are you from - what do you know, who knows you?
 *   IV   Name      who are you?
 * The figure standing beside the fire changes as you choose. The panel on
 * the right says, plainly, what each choice means. */

const STEPS = ['Calling', 'Arms', 'Origin', 'Name'];
const NUMERALS = ['I', 'II', 'III', 'IV'];
const CLASS_GLYPH: Record<ArchetypeId, string> = { warden: 'shield', reaver: 'axe', arcanist: 'staff', stalker: 'bow' };
const BG_GLYPH: Record<BackgroundId, string> = { hunter: 'claw', scholar: 'book', outcast: 'mask', devout: 'sun' };
const KNOW_NAMES: Record<string, string> = { beastlore: 'Beastlore', arcana: 'Arcana', underworld: 'The Underworld', faith: 'The Faith' };
const NAMES = ['Ashe', 'Brannagh', 'Corwen', 'Dace', 'Edda', 'Fen', 'Garrow', 'Hollis', 'Isolde', 'Jessamy', 'Kell', 'Lorne', 'Maren', 'Nolly', 'Orrin', 'Pim', 'Quill', 'Rhosyn', 'Sabre', 'Tamsin', 'Ulla', 'Voss', 'Wren', 'Yarrow'];

function set(patch: Partial<CreationDraft>) {
  const d = creation.value;
  if (d) creation.value = { ...d, ...patch };
}

function chooseArchetype(id: ArchetypeId) {
  const a = ARCHETYPES[id];
  set({ archetype: id, weaponItem: a.weapons[0], ability: a.abilities[0], palette: a.palettes[0].id, model: a.model, headgear: true });
}

export function Create() {
  const d = creation.value;
  if (!d) return null;
  const a = ARCHETYPES[d.archetype];
  const canBegin = d.name.trim().length > 0;
  const begin = () => {
    if (!canBegin) { set({ step: 3 }); return; }
    actions.beginJourney({
      name: d.name.trim(), archetype: d.archetype, background: d.background, palette: d.palette, model: d.model as CharacterModel,
      weaponItem: d.weaponItem, ability: d.ability as AbilityKind, startBoon: d.startBoon, headgear: d.headgear, cloak: d.cloak, skin: d.skin, hair: d.hair,
      sex: d.sex, hairStyle: d.hairStyle, beard: d.beard, figure: d.figure,
    });
  };
  useEffect(() => Input.on((act, e) => {
    if (e && (e.target as HTMLElement)?.tagName === 'INPUT') return;
    if (act === 'tabNext') set({ step: Math.min(3, d.step + 1) });
    else if (act === 'tabPrev') set({ step: Math.max(0, d.step - 1) });
    else if (act === 'cancel') { if (d.step > 0) set({ step: d.step - 1 }); else actions.cancelCreation(); }
    else return;
    return true;
  }), [d.step]);

  return (
    <div class="create">
      <div class="create-shade" />
      <aside class="create-left panel">
        <div class="cl-head">
          <div class="cl-kicker">By the fire on the Low Ford road</div>
          <div class="cl-title title-cap">Who sits here?</div>
        </div>
        <div class="steps">
          {STEPS.map((s, i) => (
            <button key={s} class={`step${d.step === i ? ' on' : ''}${i < d.step ? ' done' : ''}`} onClick={() => set({ step: i })}>
              <span class="step-n">{NUMERALS[i]}</span>
              <span class="step-l">{s}</span>
            </button>
          ))}
        </div>
        <div class="cl-body scroll">
          {d.step === 0 && <Calling d={d} />}
          {d.step === 1 && <Arms d={d} />}
          {d.step === 2 && <Origin d={d} />}
          {d.step === 3 && <NameLook d={d} />}
        </div>
        <div class="cl-foot">
          <button class="btn" onClick={() => (d.step > 0 ? set({ step: d.step - 1 }) : actions.cancelCreation())}>{d.step > 0 ? 'Back' : 'Leave'}</button>
          {d.step < 3
            ? <button class="btn primary" onClick={() => set({ step: d.step + 1 })}>Next: {STEPS[d.step + 1]}</button>
            : <button class={`btn primary begin${canBegin ? '' : ' wait'}`} onClick={begin}>Begin the journey</button>}
        </div>
      </aside>
      <aside class="create-right fade-in" key={d.step}>
        {d.step === 0 && <CallingDetail id={d.archetype} />}
        {d.step === 1 && <ArmsDetail d={d} />}
        {d.step === 2 && <OriginDetail id={d.background} />}
        {d.step === 3 && <Summary d={d} />}
      </aside>
      <div class="create-caption">
        <div class="cc-name">{d.name.trim() || 'Nameless'}</div>
        <div class="cc-sub">{BACKGROUNDS[d.background].name} {a.name}</div>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- steps -- */

function Calling({ d }: { d: CreationDraft }) {
  return (
    <div class="choices">
      {(Object.keys(ARCHETYPES) as ArchetypeId[]).map((id) => {
        const a = ARCHETYPES[id];
        return (
          <button key={id} class={`choice${d.archetype === id ? ' on' : ''}`} onClick={() => chooseArchetype(id)}>
            <div class="choice-emblem"><Glyph k={CLASS_GLYPH[id]} size={26} /></div>
            <div class="choice-body">
              <div class="choice-name">{a.name}</div>
              <div class="choice-tag">{a.tagline}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

function Arms({ d }: { d: CreationDraft }) {
  const a = ARCHETYPES[d.archetype];
  return (
    <div>
      <div class="sub-head">Weapon</div>
      <div class="choices">
        {a.weapons.map((id) => {
          const it = ITEMS[id];
          const w = it.weapon ? WEAPONS[it.weapon.id] : null;
          return (
            <button key={id} class={`choice${d.weaponItem === id ? ' on' : ''}`} onClick={() => set({ weaponItem: id })}>
              <div class="choice-icon"><Icon k={it.icon} size={46} /></div>
              <div class="choice-body">
                <div class="choice-name">{it.name}</div>
                <div class="choice-tag" style={{ color: w ? SCHOOL_UI[w.school] : undefined }}>{w?.name} · {w?.school}</div>
              </div>
            </button>
          );
        })}
      </div>
      <div class="sub-head">Ability</div>
      <div class="choices two">
        {a.abilities.map((id) => {
          const ab = ABILITIES[id];
          return (
            <button key={id} class={`choice tall${d.ability === id ? ' on' : ''}`} onClick={() => set({ ability: id })}>
              <div class="choice-emblem"><Glyph k={ab.icon} size={24} /></div>
              <div class="choice-name">{ab.name}</div>
              <div class="choice-tag">{ab.cooldown} s{ab.interrupts ? ' · breaks channels' : ''}</div>
            </button>
          );
        })}
      </div>
      <div class="sub-head">Starting blessing <span class="sub-note">yours at the start of every expedition</span></div>
      <div class="boon-row">
        {START_BLESSINGS.map((id) => (
          <button key={id} class={`boon-pick${d.startBoon === id ? ' on' : ''}`} onClick={() => set({ startBoon: id })} title={BOONS[id].text}>
            <Glyph k={BOONS[id].icon} size={22} />
            <span>{BOONS[id].name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Origin({ d }: { d: CreationDraft }) {
  return (
    <div class="choices">
      {(Object.keys(BACKGROUNDS) as BackgroundId[]).map((id) => {
        const bg = BACKGROUNDS[id];
        return (
          <button key={id} class={`choice${d.background === id ? ' on' : ''}`} onClick={() => set({ background: id })}>
            <div class="choice-emblem"><Glyph k={BG_GLYPH[id]} size={24} /></div>
            <div class="choice-body">
              <div class="choice-name">{bg.name}</div>
              <div class="choice-tag">{bg.summary}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

const HAIR_NAMES: Record<string, string> = {
  Hair_SimpleParted: 'Parted', Hair_Buzzed: 'Cropped', Hair_Long: 'Long', Hair_Buns: 'Buns', Hair_BuzzedFemale: 'Cropped', none: 'Shorn',
};
const figureWord = (f: number) => f < 0.45 ? 'Slender' : f < 0.95 ? 'Shapely' : f < 1.25 ? 'Full' : 'Buxom';

function NameLook({ d }: { d: CreationDraft }) {
  const a = ARCHETYPES[d.archetype];
  // Hair shows only when nothing covers it.
  const hairHidden = d.archetype === 'stalker' ? d.model === 'rogue_hooded' : d.headgear && d.archetype !== 'reaver';
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  return (
    <div>
      <div class="sub-head">Name</div>
      <div class="name-row">
        <input ref={ref} class="name-input" maxLength={18} placeholder="Your name" value={d.name}
          onInput={(e) => set({ name: (e.target as HTMLInputElement).value.replace(/[^\p{L}\p{M}' -]/gu, '') })} />
        <button class="btn small" title="A name from the road" onClick={() => set({ name: NAMES[Math.floor(Math.random() * NAMES.length)] })}>
          <Glyph k="arcane" size={16} />
        </button>
      </div>
      <div class="sub-head">Body</div>
      <div class="seg">
        {(['male', 'female'] as const).map((x) => (
          <button key={x} class={`btn small${d.sex === x ? ' on' : ''}`} onClick={() => set({ sex: x, hairStyle: HAIR_STYLES[x].includes(d.hairStyle) || d.hairStyle === 'none' ? d.hairStyle : HAIR_STYLES[x][0] })}>{x === 'male' ? 'Man' : 'Woman'}</button>
        ))}
        {d.sex === 'male' && (
          <button class={`btn small${d.beard ? ' on' : ''}`} onClick={() => set({ beard: !d.beard })}>{d.beard ? 'Bearded' : 'Clean-shaven'}</button>
        )}
      </div>
      {d.sex === 'female' && (
        <div class="figure-row">
          <span class="dye-name">Figure</span>
          <input type="range" min="0" max="1.5" step="0.1" value={d.figure} onInput={(e) => set({ figure: Number((e.target as HTMLInputElement).value) })} />
          <span class="dye-name">{figureWord(d.figure)}</span>
        </div>
      )}
      <div class="sub-head">Colours</div>
      <div class="swatches">
        {a.palettes.map((p) => (
          <button key={p.id} class={`swatch${d.palette === p.id ? ' on' : ''}`} onClick={() => set({ palette: p.id })}>
            <i style={{ background: p.ui }} />
            <span>{p.name}</span>
          </button>
        ))}
      </div>
      <div class="sub-head">Skin</div>
      <div class="dyes">
        {SKINS.map((c) => (
          <button key={c.id} title={c.name} class={`dye skin${d.skin === c.id ? ' on' : ''}`} onClick={() => set({ skin: c.id })}>
            <i style={{ background: c.color || '#f6c4a0' }} />
          </button>
        ))}
        <span class="dye-name">{SKINS.find((c) => c.id === d.skin)?.name}</span>
      </div>
      <div class="sub-head">Hair</div>
      <div class={`seg hair-cuts${hairHidden ? ' muted' : ''}`}>
        {[...HAIR_STYLES[d.sex], 'none'].map((h) => (
          <button key={h} class={`btn small${d.hairStyle === h ? ' on' : ''}`} onClick={() => set({ hairStyle: h })}>{HAIR_NAMES[h]}</button>
        ))}
      </div>
      <div class={`dyes${hairHidden ? ' muted' : ''}`}>
        {HAIRS.map((c) => (
          <button key={c.id} title={c.name} class={`dye${d.hair === c.id ? ' on' : ''}${c.id === 'as_is' ? ' calling' : ''}`} onClick={() => set({ hair: c.id })}>
            <i style={c.color ? { background: c.color } : undefined} />
          </button>
        ))}
        <span class="dye-name">{HAIRS.find((c) => c.id === d.hair)?.name}</span>
        {hairHidden && <span class="dye-note">under the hood</span>}
      </div>
      {d.archetype !== 'reaver' && <div class="sub-head">Hood</div>}
      <div class="toggles">
        {a.altModel && (
          <button class={`btn small${d.model === a.altModel ? ' focus' : ''}`} onClick={() => set({ model: d.model === a.model ? a.altModel! : a.model })}>
            {d.model === a.model ? 'Hood up' : 'Hood down'}
          </button>
        )}
        {d.archetype !== 'stalker' && d.archetype !== 'reaver' && (
          <button class={`btn small${d.headgear ? '' : ' focus'}`} onClick={() => set({ headgear: !d.headgear })}>{d.headgear ? 'Hood up' : 'Hood down'}</button>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------- details -- */

function Bar({ label, v, max }: { label: string; v: number; max: number }) {
  return (
    <div class="stat-bar">
      <span>{label}</span>
      <div class="sb-track"><div class="sb-fill" style={{ width: `${Math.min(1, v / max) * 100}%` }} /></div>
    </div>
  );
}

function CallingDetail({ id }: { id: ArchetypeId }) {
  const a = ARCHETYPES[id];
  return (
    <div class="detail">
      <div class="dt-title title-cap">{a.name}</div>
      <div class="dt-tag">{a.tagline}</div>
      <p class="dt-text">{a.description}</p>
      <div class="rule" />
      <Bar label="Health" v={a.base.maxHealth} max={200} />
      <Bar label="Armour" v={a.base.armor + 1} max={7} />
      <Bar label="Speed" v={a.base.moveSpeed - 4} max={2} />
      <Bar label="Precision" v={a.base.critChance} max={0.12} />
      <div class="rule" />
      <div class="dt-line"><b>Weapons</b> {a.weapons.map((w) => ITEMS[w].name).join(' · ')}</div>
      <div class="dt-line"><b>Abilities</b> {a.abilities.map((x) => ABILITIES[x].name).join(' · ')}</div>
    </div>
  );
}

function ArmsDetail({ d }: { d: CreationDraft }) {
  const it = ITEMS[d.weaponItem];
  const w = it.weapon ? WEAPONS[it.weapon.id] : null;
  const ab = ABILITIES[d.ability as AbilityKind];
  return (
    <div class="detail">
      <div class="dt-item">
        <div class="dt-photo"><Icon k={it.icon} size={84} /></div>
        <div>
          <div class="dt-title title-cap">{it.name}</div>
          {w && <div class="dt-tag" style={{ color: SCHOOL_UI[w.school] }}>{w.name} · {w.school}</div>}
        </div>
      </div>
      <p class="dt-text">{it.description}</p>
      {it.lore && <p class="dt-lore">{it.lore}</p>}
      {w && <div class="dt-line"><b>At rank 8</b> {w.evolutions.map((e) => `${e.name} (with ${e.catalysts.map((c) => BOONS[c.boon]?.name ?? c.boon).join(' or ')})`).join(', or ')}</div>}
      <div class="rule" />
      <div class="dt-ab">
        <div class="dt-ab-icon"><Glyph k={ab.icon} size={30} color="#ffe2b0" /></div>
        <div>
          <div class="dt-sub">{ab.name} <span class="key">{Input.keyLabel('ability')}</span></div>
          <p class="dt-text small">{ab.description}</p>
        </div>
      </div>
      <div class="rule" />
      <div class="dt-line"><b>{BOONS[d.startBoon].name}</b> {BOONS[d.startBoon].text}</div>
    </div>
  );
}

function OriginDetail({ id }: { id: BackgroundId }) {
  const bg = BACKGROUNDS[id];
  return (
    <div class="detail">
      <div class="dt-title title-cap">{bg.name}</div>
      <div class="dt-tag">{bg.summary}</div>
      <p class="dt-lore">{bg.story}</p>
      <div class="rule" />
      <div class="dt-line"><b>You know</b> {bg.knowledge.map((k) => KNOW_NAMES[k] ?? k).join(', ')}</div>
      <div class="dt-items">
        {bg.items.map((i) => (
          <div key={i} class="dt-mini">
            <Icon k={ITEMS[i].icon} size={40} />
            <div><div class={`dt-mini-name rarity-${ITEMS[i].rarity}`}>{ITEMS[i].name}</div><div class="dt-mini-text">{ITEMS[i].description}</div></div>
          </div>
        ))}
      </div>
      <div class="rule" />
      <div class="dt-sub">What it opens</div>
      <ul class="dt-opens">{bg.opens.map((o) => <li key={o}>{o}</li>)}</ul>
    </div>
  );
}

function Summary({ d }: { d: CreationDraft }) {
  const a = ARCHETYPES[d.archetype], bg = BACKGROUNDS[d.background];
  return (
    <div class="detail">
      <div class="dt-title title-cap">{d.name.trim() || 'Nameless'}</div>
      <div class="dt-tag">{bg.name} {a.name}</div>
      <p class="dt-lore">{bg.story}</p>
      <div class="rule" />
      <div class="dt-line"><b>Carries</b> {ITEMS[d.weaponItem].name}{bg.items.map((i) => `, ${ITEMS[i].name}`).join('')}</div>
      <div class="dt-line"><b>Hands</b> {ABILITIES[d.ability as AbilityKind].name}</div>
      <div class="dt-line"><b>Blessing</b> {BOONS[d.startBoon].name}</div>
      <div class="dt-line"><b>Knows</b> {bg.knowledge.map((k) => KNOW_NAMES[k] ?? k).join(', ')}</div>
      <div class="rule" />
      <p class="dt-text small">Night is falling on the Low Ford road. The fire is low. What you do from here, the world will remember.</p>
    </div>
  );
}
