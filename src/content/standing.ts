import { test, type Ctx } from '@/world/logic';

/* How the powers of Thornhollow regard the survivor.
 *
 * The Verge asks these when it decides whether a wolf, a Kerchief or a
 * digger raises a hand (so a peace holds until it is broken on purpose),
 * and the journal reads the same answers back as a page: who is with you,
 * who is against you, and why. */

const F = (c: Ctx, k: string) => c.world.facts[k];

/** The Pack lets you pass. */
export const wolvesFriendly = (c: Ctx) => !F(c, 'hollow.hostile') && (!!F(c, 'hollow.peace') || !!F(c, 'pack.allied') || F(c, 'beasts.outcome') === 'cured' || c.ch.traits.includes('wolf_friend'));

/** The Kerchiefs let you pass: their colours, a bargain, Pell's word, Redcowl's pass. */
export const kerchiefsFriendly = (c: Ctx) => !F(c, 'roost.hostile') && (test({ hasTag: 'kerchief_colors' }, c) || F(c, 'redcowl') === 'bargained' || F(c, 'caravan.pell') === 'ally' || (test({ knows: 'pass.redcowl' }, c) && !!c.world.npcs.redcowl?.flags.met));

/** The Dig's crew leaves you be, until you give them a reason. */
export const diggersFriendly = (c: Ctx) => !F(c, 'dig.hostile');

/** At their own den the Pack holds off for someone who knows how to come to it. */
export const hollowCalm = (c: Ctx) => wolvesFriendly(c) || (!F(c, 'hollow.hostile') && test({ any: [{ knows: 'beastlore' }, { knows: 'hint.greymuzzle' }, { hasTag: 'wolf_fang' }] }, c));

export type Tone = 'ally' | 'friend' | 'neutral' | 'wary' | 'hostile' | 'gone';
export interface Standing { id: string; name: string; word: string; tone: Tone; why: string }

