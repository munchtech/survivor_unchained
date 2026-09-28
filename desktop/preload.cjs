/* What the game may ask of the desktop shell: quit, and fullscreen. */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktop', {
  quit: () => ipcRenderer.invoke('desktop:quit'),
  /** Set fullscreen (true/false), or just ask (no argument). */
  fullscreen: (on) => ipcRenderer.invoke('desktop:fullscreen', on),
});
