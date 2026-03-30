const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let apiProcess = null;

const isDev = !app.isPackaged;
const shouldAutoStartApi = (process.env.VSH_AUTO_START_API || 'true').toLowerCase() === 'true';
const shouldUseDist = (process.env.VSH_USE_DIST || 'false').toLowerCase() === 'true';

app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-gpu');

function resolveProjectRoot() {
  return path.resolve(__dirname, '..');
}

function configureRuntimePaths() {
  const runtimeRoots = [
    process.env.VSH_ELECTRON_DATA_DIR,
    process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'VSH', 'electron') : null,
    process.env.APPDATA ? path.join(process.env.APPDATA, 'VSH', 'electron') : null,
    path.join(app.getPath('temp'), 'vsh-electron'),
    path.join(resolveProjectRoot(), '.runtime', 'electron'),
  ].filter(Boolean);

  let lastError = null;

  for (const runtimeRoot of runtimeRoots) {
    const userDataPath = path.join(runtimeRoot, 'userData');
    const sessionDataPath = path.join(runtimeRoot, 'session');

    try {
      fs.mkdirSync(userDataPath, { recursive: true });
      fs.mkdirSync(sessionDataPath, { recursive: true });
      app.setPath('userData', userDataPath);
      app.setPath('sessionData', sessionDataPath);
      console.log(`[VSH Desktop] runtime path set to ${runtimeRoot}`);
      return;
    } catch (error) {
      lastError = error;
      console.warn(`[VSH Desktop] failed to use runtime path ${runtimeRoot}: ${error.message}`);
    }
  }

  throw new Error(`Unable to configure Electron runtime paths: ${lastError?.message || 'unknown error'}`);
}

async function ensureApiServer() {
  const apiBase = process.env.VITE_API_BASE_URL || process.env.VITE_VSH_API_URL || 'http://127.0.0.1:3000';

  try {
    const response = await fetch(`${apiBase}/health`);
    if (response.ok) {
      return;
    }
  } catch (_error) {
    // Ignore and try spawning the local API below.
  }

  startApiServer();
}

function startApiServer() {
  if (!shouldAutoStartApi || apiProcess) return;

  const projectRoot = resolveProjectRoot();
  const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
  const args = ['-m', 'uvicorn', 'vsh_api.main:app', '--host', '127.0.0.1', '--port', '3000'];

  try {
    apiProcess = spawn(pythonCommand, args, {
      cwd: projectRoot,
      env: { ...process.env, PYTHONPATH: projectRoot },
      stdio: 'pipe',
    });
  } catch (error) {
    console.error(`[VSH API] failed to start: ${error}`);
    apiProcess = null;
    return;
  }

  apiProcess.stdout.on('data', (data) => console.log(`[VSH API] ${data.toString().trim()}`));
  apiProcess.stderr.on('data', (data) => console.error(`[VSH API] ${data.toString().trim()}`));
  apiProcess.on('exit', (code) => {
    console.log(`[VSH API] process exited with code ${code}`);
    apiProcess = null;
  });
}

function stopApiServer() {
  if (!apiProcess) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(apiProcess.pid), '/f', '/t']);
  } else {
    apiProcess.kill('SIGTERM');
  }
  apiProcess = null;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    title: 'VSH Desktop',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  mainWindow.setMenuBarVisibility(false);

  const query = {};
  if (process.env.VSH_AUTO_SCAN_TARGET) query.target = process.env.VSH_AUTO_SCAN_TARGET;
  if (process.env.VSH_AUTO_SCAN_MODE) query.mode = process.env.VSH_AUTO_SCAN_MODE;
  if (process.env.VSH_AUTO_SCAN === '1') query.autostart = '1';

  const showLoadError = (message) => {
    const escaped = String(message || 'Unknown load error')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    mainWindow.loadURL(`data:text/html;charset=utf-8,
      <html>
        <body style="font-family: Arial, sans-serif; padding: 24px; background: #f8fafc; color: #111827;">
          <h1>VSH failed to load</h1>
          <p>The Electron shell opened, but the app UI did not render correctly.</p>
          <pre style="white-space: pre-wrap; background: #ffffff; padding: 12px; border: 1px solid #d1d5db; border-radius: 8px;">${escaped}</pre>
          <p>Check that the backend is running and the frontend build completed successfully.</p>
        </body>
      </html>`);
  };

  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    showLoadError(`did-fail-load: ${errorCode} ${errorDescription}`);
  });

  const loadPromise = isDev && !shouldUseDist
    ? mainWindow.loadURL('http://localhost:5173')
    : mainWindow.loadFile(path.join(__dirname, 'dist-react', 'index.html'), { query });

  loadPromise.catch((error) => {
    showLoadError(error?.stack || error?.message || String(error));
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [{ name: 'Python Files', extensions: ['py'] }],
  });
  return result.filePaths[0];
});

ipcMain.handle('dialog:openDirectory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  return result.filePaths[0];
});

ipcMain.handle('runtime:info', async () => ({
  isElectron: true,
  apiBase: process.env.VITE_API_BASE_URL || process.env.VITE_VSH_API_URL || 'http://127.0.0.1:3000',
}));

configureRuntimePaths();

app.on('ready', async () => {
  await ensureApiServer();
  createWindow();
});

app.on('before-quit', stopApiServer);
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
app.on('activate', () => {
  if (mainWindow === null) createWindow();
});
