import flet as ft
import threading
import time
from ui.theme import THEME, get_theme
from ui.layout import create_main_layout
from engine.translator import UniversalTranslator
import os

class TranslatorApp:
    def __init__(self):
        self.page = None
        self.translator = UniversalTranslator(model_size="small")
        self.current_language = "pt"  # Default to Portuguese
        self.target_language = "clingo"  # Default alien language
        self.is_listening = False
        self.is_recording = False
        
        # Ensure directories exist
        os.makedirs("linguagens", exist_ok=True)
        for lang in [self.current_language, self.target_language]:
            os.makedirs(f"linguagens/{lang}", exist_ok=True)
    
    def main(self, page: ft.Page):
        self.page = page
        page.title = "PROJECT: UNIVERSAL TRANSLATION"
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#050505"
        page.padding = 20
        
        # Create layout
        self.layout_container = ft.Container(content=self.create_main_layout())
        page.add(self.layout_container)
        page.update()
    
    def create_main_layout(self):
        # Status indicators
        self.status_text = ft.Text(
            "[Cloud] STATUS: OFFLINE SOMENTE", 
            color=THEME["status_color"],
            size=14
        )
        
        # Header
        header = ft.Row([
            ft.Text("PROJETO: TRADUÇÃO UNIVERSAL ....", size=20, color=THEME["accent_color"]),
            self.status_text
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Learning Module
        self.learning_text = ft.Text("MÓDULO DE APRENDIZADO", color=THEME["accent_color"], size=16, weight="bold")
        self.waveform_container = ft.Container(
            height=100, 
            bgcolor="#1a1a1a", 
            border_radius=5,
            content=ft.Text("ÁUDIO CAPTADO", color="#666", size=12, text_align="center")
        )
        self.play_button = ft.ElevatedButton(
            "OUVIR ÁUDIO CAPTADO", 
            bgcolor=THEME["accent_color"], 
            color="black",
            disabled=True,
            on_click=self.play_last_audio
        )
        self.input_label = ft.Text("ENTRADA DE DADOS: PORTUGUÊS", color="white", size=14)
        self.word_display = ft.Text(
            "MÚSICA", 
            size=40, 
            weight="bold", 
            color="#ff9000",
            text_align="center"
        )
        self.text_input = ft.TextField(
            hint_text="digite a palavra...",
            bgcolor="#1a1a1a",
            border_color=THEME["border_color"],
            color="white",
            on_submit=self.on_text_submit
        )
        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            icon_color=THEME["accent_color"],
            icon_size=24,
            tooltip="Falar",
            on_click=self.on_mic_click
        )
        self.confirm_button = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE,
            icon_color="green",
            icon_size=24,
            tooltip="Confirmar",
            on_click=self.on_confirm_click,
            disabled=True
        )
        
        # Learning module content
        left_content = ft.Column([
            self.learning_text,
            self.waveform_container,
            self.play_button,
            ft.Divider(color=THEME["border_color"]),
            self.input_label,
            self.word_display,
            self.text_input,
            ft.Row([
                self.mic_button,
                ft.Text("(Falar)", color="white", size=12),
                self.confirm_button,
                ft.Text("(Confirmar)", color="white", size=12)
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10)
        
        # Conversation Module
        self.conversation_text = ft.Text("MÓDULO DE CONVERSAÇÃO", color=THEME["accent_color"], size=16, weight="bold")
        self.chat_container = ft.Container(
            height=300,
            bgcolor="#0a0a0a",
            border_radius=5,
            padding=10,
            content=ft.Column([], scroll=ft.ScrollMode.AUTO)
        )
        self.chat_input = ft.TextField(
            hint_text="escrever mensagem...",
            bgcolor="#1a1a1a",
            border_color=THEME["border_color"],
            color="white",
            on_submit=self.on_chat_submit
        )
        self.chat_mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            icon_color=THEME["accent_color"],
            icon_size=20,
            tooltip="Falar",
            on_click=self.on_chat_mic_click
        )
        self.chat_send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=THEME["accent_color"],
            icon_size=20,
            tooltip="Enviar",
            on_click=self.on_chat_send_click
        )
        
        # Conversation module content
        right_content = ft.Column([
            self.conversation_text,
            self.chat_container,
            ft.Divider(color=THEME["border_color"]),
            self.chat_input,
            ft.Row([
                self.chat_mic_button,
                ft.Text("(Falar)", color="white", size=12),
                self.chat_send_button,
                ft.Text("(Enviar)", color="white", size=12)
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10)
        
        # Main layout
        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=2, color=THEME["border_color"]),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Divider(color=THEME["border_color"]),
                            left_content
                        ]),
                        border=ft.border.all(1, THEME["border_color"]),
                        border_radius=5,
                        padding=10,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Divider(color=THEME["border_color"]),
                            right_content
                        ]),
                        border=ft.border.all(1, THEME["border_color"]),
                        border_radius=5,
                        padding=10,
                        expand=True
                    )
                ], spacing=10)
            ]),
            padding=20,
            border=ft.border.all(2, THEME["border_color"]),
            border_radius=10,
            bgcolor="#050505"
        )
    
    def add_message_to_chat(self, sender: str, message: str, is_user: bool = True):
        """Add a message to the chat container"""
        # Create message bubble
        bubble_color = "#1a1a1a" if is_user else "#0a0a0a"
        text_color = "white" if is_user else "#ff9000"
        
        message_bubble = ft.Container(
            content=ft.Column([
                ft.Text(sender, size=12, color=THEME["status_color"]),
                ft.Text(message, size=14, color=text_color)
            ], spacing=2),
            bgcolor=bubble_color,
            padding=8,
            border_radius=10,
            margin=ft.margin.only(bottom=5)
        )
        
        # Add to chat container
        chat_column = self.chat_container.content
        chat_column.controls.append(message_bubble)
        
        # Scroll to bottom
        self.chat_container.content = ft.Column(
            chat_column.controls,
            scroll=ft.ScrollMode.AUTO
        )
        
        self.page.update()
    
    def on_text_submit(self, e):
        """Handle text input submission"""
        word = self.text_input.value.strip().upper()
        if word:
            self.word_display.value = word
            self.confirm_button.disabled = False
            self.text_input.value = ""
            self.page.update()
    
    def on_mic_click(self, e):
        """Handle microphone button click for learning"""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.mic_button.icon_color = "#ff0000"  # Red when recording
        self.page.update()
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.listen_for_word, daemon=True).start()
    
    def listen_for_word(self):
        """Listen for spoken word"""
        try:
            # Usa o tradutor para gravar e transcrever
            word = self.translator.listen_and_transcribe(duration=3.0)
            word = word.strip().upper()
            
            # Update UI
            if word:
                self.word_display.value = word
                self.confirm_button.disabled = False
            else:
                self.word_display.value = "NÃO DETECTADO"
            
        except Exception as ex:
            print(f"Erro na escuta: {ex}")
            self.word_display.value = "ERRO"
        finally:
            self.is_listening = False
            self.mic_button.icon_color = THEME["accent_color"]
            self.page.update()
    
    def on_confirm_click(self, e):
        """Handle confirm button click"""
        word = self.word_display.value.strip()
        if not word or word == "NÃO DETECTADO" or word == "ERRO":
            return
            
        self.is_recording = True
        self.confirm_button.icon_color = "#ff0000"  # Red when recording
        self.page.update()
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.record_alien_sound, args=(word,), daemon=True).start()
    
    def record_alien_sound(self, word: str):
        """Record alien sound for the given word"""
        try:
            # Record audio (wait for alien to make sound)
            audio = self.translator.audio_processor.record_audio(duration=5.0)
            
            # Save audio file
            filepath = self.translator.audio_processor.save_audio(audio, word, self.target_language)
            
            # Update UI
            self.play_button.disabled = False
            self.last_audio_file = filepath
            
            # Add to conversation
            self.add_message_to_chat(
                "Você", 
                f"Aprendi: {word}", 
                is_user=True
            )
            
        except Exception as ex:
            print(f"Erro na gravação: {ex}")
            self.add_message_to_chat(
                "Sistema", 
                f"Erro ao gravar som para '{word}'", 
                is_user=False
            )
        finally:
            self.is_recording = False
            self.confirm_button.icon_color = "green"
            self.page.update()
    
    def play_last_audio(self, e):
        """Play the last recorded audio"""
        if hasattr(self, 'last_audio_file') and os.path.exists(self.last_audio_file):
            try:
                import playsound
                playsound.playsound(self.last_audio_file, block=False)
            except Exception as ex:
                print(f"Erro ao reproduzir áudio: {ex}")
                self.add_message_to_chat(
                    "Sistema", 
                    "Erro ao reproduzir áudio", 
                    is_user=False
                )
    
    def on_chat_submit(self, e):
        """Handle chat input submission"""
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()
    
    def on_chat_mic_click(self, e):
        """Handle chat microphone button click"""
        if self.is_listening:
            return
            
        self.is_listening = True
        self.chat_mic_button.icon_color = "#ff0000"  # Red when recording
        self.page.update()
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.listen_for_chat_message, daemon=True).start()
    
    def listen_for_chat_message(self):
        """Listen for spoken chat message"""
        try:
            # Usa o tradutor para ouvir a mensagem de chat
            message = self.translator.listen_and_transcribe(duration=5.0)
            message = message.strip()
            
            # Process message
            if message:
                self.process_message(message, is_user=True)
            
        except Exception as ex:
            print(f"Erro na escuta de chat: {ex}")
            self.add_message_to_chat(
                "Sistema", 
                "Erro ao processar fala", 
                is_user=False
            )
        finally:
            self.is_listening = False
            self.chat_mic_button.icon_color = THEME["accent_color"]
            self.page.update()
    
    def on_chat_send_click(self, e):
        """Handle chat send button click"""
        message = self.chat_input.value.strip()
        if message:
            self.process_message(message, is_user=True)
            self.chat_input.value = ""
            self.page.update()
    
    def process_message(self, message: str, is_user: bool):
        """Process a message (either from user or to be translated)"""
        # Add user message to chat
        if is_user:
            self.add_message_to_chat("Você", message, is_user=True)
        
        # Simple word-by-word translation simulation
        words = message.upper().split()
        translated_words = []
        
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum())
            
            # Tenta encontrar tradução usando o tradutor
            result = self.translator.audio_processor.find_best_match(
                np.array([]),  # Sem áudio, apenas checando banco
                self.target_language,
                threshold=0.1
            )
            
            if result:
                translated_word, confidence = result
                translated_words.append(translated_word)
            else:
                # Word not found - mark as unknown
                translated_words.append(f"[{word}]")
        
        # Create translated message
        translated_message = ' '.join(translated_words)
        
        # Add alien response to chat (with delay to simulate processing)
        def add_alien_response():
            time.sleep(0.5)  # Simulate processing delay
            self.add_message_to_chat("Alienígena", translated_message, is_user=False)
        
        threading.Thread(target=add_alien_response, daemon=True).start()


def main(page: ft.Page):
    app = TranslatorApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)
