# Dicionário de dados – fontes iniciais

| ID | Fonte | Origem | Formato | Acesso |
|---|---|---|---|---|
| FD01 | Inventário PANA | Gerência de TI | XLSX (6 abas) | Arquivo interno, uso restrito |
| FD02 | Relatório de ONUs do monitoramento | Gerenciador de ONUs (Python) | XLSX | Gerado sob demanda na rede interna |
| FD03 | Cadastro de câmeras e Wi-Fi público | Gerência de TI | XLSX | Arquivo interno |
| FD04 | Mapa da rede e metragem de fibra | Projeto as built (KMZ) | KMZ / XLSX | Arquivo interno |
| FD05 | Consultas às OLTs | OLTs Furukawa (CLI) | Texto / XLSX | Exportação manual pela TI |
| FD06 | Log histórico de varreduras | Coletor do projeto (a criar) | Parquet diário | Gerado na rede interna |

## Campos principais do inventário (FD01, aba ACCESS)
| Campo | Descrição | Observação |
|---|---|---|
| Descrição | Nome do local/equipamento | texto livre, sem padrão |
| IP gerência | Endereço de gerência da ONU | dado sensível – não publicar |
| OLT / GPON / ID | Posição lógica na rede | 89 registros com OLT não definida |
| Serial ONU | Identificação do equipamento | 23 registros sem serial |
| Tipo | Unidade, Wi-Fi (AP), Câmera, OLT, Switch | 5 categorias |
| Status | ONLINE / OFFLINE / SEM DADOS | apenas o último ciclo, sem histórico |
| Offline desde | Início da última queda | 362 de 364 com a mesma data |
| CTO | Caixa de atendimento | 515 preenchidos |
| Latitude / Longitude | Posição no mapa | 532 preenchidos |

Contagens obtidas no perfilamento inicial (Sprint 1), sobre o arquivo de 03/10/2026.
