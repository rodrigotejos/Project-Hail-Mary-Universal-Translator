# Project Hail Mary - Tradutor Universal / Universal Translator

![alt text](Gemini_Generated_Image_35pddd35pddd35pd.png)

<details open>
<summary><h2>🇧🇷 Versão em Português (Clique para expandir)</h2></summary>

Um Tradutor Universal autônomo inspirado no livro *Devoradores de Estrelas / Project Hail Mary* (Andy Weir). Este sistema foi projetado para ouvir idiomas desconhecidos (seja fala humana, cliques alienígenas, acordes musicais ou sons de animais), catalogá-los e traduzi-los em tempo real usando Engenharia de Áudio Avançada e Bancos de Dados Vetoriais.

### 🚀 A Jornada de Arquitetura: Aprendendo com Nossos Erros

Construir um verdadeiro Tradutor Universal não é apenas sobre transcrever voz para texto (STT). É sobre encontrar similaridade matemática entre sons completamente desconhecidos. Aqui está a jornada de engenharia que nos levou à arquitetura final, documentando nossas falhas e aprendizados:

#### ❌ Tentativa 1: Média de MFCCs (13 a 20 Dimensões)
* **A Ideia:** Extrair os Coeficientes Cepstrais de Frequência Mel (MFCCs) e tirar a média de todo o áudio.
* **A Falha:** Tirar a média destrói a *linha do tempo* do áudio. Para o computador, "Food" e "House" pareciam quase a mesma coisa. Palavras diferentes davam *match* com 94% de similaridade porque suas frequências médias gerais eram parecidas.

#### ❌ Tentativa 2: Espectrograma Mel Base (1024 Dimensões)
* **A Ideia:** Converter o áudio em uma "imagem térmica" 2D do som (Espectrograma) e redimensionar matematicamente para uma grade fixa de 32x32 (1024 números) para preservar o tempo e resolver falantes rápidos/lentos.
* **A Falha:** A grade de tempo ficou rígida demais. Se o microfone captasse um clique aleatório do mouse pouco antes da palavra ser falada, a palavra inteira era "empurrada" na grade 32x32. A similaridade caía para 36% mesmo sendo a mesma palavra.

#### ❌ Tentativa 3: MFCCs Estatísticos (60 Dimensões)
* **A Ideia:** Extrair Média, Desvio Padrão e Pico Máximo. Isso capturaria a "textura" do som sem depender de uma linha do tempo rígida.
* **A Falha:** A normalização (Z-score) achatou os dados. O modelo ficou "míope" e não conseguia mais notar a diferença fonética entre as palavras.

#### ❌ Tentativa 4: O "Canto da Sereia" da Rede Neural (Modelo CLAP - 512D)
* **A Ideia:** Usar uma IA de ponta (CLAP da LAION) treinada com milhões de áudios para extrair a "alma" do som imune a ruídos.
* **A Falha Monumental (A Armadilha Semântica):** O CLAP é inteligente demais. Ele é um classificador *semântico*, não fonético. Quando você fala "Food" e "House", ele não compara as letras. Ele classifica os dois como **"Voz Humana"**! A IA deu exatamente a mesma pontuação (0.78) para palavras totalmente diferentes, porque para ela o som significava a mesma coisa (um humano falando). Descobrimos que Redes Neurais Comerciais destroem a fonética alienígena.

#### ✅ O Santo Graal: Espectrograma Evoluído + Smart RMS Trimmer (1024D)
A solução definitiva foi **voltar para a Matemática Pura (Tentativa 2)**, mas resolvendo sua única fraqueza.
Criamos um **Cortador Inteligente de Energia (Smart RMS Trimmer)**. Antes de criar a imagem 32x32, o código varre o áudio, encontra o exato milissegundo em que a voz começa (ignorando cliques de mouse) e recorta exatamente a palavra.
* **Resultado:** Sem cliques de mouse para empurrar o áudio, a palavra fica **perfeitamente centralizada** na grade 32x32 todas as vezes. Isso nos deu uma comparação **estritamente fonética** e perfeitamente imune ao tempo (falar rápido ou devagar), sem cair nas "armadilhas semânticas" das IAs. A matemática pura venceu.

