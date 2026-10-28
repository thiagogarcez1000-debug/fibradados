"""Testes do coletor (C04) com ping simulado – não acessa a rede.
Rodar: python testes/test_coletor.py"""
import csv, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingestao"))
import coletor

PONTOS = [{"chave": f"p{i}", "alvo": f"p{i}", "tipo": "Unidade", "olt": "olt 1"} for i in range(50)]


def falso(ip, t):
    return ("online", 3.0) if int(ip[1:]) % 5 else ("sem_resposta", "")


def test_grava_cada_ciclo_completo():
    with tempfile.TemporaryDirectory() as d:
        coletor.BRUTO = Path(d)
        for _ in range(3):
            coletor.ciclo(PONTOS, 1000, 8, pingador=falso)
        dia = next(Path(d).glob("varredura_*.csv"))
        linhas = list(csv.DictReader(open(dia, encoding="utf-8")))
        ciclos = list(csv.DictReader(open(next(Path(d).glob("ciclos_*.csv")), encoding="utf-8")))
        assert len(linhas) == 3 * len(PONTOS)                       # nenhum ponto perdido
        assert len(ciclos) == 3 and all(c["pontos"] == "50" for c in ciclos)
        assert all(c["responderam"] == "40" for c in ciclos)         # 10 de 50 sem resposta
        assert {l["status"] for l in linhas} == {"online", "sem_resposta"}


def test_reinicio_continua_no_mesmo_arquivo():
    with tempfile.TemporaryDirectory() as d:
        coletor.BRUTO = Path(d)
        coletor.ciclo(PONTOS, 1000, 8, pingador=falso)
        coletor.ciclo(PONTOS, 1000, 8, pingador=falso)                # simula o coletor reiniciado no mesmo dia
        linhas = open(next(Path(d).glob("varredura_*.csv")), encoding="utf-8").read().splitlines()
        assert linhas.count(linhas[0]) == 1                           # cabeçalho uma vez só
        assert len(linhas) == 1 + 2 * len(PONTOS)


def test_ip_lan_vira_primeiro_host():
    assert coletor.ip_lan_alvo("10.171.172.0/24") == "10.171.172.1"
    assert coletor.ip_lan_alvo(None) == ""


if __name__ == "__main__":
    n = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f(); n += 1; print("OK    ", nome)
    print(f"\n{n} testes ok, 0 falha(s)")
