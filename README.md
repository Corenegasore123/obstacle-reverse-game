# Avoid the Obstacles (Tkinter)

## Security notice (read first)

`obstacle_game.py` is not only a game.

It contains an **educational cybersecurity demo** that includes **network activity** and **OS-level persistence mechanisms** (for example, adding startup entries / cron jobs) in addition to the Tkinter game UI.

Run this script **only in a controlled lab environment** and only with explicit authorization.

## Overview

Avoid the Obstacles is a lane-dodging arcade mini game built with **Python** and **Tkinter**.

- You control a player car and dodge oncoming traffic.
- The UI includes a HUD with status, time, speed multiplier, score, and best score.

## What the program does

When you start `obstacle_game.py`, it:

- Shows a **consent / security notice** window first.
- If consent is approved, it proceeds to start the application.
- Starts the **Tkinter game UI**.

In the current code, it also contains functions for:

- Establishing outbound network connections
- Running background threads
- Setting OS-level persistence hooks
- A cleanup routine intended to remove those hooks

This repository’s README intentionally does **not** provide operational instructions for those cybersecurity-demo capabilities.

## Requirements

- Python 3.8+ recommended
- Uses only standard-library modules (Tkinter included)

## Repository contents

- `obstacle_game.py`: Tkinter game UI + educational cybersecurity demo logic
- `cleanup.py`: targeted cleanup utility (Windows + Linux/Kali; limited macOS support)
- `dist/cleanup.exe`: optional packaged cleanup executable (if you build it)

## Run (game UI)

From the project directory:

```bash
python obstacle_game.py
```

## Cleanup tool

This repository includes a **targeted cleanup tool** intended to remove only the persistence/artifacts that `obstacle_game.py` creates.

### Dry run (recommended)

Prints what would be removed, without changing anything:

```bash
python cleanup.py --dry-run
```

### Run cleanup

```bash
python cleanup.py
```

Notes:

- On Windows, run from an **Administrator** terminal for best results.
- On Kali/Linux, `crontab` must be available and you must have permission to edit your user crontab.

## Packaging (optional)

If you want a single-file Windows executable for the cleanup tool:

```bash
pyinstaller --onefile cleanup.py
```

The output will be in `dist/`.

## Controls

- **A** or **Left Arrow**: move left
- **D** or **Right Arrow**: move right
- **P**: pause / resume
- **R**: restart

## Gameplay notes

- Obstacles spawn in lanes and move down the road.
- Your speed increases gradually with score (shown as a multiplier in the HUD).
- A collision ends the run and shows a game-over overlay.

## Troubleshooting

### UI text shows strange symbols (e.g. `ðŸ…` / `âœ…`)

This indicates an **encoding mismatch** (mojibake). Using a UTF-8 capable terminal can help, but the most robust fix is to replace those characters in the source with plain ASCII.

### Blank window / nothing renders

Run from a terminal to capture exceptions:

```bash
python obstacle_game.py
```

### Cleanup reports "Access is denied" on Windows

Run `cleanup.py` (or `cleanup.exe`) from an elevated terminal (Run as Administrator). Some operations (process inspection, services, and certain registry keys) require admin privileges.

If you are unsure, start with a dry run:

```bash
python cleanup.py --dry-run
```

### Safety: I only want the game

If you want this project to behave strictly like a game, remove/disable any code paths that:

- Create outbound network connections
- Register OS startup tasks / scheduled jobs
- Run background threads unrelated to gameplay
