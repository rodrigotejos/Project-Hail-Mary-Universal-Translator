# Project Hail Mary - Tradutor Universal / Universal Translator

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

<details open>
<summary><h2>🇧🇷 Versão em Português (Clique para expandir)</h2></summary>

Um Tradutor Universal autônomo inspirado no livro *Devoradores de Estrelas / Project Hail Mary* (Andy Weir). Este sistema foi projetado para ouvir idiomas desconhecidos (seja fala humana, cliques alienígenas, acordes musicais ou sons de animais), catalogá-los e traduzi-los em tempo real usando Embeddings de Áudio Neurais Avançados e Bancos de Dados Vetoriais.

### 🚀 A Jornada de Arquitetura: Aprendendo com Nossos Erros

Construir um verdadeiro Tradutor Universal não é apenas sobre transcrever voz para texto (STT). É sobre encontrar similaridade matemática entre sons completamente desconhecidos. Aqui está a jornada de engenharia que nos levou à arquitetura final, documentando nossas falhas e aprendizados:

#### ❌ Tentativa 1: Média de MFCCs (13 a 20 Dimensões)
* **A Ideia:** Extrair os Coeficientes Cepstrais de Frequência Mel (MFCCs) e tirar a média de todo o áudio.
* **A Falha:** Tirar a média destrói a *linha do tempo* do áudio. Para o computador, "Cão" e "Não" ou "Food" e "House" pareciam quase a mesma coisa. Descobrimos que palavras completamente diferentes estavam dando *match* com 94% de similaridade porque suas frequências médias eram parecidas.

#### ❌ Tentativa 2: Espectrograma Mel de Tamanho Fixo (1024 Dimensões)
* **A Ideia:** Converter o áudio em uma "imagem térmica" 2D do som (Espectrograma) e redimensionar matematicamente para uma grade fixa de 32x32 (1024 números) para preservar o tempo.
* **A Falha:** A grade de tempo ficou rígida demais. Se o microfone captasse um clique aleatório do mouse pouco antes da palavra ser falada, a palavra inteira era "empurrada" para a direita na grade 32x32. Ao comparar a palavra deslocada com a original, o Banco Vetorial ficava confuso e a similaridade despencava para 36%.

#### ❌ Tentativa 3: MFCCs Estatísticos (60 Dimensões)
* **A Ideia:** Extrair 20 faixas de MFCC e calcular a Média, Desvio Padrão e Pico Máximo para cada uma. Isso capturaria a "textura" do som sem depender de uma linha do tempo rígida.
* **A Falha:** A normalização estatística (Z-score) achatou tanto os dados que o modelo ficou "míope". Ele não conseguia mais notar a diferença entre palavras, retornando falsos positivos acima de 90%.

#### ✅ A Solução Definitiva: Rede Neural CLAP (512 Dimensões)
Abandonamos a matemática clássica de processamento de sinais e implementamos o modelo **CLAP (Contrastive Language-Audio Pretraining)** da LAION.
* **Como funciona:** Ele usa uma arquitetura avançada de *Transformers* com mecanismos de Atenção. Ele escuta o áudio, ignora ruídos de fundo (como TVs ou cliques de mouse), entende a textura central e comprime a "alma" do som em um vetor perfeito de 512 dimensões. Isso resolve completamente o problema do "elástico" (falar a mesma palavra rápido ou devagar).
* **Por que não usar o Whisper?** O Whisper da OpenAI é incrível, mas é treinado *exclusivamente para fala humana*. Se um alienígena falar em acordes musicais (como o Rocky) ou cliques, o Whisper trata isso como ruído de fundo e falha. O CLAP é treinado no dataset *AudioSet*, o que significa que ele entende vozes humanas, sons de animais, máquinas e cliques alienígenas. Ele é verdadeiramente Universal.

### 🛠️ Arquitetura
- **Cérebro de Áudio:** `laion/clap-htsat-unfused` (HuggingFace) para extração de Embeddings de 512D.
- **Memória Vetorial:** `ChromaDB` para buscas de alta dimensão e ultra velocidade usando similaridade de cosseno.
- **Banco Relacional:** `SQLite` para catalogar vocabulário e metadados.
- **Interface Humana:** `faster-whisper` para transcrever as respostas do humano para texto.

