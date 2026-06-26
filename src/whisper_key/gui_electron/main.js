const { app, BrowserWindow, screen, ipcMain } = require('electron');
const path = require('path');
const readline = require('readline');
const fs = require('fs');
const net = require('net');

// Silence security warnings for local file execution
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';

// Handle ECONNRESET cleanly on exit
process.on('uncaughtException', (error) => {
  if (error.code === 'ECONNRESET') {
    app.quit();
  } else {
    console.error('Uncaught Exception:', error);
  }
});

// Enforce custom user data path in temp folder to avoid cache lock/permission issues on Windows
app.setPath('userData', path.join(app.getPath('temp'), 'whisper-key-overlay'));

let mainWindow;

function logIPC(msg) {
  try {
    fs.appendFileSync(path.join(__dirname, 'electron_ipc.log'), `${new Date().toISOString()} - ${msg}\n`);
  } catch (e) {}
}

function createWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

  const winWidth = 520;
  const winHeight = 140;
  const x = Math.floor((screenWidth - winWidth) / 2);
  const y = Math.floor(screenHeight - winHeight - (screenHeight * 0.15));

  mainWindow = new BrowserWindow({
    width: winWidth,
    height: winHeight,
    x: x,
    y: y,
    transparent: true,
    backgroundColor: '#00000000',
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,          // Keep hidden initially
    focusable: false,     // Click-through/no focus capture
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Pipe renderer console messages to main process stdout
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Console] ${message} (at ${path.basename(sourceId)}:${line})`);
  });

  // Ensure window is always on top even above fullscreen apps
  mainWindow.setAlwaysOnTop(true, 'screen-saver');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  try {
    fs.writeFileSync(path.join(__dirname, 'electron_ipc.log'), '');
  } catch (e) {}
  createWindow();

  // Common handler function for incoming IPC messages (JSON lines)
  function handleIPCLine(line) {
    if (!line.trim()) return;
    logIPC(`Received line: ${line.trim()}`);
    try {
      const message = JSON.parse(line);
      if (mainWindow) {
        // Send message to Renderer process
        mainWindow.webContents.send('py-message', message);
        
        // Handle window visibility on the main process side
        if (message.type === 'state') {
          if (message.value === 'recording' || message.value === 'processing') {
            mainWindow.showInactive(); // Show without taking keyboard focus
          } else if (message.value === 'idle') {
            mainWindow.hide();
          }
        }
      }
      
      // If Python tells us to exit, shut down cleanly
      if (message.type === 'exit') {
        app.quit();
      }
    } catch (err) {
      console.error('Failed to parse IPC message:', err);
    }
  }

  // Fallback: Stdin line reader
  const rlStdin = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });
  rlStdin.on('line', handleIPCLine);

  // Primary: TCP Socket client connecting back to Python server on the specified port
  const portArg = process.argv.find(arg => !isNaN(arg) && Number(arg) > 1024 && Number(arg) < 65535);
  const port = portArg ? Number(portArg) : null;

  if (port) {
    logIPC(`Attempting to connect to Python TCP server on port ${port}...`);
    const client = net.createConnection({ port: port, host: '127.0.0.1' }, () => {
      logIPC(`Successfully connected to Python TCP server on port ${port}`);
    });

    client.on('error', (err) => {
      logIPC(`TCP Socket Error: ${err.message}`);
    });

    client.on('close', () => {
      logIPC(`TCP Connection closed, exiting Electron...`);
      app.quit();
    });

    const rlSocket = readline.createInterface({
      input: client,
      output: client,
      terminal: false
    });
    rlSocket.on('line', handleIPCLine);
  } else {
    logIPC(`No TCP port argument specified. Running with stdin fallback only.`);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
