"""Perfilamento inicial do inventário PANA (Sprint 1).

Lê o arquivo dados/PANA_atualizado.xlsx (não versionado) e imprime:
- quantidade de registros por tipo e status;
- percentual de preenchimento dos campos-chave;
- duplicidades e pendências de cadastro.
"""
from pathlib import Path
import pandas as pd

ARQ = Path(__file__).resolve().parents[1] / "dados" / "PANA_atualizado.xlsx"
CAMPOS = ["IP gerência", "OLT", "GPON", "ID", "Serial ONU", "CTO", "Latitude", "Longitude"]


def main() -> None:
    inv = pd.read_excel(ARQ, sheet_name="ACCESS")
    print(f"Registros: {len(inv)}")
    print("\nPor tipo e status:")
    print(pd.crosstab(inv["Tipo"], inv["Status"], margins=True))

    print("\nPreenchimento dos campos-chave (%):")
    print((inv[CAMPOS].notna().mean() * 100).round(1))

    print("\nDuplicidades:")
    print("  descrição repetida:", inv.iloc[:, 0].duplicated().sum())
    print("  serial repetido:", inv["Serial ONU"].dropna().duplicated().sum())

    print("\nDatas de 'Offline desde' (top 5):")
    print(inv["Offline desde"].dropna().astype(str).str[:10].value_counts().head())

    pend = pd.read_excel(ARQ, sheet_name="PENDÊNCIAS")
    tipo = pend["Pendência"].str.replace(r"\d+\.\d+\.\d+\.\d+(/\d+)?", "<ip>", regex=True)
    print(f"\nPendências de cadastro: {len(pend)}")
    print(tipo.value_counts().head(10))


if __name__ == "__main__":
    main()
