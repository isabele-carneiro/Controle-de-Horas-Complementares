import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página da aplicação
st.set_page_config(page_title="Sistema de Validação de AC", layout="wide")

# Ligação à base de dados SQLite
def get_connection():
    return sqlite3.connect("banco.db", check_same_thread=False)

# Inicialização da base de dados e criação das tabelas
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabela de parâmetros de limites de Carga Horária (CH) por Dimensão
    c.execute('''
        CREATE TABLE IF NOT EXISTS parametros (
            dimensao TEXT PRIMARY KEY,
            ch_maxima REAL
        )
    ''')
    
    # Inserir regras padrão caso a tabela esteja vazia
    c.execute("SELECT COUNT(*) FROM parametros")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO parametros VALUES (?, ?)", [
            ("Ensino", 40.0),
            ("Pesquisa", 40.0),
            ("Extensão", 60.0),
            ("Gestão e Representação", 20.0)
        ])
    
    # Tabela principal de Solicitações de AC
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
            status TEXT DEFAULT 'Pendente',
            nome_avaliador TEXT,
            justificativa TEXT,
            registado_siga TEXT DEFAULT 'Não'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.title("🎓 Sistema de Validação de Atividades Complementares (AC)")

# Menu de navegação por perfil de utilizador
perfil = st.sidebar.selectbox(
    "Selecione o Perfil de Acesso:",
    ["Discente (Aluno)", "Avaliador (Docente/Coordenador)", "Técnico Administrativo"]
)

# -----------------------------------------------------------------------------
# PERFIL 1: DISCENTE (ALUNO)
# -----------------------------------------------------------------------------
if perfil == "Discente (Aluno)":
    st.header("Área do Discente")
    separador1, separador2 = st.tabs(["Nova Solicitação (RF-01)", "Meu Extrato de Horas"])
    
    with separador1:
        st.subheader("Submeter Certificado")
        with st.form("form_solicitacao"):
            nome = st.text_input("Nome Completo:")
            cpf = st.text_input("CPF:")
            email = st.text_input("E-mail:")
            
            # Consulta as dimensões disponíveis
            conn = get_connection()
            df_param = pd.read_sql("SELECT dimensao FROM parametros", conn)
            conn.close()
            
            dimensao = st.selectbox("Dimensão da Atividade:", df_param["dimensao"].tolist())
            tipo = st.text_input("Tipo de Atividade (ex: Monitoria, Minicurso):")
            titulo = st.text_input("Título da Atividade:")
            ch_solic = st.number_input("Carga Horária Solicitada (CH):", min_value=0.0, step=1.0)
            link = st.text_input("Link para o Documento Comprovativo:")
            
            submeter = st.form_submit_button("Submeter Solicitação")
            
            if submeter:
                # CA-02: Validação de Entrada
                if ch_solic <= 0:
                    st.error("ERRO: A Carga Horária solicitada deve ser maior que zero!")
                elif not nome or not cpf or not titulo or not link:
                    st.warning("Atenção: Todos os campos obrigatórios devem ser preenchidos.")
                else:
                    # CA-01: Sucesso na Submissão
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO solicitacoes 
                        (nome_aluno, cpf, email, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, data_solicitacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (nome, cpf, email, dimensao, tipo, titulo, ch_solic, link, data_hoje))
                    conn.commit()
                    conn.close()
                    st.success("Solicitação enviada com sucesso! Estado inicial: Pendente.")
                    
    with separador2:
        st.subheader("Consulta de Extrato")
        cpf_busca = st.text_input("Introduza o seu CPF para consultar o seu histórico:")
        if cpf_busca:
            conn = get_connection()
            df_aluno = pd.read_sql_query("SELECT * FROM solicitacoes WHERE cpf = ?", conn, params=(cpf_busca,))
            conn.close()
            
            if not df_aluno.empty:
                st.dataframe(df_aluno[["id", "dimensao", "titulo", "ch_solicitada", "ch_aprovada", "status", "justificativa"]])
                total_aprovado = df_aluno["ch_aprovada"].sum()
                st.metric(label="Total de Carga Horária Aprovada", value=f"{total_aprovado} horas")
            else:
                st.info("Nenhuma solicitação encontrada para o CPF fornecido.")

