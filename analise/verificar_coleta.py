"""Verificação da coleta (critério CS01) – lê dados/bruto/ e mede cobertura, lacunas e ciclos inválidos.

Uso: python analise/verificar_coleta.py [--intervalo 300] [--bruto dados/bruto]
Saída (agregada, sem IPs) em dados/tratado/:
    verificacao_coleta.csv     -> indicadores da coleta (CS01)
    serie_ciclos_por_tipo.csv  -> % de pontos que responderam por ciclo e tipo (para gráfico)
    resposta_por_ponto.csv     -> classe de resposta de cada ponto no período (uso interno, fora do Git)

Regras (docs/regras_eventos.md):
- lacuna quando o intervalo entre ciclos da mesma série passa de 1,5 x o nominal;
- ciclo inválido quando nenhum ponto responde (falha do lado do coletor): vira sem_coleta;
- se houver mais de um coletor gravando ao mesmo tempo (ciclos com intervalo < 0,5 x o nominal),
  as séries são separadas pela fase do horário de início; a série principal é a mais longa
  (empate: a que começou primeiro), ou a indicada em --serie (ex.: a que continua ativa depois que
  o processo duplicado é encerrado); as demais servem só para conferência.
"""
import argparse
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]


def separar_series(c, intervalo):
    """Agrupa os ciclos pela fase do início dentro do intervalo nominal (tolerância de 30 s)."""
    seg = c["inicio"].dt.hour * 3600 + c["inicio"].dt.minute * 60 + c["inicio"].dt.second
    fase = (seg % intervalo).round(-1)          # arredonda a 10 s
    grupos, rotulo = {}, []
    for f in fase:
        chave = next((g for g in grupos if min(abs(f - g), intervalo - abs(f - g)) <= 30), None)
        if chave is None:
            chave = f; grupos[chave] = len(grupos) + 1
        rotulo.append(grupos[chave])
    return pd.Series(rotulo, index=c.index)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--intervalo", type=int, default=300)
    ap.add_argument("--bruto", default=str(BASE / "dados" / "bruto"))
    ap.add_argument("--serie", type=int, default=0, help="série principal (1, 2...); 0 = a mais longa")
    a = ap.parse_args()
    bruto = Path(a.bruto)
    c = pd.concat([pd.read_csv(f) for f in sorted(bruto.glob("ciclos_*.csv"))], ignore_index=True)
    v = pd.concat([pd.read_csv(f) for f in sorted(bruto.glob("varredura_*.csv"))], ignore_index=True)
    c["inicio"] = pd.to_datetime(c["inicio"]); c["fim"] = pd.to_datetime(c["fim"])
    c = c.sort_values("inicio").reset_index(drop=True)

    sobrepostos = int((c["inicio"].diff().dt.total_seconds() < 0.5 * a.intervalo).sum())
    c["serie"] = separar_series(c, a.intervalo) if sobrepostos else 1
    tam = c.groupby("serie")["inicio"].agg(["size", "min"]).sort_values(["size", "min"], ascending=[False, True])
    principal = a.serie if a.serie in tam.index else tam.index[0]

    # conferência entre séries simultâneas: diferença de pontos que responderam em ciclos próximos
    concord = ""
    if len(tam) > 1:
        s1 = c[c.serie == principal][["inicio", "responderam"]]
        s2 = c[c.serie != principal][["inicio", "responderam"]].rename(columns={"responderam": "r2"})
        par = pd.merge_asof(s1.sort_values("inicio"), s2.sort_values("inicio"), on="inicio",
                            direction="nearest", tolerance=pd.Timedelta(seconds=a.intervalo // 2)).dropna()
        concord = round((par["responderam"] - par["r2"]).abs().mean(), 2)

    p = c[c.serie == principal].copy()
    invalidos = p[p["responderam"] == 0]
    gaps = p["inicio"].diff().dt.total_seconds()
    lacunas = gaps[gaps > 1.5 * a.intervalo]
    periodo = (p["inicio"].iloc[-1] - p["inicio"].iloc[0]).total_seconds()
    esperados = int(periodo // a.intervalo) + 1
    validos = p[p["responderam"] > 0]
    vp = v[v["ciclo_id"].isin(validos["ciclo_id"])]
    por_ciclo = v[v["ciclo_id"].isin(p["ciclo_id"])].groupby("ciclo_id").size()
    res = {
        "primeiro_ciclo": p["inicio"].iloc[0].isoformat(), "ultimo_ciclo": p["inicio"].iloc[-1].isoformat(),
        "horas_cobertas": round(periodo / 3600, 1),
        "ciclos_gravados": len(p), "ciclos_esperados": esperados,
        "cobertura_CS01_pct": min(100.0, round(100 * len(p) / esperados, 1)),
        "lacunas": len(lacunas), "maior_lacuna_min": round(lacunas.max() / 60, 1) if len(lacunas) else 0,
        "ciclos_invalidos": len(invalidos),
        "ciclos_invalidos_horarios": ";".join(invalidos["inicio"].dt.strftime("%d/%m %H:%M")),
        "ciclos_validos": len(validos),
        "series_simultaneas": len(tam), "ciclos_sobrepostos": sobrepostos,
        "dif_media_respostas_entre_series": concord,
        "registros": len(vp), "pontos_por_ciclo_min": int(por_ciclo.min()), "pontos_por_ciclo_max": int(por_ciclo.max()),
        "duracao_ciclo_media_s": round((p["fim"] - p["inicio"]).dt.total_seconds().mean(), 1),
        "duracao_ciclo_max_s": round((p["fim"] - p["inicio"]).dt.total_seconds().max(), 1),
        "pct_responderam_medio": round(100 * validos["responderam"].sum() / validos["pontos"].sum(), 1),
    }
    vp = vp.assign(on=vp["status"].eq("online"))
    for t, x in (vp.groupby("tipo")["on"].mean() * 100).round(1).items():
        res[f"pct_respondeu_{t}"] = x

    # classe de resposta de cada ponto no período (sem_resposta persistente x intermitente x sempre)
    fr = vp.groupby(["chave", "tipo"])["on"].mean().rename("fracao").reset_index()
    fr["classe"] = pd.cut(fr["fracao"], [-0.01, 0, 0.95, 0.99999, 1],
                          labels=["nunca_respondeu", "abaixo_95", "entre_95_e_100", "sempre_respondeu"])
    for k, n in fr["classe"].value_counts().sort_index().items():
        res[f"pontos_{k}"] = int(n)

    out = BASE / "dados" / "tratado"; out.mkdir(parents=True, exist_ok=True)
    pd.Series(res).to_csv(out / "verificacao_coleta.csv", header=["valor"])
    fr.to_csv(out / "resposta_por_ponto.csv", index=False)
    s = vp.groupby(["data_hora", "tipo"])["on"].mean().unstack() * 100
    s.round(2).to_csv(out / "serie_ciclos_por_tipo.csv")
    print(pd.Series(res).to_string())
    print(pd.crosstab(fr["tipo"], fr["classe"], margins=True).to_string())


if __name__ == "__main__":
    main()
