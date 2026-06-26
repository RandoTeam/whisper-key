const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onMessage: (callback) => ipcRenderer.on('py-message', (event, value) => callback(value))
});
