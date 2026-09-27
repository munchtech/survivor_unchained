import { ITEMS } from '@/content/items';
import { slotFor, type ItemInstance } from '@/rpg/character';
import { Icon } from './Icon';

/* A grid of item slots: the pack, a shop's shelf, the inn's storeroom. */

export function ItemGrid({ items, cols, sel, onSel, onHover, onDouble, price, size = 64 }: {
  items: Array<ItemInstance | null>;
  cols: number;
  sel?: string | null;
  onSel?: (it: ItemInstance) => void;
  onHover?: (it: ItemInstance | null, e?: MouseEvent) => void;
  onDouble?: (it: ItemInstance) => void;
  price?: (it: ItemInstance) => number | null;
  size?: number;
}) {
  return (
    <div class="pack-grid" style={{ gridTemplateColumns: `repeat(${cols}, ${size}px)` }}>
      {items.map((it, i) => {
        const p = it && price ? price(it) : null;
        return (
          <div key={it?.uid ?? `e${i}`} class={`pslot${it ? ` rb-${it.rarity} filled` : ''}${it && sel === it.uid ? ' sel' : ''}${it && price && p === null ? ' refused' : ''}`}
            style={{ width: `${size}px`, height: `${size}px` }}
            onMouseEnter={(e) => onHover?.(it, e)} onMouseLeave={() => onHover?.(null)}
            onClick={() => it && onSel?.(it)} onDblClick={() => it && onDouble?.(it)}>
            {it && <Icon k={ITEMS[it.def].icon} size={Math.round(size * 0.8)} />}
            {it && it.qty > 1 && <span class="pslot-qty">{it.qty}</span>}
            {it && slotFor(ITEMS[it.def]) && <span class="pslot-dot" />}
            {p !== null && p !== undefined && <span class="pslot-price">{p}</span>}
          </div>
        );
      })}
    </div>
  );
}

/** Where a hovered slot is, in zoomed interface pixels. */
export function hoverAt(e: MouseEvent) {
  const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
  const zoom = Number((document.querySelector('.ui-root') as HTMLElement)?.style.zoom || 1);
  return { x: r.right / zoom + 10, y: r.top / zoom };
}
