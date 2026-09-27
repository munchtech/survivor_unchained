import { glyphFor } from '../glyphs';
import { itemIcon } from '../itemIcons';

/* An icon is a photograph of the thing when there is a thing (items), and
 * an engraved line glyph when there is not (boons, schools, abilities). */

export function Glyph({ k, size = 24, color = 'currentColor', stroke = 1.6, glow }: { k: string; size?: number; color?: string; stroke?: number; glow?: string }) {
  return (
    <svg class="glyph" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} stroke-width={stroke}
      stroke-linecap="round" stroke-linejoin="round" style={glow ? { filter: `drop-shadow(0 0 3px ${glow}) drop-shadow(0 0 8px ${glow})` } : undefined}>
      <path d={glyphFor(k)} />
    </svg>
  );
}

export function Icon({ k, size = 40, color, glow }: { k: string; size?: number; color?: string; glow?: string }) {
  const src = itemIcon(k);
  if (src) return <img class="icon-img" src={src} width={size} height={size} draggable={false} alt="" />;
  return <Glyph k={k} size={Math.round(size * 0.72)} color={color} glow={glow} />;
}