# -----------------------------------------------------------------------------
# PERFIL 2: AVALIADOR (DOCENTE / COORDENADOR)
# -----------------------------------------------------------------------------
elif perfil == "Avaliador (Docente/Coordenador)":
    st.header("Painel de Avaliação de Pedidos")
    
    conn = get_connection()
    df_pendentes = pd.read_sql_query("SELECT * FROM solicitacoes WHERE status = 'Pendente'", conn)
    conn.close()
    
    if df_pendentes.empty:
        st.success("Não existem solicitações pendentes para avaliação de momento.")
    else:
        st.subheader("Solicitações Aguardando Análise")
        st.dataframe(df_pendentes[["id", "nome_aluno", "dimensao", "tipo_atividade", "titulo", "ch_solicitada", "link_comprovativo"]])
        
        id_sel = st.number_input("Introduza o ID da Solicitação que deseja avaliar:", min_value=1, step=1)
        
        # Procura a solicitação selecionada
        solic = df_pendentes[df_pendentes["id"] == id_sel]
        if not solic.empty:
            dados = solic.iloc[0]
            st.write(f"**Aluno:** {dados['nome_aluno']} | **Dimensão:** {dados['dimensao']} | **CH Solicitada:** {dados['ch_solicitada']}h")
            st.write(f"**Comprovativo:** [Aceder ao Documento]({dados['link_comprovativo']})")
            
            # Consulta o teto da dimensão
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT ch_maxima FROM parametros WHERE dimensao = ?", (dados['dimensao'],))
            teto = c.fetchone()[0]
            
            # Consulta quanto o aluno já acumulou nessa dimensão
            c.execute("SELECT SUM(ch_aprovada) FROM solicitacoes WHERE cpf = ? AND dimensao = ? AND status = 'Aprovado'", (dados['cpf'], dados['dimensao']))
            acumulado = c.fetchone()[0] or 0.0
            conn.close()
            
            disponivel = max(0.0, teto - acumulado)
            st.info(f"Teto da dimensão '{dados['dimensao']}': {teto}h | Já acumulado pelo aluno: {acumulado}h | Limite disponível para aprovação: {disponivel}h")
            
            with st.form("form_avaliacao"):
                nome_prof = st.text_input("Nome do Avaliador:")
                decisao = st.radio("Decisão:", ["Aprovar", "Indeferir"])
                ch_concedida = st.number_input("CH Aprovada:", min_value=0.0, max_value=float(dados['ch_solicitada']), step=1.0)
                justificativa = st.text_area("Justificativa (Obrigatória em caso de indeferimento ou corte de horas):")
                
                submeter_eval = st.form_submit_button("Confirmar Avaliação")
                
                if submeter_eval:
                    # CA-04: Exigência de Justificativa
                    if decisao == "Indeferir" and not justificativa.strip():
                        st.error("ERRO (CA-04): É obrigatório registar a justificativa em caso de indeferimento!")
                    else:
                        # CA-03: Cálculo e aplicação do teto máximo
                        ch_final = 0.0
                        nuevo_status = "Indeferido"
                        
                        if decisao == "Aprovar":
                            # O valor aprovado não pode ultrapassar a folga restante da dimensão
                            ch_final = min(ch_concedida, disponivel)
                            nuevo_status = "Aprovado"
                            if ch_final < ch_concedida:
                                st.warning(f"Atenção (CA-03): A carga horária foi ajustada para {ch_final}h para respeitar o teto máximo da dimensão.")
                        
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute('''
                            UPDATE solicitacoes 
                            SET ch_aprovada = ?, status = ?, nome_avaliador = ?, justificativa = ?
                            WHERE id = ?
                        ''', (ch_final, nuevo_status, nome_prof, justificativa, id_sel))
                        conn.commit()
                        conn.close()
                        st.success(f"Solicitação #{id_sel} avaliada com sucesso como '{nuevo_status}'!")

# -----------------------------------------------------------------------------
# PERFIL 3: TÉCNICO ADMINISTRATIVO
# -----------------------------------------------------------------------------
elif perfil == "Técnico Administrativo":
    st.header("Painel de Controlo Administrativo")
    st.subheader("Processos Avaliados para Registo no SIGA")
    
    conn = get_connection()
    df_avaliados = pd.read_sql_query("SELECT * FROM solicitacoes WHERE status IN ('Aprovado', 'Indeferido')", conn)
    conn.close()
    
    if df_avaliados.empty:
        st.info("Não existem processos avaliados aguardando registo.")
    else:
        st.dataframe(df_avaliados[["id", "nome_aluno", "cpf", "dimensao", "ch_aprovada", "status", "registado_siga"]])
        
        id_siga = st.number_input("ID do processo para atualizar registo no SIGA:", min_value=1, step=1)
        if st.button("Confirmar Registo no SIGA (CA-05)"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE solicitacoes SET registado_siga = 'Sim' WHERE id = ?", (id_siga,))
            conn.commit()
            conn.close()
            st.success(f"Processo #{id_siga} marcado como 'Registado no SIGA' com sucesso!")
