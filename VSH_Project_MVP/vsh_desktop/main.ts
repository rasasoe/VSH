import { app, BrowserWindow, ipcMain, dialog, Menu } from 'electron';
import * as path from 'path';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';

let mainWindow: BrowserWindow;
let apiProcess: ChildProcessWithoutNullStreams | null = null;

const isDev = !app.isPackaged;
const shouldAutoStartApi = (process.env.VSH_AUTO_START_API || 'false').toLowerCase() === 'true';

function resolveProjectRoot(): string {
  return path.resolve(__dirname, '..');
}

function waitForServer(url: string, timeout: number = 30000): Promise<boolean> {
  const startTime = Date.now();
  const checkServer = async (): Promise<boolean> => {
    try {
      const response = await fetch(url, { timeout: 1000 });
      return response.ok;
    } catch (e) {
      if (Date.now() - startTime > timeout) {
        return false;
      }
      await new Promise(r => setTimeout(r, 500));
      return checkServer();
    }
  };
  return checkServer();
}

function startApiServer() {
  if (!shouldAutoStartApi || apiProcess) {
    return;
  }

  const projectRoot = resolveProjectRoot();
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
  const args = ['-m', 'uvicorn', 'vsh_api.main:app', '--host', '127.0.0.1', '--port', '3000'];

  try {
    apiProcess = spawn(pythonCommand, args, {
      cwd: projectRoot,
      env: { ...process.env, PYTHONPATH: projectRoot },
      stdio: 'pipe',
      detached: process.platform !== 'win32'
    });

    if (apiProcess.pid) {
      console.log(`[VSH API] Started with PID ${apiProcess.pid}`);
    }
  } catch (error) {
    console.error(`[VSH API] Failed to start: ${error}`);
    apiProcess = null;
    return;
  }

  if (apiProcess.stdout) {
    apiProcess.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) console.log(`[VSH API] ${msg}`);
    });
  }

  if (apiProcess.stderr) {
    apiProcess.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) console.error(`[VSH API] ${msg}`);
    });
  }

  apiProcess.on('error', (err) => {
    console.error(`[VSH API] Process error: ${err}`);
    apiProcess = null;
  });

  apiProcess.on('exit', (code) => {
    console.log(`[VSH API] Process exited with code ${code}`);
    apiProcess = null;
  });
}

function stopApiServer() {
  if (!apiProcess) {
    return;
  }

  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(apiProcess.pid), '/f', '/t']);
    } else if (apiProcess.pid) {
      process.kill(-apiProcess.pid, 'SIGTERM');
    }
  } catch (e) {
    console.error(`[VSH API] Failed to stop: ${e}`);
  }

  apiProcess = null;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null!;
  });

  if (isDev) {
    console.log('[Electron] Loading from http://localhost:5173');
    mainWindow.loadURL('http://localhost:5173').catch(err => {
      console.error('[Electron] Failed to load dev server:', err);
      mainWindow.loadFile(path.join(__dirname, '../vsh_desktop/index.html'));
    });
    mainWindow.webContents.openDevTools();
  } else {
    const distPath = path.join(__dirname, '../dist-react/index.html');
    console.log('[Electron] Loading from:', distPath);
    mainWindow.loadFile(distPath).catch(err => {
      console.error('[Electron] Failed to load file:', err);
      mainWindow.webContents.loadURL(`data:text/html;charset=utf-8,<h1>Failed to load app. Check logs.</h1>`);
    });
  }
}

ipcMain.handle('dialog:openFile', async () => {
  if (!mainWindow) return undefined;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Python Files', extensions: ['py'] },
      { name: 'All Files', extensions: ['*'] }
    ],
  });
  return result.filePaths[0];
});

ipcMain.handle('dialog:openDirectory', async () => {
  if (!mainWindow) return undefined;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  return result.filePaths[0];
});

ipcMain.handle('runtime:info', async () => ({
  isElectron: true,
  apiBase: process.env.VITE_API_BASE_URL || process.env.VITE_VSH_API_URL || 'http://127.0.0.1:3000',
}));

app.on('ready', async () => {
  console.log('[Electron] App ready, starting services...');
  startApiServer();
  
  if (isDev && shouldAutoStartApi) {
    const apiReady = await waitForServer('http://127.0.0.1:3000/health', 15000);
    console.log(`[Electron] API ready: ${apiReady}`);
  }
  
  createWindow();
});

app.on('before-quit', () => {
  console.log('[Electron] Quitting, stopping API...');
  stopApiServer();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

if (isDev) {
  console.log('[Electron] Development mode');
}
