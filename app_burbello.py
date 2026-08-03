import streamlit as st
import requests
import time
import pdfplumber
import re
import csv
import io
import json
import os
import hashlib

st.set_page_config(page_title="Ferramentas | Burbello", page_icon="🏢")

if os.path.exists("logo-site.png"):
    st.image("logo-site.png", width=250)

st.title("🏢 Ferramentas | Burbello")

aba_cnpj, aba_folha = st.tabs(["🏢 Consultor de CNPJ", "📄 Extrator de Folha"])

# =========================================================
# ABA 1 - CONSULTOR DE CNPJ
# =========================================================
with aba_cnpj:
    st.header("Consultor de CNPJ")

    cnpj_input = st.text_area(
        "Cole os CNPJs (separados por vírgula)",
        placeholder="00090643000173, 00452964000170",
        height=200,
        key="cnpj_input",
    )

    def limpar_cnpj(cnpj):
        return ''.join(filter(str.isdigit, cnpj))

    def consultar_cnpj(cnpj, tentativas=3):
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
        for i in range(tentativas):
            response = requests.get(url)
            if response.status_code == 200:
                dados = response.json()
                if dados.get("status") != "ERROR":
                    return dados
            elif response.status_code == 429:
                espera = 20 * (i + 1)
                time.sleep(espera)
        return None

    if st.button("Consultar", key="btn_consultar_cnpj"):
        linhas = [l.strip() for l in cnpj_input.strip().replace(";", ",").split(",") if l.strip()]
        if not linhas:
            st.error("Cole ao menos um CNPJ.")
        else:
            resultados = []
            progress = st.progress(0, text="Consultando...")
            for i, linha in enumerate(linhas):
                cnpj = limpar_cnpj(linha)
                if len(cnpj) != 14:
                    resultados.append({"CNPJ": linha, "Razão Social": "CNPJ inválido"})
                else:
                    dados = consultar_cnpj(cnpj)
                    if dados:
                        resultados.append({
                            "CNPJ": linha,
                            "Razão Social": dados.get("nome", "—"),
                        })
                    else:
                        resultados.append({"CNPJ": linha, "Razão Social": "Não encontrado"})
                progress.progress((i + 1) / len(linhas), text=f"Consultando {i+1} de {len(linhas)}...")
                if i < len(linhas) - 1:
                    time.sleep(20)
            progress.empty()

            if resultados:
                st.success(f"{len(resultados)} CNPJs consultados!")
                st.dataframe(resultados, use_container_width=True)

                saida_cnpj = io.StringIO()
                writer_cnpj = csv.DictWriter(
                    saida_cnpj,
                    fieldnames=["CNPJ", "Razão Social"],
                    delimiter=";",
                    extrasaction="ignore",
                )
                writer_cnpj.writeheader()
                writer_cnpj.writerows(resultados)

                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=saida_cnpj.getvalue().encode("utf-8-sig"),
                    file_name="consulta_cnpj.csv",
                    mime="text/csv",
                    key="btn_download_cnpj",
                )
            else:
                st.warning("Nenhum CNPJ válido encontrado.")

