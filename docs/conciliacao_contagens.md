# Conciliação das contagens entre as fontes (27/10/2026)

As quantidades aparecem diferentes em partes do relatório porque vêm de arquivos e abrangências diferentes.

| Grupo | Inventário PANA, aba ACCESS (03/10/2026) | Planilha específica (FD03) | Diferença |
|---|---|---|---|
| Câmeras (pontos) | 155 | 153 | 2 pontos só no inventário, cadastrados sem identificação ("ONU pt ?"), um na OLT 1 e um na OLT 3 |
| Wi-Fi público (AP) | 204 | 204 | nenhuma: os 204 IPs e seriais são os mesmos |

- Os 153 IPs da planilha de câmeras estão todos no inventário; 139 câmeras têm serial e todos os 139 conferem com o inventário.
- Na planilha de câmeras, 78 registros estão com OLT "olt x" (não definida) e 13 com nome "pt x", o que explica 78 dos 89 registros do inventário com OLT não definida (os outros 11 são unidades).
- A versão 1.0 do relatório citou 152 câmeras e 203 pontos de Wi-Fi na FD03. Esses números estavam errados; a recontagem feita nesta revisão mostra 153 e 204.
- A caracterização institucional (155 câmeras e 204 Wi-Fi) usa o inventário, que é a referência do projeto.

## Pendências de cadastro
- A aba PENDÊNCIAS do inventário tem **171** registros. A versão 1.0 do relatório citou 170; o número foi corrigido nesta revisão.
- O resumo da própria planilha classifica 165 pendências em 8 categorias (OLT não definida 89, diferente do monitoramento 22, sem ID 16, sem serial 15, máscara/gateway WAN fora do padrão 11, serial repetido 8, IP WAN repetido 2, IP LAN repetido 2).
- "Sem serial" aparece como 15 no resumo e como 23 no perfilamento porque o perfilamento conta todos os 581 registros, incluindo as 6 OLTs e os 2 switches, que não têm serial de ONU.
