"""Tratamento e integração do cadastro (cards C06 e C07).

Entrada (camada bruta): inventário PANA (ACCESS e PENDÊNCIAS), planilhas de câmeras e Wi-Fi
e o vínculo ONU x mapa. Saída (camada tratada, fora do Git):
    dados/tratado/cadastro_pontos.csv     um registro por ponto, com chave única e marcas de qualidade
    dados/tratado/pendencias_cadastro.xlsx relatório para a equipe (C07)
    dados/tratado/resumo_tratamento.csv   números agregados (usados no relatório acadêmico)

Regras (docs/regras_eventos.md e decisões da Sprint 2):
 - chave = IP de gerência (único; presente em 99,8% dos registros).
 - OLT padronizada para "OLT 01".."OLT 06". "olt x" vira OLT ausente (falha de cadastro), nunca é inventada.
 - Divergência entre OLT do mapa e OLT da planilha é marcada; nenhuma das duas é escolhida automaticamente.
 - Campos ausentes ficam vazios + marca; a ausência de informação nunca vira valor.
 - O status do inventário é guardado só como referência histórica: não é usado como disponibilidade.
"""
import re
import sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DADOS = BASE / "dados"
TRAT = DADOS / "tratado"


def olt_padrao(v):
    m = re.search(r"(\d+)", str(v)) if pd.notna(v) else None
    return f"OLT {int(m.group(1)):02d}" if m else None


def tipo_padrao(v):
    v = str(v).lower()
    return "unidade" if v.startswith("unidade") else "wifi" if "wi-fi" in v else "camera" if "câmera" in v else "olt" if v == "olt" else "switch" if v == "switch" else "outro"


def main(inv=DADOS / "PANA_atualizado.xlsx", cam=DADOS / "projeto_cameras.xlsx", wifi=DADOS / "projeto_wifi.xlsx", vinc=DADOS / "vinculo_onu_mapa.xlsx"):
    TRAT.mkdir(parents=True, exist_ok=True)
    a = pd.read_excel(inv, sheet_name="ACCESS")
    sem_chave = int(a["IP gerência"].isna().sum())          # registro sem IP de gerência: fica de fora e vai para pendências
    a = a[a["IP gerência"].notna()].reset_index(drop=True)
    pend = pd.read_excel(inv, sheet_name="PENDÊNCIAS")
    p = pd.DataFrame({
        "chave": a["IP gerência"].astype(str).str.strip(),
        "nome": a.iloc[:, 0].astype(str).str.strip(),
        "tipo": a["Tipo"].map(tipo_padrao),
        "olt": a["OLT"].map(olt_padrao),
        "olt_original": a["OLT"],
        "porta_gpon": a["GPON"], "onu_id": a["ID"], "serial": a["Serial ONU"],
        "cto": a["CTO"], "ponto_mapa": a["Ponto no mapa (KMZ)"],
        "lat": a["Latitude"], "lon": a["Longitude"], "ip_lan": a["IP LAN"],
        "status_inventario": a["Status"], "fonte_status_inventario": a["Fonte do status"],
    })
    p = p[~p["chave"].isin(["nan", "", "None"])].copy()
    eh_onu = p["tipo"].isin(["unidade", "camera", "wifi"])
    # marcas de qualidade (ausência de informação = falha de cadastro, não indisponibilidade)
    p["sem_olt"] = eh_onu & p["olt"].isna()
    p["sem_porta"] = eh_onu & p["porta_gpon"].isna()
    p["sem_serial"] = eh_onu & p["serial"].isna()
    p["sem_cto"] = eh_onu & p["cto"].isna()
    p["sem_coordenadas"] = p["lat"].isna() | p["lon"].isna()
    p["nome_repetido"] = p["nome"].duplicated(keep=False)
    p["serial_repetido"] = p["serial"].notna() & p["serial"].duplicated(keep=False)
    # câmeras e Wi-Fi: presença nas planilhas específicas (FD03)
    c = pd.read_excel(cam); w = pd.read_excel(wifi)
    p["em_planilha_especifica"] = pd.NA
    p.loc[p["tipo"].eq("camera"), "em_planilha_especifica"] = p["chave"].isin(c["IP ONU"].astype(str).str.strip())
    p.loc[p["tipo"].eq("wifi"), "em_planilha_especifica"] = p["chave"].isin(w["IP ONU"].astype(str).str.strip())
    # vínculo com o mapa (unidades: IP LAN)
    v = pd.read_excel(vinc)
    v["ip_lan"] = v["IP ONU"].astype(str).str.strip()
    v = v.rename(columns={"Confiança": "confianca_mapa", "OLT pelo mapa": "olt_mapa", "OLT confere?": "olt_confere"})
    import ipaddress
    def lan1(x):
        try:
            x = str(x).strip(); return str(next(ipaddress.ip_network(x, strict=False).hosts())) if "/" in x else x
        except ValueError:
            return ""
    p["ip_lan"] = p["ip_lan"].map(lan1)
    p = p.merge(v[["ip_lan", "confianca_mapa", "olt_mapa", "olt_confere"]], on="ip_lan", how="left")
    p["olt_mapa"] = p["olt_mapa"].map(olt_padrao)
    p["divergencia_olt_mapa"] = p["olt_mapa"].notna() & p["olt"].notna() & p["olt_mapa"].ne(p["olt"])
    flags = ["sem_olt", "sem_porta", "sem_serial", "sem_cto", "sem_coordenadas", "nome_repetido", "serial_repetido", "divergencia_olt_mapa"]
    p["qtd_pendencias"] = p[flags].sum(axis=1)
    p["situacao_cadastro"] = p["qtd_pendencias"].map(lambda n: "completo" if n == 0 else "incompleto")
    # posição na topologia: só entra nos indicadores por OLT/porta quando OLT e porta são conhecidas
    p["apto_indicador_olt"] = ~p["sem_olt"] & ~p["sem_porta"] & ~p["divergencia_olt_mapa"]
    p.drop(columns=["ip_lan"]).to_csv(TRAT / "cadastro_pontos.csv", index=False, encoding="utf-8")

    # relatório de pendências (C07)
    linhas = []
    for f in flags:
        sub = p[p[f]]
        for _, r in sub.iterrows():
            linhas.append({"pendencia": f, "nome": r["nome"], "tipo": r["tipo"], "olt": r["olt"] or "", "chave": r["chave"]})
    det = pd.DataFrame(linhas)
    resumo = (det.groupby(["pendencia", "tipo"]).size().unstack(fill_value=0) if len(det) else pd.DataFrame())
    with pd.ExcelWriter(TRAT / "pendencias_cadastro.xlsx") as xw:
        resumo.to_excel(xw, sheet_name="Resumo")
        det.to_excel(xw, sheet_name="Detalhe", index=False)
        pend.to_excel(xw, sheet_name="Pendências do inventário", index=False)
    agg = {"registros_inventario": len(p) + sem_chave, "sem_chave": sem_chave, "registros": len(p), "pontos_onu": int(eh_onu.sum()), "completos": int((p["situacao_cadastro"] == "completo").sum()),
           "aptos_indicador_olt": int(p["apto_indicador_olt"].sum())}
    agg.update({f: int(p[f].sum()) for f in flags})
    agg["pendencias_inventario"] = len(pend)
    pd.Series(agg).to_csv(TRAT / "resumo_tratamento.csv", header=["valor"])
    print(pd.Series(agg).to_string())
    print(resumo.to_string())


if __name__ == "__main__":
    main()
