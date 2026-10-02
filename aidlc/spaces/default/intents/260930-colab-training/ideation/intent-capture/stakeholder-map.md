# Stakeholder Map: Treinamento em Nuvem com Google Colab CLI

## Key Stakeholders & Interests

| Stakeholder | Role | Interests & Concerns | Source |
|---|---|---|---|
| Desenvolvedor do Projeto | Desenvolvedor / Pesquisador ML | Execução automatizada e confiável de treinos via Colab CLI, benchmarking de aceleradores (GPU/TPU) com custo-benefício ótimo e validação dos embeddings acústicos | [desc] [Q2] [Q5] [Q6] |
| Mantenedor do Repositório | Engenheiro de Software | Manutenibilidade da base de código, testes locais reproduzíveis e preservação da compatibilidade com os módulos existentes (Modal e SiameseNet) | [desc] [Q1] [Q5] |

## Decision-Makers vs. Influencers

| Role / Entity | Type | Scope of Authority | Source |
|---|---|---|---|
| Desenvolvedor do Projeto | Decision-Maker | Decisão sobre arquitetura técnica, escolha de hardware para benchmark, e aprovação dos gates de entrega | [Q5] |
| Métricas de Custo e Tempo | Influencer | Dados empíricos de tempo por época vs. custo por hora definem se haverá escalada para instâncias superiores de GPU ou TPU | [Q3] [Q6] |

## Communication Requirements

| Cadence / Channel | Audience | Content / Focus | Source |
|---|---|---|---|
| Terminal / CLI Logs & Notebook Outputs | Desenvolvedor do Projeto | Acompanhamento do progresso de época, convergência da perda e métricas de validação | [desc] [Q3] [Q7] |

## Assumptions & Open Questions

None.
