"""
Demonstration script for recording and transcribing audio.
"""
import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine.translator import UniversalTranslator  # pylint: disable=wrong-import-position

def main():
    """Main execution function for the demo recording script."""
    print("=== INICIANDO DEMO DE GRAVAÇÃO E TRANSCRIÇÃO ===")

    # Inicializa o tradutor (isso pode levar alguns segundos para carregar o modelo)
    print("Carregando modelo Whisper (small)...")
    translator = UniversalTranslator(model_size="small")

    # Define a pasta de teste
    test_folder = "teste"
    os.makedirs(os.path.join("linguagens", test_folder), exist_ok=True)

    print("\nPREPARE-SE: Grave algo em PORTUGUÊS em 3 segundos...")
    input("Pressione ENTER para começar a gravar...")

    try:
        # 1. Gravar áudio
        audio_data = translator.audio_processor.record_audio(duration=4.0)

        # 2. Salvar o áudio para conferência
        filename = "gravacao_manual"
        filepath = translator.audio_processor.save_audio(audio_data, filename, test_folder)
        print(f"\n[OK] Áudio salvo em: {filepath}")

        # 3. Transcrever
        print("Transcrevendo...")
        transcription = translator.stt_manager.transcribe(audio_data, language="pt")

        print("\n" + "="*30)
        print(f"VOCÊ DISSE: {transcription}")
        print("="*30)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n[ERRO] Ocorreu um problema: {e}")

if __name__ == "__main__":
    main()
