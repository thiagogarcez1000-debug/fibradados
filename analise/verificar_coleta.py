"""Verificação da coleta (critério CS01) – lê dados/bruto/ e mede cobertura e lacunas.

Uso: python analise/verificar_coleta.py [--intervalo 300]
Saída: resumo no terminal e dados/tratado/verificacao_coleta.csv (agregado, sem IPs).
Regras (docs/regras_eventos.md): lacuna quando o intervalo entre ciclos passa de 1,5 x o nominal.
"""
import argparse
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--intervalo", type=int, default=300)
    ap.add_argument("--bruto", default=str(BASE / "dados" / "bruto")); a = ap.parse_args()
    bruto = Path(a.bruto)
    c = pd.concat([pd.read_csv(f) for f in sorted(bruto.glob("ciclos_*.csv"))], ignore_index=True)
    v = pd.concat([pd.read_csv(f) for f in sorted(bruto.glob("varredura_*.csv"))], ignore_index=True)
    c["inicio"] = pd.to_datetime(c["inicio"]); c["fim"] = pd.to_datetime(c["fim"])
    c = c.sort_values("inicio")
    gaps = c["inicio"].diff().dt.total_seconds()
    lacunas = gaps[gaps > 1.5 * a.intervalo]
    periodo = (c["inicio"].iloc[-1] - c["inicio"].iloc[0]).total_seconds()
    esperados = int(periodo // a.intervalo) + 1
    por_ciclo = v.groupby("ciclo_id").size()
    res = {
        "primeiro_ciclo": c["inicio"].iloc[0].isoformat(), "ultimo_ciclo": c["inicio"].iloc[-1].isoformat(),
        "ciclos_gravados": len(c), "ciclos_esperados": esperados,
        "cobertura_CS01_pct": min(100.0, round(100 * len(c) / esperados, 1)),
        "lacunas": len(lacunas), "maior_lacuna_min": round(lacunas.max() / 60, 1) if len(lacunas) else 0,
        "registros": len(v), "pontos_por_ciclo_min": int(por_ciclo.min()), "pontos_por_ciclo_max": int(por_ciclo.max()),
        "duracao_ciclo_media_s": round((c["fim"] - c["inicio"]).dt.total_seconds().mean(), 1),
        "pct_responderam_medio": round(100 * c["responderam"].sum() / c["pontos"].sum(), 1),
    }
    tipo = (v.assign(on=v["status"].eq("online")).groupby("tipo")["on"].mean() * 100).round(1)
    for t, p in tipo.items():
        res[f"pct_respondeu_{t}"] = p
    out = BASE / "dados" / "tratado"; out.mkdir(parents=True, exist_ok=True)
    pd.Series(res).to_csv(out / "verificacao_coleta.csv", header=["valor"])
    # série agregada por ciclo e tipo (para gráfico), sem identificação de pontos
    s = v.assign(on=v["status"].eq("online")).groupby(["data_hora", "tipo"])["on"].mean().unstack()
    s.to_csv(out / "serie_ciclos_por_tipo.csv")
    print(pd.Series(res).to_string())


if __name__ == "__main__":
    main()
