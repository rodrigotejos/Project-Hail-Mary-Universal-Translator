Documentação Oficial: Projeto Tradução Universal

1. Visão Geral do Projeto

O Projeto Tradução Universal (inspirado no conceito de comunicação interespécies do livro/filme Project Hail Mary) é um sistema de software projetado para aprender, catalogar e traduzir em tempo real um idioma desconhecido (alienígena ou não catalogado).

Premissa: O sistema parte do zero. Ele aprende mapeando palavras do nosso idioma base para assinaturas de áudio emitidas pelo outro ser.
Fase de Lançamento (V1): O sistema será 100% offline (local-first) e focado em Português como idioma de entrada, mas com a arquitetura preparada para um sistema de "idioma pivô" em atualizações futuras.

2. Estrutura de Dados e Armazenamento

O armazenamento de V1 é baseado em um sistema de arquivos local simples e eficiente, atuando como um dicionário de chave-valor (De/Para).

Diretório Raiz: /linguagens/

Subdiretórios: Uma pasta para cada idioma (ex: /linguagens/ingles/, /linguagens/clingo/, /linguagens/goriles/).

Arquivos de Áudio: Os sons gravados do outro ser serão salvos dentro da pasta do idioma correspondente.

Regra de Nomenclatura (V1): O nome do arquivo será exatamente a palavra traduzida no idioma base (Português).

Formato: .wav ou .flac (formatos sem perda para facilitar a análise de frequência).

Exemplo: Para a palavra "música", o som emitido pelo ser será salvo como /linguagens/clingo/musica.wav.

3. Interface do Usuário (UI)

A interface possui uma estética Sci-Fi (painel de nave) e é dividida em blocos lógicos principais.

3.1. Barra Superior (Header)

Título: PROJETO: TRADUÇÃO UNIVERSAL ...

Controles de Idioma: Dropdown para selecionar a linguagem de entrada (Humana) e a linguagem alvo (Alienígena). Botão [ + Criar Nova Linguagem ].

Status de Conexão: Indicador de nuvem escrito [Nuvem] Status: OFFLINE SOMENTE (em cor cinza/desativado na V1. Na V2, ficará verde/vermelho dependendo da conexão).

3.2. Painel Esquerdo: MÓDULO DE APRENDIZADO

Dividido em duas seções verticais (Cima e Baixo). O objetivo desta área é criar novos pares de palavras.

Área Inferior (Nossa Entrada):

Input de texto e um botão de microfone (transcrição).

O usuário digita ou fala a palavra no idioma base (ex: "MÚSICA").

A palavra digitada/falada aparece em texto bem grande e em destaque no centro do módulo.

Área Superior (Captura do Outro Ser):

Botão "Gravar Áudio do Outro Ser".

Ao clicar, o sistema aguarda o áudio externo. O sistema detecta automaticamente o silêncio para encerrar a gravação.

Após a gravação, o arquivo é salvo (usando o texto grande como nome do arquivo) e surge um botão [ ▶ Ouvir Áudio Captado ] para o usuário validar a gravação.

3.3. Painel Direito: MÓDULO DE CONVERSAÇÃO

Interface em formato de Chatbot. Exibe o histórico completo da conversa.

Área de Chat (Histórico): Exibe balões de conversa (Você vs. Ser Extraterrestre).

Lógica de Palavras Desconhecidas (Missing Words): Seja na fala do usuário ou na fala do outro ser, se o sistema identificar uma palavra/som que não está no banco de dados, essa palavra ficará destacada em vermelho.

O usuário poderá clicar nessa palavra vermelha para enviá-la automaticamente para o Módulo de Aprendizado.

Entrada de Dados (Bottom Bar): Input de texto com botão de [Enter] (Enviar) e um botão de [Microfone] (Falar).

4. Arquitetura de Módulos Internos

O sistema é orquestrado por módulos independentes que se comunicam através de um Gerenciador Geral.

4.1. Gerenciador Geral (Orquestrador)

Recebe os inputs (texto ou áudio) e decide para qual fluxo mandar.

Controla a alternância fluida entre o estado de "Conversando" e "Aprendendo".

