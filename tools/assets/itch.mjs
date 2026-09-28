/* Fetch free (pay-what-you-want, $0) asset packs from itch.io, the way the
 * "No thanks, just take me to the downloads" button does.
 *
 *   node tools/assets/itch.mjs <game url> [--list] [--get <name regex>] [--out dir]
 *
 * Lists the pack's files, or downloads the ones whose name matches. Used to
 * pull the CC0 Quaternius packs the game's people and animations come from
 * (see public/assets/CREDITS.md); kept so the art can be fetched again. */
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const game = args.find((a) => a.startsWith('http'));
const want = args.includes('--get') ? new RegExp(args[args.indexOf('--get') + 1], 'i') : null;
const out = args.includes('--out') ? args[args.indexOf('--out') + 1] : '.';
if (!game) { console.log('usage: node tools/assets/itch.mjs <game url> [--list] [--get regex] [--out dir]'); process.exit(1); }

const jar = new Map();
const cookie = () => [...jar].map(([k, v]) => `${k}=${v}`).join('; ');
async function req(url, opts = {}) {
  const r = await fetch(url, { ...opts, redirect: 'manual', headers: { cookie: cookie(), 'user-agent': 'Mozilla/5.0', ...(opts.headers ?? {}) } });
  for (const c of r.headers.getSetCookie?.() ?? []) { const [kv] = c.split(';'); const i = kv.indexOf('='); jar.set(kv.slice(0, i), kv.slice(i + 1)); }
  if (r.status >= 300 && r.status < 400 && r.headers.get('location')) return req(new URL(r.headers.get('location'), url).toString(), { method: 'GET' });
  return r;
}
const form = (o) => ({ method: 'POST', body: new URLSearchParams(o).toString(), headers: { 'content-type': 'application/x-www-form-urlencoded' } });

const page = await (await req(game)).text();
const csrf = page.match(/name="csrf_token" value="([^"]+)"/)?.[1];
if (!csrf) throw new Error('no csrf token on the page');
const dl = await (await req(`${game.replace(/\/$/, '')}/download_url`, form({ csrf_token: csrf }))).json();
if (!dl.url) throw new Error(`no download page: ${JSON.stringify(dl)}`);
const key = dl.url.split('/download/')[1];
const dpage = await (await req(dl.url)).text();
const uploads = [...dpage.matchAll(/data-upload_id="(\d+)"[\s\S]*?<strong[^>]*title="([^"]+)"[\s\S]*?class="file_size"><span>([^<]+)</g)].map((m) => ({ id: m[1], name: m[2], size: m[3] }));
if (!uploads.length) {
  // Older markup: the name before the id.
  for (const m of dpage.matchAll(/<strong[^>]*class="name"[^>]*>([^<]+)<\/strong>[\s\S]*?data-upload_id="(\d+)"/g)) uploads.push({ id: m[2], name: m[1], size: '?' });
}
if (!uploads.length) { fs.writeFileSync('/tmp/itch_download_page.html', dpage); console.log('no uploads found; page saved to /tmp/itch_download_page.html'); }
for (const u of uploads) console.log(`${u.id}\t${u.size}\t${u.name}`);
if (!want) process.exit(0);
fs.mkdirSync(out, { recursive: true });
const dcsrf = dpage.match(/name="csrf_token" value="([^"]+)"/)?.[1] ?? csrf;
for (const u of uploads.filter((u) => want.test(u.name))) {
  // A free pack hands out its files without the purchase key (the key flow
  // answers "invalid key" for $0 downloads); the link lives for a minute.
  let f = await (await req(`${game.replace(/\/$/, '')}/file/${u.id}?source=view_game&as_props=1&after_download_lightbox=true`, form({ csrf_token: csrf }))).json();
  if (!f.url) f = await (await req(`${game.replace(/\/$/, '')}/file/${u.id}?source=game_download&key=${key}`, form({ csrf_token: dcsrf }))).json();
  if (!f.url) { console.log('no url for', u.name, JSON.stringify(f)); continue; }
  const r = await fetch(f.url);
  const buf = Buffer.from(await r.arrayBuffer());
  const file = path.join(out, u.name);
  fs.writeFileSync(file, buf);
  console.log(`saved ${file} (${(buf.length / 1e6).toFixed(1)} MB)`);
}
