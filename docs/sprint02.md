# Registro da Sprint 02 (12/10 a 25/10/2026)

## Situação dos cards
| Card | Atividade | Situação | Evidência |
|---|---|---|---|
| C04 | Coletor de varreduras com registro histórico | Não executado no período; implementado em 28/10; coleta real desde 28/10 10:03 | `ingestao/coletor.py`, `testes/test_coletor.py`, `analise/verificar_coleta.py` |
| C05 | Ingestão das planilhas e do mapa | Planilhas na camada bruta em 28/10; extração do KMZ pendente | `ingestao/importar_fontes.py` |
| C06 | Tratamento, padronização e vínculo com o mapa | Implementado em 28/10; em validação | `tratamento/cadastro_integrado.py` |
| C07 | Relatório de qualidade do cadastro | Planilha gerada em 28/10; aguarda retorno da equipe | `tratamento/cadastro_integrado.py` |

Nenhuma atividade foi executada entre 12 e 25/10/2026. A recuperação começou em 28/10/2026, já no período da Sprint 3.

## Execução do coletor (servidor Linux da Gerência de TI)
```bash
cd /root/fibradados
TZ=America/Sao_Paulo nohup python3 ingestao/coletor.py --intervalo 300 > /dev/null 2>&1 &
pgrep -af coletor.py        # deve haver um único processo
tail -3 dados/bruto/coletor.log
```
- A lista de pontos (`dados/pontos_coletor.csv`) é copiada do computador da TI; tem IPs e não vai para o Git.
- O servidor usa UTC; `TZ=America/Sao_Paulo` grava os horários no fuso de Brasília.

## Verificação da coleta (CS01) – 31/10/2026
`python3 analise/verificar_coleta.py` sobre os dados de 28/10 10:07 a 31/10 10:52 (`--serie 2`, o coletor que continua ativo):

| Verificação | Esperado | Encontrado | Decisão |
|---|---|---|---|
| Cobertura de ciclos (CS01) | ≥ 95% | 874 de 874 (100%), 0 lacunas | Atendido |
| Pontos por ciclo | 580 em todos | 580 (mín. e máx.) | Atendido |
| Ciclos inválidos | 0 | 1 (28/10 14:42, nenhum ponto respondeu) | Tratado como `sem_coleta` (regra nova) |
| Processo único | 1 coletor | 2 coletores simultâneos (início duplicado em 28/10) | Duplicado encerrado em 31/10 10:58; a série dele serviu só de conferência (diferença média de 0,44 ponto por ciclo) |

Resultados agregados: 177 pontos responderam em todos os ciclos, 67 entre 95% e 100%, 15 abaixo de 95% e 321 nunca responderam (301 deles já estavam OFFLINE no inventário de 03/10/2026). Regras novas em `docs/regras_eventos.md` (ciclo inválido, coletores simultâneos e sem resposta persistente).

Validação: conferido pelo Gerente de TI (Thiago J. S. Garcez).
