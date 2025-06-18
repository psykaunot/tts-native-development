#!/usr/bin/env python3
"""
Local TTS - High-Quality Linux Desktop Application
Works with any Linux system, appears in system tray/notification area
"""

import sys
import os
import threading
import time
import json
import tempfile
import subprocess
from pathlib import Path

try:
    import pyperclip
    import pyttsx3
    import pygame
    from gtts import gTTS
    from pynput import keyboard
    TTS_DEPS_AVAILABLE = True
except ImportError as e:
    TTS_DEPS_AVAILABLE = False
    print(f"TTS dependencies not available: {e}")

# For now, disable pystray due to compatibility issues
# Will run in background mode with global hotkeys
PYSTRAY_AVAILABLE = False
print("🎤 Local TTS - Background mode (global hotkeys enabled)")

class LocalTTS:
    """Local TTS - High-quality system TTS application"""
    
    def __init__(self):
        if not TTS_DEPS_AVAILABLE:
            self.show_install_help()
            sys.exit(1)
        
        # Initialize TTS
        self.init_tts()
        
        # Configuration
        self.config_file = Path.home() / '.config' / 'local_tts.json'
        self.config = self.load_config()
        
        # State
        self.speaking = False
        self.hotkey_listener = None
        self.clipboard_monitor_active = False
        self.last_clipboard_content = ""
        self.running = True
        
        # Create system tray or background service
        if PYSTRAY_AVAILABLE:
            self.create_system_tray()
        else:
            self.run_background_service()
    
    def show_install_help(self):
        """Show installation help"""
        print("🚨 Local TTS - Missing Dependencies")
        print("=" * 35)
        print("Install required packages:")
        print("pip3 install --user pyttsx3 gtts pygame pyperclip pynput")
        print("")
        print("For system tray icon (optional):")
        print("pip3 install --user pystray Pillow")
        
        try:
            subprocess.run([
                'notify-send', 'Local TTS',
                'Missing dependencies. Check terminal for installation instructions.',
                '--icon=dialog-error'
            ])
        except:
            pass
    
    def init_tts(self):
        """Initialize TTS engines"""
        self.available_engines = []
        self.current_engine = None
        self.pyttsx3_engine = None
        
        # Initialize pygame for audio
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.pygame_available = True
        except:
            self.pygame_available = False
        
        # Test pyttsx3
        try:
            self.pyttsx3_engine = pyttsx3.init()
            self.available_engines.append({
                'name': 'pyttsx3',
                'display_name': 'System Voice (Fast)'
            })
        except:
            pass
        
        # Test Google TTS
        try:
            test_tts = gTTS("test", lang='en')
            self.available_engines.append({
                'name': 'gtts',
                'display_name': 'Google TTS (High Quality)'
            })
        except:
            pass
        
        # Set default (prefer Google TTS)
        if self.available_engines:
            gtts_engine = next((e for e in self.available_engines if e['name'] == 'gtts'), None)
            self.current_engine = gtts_engine if gtts_engine else self.available_engines[0]
        else:
            print("❌ No TTS engines available")
            sys.exit(1)
    
    def load_config(self):
        """Load configuration"""
        default_config = {
            'engine': 'gtts',
            'voice_lang': 'en',
            'hotkey_enabled': True,
            'clipboard_monitor': False,
            'notifications': True,
            'startup_notification': True
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
        except:
            pass
        
        return default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def create_system_tray(self):
        """Create system tray icon"""
        # Try to load custom icon, fallback to generated
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'tts_image.png')
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                # Resize to standard tray icon size
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
            else:
                raise FileNotFoundError("Custom icon not found")
        except Exception:
            # Fallback to generated icon
            image = Image.new('RGB', (64, 64), color='#4CAF50')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='white')
            draw.text((22, 22), '🎤', fill='#4CAF50')
        
        # Create menu
        def create_menu():
            return TrayMenu(
                TrayItem('🎤 Local TTS', None, enabled=False),
                TrayMenu.SEPARATOR,
                TrayItem('🗣️ Speak Clipboard', self.speak_clipboard),
                TrayItem('✏️ Enter Text...', self.show_text_input),
                TrayMenu.SEPARATOR,
                TrayItem(f'🟢 {self.current_engine["display_name"]}', self.toggle_engine),
                TrayMenu.SEPARATOR,
                TrayItem('🔥 Global Hotkey (Ctrl+Alt+S)', self.toggle_hotkey, 
                        checked=lambda item: self.config['hotkey_enabled']),
                TrayItem('📋 Monitor Clipboard', self.toggle_clipboard,
                        checked=lambda item: self.config['clipboard_monitor']),
                TrayItem('🔔 Notifications', self.toggle_notifications,
                        checked=lambda item: self.config['notifications']),
                TrayMenu.SEPARATOR,
                TrayItem('🖥️ Open Full App', self.open_full_app),
                TrayItem('ℹ️ About', self.show_about),
                TrayItem('⚙️ Test Voice', self.test_voice),
                TrayMenu.SEPARATOR,
                TrayItem('❌ Quit', self.quit_app)
            )
        
        self.icon = TrayIcon("Local TTS", image, menu=create_menu())
        
        # Start services
        self.start_services()
        
        # Show startup notification
        if self.config['startup_notification']:
            self.show_notification("Local TTS started! Right-click tray icon for menu.")
        
        # Run tray icon (this blocks)
        self.icon.run()
    
    def run_background_service(self):
        """Run as background service without system tray"""
        print("🎤 Local TTS - Background Service Mode")
        print("=" * 35)
        print("Running without system tray (pystray not available)")
        print("")
        print("🎯 CONTROLS:")
        print("• Global Hotkey: Ctrl+Alt+S (speak clipboard)")
        print("• Command: local-tts <text>")
        print("• Stop: Ctrl+C")
        print("")
        
        # Start services
        self.start_services()
        
        # Show notification
        self.show_notification("Local TTS running in background. Press Ctrl+Alt+S to speak clipboard.")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Local TTS stopped")
            self.quit_app()
    
    def speak_clipboard(self, icon=None, item=None):
        """Speak clipboard content"""
        try:
            text = pyperclip.paste()
            if text.strip():
                self.speak_text(text)
                if self.config['notifications']:
                    self.show_notification(f"Speaking: {text[:50]}...")
            else:
                if self.config['notifications']:
                    self.show_notification("Clipboard is empty")
        except Exception as e:
            self.show_notification(f"Error: {e}")
    
    def show_text_input(self, icon=None, item=None):
        """Show text input dialog"""
        def show_dialog():
            try:
                # Try zenity first
                result = subprocess.run([
                    'zenity', '--entry',
                    '--title=Local TTS',
                    '--text=Enter text to speak:',
                    '--width=400'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and result.stdout.strip():
                    text = result.stdout.strip()
                    self.speak_text(text)
                    return
            except:
                pass
            
            # Fallback: use the full app
            self.open_full_app()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def toggle_engine(self, icon=None, item=None):
        """Toggle between available engines"""
        if len(self.available_engines) > 1:
            current_index = next((i for i, e in enumerate(self.available_engines) 
                                if e['name'] == self.current_engine['name']), 0)
            next_index = (current_index + 1) % len(self.available_engines)
            self.current_engine = self.available_engines[next_index]
            self.config['engine'] = self.current_engine['name']
            self.save_config()
            
            if self.config['notifications']:
                self.show_notification(f"Switched to: {self.current_engine['display_name']}")
    
    def toggle_hotkey(self, icon=None, item=None):
        """Toggle global hotkey"""
        self.config['hotkey_enabled'] = not self.config['hotkey_enabled']
        self.save_config()
        
        if self.config['hotkey_enabled']:
            self.start_hotkey_listener()
            self.show_notification("Global hotkey enabled (Ctrl+Alt+S)")
        else:
            self.stop_hotkey_listener()
            self.show_notification("Global hotkey disabled")
    
    def toggle_clipboard(self, icon=None, item=None):
        """Toggle clipboard monitoring"""
        self.config['clipboard_monitor'] = not self.config['clipboard_monitor']
        self.save_config()
        
        if self.config['clipboard_monitor']:
            self.start_clipboard_monitor()
            self.show_notification("Clipboard monitoring enabled")
        else:
            self.stop_clipboard_monitor()
            self.show_notification("Clipboard monitoring disabled")
    
    def toggle_notifications(self, icon=None, item=None):
        """Toggle notifications"""
        self.config['notifications'] = not self.config['notifications']
        self.save_config()
        
        if self.config['notifications']:
            self.show_notification("Notifications enabled")
    
    def test_voice(self, icon=None, item=None):
        """Test current voice"""
        test_text = f"Hello! This is a test of {self.current_engine['display_name']}. The voice quality is much better than basic espeak."
        self.speak_text(test_text)
    
    def show_about(self, icon=None, item=None):
        """Show about information"""
        about_text = f"""Local TTS v1.0

Current Engine: {self.current_engine['display_name']}
Available Engines: {len(self.available_engines)}

Features:
• High-quality voices (Google TTS)
• Global hotkey (Ctrl+Alt+S)
• System tray integration
• Clipboard monitoring
• Works system-wide

Usage:
Right-click tray icon for menu
Press Ctrl+Alt+S anywhere to speak clipboard"""

        try:
            subprocess.run([
                'zenity', '--info',
                '--title=About Local TTS',
                f'--text={about_text}',
                '--width=350'
            ])
        except:
            self.show_notification("Local TTS v1.0 - High-quality text-to-speech")
    
    def open_full_app(self, icon=None, item=None):
        """Open full premium TTS application"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            premium_tts_path = os.path.join(script_dir, 'premium_tts.py')
            if os.path.exists(premium_tts_path):
                subprocess.Popen([sys.executable, premium_tts_path])
            else:
                self.show_notification("Full app not found. Install premium_tts.py")
        except Exception as e:
            self.show_notification(f"Failed to open full app: {e}")
    
    def speak_text(self, text):
        """Speak text using current engine"""
        if self.speaking or not text.strip():
            return
        
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
    
    def _speak_thread(self, text):
        """Thread function for speaking"""
        self.speaking = True
        
        try:
            if self.current_engine['name'] == 'gtts':
                self._speak_gtts(text)
            elif self.current_engine['name'] == 'pyttsx3':
                self._speak_pyttsx3(text)
        except Exception as e:
            print(f"Speech failed: {e}")
        finally:
            self.speaking = False
    
    def _speak_gtts(self, text):
        """Speak using Google TTS"""
        try:
            tts = gTTS(text=text, lang=self.config['voice_lang'], slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                tts.save(temp_file.name)
                
                if self.pygame_available:
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                else:
                    # Fallback to system player
                    subprocess.run(['mpg123', temp_file.name], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"Google TTS failed: {e}")
    
    def _speak_pyttsx3(self, text):
        """Speak using pyttsx3"""
        try:
            if self.pyttsx3_engine:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"pyttsx3 failed: {e}")
    
    def show_notification(self, message):
        """Show desktop notification"""
        if self.config['notifications']:
            try:
                subprocess.run([
                    'notify-send', 
                    'Local TTS', 
                    message,
                    '--icon=audio-speakers',
                    '--app-name=Local TTS'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
    
    def start_services(self):
        """Start background services"""
        if self.config['hotkey_enabled']:
            self.start_hotkey_listener()
        
        if self.config['clipboard_monitor']:
            self.start_clipboard_monitor()
    
    def start_hotkey_listener(self):
        """Start global hotkey listener"""
        def on_hotkey():
            self.speak_clipboard()
        
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({
                '<ctrl>+<alt>+s': on_hotkey
            })
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Hotkey listener failed: {e}")
    
    def stop_hotkey_listener(self):
        """Stop hotkey listener"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
    
    def start_clipboard_monitor(self):
        """Start clipboard monitoring"""
        if not self.clipboard_monitor_active:
            self.clipboard_monitor_active = True
            threading.Thread(target=self._clipboard_monitor_thread, daemon=True).start()
    
    def stop_clipboard_monitor(self):
        """Stop clipboard monitoring"""
        self.clipboard_monitor_active = False
    
    def _clipboard_monitor_thread(self):
        """Clipboard monitoring thread"""
        while self.clipboard_monitor_active:
            try:
                current_content = pyperclip.paste()
                if (current_content != self.last_clipboard_content and 
                    current_content.strip() and 
                    len(current_content) < 300):
                    
                    self.last_clipboard_content = current_content
                    time.sleep(0.5)
                    
                    if self.clipboard_monitor_active:
                        self.speak_text(current_content)
            except Exception as e:
                print(f"Clipboard monitor error: {e}")
            
            time.sleep(1)
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        self.running = False
        self.stop_hotkey_listener()
        self.stop_clipboard_monitor()
        
        if PYSTRAY_AVAILABLE and hasattr(self, 'icon'):
            self.icon.stop()
        
        sys.exit(0)

def main():
    """Main entry point"""
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Local TTS - High Quality Text-to-Speech")
            print("Usage:")
            print("  local-tts.py                 # Start system tray app")
            print("  local-tts.py 'text to speak' # Speak text directly")
            print("  local-tts.py --help          # Show this help")
            return
        else:
            # Speak the provided text
            text = ' '.join(sys.argv[1:])
            if not TTS_DEPS_AVAILABLE:
                print("❌ Missing dependencies. Install with:")
                print("pip3 install --user pyttsx3 gtts pygame pyperclip pynput")
                sys.exit(1)
            
            app = LocalTTS()
            app.speak_text(text)
            
            # Wait for speech to complete
            while app.speaking:
                time.sleep(0.1)
            time.sleep(1)
            return
    
    # Start system tray application
    if not TTS_DEPS_AVAILABLE:
        print("❌ Required dependencies not available")
        print("Install with: pip3 install --user pyttsx3 gtts pygame pyperclip pynput")
        if not PYSTRAY_AVAILABLE:
            print("For system tray: pip3 install --user pystray Pillow")
        sys.exit(1)
    
    try:
        app = LocalTTS()
    except Exception as e:
        print(f"❌ Failed to start Local TTS: {e}")
        print("Make sure all dependencies are installed.")
        sys.exit(1)

if __name__ == '__main__':
    main()