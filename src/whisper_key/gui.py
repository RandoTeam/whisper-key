import os
import sys
import math
import colorsys
import ctypes
from ctypes import c_int, sizeof, byref, Structure, pointer
from ctypes.wintypes import DWORD, ULONG
import customtkinter as ctk
import win32gui
import win32con
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

import subprocess
import json
import threading
import atexit
import socket

class FloatingOverlay:
    def __init__(self, parent=None):
        self.parent = parent
        self.target_text = ""
        self.client_socket = None
        self.server_socket = None
        self.pending_commands = []
        self.lock = threading.Lock()
        
        # Determine the Electron app directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.electron_app_dir = os.path.join(current_dir, "gui_electron")
        
        # Start a local TCP server on a random free port
        port = None
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('127.0.0.1', 0))
            self.server_socket.listen(1)
            port = self.server_socket.getsockname()[1]
        except Exception as e:
            print(f"[FloatingOverlay] Failed to bind TCP socket: {e}", flush=True)

        # Locate the locally downloaded Electron binary
        local_electron = os.path.join(self.electron_app_dir, "node_modules", "electron", "dist", "electron.exe")
        
        if os.path.exists(local_electron):
            cmd = [local_electron, "."]
        else:
            npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
            cmd = [npx_cmd, "electron", "."]
            
        if port is not None:
            cmd.append(str(port))
            
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        try:
            self.proc = subprocess.Popen(
                cmd,
                cwd=self.electron_app_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            
            # Start background threads to capture and print stdout/stderr
            threading.Thread(target=self._read_stream, args=(self.proc.stdout, "STDOUT"), daemon=True).start()
            threading.Thread(target=self._read_stream, args=(self.proc.stderr, "STDERR"), daemon=True).start()
            
            # Accept Electron's connection in a background thread
            if port is not None:
                threading.Thread(target=self._accept_connection, daemon=True).start()
            
        except Exception as e:
            print(f"[FloatingOverlay] Failed to start Electron process: {e}", flush=True)
            self.proc = None
            
        # Register clean exit handler
        atexit.register(self.close)
        
    def _accept_connection(self):
        try:
            self.server_socket.settimeout(5.0) # 5 seconds timeout
            client_socket, addr = self.server_socket.accept()
            client_socket.setblocking(True)
            
            with self.lock:
                self.client_socket = client_socket
                print(f"[FloatingOverlay] Electron client connected successfully from {addr}", flush=True)
                
                # Flush pending commands
                for cmd_dict in self.pending_commands:
                    try:
                        cmd_json = json.dumps(cmd_dict) + "\n"
                        self.client_socket.sendall(cmd_json.encode('utf-8'))
                    except Exception as e:
                        print(f"[FloatingOverlay] Failed to send queued command: {e}", flush=True)
                self.pending_commands.clear()
        except Exception as e:
            print(f"[FloatingOverlay] Electron connection failed or timed out: {e}", flush=True)

    def _read_stream(self, stream, name):
        try:
            for line in stream:
                line_str = line.strip()
                if line_str:
                    print(f"[Electron {name}] {line_str}", flush=True)
        except Exception:
            pass

    def _send_command(self, cmd_dict):
        with self.lock:
            # Send via TCP socket if available
            if self.client_socket:
                try:
                    cmd_json = json.dumps(cmd_dict) + "\n"
                    self.client_socket.sendall(cmd_json.encode('utf-8'))
                    return
                except Exception as e:
                    print(f"[FloatingOverlay] TCP socket send error: {e}, falling back to stdin", flush=True)
                    try:
                        self.client_socket.close()
                    except Exception:
                        pass
                    self.client_socket = None
            else:
                # If not connected yet, queue the command to be sent as soon as it connects.
                # Don't accumulate too many outdated text/volume updates.
                if cmd_dict["type"] == "state":
                    self.pending_commands.append(cmd_dict)
                else:
                    self.pending_commands = [c for c in self.pending_commands if c["type"] != cmd_dict["type"]]
                    self.pending_commands.append(cmd_dict)
                
        # Fallback to stdin
        if self.proc and self.proc.poll() is None:
            try:
                cmd_json = json.dumps(cmd_dict) + "\n"
                self.proc.stdin.write(cmd_json)
                self.proc.stdin.flush()
            except Exception as e:
                print(f"[FloatingOverlay] Stdin write error: {e}", flush=True)

    def show_recording(self):
        self.target_text = ""
        self._send_command({"type": "state", "value": "recording"})

    def show_processing(self):
        self.target_text = ""
        self._send_command({"type": "state", "value": "processing"})

    def hide(self):
        self.target_text = ""
        self._send_command({"type": "state", "value": "idle"})

    def update_volume(self, rms):
        self._send_command({"type": "volume", "value": float(rms)})

    def update_text(self, text):
        text = text.strip()
        if not text:
            return
        # Ensure capitalization of the first letter
        text = text[0].upper() + text[1:]
        self.target_text = text
        self._send_command({"type": "text", "value": text})

    def close(self):
        # 1. Close TCP connections
        if self.client_socket:
            try:
                cmd_json = json.dumps({"type": "exit"}) + "\n"
                self.client_socket.sendall(cmd_json.encode('utf-8'))
            except Exception:
                pass
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        # 2. Terminate Electron process
        if hasattr(self, 'proc') and self.proc:
            if self.proc.poll() is None:
                self._send_command({"type": "exit"})
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass
                try:
                    self.proc.wait(timeout=1.5)
                except subprocess.TimeoutExpired:
                    try:
                        self.proc.terminate()
                    except Exception:
                        pass
                except Exception:
                    pass
            self.proc = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass



class SettingsWindow(ctk.CTk):
    def __init__(self, state_manager, config_manager, model_registry, audio_recorder):
        super().__init__()
        
        self.state_manager = state_manager
        self.config_manager = config_manager
        self.model_registry = model_registry
        self.audio_recorder = audio_recorder
        
        # Window Settings
        self.title("Whisper Key - Настройки")
        self.geometry("520x340")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        self._create_ui()
        
    def _create_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="НАСТРОЙКИ WHISPER KEY",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        self.header_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.model_lbl = ctk.CTkLabel(
            self.form_frame,
            text="Модель Whisper:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.model_lbl.grid(row=0, column=0, sticky="w", pady=8)
        
        models = []
        for group in self.model_registry.get_groups_ordered():
            for m in self.model_registry.get_models_by_group(group):
                models.append(m)
        self.models_map = {m.label: m.key for m in models}
        model_labels = list(self.models_map.keys())
        
        self.model_menu = ctk.CTkOptionMenu(
            self.form_frame,
            values=model_labels,
            command=self._on_model_select,
            width=260
        )
        self.model_menu.grid(row=0, column=1, sticky="w", padx=15, pady=8)
        
        current_model_key = self.config_manager.get_setting("whisper", "model")
        for label, key in self.models_map.items():
            if key == current_model_key:
                self.model_menu.set(label)
                break
                
        self.mic_lbl = ctk.CTkLabel(
            self.form_frame,
            text="Микрофон:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.mic_lbl.grid(row=1, column=0, sticky="w", pady=8)
        
        current_host = self.state_manager.get_current_audio_host()
        devices = self.audio_recorder.get_available_audio_devices(current_host)
        self.devices_map = {f"{d['name']} ({d['hostapi']})": d['id'] for d in devices}
        device_labels = list(self.devices_map.keys())
        
        self.device_menu = ctk.CTkOptionMenu(
            self.form_frame,
            values=device_labels,
            command=self._on_device_select,
            width=260
        )
        self.device_menu.grid(row=1, column=1, sticky="w", padx=15, pady=8)
        
        current_dev_id = self.audio_recorder.get_device_id()
        for label, dev_id in self.devices_map.items():
            if dev_id == current_dev_id:
                self.device_menu.set(label)
                break
                
        self.paste_lbl = ctk.CTkLabel(
            self.form_frame,
            text="Авто-вставка текста:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.paste_lbl.grid(row=2, column=0, sticky="w", pady=8)
        
        auto_paste_enabled = self.config_manager.get_setting('clipboard', 'auto_paste')
        self.paste_switch = ctk.CTkSwitch(
            self.form_frame,
            text="Вставлять текст автоматически на позицию курсора",
            command=self._on_paste_toggle
        )
        if auto_paste_enabled:
            self.paste_switch.select()
        else:
            self.paste_switch.deselect()
        self.paste_switch.grid(row=2, column=1, sticky="w", padx=15, pady=8)
        
        hotkey_str = self.config_manager.get_setting("hotkey", "recording_hotkey").upper()
        stop_key_str = self.config_manager.get_setting("hotkey", "stop_key").upper()
        
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Быстрые клавиши: Зажать [{hotkey_str}] для записи, отпустить для завершения.\n"
                 f"Альтернативный стоп: клавиша [{stop_key_str}]. Окно скрывается автоматически.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="gray"
        )
        self.info_label.pack(side="bottom", fill="x", pady=15)

    def _on_model_select(self, label):
        model_key = self.models_map.get(label)
        if model_key:
            self.state_manager.request_model_change(model_key)
            self.config_manager.update_user_setting('whisper', 'model', model_key)
            
    def _on_device_select(self, label):
        dev_id = self.devices_map.get(label)
        if dev_id is not None:
            dev_name = label.split(" (")[0]
            self.state_manager.request_audio_device_change(dev_id, dev_name)
            self.config_manager.update_user_setting('audio', 'input_device', dev_id)
            
    def _on_paste_toggle(self):
        val = bool(self.paste_switch.get())
        self.state_manager.update_transcription_mode(val)
        
    def show_window(self):
        current_host = self.state_manager.get_current_audio_host()
        devices = self.audio_recorder.get_available_audio_devices(current_host)
        self.devices_map = {f"{d['name']} ({d['hostapi']})": d['id'] for d in devices}
        self.device_menu.configure(values=list(self.devices_map.keys()))
        self.deiconify()
        self.focus_force()
        
    def hide_window(self):
        self.withdraw()
