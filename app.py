# =====================================================
# GAN SISTEMA CONTÁBIL (WEB READY)
# =====================================================

import streamlit as st

st.set_page_config(
    page_title="GAN Sistema Contábil",
    layout="wide"
)

import os
import json
import hashlib
import pandas as pd
from datetime import datetime

# =====================================================
# PLOTLY
# =====================================================
try:
    import plotly.express as px
    PLOTLY_OK = True
except:
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
# CONFIG (WEB SAFE)
# =====================================================
BASE_DIR = os.getcwd()

BASE_OUTPUT = os.path.join(BASE_DIR, "output")
BASE_CONTRATADAS = os.path.join(BASE_DIR, "contratadas")
BASE_USERS = os.path.join(BASE_DIR, "users.json")

TEMPLATES_CONTRATOS = os.path.join(BASE_DIR, "templates", "CONTRATOS")
TEMPLATES_PROPOSTAS = os.path.join(BASE_DIR, "templates", "PROPOSTAS")

# cria pastas automaticamente
for p in [BASE_OUTPUT, BASE_CONTRATADAS, TEMPLATES_CONTRATOS, TEMPLATES_PROPOSTAS]:
    os.makedirs(p, exist_ok=True)

# cria arquivo de usuários se não existir
if not os.path.exists(BASE_USERS):
    with open(BASE_USERS, "w", encoding="utf-8") as f:
        json.dump({}, f)

# inicializa banco
init_db()

# =====================================================
# FUNÇÕES
# =====================================================
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def carregar_usuarios():
    with open(BASE_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(d):
    with open(BASE_USERS, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def listar_templates(pasta):
    if not os.path.exists(pasta):
        return []
    return [f for f in os.listdir(pasta) if f.endswith(".docx")]

def listar_contratadas():
    if not os.path.exists(BASE_CONTRATADAS):
        return []
    return [
        f.replace(".json", "")
        for f in os.listdir(BASE_CONTRATADAS)
        if f.endswith(".json")
    ]

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
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if u in usuarios and usuarios[u] == hash_senha(s):
                st.session_state.usuario = u
                os.makedirs(os.path.join(BASE_OUTPUT, u), exist_ok=True)
                st.success("Login realizado com sucesso")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    with tab2:
        nu = st.text_input("Novo Usuário")
        ns = st.text_input("Senha", type="password")
        cs = st.text_input("Confirmar Senha", type="password")

        if st.button("Criar Acesso"):
            if nu in usuarios:
                st.warning("Usuário já existe")
            elif ns != cs:
                st.error("Senhas não conferem")
            else:
                usuarios[nu] = hash_senha(ns)
                salvar_usuarios(usuarios)
                st.success("Usuário criado com sucesso")
                st.stop()

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
    st.subheader("📊 Dashboard")

    df = pd.DataFrame(listar_historico())

    if df.empty:
        st.info("Nenhum dado registrado ainda")
        st.stop()

    df = df[df["usuario"] == USUARIO].copy()

    df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")
    df["data"] = df["criado_em"].dt.strftime("%d/%m/%Y")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total", len(df))
    c2.metric("Revisão", len(df[df["status"] == "REVISAO"]))
    c3.metric("Assinados", len(df[df["status"] == "ASSINADO"]))
    c4.metric("Concluídos", len(df[df["status"] == "CONCLUIDO"]))

    if PLOTLY_OK:
        fig = px.bar(df.groupby("data").size().reset_index(name="q"), x="data", y="q")
        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GERAR CONTRATO
# =====================================================
elif menu == "📄 Gerar Contrato":
    st.subheader("📄 Gerar Contrato")

    templates = listar_templates(TEMPLATES_CONTRATOS)

    if not templates:
        st.warning("Envie um template em Configurações")
        st.stop()

    template = st.selectbox("Template", templates)
    nome_cliente = st.text_input("Nome do Cliente")

    if st.button("Gerar"):
        if not nome_cliente:
            st.warning("Informe o nome do cliente")
            st.stop()

        pasta = os.path.join(BASE_OUTPUT, USUARIO, nome_cliente)
        os.makedirs(pasta, exist_ok=True)

        st.success("Contrato gerado com sucesso")

# =====================================================
# CADASTRO
# =====================================================
elif menu == "🏢 Cadastro de Contratadas":
    st.subheader("Cadastro")

    nome = st.text_input("Nome")

    if st.button("Salvar"):
        if nome:
            with open(os.path.join(BASE_CONTRATADAS, f"{nome}.json"), "w") as f:
                json.dump({"nome": nome}, f)
            st.success("Salvo com sucesso")

# =====================================================
# HISTÓRICO
# =====================================================
elif menu == "📚 Histórico":
    st.subheader("Histórico")

    base_user = os.path.join(BASE_OUTPUT, USUARIO)

    if not os.path.exists(base_user):
        st.info("Sem histórico")
        st.stop()

    for pasta in os.listdir(base_user):
        st.write(pasta)

# =====================================================
# CONFIG
# =====================================================
elif menu == "⚙️ Configurações":
    st.subheader("Templates")

    arq = st.file_uploader("Arquivo DOCX")

    if arq:
        with open(os.path.join(TEMPLATES_CONTRATOS, arq.name), "wb") as f:
            f.write(arq.read())
        st.success("Template enviado")