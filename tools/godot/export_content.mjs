/* The web game's written content, as JSON for the Godot game: every
 * conversation, quest, person, shop, item, calling, background and trait,
 * the daily rules, who talks to whom, the town's folk and the looks, and
 * the interface's line glyphs. Loaded
 * from the real TypeScript through Vite (so what the web game runs is what
 * is exported); functions are not data and are ported by hand (item
 * affixes, objectives, standings, the chapter's summary).
 *
 *   node tools/godot/export_content.mjs
 *
 * Writes godot/data/content/*.json. */
import { createServer } from 'vite';
import fs from 'node:fs';

const out = 'godot/data/content';
fs.mkdirSync(out, { recursive: true });
const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error' });
const load = (p) => server.ssrLoadModule(p);

/** JSON with functions refused: a function in content would be silently lost. */
function write(name, value) {
  const json = JSON.stringify(value, (k, v) => {
    if (typeof v === 'function') throw new Error(`${name}: a function at "${k}" is not data`);
    return v;
  }, 1);
  fs.writeFileSync(`${out}/${name}.json`, json + '\n');
  console.log(`${name}.json  ${(json.length / 1024).toFixed(0)} KB`);
}

const dialogue = await load('/src/content/dialogue/index.ts');
write('dialogue', dialogue.CONVOS);
const quests = await load('/src/content/quests.ts');
write('quests', quests.QUESTS);
const npcs = await load('/src/content/npcs.ts');
write('npcs', { npcs: npcs.NPCS, outsiders: npcs.OUTSIDERS, speakers: npcs.SPEAKERS, guards: npcs.GUARDS });
const concerns = await load('/src/content/concerns.ts');
write('concerns', concerns.CONCERNS);
const shops = await load('/src/content/shops.ts');
write('shops', shops.SHOPS);
const folk = await load('/src/content/folk.ts');
write('folk', { looks: folk.FOLK_LOOKS, children: folk.CHILD_LOOKS, watch: folk.WATCH_LOOK, lines: folk.FOLK_LINES });
const looks = await load('/src/content/looks.ts');
write('looks', { cloaks: looks.CLOAK_DYES, skins: looks.SKINS, hairs: looks.HAIRS, hairStyles: looks.HAIR_STYLES });
const rules = await load('/src/content/rules.ts');
write('rules', { rules: rules.RULES, social: rules.SOCIAL, caravanSettle: rules.CARAVAN_SETTLE });
const arche = await load('/src/content/archetypes.ts');
write('archetypes', { archetypes: arche.ARCHETYPES, backgrounds: arche.BACKGROUNDS, traits: arche.TRAITS });
const items = await load('/src/content/items.ts');
write('items', { items: items.ITEMS, raritynames: items.RARITY_NAMES, slots: items.EQUIP_SLOTS });
const glyphs = await load('/src/ui/glyphs.ts');
write('glyphs', glyphs.GLYPHS);
await server.close();
