/* Survivor Unchained on the desktop: an Electron window around the built
 * game.
 *
 * The game (dist/, from `npm run build`) is served over a private app://
 * scheme rather than file://, so its absolute asset paths (/assets/...)
 * resolve as they do on the dev server, fetch and WebAssembly work, and it
 * has an origin of its own for its saves (kept in the user's app data).
 *
 * SU_DEV_URL=http://localhost:5173 points the window at the dev server
 * instead (npm run desktop:dev). */
const { app, BrowserWindow, Menu, ipcMain, net, protocol, shell } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const DIST = path.join(__dirname, '..', 'dist');
const DEV_URL = process.env.SU_DEV_URL;

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } },
]);

// A game wants the GPU it has, not the one a blocklist allows.
app.commandLine.appendSwitch('ignore-gpu-blocklist');
app.commandLine.appendSwitch('enable-gpu-rasterization');

function serve() {
  protocol.handle('app', (req) => {
    const { pathname } = new URL(req.url);
    const file = path.normalize(path.join(DIST, decodeURIComponent(pathname === '/' ? '/index.html' : pathname)));
    if (!file.startsWith(DIST)) return new Response('Not found', { status: 404 });
    return net.fetch(pathToFileURL(file).toString());
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1600,
    height: 900,
    minWidth: 1024,
    minHeight: 600,
    backgroundColor: '#0b0a0d',
    title: 'Survivor Unchained',
    icon: path.join(__dirname, 'icon.png'),
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      // Keep simulating and rendering when the window is covered; the game
      // pauses itself when it loses focus.
      backgroundThrottling: false,
    },
  });
  win.once('ready-to-show', () => win.show());
  // F11 and Alt+Enter: fullscreen, as every game does.
  win.webContents.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11' || (input.alt && input.key === 'Enter')) {
      win.setFullScreen(!win.isFullScreen());
      e.preventDefault();
    }
  });
  // Links (the credits) open in the player's browser, not in the game.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith('app://') && !(DEV_URL && url.startsWith(DEV_URL))) e.preventDefault();
  });
  win.loadURL(DEV_URL || 'app://game/index.html');
  return win;
}

app.whenReady().then(() => {
  serve();
  Menu.setApplicationMenu(null);
  ipcMain.handle('desktop:quit', () => app.quit());
  ipcMain.handle('desktop:fullscreen', (e, on) => {
    const win = BrowserWindow.fromWebContents(e.sender);
    if (!win) return false;
    if (typeof on === 'boolean') win.setFullScreen(on);
    return win.isFullScreen();
  });
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => app.quit());