### 🛠️ Arquitetura
- **Cérebro de Áudio:** Espectrograma Mel 32x32 de Tamanho Fixo + Smart RMS Trimmer.
- **Memória Vetorial:** `ChromaDB` para buscas de alta dimensão usando similaridade de cosseno.
- **Banco Relacional:** `SQLite` para catalogar vocabulário e metadados.
- **Interface Humana:** `faster-whisper` para transcrever as respostas do humano para texto.

### 💻 Como Executar
1. Instale as dependências: `pip install -r requirements.txt`
2. **Migrar/Reconstruir Banco:** `python scripts/migrate_to_vector_db.py`
3. **Tradução em Tempo Real:** `python scripts/translate_audio.py`

</details>

<br>

<details>
<summary><h2>🇺🇸 English Version (Click to expand)</h2></summary>

An autonomous Universal Translator inspired by the book *Project Hail Mary* (Andy Weir). This system is designed to listen to unknown languages (be it human speech, alien clicks, musical chords, or animal sounds), catalog them, and translate them in real-time using Advanced Audio Engineering and Vector Databases.

### 🚀 The Architectural Journey: Learning from Our Mistakes

Building a true Universal Translator is not just about speech-to-text. It's about finding mathematical similarity between completely unknown sounds. Here is the engineering journey that led to our final architecture, documenting our failures and learnings:

#### ❌ Attempt 1: Mean MFCCs (13 to 20 Dimensions)
* **The Idea:** Extract the Mel-Frequency Cepstral Coefficients (MFCCs) and take the average across the entire audio clip.
* **The Failure:** Taking the average destroys the *timeline* of the audio. "Cat" and "Tac" look exactly the same. We found that completely different words (like "Food" and "House") were matching with 94% similarity because their average frequencies were similar.

#### ❌ Attempt 2: Base Fixed-Size Spectrogram (1024 Dimensions)
* **The Idea:** Convert the audio into a 2D "thermal image" of sound (Spectrogram) and mathematically resize it to a fixed 32x32 grid (1024 flat numbers) to preserve time and solve fast/slow speakers.
* **The Failure:** The time grid was too rigid. If the microphone captured a random mouse click right before the word was spoken, the entire word was shifted forward in the grid. Similarity dropped to an abysmal 36% for the exact same word.

#### ❌ Attempt 3: Statistical MFCCs (60 Dimensions)
* **The Idea:** Extract Mean, Standard Deviation, and Maximum peak for 20 MFCC bands.
* **The Failure:** The statistical normalization (Z-score) flattened the data so much that the model became "nearsighted". It couldn't tell the phonetic difference between words anymore.

#### ❌ Attempt 4: The Neural Network Siren Song (CLAP Model - 512D)
* **The Idea:** Use a state-of-the-art AI (LAION's CLAP) trained on millions of sounds to extract the ultimate noise-immune embedding.
* **The Monumental Failure (The Semantic Trap):** CLAP is too smart. It is a *semantic* classifier, not a phonetic one. When you say "Food" and "House", it doesn't compare the letters. It classifies BOTH as **"Human Speech"**! The AI gave the exact same high score (0.78) for totally different words because, semantically, the sound meant the same thing (a human talking). We learned that Commercial AIs destroy alien phonetics.

#### ✅ The Holy Grail: Evolved Spectrogram + Smart RMS Trimmer (1024D)
The definitive solution was to **return to Pure Math (Attempt 2)**, but fixing its only weakness.
We created a **Smart RMS Energy Trimmer**. Before creating the 32x32 image, the code scans the audio, finds the exact millisecond the voice starts (ignoring mouse clicks), and precisely crops the word.
* **The Result:** With no mouse clicks to shift the audio, the word is **perfectly centered** on the 32x32 grid every single time. This gave us a **strictly phonetic** comparison that is perfectly immune to time-stretching (fast/slow speakers), without falling into the "semantic traps" of AI. Pure math won.

### 🛠️ Architecture
- **Audio Brain:** 32x32 Fixed-Size Mel-Spectrogram + Smart RMS Trimmer.
- **Memory/Vector DB:** `ChromaDB` for high-dimensional cosine similarity searches.
- **Relational DB:** `SQLite` for cataloging vocabulary and metadata.
- **Human Interface:** `faster-whisper` for transcribing the human's response to text.

### 💻 How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. **Migrate/Rebuild Database:** `python scripts/migrate_to_vector_db.py`
3. **Real-Time Translation:** `python scripts/translate_audio.py`

</details>