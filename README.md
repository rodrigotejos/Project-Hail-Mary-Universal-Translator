# Project: Universal Translator | Projeto: Tradutor Universal

[![Language: English](https://img.shields.io/badge/lang-en-blue.svg)](#english)
[![Linguagem: Português](https://img.shields.io/badge/lang-pt--br-green.svg)](#português)

---

<a name="english"></a>
## 🌍 English Version

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

### 1. Project Overview
The **Universal Translator Project** (inspired by the interspecies communication concept in the book/movie *Project Hail Mary*) is a software system designed to learn, catalog, and translate unknown languages (alien or uncatalogued) in real-time.

*   **Premise:** The system starts from zero. It learns by mapping words from our base language to audio signatures emitted by the other being.
*   **Launch Phase (V1):** Local-first (100% offline), focusing on Portuguese as the base language, with an architecture ready for a "Pivot Language" system in future updates.

### 2. Data Structure & Storage
V1 storage is based on a simple and efficient local file system acting as a Key-Value dictionary.

*   **Root Directory:** `/linguagens/`
*   **Subdirectories:** One folder per language (e.g., `/linguagens/ingles/`, `/linguagens/clingo/`).
*   **Audio Files:** Recorded sounds are saved within the corresponding language folder.
*   **Naming Convention (V1):** The filename is exactly the translated word in the base language (Portuguese).
*   **Format:** `.wav` or `.flac` (lossless formats to facilitate frequency analysis).
*   **Example:** For the word "música" (music), the sound emitted by the being will be saved as `/linguagens/clingo/musica.wav`.

### 3. User Interface (UI)
The interface features a Sci-Fi aesthetic (starship console) divided into main logical blocks.

#### 3.1. Header
*   **Title:** PROJECT: UNIVERSAL TRANSLATION...
*   **Language Controls:** Dropdown to select input language (Human) and target language (Alien). Button: `[ + Create New Language ]`.
*   **Connection Status:** Cloud indicator: `[Cloud] Status: OFFLINE ONLY` (Gray/disabled in V1; Green/Red in V2).

#### 3.2. Left Panel: Learning Module
Split into two vertical sections (Top and Bottom) to create new word pairs.
*   **Bottom Area (Our Input):** Text input and microphone button (transcription). The user types/speaks a word (e.g., "MÚSICA"), which appears highlighted in large text.
*   **Top Area (Alien Capture):** "Record Audio" button. The system waits for external audio and automatically detects silence to end recording.
*   **Validation:** After recording, the file is saved (using the large text as filename), and a `[ ▶ Listen ]` button appears for validation.

#### 3.3. Right Panel: Conversation Module
Chatbot interface displaying the full conversation history.
*   **Chat Area:** Message bubbles (You vs. Alien).
*   **Missing Words Logic:** If a word/sound is not in the database, it is highlighted in **red**. Clicking it sends it automatically to the Learning Module.
*   **Bottom Bar:** Text input with `[Enter]` and `[Microphone]` buttons.

### 4. Internal Architecture
Independent modules orchestrated by a General Manager.

*   **General Manager (Orchestrator):** Decides flows between input (text/audio) and states (Chatting vs. Learning).
*   **Transcription & Indexing:** Converts user speech to text. This text serves as the "key" (filename) for database lookups.
*   **Audio Analyzer (The "Shazam"):** Listens to the alien. Slices continuous audio into clips based on silence/peaks and compares "audio signatures" (spectrograms) with saved files.
*   **Conversation Manager:** Handles Outgoing (Us -> Them) and Incoming (Them -> Us) flows, identifying known/missing words and sequencing audio playback.
*   **Learning Manager:** Processes user string + raw alien audio, applies noise cleaning, and saves the file.

### 5. Exception Flows & Critical Features
*   **Partial Transmission (Missing Words):** If a sentence contains an unlearned word, communication continues. Known words are played; missing ones are ignored in audio but flagged in red in the chat.
*   **Intelligent Recording:** Automatic silence detection (Threshold) ends and saves recordings after X milliseconds of silence.

### 6. Future Roadmap
*   **V1.5: Pivot Language Support:** To avoid recreating databases for every human language (e.g., French vs. Portuguese), the system will use a base indexer (e.g., English). "Olá" translates to the key "hello", saving `hello.wav`.
*   **V2.0: Cloud Collaboration:** Activation of the online module to sync local audio databases with cloud storage (S3/Firebase), allowing collaborative universal learning.

---

<a name="português"></a>
## 🇧🇷 Versão em Português

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

### 1. Visão Geral do Projeto
O **Projeto Tradução Universal** (inspirado no conceito de comunicação interespécies do livro/filme *Project Hail Mary*) é um sistema de software projetado para aprender, catalogar e traduzir em tempo real um idioma desconhecido (alienígena ou não catalogado).

*   **Premise:** O sistema parte do zero. Ele aprende mapeando palavras do nosso idioma base para assinaturas de áudio emitidas pelo outro ser.
*   **Fase de Lançamento (V1):** O sistema será 100% offline (local-first) e focado em Português como idioma de entrada, mas com a arquitetura preparada para um sistema de "idioma pivô" em atualizações futuras.

### 2. Estrutura de Dados e Armazenamento
O armazenamento de V1 é baseado em um sistema de arquivos local simples e eficiente, atuando como um dicionário de chave-valor (De/Para).

*   **Diretório Raiz:** `/linguagens/`
*   **Subdiretórios:** Uma pasta para cada idioma (ex: `/linguagens/ingles/`, `/linguagens/clingo/`).
*   **Arquivos de Áudio:** Os sons gravados do outro ser serão salvos dentro da pasta do idioma correspondente.
*   **Regra de Nomenclatura (V1):** O nome do arquivo será exatamente a palavra traduzida no idioma base (Português).
*   **Formato:** `.wav` ou `.flac` (formatos sem perda para facilitar a análise de frequência).
*   **Exemplo:** Para a palavra "música", o som emitido pelo ser será salvo como `/linguagens/clingo/musica.wav`.

### 3. Interface do Usuário (UI)
A interface possui uma estética Sci-Fi (painel de nave) e é dividida em blocos lógicos principais.

#### 3.1. Barra Superior (Header)
*   **Título:** PROJETO: TRADUÇÃO UNIVERSAL ...
*   **Controles de Idioma:** Dropdown para selecionar a linguagem de entrada (Humana) e a linguagem alvo (Alienígena). Botão `[ + Criar Nova Linguagem ]`.
*   **Status de Conexão:** Indicador de nuvem escrito `[Nuvem] Status: OFFLINE SOMENTE` (cinza/desativado na V1; verde/vermelho na V2).

#### 3.2. Painel Esquerdo: MÓDULO DE APRENDIZADO
Dividido em duas seções verticais (Cima e Baixo) para criar novos pares de palavras.
*   **Área Inferior (Nossa Entrada):** Input de texto e um botão de microfone (transcrição). O usuário digita ou fala a palavra (ex: "MÚSICA"), que aparece em destaque central.
*   **Área Superior (Captura do Outro Ser):** Botão "Gravar Áudio do Outro Ser". O sistema detecta automaticamente o silêncio para encerrar a gravação.
*   **Validação:** Após a gravação, o arquivo é salvo e surge um botão `[ ▶ Ouvir Áudio Captado ]` para validação.

#### 3.3. Painel Direito: MÓDULO DE CONVERSAÇÃO
Interface em formato de Chatbot que exibe o histórico completo.
*   **Área de Chat:** Balões de conversa (Você vs. Ser Extraterrestre).
*   **Lógica de Palavras Desconhecidas:** Se o sistema identificar uma palavra/som que não está no banco, ela ficará em **vermelho**. Clicar nela a envia para o Módulo de Aprendizado.
*   **Entrada de Dados:** Input de texto com botão de `[Enter]` e `[Microphone]`.

### 4. Arquitetura de Módulos Internos
Módulos independentes orquestrados por um Gerenciador Geral.

*   **Gerenciador Geral (Orquestrador):** Controla os inputs e a alternância entre "Conversando" e "Aprendendo".
*   **Módulo de Transcrição e Indexação:** Converte a fala do usuário em texto, usado como "chave" (nome do arquivo) no banco de dados.
*   **Módulo Analisador de Áudio (O "Shazam"):** Processa o áudio contínuo do alienígena, fatia em clipes e compara a "assinatura de áudio" com os arquivos salvos.
*   **Gerenciador de Conversação:** Controla os fluxos de Saída (Nós -> Eles) e Entrada (Eles -> Nós), identificando palavras conhecidas e faltantes.
*   **Gerenciador de Aprendizado:** Recebe a string e o áudio bruto, limpa o ruído e salva fisicamente o arquivo.

### 5. Fluxos de Exceção e Features Críticas
*   **Transmissão Parcial (Missing Words):** Se faltar uma palavra, a comunicação continua. O sistema reproduz o que sabe e marca o que falta em vermelho no chat.
*   **Gravação Inteligente:** Detecção de limite de decibéis (Threshold) encerra a gravação automaticamente após silêncio.

### 6. Roadmap Futuro
*   **Versão 1.5: Suporte Multilíngue (Idioma Pivô):** O sistema adotará o Inglês como indexador universal para que dicionários criados em diferentes línguas humanas sejam compatíveis entre si.
*   **Versão 2.0: Colaboração em Nuvem:** Sincronização com nuvem (S3/Firebase) para aprendizado colaborativo universal.