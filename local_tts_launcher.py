#!/usr/bin/env python3
"""
Local TTS Launcher - Simple GUI for Local TTS
Shows a window that can be clicked from desktop/menu
"""

import sys
import os
import subprocess
import threading
import tempfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    import pyperclip
    import pyttsx3
    import pygame
    from gtts import gTTS
    from pynput import keyboard
    GUI_AVAILABLE = True
except ImportError as e:
    GUI_AVAILABLE = False
    print(f"GUI dependencies not available: {e}")

class LocalTTSLauncher:
    """Simple GUI launcher for Local TTS"""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            print("❌ GUI not available")
            sys.exit(1)
        
        # Initialize TTS
        self.init_tts()
        
        # Configuration
        self.config_file = Path.home() / '.config' / 'local_tts_launcher.json'
        
        # State
        self.speaking = False
        self.background_service = None
        
        # Create GUI
        self.create_gui()
    
    def init_tts(self):
        """Initialize TTS engines"""
        self.available_engines = []
        self.current_engine = None
        self.pyttsx3_engine = None
        
        # Initialize pygame
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
        
        # Set default
        if self.available_engines:
            gtts_engine = next((e for e in self.available_engines if e['name'] == 'gtts'), None)
            self.current_engine = gtts_engine if gtts_engine else self.available_engines[0]
    
    def create_gui(self):
        """Create the GUI"""
        self.root = tk.Tk()
        self.root.title("Local TTS - High Quality Text-to-Speech")
        self.root.geometry("600x500")
        
        # Set custom icon if available
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'tts_image.png')
            if os.path.exists(icon_path):
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎤 Local TTS", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        subtitle_label = ttk.Label(main_frame, text="High-Quality Text-to-Speech", 
                                  font=('Arial', 10))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Text input
        ttk.Label(main_frame, text="Enter text to speak:", font=('Arial', 11, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.text_area = scrolledtext.ScrolledText(main_frame, height=8, width=70, 
                                                  font=('Arial', 11))
        self.text_area.grid(row=3, column=0, columnspan=2, pady=(0, 15), 
                           sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=(0, 15))
        
        self.speak_btn = ttk.Button(buttons_frame, text="🎤 Speak", 
                                   command=self.speak_text, style='Accent.TButton')
        self.speak_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(buttons_frame, text="⏹ Stop", command=self.stop_speech)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(buttons_frame, text="🗑 Clear", command=self.clear_text)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.paste_btn = ttk.Button(buttons_frame, text="📋 Paste & Speak", 
                                   command=self.paste_and_speak)
        self.paste_btn.pack(side=tk.LEFT)
        
        # Quick actions frame
        quick_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="10")
        quick_frame.grid(row=5, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        ttk.Button(quick_frame, text="🔥 Start Background Service", 
                  command=self.start_background_service).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(quick_frame, text="⚙️ Test Voice Quality", 
                  command=self.test_voice).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(quick_frame, text="📖 Read Clipboard", 
                  command=self.read_clipboard).pack(side=tk.LEFT)
        
        # Engine selection
        engine_frame = ttk.LabelFrame(main_frame, text="Voice Engine", padding="10")
        engine_frame.grid(row=6, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.engine_var = tk.StringVar(value=self.current_engine['name'] if self.current_engine else '')
        
        for engine in self.available_engines:
            ttk.Radiobutton(engine_frame, text=engine['display_name'], 
                           variable=self.engine_var, value=engine['name'],
                           command=self.change_engine).pack(side=tk.LEFT, padx=(0, 15))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Local TTS Launcher")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, font=('Arial', 9))
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Info label
        info_text = "💡 Tip: Click 'Start Background Service' to enable global hotkey (Ctrl+Alt+S)"
        ttk.Label(main_frame, text=info_text, font=('Arial', 9), 
                 foreground='blue').grid(row=8, column=0, columnspan=2, pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def speak_text(self):
        """Speak the text in the text area"""
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.status_var.set("Speaking...")
            self.speak_btn.config(state='disabled')
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
            self.root.after(0, lambda: self.speak_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def _speak_gtts(self, text):
        """Speak using Google TTS"""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                tts.save(temp_file.name)
                
                if self.pygame_available:
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        if not self.speaking:  # Allow stopping
                            pygame.mixer.music.stop()
                            break
                        pygame.time.wait(100)
                
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
    
    def stop_speech(self):
        """Stop current speech"""
        self.speaking = False
        if self.pygame_available:
            pygame.mixer.music.stop()
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
    
    def read_clipboard(self):
        """Read clipboard content directly"""
        try:
            text = pyperclip.paste()
            if text.strip():
                self.status_var.set("Speaking clipboard...")
                threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
            else:
                messagebox.showinfo("Info", "Clipboard is empty")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read clipboard: {e}")
    
    def change_engine(self):
        """Change TTS engine"""
        engine_name = self.engine_var.get()
        engine = next((e for e in self.available_engines if e['name'] == engine_name), None)
        if engine:
            self.current_engine = engine
            self.status_var.set(f"Switched to: {engine['display_name']}")
    
    def test_voice(self):
        """Test current voice"""
        test_text = f"Hello! This is Local TTS using {self.current_engine['display_name']}. The voice quality is much better than basic espeak."
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", test_text)
        self.speak_text()
    
    def start_background_service(self):
        """Start the background service"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_tts_path = os.path.join(script_dir, 'local_tts.py')
            
            if os.path.exists(local_tts_path):
                # Start background service
                self.background_service = subprocess.Popen([
                    sys.executable, local_tts_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.status_var.set("Background service started! Global hotkey: Ctrl+Alt+S")
                messagebox.showinfo("Success", 
                    "Local TTS background service started!\n\n" +
                    "• Press Ctrl+Alt+S anywhere to speak clipboard\n" +
                    "• Works in VS Code, Firefox, any application\n" +
                    "• Service runs in background")
            else:
                messagebox.showerror("Error", "local_tts.py not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start background service: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.background_service:
            try:
                self.background_service.terminate()
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Run the launcher"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main entry point"""
    if not GUI_AVAILABLE:
        print("❌ GUI dependencies not available")
        print("Install with: pip3 install --user tkinter")
        sys.exit(1)
    
    app = LocalTTSLauncher()
    app.run()

if __name__ == '__main__':
    main()