"""Importação das fontes para a camada bruta (card C05).

Copia os arquivos de cadastro (FD01 a FD05) para dados/bruto/fontes/<data>/ sem alterações
e registra um manifesto com nome, tamanho, hash SHA-256, abas e linhas de cada arquivo.
Uso: python ingestao/importar_fontes.py dados/PANA_atualizado.xlsx dados/projeto_cameras.xlsx ...
"""
import csv, datetime as dt, hashlib, shutil, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def linhas_xlsx(p):
    import openpyxl
    wb = openpyxl.load_workbook(p, read_only=True)
    return ";".join(f"{ws.title}={ws.max_row - 1}" for ws in wb.worksheets)


def main(arquivos):
    hoje = dt.date.today().isoformat()
    destino = BASE / "dados" / "bruto" / "fontes" / hoje
    destino.mkdir(parents=True, exist_ok=True)
    man = destino / "manifesto.csv"
    with open(man, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arquivo", "bytes", "sha256", "abas_linhas", "carregado_em"])
        for a in map(Path, arquivos):
            shutil.copy2(a, destino / a.name)
            info = linhas_xlsx(a) if a.suffix.lower() == ".xlsx" else ""
            w.writerow([a.name, a.stat().st_size, sha256(a), info, dt.datetime.now().isoformat(timespec="seconds")])
            print(f"{a.name}: {info}")
    print(f"manifesto: {man}")


if __name__ == "__main__":
    main(sys.argv[1:])
