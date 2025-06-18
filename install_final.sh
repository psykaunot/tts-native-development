#!/bin/bash
# Final TTS Desktop Application Installer
# Creates a professional Linux desktop app with system tray integration

set -e

echo "🎤 Installing Local TTS - Professional Desktop Application"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "Please don't run this script as root"
   exit 1
fi

print_status "Installing Python dependencies..."
pip3 install --user pyttsx3 gtts pygame pyperclip pynput pystray Pillow requests

print_status "Setting up application structure..."

# Create application directory
APP_NAME="local-tts"
APP_DIR="$HOME/.local/share/$APP_NAME"
mkdir -p "$APP_DIR"

# Copy application files
cp local_tts.py "$APP_DIR/local_tts.py"
cp local_tts_launcher.py "$APP_DIR/local_tts_launcher.py"
cp premium_tts.py "$APP_DIR/premium_tts.py" 2>/dev/null || print_warning "premium_tts.py not found"
cp tts_image.png "$APP_DIR/tts_image.png" 2>/dev/null || print_warning "tts_image.png not found"

# Make executable
chmod +x "$APP_DIR/local_tts.py"
chmod +x "$APP_DIR/local_tts_launcher.py"

print_status "Creating desktop integration..."

# Create desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/local-tts.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Local TTS
GenericName=Text-to-Speech
Comment=High-quality local text-to-speech with system tray integration
Exec=python3 $APP_DIR/local_tts_launcher.py
Icon=$APP_DIR/tts_image.png
Terminal=false
Categories=Accessibility;AudioVideo;Audio;Utility;
Keywords=TTS;text-to-speech;accessibility;voice;speak;read;local;
StartupNotify=true
NoDisplay=false
Path=$APP_DIR
MimeType=text/plain;
EOF

chmod +x "$DESKTOP_FILE"

# Create command-line launcher
LAUNCHER_DIR="$HOME/.local/bin"
mkdir -p "$LAUNCHER_DIR"

LAUNCHER_SCRIPT="$LAUNCHER_DIR/local-tts"
cat > "$LAUNCHER_SCRIPT" << EOF
#!/bin/bash
# Local TTS Launcher
cd "$APP_DIR"
exec python3 local_tts.py "\$@"
EOF

chmod +x "$LAUNCHER_SCRIPT"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$LAUNCHER_DIR:"* ]]; then
    echo "export PATH=\"\$PATH:$LAUNCHER_DIR\"" >> ~/.bashrc
    print_status "Added $LAUNCHER_DIR to PATH"
fi

print_status "Setting up system integration..."

# Create autostart entry (ask user)
echo ""
read -p "🚀 Do you want Local TTS to start automatically at login? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$AUTOSTART_DIR/local-tts.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Local TTS
Comment=High-quality local text-to-speech system tray application
Exec=python3 $APP_DIR/local_tts.py
Icon=$APP_DIR/tts_image.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=Accessibility;
Path=$APP_DIR
EOF
    
    chmod +x "$AUTOSTART_DIR/local-tts.desktop"
    print_success "Autostart enabled - app will start with your desktop"
fi

print_status "Installing system packages (optional)..."

# Install optional system packages for better functionality
if command -v apt >/dev/null 2>&1; then
    print_status "Installing optional packages via apt..."
    sudo apt install -y zenity mpg123 libnotify-bin alsa-utils || print_warning "Some optional packages failed to install"
elif command -v dnf >/dev/null 2>&1; then
    print_status "Installing optional packages via dnf..."
    sudo dnf install -y zenity mpg123 libnotify alsa-utils || print_warning "Some optional packages failed to install"
elif command -v pacman >/dev/null 2>&1; then
    print_status "Installing optional packages via pacman..."
    sudo pacman -S --noconfirm zenity mpg123 libnotify alsa-utils || print_warning "Some optional packages failed to install"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications"
    print_status "Updated desktop database"
fi

print_status "Testing installation..."

# Test Python dependencies
python3 -c "
try:
    import pyttsx3, gtts, pygame, pyperclip, pynput
    print('✅ Core TTS dependencies available')
except Exception as e:
    print(f'❌ TTS dependencies test failed: {e}')
    exit(1)

try:
    import pystray
    from PIL import Image
    print('✅ System tray dependencies available')
except Exception as e:
    print(f'⚠️ System tray dependencies missing: {e}')
    print('App will run in background mode')
"

# Test basic TTS functionality
print_status "Testing TTS functionality..."
python3 "$APP_DIR/local_tts.py" "Local TTS installation test successful" || print_warning "TTS test may have failed"

echo ""
print_success "🎉 Local TTS Installation Complete!"
echo ""
echo "🎯 SYSTEM TRAY APPLICATION FEATURES:"
echo "══════════════════════════════════════"
echo "📍 System Tray Icon - Appears next to WiFi, Bluetooth, volume"
echo "🔥 Global Hotkey - Press Ctrl+Alt+S anywhere to speak clipboard"
echo "🎵 High-Quality Voices - Google TTS for natural speech"
echo "📋 Clipboard Monitoring - Auto-speak copied text (optional)"
echo "🔔 Desktop Notifications - Visual feedback"
echo "⚙️ Easy Configuration - Right-click menu settings"
echo ""
echo "🚀 HOW TO USE:"
echo "═════════════"
echo "1. 📱 Start from Application Menu:"
echo "   Search for 'Local TTS' in your app launcher"
echo ""
echo "2. 💻 Start from Command Line:"
echo "   local-tts &"
echo ""
echo "3. 🎤 Quick Text-to-Speech:"
echo "   local-tts \"Hello, this is a test\""
echo ""
echo "4. 🖱️ Using System Tray:"
echo "   • Look for speaker icon in system tray"
echo "   • Right-click for full menu"
echo "   • Left-click to speak clipboard quickly"
echo ""
echo "5. ⌨️ Global Hotkey:"
echo "   • Press Ctrl+Alt+S anywhere"
echo "   • Works in VS Code, Firefox, any app"
echo "   • Speaks current clipboard content"
echo ""
echo "🎨 SYSTEM INTEGRATION:"
echo "═════════════════════"
echo "• Application appears in your desktop's application menu"
echo "• System tray icon (notification area)"
echo "• Global keyboard shortcuts"
echo "• Desktop notifications"
echo "• Autostart capability"
echo "• Proper Linux desktop application"
echo ""
echo "🌟 VOICE QUALITY:"
echo "═══════════════"
echo "• Google TTS: Natural, human-like voices"
echo "• Much better than robotic espeak"
echo "• Multiple languages and accents"
echo "• Crystal clear pronunciation"
echo ""
echo "To start now:"
echo "local-tts &"
echo ""
echo "👀 Look for the speaker icon in your system tray!"