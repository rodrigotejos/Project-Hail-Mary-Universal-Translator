# Project: Universal Translator | Projeto: Tradutor Universal

[![Language: English](https://img.shields.io/badge/lang-en-blue.svg)](#english)
[![Linguagem: Português](https://img.shields.io/badge/lang-pt--br-green.svg)](#português)

---

<a name="english"></a>
## 🌍 English Version

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

### 1. Project Overview
The **Universal Translator Project** is a software system designed to learn, catalog, and translate unknown languages in real-time using AI and Digital Signal Processing.

### 2. New Features (Current Stage)
- **AI Core**: Integrated `faster-whisper` (Small model) for high-accuracy Speech-to-Text.
- **Audio Engine**: Real-time recording, automatic normalization, and 16kHz resampling for optimal AI processing.
- **Persistence**: SQLite database (`TranslatorDB`) to store vocabulary, language mappings, and audio file paths.
- **Integrated Tests**: Full test suite covering audio processing and translation logic.

### 3. How to Run

#### Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

#### Running Tests
To ensure everything is working correctly:
- Run all tests: `python -m pytest`
- Test audio engine: `python tests/test_audio_process.py`
- Test translation engine: `python tests/test_translator.py`

#### Demonstration Scripts
- **Record & Transcribe**: `python scripts/demo_recording.py` (Tests your mic and Whisper).
- **Learn Vocabulary**: `python scripts/learn_vocabulary.py` (Learn new words and save to DB).
- **List Vocabulary**: `python scripts/list_vocabulary.py` (See what's stored in SQLite).
- **Real-time Translation**: `python scripts/translate_audio.py` (Identify spoken words from the learned database).

---

<a name="português"></a>
## 🇧🇷 Versão em Português

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

### 1. Visão Geral do Projeto
O **Projeto Tradução Universal** é um sistema projetado para aprender, catalogar e traduzir idiomas desconhecidos em tempo real usando IA e processamento digital de sinais.

### 2. Novas Funcionalidades (Estágio Atual)
- **IA Core**: Integração com `faster-whisper` (modelo Small) para transcrição de alta precisão.
- **Motor de Áudio**: Gravação em tempo real, normalização automática e resampling para 16kHz.
- **Persistência**: Banco de dados SQLite (`TranslatorDB`) para salvar vocabulário e caminhos de áudio.
- **Testes Integrados**: Suite de testes completa cobrindo o motor de áudio e a lógica do tradutor.

### 3. Como Executar

#### Configuração
1. Crie o ambiente virtual: `python -m venv venv`
2. Ative o ambiente: `.\venv\Scripts\activate`
3. Instale as dependências: `pip install -r requirements.txt`

#### Executando Testes
Para garantir que tudo está funcionando:
- Rodar todos os testes: `python -m pytest`
- Testar motor de áudio: `python tests/test_audio_process.py`
- Testar motor do tradutor: `python tests/test_translator.py`

#### Scripts de Demonstração
- **Gravação e Transcrição**: `python scripts/demo_recording.py` (Testa seu mic e o Whisper).
- **Aprender Vocabulário**: `python scripts/learn_vocabulary.py` (Ensina novas palavras e salva no banco).
- **Listar Vocabulário**: `python scripts/list_vocabulary.py` (Ver o que está salvo no SQLite).
- **Tradução em Tempo Real**: `python scripts/translate_audio.py` (Identifica palavras faladas comparando com o banco).

---

[Conteúdo original do roadmap e UI mantido abaixo...]