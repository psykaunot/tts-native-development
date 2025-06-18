# Local Text to Speech (TTS) - Linux Desktop Application

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-linux-lightgrey.svg)]()

High-quality text-to-speech desktop application with system integration and custom icon support.

![Local TTS Screenshot](tts_image.png)

## Features

- **High-Quality Voices** - Google TTS integration
- **Custom Icon Support** - Use your own tts_image.png  
- **Global Hotkeys** - Ctrl+Alt+S works system-wide
- **Desktop Integration** - Proper Linux application
- **Universal Compatibility** - Works in VS Code, Firefox, any app
- **Background Service** - Minimal resource usage
- **Easy to Use** - GUI launcher + command line

## Files Overview

| File | Purpose |
|------|---------|
| `local_tts_launcher.py` | Main GUI application |
| `local_tts.py` | Background service with global hotkeys |
| `premium_tts.py` | Advanced TTS with full features |
| `tts_image.png` | Custom icon |
| `install_final.sh` | Installation script |
| `local_tts.desktop` | Desktop entry for app menu |

## Installation

```bash
git clone https://github.com/psykaunot/tts-native-development.git
cd tts-native-development
chmod +x install_final.sh
./install_final.sh
```

The installer will:
- Install all dependencies
- Create proper Linux desktop app
- Use your custom `tts_image.png` icon
- Set up application menu entry
- Configure global hotkeys (Ctrl+Alt+S)

## Usage

### GUI Application
1. Search "Local TTS" in application menu
2. Or run `python3 local_tts_launcher.py`
3. Features include:
   - Text input with speak button
   - Engine selection (Google TTS vs System Voice)
   - Clipboard integration
   - Background service control
   - Voice quality test

### Background Service
- Click "Start Background Service" in GUI
- Enables global hotkey (Ctrl+Alt+S)
- Works system-wide in any application
- Press Ctrl+Alt+S anywhere to speak clipboard

### Voice Engines

| Engine | Quality | Requirements |
|--------|---------|-------------|
| Google TTS | Excellent | Internet connection |
| System Voice | Good | Works offline |

### Supported Languages

**Google TTS** supports 100+ languages including:
- English (US, UK, AU, IN)
- Spanish (ES, MX, AR)
- French (FR, CA)
- German, Italian, Portuguese
- Chinese (Mandarin, Cantonese)
- Japanese, Korean
- Arabic, Hindi, Russian
- And many more regional variants

**System Voice** language support depends on your Linux distribution's installed TTS packages (typically espeak/festival).

## Testing

```bash
# Test voice quality
python3 local_tts_launcher.py

# Or install and use from menu
./install_final.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Text-to-Speech API for high-quality voices
- Python TTS libraries (pyttsx3, gTTS)
- Linux desktop integration standards