4.2. Módulo de Transcrição e Indexação (Idioma Base)

Converte o áudio falado pelo usuário em um array de palavras (texto).

Preparação para V1.5: Este módulo encapsulará a lógica de tradução. O dado de entrada é convertido para texto, e esse texto é usado como "chave" (nome do arquivo) para buscar ou salvar no banco de dados.

4.3. Módulo Analisador de Áudio (O "Shazam")

Responsável por ouvir o áudio do outro ser.

Processamento: Pega uma frase em áudio contínuo e fatia (splits) baseando-se em micro-silêncios ou picos de frequência, transformando a frase em um array de clipes de áudio isolados.

Matching: Compara a "assinatura de áudio" (espectrograma/frequência) de cada clipe com os arquivos .wav salvos na pasta do idioma selecionado.

Retorna a transcrição correspondente na nossa linguagem ou uma flag de [som_desconhecido].

4.4. Gerenciador de Conversação

Fluxo de Saída (Nós -> Eles):

Recebe a frase digitada ou transcrita do usuário.

Valida as palavras contra o banco de dados local para identificar as mapeadas e as faltantes.

Reproduz em sequência os áudios correspondentes apenas das palavras conhecidas.

Exibe a frase completa no Chatbot, mantendo as palavras conhecidas com a formatação normal e destacando as palavras faltantes em vermelho, para posterior cadastro no Módulo de Aprendizado.

Fluxo de Entrada (Eles -> Nós):

Recebe o array do Módulo Analisador ("Shazam").

Identifica os clipes de áudio combinados (traduzidos).

Identifica os clipes sem correspondência (palavras novas).

Joga a frase no Chatbot, marcando em vermelho os trechos não traduzidos e oferecendo a opção de iniciar o aprendizado deles.

4.5. Gerenciador de Aprendizado

Recebe a String do usuário.

Recebe o Áudio bruto do outro ser.

Aplica algoritmos de limpeza de ruído (noise gate, normalização).

Salva fisicamente o arquivo no diretório com o nome da String recebida.

5. Fluxos de Exceção e Features Críticas

Transmissão Parcial de Conversa (Missing Words): Se o usuário emitir uma frase que contenha uma palavra ainda não aprendida pelo sistema, a comunicação não é interrompida. O sistema reproduz os áudios das palavras que ele já sabe para o outro ser e ignora a emissão da palavra desconhecida. No painel de Chatbot, o sistema exibe a palavra desconhecida em vermelho para alertar o usuário.

Gravação Inteligente: O gatilho de gravação do alienígena não exige que o usuário aperte "Stop". O sistema deve possuir uma detecção de limite de decibéis (Threshold) que encerra e salva o arquivo automaticamente após X milissegundos de silêncio.

6. Roadmap Futuro

Versão 1.5: Suporte Multilíngue Interno (A Abordagem "Idioma Pivô")

O Problema: Se mapearmos os arquivos como ola.wav em Português, um usuário que fala Francês precisaria criar um banco de dados alienígena totalmente novo para mapear bonjour.wav.

A Solução (Idioma Pivô): O sistema adotará um idioma base indexador (ex: Inglês).

Exemplo Prático: O usuário fala Português ("Olá"). O Módulo de Transcrição ouve "Olá", traduz automaticamente para a chave em inglês ("hello") e busca/salva o arquivo como hello.wav.

No painel do Chatbot, o sistema continua exibindo a frase na língua materna do usuário ("Olá"), mas nos bastidores, toda a estrutura de pastas e comunicação usa a língua pivô. Isso permite que dicionários alienígenas criados por brasileiros sejam usados instantaneamente por franceses ou americanos.

Versão 2.0: Colaboração em Nuvem

Status Nuvem: Ativação do módulo online.

Sincronização: Sincronizar o banco de dados de áudios (arquivos locais indexados pela linguagem pivô) com um bucket na nuvem (ex: AWS S3 / Firebase Storage).

Múltiplos Usuários: Permitir que diferentes instâncias e nacionalidades baixem a mesma linguagem "Gorilês" e se beneficiem do aprendizado colaborativo universal.