### 💻 Como Executar
1. Instale as dependências: `pip install -r requirements.txt`
2. **Migrar/Reconstruir Banco:** `python scripts/migrate_to_vector_db.py`
  *(Baixa o modelo CLAP (~600MB) e processa os áudios salvos).*
3. **Tradução em Tempo Real:** `python scripts/translate_audio.py`
  *(Ouve seu microfone e encontra a palavra exata no banco de dados alienígena).*

</details>

<br>

<details>
<summary><h2>🇺🇸 English Version (Click to expand)</h2></summary>

An autonomous Universal Translator inspired by the book *Project Hail Mary* (Andy Weir). This system is designed to listen to unknown languages (be it human speech, alien clicks, musical chords, or animal sounds), catalog them, and translate them in real-time using advanced Neural Audio Embeddings and Vector Databases.

### 🚀 The Architectural Journey: Learning from Our Mistakes

Building a true Universal Translator is not just about speech-to-text. It's about finding mathematical similarity between completely unknown sounds. Here is the engineering journey that led to our final architecture, documenting our failures and learnings:

#### ❌ Attempt 1: Mean MFCCs (13 to 20 Dimensions)
* **The Idea:** Extract the Mel-Frequency Cepstral Coefficients (MFCCs) and take the average across the entire audio clip.
* **The Failure:** Taking the average destroys the *timeline* of the audio. "Cat" and "Tac" look exactly the same. We found that completely different words (like "Food" and "House") were matching with 94% similarity because their average frequencies were similar.

#### ❌ Attempt 2: Fixed-Size Mel-Spectrogram (1024 Dimensions)
* **The Idea:** Convert the audio into a 2D "thermal image" of sound (Spectrogram) and mathematically resize it to a fixed 32x32 grid (1024 flat numbers) to preserve time.
* **The Failure:** The time grid was too rigid. If the microphone captured a random mouse click right before the word was spoken, the entire word was shifted forward in the 32x32 grid. When comparing the shifted word to the original, the Vector Database got confused and similarity dropped to an abysmal 36%.

#### ❌ Attempt 3: Statistical MFCCs (60 Dimensions)
* **The Idea:** Extract 20 MFCC bands and calculate the Mean, Standard Deviation, and Maximum peak for each. This captures the "texture" of the sound without relying on a strict timeline.
* **The Failure:** The statistical normalization (Z-score) flattened the data so much that the model became "nearsighted". It couldn't tell the difference between words anymore, returning 96% matches for entirely different audio samples.

#### ✅ The Definitive Solution: CLAP Neural Network (512 Dimensions)
We abandoned classical math and implemented **CLAP (Contrastive Language-Audio Pretraining)** by LAION.
* **How it works:** It uses an advanced Transformer architecture with Attention mechanisms. It listens to the audio, ignores background noise (like TVs or mouse clicks), understands the core texture, and compresses the "soul" of the sound into a perfect 512-dimensional vector. It completely solves the "time-stretching" problem (speaking faster or slower).
* **Why not Whisper Embeddings?** OpenAI's Whisper is incredible, but it is trained exclusively on *human speech*. If an alien speaks in musical chords (like Rocky) or clicks, Whisper treats it as background noise and fails. CLAP is trained on the *AudioSet* dataset, meaning it understands human voices, animal sounds, machines, and alien clicks. It is truly Universal.

### 🛠️ Architecture
- **Audio Brain:** `laion/clap-htsat-unfused` (HuggingFace) for 512D feature extraction.
- **Memory/Vector DB:** `ChromaDB` for ultra-fast, high-dimensional cosine similarity searches.
- **Relational DB:** `SQLite` for cataloging vocabulary and metadata.
- **Human Interface:** `faster-whisper` for transcribing the human's response to text.

### 💻 How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. **Migrate/Rebuild Database:** `python scripts/migrate_to_vector_db.py`
  *(Downloads the CLAP model (~600MB) and processes all saved audio into 512D vectors).*
3. **Real-Time Translation:** `python scripts/translate_audio.py`
  *(Listens to your microphone and finds the exact matching word in the alien database).*

</details>