/** Every power you have met, and where you stand with it. */
export function standings(c: Ctx): Standing[] {
  const out: Standing[] = [];
  const w = c.world;
  const q = (id: string, entry: string) => !!w.quests[id]?.entries.includes(entry);

  // The Watch: Holloway's regard, and the law.
  const h = w.npcs.holloway;
  if (F(c, 'player.wanted')) out.push({ id: 'watch', name: 'The Watch', word: 'Wanted', tone: 'hostile', why: 'For selling stolen Coyle cargo. Holloway has your name.' });
  else if (F(c, 'holloway.lied_to') && !F(c, 'holloway.lie_settled')) out.push({ id: 'watch', name: 'The Watch', word: 'Suspicious', tone: 'wary', why: 'Holloway knows you lied to him about the wolves.' });
  else if (h) {
    const v = h.trust + h.respect;
    out.push(v >= 50 ? { id: 'watch', name: 'The Watch', word: 'Trusted', tone: 'ally', why: 'Holloway would stand a gate beside you.' }
      : v >= 15 ? { id: 'watch', name: 'The Watch', word: 'Friendly', tone: 'friend', why: 'The captain nods when you pass. From him, that is a speech.' }
        : v <= -30 ? { id: 'watch', name: 'The Watch', word: 'Watchful', tone: 'wary', why: 'The gate guards know your face, and not kindly.' }
          : { id: 'watch', name: 'The Watch', word: 'Watchful', tone: 'neutral', why: 'Another armed stranger off the road.' });
  }

  // The Coyle Company: Harlan, and his nephew.
  if (w.quests.caravan && w.quests.caravan.status !== 'unknown') {
    if (F(c, 'caravan.survivors') === 'rescued' && F(c, 'caravan.cargo') === 'returned') out.push({ id: 'coyle', name: 'The Coyle Company', word: 'In your debt', tone: 'ally', why: 'You brought Jory home, and every crate with him.' });
    else if (F(c, 'caravan.cargo') === 'kept' || F(c, 'caravan.cargo') === 'sold') out.push({ id: 'coyle', name: 'The Coyle Company', word: 'Cheated', tone: 'hostile', why: F(c, 'caravan.survivors') === 'rescued' ? 'You brought Jory home. You kept his uncle\'s goods.' : 'The Coyle cargo went where you took it.' });
    else if (F(c, 'caravan.survivors') === 'rescued') out.push({ id: 'coyle', name: 'The Coyle Company', word: 'Grateful', tone: 'ally', why: 'You brought Jory home.' });
    else if (F(c, 'caravan.survivors') === 'dead') out.push({ id: 'coyle', name: 'The Coyle Company', word: 'Grieving', tone: 'neutral', why: 'The teamsters died in the Roost\'s cages.' });
    else out.push({ id: 'coyle', name: 'The Coyle Company', word: 'Hoping', tone: 'friend', why: 'Harlan is waiting on news of his nephew.' });
  }

  // The Kerchiefs, once you know they are there.
  if (q('caravan', 'wreck') || q('caravan', 'roost_found') || Number(F(c, 'kerchief.raids') ?? 0) > 0 || w.npcs.redcowl?.flags.met) {
    if (F(c, 'redcowl') === 'dead') out.push({ id: 'kerchief', name: 'The Kerchiefs', word: 'Broken', tone: 'gone', why: 'Redcowl is dead. What is left of them has scattered.' });
    else if (F(c, 'roost.hostile')) out.push({ id: 'kerchief', name: 'The Kerchiefs', word: 'At war', tone: 'hostile', why: 'You broke the peace at the Roost. Every red rag in the Verge knows it.' });
    else if (kerchiefsFriendly(c)) {
      const why = test({ hasTag: 'kerchief_colors' }, c) ? 'You wear their red. They take it as a promise.'
        : F(c, 'redcowl') === 'bargained' ? 'You struck a bargain with Redcowl. It holds while it pays.'
          : F(c, 'caravan.pell') === 'ally' ? 'Pell\'s word goes a long way in the Roost.'
            : 'Redcowl gave you a pass, and his people know your face.';
      out.push({ id: 'kerchief', name: 'The Kerchiefs', word: 'Tolerated', tone: 'neutral', why });
    } else out.push({ id: 'kerchief', name: 'The Kerchiefs', word: 'Hostile', tone: 'hostile', why: 'Road bandits in red. They take what travels the Old Road.' });
  }

  // The Pack.
  if (w.quests.beasts && w.quests.beasts.status !== 'unknown') {
    const o = F(c, 'beasts.outcome');
    if (o === 'slaughtered' || F(c, 'greymuzzle') === 'dead') out.push({ id: 'pack', name: 'The Pack', word: 'Gone', tone: 'gone', why: o === 'slaughtered' ? 'You killed them. The Verge is quiet.' : 'Greymuzzle is dead. The rest will not come near you.' });
    else if (F(c, 'pack.allied') || o === 'allied') out.push({ id: 'pack', name: 'The Pack', word: 'Runs with you', tone: 'ally', why: 'Greymuzzle\'s wolves follow where you lead.' });
    else if (F(c, 'hollow.hostile')) out.push({ id: 'pack', name: 'The Pack', word: 'Hunting you', tone: 'hostile', why: 'You drew blood at the Hollow. They remember.' });
    else if (o === 'cured') out.push({ id: 'pack', name: 'The Pack', word: 'At peace', tone: 'friend', why: 'The stream runs clear. The wolves have gone back to the deep wood.' });
    else if (wolvesFriendly(c)) out.push({ id: 'pack', name: 'The Pack', word: 'Let you pass', tone: 'neutral', why: 'Greymuzzle showed you the sick ones. The Pack holds off.' });
    else out.push({ id: 'pack', name: 'The Pack', word: 'Starving', tone: 'hostile', why: 'The wolves are sick, and they are hunting the road.' });
  }

  // The Dig, once you know who is poisoning the stream.
  if (q('beasts', 'root_cause') || q('beasts', 'clue.pipe') || F(c, 'dig.hostile')) {
    const pump = F(c, 'dig.pump');
    if (pump === 'blown') out.push({ id: 'dig', name: 'Grimtunnel\'s Dig', word: 'Buried', tone: 'gone', why: 'You blew their powder. There is not much Dig left.' });
    else if (F(c, 'dig.hostile')) out.push({ id: 'dig', name: 'Grimtunnel\'s Dig', word: 'Hostile', tone: 'hostile', why: pump === 'broken' ? 'You wrecked their pump. The crew wants a word.' : 'You gave the diggers a reason.' });
    else if (pump === 'moved') out.push({ id: 'dig', name: 'Grimtunnel\'s Dig', word: F(c, 'dig.pell_cut') ? 'Paid off' : 'Working elsewhere', tone: 'neutral', why: F(c, 'dig.pell_cut') ? 'Pell paid them to move the outflow. You were paid to tell him.' : 'The foreman moved the outflow. He did not enjoy it.' });
    else out.push({ id: 'dig', name: 'Grimtunnel\'s Dig', word: 'Indifferent', tone: 'neutral', why: 'Diggers and their lamplings. They will not trouble you, if you do not trouble them.' });
  }
  return out;
}
