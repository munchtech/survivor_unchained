import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'preact/hooks';
import { mapView } from '../store';
import { actions } from '@/game/actions';
import { Glyph } from '../components/Icon';
import './map.css';

/* The map: the zone as the survivor has walked it.
 *
 * The drawing underneath is made from the zone itself; the fog is plain
 * paper where you have not been; places are named only once you have seen
 * them (exits and what the journal already told you are always there). The
 * wheel zooms, a drag pans, and M or Escape puts it away. Labels find room
 * for themselves: each tries below, above, right and left of its pin, the
 * most important first, and one with nowhere to go waits for a closer zoom
 * (its name still shows under the cursor). */

const GLYPH: Record<string, string> = { quest: 'quest', turn: 'quest', danger: 'skull', mystery: 'eye', exit: 'next', place: 'map', person: 'talk' };
const RANK: Record<string, number> = { quest: 0, turn: 1, corpse: 2, danger: 3, mystery: 4, exit: 5, person: 6, place: 7 };
const PIN_R: Record<string, number> = { person: 8, place: 0 };

type Side = 'below' | 'above' | 'right' | 'left' | 'center' | 'none';
interface Box { x0: number; y0: number; x1: number; y1: number }
const overlap = (a: Box, b: Box) => Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)) * Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));

/** Where each label goes, in screen pixels at this zoom (pins never move). */
function layout(items: Array<{ key: string; x: number; y: number; kind: string; label: string }>, you: { x: number; y: number }, view: Box): Map<string, Side> {
  const out = new Map<string, Side>();
  // Whatever hangs off the edge of the frame counts as covered.
  const outside = (b: Box) => (b.x1 - b.x0) * (b.y1 - b.y0) - overlap(b, view);
  const taken: Box[] = [{ x0: you.x - 12, y0: you.y - 12, x1: you.x + 12, y1: you.y + 12 }];
  const sorted = [...items].sort((a, b) => (RANK[a.kind] ?? 9) - (RANK[b.kind] ?? 9));
  for (const it of sorted) {
    const r = PIN_R[it.kind] ?? 11;
    if (r) taken.push({ x0: it.x - r, y0: it.y - r, x1: it.x + r, y1: it.y + r });
  }
  for (const it of sorted) {
    const r = PIN_R[it.kind] ?? 11;
    const w = it.label.length * (it.kind === 'person' ? 6.1 : it.kind === 'place' ? 7.4 : 6.8) + (it.kind === 'place' ? 12 : 4), h = it.kind === 'place' ? 19 : 16;
    const opts: Array<[Side, Box]> = r
      ? [
        ['below', { x0: it.x - w / 2, y0: it.y + r + 1, x1: it.x + w / 2, y1: it.y + r + 1 + h }],
        ['above', { x0: it.x - w / 2, y0: it.y - r - 1 - h, x1: it.x + w / 2, y1: it.y - r - 1 }],
        ['right', { x0: it.x + r + 3, y0: it.y - h / 2, x1: it.x + r + 3 + w, y1: it.y + h / 2 }],
        ['left', { x0: it.x - r - 3 - w, y0: it.y - h / 2, x1: it.x - r - 3, y1: it.y + h / 2 }],
      ]
      : [
        ['center', { x0: it.x - w / 2, y0: it.y - h / 2, x1: it.x + w / 2, y1: it.y + h / 2 }],
        ['below', { x0: it.x - w / 2, y0: it.y + 8, x1: it.x + w / 2, y1: it.y + 8 + h }],
        ['above', { x0: it.x - w / 2, y0: it.y - 8 - h, x1: it.x + w / 2, y1: it.y - 8 }],
      ];
    let best: [Side, Box] | null = null, bestO = Infinity;
    for (const o of opts) {
      const ov = taken.reduce((s, t) => s + overlap(o[1], t), 0) + outside(o[1]) * 2;
      if (ov < bestO) { bestO = ov; best = o; }
      if (ov === 0) break;
    }
    if (best && bestO < w * h * 0.12) { out.set(it.key, best[0]); taken.push(best[1]); }
    else out.set(it.key, 'none');
  }
  return out;
}

function labelStyle(side: Side, r: number): string {
  switch (side) {
    case 'below': return `translate(-50%, ${r + 1}px)`;
    case 'above': return `translate(-50%, calc(-100% - ${r + 1}px))`;
    case 'right': return `translate(${r + 3}px, -50%)`;
    case 'left': return `translate(calc(-100% - ${r + 3}px), -50%)`;
    default: return 'translate(-50%, -50%)';
  }
}

