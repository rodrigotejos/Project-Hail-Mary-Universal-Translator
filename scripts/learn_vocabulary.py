"""
Vocabulary learning module for Universal Translator.
"""
import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine.translator import UniversalTranslator  # pylint: disable=wrong-import-position

def main():
    """Main execution function for learning vocabulary."""
    print("=== MÓDULO DE APRENDIZADO DO TRADUTOR UNIVERSAL ===")

    # Inicializa o tradutor com o modelo 'small'
    print("Iniciando motores e carregando Whisper (small)...")
    translator = UniversalTranslator(model_size="small")

    # Define o idioma alvo (ex: 'ingles')
    target_lang = input("\nDigite o nome do idioma que quer ensinar (padrão: ingles): ") or "ingles"

    while True:
        print("\n" + "="*50)
        print("PASSO 1: Fale a palavra em PORTUGUÊS que quer ensinar.")
        input("Pressione ENTER para gravar sua voz...")

        try:
            # Captura a palavra humana
            human_word = translator.listen_and_transcribe(duration=3.0)
            human_word = human_word.strip().upper().replace(".", "")

            if not human_word:
                print("[!] Não entendi nada. Tente falar mais perto do microfone.")
                continue

            print(f"\n[OK] Entendi a palavra: {human_word}")

            print(f"\nPASSO 2: Agora faça o som em '{target_lang.upper()}' para '{human_word}'.")
            input(f"Pressione ENTER para gravar o som de '{human_word}'...")

            # Grava e salva no banco
            filepath = translator.learn_word(human_word, duration=4.0, language=target_lang)

            print("\n[SUCESSO] Aprendizado concluído!")
            print(f"Palavra: {human_word} -> Áudio: {filepath}")

            # Pergunta se quer continuar
            cont = input("\nDeseja ensinar outra palavra? (s/n): ")
            if cont.lower() != 's':
                break

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n[ERRO] Ocorreu um problema: {e}")
            break

    print("\nEncerrando módulo de aprendizado. Até a próxima!")

if __name__ == "__main__":
    main()
