# Regras dos eventos e da coleta (revisão pós-feedback – 27/10/2026; atualizada em 31/10/2026)

Documento criado para atender ao feedback da Proposta de Projeto (seções 5.3, 6.3 a 6.6 e 6.4).

## 1. Estados de cada observação
| Estado | Quando ocorre | Entra na disponibilidade? |
|---|---|---|
| `online` | o ponto respondeu no ciclo | sim, como tempo disponível |
| `sem_resposta` | o ciclo rodou e o ponto não respondeu | sim, como tempo indisponível |
| `sem_coleta` | não há ciclo gravado no intervalo (coletor parado, PC desligado) | **não** – excluído do numerador e do denominador |
| `nao_confirmado` | ponto marcado como "bloqueia ping" (LM03) | **não** – fica fora dos indicadores até verificação complementar |

A ausência de observação nunca é contada como tempo disponível nem como indisponível.

## 2. Ciclos e lacunas
- Intervalo nominal entre ciclos: 5 min. Cada ciclo grava um registro de controle (`ciclo_id`, início, fim, nº de pontos testados).
- Há **lacuna de coleta** quando o intervalo entre dois ciclos gravados passa de 7,5 min (1,5 × o nominal). O período da lacuna é marcado como `sem_coleta` para todos os pontos.
- **Ciclo inválido (revisão de 31/10/2026):** ciclo em que nenhum ponto respondeu, inclusive as OLTs. Indica falha do lado do coletor (rede ou servidor), e não queda dos pontos. O ciclo inteiro é tratado como `sem_coleta`. Caso real: 28/10/2026, 14:42–14:43, visto pelos dois coletores.
- **Coletores simultâneos (revisão de 31/10/2026):** se dois processos gravarem ao mesmo tempo (ciclos com intervalo menor que 2,5 min), as séries são separadas pela fase do horário de início. A principal é a do processo que continua ativo (ou, sem essa informação, a mais longa); as outras servem só para conferência e nunca são somadas. Caso real: 28/10 a 31/10/2026; o processo duplicado foi encerrado em 31/10 às 10:58.

## 2.1 Pontos sem resposta persistente (revisão de 31/10/2026)
- Ponto que não respondeu em **nenhum** ciclo válido do período recebe a marca `sem_resposta_persistente`.
- Ele **não** entra no MTTR nem na contagem de quedas, e a disponibilidade dele é apresentada à parte, nunca misturada com a dos pontos ativos. O motivo (desativado, sem energia, bloqueio de ping ou cadastro errado) é uma pendência de cadastro para a equipe, e não um evento.
- Base: na primeira coleta (28 a 31/10/2026), 321 pontos nunca responderam, e 301 deles já constavam como OFFLINE no inventário de 03/10/2026.

## 3. Início, término e duração das quedas
- **Queda confirmada:** dois ou mais ciclos seguidos com `sem_resposta`. Uma falha isolada (um único ciclo) não abre evento, mas o intervalo dela conta como indisponível.
- **Início:** horário do primeiro ciclo `sem_resposta` da sequência. Incerteza: até 1 intervalo (a queda ocorreu entre o último `online` e esse ciclo).
- **Término:** horário do primeiro ciclo `online` depois da sequência. Incerteza: até 1 intervalo.
- **Duração:** término − início, menos o tempo de lacunas de coleta dentro do evento. Tolerância declarada: ±5 min.
- **Lacuna dentro de um evento:** se for menor que 30 min e o ponto continuar sem resposta depois dela, o evento continua (com a marca `com_lacuna`). Se for de 30 min ou mais, o evento é encerrado como `fim_nao_observado`.

## 4. Eventos incompletos
| Situação | Marca | Disponibilidade | MTTR |
|---|---|---|---|
| Ponto já estava sem resposta no início do período | `inicio_nao_observado` | conta só a parte dentro do período | fora |
| Ponto continua sem resposta no fim do período | `aberto` | conta até o fim do período | fora |
| Evento interrompido por lacuna ≥ 30 min | `fim_nao_observado` | conta só o tempo observado | fora |

O MTTR usa apenas eventos com início e término observados.

## 5. Quedas em massa (hipóteses de investigação)
- Quedas confirmadas que começam numa janela de 10 min e compartilham a mesma porta GPON ou CTO formam um **grupo**.
- Grupo com 3 ou mais pontos → "possível falha em trecho comum". Queda sem grupo → "queda individual".
- As duas classificações são **hipóteses**: só viram causa depois de confirmadas pela equipe (OTDR, inspeção). Uma queda individual também pode vir de um trecho compartilhado.

## 6. Gravação dos registros (coletor)
- Ao fim de **cada ciclo**, os resultados são acrescentados ao arquivo do dia (`bruto/AAAA-MM-DD.csv`) com `flush` imediato. Se o computador desligar, perde-se no máximo o ciclo em andamento.
- Uma vez por dia, o arquivo do dia anterior é convertido para Parquet (camada bruta), e o CSV só é apagado depois que a conversão for conferida (mesmo número de linhas).
- Ao reiniciar, o coletor continua no arquivo do dia e registra a lacuna.

## 7. Validação (CS03 e CS04 revisados)
- **CS03a – cálculos:** séries sintéticas com resposta conhecida (quedas, lacunas, eventos abertos). Aceitação: nº de eventos exato, duração dentro de ±5 min e disponibilidade dentro de ±0,5 ponto percentual.
- **CS03b – dados reais:** amostra de 10 quedas registradas pela equipe após o início da coleta. Aceitação: pelo menos 9 de 10 encontradas, com início e término dentro de ±10 min (2 ciclos).
- **CS04a – composição:** a lista real das 66 ONUs afetadas em 06/10/2026 (portas GPON 7 e 8 da OLT 02) deve ser agrupada pela regra só nas portas 7 e 8 da OLT 02, sem ONU de outra porta.
- **CS04b – tempo:** os relatórios do incidente têm só a data (06/10/2026), sem horário por ONU. Por isso a parte temporal é testada com uma simulação do cenário, o que **verifica a regra, mas não comprova o comportamento histórico** do incidente real. A comprovação temporal fica para o primeiro incidente real registrado pelo coletor, conferido com a equipe.
