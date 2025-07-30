# Sole Power Live - Launcher Instructions

## 🎺 Quick Start

You now have two ways to launch Sole Power Live:

### Option 1: Double-Click Launcher (Recommended)
Simply double-click the `Sole_Power_Live.command` file in this folder.

### Option 2: Terminal
Run `./start_sole_power_live.sh` from the terminal.

## What it does:
1. **Kills any existing processes** - Ensures a fresh start
2. **Clears Google authentication** - Forces fresh Google Drive connection
3. **Clears frontend cache** - No stale data
4. **Starts the backend API** - On port 8000
5. **Starts the frontend** - On port 3000
6. **Opens your browser** - Automatically navigates to the platform

## Features:
- ✅ Fresh start every time (no cached files)
- ✅ Fresh Google authentication each session
- ✅ Clean login screen (no OAuth redirects)
- ✅ Only shows current files (excludes trashed items)
- ✅ Automatic cleanup on exit (Ctrl+C)
- ✅ Colored output for easy reading
- ✅ Log files for debugging
- ✅ Automatic browser opening

## Authentication Flow:
1. **Clean login screen** - Enter your Google account email and password
2. **Seamless authentication** - System handles Google Drive connection automatically
3. **No redirects** - Stay on the same page throughout the process
4. **Files load** - Your current Sole Power Live files appear immediately

## Troubleshooting:

### "Permission Denied" Error
If you get a permission error, run:
```bash
chmod +x Sole_Power_Live.command
chmod +x start_sole_power_live.sh
```

### Making it look like an app
1. Right-click on `Sole_Power_Live.command`
2. Select "Get Info"
3. Drag a custom icon to the icon in the top-left of the Info window

### Still seeing old files?
The launcher now clears authentication each time, but if you still see outdated files:
1. Check Google Drive trash - empty it completely
2. Restart the launcher completely (Ctrl+C, then relaunch)

### First time setup
The first time you run it, macOS might ask for permission to run Terminal commands.

## Logs
- Backend log: `backend/backend.log`
- Frontend log: `frontend/frontend.log`

## Stopping the Platform
Press `Ctrl+C` in the Terminal window, or just close the Terminal window.