"""
Main application module for the Universal Translator UI.
"""
# pylint: disable=unexpected-keyword-arg, too-many-function-args, no-member
import os
import re
import sys
import time
import queue
import threading
import subprocess
import numpy as np
import flet as ft
import sounddevice as sd

from ui.theme import THEME, get_theme
from engine.translator import UniversalTranslator
from config import TRAINING_MODE, ACOUSTIC_MODEL_BACKBONE

class TranslatorApp:  # pylint: disable=too-many-instance-attributes
    """Main application class for the Universal Translator."""
    def __init__(self):
        self.page = None
        self.translator = None  # Loaded in a background thread to prevent GUI freezing on startup
        self.current_language = "pt"  # Default to Portuguese
        self.target_language = "clingo"  # Default alien language
        self.is_listening = False
        self.is_recording = False
        self.is_playing_audio = False
        self.recorded_alien_audio = None
        self.last_audio_file = None

        # Ensure directories exist
        os.makedirs("linguagens", exist_ok=True)
        for lang in [self.current_language, self.target_language]:
            os.makedirs(f"linguagens/{lang}", exist_ok=True)

    def main(self, page: ft.Page):
        """Entry point for the Flet application."""
        self.page = page
        page.title = "PROJECT: UNIVERSAL TRANSLATION"
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#050505"
        page.padding = 15

        # Set window size
        page.window_width = 1280
        page.window_height = 800
        try:
            page.window.width = 1280
            page.window.height = 800
        except Exception:
            pass

        # Build UI layout
        self.create_ui_elements()
        page.add(self.layout_container)
        page.update()

        # Start loading the translator engine in the background
        threading.Thread(target=self.load_translator_engine, daemon=True).start()

    def load_translator_engine(self):
        """Load PyTorch, Whisper, and ChromaDB in a background thread."""
        self.log_to_console("[SISTEMA] Inicializando motores neurais...\n")
        self.log_to_console("[SISTEMA] Carregando modelo Whisper 'small' (isso pode levar alguns segundos)...\n")
        
        try:
            self.translator = UniversalTranslator(model_size="small")
            self.status_text.value = f"[Nuvem] STATUS: PRONTO ({TRAINING_MODE.upper()} / {ACOUSTIC_MODEL_BACKBONE.upper()})"
            self.status_text.color = "#00ff00"
            
            # Enable buttons
            self.mic_button.disabled = False
            self.chat_mic_button.disabled = False
            self.chat_send_button.disabled = False
            self.alien_mic_btn.disabled = False
            self.train_button.disabled = False
            self.sync_button.disabled = False
            
            self.log_to_console("[SISTEMA] Todos os modelos carregados com sucesso! Tradutor online.\n")
        except Exception as ex:
            self.status_text.value = "ERRO AO CARREGAR MOTOR"
            self.status_text.color = "#ff0000"
            self.log_to_console(f"[ERRO] Falha crítica ao inicializar o UniversalTranslator: {ex}\n")
        
        self.page.update()

    def create_ui_elements(self):
        """Initializes and styles all Flet components into a 3-column widescreen grid."""
        # --- HEADER ---
        self.status_text = ft.Text(
            "SISTEMA INICIANDO (Carregando IA)...",
            color=THEME["status_color"],
            size=13,
            weight="bold"
        )
        header = ft.Row([
            ft.Text("PROJETO: TRADUÇÃO UNIVERSAL ....", size=20, color=THEME["accent_color"], weight="bold"),
            self.status_text
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # --- LEFT PANEL: LEARNING MODULE ---
        self.vu_bars = [
            ft.Container(width=6, height=10, bgcolor="#1a1a1a", border_radius=2)
            for _ in range(16)
        ]
        vu_row = ft.Row(self.vu_bars, alignment=ft.MainAxisAlignment.CENTER, spacing=4)

        self.play_button = ft.ElevatedButton(
            "OUVIR ÁUDIO CAPTADO",
            icon=ft.Icons.PLAY_ARROW,
            bgcolor=THEME["accent_color"],
            color="black",
            disabled=True,
            on_click=self.play_last_audio
        )

        self.word_display = ft.Text(
            "NENHUMA",
            size=36,
            weight="bold",
            color=THEME["status_color"],
            text_align="center"
        )

        self.text_input = ft.TextField(
            label="Palavra em Português",
            hint_text="Digite para mapear...",
            bgcolor="#111",
            border_color=THEME["border_color"],
            color="white",
            on_submit=self.on_text_submit,
            text_size=14
        )

        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            icon_color=THEME["accent_color"],
            icon_size=24,
            tooltip="Falar palavra em Português",
            disabled=True,
            on_click=self.on_mic_click
        )

        self.record_alien_btn = ft.ElevatedButton(
            "GRAVAR SOM ALIENÍGENA",
            icon=ft.Icons.FIBER_MANUAL_RECORD,
            bgcolor="#ff2a2a",
            color="white",
            on_click=self.record_alien_sound_start
        )

        self.save_word_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            icon_color="green",
            icon_size=28,
            tooltip="Salvar e Mapear Palavra",
            disabled=True,
            on_click=self.save_word
        )

        left_content = ft.Column([
            ft.Text("MÓDULO DE APRENDIZADO", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            
            # Audio Waveform visualizer container
            ft.Container(
                content=ft.Column([
                    ft.Text("CALIBRAÇÃO ACÚSTICA (EQUALIZADOR)", size=11, color="#888", weight="bold"),
                    vu_row
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                height=110,
                bgcolor="#0e0e0e",
                border=ft.border.all(1, "#333"),
                border_radius=5,
                padding=10
            ),
            
            ft.Row([self.play_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color="#222"),
            
            ft.Text("CONCEITO SEMÂNTICO EM FOCO:", size=11, color="#888", weight="bold"),
            ft.Container(
                content=self.word_display,
                alignment=ft.alignment.center,
                height=60,
                bgcolor="#0d0e15",
                border_radius=5
            ),
            
            ft.Row([
                ft.Container(self.text_input, expand=True),
                self.mic_button
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Divider(color="#222"),
            ft.Text("EMPARELHAR COM SOM ALIENÍGENA (4s):", size=11, color="#888", weight="bold"),
            ft.Row([
                self.record_alien_btn,
                self.save_word_button
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        # --- CENTER PANEL: CONVERSATION MODULE ---
        self.chat_container = ft.Container(
            height=460,
            bgcolor="#040406",
            border=ft.border.all(1, "#222"),
            border_radius=5,
            padding=10,
            content=ft.Column([], scroll=ft.ScrollMode.AUTO)
        )

        self.chat_input = ft.TextField(
            hint_text="Escreva em Português para traduzir...",
            bgcolor="#111",
            border_color=THEME["border_color"],
            color="white",
            on_submit=self.on_chat_submit,
            text_size=13,
            expand=True
        )

        self.chat_mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            icon_color=THEME["accent_color"],
            icon_size=20,
            tooltip="Falar mensagem (Human -> Alien)",
            disabled=True,
            on_click=self.on_chat_mic_click
        )

        self.chat_send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=THEME["accent_color"],
            icon_size=20,
            tooltip="Enviar mensagem",
            disabled=True,
            on_click=self.on_chat_send_click
        )

        self.alien_mic_btn = ft.IconButton(
            icon=ft.Icons.SPEAKER_PHONE,
            icon_color=THEME["status_color"],
            icon_size=22,
            tooltip="Ouvir & Traduzir Som Alien (Alien -> Human)",
            disabled=True,
            on_click=self.on_alien_mic_click
        )

        right_content = ft.Column([
            ft.Text("CANAL DE DIÁLOGO INTERESPÉCIES", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            self.chat_container,
            ft.Row([
                self.chat_input,
                self.chat_mic_button,
                self.chat_send_button,
                self.alien_mic_btn
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        ], spacing=8)

        # --- RIGHT PANEL: NEURAL TELEMETRY & CONSOLE ---
        self.backbone_dropdown = ft.Dropdown(
            label="Backbone Acústico",
            options=[
                ft.dropdown.Option("ast", "AST (Google Transformer)"),
                ft.dropdown.Option("mobilenet", "MobileNet V2 (CNN)")
            ],
            value=ACOUSTIC_MODEL_BACKBONE,
            bgcolor="#111",
            border_color=THEME["border_color"],
            color="white",
            on_change=self.save_config
        )

        self.train_mode_dropdown = ft.Dropdown(
            label="Ambiente de Treino",
            options=[
                ft.dropdown.Option("local", "Local GPU/CPU"),
                ft.dropdown.Option("cloud", "Nuvem (Modal.com T4/L4)")
            ],
            value=TRAINING_MODE,
            bgcolor="#111",
            border_color=THEME["border_color"],
            color="white",
            on_change=self.save_config
        )

        self.train_button = ft.ElevatedButton(
            "EXECUTAR TREINAMENTO SIAMES",
            icon=ft.Icons.PLAY_CIRCLE_FILL,
            bgcolor=THEME["status_color"],
            color="black",
            disabled=True,
            on_click=lambda _: self.run_script_in_console("train_siamese.py", ["--epochs", "10"])
        )

        self.sync_button = ft.ElevatedButton(
            "SINCRONIZAR CHROMADB",
            icon=ft.Icons.SYNC,
            bgcolor=THEME["accent_color"],
            color="black",
            disabled=True,
            on_click=lambda _: self.run_script_in_console("migrate_to_vector_db.py")
        )

        self.console_column = ft.Column(
            [],
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True
        )

        console_container = ft.Container(
            content=self.console_column,
            height=280,
            bgcolor="#000000",
            border=ft.border.all(1, THEME["border_color"]),
            border_radius=5,
            padding=8
        )

        clear_console_btn = ft.IconButton(
            icon=ft.Icons.DELETE_SWEEP,
            icon_color="#ff2a2a",
            icon_size=20,
            tooltip="Limpar Console",
            on_click=self.clear_console
        )

        telemetry_content = ft.Column([
            ft.Text("TELEMETRIA NEURAL & BANCO", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            self.backbone_dropdown,
            self.train_mode_dropdown,
            ft.Row([self.train_button, self.sync_button], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color="#222"),
            ft.Row([
                ft.Text("TELECONEXÃO MONITOR (LOGS SYSTEM):", size=11, color="#888", weight="bold"),
                clear_console_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            console_container
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        # --- MAIN CONTAINER GRID ---
        self.layout_container = ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=2, color=THEME["border_color"]),
                ft.Row([
                    # Column 1
                    ft.Container(
                        content=left_content,
                        border=ft.border.all(1, THEME["border_color"]),
                        border_radius=6,
                        padding=12,
                        expand=3
                    ),
                    # Column 2
                    ft.Container(
                        content=right_content,
                        border=ft.border.all(1, THEME["border_color"]),
                        border_radius=6,
                        padding=12,
                        expand=4
                    ),
                    # Column 3
                    ft.Container(
                        content=telemetry_content,
                        border=ft.border.all(1, THEME["border_color"]),
                        border_radius=6,
                        padding=12,
                        expand=3
                    )
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            ]),
            padding=15,
            border=ft.border.all(2, THEME["border_color"]),
            border_radius=8,
            bgcolor="#050505",
            expand=True
        )

    def log_to_console(self, text: str):
        """Append log lines to the scrolling visual terminal."""
        lines = text.splitlines()
        for line in lines:
            if not line.strip() and not line:
                continue
            
            # Select color based on log contents
            color = "#00f0ff"  # Default cyan
            if "[OK]" in line or "SUCESSO" in line or "CONCLUÍDO" in line:
                color = "#00ff00"  # Green
            elif "[ERRO]" in line or "FAILED" in line or "Traceback" in line:
                color = "#ff0000"  # Red
            elif "[AVISO]" in line or "WARNING" in line:
                color = "#ff9000"  # Orange/Yellow
                
            self.console_column.controls.append(
                ft.Text(line, font_family="monospace", size=10, color=color)
            )
            
        # Limit to 150 lines to keep performance high
        if len(self.console_column.controls) > 150:
            self.console_column.controls = self.console_column.controls[-150:]
            
        self.page.update()

    def clear_console(self, _e):
        """Clear all lines in the log console."""
        self.console_column.controls.clear()
        self.page.update()

    def save_config(self, _e=None):
        """Updates the configuration in src/config.py dynamically on selection changes."""
        backbone = self.backbone_dropdown.value
        mode = self.train_mode_dropdown.value
        
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.py"))
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                content = re.sub(r'TRAINING_MODE\s*=\s*["\'][^"\']*["\']', f'TRAINING_MODE = "{mode}"', content)
                content = re.sub(r'ACOUSTIC_MODEL_BACKBONE\s*=\s*["\'][^"\']*["\']', f'ACOUSTIC_MODEL_BACKBONE = "{backbone}"', content)
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log_to_console(f"[CONFIG] Atualização salva: BACKBONE={backbone.upper()} | MODO={mode.upper()}\n")
                
                # Update header status text to show active configurations
                self.status_text.value = f"[Nuvem] STATUS: PRONTO ({mode.upper()} / {backbone.upper()})"
                self.page.update()
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao escrever config.py: {ex}\n")

    def run_script_in_console(self, script_name: str, args: list = []):
        """Executes a Python script as an async background subprocess, streaming standard output to console."""
        self.train_button.disabled = True
        self.sync_button.disabled = True
        self.page.update()

        def target():
            try:
                script_path = os.path.join("scripts", script_name)
                self.log_to_console(f"\n[SISTEMA] INICIANDO: python {script_name} {' '.join(args)}\n")
                
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                
                process = subprocess.Popen(
                    [sys.executable, script_path] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env
                )
                
                for line in iter(process.stdout.readline, ''):
                    self.log_to_console(line)
                
                process.stdout.close()
                rc = process.wait()
                
                if rc == 0:
                    self.log_to_console(f"[SISTEMA] OPERAÇÃO CONCLUÍDA COM SUCESSO!\n")
                else:
                    self.log_to_console(f"[SISTEMA] ERRO: OPERAÇÃO FALHOU COM CÓDIGO {rc}\n")
            except Exception as ex:
                self.log_to_console(f"[SISTEMA] FALHA DE INICIALIZAÇÃO DE SUBPROCESSO: {ex}\n")
            finally:
                self.train_button.disabled = False
                self.sync_button.disabled = False
                self.page.update()

        threading.Thread(target=target, daemon=True).start()

    def add_message_to_chat(self, sender: str, message: str = "", is_user: bool = True, spans: list = None):
        """Add a message to the chat layout, supporting styled spans for highlighting missing words."""
        bubble_color = "#121420" if is_user else "#0f0e0d"
        border_color = THEME["accent_color"] if is_user else THEME["status_color"]
        
        if spans:
            text_control = ft.Text(spans=spans, size=13)
        else:
            text_color = "white" if is_user else THEME["status_color"]
            text_control = ft.Text(message, size=13, color=text_color)
            
        message_bubble = ft.Container(
            content=ft.Column([
                ft.Text(sender, size=10, color="#888888", weight="bold"),
                text_control
            ], spacing=2),
            bgcolor=bubble_color,
            border=ft.border.all(1, border_color),
            padding=9,
            border_radius=8,
            margin=ft.margin.only(bottom=5),
            width=280
        )
        
        bubble_row = ft.Row(
            [message_bubble],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        )
        
        chat_column = self.chat_container.content
        chat_column.controls.append(bubble_row)
        self.page.update()

    # --- LEARNING MODULE LOGIC ---
    def on_text_submit(self, _e):
        """Handle manual text input for learning."""
        word = self.text_input.value.strip().upper()
        if word:
            self.word_display.value = word
            self.text_input.value = ""
            self.log_to_console(f"[APRENDIZADO] Semântica definida: '{word}'. Grave o áudio correspondente.\n")
            self.page.update()

    def on_mic_click(self, _e):
        """Record and transcribe Portuguese speech using Whisper to define the target word."""
        if self.is_listening:
            return

        self.is_listening = True
        self.mic_button.icon_color = "#ff0000"
        self.page.update()

        self.log_to_console("[APRENDIZADO] Ouvindo voz humana (3s)...\n")
        threading.Thread(target=self.listen_for_word, daemon=True).start()

    def listen_for_word(self):
        """Record human word in background and transcribe."""
        try:
            word = self.translator.listen_and_transcribe(duration=3.0)
            word = word.strip().upper().replace(".", "").replace(",", "").replace("!", "")

            if word:
                self.word_display.value = word
                self.log_to_console(f"[APRENDIZADO] Transcrição bem sucedida: '{word}'\n")
            else:
                self.word_display.value = "NÃO DETECTADO"
                self.log_to_console("[APRENDIZADO] Nenhuma palavra foi identificada. Tente novamente.\n")
        except Exception as ex:
            self.log_to_console(f"[ERRO] Falha na transcrição: {ex}\n")
            self.word_display.value = "ERRO"
        finally:
            self.is_listening = False
            self.mic_button.icon_color = THEME["accent_color"]
            self.page.update()

    def record_alien_sound_start(self, _e):
        """Starts recording alien sound for learned word mapping."""
        word = self.word_display.value.strip()
        if not word or word in ("NENHUMA", "NÃO DETECTADO", "ERRO"):
            self.log_to_console("[AVISO] Defina um conceito em foco antes de gravar o som correspondente!\n")
            return

        if self.is_recording:
            return

        self.is_recording = True
        self.record_alien_btn.bgcolor = "#888888"
        self.record_alien_btn.text = "GRAVANDO SOM..."
        self.page.update()

        self.log_to_console(f"[APRENDIZADO] Gravando grunhido alienígena para '{word}' (4s). Fale ao microfone.\n")
        threading.Thread(target=self.record_alien_sound, daemon=True).start()

    def record_alien_sound(self):
        """Runs the audio recording process and activates VU animations."""
        # Start VU Meter animation thread
        threading.Thread(target=self.animate_vu_meter, daemon=True).start()
        
        try:
            # Record via AudioProcessor
            audio = self.translator.audio_processor.record_audio(duration=4.0)
            self.recorded_alien_audio = audio
            
            # Enable play and confirm buttons
            self.play_button.disabled = False
            self.save_word_button.disabled = False
            self.log_to_console(f"[APRENDIZADO] Captação de som finalizada. Valide jogando no reprodutor ou salve a assinatura.\n")
        except Exception as ex:
            self.log_to_console(f"[ERRO] Falha ao capturar som alienígena: {ex}\n")
        finally:
            self.is_recording = False
            self.record_alien_btn.bgcolor = "#ff2a2a"
            self.record_alien_btn.text = "GRAVAR SOM ALIENÍGENA"
            self.page.update()

    def animate_vu_meter(self):
        """Simulates real-time microphone intensity inside the visual EQ equalizer bars."""
        import random
        while self.is_recording:
            for bar in self.vu_bars:
                bar.height = random.randint(10, 90)
                # Color gradient for the bars
                if bar.height > 70:
                    bar.bgcolor = "#ff9000"  # Orange
                elif bar.height > 40:
                    bar.bgcolor = "#00f0ff"  # Cyan
                else:
                    bar.bgcolor = "#0055ff"  # Blue
            self.page.update()
            time.sleep(0.08)
            
        # Reset bars after recording completes
        for bar in self.vu_bars:
            bar.height = 10
            bar.bgcolor = "#1a1a1a"
        self.page.update()

    def play_last_audio(self, _e):
        """Play the recorded audio array directly using sounddevice."""
        if self.recorded_alien_audio is None:
            return

        self.play_button.disabled = True
        self.page.update()

        def play_task():
            self.is_playing_audio = True
            threading.Thread(target=self.animate_playback_waveform, daemon=True).start()
            
            try:
                sd.play(self.recorded_alien_audio, self.translator.audio_processor.sample_rate)
                sd.wait()
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao reproduzir áudio: {ex}\n")
            finally:
                self.is_playing_audio = False
                self.play_button.disabled = False
                self.page.update()

        threading.Thread(play_task, daemon=True).start()

    def animate_playback_waveform(self):
        """Simulates signal wave pulse animations during audio playback."""
        import random
        while self.is_playing_audio:
            for bar in self.vu_bars:
                bar.height = random.randint(10, 60)
                bar.bgcolor = THEME["accent_color"]
            self.page.update()
            time.sleep(0.08)
            
        for bar in self.vu_bars:
            bar.height = 10
            bar.bgcolor = "#1a1a1a"
        self.page.update()

    def save_word(self, _e):
        """Saves physical audio, inserts into SQLite, and indexes in ChromaDB vector database."""
        word = self.word_display.value.strip()
        if not word or self.recorded_alien_audio is None:
            return

        self.save_word_button.disabled = True
        self.page.update()

        try:
            self.log_to_console(f"[APRENDIZADO] Registrando '{word}' nas bases locais...\n")
            
            # 1. Save physical audio
            filepath = self.translator.audio_processor.save_audio(
                self.recorded_alien_audio, word, self.target_language
            )
            
            # 2. Register in SQLite database (metadata)
            self.translator.db.add_word(self.target_language, word, filepath)
            
            # 3. Save audio embedding in ChromaDB vector database
            signature = self.translator.audio_processor.extract_features(self.recorded_alien_audio)
            self.translator.vdb.add_audio_signature(
                word=word,
                language=self.target_language,
                embedding=signature.tolist(),
                audio_path=filepath
            )
            
            self.log_to_console(f"[SUCESSO] '{word}' registrada com sucesso nas bases física, SQLite e ChromaDB!\n")
            
            self.add_message_to_chat(
                "Sistema",
                f"Novo emparelhamento indexado: '{word}' -> {self.target_language.upper()}",
                is_user=False
            )
            
            # Reset states
            self.word_display.value = "NENHUMA"
            self.recorded_alien_audio = None
            self.play_button.disabled = True
        except Exception as ex:
            self.log_to_console(f"[ERRO] Falha ao salvar palavra: {ex}\n")
        finally:
            self.save_word_button.disabled = True
            self.page.update()

    # --- CONVERSATION MODULE LOGIC ---
    def on_chat_submit(self, _e):
        """Handle submit from text input box."""
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()

    def on_chat_mic_click(self, _e):
        """Uses Whisper to record human speech and send it to the conversation parser."""
        if self.is_listening:
            return

        self.is_listening = True
        self.chat_mic_button.icon_color = "#ff0000"
        self.page.update()

        self.log_to_console("[CONVERSA] Gravando fala humana para tradução (5s)...\n")
        
        def run():
            try:
                message = self.translator.listen_and_transcribe(duration=5.0)
                message = message.strip()
                if message:
                    self.process_message(message, is_user=True)
            except Exception as ex:
                self.log_to_console(f"[ERRO] Erro na gravação do chat: {ex}\n")
            finally:
                self.is_listening = False
                self.chat_mic_button.icon_color = THEME["accent_color"]
                self.page.update()

        threading.Thread(run, daemon=True).start()

    def on_chat_send_click(self, _e):
        """Handle send button clicks."""
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()

    def on_alien_mic_click(self, _e):
        """Listens to alien sound from microphone, matches inside Vector DB, and posts translation."""
        if self.is_recording:
            return

        self.is_recording = True
        self.alien_mic_btn.icon_color = "#ff0000"
        self.page.update()

        self.log_to_console("[CONVERSA] Capturando som extraterrestre (4s)...\n")
        threading.Thread(target=self.listen_and_translate_alien_audio, daemon=True).start()

    def listen_and_translate_alien_audio(self):
        """Record alien sound, extract embedding, query ChromaDB, and add message to chat."""
        # Animate visual EQ bars during recording
        threading.Thread(target=self.animate_vu_meter, daemon=True).start()
        
        try:
            audio_data = self.translator.audio_processor.record_audio(duration=4.0)
            self.is_recording = False
            
            self.log_to_console("[CONVERSA] Extraindo assinatura acústica e buscando no ChromaDB...\n")
            result = self.translator.translate_alien_audio(audio_data)
            
            if result:
                self.log_to_console(f"[CONVERSA] Tradução encontrada: {result}\n")
                self.add_message_to_chat(
                    "Ser Extraterrestre (Som)",
                    f"Tradução: {result}",
                    is_user=False
                )
            else:
                self.log_to_console("[CONVERSA] Nenhuma tradução correspondente com score mínimo.\n")
                self.add_message_to_chat(
                    "Ser Extraterrestre (Som)",
                    is_user=False,
                    spans=[ft.TextSpan("[SOM NÃO IDENTIFICADO / LACUNA NO ESPAÇO LATENTE]", style=ft.TextStyle(color="red", weight="bold"))]
                )
        except Exception as ex:
            self.log_to_console(f"[ERRO] Erro na tradução acústica: {ex}\n")
        finally:
            self.is_recording = False
            self.alien_mic_btn.icon_color = THEME["status_color"]
            self.page.update()

    def process_message(self, message: str, is_user: bool):
        """Splits sentences, identifies missing words in vector db, highlights them in red, and plays corresponding audios in background."""
        if not is_user:
            return

        self.add_message_to_chat("Você", message, is_user=True)

        # Parse message into clean words
        words = message.upper().split()
        clean_words = []
        for w in words:
            cw = ''.join(c for c in w if c.isalnum())
            if cw:
                clean_words.append(cw)

        if not clean_words:
            return

        # Prepare spans and audio lists
        spans = []
        audio_files_to_play = []

        for word in clean_words:
            # Query the database
            audio_path = self.translator.db.get_word_audio(self.target_language, word)
            if audio_path and os.path.exists(audio_path):
                # Found translated word - display in orange
                spans.append(ft.TextSpan(f"{word} ", style=ft.TextStyle(color=THEME["status_color"], weight="bold")))
                audio_files_to_play.append(audio_path)
            else:
                # Untranslated/Missing word - display in bold red
                spans.append(ft.TextSpan(f"[{word}] ", style=ft.TextStyle(color="red", weight="bold")))

        def alien_response_task():
            # Delay to simulate translation processing
            time.sleep(0.5)
            self.add_message_to_chat("Ser Extraterrestre", is_user=False, spans=spans)
            
            # Play audios sequentially if available
            if audio_files_to_play:
                self.play_sequenced_audio(audio_files_to_play)

        threading.Thread(target=alien_response_task, daemon=True).start()

    def play_sequenced_audio(self, paths: list):
        """Sequentially play sound files using sounddevice (avoiding file locking issues)."""
        self.is_playing_audio = True
        threading.Thread(target=self.animate_playback_waveform, daemon=True).start()

        import librosa
        for path in paths:
            try:
                audio, sr = librosa.load(path, sr=22050)
                sd.play(audio, sr)
                sd.wait()
                time.sleep(0.15)  # Brief silence between words
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao reproduzir áudio de '{path}': {ex}\n")

        self.is_playing_audio = False
        self.page.update()

def main(page: ft.Page):
    """Entrypoint function for the Flet app."""
    app = TranslatorApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)
