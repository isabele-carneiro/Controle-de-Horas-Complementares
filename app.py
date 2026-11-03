import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página da aplicação
st.set_page_config(page_title="Sistema de Controle de AC", layout="wide")

# Conexão com o banco de dados SQLite
def get_connection():
    return sqlite3.connect("banco.db", check_same_thread=False)

# Inicialização do banco de dados e criação das tabelas
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabela de Usuários (RF-00)
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT,
            perfil TEXT
        )
    ''')
    
    # Tabela de Parâmetros de Carga Horária por Atividade (RF-02)
    c.execute('''
        CREATE TABLE IF NOT EXISTS parametros (
            tipo_atividade TEXT PRIMARY KEY,
            dimensao TEXT,
            teto_horas REAL
        )
    ''')
    
    # Popula regras padrão de tetos por atividade se a tabela estiver vazia
    c.execute("SELECT COUNT(*) FROM parametros")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO parametros VALUES (?, ?, ?)", [
            ("Minicurso / Oficina", "Ensino", 20.0),
            ("Monitoria", "Ensino", 40.0),
            ("Iniciação Científica", "Pesquisa", 40.0),
            ("Projeto de Extensão", "Extensão", 30.0),
            ("Representação Estudantil", "Gestão", 20.0)
        ])
    
    # Tabela principal de Solicitações de AC (RF-01, RF-02, RF-03)
    c.execute('''
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_aluno TEXT,
            cpf TEXT,
            email TEXT,
            dimensao TEXT,
            tipo_atividade TEXT,
            titulo TEXT,
            ch_solicitada REAL,
            link_comprovativo TEXT,
            data_solicitacao TEXT,
            ch_aprovada REAL DEFAULT 0,
            ch_maxima_atingida TEXT DEFAULT 'Não',
            status TEXT DEFAULT 'Pendente',
            nome_avaliador TEXT,
            justificativa TEXT,
            registado_siga TEXT DEFAULT 'Não'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.title("🎓 Sistema de Controle de Atividades Complementares (AC)")

# Controle de Sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["cpf"] = None
    st.session_state["nome"] = None
    st.session_state["email"] = None
    st.session_state["perfil"] = None

# =============================================================================
# RF-00: AUTENTICAÇÃO E CONTROLE DE PERFIL
# =============================================================================
if not st.session_state["logado"]:
    st.subheader("🔐 Autenticação no Sistema")
    
    tab_login, tab_primeiro_acesso = st.tabs(["🔑 Login", "🆕 Primeiro Acesso (Criar Senha)"])
    
    # CA-00a, CA-00b, CA-00c, CA-00d: Login com CPF e Senha
    with tab_login:
        with st.form("form_login"):
            cpf_login = st.text_input("Número do CPF (Apenas dígitos):", key="login_cpf").strip()
            senha_login = st.text_input("Senha:", type="password", key="login_senha").strip()
            btn_entrar = st.form_submit_button("Entrar")
            
            if btn_entrar:
                if not cpf_login or not senha_login:
                    st.error("Credenciais inválidas")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT cpf, nome, email, senha, perfil FROM usuarios WHERE cpf = ?", (cpf_login,))
                    user = c.fetchone()
                    conn.close()
                    
                    if user is None or user[3] != senha_login:
                        # CA-00d: Exibe a mensagem exata de erro
                        st.error("Credenciais inválidas")
                    else:
                        st.session_state["logado"] = True
                        st.session_state["cpf"] = user[0]
                        st.session_state["nome"] = user[1]
                        st.session_state["email"] = user[2]
                        st.session_state["perfil"] = user[4]
                        st.success(f"Login efetuado com sucesso! Perfil: {user[4]}")
                        st.rerun()

    # Primeiro Acesso: Criação de Senha vinculada ao CPF
    with tab_primeiro_acesso:
        st.info("No primeiro acesso, informe seu número de CPF e crie sua senha de utilização futura.")
        with st.form("form_primeiro_acesso"):
            cpf_cad = st.text_input("Número do CPF:", key="cad_cpf").strip()
            nome_cad = st.text_input("Nome Completo:", key="cad_nome").strip()
            email_cad = st.text_input("E-mail:", key="cad_email").strip()
            perfil_cad = st.selectbox(
                "Perfil de Acesso:",
                ["Discente", "Docente/Avaliador", "Técnico Administrativo"],
                key="cad_perfil"
            )
            nova_senha = st.text_input("Crie uma Senha:", type="password", key="cad_senha1").strip()
            confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_senha2").strip()
            
            btn_cadastrar = st.form_submit_button("Cadastrar Senha e Acessar")
            
            if btn_cadastrar:
                if not cpf_cad or not nome_cad or not email_cad or not nova_senha:
                    st.error("Erro no cadastro: Todos os campos são de preenchimento obrigatório.")
                elif nova_senha != confirma_senha:
                    st.error("Erro no cadastro: As senhas informadas não coincidem.")
                else:
                    conn = get_connection()
                    c = conn.cursor()
