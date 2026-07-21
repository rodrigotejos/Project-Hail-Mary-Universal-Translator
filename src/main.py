"""
Main application module for the Universal Translator UI.
"""
# pylint: disable=unexpected-keyword-arg, too-many-function-args, no-member
import os
import re
import sys
import time
import threading
import subprocess
import numpy as np
import flet as ft
import sounddevice as sd

from ui.theme import THEME, get_theme
from engine.translator import UniversalTranslator
from config import TRAINING_MODE, ACOUSTIC_MODEL_BACKBONE

def border_all(width: float, color: str):
    """Helper to create a 4-sided border in backward-compatible Flet syntax."""
    return ft.border.Border(
        top=ft.BorderSide(width, color),
        right=ft.BorderSide(width, color),
        bottom=ft.BorderSide(width, color),
        left=ft.BorderSide(width, color)
    )

class TranslatorApp:  # pylint: disable=too-many-instance-attributes
    """Main application class for the Universal Translator."""
    def __init__(self):
        self.page = None
        self.translator = None
        self.current_language = "pt"
        self.target_language = "clingo"
        self.is_listening = False
        self.is_recording = False
        self.is_playing_audio = False
        self.recorded_alien_audio = None
        self.last_audio_file = None

        os.makedirs("linguagens", exist_ok=True)
        for lang in [self.current_language, self.target_language]:
            os.makedirs(f"linguagens/{lang}", exist_ok=True)

    def main(self, page: ft.Page):
        self.page = page
        page.title = "PROJECT: UNIVERSAL TRANSLATION"
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#050505"
        page.padding = 15

        try:
            page.window.width = 1280
            page.window.height = 800
        except Exception:
            pass

        self.create_ui_elements()
        page.add(self.layout_container)
        page.update()

        threading.Thread(target=self.load_translator_engine, daemon=True).start()

    def load_translator_engine(self):
        self.log_to_console("[SISTEMA] Inicializando motores neurais...\n")
        self.log_to_console("[SISTEMA] Carregando modelo Whisper 'small' (isso pode levar alguns segundos)...\n")
        try:
            self.translator = UniversalTranslator(model_size="small")
            self.status_text.value = f"[Nuvem] STATUS: PRONTO ({TRAINING_MODE.upper()} / {ACOUSTIC_MODEL_BACKBONE.upper()})"
            self.status_text.color = "#00ff00"
            
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
            self.log_to_console(f"[ERRO] Falha crítica ao inicializar: {ex}\n")
        self.page.update()

    def on_sync_cloud_click(self, _e=None):
        self.sync_cloud_btn.disabled = True
        self.cloud_status_text.value = "[Cloud] STATUS: SINCRONIZANDO..."
        self.cloud_status_text.color = "#ffaa00"
        self.page.update()

        def do_sync():
            try:
                from src.database.registry import TranslatorDB
                from src.services.sync_service import MockSupabaseSync
                db = TranslatorDB()
                sync_svc = MockSupabaseSync(db)
                res = sync_svc.sync_all()
                if res.success:
                    self.cloud_status_text.value = f"[Cloud] ONLINE (Pushed: {res.records_pushed} | Pulled: {res.records_pulled})"
                    self.cloud_status_text.color = "#00ff00"
                    snack = ft.SnackBar(content=ft.Text(f"Sincronização concluída com sucesso! (Pushed: {res.records_pushed}, Pulled: {res.records_pulled})"), bgcolor="green")
                else:
                    self.cloud_status_text.value = "[Cloud] FALHA NA SINCRONIZAÇÃO"
                    self.cloud_status_text.color = "#ff0000"
                    snack = ft.SnackBar(content=ft.Text(f"Erro na sincronização: {res.error_message}"), bgcolor="red")
            except Exception as ex:
                self.cloud_status_text.value = "[Cloud] ERRO"
                self.cloud_status_text.color = "#ff0000"
                snack = ft.SnackBar(content=ft.Text(f"Falha ao sincronizar: {ex}"), bgcolor="red")
            finally:
                self.sync_cloud_btn.disabled = False
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        threading.Thread(target=do_sync, daemon=True).start()

    def get_available_languages(self):
        langs = ["clingo", "ingles"]
        if os.path.exists("linguagens"):
            for item in os.listdir("linguagens"):
                if os.path.isdir(os.path.join("linguagens", item)):
                    if item not in langs:
                        langs.append(item)
        return langs

    def create_ui_elements(self):
        # --- HEADER ---
        self.status_text = ft.Text("SISTEMA INICIANDO (Carregando IA)...", color=THEME["status_color"], size=13, weight="bold")
        self.cloud_status_text = ft.Text("[Cloud] STATUS: OFFLINE", color=THEME["status_color"], size=13, weight="bold", key="txt-cloud-status")
        self.sync_cloud_btn = ft.ElevatedButton("SINCRONIZAR NUVEM", icon=ft.Icons.CLOUD_SYNC, bgcolor=THEME["accent_color"], color="black", key="btn-sync-cloud")
        self.sync_cloud_btn.on_click = self.on_sync_cloud_click

        header = ft.Row([
            ft.Text("PROJETO: TRADUÇÃO UNIVERSAL ....", size=20, color=THEME["accent_color"], weight="bold"),
            ft.Row([self.cloud_status_text, self.sync_cloud_btn, self.status_text], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # --- LEFT PANEL: LEARNING MODULE ---
        self.lang_dropdown = ft.Dropdown(
            label="Idioma Alvo",
            options=[ft.dropdown.Option(l) for l in self.get_available_languages()],
            value=self.target_language,
            expand=2
        )
        self.lang_dropdown.on_change = self.on_lang_change

        self.new_lang_input = ft.TextField(hint_text="Criar...", bgcolor="#111", border_color=THEME["border_color"], color="white", text_size=12, expand=1)
        self.add_lang_btn = ft.IconButton(icon=ft.Icons.ADD, icon_color=THEME["accent_color"], tooltip="Adicionar Novo Idioma")
        self.add_lang_btn.on_click = self.add_new_language

        self.vu_bars = [ft.Container(width=6, height=10, bgcolor="#1a1a1a", border_radius=2) for _ in range(16)]
        vu_row = ft.Row(self.vu_bars, alignment=ft.MainAxisAlignment.CENTER, spacing=4)

        # Bulletproof Custom Progress Bar
        self.progress_bar_inner = ft.Container(width=0, height=8, bgcolor=THEME["accent_color"], border_radius=4)
        self.progress_bar_container = ft.Container(
            width=280, height=8, bgcolor="#1a1a1a", border_radius=4, content=self.progress_bar_inner
        )

        self.countdown_text = ft.Text("STATUS: INATIVO", size=10, color="#888888", weight="bold")
        self.play_button = ft.ElevatedButton("OUVIR ÁUDIO CAPTADO", icon=ft.Icons.PLAY_ARROW, bgcolor=THEME["accent_color"], color="black", disabled=True)
        self.play_button.on_click = self.play_last_audio
        self.word_display = ft.Text("NENHUMA", size=36, weight="bold", color=THEME["status_color"], text_align="center")

        self.text_input = ft.TextField(label="Palavra em Português", hint_text="Digite para mapear...", bgcolor="#111", border_color=THEME["border_color"], color="white", text_size=14, key="input-word-key")
        self.text_input.on_submit = self.on_text_submit
        self.text_input.on_change = self.on_text_change
        self.mic_button = ft.IconButton(icon=ft.Icons.MIC, icon_color=THEME["accent_color"], icon_size=24, disabled=True)
        self.mic_button.on_click = self.on_mic_click

        # Custom Container Button to guarantee style updates bypass Flet ElevatedButton bugs
        self.record_alien_btn_text = ft.Text("GRAVAR SOM ALIENÍGENA", color="white", weight="bold", size=13)
        self.record_alien_btn = ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, color="white", size=16), self.record_alien_btn_text], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#ff2a2a", width=260, height=45, border_radius=5, alignment=ft.alignment.center, on_click=self.record_alien_sound_start, ink=True
        )

        self.save_word_button = ft.IconButton(icon=ft.Icons.SAVE, icon_color="green", icon_size=28, disabled=True)
        self.save_word_button.on_click = self.save_word

        left_content = ft.Column([
            ft.Text("MÓDULO DE APRENDIZADO", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            ft.Row([self.lang_dropdown, self.new_lang_input, self.add_lang_btn], spacing=5),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("GRAVAÇÃO E CALIBRAÇÃO", size=10, color="#888", weight="bold"), self.countdown_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    vu_row,
                    self.progress_bar_container
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                height=130, bgcolor="#0e0e0e", border=border_all(1, "#333"), border_radius=5, padding=10
            ),
            ft.Row([self.play_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color="#222"),
            ft.Text("CONCEITO SEMÂNTICO EM FOCO:", size=11, color="#888", weight="bold"),
            ft.Container(content=self.word_display, alignment=ft.alignment.Alignment(0, 0), height=60, bgcolor="#0d0e15", border_radius=5),
            ft.Row([ft.Container(self.text_input, expand=True), self.mic_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color="#222"),
            ft.Text("EMPARELHAR COM SOM ALIENÍGENA (4s):", size=11, color="#888", weight="bold"),
            ft.Row([self.record_alien_btn, self.save_word_button], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        # --- CENTER PANEL: CONVERSATION MODULE ---
        self.chat_container = ft.Container(height=460, bgcolor="#040406", border=border_all(1, "#222"), border_radius=5, padding=10, content=ft.Column([], scroll=ft.ScrollMode.AUTO))
        self.chat_input = ft.TextField(hint_text="Escreva em Português para traduzir...", bgcolor="#111", border_color=THEME["border_color"], color="white", text_size=13, expand=True, key="input-conversation-msg")
        self.chat_input.on_submit = self.on_chat_submit
        self.chat_mic_button = ft.IconButton(icon=ft.Icons.MIC, icon_color=THEME["accent_color"], icon_size=20, disabled=True)
        self.chat_mic_button.on_click = self.on_chat_mic_click
        self.chat_send_button = ft.IconButton(icon=ft.Icons.SEND, icon_color=THEME["accent_color"], icon_size=20, disabled=True)
        self.chat_send_button.on_click = self.on_chat_send_click
        self.alien_mic_btn = ft.IconButton(icon=ft.Icons.SPEAKER_PHONE, icon_color=THEME["status_color"], icon_size=22, disabled=True)
        self.alien_mic_btn.on_click = self.on_alien_mic_click

        right_content = ft.Column([
            ft.Text("CANAL DE DIÁLOGO INTERESPÉCIES", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            self.chat_container,
            ft.Row([self.chat_input, self.chat_mic_button, self.chat_send_button, self.alien_mic_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        ], spacing=8)

        # --- RIGHT PANEL: TELEMETRY ---
        self.backbone_dropdown = ft.Dropdown(label="Backbone Acústico", options=[ft.dropdown.Option("ast"), ft.dropdown.Option("mobilenet")], value=ACOUSTIC_MODEL_BACKBONE, bgcolor="#111", border_color=THEME["border_color"], color="white")
        self.backbone_dropdown.on_change = self.save_config
        self.train_mode_dropdown = ft.Dropdown(label="Ambiente de Treino", options=[ft.dropdown.Option("local"), ft.dropdown.Option("cloud")], value=TRAINING_MODE, bgcolor="#111", border_color=THEME["border_color"], color="white")
        self.train_mode_dropdown.on_change = self.save_config
        
        self.train_button = ft.ElevatedButton("EXECUTAR TREINAMENTO SIAMES", icon=ft.Icons.PLAY_CIRCLE_FILL, bgcolor=THEME["status_color"], color="black", disabled=True)
        self.train_button.on_click = lambda _: self.run_script_in_console("train_siamese.py", ["--epochs", "10"])
        self.sync_button = ft.ElevatedButton("SINCRONIZAR CHROMADB", icon=ft.Icons.SYNC, bgcolor=THEME["accent_color"], color="black", disabled=True)
        self.sync_button.on_click = lambda _: self.run_script_in_console("migrate_to_vector_db.py")

        self.console_column = ft.Column([], scroll=ft.ScrollMode.AUTO, auto_scroll=True)
        console_container = ft.Container(content=self.console_column, height=280, bgcolor="#000000", border=border_all(1, THEME["border_color"]), border_radius=5, padding=8)
        clear_console_btn = ft.IconButton(icon=ft.Icons.DELETE_SWEEP, icon_color="#ff2a2a", icon_size=20)
        clear_console_btn.on_click = self.clear_console

        telemetry_content = ft.Column([
            ft.Text("TELEMETRIA NEURAL & BANCO", color=THEME["accent_color"], size=15, weight="bold"),
            ft.Divider(color=THEME["border_color"], height=1),
            self.backbone_dropdown, self.train_mode_dropdown,
            ft.Row([self.train_button, self.sync_button], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color="#222"),
            ft.Row([ft.Text("TELECONEXÃO MONITOR (LOGS SYSTEM):", size=11, color="#888", weight="bold"), clear_console_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            console_container
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        # MAIN LAYOUT
        self.layout_container = ft.Container(
            content=ft.Column([
                header, ft.Divider(height=2, color=THEME["border_color"]),
                ft.Row([
                    ft.Container(content=left_content, border=border_all(1, THEME["border_color"]), border_radius=6, padding=12, expand=3),
                    ft.Container(content=right_content, border=border_all(1, THEME["border_color"]), border_radius=6, padding=12, expand=4),
                    ft.Container(content=telemetry_content, border=border_all(1, THEME["border_color"]), border_radius=6, padding=12, expand=3)
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            ]),
            padding=15, border=border_all(2, THEME["border_color"]), border_radius=8, bgcolor="#050505", expand=True
        )

    def log_to_console(self, text: str):
        lines = text.splitlines()
        for line in lines:
            if not line.strip(): continue
            color = "#00f0ff"
            if "[OK]" in line or "SUCESSO" in line or "CONCLUÍDO" in line: color = "#00ff00"
            elif "[ERRO]" in line or "FAILED" in line or "Traceback" in line: color = "#ff0000"
            elif "[AVISO]" in line or "WARNING" in line: color = "#ff9000"
            self.console_column.controls.append(ft.Text(line, font_family="monospace", size=10, color=color))
            
        if len(self.console_column.controls) > 150:
            self.console_column.controls = self.console_column.controls[-150:]
        self.page.update()

    def clear_console(self, _e):
        self.console_column.controls.clear()
        self.page.update()

    def save_config(self, _e=None):
        backbone = self.backbone_dropdown.value
        mode = self.train_mode_dropdown.value
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.py"))
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f: content = f.read()
                content = re.sub(r'TRAINING_MODE\s*=\s*["\'][^"\']*["\']', f'TRAINING_MODE = "{mode}"', content)
                content = re.sub(r'ACOUSTIC_MODEL_BACKBONE\s*=\s*["\'][^"\']*["\']', f'ACOUSTIC_MODEL_BACKBONE = "{backbone}"', content)
                with open(config_path, "w", encoding="utf-8") as f: f.write(content)
                self.log_to_console(f"[CONFIG] Atualização salva: BACKBONE={backbone.upper()} | MODO={mode.upper()}\n")
                self.status_text.value = f"[Nuvem] STATUS: PRONTO ({mode.upper()} / {backbone.upper()})"
                self.page.update()
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao escrever config.py: {ex}\n")

    def run_script_in_console(self, script_name: str, args: list = []):
        self.train_button.disabled = True
        self.sync_button.disabled = True
        self.page.update()
        def target():
            try:
                script_path = os.path.join("scripts", script_name)
                self.log_to_console(f"\n[SISTEMA] INICIANDO: python {script_name} {' '.join(args)}\n")
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                process = subprocess.Popen([sys.executable, script_path] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
                for line in iter(process.stdout.readline, ''): self.log_to_console(line)
                process.stdout.close()
                rc = process.wait()
                if rc == 0: self.log_to_console(f"[SISTEMA] OPERAÇÃO CONCLUÍDA COM SUCESSO!\n")
                else: self.log_to_console(f"[SISTEMA] ERRO: OPERAÇÃO FALHOU COM CÓDIGO {rc}\n")
            except Exception as ex:
                self.log_to_console(f"[SISTEMA] FALHA DE INICIALIZAÇÃO DE SUBPROCESSO: {ex}\n")
            finally:
                self.train_button.disabled = False
                self.sync_button.disabled = False
                self.page.update()
        threading.Thread(target=target, daemon=True).start()

    def add_message_to_chat(self, sender: str, message: str = "", is_user: bool = True, spans: list = None):
        bubble_color = "#121420" if is_user else "#0f0e0d"
        border_color = THEME["accent_color"] if is_user else THEME["status_color"]
        if spans: text_control = ft.Text(spans=spans, size=13)
        else: text_control = ft.Text(message, size=13, color="white" if is_user else THEME["status_color"])
        message_bubble = ft.Container(
            content=ft.Column([ft.Text(sender, size=10, color="#888888", weight="bold"), text_control], spacing=2),
            bgcolor=bubble_color, border=border_all(1, border_color), padding=9, border_radius=8, margin=ft.margin.Margin(bottom=5), width=280
        )
        self.chat_container.content.controls.append(ft.Row([message_bubble], alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START))
        self.page.update()

    def on_lang_change(self, _e):
        self.target_language = self.lang_dropdown.value
        self.log_to_console(f"[SISTEMA] Idioma alvo alterado para: '{self.target_language.upper()}'\n")

    def add_new_language(self, _e):
        new_lang = self.new_lang_input.value.strip().lower()
        if new_lang:
            os.makedirs(f"linguagens/{new_lang}", exist_ok=True)
            self.target_language = new_lang
            self.new_lang_input.value = ""
            self.lang_dropdown.options = [ft.dropdown.Option(l) for l in self.get_available_languages()]
            self.lang_dropdown.value = new_lang
            self.log_to_console(f"[SISTEMA] Novo idioma criado e selecionado: '{new_lang.upper()}'\n")
            self.page.update()

    def on_text_change(self, _e):
        word = self.text_input.value.strip().upper()
        self.word_display.value = word if word else "NENHUMA"
        self.page.update()

    def on_text_submit(self, _e):
        word = self.text_input.value.strip().upper()
        if word:
            self.word_display.value = word
            self.page.update()

    def on_mic_click(self, _e):
        if self.is_listening: return
        self.is_listening = True
        self.mic_button.icon_color = "#ff0000"
        self.page.update()
        self.log_to_console("[APRENDIZADO] Ouvindo voz humana (3s)...\n")
        threading.Thread(target=self.listen_for_word, daemon=True).start()

    def listen_for_word(self):
        try:
            word = self.translator.listen_and_transcribe(duration=3.0)
            word = word.strip().upper().replace(".", "").replace(",", "").replace("!", "")
            if word:
                self.word_display.value = word
                self.text_input.value = ""
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
        if self.word_display.value in ("NENHUMA", "NÃO DETECTADO", "ERRO") and self.text_input.value.strip():
            self.word_display.value = self.text_input.value.strip().upper()
        word = self.word_display.value.strip()
        if not word or word in ("NENHUMA", "NÃO DETECTADO", "ERRO"):
            self.log_to_console("[AVISO] Defina um conceito em foco antes de gravar o som correspondente!\n")
            return
        if self.is_recording: return

        self.is_recording = True
        self.record_alien_btn.bgcolor = "#888888"
        self.record_alien_btn_text.value = "GRAVANDO SOM (4.0s)..."
        self.progress_bar_inner.width = 0
        self.countdown_text.value = "GRAVANDO: 4.0s"
        self.countdown_text.color = "#ff9000"
        self.page.update()

        self.log_to_console(f"[APRENDIZADO] Gravando grunhido alienígena para '{word}' (4s). Fale ao microfone.\n")
        threading.Thread(target=self.record_alien_sound, daemon=True).start()

    def record_alien_sound(self):
        duration = 4.0
        sample_rate = self.translator.audio_processor.sample_rate
        channels = self.translator.audio_processor.channels
        try:
            # Create a console text control for the text progress bar!
            console_progress = ft.Text("", font_family="monospace", size=10, color="#ff9000")
            self.console_column.controls.append(console_progress)
            self.page.update()
            
            audio_buffer = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='float32')
            
            steps = 40
            sleep_interval = duration / steps
            import random
            for i in range(steps):
                pct = (i + 1) / steps
                remaining = duration - ((i + 1) * sleep_interval)
                
                # GUI updates
                self.record_alien_btn_text.value = f"GRAVANDO ({max(0.0, remaining):.1f}s)..."
                self.countdown_text.value = f"GRAVANDO: {max(0.0, remaining):.1f}s"
                self.progress_bar_inner.width = 280 * pct
                
                # Console ASCII progress bar update
                bar_len = 20
                filled = int(pct * bar_len)
                bar_str = "█" * filled + "-" * (bar_len - filled)
                console_progress.value = f"[GRAVAÇÃO] [{bar_str}] {int(pct*100)}%"
                
                for bar in self.vu_bars:
                    bar.height = random.randint(10, 90)
                    if bar.height > 70: bar.bgcolor = "#ff9000"
                    elif bar.height > 40: bar.bgcolor = "#00f0ff"
                    else: bar.bgcolor = "#0055ff"
                        
                self.page.update()
                time.sleep(sleep_interval)
                
            sd.wait()
            audio = audio_buffer.flatten()
            max_val = np.max(np.abs(audio))
            if max_val > 0: audio = audio / max_val
            self.recorded_alien_audio = audio
            
            self.play_button.disabled = False
            self.save_word_button.disabled = False
            self.log_to_console(f"[APRENDIZADO] Captação de som finalizada. Valide jogando no reprodutor ou salve a assinatura.\n")
        except Exception as ex:
            self.log_to_console(f"[ERRO] Falha ao capturar som alienígena: {ex}\n")
        finally:
            self.is_recording = False
            self.progress_bar_inner.width = 0
            self.countdown_text.value = "STATUS: INATIVO"
            self.countdown_text.color = "#888888"
            self.record_alien_btn.bgcolor = "#ff2a2a"
            self.record_alien_btn_text.value = "GRAVAR SOM ALIENÍGENA"
            for bar in self.vu_bars:
                bar.height = 10
                bar.bgcolor = "#1a1a1a"
            self.page.update()

    def play_last_audio(self, _e):
        if self.recorded_alien_audio is None: return
        self.play_button.disabled = True
        self.page.update()
        def play_task():
            self.is_playing_audio = True
            playback_duration = len(self.recorded_alien_audio) / self.translator.audio_processor.sample_rate
            threading.Thread(target=self.animate_playback, args=(playback_duration,), daemon=True).start()
            try:
                device_info = sd.query_devices(sd.default.device[1])
                device_name = device_info['name'] if device_info else 'Desconhecido'
                self.log_to_console(f"[SISTEMA] Reproduzindo áudio na saída: {device_name}\n")
                sd.play(self.recorded_alien_audio, self.translator.audio_processor.sample_rate)
                sd.wait()
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao reproduzir áudio: {ex}\n")
            finally:
                self.is_playing_audio = False
                self.play_button.disabled = False
                self.page.update()
        threading.Thread(target=play_task, daemon=True).start()

    def animate_playback(self, duration: float):
        import random
        steps = int(duration / 0.1)
        if steps == 0: steps = 10
        sleep_interval = duration / steps
        self.countdown_text.value = "REPRODUZINDO"
        self.countdown_text.color = "#00ff00"
        for _ in range(steps):
            if not self.is_playing_audio: break
            for bar in self.vu_bars:
                bar.height = random.randint(10, 60)
                bar.bgcolor = THEME["accent_color"]
            self.page.update()
            time.sleep(sleep_interval)
        for bar in self.vu_bars:
            bar.height = 10
            bar.bgcolor = "#1a1a1a"
        self.countdown_text.value = "STATUS: INATIVO"
        self.countdown_text.color = "#888888"
        self.page.update()

    def save_word(self, _e):
        word = self.word_display.value.strip()
        if not word or self.recorded_alien_audio is None: return
        self.save_word_button.disabled = True
        self.page.update()
        try:
            self.log_to_console(f"[APRENDIZADO] Registrando '{word}' nas bases locais para o idioma '{self.target_language.upper()}'...\n")
            filepath = self.translator.audio_processor.save_audio(self.recorded_alien_audio, word, self.target_language)
            self.translator.db.add_word(self.target_language, word, filepath)
            signature = self.translator.audio_processor.extract_features(self.recorded_alien_audio)
            self.translator.vdb.add_audio_signature(word=word, language=self.target_language, embedding=signature.tolist(), audio_path=filepath)
            self.log_to_console(f"[SUCESSO] '{word}' registrada com sucesso nas bases física, SQLite e ChromaDB!\n")
            self.add_message_to_chat("Sistema", f"Novo emparelhamento indexado: '{word}' -> {self.target_language.upper()}", is_user=False)
            self.word_display.value = "NENHUMA"
            self.recorded_alien_audio = None
            self.play_button.disabled = True
            self.text_input.value = ""
        except Exception as ex:
            self.log_to_console(f"[ERRO] Falha ao salvar palavra: {ex}\n")
        finally:
            self.save_word_button.disabled = True
            self.page.update()

    def on_chat_submit(self, _e):
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()

    def on_chat_mic_click(self, _e):
        if self.is_listening: return
        self.is_listening = True
        self.chat_mic_button.icon_color = "#ff0000"
        self.page.update()
        self.log_to_console("[CONVERSA] Gravando fala humana para tradução (5s)...\n")
        def run():
            try:
                message = self.translator.listen_and_transcribe(duration=5.0)
                message = message.strip()
                if message: self.process_message(message, is_user=True)
            except Exception as ex:
                self.log_to_console(f"[ERRO] Erro na gravação do chat: {ex}\n")
            finally:
                self.is_listening = False
                self.chat_mic_button.icon_color = THEME["accent_color"]
                self.page.update()
        threading.Thread(target=run, daemon=True).start()

    def on_chat_send_click(self, _e):
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()

    def on_alien_mic_click(self, _e):
        if self.is_recording: return
        self.is_recording = True
        self.alien_mic_btn.icon_color = "#ff0000"
        self.page.update()
        self.log_to_console("[CONVERSA] Capturando som extraterrestre (4s)...\n")
        threading.Thread(target=self.listen_and_translate_alien_audio, daemon=True).start()

    def listen_and_translate_alien_audio(self):
        try:
            console_progress = ft.Text("", font_family="monospace", size=10, color="#ff9000")
            self.console_column.controls.append(console_progress)
            self.page.update()
            
            duration = 4.0
            sample_rate = self.translator.audio_processor.sample_rate
            audio_buffer = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            steps = 40
            sleep_interval = duration / steps
            import random
            for i in range(steps):
                pct = (i + 1) / steps
                bar_len = 20
                filled = int(pct * bar_len)
                bar_str = "█" * filled + "-" * (bar_len - filled)
                console_progress.value = f"[CAPTURA ALIEN] [{bar_str}] {int(pct*100)}%"
                self.page.update()
                time.sleep(sleep_interval)
                
            sd.wait()
            audio_data = audio_buffer.flatten()
            self.is_recording = False
            self.log_to_console("[CONVERSA] Extraindo assinatura acústica e buscando no ChromaDB...\n")
            result = self.translator.translate_alien_audio(audio_data)
            if result:
                self.log_to_console(f"[CONVERSA] Tradução encontrada: {result}\n")
                self.add_message_to_chat("Ser Extraterrestre (Som)", f"Tradução: {result}", is_user=False)
            else:
                self.log_to_console("[CONVERSA] Nenhuma tradução correspondente com score mínimo.\n")
                self.add_message_to_chat("Ser Extraterrestre (Som)", is_user=False, spans=[ft.TextSpan("[SOM NÃO IDENTIFICADO / LACUNA NO ESPAÇO LATENTE]", style=ft.TextStyle(color="red", weight="bold"))])
        except Exception as ex:
            self.log_to_console(f"[ERRO] Erro na tradução acústica: {ex}\n")
        finally:
            self.is_recording = False
            self.alien_mic_btn.icon_color = THEME["status_color"]
            self.page.update()

    def process_message(self, message: str, is_user: bool):
        if not is_user: return
        self.add_message_to_chat("Você", message, is_user=True)
        words = message.upper().split()
        clean_words = [ ''.join(c for c in w if c.isalnum()) for w in words ]
        clean_words = [ cw for cw in clean_words if cw ]
        if not clean_words: return
        spans = []
        audio_files_to_play = []
        for word in clean_words:
            audio_path = self.translator.db.get_word_audio(self.target_language, word)
            if audio_path and os.path.exists(audio_path):
                spans.append(ft.TextSpan(f"{word} ", style=ft.TextStyle(color=THEME["status_color"], weight="bold")))
                audio_files_to_play.append(audio_path)
            else:
                spans.append(ft.TextSpan(f"[{word}] ", style=ft.TextStyle(color="red", weight="bold")))
        def alien_response_task():
            time.sleep(0.5)
            self.add_message_to_chat("Ser Extraterrestre", is_user=False, spans=spans)
            if audio_files_to_play: self.play_sequenced_audio(audio_files_to_play)
        threading.Thread(target=alien_response_task, daemon=True).start()

    def play_sequenced_audio(self, paths: list):
        self.is_playing_audio = True
        import librosa
        for path in paths:
            try:
                audio, sr = librosa.load(path, sr=22050)
                playback_duration = len(audio) / sr
                threading.Thread(target=self.animate_playback, args=(playback_duration,), daemon=True).start()
                max_val = np.max(np.abs(audio))
                if max_val > 0: audio = audio / max_val
                
                device_info = sd.query_devices(sd.default.device[1])
                device_name = device_info['name'] if device_info else 'Desconhecido'
                self.log_to_console(f"[SISTEMA] Playback de sequência em: {device_name}\n")
                
                sd.play(audio, sr)
                sd.wait()
                time.sleep(0.15)
            except Exception as ex:
                self.log_to_console(f"[ERRO] Falha ao reproduzir áudio de '{path}': {ex}\n")
        self.is_playing_audio = False
        self.page.update()

def main(page: ft.Page):
    app = TranslatorApp()
    app.main(page)

if __name__ == "__main__":
    if hasattr(ft, 'run'):
        ft.run(main)
    else:
        ft.app(target=main)
