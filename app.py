# =====================================================
# EBRASIL AUTOMAÇÃO
# Contratos e Propostas - APP FINAL CONSOLIDADO
# =====================================================

import streamlit as st
import os
import json
import hashlib
import pandas as pd
from datetime import datetime, date

# =====================================================
# PLOTLY
# =====================================================
try:
    import plotly.express as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

# =====================================================
# IMPORTS DO SISTEMA
# =====================================================
from document_utils import gerar_documento
from pdf_utils import gerar_pdf
from database import (
    salvar_documento,
    salvar_historico,
    init_db,
    listar_historico
)

# =====================================================
# CONFIGURAÇÃO INICIAL
# =====================================================
init_db()
st.set_page_config(page_title="EBRASIL AUTOMAÇÃO", layout="wide")

BASE_OUTPUT = "output"
BASE_CONTRATADAS = "contratadas"
BASE_USERS = "users.json"

TEMPLATES_CONTRATOS = "templates/CONTRATOS"
TEMPLATES_PROPOSTAS = "templates/PROPOSTAS"

for p in [BASE_OUTPUT, BASE_CONTRATADAS, TEMPLATES_CONTRATOS, TEMPLATES_PROPOSTAS]:
    os.makedirs(p, exist_ok=True)

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def carregar_usuarios():
    if not os.path.exists(BASE_USERS):
        with open(BASE_USERS, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(BASE_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(d):
    with open(BASE_USERS, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def listar_templates(pasta):
    return [f for f in os.listdir(pasta) if f.endswith(".docx")]

def listar_contratadas():
    return [
        f.replace(".json", "")
        for f in os.listdir(BASE_CONTRATADAS)
        if f.endswith(".json")
    ]

def formatar_moeda(valor):
    try:
        v = float(valor.replace(".", "").replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

# =====================================================
# LOGIN
# =====================================================
usuarios = carregar_usuarios()

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    st.title("🔐 Acesso ao Sistema")

    tab1, tab2 = st.tabs(["Entrar", "Primeiro Acesso"])

    with tab1:
        u = st.text_input("Usuário", key="login_user")
        s = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Entrar", key="btn_login"):
            if u in usuarios and usuarios[u] == hash_senha(s):
                st.session_state.usuario = u
                os.makedirs(os.path.join(BASE_OUTPUT, u), exist_ok=True)
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    with tab2:
        nu = st.text_input("Novo Usuário", key="cad_user")
        ns = st.text_input("Senha", type="password", key="cad_pass")
        cs = st.text_input("Confirmar Senha", type="password", key="cad_conf")

        if st.button("Criar Acesso", key="btn_cad"):
            if nu in usuarios:
                st.warning("Usuário já existe")
            elif ns != cs:
                st.error("Senhas não conferem")
            else:
                usuarios[nu] = hash_senha(ns)
                salvar_usuarios(usuarios)
                os.makedirs(os.path.join(BASE_OUTPUT, nu), exist_ok=True)
                st.success("Usuário criado com sucesso")
                st.stop()

USUARIO = st.session_state.usuario

# =====================================================
# MENU
# =====================================================
MENU_OPCOES = [
    "📊 Dashboard",
    "📄 Gerar Contrato",
    "🏢 Cadastro de Contratadas",
    "📚 Histórico",
    "⚙️ Configurações"
]

menu = st.sidebar.radio("📌 Menu", MENU_OPCOES)

# =====================================================
# DASHBOARD
# =====================================================
if menu == "📊 Dashboard":
    st.subheader("📊 Dashboard Inteligente")

    df = pd.DataFrame(listar_historico())

    if df.empty:
        st.info("Nenhum dado registrado ainda")
        st.stop()

    # 🔐 Dashboard por usuário
    df = df[df["usuario"] == USUARIO].copy()

    df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")
    df["data"] = df["criado_em"].dt.strftime("%d/%m/%Y")

    # =========================
    # MÉTRICAS
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📄 Total", len(df))
    c2.metric("🟡 Revisão", len(df[df["status"] == "REVISAO"]))
    c3.metric("🟢 Assinados", len(df[df["status"] == "ASSINADO"]))
    c4.metric("🔵 Concluídos", len(df[df["status"] == "CONCLUIDO"]))

    # =========================
    # GRÁFICOS
    # =========================
    if PLOTLY_OK:
        col1, col2 = st.columns(2)

        with col1:
            df_group = (
                df.groupby("data")
                .size()
                .reset_index(name="Quantidade")
                .sort_values("data")
            )

            fig = px.bar(
                df_group,
                x="data",
                y="Quantidade",
                title="📅 Documentos por Dia"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.pie(
                df.groupby("status")
                .size()
                .reset_index(name="Quantidade"),
                names="status",
                values="Quantidade",
                title="📌 Status dos Documentos"
            )
            st.plotly_chart(fig2, use_container_width=True)

        # =========================
        # 💰 FATURAMENTO MENSAL
        # =========================
        if "valor" not in df.columns:
            df["valor"] = "0"

        df["valor_num"] = (
            df["valor"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )

        df["valor_num"] = pd.to_numeric(
            df["valor_num"], errors="coerce"
        ).fillna(0)

        df["mes"] = df["criado_em"].dt.to_period("M").astype(str)

        faturamento = (
            df.groupby("mes")["valor_num"]
            .sum()
            .reset_index()
        )

        fig_fat = px.bar(
            faturamento,
            x="mes",
            y="valor_num",
            title="💰 Faturamento Mensal",
            labels={"valor_num": "R$"}
        )
        st.plotly_chart(fig_fat, use_container_width=True)

# =====================================================
# GERAR CONTRATO
# =====================================================
elif menu == "📄 Gerar Contrato":
    st.subheader("📄 Gerar Contrato")

    template = st.selectbox("Template", listar_templates(TEMPLATES_CONTRATOS))

    st.markdown("### 👤 CONTRATANTE")
    dados = {
        "CONTRATANTE_NOME": st.text_input("Nome do Cliente"),
        "CONTRATANTE_CNPJ": st.text_input("CNPJ"),
        "CONTRATANTE_ENDERECO": st.text_input("Endereço"),
        "CONTRATANTE_CIDADE_UF": st.text_input("Cidade / UF"),
        "CONTRATANTE_RESPONSAVEL": st.text_input("Responsável Legal"),
        "DATA_ATUALIZADA": date.today().strftime("%d/%m/%Y")
    }

    st.markdown("### 📑 Informações do Contrato")
    dados["REGIME_TRIBUTARIO"] = st.selectbox(
        "Regime Tributário",
        ["Simples Nacional", "Lucro Presumido", "Lucro Real"]
    )

    dados["TIPO_SERVICOS"] = st.text_input("Tipo de Serviços")
    dados["SERVICOS"] = st.text_area("Descrição dos Serviços", height=150)
    dados["INICIO_ATIVIDADES"] = st.date_input("Início das Atividades").strftime("%d/%m/%Y")
    dados["BALANCETE_CONTABIL"] = st.selectbox(
        "Entrega de Balancete",
        ["Mensal", "Trimestral", "Anual"]
    )

    setor = st.selectbox(
        "Setor",
        ["Fiscal", "Contábil", "Contabilidade Completa", "Pessoal", "Consultoria", "Jurídico"]
    )

    st.markdown("### 🏢 CONTRATADA")
    contratada = st.selectbox("Selecione", listar_contratadas())

    if contratada:
        with open(os.path.join(BASE_CONTRATADAS, f"{contratada}.json"), encoding="utf-8") as f:
            dados.update(json.load(f))

    st.markdown("### 💰 Financeiro")
    dados["VALOR"] = formatar_moeda(st.text_input("Valor do Contrato"))
    dados["PERCENTUAL"] = st.text_input("Percentual (%)")

    if st.button("🚀 Gerar Contrato"):
        pasta_destino = os.path.join(BASE_OUTPUT, USUARIO, dados["CONTRATANTE_NOME"], setor)
        os.makedirs(pasta_destino, exist_ok=True)

        docx = gerar_documento(
            os.path.join(TEMPLATES_CONTRATOS, template),
            dados,
            "CONTRATO",
            dados["CONTRATANTE_NOME"],
            pasta_destino
        )

        gerar_pdf(docx)

        salvar_documento("CONTRATO", dados["CONTRATANTE_NOME"], docx, USUARIO, "REVISAO")

        salvar_historico({
            "criado_em": datetime.now(),
            "cliente": dados["CONTRATANTE_NOME"],
            "usuario": USUARIO,
            "setor": setor,
            "arquivo": os.path.basename(docx),
            "status": "REVISAO",
            "valor": dados["VALOR"]
        })

        st.success("✅ Contrato gerado com sucesso!")

# =====================================================
# CADASTRO DE CONTRATADAS
# =====================================================
elif menu == "🏢 Cadastro de Contratadas":
    st.subheader("🏢 Cadastro da CONTRATADA")

    with st.form("form_contratada"):
        nome = st.text_input("Razão Social", key="ct_nome")
        cnpj = st.text_input("CNPJ", key="ct_cnpj")
        endereco = st.text_input("Endereço", key="ct_end")
        cidade = st.text_input("Cidade / UF", key="ct_cid")
        responsavel = st.text_input("Responsável Legal", key="ct_resp")

        banco = st.text_input("Banco", key="ct_banco")
        agencia = st.text_input("Agência", key="ct_ag")
        conta = st.text_input("Conta Corrente", key="ct_cc")

        if st.form_submit_button("Salvar"):
            dados = {
                "CONTRATADA_NOME": nome,
                "CONTRATADA_CNPJ": cnpj,
                "CONTRATADA_ENDERECO": endereco,
                "CONTRATADA_CIDADE": cidade,
                "CONTRATADA_RESPONSAVEL": responsavel,
                "BANCO": banco,
                "AGENCIA": agencia,
                "CONTA_CORRENTE": conta
            }

            with open(
                os.path.join(BASE_CONTRATADAS, f"{nome.replace(' ', '_')}.json"),
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)

            st.success("Contratada cadastrada com sucesso")

# =====================================================
# HISTÓRICO
# =====================================================
elif menu == "📚 Histórico":
    st.subheader("📚 Histórico")

    base_user = os.path.join(BASE_OUTPUT, USUARIO)
    for empresa in os.listdir(base_user):
        st.markdown(f"### 🏢 {empresa}")
        for setor in os.listdir(os.path.join(base_user, empresa)):
            pasta = os.path.join(base_user, empresa, setor)
            for arq in os.listdir(pasta):
                st.download_button(
                    arq,
                    open(os.path.join(pasta, arq), "rb"),
                    file_name=arq
                )

# =====================================================
# CONFIGURAÇÕES
# =====================================================
elif menu == "⚙️ Configurações":
    st.subheader("⚙️ Configurações de Templates")

    tipo = st.selectbox("Tipo", ["Contrato", "Proposta"])
    arq = st.file_uploader("Arquivo DOCX", type=["docx"])
    nome = st.text_input("Nome do Template")

    if st.button("Salvar") and arq:
        pasta = TEMPLATES_CONTRATOS if tipo == "Contrato" else TEMPLATES_PROPOSTAS
        with open(os.path.join(pasta, f"{nome}.docx"), "wb") as f:
            f.write(arq.read())
        st.success("Template salvo com sucesso")
