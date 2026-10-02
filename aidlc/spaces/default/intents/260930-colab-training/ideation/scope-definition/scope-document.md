# Scope Definition: Treinamento em Nuvem Google Colab CLI

## Upstream References

- Consumes: [Intent Statement](file:///e:/code/PHM-Tradutor_Universal/aidlc/spaces/default/intents/260930-colab-training/ideation/intent-capture/intent-statement.md)
- Questions: [Scope Questions](file:///e:/code/PHM-Tradutor_Universal/aidlc/spaces/default/intents/260930-colab-training/ideation/scope-definition/scope-definition-questions.md)

## In-Scope Boundaries (Must-Have)

1. **Orquestração e Execução via Google Colab CLI:**
   - Criação de módulo/script integrador capaz de acionar e monitorar execuções com `colab exec` e parâmetros de acelerador (`--gpu`).
   - Suporte a verificação de status e captura de logs/saídas remotas.
2. **Notebook de Treinamento Versionado (`.ipynb`):**
   - Notebook de treinamento estruturado no repositório contendo todas as células necessárias (instalação de dependências, montagem do código/dados em memória, pré-computação de features acústicas, treinamento siamês e salvamento de checkpoint).
   - Capacidade de servir tanto para execução via CLI quanto para subida manual no Google Colab Web caso desejado.
3. **Matriz Progressiva de Aceleradores (Custo-Benefício):**
   - Mapeamento e testes partindo da instância mais básica/gratuita (CPU / T4), com coleta de métricas de tempo por época vs. custo financeiro.
   - Critério formal de escalada: somente sugerir/usar GPUs de alto custo (V100, A100) ou TPUs caso haja redução substantiva de tempo de treino com justificativa de custo.
4. **Validação e Checkpoint das Gerações:**
   - Exportação de pesos de modelo (`.pth`) e relatório de métricas acústicas (triplet loss, distâncias de pares positivos/negativos).
   - Script de teste de inferência pós-treino para validar que os embeddings gerados pelo modelo treinado no Colab mantêm a separação das línguas acústicas.

## Out-of-Scope (Won't Have no incremento atual)

1. **Pipelines de CI/CD automatizados em nuvem paga:** O treinamento continuará sendo um processo disparado sob demanda pelo desenvolvedor.
2. **Cluster Multi-Nó / Distributed Data Parallel (DDP):** O tamanho atual do dataset e do modelo siamês não justifica a complexidade de treinamento distribuído em múltiplos nós.
3. **Migração completa ou descontinuação do Modal:** O Modal é mantido intacto como opção existente, operando de forma paralela e independente.

## Assumptions & Open Questions

None.
