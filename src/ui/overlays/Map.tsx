import { useEffect, useRef, useState } from 'preact/hooks';
import { mapView } from '../store';
import { actions } from '@/game/actions';
import { Glyph } from '../components/Icon';
import './map.css';

/* The map: the zone as the survivor has walked it.
 *
 * The drawing underneath is made from the zone itself; the fog is plain
 * paper where you have not been; places are named only once you have seen
 * them (exits and what the journal already told you are always there). The
 * wheel zooms, a drag pans, and M or Escape puts it away. */

const GLYPH: Record<string, string> = { quest: 'quest', turn: 'quest', danger: 'skull', mystery: 'eye', exit: 'next', place: 'map', person: 'talk' };

export function WorldMap() {
  const v = mapView.value;
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  useEffect(() => { setZoom(1); setPan({ x: 0, y: 0 }); }, [v?.zone]);
  if (!v) return null;
  const pct = (w: number) => `${(w / v.extent + 0.5) * 100}%`;
  const seen = (x: number, z: number) => {
    const i = Math.floor((x / v.extent + 0.5) * v.n), j = Math.floor((z / v.extent + 0.5) * v.n);
    return i >= 0 && j >= 0 && i < v.n && j < v.n && v.seen[j * v.n + i] === '1';
  };
  const marks = v.marks.filter((m) => m.kind === 'exit' || m.kind === 'quest' || seen(m.x, m.z));
  const onWheel = (e: WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(1, Math.min(3.5, z * (e.deltaY < 0 ? 1.18 : 1 / 1.18))));
  };
  const onDown = (e: PointerEvent) => { drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y }; (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); };
  const onMove = (e: PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    setPan({ x: d.px + (e.clientX - d.x) / zoom, y: d.py + (e.clientY - d.y) / zoom });
  };
  const onUp = () => { drag.current = null; };
  const facing = Math.PI - v.player.facing;
  return (
    <div class="map-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="map-sheet rise-in">
        <div class="map-head">
          <div class="map-title">{v.name}</div>
          {v.region && <div class="map-region">{v.region}</div>}
        </div>
        <div class="map-frame" onWheel={onWheel} onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}>
          <div class="map-world" style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)` }}>
            <img class="map-base" src={v.image} draggable={false} />
            <img class="map-fog" src={v.fog} draggable={false} />
            {marks.map((m) => (
              <div key={`${m.kind}:${m.label}`} class={`map-mark k-${m.kind}`} style={{ left: pct(m.x), top: pct(m.z), transform: `translate(-50%, -50%) scale(${1 / zoom})` }}>
                <span class="map-pin"><Glyph k={GLYPH[m.kind] ?? 'map'} size={m.kind === 'place' ? 11 : 14} /></span>
                <span class="map-label">{m.label}</span>
              </div>
            ))}
            {v.corpse && (
              <div class="map-mark k-corpse" style={{ left: pct(v.corpse.x), top: pct(v.corpse.z), transform: `translate(-50%, -50%) scale(${1 / zoom})` }}>
                <span class="map-pin"><Glyph k="skull" size={14} /></span>
                <span class="map-label">{v.corpse.label}</span>
              </div>
            )}
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