# =========================================================
# ABA 2 - EXTRATOR DE FOLHA DE PAGAMENTO
# =========================================================
with aba_folha:
    st.header("Extrator de Folha de Pagamento")

    STORAGE_FILE = "dados_folhas.json"

    def str_para_float(valor_str):
        if not valor_str:
            return 0.0
        return float(valor_str.replace('.', '').replace(',', '.'))

    def float_para_str(valor_float):
        return f"{valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def carregar_dados():
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def salvar_dados(dados):
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def extrair_dados(arquivo):
        with pdfplumber.open(arquivo) as pdf:
            paginas = [p.extract_text() or "" for p in pdf.pages]
        texto = "\n".join(paginas)

        m = re.search(r'Empresa:\s*(\d+)\s*-\s*(.+?)\s+\d{2}/\d{2}/\d{4}', texto)
        codigo_empresa = m.group(1).strip() if m else "NÃO ENCONTRADO"
        nome_empresa   = m.group(2).strip() if m else "NÃO ENCONTRADO"

        m = re.search(r'1 - Empregado\s+(\d+)', texto)
        qtd = m.group(1) if m else "0"

        m = re.search(r'Totais\s*\n\s*Proventos:.*?L[íi]quido:\s*([\d.,]+)', texto, re.DOTALL)
        liquido = m.group(1) if m else "0,00"

        matches_11 = re.findall(r'11\s*-\s*FGTS mensal\s+([\d.,]+)', texto)
        valor_11 = str_para_float(matches_11[-1]) if matches_11 else 0.0

        matches_12 = re.findall(r'12\s*-\s*FGTS\s*13[°º].*?\s+([\d.,]+)', texto)
        valor_12 = str_para_float(matches_12[-1]) if matches_12 else 0.0

        fgts_11_somado = float_para_str(valor_11 + valor_12)

        m_cons = re.search(r'Empr[eé]stimo Cr[eé]dito do Trabalhador\s+\d+\s+([\d.,]+)', texto)
        fgts_consignado = m_cons.group(1) if m_cons else "0,00"

        m_fgts_total = re.search(r'Total FGTS Mensal\s+\d+\s+([\d.,]+)', texto)
        fgts_total = m_fgts_total.group(1) if m_fgts_total else "0,00"

        m_inss = re.search(r'Resumo Contribui[çc][õo]es.*?Total:\s+([\d.,]+)', texto, re.DOTALL)
        inss = m_inss.group(1) if m_inss else "0,00"

        m_irrf = re.search(r'Total IRRF\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)', texto)
        irrf = m_irrf.group(1) if m_irrf else "0,00"

        m_dctf = re.search(r'Total EMPRESA:.*?([\d.,]+)$', texto, re.MULTILINE)
        dctf = m_dctf.group(1) if m_dctf else "0,00"

        m_sind = re.search(r'Total Descontos Sindicais\s+\d+\s+[\d.,]+\s+([\d.,]+)', texto)
        sindicato = m_sind.group(1) if m_sind else "0,00"

        return {
            "Codigo_Empresa":   codigo_empresa,
            "Nome_Empresa":     nome_empresa,
            "Qtd_Funcionarios": qtd,
            "Total_Liquido":    liquido,
            "FGTS_11_Somado":   fgts_11_somado,
            "FGTS_Consignado":  fgts_consignado,
            "FGTS_Total":       fgts_total,
            "INSS":             inss,
            "IRRF":             irrf,
            "Total_Sindicato":  sindicato,
            "DCTFWeb":          dctf,
        }

    registros = carregar_dados()
    arquivo = st.file_uploader("Envie o PDF da Folha", type=["pdf"], key="folha_upload")

    if arquivo:
        conteudo = arquivo.read()
        arquivo.seek(0)
        hash_arquivo = hashlib.md5(conteudo).hexdigest()

        if "ultimo_hash" not in st.session_state or st.session_state.ultimo_hash != hash_arquivo:
            dados = extrair_dados(arquivo)
            if not any(r['Codigo_Empresa'] == dados['Codigo_Empresa'] for r in registros):
                registros.append(dados)
                salvar_dados(registros)
                st.success(f"✅ Sucesso: {dados['Nome_Empresa']}")
            st.session_state.ultimo_hash = hash_arquivo

    if registros:
        st.subheader("📊 Tabela de Resultados")
        st.table(registros)

        col1, col2 = st.columns(2)

        with col1:
            campos = [
                "Codigo_Empresa", "Nome_Empresa", "Qtd_Funcionarios",
                "Total_Liquido", "FGTS_11_Somado", "FGTS_Consignado",
                "FGTS_Total", "INSS", "IRRF", "Total_Sindicato", "DCTFWeb"
            ]

            saida = io.StringIO()
            writer = csv.DictWriter(saida, fieldnames=campos, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(registros)

            st.download_button(
                label="⬇️ Baixar CSV Completo",
                data=saida.getvalue().encode("utf-8-sig"),
                file_name="relatorio_folhas_unificado.csv",
                mime="text/csv",
                key="btn_download_csv",
            )

        with col2:
            if st.button("🗑️ Limpar Tudo", key="btn_limpar_folhas"):
                salvar_dados([])
                st.rerun()
