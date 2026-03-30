const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('dialog:openFile').catch((e: Error) => {
    console.error('[Preload] openFile error:', e);
    return undefined;
  }),
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory').catch((e: Error) => {
    console.error('[Preload] openDirectory error:', e);
    return undefined;
  }),
  getRuntimeInfo: () => ipcRenderer.invoke('runtime:info').catch((e: Error) => {
    console.error('[Preload] getRuntimeInfo error:', e);
    return { isElectron: false, apiBase: 'http://127.0.0.1:3000' };
  }),
});
