# Requirements Document: Treinamento em Nuvem Google Colab CLI

## Intent Analysis

O objetivo desta iniciativa é capacitar o projeto PHM Universal Translator a executar seus treinamentos acústicos siameses no Google Colab, alavancando a ferramenta oficial Google Colab CLI (`colab exec`) e notebooks versionados. A arquitetura deve fornecer uma estratégia orientada a custo-benefício de hardware, priorizando aceleradores econômicos (CPU / GPU T4) e permitindo escalada para V100/A100 ou TPU apenas quando o ganho percentual de tempo justificar o custo.

## Functional Requirements

### FR1: Orquestração e Execução via Google Colab CLI
- **FR1.1**: O sistema deve prover um módulo de entrada (`src/engine/colab_train.py`) com interface CLI para orquestrar o envio e execução de jobs no Colab.
- **FR1.2**: O módulo deve suportar os parâmetros de execução: `--gpu <tipo>` (ex: `none`, `t4`, `v100`, `a100`, `tpu`), `--epochs <int>`, `--batch-size <int>`, `--backbone <mobilenet|ast>` e `--dry-run`.
- **FR1.3**: Em modo `--dry-run`, o sistema deve validar sintaxe, dependências e empacotamento localmente sem acionar o comando remoto `colab`.
- **FR1.4**: Em execução real, o sistema deve invocar o `colab exec` apontando para o notebook estruturado, transmitindo logs de saída em tempo real para o console.

### FR2: Notebook Estruturado de Treinamento (`colab_train_siamese.ipynb`)
- **FR2.1**: O notebook deve conter células autônomas para configurar o ambiente Python no Colab, instalando dependências (`torchaudio`, `librosa`, `scipy`, `transformers`, etc.).
- **FR2.2**: O notebook deve suportar descompactação e carregamento dos arquivos de áudio do dataset acústico em memória.
- **FR2.3**: O notebook deve realizar a pré-computação dos tensores acústicos e executar o loop de treino siamês com triplet loss.
- **FR2.4**: O notebook deve salvar o checkpoint final (`models/siamese_colab.pth`) e o sumário de métricas (`training_metrics.json`).
- **FR2.5**: O notebook deve ser totalmente executável tanto de forma automatizada pelo CLI quanto via interface web manual no navegador.

### FR3: Matriz de Aceleradores e Benchmark de Custo/Tempo
- **FR3.1**: O sistema deve manter uma matriz de perfis de hardware suportados pelo Google Colab:
  - `cpu`: baseline sem acelerador
  - `t4`: perfil padrão recomendado para custo-benefício
  - `v100`: perfil de GPU com maior largura de banda de memória
  - `a100`: perfil de alta performance para cargas massivas
  - `tpu`: perfil experimental baseado em PyTorch XLA
- **FR3.2**: O orquestrador deve registrar e calcular o tempo médio por época (segundos/época) e comparar o ganho relativo em relação à T4.
- **FR3.3**: O sistema deve emitir recomendação ao final do benchmark indicando se a instância superior é economicamente viável.

### FR4: Validação de Inferência e Checkpoint
- **FR4.1**: O sistema deve verificar a integridade estrutural do arquivo de checkpoint `.pth` salvo.
- **FR4.2**: O sistema deve carregar o modelo treinado localmente e rodar teste de projeção de embeddings com pares de áudios de validação.
- **FR4.3**: O teste deve verificar se a distância cosseno média de pares da mesma língua (positivos) é estritamente menor que a distância de pares de línguas distintas (negativos) com margem de segurança configurável.

## Non-Functional Requirements

- **NFR1 (Custo e Eficiência)**: O workflow de treinamento deve desencorajar alocação desnecessária de GPUs caras quando instâncias T4 apresentarem throughput equivalente para o volume atual de dados.
- **NFR2 (Portabilidade)**: Os scripts e o notebook devem funcionar sem modificações em sistemas Windows, Linux e macOS com Python >= 3.10.
- **NFR3 (Resiliência)**: Falhas de rede ou timeout durante a chamada do `colab exec` devem ser capturadas com mensagens claras de diagnóstico e instrução de fallback manual no browser.
- **NFR4 (Segurança)**: Não armazenar tokens ou credenciais de acesso em texto puro no código; utilizar variáveis de ambiente ou autenticação nativa do `colab login` / Google Cloud CLI.

## Constraints

- O CLI `colab` oficial requer autenticação prévia na conta Google do usuário (`colab login`).
- Cotas de execução de GPU e TPU no Google Colab estão sujeitas a limites dinâmicos da conta (gratuita ou Pro/Pro+).
- O dataset acústico deve ser transferido de forma compacta para respeitar limites de payload e tempo de upload.

## Assumptions

- O desenvolvedor possui acesso a um runtime do Google Colab com suporte a GPU.
- O formato dos tensores de áudio é compatível com os backbones AST e MobileNet já implementados em `src/engine/siamese_net.py`.

## Out of Scope

- Interface gráfica (Flet) modificada neste incremento (será mantida com o runner atual).
- Treinamento contínuo em runners de GitHub Actions.
- Treinamento distribuído em múltiplos nós.

## Open Questions

None.
