MouseFX Upgrade — Windows 10/11

FEATURES
- Neon, Fireflies, Smoke and Magic effects
- Colour picker and particle-density slider
- Left-click burst and global F8 toggle
- System tray menu and optional Windows startup
- Click-through overlay intended to preserve normal clicks/taskbar

INSTALL
1. Extract this folder to C:\\MouseFX (or another permanent folder).
2. Double-click install.bat and wait for it to finish.
3. Double-click run.bat.
4. Find MouseFX near the clock; right-click its tray icon for controls/quit.

CONTROLS
- F8: toggle effects anywhere
- Left-click: particle burst
- Control Center: choose effect, colour, density, startup
- Keep density at 1–5 on a 4 GB RAM PC.

OPTIONAL EXE
Double-click build_exe.bat. If successful, the app is dist\\MouseFX.exe.

STOP / UNINSTALL
- Right-click tray icon > Quit MouseFX.
- Turn off Start with Windows in the control center, or delete:
  %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\MouseFX-start.bat
- Delete the extracted folder if you no longer want it.

NOTES
First release; not tested on your specific PC. It may not display on the Windows lock screen, UAC secure desktop, or some protected full-screen apps. Python 3.12/3.13 may be easier if your Python 3.14 cannot install a compatible PySide6 wheel.
