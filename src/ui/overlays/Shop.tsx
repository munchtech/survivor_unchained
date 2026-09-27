import { useState } from 'preact/hooks';
import { character, worldView, shopView, rev } from '../store';
import { actions } from '@/game/actions';
import { NPCS } from '@/content/npcs';
import type { ItemInstance } from '@/rpg/character';
import { Glyph } from '../components/Icon';
import { ItemCard } from '../components/ItemCard';
import { ItemGrid, hoverAt } from '../components/ItemGrid';
import './inventory.css';

/* Buying and selling. The seller's shelf on the left, your pack on the
 * right, the price on every tag. What they will not buy is dimmed. */

export function Shop() {
  void rev.value;
  const sv = shopView.value, ch = character.value, w = worldView.value;
  const [sel, setSel] = useState<{ uid: string; side: 'buy' | 'sell' } | null>(null);
  const [hover, setHover] = useState<{ it: ItemInstance; x: number; y: number } | null>(null);
  if (!sv || !ch || !w) return null;
  const stock = w.shops[sv.id]?.stock ?? [];
  const shelf: Array<ItemInstance | null> = [...stock];
  while (shelf.length < 20) shelf.push(null);
  const selected = sel ? (sel.side === 'buy' ? stock.find((x) => x.uid === sel.uid) : ch.pack.find((x) => x?.uid === sel.uid)) ?? null : null;
  const price = selected && sel ? actions.priceOf(selected.uid, sel.side) : null;
  const who = NPCS[sv.npc];
  const close = () => { shopView.value = null; actions.closeOverlay(); };
  const onHover = (it: ItemInstance | null, e?: MouseEvent) => setHover(it && e ? { it, ...hoverAt(e) } : null);
  return (
    <div class="inv-overlay">
      <div class="scrim fade-in" onClick={close} />
      <div class="inv panel rise-in shop">
        <div class="inv-head">
          <div>
            <div class="title-cap">{sv.name}</div>
            {who && <div class="shop-who">{who.name}, {who.role.toLowerCase()}</div>}
          </div>
          <button class="btn small" onClick={close}><span class="key">Esc</span> Leave</button>
        </div>
        <div class="shop-body">
          <section>
            <div class="sub-label">For sale</div>
            <ItemGrid items={shelf} cols={5} sel={sel?.side === 'buy' ? sel.uid : null}
              onSel={(it) => setSel({ uid: it.uid, side: 'buy' })} onDouble={(it) => actions.buy(sv.id, it.uid)}
              onHover={onHover} price={(it) => actions.priceOf(it.uid, 'buy')} />
          </section>
          <section class="inv-detail">
            {selected && sel ? (
              <ItemCard it={selected} ch={ch} compare>
                <div class="ic-actions">
                  {sel.side === 'buy' ? (
                    <button class="btn small primary" disabled={price === null || ch.gold < price} onClick={() => actions.buy(sv.id, selected.uid)}>
                      Buy · <Glyph k="coin" size={12} /> {price}
                    </button>
                  ) : price !== null ? (
                    <button class="btn small primary" onClick={() => { actions.sell(selected.uid); setSel(null); }}>Sell · <Glyph k="coin" size={12} /> {price}</button>
                  ) : <span class="refuse">They will not buy this.</span>}
                </div>
              </ItemCard>
            ) : (
              <div class="inv-empty"><Glyph k="coin" size={28} /><p>Choose something on the shelf, or in your pack.</p><p class="dim">Prices soften for people who like you.</p></div>
            )}
          </section>
          <section>
            <div class="sub-label">Your pack</div>
            <ItemGrid items={ch.pack} cols={6} size={56} sel={sel?.side === 'sell' ? sel.uid : null}
              onSel={(it) => setSel({ uid: it.uid, side: 'sell' })} onDouble={(it) => actions.sell(it.uid)}
              onHover={onHover} price={(it) => actions.priceOf(it.uid, 'sell')} />
            <div class="pack-foot"><span class="gold"><Glyph k="coin" size={16} color="#f3d9a0" /> {ch.gold}</span><span class="pack-hint">Double-click to buy or sell</span></div>
          </section>
        </div>
      </div>
      {hover && hover.it.uid !== sel?.uid && <div class="inv-tip" style={{ left: `${hover.x}px`, top: `${hover.y}px` }}><ItemCard it={hover.it} ch={ch} compare /></div>}
    </div>
  );
}

export function Stash() {
  void rev.value;
  const ch = character.value, w = worldView.value;
  const [hover, setHover] = useState<{ it: ItemInstance; x: number; y: number } | null>(null);
  if (!ch || !w) return null;
  const onHover = (it: ItemInstance | null, e?: MouseEvent) => setHover(it && e ? { it, ...hoverAt(e) } : null);
  return (
    <div class="inv-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="inv panel rise-in shop">
        <div class="inv-head">
          <div><div class="title-cap">Rook's Storeroom</div><div class="shop-who">Kept safe, whatever becomes of you.</div></div>
          <button class="btn small" onClick={() => actions.closeOverlay()}><span class="key">Esc</span> Close</button>
        </div>
        <div class="stash-body">
          <section>
            <div class="sub-label">Stored</div>
            <ItemGrid items={w.stash} cols={8} size={56} onSel={(it) => actions.unstash(it.uid)} onHover={onHover} />
          </section>
          <section>
            <div class="sub-label">Your pack</div>
            <ItemGrid items={ch.pack} cols={6} size={56} onSel={(it) => actions.stash(it.uid)} onHover={onHover} />
            <div class="pack-foot"><span class="pack-hint">Click to move between pack and store</span></div>
          </section>
        </div>
      </div>
      {hover && <div class="inv-tip" style={{ left: `${hover.x}px`, top: `${hover.y}px` }}><ItemCard it={hover.it} ch={ch} /></div>}
    </div>
  );
}
