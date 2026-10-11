# FibraDados – Análise de Disponibilidade da Rede Óptica Municipal (GPON)

Projeto extensionista da disciplina **Big Data Aplicado** – UniEVANGÉLICA, 2026/2.

**Aluno:** Thiago José da Silva Garcez
**Instituição parceira:** Prefeitura Municipal de Anápolis – Gerência de Tecnologia da Informação
**Kanban:** https://trello.com/b/AW6AJXkV/fibradados-big-data-aplicado

## Objetivo
Transformar as varreduras da rede GPON (cerca de 580 pontos: unidades, câmeras e Wi-Fi público)
em um histórico de eventos e em indicadores de disponibilidade, número de quedas, tempo de
restabelecimento e quedas em massa, apoiando a manutenção e o planejamento da rede.

## Estrutura (planejada)
- `ingestao/` – coletor de varreduras e importação de planilhas/KMZ
- `tratamento/` – padronização, integração e vínculo com o mapa
- `analise/` – eventos, indicadores e agrupamento de quedas em massa
- `painel/` – painel interativo para a rede interna
- `notebooks/` – explorações e perfilamento dos dados
- `docs/` – dicionário de dados e documentação

## Dados
Os dados da rede **não** são versionados neste repositório (IPs, seriais e localização de
equipamentos públicos). A pasta `dados/` é ignorada pelo Git e existe apenas no ambiente
interno da Prefeitura.

## Sprints
| Sprint | Período | Foco |
|---|---|---|
| 1 | 28/09 a 11/10/2026 | Fontes, perfilamento e estrutura do projeto |
| 2 | 12/10 a 25/10/2026 | Coletor histórico, ingestão e tratamento |
| 3 | 26/10 a 08/11/2026 | Eventos, indicadores e quedas em massa |
| 4 | 09/11 a 22/11/2026 | Painel, validação e entrega |
