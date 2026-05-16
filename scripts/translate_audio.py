import os
import sys
import numpy as np

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine.translator import UniversalTranslator

def main():
    print("=== MÓDULO DE TRADUÇÃO EM TEMPO REAL ===")
    
    # Inicializa o tradutor
    print("Iniciando motores de comparação...")
    translator = UniversalTranslator()
    
    # Pergunta qual idioma estamos ouvindo
    target_lang = input("\nQual idioma você vai falar? (padrão: ingles): ") or "ingles"
    translator.target_language = target_lang
    
    print(f"\n[SISTEMA ATIVO] Ouvindo idioma: {target_lang.upper()}")
    print("Dica: Fale uma palavra que você já ensinou ao sistema.")
    input("Pressione ENTER para começar a ouvir...")
    
    try:
        # 1. Grava o áudio do usuário (o som 'desconhecido')
        audio_data = translator.audio_processor.record_audio(duration=4.0)
        
        # 2. Tenta traduzir comparando assinaturas de áudio
        print("Analisando frequências e buscando no banco de dados...")
        result = translator.translate_alien_audio(audio_data)
        
        print("\n" + "="*40)
        if result:
            print(f"TRADUÇÃO ENCONTRADA: {result}")
            print(f"Significado em Português: {result}")
        else:
            print("TRADUÇÃO NÃO ENCONTRADA.")
            print("Dica: Verifique se você já ensinou essa palavra no script de aprendizado.")
        print("="*40)
        
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um problema: {e}")

if __name__ == "__main__":
    main()
