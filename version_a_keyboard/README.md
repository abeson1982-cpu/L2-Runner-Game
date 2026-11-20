# Speed Runner — Version A (Keyboard Edition)

An arcade endless runner game built with **Python** and **Pygame**.

---

## 🎮 How to Play

### Controls
| Key | Action |
| --- | --- |
| **SPACE** or **UP ARROW** | **Jump** over ground obstacles (cacti / spikes) |
| **DOWN ARROW** | **Duck / Slide** under flying drones |
| **SPACE** or **R** | **Restart** after Game Over |
| **ESC** | Quit game |

---

## 🚀 How to Run

### Method 1: Double-Click (Quickest)
Double-click `run_game.bat` inside this folder.

### Method 2: From PowerShell or Terminal
Open terminal in this directory and run:
```powershell
& "C:\Users\abeso\AppData\Local\Programs\Python\Python313\python.exe" game.py
```
Or if Python is in your PATH:
```bash
python game.py
```

---

## ⭐ Features
- **Smooth Physics**: Jump arc with realistic gravity, landing dust particles, and running stride animations.
- **Dynamic Obstacles**:
  - Ground obstacles (Green Spikes / Cacti) that require jumping.
  - Overhead flying obstacles (Drones / Bats) with animated wings that require ducking.
- **Procedural Audio**: Synthesized sound effects for jumps, coin pickups, and collisions (no external audio files needed).
- **Collectibles**: Spinning gold coins worth +15 bonus points with sparkle effects.
- **Progressive Difficulty**: Speed gradually increases as your score climbs.
- **High Score**: Best score is saved locally to `highscore.txt`.

