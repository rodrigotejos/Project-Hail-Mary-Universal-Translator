## Q1. Qual é o escopo mínimo viável (Must-Have) para esta entrega?

A. Script/orquestrador de execução no Colab CLI, notebook (.ipynb) de treinamento acoplável para fallback manual, matriz de aceleradores progressiva (T4/CPU -> GPU/TPU) e validação dos checkpoints/embeddings gerados
B. Apenas o notebook estático (.ipynb) sem orquestração via CLI
C. Integração completa na interface gráfica Flet antes de testar os scripts CLI
D. Não aplicável / Ainda não definido
X. Outro (por favor, especificar)
[Answer]: A

## Q2. Quais recursos são considerados Nice-to-Have ou fora do escopo inicial?

A. Automação de deploy em CI contínuo com GPU e suporte a cluster multi-nó são Nice-to-Have/fora de escopo; foco no desenvolvedor rodando sob demanda
B. Nenhuma funcionalidade é secundária, tudo deve ser entregue simultaneamente
C. Não aplicável
X. Outro (por favor, especificar)
[Answer]: A

## Q3. Qual é a preferência de sequenciamento de entrega?

A. Value-first com foco em eficiência econômica: validar primeiro o pipeline completo em hardware econômico (T4/CPU) e depois expandir o benchmark para instâncias superiores (V100/A100/TPU)
B. Risk-first: focar exclusivamente em testar limites extremos de TPU antes de qualquer script básico
C. Dependency-first: construir primeiro infraestruturas de observabilidade remota
D. Não aplicável
X. Outro (por favor, especificar)
[Answer]: A

## Consolidated Summary Confirmation

Does this all look correct?

- Must-Have: Orquestrador Colab CLI (`colab exec`), notebook de treinamento (.ipynb) versionado, matriz de hardware com progressão de custo (T4/CPU -> GPU/TPU) e validação de inferência pós-treino.
- Out of scope: CI contínuo com instâncias pagas e automações multi-nó.
- Sequenciamento: Value-first e custo-eficiente (validar ponta a ponta no hardware básico antes de benchmarking avançado).

[Answer]: Looks correct
