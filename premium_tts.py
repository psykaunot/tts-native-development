#!/usr/bin/env python3
"""
Premium Desktop TTS - High Quality Text-to-Speech
Uses multiple TTS backends for the best possible voice quality
"""

import sys
import os
import subprocess
import threading
import time
import json
import tempfile
import hashlib
from pathlib import Path
from urllib.parse import quote

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    import pyperclip
    import pyttsx3
    import pygame
    from gtts import gTTS
    import requests
    from pynput import keyboard
    from pynput.keyboard import Key, Listener
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    print(f"Dependencies not available: {e}")
    print("Install with: pip install pyttsx3 gtts pygame pyperclip pynput requests")

class PremiumTTSEngine:
    """High-quality TTS engine with multiple backends"""
    
    def __init__(self):
        self.available_engines = []
        self.current_engine = None
        self.pyttsx3_engine = None
        self.voice_cache_dir = Path.home() / '.cache' / 'premium_tts'
        self.voice_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pygame for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.pygame_available = True
        except:
            self.pygame_available = False
        
        self.init_engines()
    
    def init_engines(self):
        """Initialize all available TTS engines"""
        # Test pyttsx3 (local, fast, decent quality)
        try:
            self.pyttsx3_engine = pyttsx3.init()
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                self.available_engines.append({
                    'name': 'pyttsx3',
                    'display_name': 'System TTS (Fast)',
                    'quality': 'medium',
                    'online': False,
                    'voices': [{'id': v.id, 'name': v.name} for v in voices if v]
                })
        except Exception as e:
            print(f"pyttsx3 not available: {e}")
        
        # Google TTS (online, high quality)
        try:
            # Test with a small phrase
            test_tts = gTTS("test", lang='en')
            self.available_engines.append({
                'name': 'gtts',
                'display_name': 'Google TTS (High Quality)',
                'quality': 'high',
                'online': True,
                'voices': [
                    {'id': 'en', 'name': 'English (US)'},
                    {'id': 'en-uk', 'name': 'English (UK)'},
                    {'id': 'en-au', 'name': 'English (Australia)'},
                    {'id': 'en-ca', 'name': 'English (Canada)'}
                ]
            })
        except Exception as e:
            print(f"Google TTS not available: {e}")
        
        # Festival (local, good quality)
        try:
            result = subprocess.run(['festival', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_engines.append({
                    'name': 'festival',
                    'display_name': 'Festival TTS (Good Quality)',
                    'quality': 'good',
                    'online': False,
                    'voices': [
                        {'id': 'default', 'name': 'Default Festival Voice'}
                    ]
                })
        except Exception as e:
            print(f"Festival not available: {e}")
        
        # espeak-ng (improved espeak)
        try:
            result = subprocess.run(['espeak-ng', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.available_engines.append({
                    'name': 'espeak-ng',
                    'display_name': 'eSpeak NG (Enhanced)',
                    'quality': 'medium',
                    'online': False,
                    'voices': [
                        {'id': 'en+f3', 'name': 'Female Voice 3'},
                        {'id': 'en+f4', 'name': 'Female Voice 4'},
                        {'id': 'en+m3', 'name': 'Male Voice 3'},
                        {'id': 'en+m4', 'name': 'Male Voice 4'}
                    ]
                })
        except Exception as e:
            print(f"espeak-ng not available: {e}")
        
        # Set default engine (prefer Google TTS for quality)
        if self.available_engines:
            # Prefer Google TTS if available
            gtts_engine = next((e for e in self.available_engines if e['name'] == 'gtts'), None)
            if gtts_engine:
                self.current_engine = gtts_engine
            else:
                self.current_engine = self.available_engines[0]
    
    def get_cache_path(self, text, voice_id):
        """Get cache file path for spoken text"""
        text_hash = hashlib.md5(f"{text}_{voice_id}".encode()).hexdigest()
        return self.voice_cache_dir / f"{text_hash}.mp3"
    
    def speak_gtts(self, text, voice_id='en'):
        """Speak using Google TTS"""
        try:
            # Check cache first
            cache_path = self.get_cache_path(text, voice_id)
            
            if not cache_path.exists():
                # Generate speech
                tts = gTTS(text=text, lang=voice_id, slow=False)
                tts.save(str(cache_path))
            
            # Play audio
            if self.pygame_available:
                pygame.mixer.music.load(str(cache_path))
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                return True
            else:
                # Fallback to system player
                subprocess.run(['mpg123', str(cache_path)], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                return True
                
        except Exception as e:
            print(f"Google TTS failed: {e}")
            return False
    
    def speak_pyttsx3(self, text, voice_id=None):
        """Speak using pyttsx3"""
        try:
            if not self.pyttsx3_engine:
                return False
            
            if voice_id:
                self.pyttsx3_engine.setProperty('voice', voice_id)
            
            # Better quality settings
            self.pyttsx3_engine.setProperty('rate', 180)  # Slightly slower for clarity
            self.pyttsx3_engine.setProperty('volume', 0.9)
            
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"pyttsx3 failed: {e}")
            return False
    
    def speak_festival(self, text, voice_id='default'):
        """Speak using Festival"""
        try:
            # Create temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(text)
                temp_file = f.name
            
            try:
                # Use Festival to synthesize
                result = subprocess.run([
                    'festival', '--tts', temp_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                
                return result.returncode == 0
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            print(f"Festival failed: {e}")
            return False
    
    def speak_espeak_ng(self, text, voice_id='en+f3'):
        """Speak using espeak-ng with better settings"""
        try:
            subprocess.run([
                'espeak-ng',
                '-v', voice_id,
                '-s', '160',  # Speed
                '-a', '100',  # Amplitude
                '-p', '50',   # Pitch
                '-g', '10',   # Gap between words
                text
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            return True
            
        except Exception as e:
            print(f"espeak-ng failed: {e}")
            return False
    
    def speak(self, text, voice_id=None):
        """Speak text using the current engine"""
        if not text.strip():
            return False
        
        if not self.current_engine:
            return False
        
        engine_name = self.current_engine['name']
        
        try:
            if engine_name == 'gtts':
                return self.speak_gtts(text, voice_id or 'en')
            elif engine_name == 'pyttsx3':
                return self.speak_pyttsx3(text, voice_id)
            elif engine_name == 'festival':
                return self.speak_festival(text, voice_id)
            elif engine_name == 'espeak-ng':
                return self.speak_espeak_ng(text, voice_id or 'en+f3')
            else:
                return False
                
        except Exception as e:
            print(f"Speech failed: {e}")
            return False
    
    def stop(self):
        """Stop current speech"""
        try:
            if self.pygame_available:
                pygame.mixer.music.stop()
            
            # Kill various TTS processes
            for process in ['espeak', 'espeak-ng', 'festival']:
                try:
                    subprocess.run(['killall', process], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                except:
                    pass
            
            if self.pyttsx3_engine:
                try:
                    self.pyttsx3_engine.stop()
                except:
                    pass
                    
        except Exception as e:
            print(f"Stop failed: {e}")
    
    def set_engine(self, engine_name):
        """Set the current TTS engine"""
        engine = next((e for e in self.available_engines if e['name'] == engine_name), None)
        if engine:
            self.current_engine = engine
            return True
        return False
    
    def clear_cache(self):
        """Clear voice cache"""
        try:
            for file in self.voice_cache_dir.glob('*.mp3'):
                file.unlink()
            return True
        except Exception as e:
            print(f"Cache clear failed: {e}")
            return False

class PremiumTTSApp:
    """Premium TTS Desktop Application"""
    
    def __init__(self):
        self.tts = PremiumTTSEngine()
        self.config_file = Path.home() / '.config' / 'premium_tts.json'
        self.config = self.load_config()
        self.hotkey_listener = None
        self.clipboard_monitor_active = False
        self.last_clipboard_content = ""
        
        if not self.tts.available_engines:
            messagebox.showerror("Error", "No TTS engines available. Please install pyttsx3, gtts, or festival.")
            sys.exit(1)
        
        self.create_gui()
    
    def load_config(self):
        """Load configuration"""
        default_config = {
            'engine': 'gtts',
            'voice_id': 'en',
            'hotkey_enabled': True,
            'clipboard_monitor': False,
            'cache_enabled': True
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
    
    def create_gui(self):
        """Create the premium GUI"""
        self.root = tk.Tk()
        self.root.title("Premium TTS - High Quality Text-to-Speech")
        self.root.geometry("700x600")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Premium TTS", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Text input area
        ttk.Label(main_frame, text="Text to Speak:", 
                 font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.text_area = scrolledtext.ScrolledText(main_frame, height=8, width=80, 
                                                  font=('Arial', 11))
        self.text_area.grid(row=2, column=0, columnspan=3, pady=(0, 15), 
                           sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.speak_btn = ttk.Button(button_frame, text="🎤 Speak", command=self.speak_text)
        self.speak_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_speech)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="🗑 Clear", command=self.clear_text)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.paste_btn = ttk.Button(button_frame, text="📋 Paste & Speak", command=self.paste_and_speak)
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(button_frame, text="💾 Save Audio", command=self.save_audio)
        self.save_btn.pack(side=tk.LEFT)
        
        # Engine selection frame
        engine_frame = ttk.LabelFrame(main_frame, text="TTS Engine", padding="10")
        engine_frame.grid(row=4, column=0, columnspan=3, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.engine_var = tk.StringVar(value=self.config['engine'])
        for i, engine in enumerate(self.tts.available_engines):
            quality_indicator = "🟢" if engine['quality'] == 'high' else "🟡" if engine['quality'] == 'good' else "🟠"
            online_indicator = "🌐" if engine['online'] else "💻"
            
            ttk.Radiobutton(engine_frame, 
                           text=f"{quality_indicator} {online_indicator} {engine['display_name']}", 
                           variable=self.engine_var, 
                           value=engine['name'],
                           command=self.update_engine).grid(row=i//2, column=i%2, 
                                                           sticky=tk.W, padx=(0, 20), pady=2)
        
        # Voice selection
        voice_frame = ttk.LabelFrame(main_frame, text="Voice Selection", padding="10")
        voice_frame.grid(row=5, column=0, columnspan=3, pady=(0, 15), sticky=(tk.W, tk.E))
        
        ttk.Label(voice_frame, text="Voice:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.voice_var = tk.StringVar(value=self.config['voice_id'])
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, 
                                       state="readonly", width=30)
        self.voice_combo.grid(row=0, column=1, padx=(0, 20), sticky=(tk.W, tk.E))
        self.voice_combo.bind('<<ComboboxSelected>>', self.update_voice)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=6, column=0, columnspan=3, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.hotkey_var = tk.BooleanVar(value=self.config['hotkey_enabled'])
        ttk.Checkbutton(options_frame, text="Enable Global Hotkey (Ctrl+Alt+S)", 
                       variable=self.hotkey_var, command=self.toggle_hotkey).grid(row=0, column=0, sticky=tk.W)
        
        self.clipboard_var = tk.BooleanVar(value=self.config['clipboard_monitor'])
        ttk.Checkbutton(options_frame, text="Monitor Clipboard", 
                       variable=self.clipboard_var, command=self.toggle_clipboard).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        self.cache_var = tk.BooleanVar(value=self.config['cache_enabled'])
        ttk.Checkbutton(options_frame, text="Enable Voice Cache", 
                       variable=self.cache_var, command=self.toggle_cache).grid(row=1, column=0, sticky=tk.W)
        
        ttk.Button(options_frame, text="Clear Cache", command=self.clear_cache).grid(row=1, column=1, sticky=tk.W, padx=(20, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Premium TTS Initialized")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, font=('Arial', 9))
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        engine_frame.columnconfigure(1, weight=1)
        voice_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
        # Initialize
        self.update_engine()
        self.update_voice_list()
        
        if self.config['hotkey_enabled']:
            self.start_hotkey_listener()
        
        if self.config['clipboard_monitor']:
            self.start_clipboard_monitor()
    
    def update_engine(self):
        """Update TTS engine"""
        engine_name = self.engine_var.get()
        if self.tts.set_engine(engine_name):
            self.config['engine'] = engine_name
            self.save_config()
            self.update_voice_list()
            self.status_var.set(f"Engine changed to: {self.tts.current_engine['display_name']}")
    
    def update_voice_list(self):
        """Update voice selection list"""
        if self.tts.current_engine:
            voices = self.tts.current_engine['voices']
            voice_names = [f"{v['name']} ({v['id']})" for v in voices]
            self.voice_combo['values'] = voice_names
            
            if voice_names:
                self.voice_combo.current(0)
                self.voice_var.set(voice_names[0])
    
    def update_voice(self, event=None):
        """Update voice selection"""
        voice_selection = self.voice_var.get()
        if '(' in voice_selection:
            voice_id = voice_selection.split('(')[-1].rstrip(')')
            self.config['voice_id'] = voice_id
            self.save_config()
    
    def speak_text(self):
        """Speak the text in the text area"""
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.status_var.set("Speaking...")
            self.speak_btn.config(state='disabled')
            threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
    
    def _speak_thread(self, text):
        """Thread function for speaking"""
        voice_id = self.config['voice_id']
        success = self.tts.speak(text, voice_id)
        
        self.root.after(0, lambda: self.speak_btn.config(state='normal'))
        self.root.after(0, lambda: self.status_var.set("Ready" if success else "Speech failed"))
    
    def stop_speech(self):
        """Stop current speech"""
        self.tts.stop()
        self.status_var.set("Stopped")
        self.speak_btn.config(state='normal')
    
    def clear_text(self):
        """Clear the text area"""
        self.text_area.delete("1.0", tk.END)
    
    def paste_and_speak(self):
        """Paste clipboard content and speak it"""
        try:
            text = pyperclip.paste()
            if text:
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", text)
                self.speak_text()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste: {e}")
    
    def save_audio(self):
        """Save speech as audio file"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No text to save")
            return
        
        if self.tts.current_engine['name'] != 'gtts':
            messagebox.showinfo("Info", "Audio saving only available with Google TTS")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                voice_id = self.config['voice_id']
                tts = gTTS(text=text, lang=voice_id, slow=False)
                tts.save(filename)
                self.status_var.set(f"Audio saved: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save audio: {e}")
    
    def toggle_hotkey(self):
        """Toggle global hotkey"""
        enabled = self.hotkey_var.get()
        self.config['hotkey_enabled'] = enabled
        self.save_config()
        
        if enabled:
            self.start_hotkey_listener()
        else:
            self.stop_hotkey_listener()
    
    def toggle_clipboard(self):
        """Toggle clipboard monitoring"""
        enabled = self.clipboard_var.get()
        self.config['clipboard_monitor'] = enabled
        self.save_config()
        
        if enabled:
            self.start_clipboard_monitor()
        else:
            self.stop_clipboard_monitor()
    
    def toggle_cache(self):
        """Toggle voice cache"""
        self.config['cache_enabled'] = self.cache_var.get()
        self.save_config()
    
    def clear_cache(self):
        """Clear voice cache"""
        if self.tts.clear_cache():
            self.status_var.set("Cache cleared")
        else:
            self.status_var.set("Failed to clear cache")
    
    def start_hotkey_listener(self):
        """Start global hotkey listener"""
        def on_hotkey():
            try:
                text = pyperclip.paste()
                if text:
                    self.tts.speak(text, self.config['voice_id'])
            except:
                pass
        
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
                    len(current_content) < 500):
                    
                    self.last_clipboard_content = current_content
                    time.sleep(0.5)  # Delay to avoid rapid-fire speaking
                    
                    if self.clipboard_monitor_active:
                        self.tts.speak(current_content, self.config['voice_id'])
            except Exception as e:
                print(f"Clipboard monitor error: {e}")
            
            time.sleep(1)
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        finally:
            self.stop_hotkey_listener()
            self.stop_clipboard_monitor()

def main():
    """Main entry point"""
    if not DEPS_AVAILABLE:
        print("Required dependencies not available")
        print("Install with: pip install pyttsx3 gtts pygame pyperclip pynput requests")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # CLI mode
        text = ' '.join(sys.argv[1:])
        tts = PremiumTTSEngine()
        if tts.available_engines:
            tts.speak(text)
        else:
            print("No TTS engines available")
    else:
        # GUI mode
        app = PremiumTTSApp()
        app.run()

if __name__ == '__main__':
    main()