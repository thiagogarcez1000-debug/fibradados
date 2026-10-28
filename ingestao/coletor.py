"""Coletor de varreduras – FibraDados (card C04).

Testa todos os pontos do inventário por ping a cada ciclo e grava o resultado
de cada ciclo em disco imediatamente (docs/regras_eventos.md, seção 6).

Uso (na pasta do projeto):
    python ingestao/coletor.py            (usa dados/pontos_coletor.csv; sem bibliotecas externas)
    python ingestao/coletor.py --inventario dados/PANA_atualizado.xlsx   (gera o CSV; precisa de openpyxl)
Opções: --intervalo 300 (s)  --timeout 1000 (ms)  --threads 64  --uma-vez

Saída (pasta dados/bruto/, fora do Git):
    varredura_AAAA-MM-DD.csv  -> data_hora, ciclo_id, chave, tipo, olt, status, rtt_ms
    ciclos_AAAA-MM-DD.csv     -> ciclo_id, inicio, fim, pontos, responderam
    coletor.log
Somente leitura: o coletor só envia ping; não altera nenhum equipamento.
"""
import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import os
import platform
import re
import subprocess
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BRUTO = BASE / "dados" / "bruto"
WINDOWS = platform.system() == "Windows"
RTT = re.compile(r"(?:tempo|time)[=<]\s*(\d+(?:[.,]\d+)?)\s*ms", re.I)


def log(msg):
    BRUTO.mkdir(parents=True, exist_ok=True)
    linha = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha, flush=True)
    with open(BRUTO / "coletor.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def ip_lan_alvo(lan):
    """O inventário guarda a rede LAN (ex.: 10.171.172.0/24); o Gerenciador pinga o primeiro host (.1)."""
    import ipaddress
    lan = str(lan or "").strip()
    if not lan or lan.lower() == "none":
        return ""
    try:
        rede = ipaddress.ip_network(lan, strict=False)
        return str(next(rede.hosts())) if "/" in lan else lan
    except ValueError:
        return ""


def carregar_pontos_csv(caminho):
    """Lê a lista de pontos exportada (dados/pontos_coletor.csv), sem precisar de bibliotecas externas."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def exportar_pontos(pontos, caminho):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["chave", "alvo", "tipo", "olt"])
        w.writeheader(); w.writerows(pontos)


def carregar_pontos(caminho):
    """Lê a aba ACCESS do inventário (precisa do openpyxl). Unidades: IP LAN; câmeras/APs/OLT/switch: IP de gerência
    (mesma regra do Gerenciador de ONUs)."""
    import openpyxl
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb["ACCESS"]
    linhas = ws.iter_rows(values_only=True)
    cab = [str(c).strip() if c is not None else "" for c in next(linhas)]
    idx = {n: i for i, n in enumerate(cab)}
    pontos = []
    for r in linhas:
        ger = str(r[idx["IP gerência"]] or "").strip()
        if not ger:
            continue
        tipo = str(r[idx["Tipo"]] or "").strip()
        lan = ip_lan_alvo(r[idx["IP LAN"]]) if "IP LAN" in idx else ""
        alvo = lan if tipo.startswith("Unidade") and lan else ger
        pontos.append({"chave": ger, "alvo": alvo, "tipo": tipo, "olt": str(r[idx["OLT"]] or "").strip().lower()})
    return pontos


def pingar(ip, timeout_ms):
    cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip] if WINDOWS else ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_ms / 1000 + 3,
                           creationflags=0x08000000 if WINDOWS else 0)
        ok = p.returncode == 0 and "TTL=" in p.stdout.upper()
        m = RTT.search(p.stdout)
        return ("online" if ok else "sem_resposta"), (float(m.group(1).replace(",", ".")) if ok and m else "")
    except Exception:
        return "sem_resposta", ""


def ciclo(pontos, timeout_ms, threads, pingador=pingar):
    inicio = dt.datetime.now()
    cid = inicio.strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:4]
    with cf.ThreadPoolExecutor(threads) as ex:
        res = list(ex.map(lambda p: pingador(p["alvo"], timeout_ms), pontos))
    fim = dt.datetime.now()
    dia = inicio.strftime("%Y-%m-%d")
    BRUTO.mkdir(parents=True, exist_ok=True)
    arq = BRUTO / f"varredura_{dia}.csv"
    novo = not arq.exists()
    with open(arq, "a", newline="", encoding="utf-8") as f:       # grava o ciclo inteiro de uma vez
        w = csv.writer(f)
        if novo:
            w.writerow(["data_hora", "ciclo_id", "chave", "tipo", "olt", "status", "rtt_ms"])
        for p, (st, rtt) in zip(pontos, res):
            w.writerow([inicio.isoformat(timespec="seconds"), cid, p["chave"], p["tipo"], p["olt"], st, rtt])
        f.flush(); os.fsync(f.fileno())
    ctrl = BRUTO / f"ciclos_{dia}.csv"
    novo = not ctrl.exists()
    resp = sum(1 for st, _ in res if st == "online")
    with open(ctrl, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["ciclo_id", "inicio", "fim", "pontos", "responderam"])
        w.writerow([cid, inicio.isoformat(timespec="seconds"), fim.isoformat(timespec="seconds"), len(pontos), resp])
        f.flush(); os.fsync(f.fileno())
    log(f"ciclo {cid}: {len(pontos)} pontos, {resp} responderam, {(fim - inicio).total_seconds():.1f} s")
    return cid, resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventario", default=str(BASE / "dados" / "PANA_atualizado.xlsx"))
    ap.add_argument("--pontos", default=str(BASE / "dados" / "pontos_coletor.csv"),
                    help="lista de pontos em CSV; se existir, é usada no lugar do inventário")
    ap.add_argument("--intervalo", type=int, default=300)
    ap.add_argument("--timeout", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=64)
    ap.add_argument("--uma-vez", action="store_true")
    a = ap.parse_args()
    if Path(a.pontos).exists():
        pontos = carregar_pontos_csv(a.pontos)
    else:
        pontos = carregar_pontos(a.inventario)
        exportar_pontos(pontos, a.pontos)
    log(f"coletor iniciado: {len(pontos)} pontos, intervalo {a.intervalo} s")
    while True:
        t0 = time.time()
        try:
            ciclo(pontos, a.timeout, a.threads)
        except Exception as e:                                   # nunca para em silêncio: registra e segue
            log(f"ERRO no ciclo: {e!r}")
        if a.uma_vez:
            break
        time.sleep(max(5, a.intervalo - (time.time() - t0)))


if __name__ == "__main__":
    main()