export function WorldMap() {
  const v = mapView.value;
  const [zoom, setZoom] = useState(1);
  // The pan is a fraction of the drawing's width, so it needs no measuring.
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [size, setSize] = useState(560);
  const frame = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  useEffect(() => {
    const f = v?.focus;
    setZoom(f?.zoom ?? 1);
    setPan(f && v ? { x: -f.x / v.extent, y: -f.z / v.extent } : { x: 0, y: 0 });
  }, [v?.zone]);
  useLayoutEffect(() => { if (frame.current) setSize(frame.current.clientWidth || 560); }, [v?.zone]);
  const seen = (x: number, z: number) => {
    if (!v) return false;
    const i = Math.floor((x / v.extent + 0.5) * v.n), j = Math.floor((z / v.extent + 0.5) * v.n);
    return i >= 0 && j >= 0 && i < v.n && j < v.n && v.seen[j * v.n + i] === '1';
  };
  const marks = v ? v.marks.filter((m) => m.kind === 'exit' || m.kind === 'quest' || seen(m.x, m.z)) : [];
  const sides = useMemo(() => {
    if (!v) return new Map<string, Side>();
    const px = (w: number) => (w / v.extent) * size * zoom;
    const items = marks.map((m) => ({ key: `${m.kind}:${m.label}`, x: px(m.x), y: px(m.z), kind: m.kind, label: m.label }));
    if (v.corpse) items.push({ key: 'corpse', x: px(v.corpse.x), y: px(v.corpse.z), kind: 'corpse', label: v.corpse.label });
    const half = size / 2, sx = pan.x * size * zoom, sy = pan.y * size * zoom;
    return layout(items, { x: px(v.player.x), y: px(v.player.z) }, { x0: -half - sx + 4, y0: -half - sy + 4, x1: half - sx - 4, y1: half - sy - 4 });
  }, [v, zoom, size, marks.length, pan.x, pan.y]);
  if (!v) return null;
  const pct = (w: number) => `${(w / v.extent + 0.5) * 100}%`;
  const onWheel = (e: WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(1, Math.min(3.5, z * (e.deltaY < 0 ? 1.18 : 1 / 1.18))));
  };
  const onDown = (e: PointerEvent) => { drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y }; (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); };
  const onMove = (e: PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    const s = size * zoom;
    // Keep some of the drawing in the frame, however far it is dragged.
    const lim = 0.5;
    setPan({ x: Math.max(-lim, Math.min(lim, d.px + (e.clientX - d.x) / s)), y: Math.max(-lim, Math.min(lim, d.py + (e.clientY - d.y) / s)) });
  };
  const onUp = () => { drag.current = null; };
  const mark = (key: string, kind: string, x: number, z: number, label: string, glyph: string) => {
    const side = sides.get(key) ?? 'below';
    const r = PIN_R[kind] ?? 11;
    return (
      <div key={key} class={`map-mark k-${kind}`} style={{ left: pct(x), top: pct(z), transform: `scale(${1 / zoom})` }}>
        <span class="map-pin" title={label}><Glyph k={glyph} size={kind === 'place' ? 11 : kind === 'person' ? 11 : 14} /></span>
        {side !== 'none' && <span class="map-label" style={{ transform: labelStyle(side, r) }}>{label}</span>}
      </div>
    );
  };
  const facing = Math.PI - v.player.facing;
  return (
    <div class="map-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="map-sheet rise-in">
        <div class="map-head">
          <div class="map-title">{v.name}</div>
          {v.region && <div class="map-region">{v.region}</div>}
        </div>
        <div class="map-frame" ref={frame} onWheel={onWheel} onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}>
          <div class="map-world" style={{ transform: `scale(${zoom}) translate(${pan.x * 100}%, ${pan.y * 100}%)` }}>
            <img class="map-base" src={v.image} draggable={false} />
            <img class="map-fog" src={v.fog} draggable={false} />
            {marks.map((m) => mark(`${m.kind}:${m.label}`, m.kind, m.x, m.z, m.label, GLYPH[m.kind] ?? 'map'))}
            {v.corpse && mark('corpse', 'corpse', v.corpse.x, v.corpse.z, v.corpse.label, 'skull')}
            <div class="map-you" style={{ left: pct(v.player.x), top: pct(v.player.z), transform: `translate(-50%, -50%) scale(${1 / zoom})` }}>
              <div class="map-you-ring" />
              <svg viewBox="-10 -10 20 20" width="22" height="22" style={{ transform: `rotate(${facing}rad)` }}>
                <path d="M0,-8 L6,6 L0,3 L-6,6 Z" fill="#b8321e" stroke="#2a1408" stroke-width="1.4" stroke-linejoin="round" />
              </svg>
            </div>
          </div>
          <svg class="map-compass" viewBox="-50 -50 100 100" width="84" height="84">
            <circle r="30" fill="none" stroke="#5a3e24" stroke-width="1.2" opacity="0.7" />
            <circle r="24" fill="none" stroke="#5a3e24" stroke-width="0.6" opacity="0.6" />
            <path d="M0,-44 L7,0 L0,6 L-7,0 Z" fill="#6a2a1a" />
            <path d="M0,44 L7,0 L0,-6 L-7,0 Z" fill="#8a6a44" />
            <path d="M-40,0 L0,5 L4,0 L0,-5 Z M40,0 L0,5 L-4,0 L0,-5 Z" fill="#8a6a44" opacity="0.8" />
            <text y="-35" x="10" font-size="11" fill="#3a2414" font-family="Cinzel, serif">N</text>
          </svg>
        </div>
        <div class="map-foot">
          <span><span class="lg k-quest"><Glyph k="quest" size={12} /></span> Someone needs you</span>
          <span><span class="lg k-danger"><Glyph k="skull" size={12} /></span> Hostile</span>
          <span><span class="lg k-mystery"><Glyph k="eye" size={12} /></span> Unexplained</span>
          <span><span class="lg k-exit"><Glyph k="next" size={12} /></span> The way out</span>
          <span class="map-keys"><span class="key">M</span> close · wheel to zoom · drag to move</span>
        </div>
      </div>
    </div>
  );
}
