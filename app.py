import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema de Controle de Atividades Complementares", layout="wide")

# Conexão com o banco de dados SQLite
def get_connection():
    return sqlite3.connect("banco.db", check_same_thread=False)

# Inicialização e carregamento da Tabela Oficial de Parâmetros
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT,
            perfil TEXT
        )
    ''')
    
    # 2. Tabela de Parâmetros com os DOIS Tetos + Documento Comprobatório
    c.execute("DROP TABLE IF EXISTS parametros")
    c.execute('''
        CREATE TABLE parametros (
            tipo_atividade TEXT PRIMARY KEY,
            dimensao TEXT,
            ch_por_atividade TEXT,
            ch_maxima_total REAL,
            doc_comprovatorio TEXT
        )
    ''')
    
    # Cadastro completo das 20 atividades com Tetos Individuais e Tetos Acumulados Gerais
    tabela_oficial_parametros = [
        # --- EIXO: ENSINO (6 Opções) ---
        (
            "Disciplinas cursadas com aproveitamento satisfatório em outros cursos da IES ou em outras IES", 
            "Ensino", 
            "Até 15 horas por disciplina", 
            45.0, 
            "Histórico escolar e ementa da disciplina"
        ),
        (
            "Cursos de língua estrangeira em instituições credenciadas com aproveitamento", 
            "Ensino", 
            "Até 10 horas por curso", 
            20.0, 
            "Certificado de conclusão"
        ),
        (
            "Cursos livres relacionados à área de graduação em instituições de ensino com aproveitamento", 
            "Ensino", 
            "Até 10 horas por curso", 
            30.0, 
            "Certificado de conclusão"
        ),
        (
            "Monitoria realizada na FCAP em disciplinas teóricas ou práticas", 
            "Ensino", 
            "15 horas por monitoria/semestre", 
            45.0, 
            "Certificado de participação emitido pela coordenação responsável"
        ),
        (
            "Estágio não curricular", 
            "Ensino", 
            "1 hora por hora realizada", 
            40.0, 
            "Contrato do estágio e relatório de atividades"
        ),
        (
            "Participação em projetos de ensino", 
            "Ensino", 
            "Até 30 horas por projeto", 
            90.0, 
            "Declaração de participação emitida pela coordenação responsável"
        ),

        # --- EIXO: PESQUISA (3 Opções) ---
        (
            "Participação em projetos de iniciação científica", 
            "Pesquisa", 
            "Até 30 horas por projeto", 
            90.0, 
            "Declaração de participação emitida pela Coordenação de Pesquisa"
        ),
        (
            "Publicação de artigos completos em jornais, revistas científicas e anais de eventos", 
            "Pesquisa", 
            "20 horas por artigo", 
            80.0, 
            "Cópia do artigo na plataforma"
        ),
        (
            "Apresentação de trabalho em evento científico com publicação", 
            "Pesquisa", 
            "15 horas por trabalho", 
            90.0, 
            "Certificado de participação e cópia do trabalho"
        ),

        # --- EIXO: EXTENSÃO (9 Opções) ---
        (
            "Participação em palestras como ouvinte", 
            "Extensão", 
            "1 hora por hora realizada", 
            60.0, 
            "Declaração de participação emitida pela comissão organizadora"
        ),
        (
            "Participação como palestrante ou instrutor em minicurso e oficina", 
            "Extensão", 
            "1 hora por hora realizada", 
            40.0, 
            "Declaração de participação emitida pela comissão organizadora"
        ),
        (
            "Participação em congressos, seminários, simpósio, ciclo de conferências, debate, workshop, jornada, oficina e fórum", 
            "Extensão", 
            "1 hora por hora realizada", 
            40.0, 
            "Certificado de participação emitido pela comissão organizadora"
        ),
        (
            "Visita técnica orientada (que não faça parte da carga horária regular)", 
            "Extensão", 
            "3 horas por visita", 
            15.0, 
            "Declaração de participação e relatório assinado"
        ),
        (
            "Participação em projetos de extensão", 
            "Extensão", 
            "Até 30 horas por projeto", 
            90.0, 
            "Declaração de participação emitida pela Coordenação de Extensão"
        ),
        (
            "Participação em cursos de extensão", 
            "Extensão", 
            "1 hora por hora realizada", 
            30.0, 
            "Certificado de participação emitido pela Coordenação de Extensão"
        ),
        (
            "Participação como Presidente ou Diretor da Empresa Júnior", 
            "Extensão", 
            "30 horas por semestre", 
            90.0, 
            "Declaração de participação emitida pela Empresa Júnior"
        ),
        (
            "Participação como membro da Empresa Júnior", 
            "Extensão", 
            "20 horas por semestre", 
            60.0, 
            "Declaração emitida pelo professor responsável pelo projeto"
        ),
        (
            "Participação em atividades acadêmicas ou comunitário-voluntárias oferecidas pelo curso", 
            "Extensão", 
            "Até 10 horas por atividade", 
            30.0, 
            "Declaração de participação emitida pela comissão organizadora"
        ),

        # --- EIXO: GESTÃO (2 Opções) ---
        (
            "Representação de Presidência ou Diretoria do Diretório Acadêmico", 
            "Gestão", 
            "30 horas por semestre", 
            90.0, 
            "Declaração de participação emitida pelo DA"
        ),
        (
            "Participação voluntária no Diretório Acadêmico", 
            "Gestão", 
            "20 horas por semestre", 
            60.0, 
            "Declaração de participação emitida pelo DA"
        )
    ]
    c.executemany("INSERT INTO parametros VALUES (?, ?, ?, ?, ?)", tabela_oficial_parametros)

    # 3. Tabela de Solicitações de AC
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
            comprovativo_nome TEXT,
            comprovativo_blob BLOB,
            data_solicitacao TEXT,
            ch_aprovada REAL DEFAULT 0,
            ch_maxima_atingida TEXT DEFAULT 'Não',
            status TEXT DEFAULT 'Pendente',
            nome_avaliador TEXT,
            justificativa TEXT,
            registado_siga TEXT DEFAULT 'Não'
        )
    ''')
    
    c.execute("PRAGMA table_info(solicitacoes)")
    colunas_solic = [row[1] for row in c.fetchall()]
    if "comprovativo_nome" not in colunas_solic:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN comprovativo_nome TEXT")
    if "comprovativo_blob" not in colunas_solic:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN comprovativo_blob BLOB")
    if "ch_maxima_atingida" not in colunas_solic:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN ch_maxima_atingida TEXT DEFAULT 'Não'")

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
# AUTENTICAÇÃO E CONTROLE DE PERFIL
# =============================================================================
if not st.session_state["logado"]:
    st.subheader("🔐 Autenticação no Sistema")
    
    opcao_acesso = st.radio(
        "Selecione uma opção:",
        ["🔑 Já tenho senha (Login)", "🆕 Primeiro Acesso (Cadastrar CPF e Senha)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # LOGIN REGULAR
    if opcao_acesso == "🔑 Já tenho senha (Login)":
        st.markdown("### Entrar com CPF e Senha")
        with st.form("form_login"):
            cpf_login = st.text_input("Número do CPF (Apenas dígitos):").strip()
            senha_login = st.text_input("Senha:", type="password").strip()
            btn_entrar = st.form_submit_button("Entrar")
            
            if btn_entrar:
                if not cpf_login or not senha_login:
                    st.error("Credenciais inválidas")
                else:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT cpf, nome, email, senha, perfil FROM usuarios WHERE cpf = ?", (cpf_login,))
                        user = c.fetchone()
                        conn.close()
                        
                        if user is None or user[3] != senha_login:
                            st.error("Credenciais inválidas")
                        else:
                            st.session_state["logado"] = True
                            st.session_state["cpf"] = user[0]
                            st.session_state["nome"] = user[1]
                            st.session_state["email"] = user[2]
                            st.session_state["perfil"] = user[4]
                            st.success(f"Login realizado com sucesso! Bem-vindo(a), {user[1]}.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao conectar ao banco de dados: {e}")

    # PRIMEIRO ACESSO (CADASTRO)
    else:
        st.markdown("### Cadastro de Primeiro Acesso")
        st.info("Preencha todos os campos abaixo para cadastrar seu CPF e definir sua senha de acesso.")
        
        with st.form("form_primeiro_acesso"):
            cpf_cad = st.text_input("Número do CPF (Ex: 12345678900):").strip()
            nome_cad = st.text_input("Nome Completo:").strip()
            email_cad = st.text_input("E-mail:").strip()
            perfil_cad = st.selectbox(
                "Perfil de Acesso:",
                ["Discente", "Docente/Avaliador", "Técnico Administrativo"]
            )
            nova_senha = st.text_input("Crie uma Senha:", type="password").strip()
            confirma_senha = st.text_input("Confirme a Senha:", type="password").strip()
            
            btn_cadastrar = st.form_submit_button("Cadastrar Senha e Entrar")
            
            if btn_cadastrar:
                if not cpf_cad or not nome_cad or not email_cad or not nova_senha:
                    st.error("⚠️ Preencha todos os campos obrigatórios para realizar o cadastro.")
                elif nova_senha != confirma_senha:
                    st.error("⚠️ As senhas digitadas não coincidem! Digite a mesma senha nos dois campos.")
                else:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT senha FROM usuarios WHERE cpf = ?", (cpf_cad,))
                        existente = c.fetchone()
                        
                        if existente and existente[0] is not None and existente[0] != "":
                            st.warning("Este CPF já possui uma senha cadastrada! Alterne para a opção 'Já tenho senha (Login)'.")
                            conn.close()
                        else:
                            c.execute('''
                                INSERT OR REPLACE INTO usuarios (cpf, nome, email, senha, perfil)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (cpf_cad, nome_cad, email_cad, nova_senha, perfil_cad))
                            conn.commit()
                            conn.close()
                            
                            st.session_state["logado"] = True
                            st.session_state["cpf"] = cpf_cad
                            st.session_state["nome"] = nome_cad
                            st.session_state["email"] = email_cad
                            st.session_state["perfil"] = perfil_cad
                            st.success("✅ Senha cadastrada com sucesso! Entrando no sistema...")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar cadastro no banco de dados: {e}")

# =============================================================================
# ÁREA LOGADA - DIRECIONAMENTO POR PERFIL
# =============================================================================
else:
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['nome']}")
    st.sidebar.markdown(f"🆔 **CPF:** {st.session_state['cpf']}")
    st.sidebar.markdown(f"🛡️ **Perfil Ativo:** {st.session_state['perfil']}")
    
    if st.sidebar.button("🚪 Sair / Encerrar Sessão"):
        st.session_state["logado"] = False
        st.session_state["cpf"] = None
        st.session_state["nome"] = None
        st.session_state["email"] = None
        st.session_state["perfil"] = None
        st.rerun()

    perfil = st.session_state["perfil"]

    # -----------------------------------------------------------------------------
    # PAINEL DO DISCENTE (ALUNO)
    # -----------------------------------------------------------------------------
    if perfil == "Discente":
        st.header("📌 Painel do Discente")
        tab_submeter, tab_extrato, tab_quadro = st.
