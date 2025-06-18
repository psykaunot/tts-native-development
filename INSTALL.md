# 🚀 Local TTS Installation Guide

## Quick Install (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/local-tts.git
cd local-tts
chmod +x install_final.sh
./install_final.sh
```

## Manual Installation

### 1. Prerequisites

**System Packages:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-tk mpg123 libnotify-bin zenity

# Fedora
sudo dnf install python3 python3-pip python3-tkinter mpg123 libnotify zenity

# Arch Linux
sudo pacman -S python python-pip tk mpg123 libnotify zenity
```

**Python Dependencies:**
```bash
pip3 install --user pyttsx3 gtts pygame pyperclip pynput
```

### 2. Download & Setup

```bash
git clone https://github.com/YOUR_USERNAME/local-tts.git
cd local-tts
chmod +x *.py
```

### 3. Desktop Integration

```bash
# Copy to applications directory
cp local_tts.desktop ~/.local/share/applications/

# Update desktop database
update-desktop-database ~/.local/share/applications
```

### 4. Optional: Add to PATH

```bash
# Create launcher
mkdir -p ~/.local/bin
echo '#!/bin/bash' > ~/.local/bin/local-tts
echo 'cd /path/to/local-tts' >> ~/.local/bin/local-tts
echo 'python3 local_tts_launcher.py "$@"' >> ~/.local/bin/local-tts
chmod +x ~/.local/bin/local-tts

# Add to PATH (add to ~/.bashrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Launch GUI
```bash
# From application menu
Search "Local TTS"

# From command line
python3 local_tts_launcher.py

# From PATH (if configured)
local-tts
```

### Background Service
```bash
# Start background service with global hotkeys
python3 local_tts.py

# Speak text directly
python3 local_tts.py "Hello, this is Local TTS"
```

### Global Hotkey
- Press `Ctrl+Alt+S` anywhere to speak clipboard content
- Works in VS Code, Firefox, any application

## Troubleshooting

### No Sound
```bash
# Test audio system
speaker-test

# Check pygame
python3 -c "import pygame; pygame.mixer.init(); print('Audio OK')"

# Install audio dependencies
sudo apt install pulseaudio alsa-utils
```

### GUI Issues
```bash
# Test tkinter
python3 -c "import tkinter; print('GUI OK')"

# Install GUI dependencies
sudo apt install python3-tk
```

### Global Hotkeys Not Working
```bash
# Test pynput
python3 -c "import pynput; print('Hotkeys OK')"

# May need elevated permissions for global hotkeys
sudo python3 local_tts.py
```

### Google TTS Issues
- Requires internet connection
- Check firewall settings
- Falls back to system voice automatically

## Configuration

Local TTS saves configuration in:
- `~/.config/local_tts.json` - Main app settings
- `~/.config/local_tts_launcher.json` - GUI settings

## Uninstall

```bash
# Remove application files
rm -rf ~/.local/share/local-tts
rm ~/.local/share/applications/local-tts.desktop
rm ~/.local/bin/local-tts
rm ~/.config/autostart/local-tts.desktop
rm ~/.config/local_tts*.json

# Update desktop database
update-desktop-database ~/.local/share/applications
```