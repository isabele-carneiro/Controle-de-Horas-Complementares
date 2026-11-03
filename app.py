import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página
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
    
    # Tabela de Parâmetros de Carga Horária (RF-02)
    c.execute('''
        CREATE TABLE IF NOT EXISTS parametros (
            tipo_atividade TEXT PRIMARY KEY,
            dimensao TEXT,
            teto_horas REAL
        )
    ''')
    
    # Popula regras padrão se estiver vazia
    c.execute("SELECT COUNT(*) FROM parametros")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO parametros VALUES (?, ?, ?)", [
            ("Minicurso / Oficina", "Ensino", 20.0),
            ("Monitoria", "Ensino", 40.0),
            ("Iniciação Científica", "Pesquisa", 40.0),
            ("Projeto de Extensão", "Extensão", 30.0),
            ("Representação Estudantil", "Gestão", 20.0)
        ])
    
    # Tabela de Solicitações de AC (RF-01, RF-02, RF-03)
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
    
    # Seleção de modo de acesso fixa e persistente
    opcao_acesso = st.radio(
        "Selecione uma opção:",
        ["🔑 Já tenho senha (Login)", "🆕 Primeiro Acesso (Cadastrar CPF e Senha)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # OPÇÃO 1: LOGIN
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
                            # CA-00d: Falha de autenticação
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

    # OPÇÃO 2: PRIMEIRO ACESSO (CADASTRO)
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
                            
                            # Salva sessão
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
    # Barra Lateral
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
    # CA-00a: PAINEL DO DISCENTE (ALUNO)
    # -----------------------------------------------------------------------------
    if perfil == "Discente":
        st.header("📌 Painel do Discente")
        tab_submeter, tab_extrato = st.tabs(["Submeter Solicitação (RF-01)", "Extrato de Horas"])
        
        # RF-01: Submissão de Solicitação de AC
        with tab_submeter:
            st.subheader("Formulário de Solicitação de AC")
            with st.form("form_solicitacao"):
                st.text_input("Nome do Discente:", value=st.session_state["nome"], disabled=True)
                st.text_input("CPF:", value=st.session_state["cpf"], disabled=True)
                
                conn = get_connection()
                df_param = pd.read_sql("SELECT tipo_atividade, dimensao, teto_horas FROM parametros", conn)
                conn.close()
                
                dimensao = st.selectbox("Dimensão da Atividade:", sorted(df_param["dimensao"].unique()))
                tipo = st.selectbox("Tipo de Atividade Realizada:", df_param[df_param["dimensao"] == dimensao]["tipo_atividade"].tolist())
                titulo = st.text_input("Título da Atividade:")
                ch_solic = st.number_input("Carga Horária Solicitada (CH):", min_value=0.0, step=1.0)
                link_doc = st.text_input("Hiperligação para o Documento Comprovativo:")
                
                btn_submeter = st.form_submit_button("Submeter Solicitação")
                
                if btn_submeter:
                    erros = []
                    if not dimensao:
                        erros.append("Dimensão da atividade")
                    if not tipo:
                        erros.append("Tipo de atividade realizada")
                    if not titulo.strip():
                        erros.append("Título da atividade")
                    if ch_solic <= 0:
                        erros.append("Carga Horária Solicitada (deve ser maior que zero)")
                    if not link_doc.strip():
                        erros.append("Hiperligação para o documento comprovativo")
                    
                    if erros:
                        st.error(f"⚠️ **Envio Impedido (CA-02):** É necessário corrigir os seguintes campos: **{', '.join(erros)}**.")
                    else:
                        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO solicitacoes 
                            (nome_aluno, cpf, email, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, data_solicitacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (st.session_state["nome"], st.session_state["cpf"], st.session_state["email"], dimensao, tipo, titulo, ch_solic, link_doc, data_atual))
                        conn.commit()
                        conn.close()
                        st.success("✅ **Solicitação gravada com sucesso! (CA-01)** Estado: **Pendente** | Data: " + data_atual)

        with tab_extrato:
            st.subheader("Extrato de Saldo do Discente")
            conn = get_connection()
            df_aluno = pd.read_sql_query("SELECT id, dimensao, tipo_atividade, titulo, ch_solicitada, ch_aprovada, ch_maxima_atingida, status, justificativa, registado_siga FROM solicitacoes WHERE cpf = ?", conn, params=(st.session_state["cpf"],))
            conn.close()
            
            if not df_aluno.empty:
                st.dataframe(df_aluno, use_container_width=True)
                total_aprovado = df_aluno["ch_aprovada"].sum()
                st.metric(label="Total de Carga Horária Aprovada", value=f"{total_aprovado} horas")
            else:
                st.info("Nenhuma solicitação cadastrada até o momento.")

    # -----------------------------------------------------------------------------
    # CA-00b: PAINEL DE AVALIAÇÃO DO DOCENTE / AVALIADOR
    # -----------------------------------------------------------------------------
    elif perfil == "Docente/Avaliador":
        st.header("📋 Painel de Avaliação do Docente / Avaliador")
        
        conn = get_connection()
        df_pendentes = pd.read_sql_query("SELECT id, nome_aluno, cpf, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, data_solicitacao FROM solicitacoes WHERE status = 'Pendente'", conn)
        conn.close()
        
        if df_pendentes.empty:
            st.success("Nenhuma solicitação pendente para avaliação no momento.")
        else:
            st.subheader("Solicitações Pendentes de Avaliação")
            st.dataframe(df_pendentes, use_container_width=True)
            
            id_sel = st.number_input("Informe o ID da Solicitação para Avaliar:", min_value=1, step=1)
            solic = df_pendentes[df_pendentes["id"] == id_sel]
            
            if not solic.empty:
                dados = solic.iloc[0]
                st.markdown("---")
                st.markdown(f"### Avaliando Processo #{dados['id']} - Aluno: {dados['nome_aluno']}")
                st.write(f"**Dimensão:** {dados['dimensao']} | **Tipo:** {dados['tipo_atividade']}")
                st.write(f"**Título:** {dados['titulo']} | **CH Solicitada:** {dados['ch_solicitada']}h")
                st.write(f"**Comprovativo:** [Acessar Link]({dados['link_comprovativo']})")
                
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT teto_horas FROM parametros WHERE tipo_atividade = ?", (dados['tipo_atividade'],))
                res_teto = c.fetchone()
                conn.close()
                
                teto_atividade = res_teto[0] if res_teto else 20.0
                st.info(f"ℹ️ **Teto Máximo Configurado para '{dados['tipo_atividade']}':** {teto_atividade} horas.")
                
                with st.form("form_avaliacao"):
                    decisao = st.radio("Ação do Avaliador:", ["Aprovar", "Indeferir"])
                    ch_informada = st.number_input("Carga Horária Aprovada (CH):", min_value=0.0, max_value=float(dados['ch_solicitada']), step=1.0)
                    justificativa = st.text_area("Justificativa da Avaliação (Obrigatória para indeferimentos ou 0h):")
                    
                    btn_confirmar_eval = st.form_submit_button("Guardar Avaliação")
                    
                    if btn_confirmar_eval:
                        if (decisao == "Indeferir" or ch_informada == 0) and not justificativa.strip():
                            st.error("🚫 **Gravação Bloqueada (CA-04):** Quando a CH aprovada for 0 horas (ou em caso de indeferimento), o preenchimento da justificativa é obrigatório!")
                        else:
                            ch_final = 0.0
                            ch_max_atingida = "Não"
                            nuevo_status = "Indeferido"
                            
                            if decisao == "Aprovar":
                                nuevo_status = "Aprovado"
                                if ch_informada >= teto_atividade or dados['ch_solicitada'] >= teto_atividade:
                                    ch_final = min(ch_informada, teto_atividade)
                                    ch_max_atingida = "Sim"
                                    st.warning(f"⚠️ **Teto Atingido (CA-03):** O limite de {teto_atividade}h da atividade foi aplicado. Indicador 'CH máxima atingida' marcado como **Sim**.")
                                else:
                                    ch_final = ch_informada
                            
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute('''
                                UPDATE solicitacoes 
                                SET ch_aprovada = ?, ch_maxima_atingida = ?, status = ?, nome_avaliador = ?, justificativa = ?
                                WHERE id = ?
                            ''', (ch_final, ch_max_atingida, nuevo_status, st.session_state["nome"], justificativa, id_sel))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Processo #{id_sel} avaliado como '{nuevo_status}' com sucesso!")
                            st.rerun()

    # -----------------------------------------------------------------------------
    # CA-00c: PAINEL DO TÉCNICO ADMINISTRATIVO
    # -----------------------------------------------------------------------------
    elif perfil == "Técnico Administrativo":
        st.header("⚙️ Painel do Técnico Administrativo")
        
        conn = get_connection()
        df_avaliados = pd.read_sql_query("SELECT id, nome_aluno, cpf, dimensao, tipo_atividade, ch_aprovada, status, registado_siga FROM solicitacoes WHERE status IN ('Aprovado', 'Indeferido')", conn)
        conn.close()
        
        if df_avaliados.empty:
            st.info("Nenhum processo avaliado pendente de registro no SIG@.")
        else:
            st.subheader("Processos Avaliados para Lançamento no SIG@")
            st.dataframe(df_avaliados, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Confirmar Lançamento no Sistema Acadêmico Oficial (SIG@)")
            
            with st.form("form_siga"):
                id_processo = st.number_input("Informe o ID da Solicitação Avaliada:", min_value=1, step=1)
                confirmar_siga = st.checkbox("Confirmar: Registrado no SIG@?")
                
                btn_siga = st.form_submit_button("Confirmar Integração no SIG@")
                
                if btn_siga:
                    if not confirmar_siga:
                        st.warning("Marque a opção 'Registrado no SIG@?' para confirmar a finalização do processo.")
                    else:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute('''
                            UPDATE solicitacoes 
                            SET registado_siga = 'Sim', status = 'Concluído'
                            WHERE id = ? AND status IN ('Aprovado', 'Indeferido')
                        ''', (id_processo,))
                        linhas_afetadas = c.rowcount
                        conn.commit()
                        conn.close()
                        
                        if linhas_afetadas > 0:
                            st.success(f"✅ **Processo #{id_processo} finalizado com sucesso! (CA-05)** Estado atualizado para **Concluído**.")
                            st.rerun()
                        else:
                            st.error(f"Solicitação #{id_processo} não encontrada ou ainda não avaliada pelo docente.")
