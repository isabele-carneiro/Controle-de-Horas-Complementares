import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =============================================================================
# CONFIGURAÇÃO INICIAL DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Sistema de Controle de Atividades Complementares (AC) - FCAP/UPE",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# BANCO DE DADOS - CONEXÃO E INICIALIZAÇÃO
# =============================================================================
def get_connection():
    """Retorna uma conexão ativa com o banco de dados SQLite."""
    return sqlite3.connect("banco.db", check_same_thread=False)

def init_db():
    """
    Inicializa a estrutura do banco de dados SQLite.
    Cria as tabelas caso não existam e garante a carga completa do regulamento oficial.
    """
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabela de Usuários (Discente, Docente, Técnico)
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)
    
    # 2. Tabela de Parâmetros do Regulamento (Tetos e Documentos)
    c.execute("""
        CREATE TABLE IF NOT EXISTS parametros (
            tipo_atividade TEXT PRIMARY KEY,
            dimensao TEXT NOT NULL,
            ch_por_atividade TEXT NOT NULL,
            ch_maxima_total REAL NOT NULL,
            doc_comprovatorio TEXT NOT NULL
        )
    """)
    
    # 3. Tabela de Solicitações de AC
    c.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_aluno TEXT NOT NULL,
            cpf TEXT NOT NULL,
            email TEXT NOT NULL,
            dimensao TEXT NOT NULL,
            tipo_atividade TEXT NOT NULL,
            titulo TEXT NOT NULL,
            ch_solicitada REAL NOT NULL,
            link_comprovativo TEXT,
            comprovativo_nome TEXT,
            comprovativo_blob BLOB,
            data_solicitacao TEXT NOT NULL,
            ch_aprovada REAL DEFAULT 0.0,
            ch_maxima_atingida TEXT DEFAULT 'Não',
            status TEXT DEFAULT 'Pendente',
            nome_avaliador TEXT,
            justificativa TEXT,
            registado_siga TEXT DEFAULT 'Não'
        )
    """)
    
    # Garantia de Migração: Adiciona colunas eventualmente ausentes em bancos legados
    c.execute("PRAGMA table_info(solicitacoes)")
    colunas_existentes = [row[1] for row in c.fetchall()]
    
    if "comprovativo_nome" not in colunas_existentes:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN comprovativo_nome TEXT")
    if "comprovativo_blob" not in colunas_existentes:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN comprovativo_blob BLOB")
    if "ch_maxima_atingida" not in colunas_existentes:
        c.execute("ALTER TABLE solicitacoes ADD COLUMN ch_maxima_atingida TEXT DEFAULT 'Não'")

    # Cadastro / Atualização Garantida de todas as 20 Atividades Oficiais do Regulamento
    tabela_oficial_parametros = [
        # --- EIXO 1: ENSINO (6 Atividades) ---
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

        # --- EIXO 2: PESQUISA (3 Atividades) ---
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

        # --- EIXO 3: EXTENSÃO (9 Atividades) ---
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

        # --- EIXO 4: GESTÃO (2 Atividades) ---
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
    
    c.executemany("INSERT OR REPLACE INTO parametros VALUES (?, ?, ?, ?, ?)", tabela_oficial_parametros)
    conn.commit()
    conn.close()

# Executa inicialização na subida da aplicação
init_db()

# =============================================================================
# FUNÇÕES AUXILIARES DE CONSULTA E NAVEGAÇÃO DO BANCO
# =============================================================================
def carregar_parametros():
    """Carrega todos os parâmetros do regulamento em um DataFrame."""
    conn = get_connection()
    df = pd.read_sql("SELECT tipo_atividade, dimensao, ch_por_atividade, ch_maxima_total, doc_comprovatorio FROM parametros", conn)
    conn.close()
    return df

def carregar_horas_acumuladas_por_eixo(cpf_aluno):
    """Retorna um dicionário com o total de horas aprovadas/concluídas por eixo do aluno."""
    conn = get_connection()
    query = """
        SELECT dimensao, SUM(ch_aprovada) as total_aprovado 
        FROM solicitacoes 
        WHERE cpf = ? AND status IN ('Aprovado', 'Aprovado Parcialmente', 'Concluído') 
        GROUP BY dimensao
    """
    df = pd.read_sql(query, conn, params=(cpf_aluno,))
    conn.close()
    if df.empty:
        return {}
    return dict(zip(df["dimensao"], df["total_aprovado"]))

def carregar_solicitacoes_aluno(cpf_aluno):
    """Carrega todas as solicitações registradas para o aluno informado."""
    conn = get_connection()
    query = """
        SELECT id, dimensao, tipo_atividade, titulo, ch_solicitada, ch_aprovada, 
               ch_maxima_atingida, status, justificativa, registado_siga, data_solicitacao 
        FROM solicitacoes 
        WHERE cpf = ? 
        ORDER BY id DESC
    """
    df = pd.read_sql_query(query, conn, params=(cpf_aluno,))
    conn.close()
    return df

def carregar_solicitacoes_pendentes():
    """Carrega a lista de solicitações pendentes para avaliação docente."""
    conn = get_connection()
    query = """
        SELECT id, nome_aluno, cpf, email, dimensao, tipo_atividade, titulo, 
               ch_solicitada, link_comprovativo, comprovativo_nome, data_solicitacao 
        FROM solicitacoes 
        WHERE status = 'Pendente' 
        ORDER BY id ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def carregar_solicitacoes_avaliadas():
    """Carrega solicitações já avaliadas aguardando lançamento no SIG@."""
    conn = get_connection()
    query = """
        SELECT id, nome_aluno, cpf, dimensao, tipo_atividade, ch_aprovada, status, registado_siga, data_solicitacao 
        FROM solicitacoes 
        WHERE status IN ('Aprovado', 'Aprovado Parcialmente', 'Indeferido', 'Negado') 
        ORDER BY id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# =============================================================================
# CONTROLE DE SESSÃO E AUTENTICAÇÃO
# =============================================================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["cpf"] = None
    st.session_state["nome"] = None
    st.session_state["email"] = None
    st.session_state["perfil"] = None

st.title("🎓 Sistema de Controle de Atividades Complementares (AC)")
st.caption("Faculdade de Ciências da Administração de Pernambuco - FCAP/UPE")

if not st.session_state["logado"]:
    st.subheader("🔐 Autenticação no Sistema")
    
    opcao_acesso = st.radio(
        "Escolha como deseja acessar:",
        ["🔑 Já tenho cadastro (Login)", "🆕 Primeiro Acesso (Cadastrar CPF e Definir Senha)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # OPÇÃO 1: LOGIN DE USUÁRIO JÁ CADASTRADO
    # -------------------------------------------------------------------------
    if opcao_acesso == "🔑 Já tenho cadastro (Login)":
        st.markdown("### Entrar com CPF e Senha")
        with st.form("form_login"):
            cpf_login = st.text_input("Número do CPF (Apenas dígitos):").strip()
            senha_login = st.text_input("Senha de Acesso:", type="password").strip()
            btn_entrar = st.form_submit_button("Entrar no Sistema")
            
            if btn_entrar:
                if not cpf_login or not senha_login:
                    st.error("⚠️ Por favor, informe o CPF e a senha para acessar.")
                else:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT cpf, nome, email, senha, perfil FROM usuarios WHERE cpf = ?", (cpf_login,))
                        user = c.fetchone()
                        conn.close()
                        
                        if user is None or user[3] != senha_login:
                            st.error("🚫 CPF ou senha incorretos! Verifique suas credenciais.")
                        else:
                            st.session_state["logado"] = True
                            st.session_state["cpf"] = user[0]
                            st.session_state["nome"] = user[1]
                            st.session_state["email"] = user[2]
                            st.session_state["perfil"] = user[4].strip()
                            st.success(f"✅ Login realizado com sucesso! Bem-vindo(a), {user[1]}.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao conectar ao banco de dados: {e}")

    # -------------------------------------------------------------------------
    # OPÇÃO 2: PRIMEIRO ACESSO / CADASTRO DE NOVO USUÁRIO
    # -------------------------------------------------------------------------
    else:
        st.markdown("### Cadastro de Primeiro Acesso")
        st.info("Preencha todos os campos obrigatórios abaixo para cadastrar seu perfil no sistema.")
        
        with st.form("form_primeiro_acesso"):
            cpf_cad = st.text_input("Número do CPF (Ex: 12345678900):").strip()
            nome_cad = st.text_input("Nome Completo:").strip()
            email_cad = st.text_input("E-mail Institucional ou Pessoal:").strip()
            perfil_cad = st.selectbox(
                "Perfil de Acesso ao Sistema:",
                ["Discente", "Docente/Avaliador", "Técnico Administrativo"]
            )
            nova_senha = st.text_input("Crie uma Senha:", type="password").strip()
            confirma_senha = st.text_input("Confirme a Senha:", type="password").strip()
            
            btn_cadastrar = st.form_submit_button("Cadastrar e Acessar")
            
            if btn_cadastrar:
                if not cpf_cad or not nome_cad or not email_cad or not nova_senha:
                    st.error("⚠️ Preencha todos os campos obrigatórios antes de prosseguir.")
                elif nova_senha != confirma_senha:
                    st.error("⚠️ As senhas digitadas não coincidem! Redigite com atenção.")
                else:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT senha FROM usuarios WHERE cpf = ?", (cpf_cad,))
                        existente = c.fetchone()
                        
                        if existente and existente[0] is not None and existente[0] != "":
                            st.warning("⚠️ Este CPF já possui cadastro ativo! Alterne para a opção 'Já tenho cadastro (Login)'.")
                            conn.close()
                        else:
                            c.execute("""
                                INSERT OR REPLACE INTO usuarios (cpf, nome, email, senha, perfil)
                                VALUES (?, ?, ?, ?, ?)
                            """, (cpf_cad, nome_cad, email_cad, nova_senha, perfil_cad))
                            conn.commit()
                            conn.close()
                            
                            st.session_state["logado"] = True
                            st.session_state["cpf"] = cpf_cad
                            st.session_state["nome"] = nome_cad
                            st.session_state["email"] = email_cad
                            st.session_state["perfil"] = perfil_cad
                            st.success("✅ Cadastro realizado com sucesso! Entrando no sistema...")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar cadastro no banco de dados: {e}")

# =============================================================================
# ÁREA RESTRITA - PAINÉIS DE ACORDO COM O PERFIL LOGADO
# =============================================================================
else:
    # Barra Lateral com dados do usuário ativo
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['nome']}")
    st.sidebar.markdown(f"🆔 **CPF:** {st.session_state['cpf']}")
    st.sidebar.markdown(f"🛡️ **Perfil:** {st.session_state['perfil']}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Encerrar Sessão / Sair"):
        st.session_state["logado"] = False
        st.session_state["cpf"] = None
        st.session_state["nome"] = None
        st.session_state["email"] = None
        st.session_state["perfil"] = None
        st.rerun()

    perfil = st.session_state.get("perfil", "").strip()

    # =========================================================================
    # 1. PAINEL DO DISCENTE (ALUNO)
    # =========================================================================
    if perfil == "Discente":
        st.header("📌 Painel do Discente")
        tab_submeter, tab_extrato, tab_quadro = st.tabs([
            "Submeter Solicitação", 
            "Extrato & Integralização de Horas", 
            "📊 Tabela Completa do Regulamento"
        ])
        
        # ---------------------------------------------------------------------
        # ABA 1: SUBMETER NOVA SOLICITAÇÃO
        # ---------------------------------------------------------------------
        with tab_submeter:
            st.subheader("Formulário de Solicitação de Atividade Complementar")
            
            df_param = carregar_parametros()
            horas_eixo_dict = carregar_horas_acumuladas_por_eixo(st.session_state["cpf"])
            
            # PASSO 1: Seleção do Eixo / Dimensão (Reativo fora do form)
            dimensoes_disponiveis = ["Ensino", "Pesquisa", "Extensão", "Gestão"]
            dimensao = st.selectbox("1. Selecione o Eixo / Dimensão da Atividade:", dimensoes_disponiveis)
            
            # Exibe status e saldo de horas no eixo selecionado
            horas_no_eixo = horas_eixo_dict.get(dimensao, 0.0)
            if horas_no_eixo >= 100.0:
                st.warning(f"⚠️ **Atenção (Teto de Eixo Atingido):** Você já possui **{horas_no_eixo:.1f}h** aprovadas no eixo **{dimensao}**. O regulamento aproveita no máximo **100 horas por eixo**.")
            elif horas_no_eixo > 0:
                st.info(f"📊 **Saldo Atual no Eixo {dimensao}:** {horas_no_eixo:.1f}h de 100.0h máximas computáveis.")
            else:
                st.caption(f"ℹ️ Você ainda não possui horas computadas no eixo **{dimensao}**.")
            
            # PASSO 2: Filtragem das atividades por eixo
            df_filtrado = df_param[df_param["dimensao"] == dimensao]
            tipos_filtrados = df_filtrado["tipo_atividade"].tolist()
            
            if not tipos_filtrados:
                st.error("Nenhuma atividade encontrada para este eixo. Recarregue a página.")
            else:
                # PASSO 3: Seleção da atividade (Reativo fora do form)
                tipo = st.selectbox("2. Selecione o Tipo de Atividade Realizada:", tipos_filtrados)
                
                # EXIBIÇÃO INSTANTÂNEA DAS REGRAS E TETOS DA ATIVIDADE SELECIONADA
                if tipo:
                    row_info = df_filtrado[df_filtrado["tipo_atividade"] == tipo].iloc[0]
                    st.info(f"""
                    📌 **Regras Oficiais da Atividade Selecionada:**
                    * **Limite por Item/Atividade:** {row_info['ch_por_atividade']}
                    * **Teto Máximo Geral Acumulado na Atividade:** {row_info['ch_maxima_total']} horas
                    * **Documento Comprobatório Exigido:** {row_info['doc_comprovatorio']}
                    * **Regra do Eixo {dimensao}:** Máximo de 100.0h computadas no curso (mínimo de 2 eixos exigidos).
                    """)

                # PASSO 4: Form para inserção dos dados e upload
                with st.form("form_solicitacao_aluno"):
                    titulo = st.text_input("3. Título / Descrição Detalhada da Atividade Realizada:")
                    ch_solic = st.number_input("4. Carga Horária Solicitada (CH em horas):", min_value=0.0, step=1.0)
                    
                    st.markdown("---")
                    st.markdown("**5. Anexo de Documentação Comprobatória (Obrigatório PDF ou Link):**")
                    arquivo_pdf = st.file_uploader("📎 Anexar Comprovante (Arquivo no formato PDF):", type=["pdf"])
                    link_doc = st.text_input("🔗 OU Inserir Link Externo para Validação do Comprovante:")
                    
                    btn_submeter = st.form_submit_button("🚀 Submeter Solicitação para Avaliação")
                    
                    if btn_submeter:
                        erros = []
                        if not dimensao:
                            erros.append("Dimensão da atividade")
                        if not tipo:
                            erros.append("Tipo de atividade")
                        if not titulo.strip():
                            erros.append("Título da atividade")
                        if ch_solic <= 0:
                            erros.append("Carga Horária Solicitada deve ser maior que zero")
                        if not arquivo_pdf and not link_doc.strip():
                            erros.append("Comprovante (deve anexar arquivo PDF ou fornecer Link)")
                        
                        if erros:
                            st.error(f"⚠️ **Não foi possível submeter:** Corrija os seguintes itens: **{', '.join(erros)}**.")
                        else:
                            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            pdf_nome = arquivo_pdf.name if arquivo_pdf is not None else None
                            pdf_bytes = arquivo_pdf.read() if arquivo_pdf is not None else None
                            link_final = link_doc.strip() if link_doc.strip() else None
                            
                            conn = get_connection()
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO solicitacoes 
                                (nome_aluno, cpf, email, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, comprovativo_nome, comprovativo_blob, data_solicitacao)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                st.session_state["nome"], 
                                st.session_state["cpf"], 
                                st.session_state["email"], 
                                dimensao, 
                                tipo, 
                                titulo, 
                                ch_solic, 
                                link_final, 
                                pdf_nome, 
                                pdf_bytes, 
                                data_atual
                            ))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ **Solicitação enviada com sucesso!** Protocolo registrado em {data_atual}.")

        # ---------------------------------------------------------------------
        # ABA 2: EXTRATO DE SALDO E AUDITORIA DE REQUISITOS DE INTEGRALIZAÇÃO
        # ---------------------------------------------------------------------
        with tab_extrato:
            st.subheader("Extrato de Atividades e Integralização Acadêmica")
            
            df_aluno = carregar_solicitacoes_aluno(st.session_state["cpf"])
            
            if not df_aluno.empty:
                st.markdown("### 📄 Histórico de Solicitações Submetidas")
                st.dataframe(df_aluno, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📊 Balanço e Validação de Requisitos por Eixo")
                st.caption("📌 Regulamento: O estudante deve acumular horas em pelo menos 2 eixos diferentes, computando no máximo 100 horas por eixo.")
                
                df_aprovadas = df_aluno[df_aluno["status"].isin(["Aprovado", "Aprovado Parcialmente", "Concluído"])]
                
                eixos_cadastrados = ["Ensino", "Pesquisa", "Extensão", "Gestão"]
                resumo_eixos = []
                total_aproveitavel = 0.0
                eixos_com_horas_count = 0
                
                for e in eixos_cadastrados:
                    sub = df_aprovadas[df_aprovadas["dimensao"] == e]
                    horas_brutas = sub["ch_aprovada"].sum() if not sub.empty else 0.0
                    horas_computadas = min(horas_brutas, 100.0) # Trava de 100h por eixo
                    
                    if horas_computadas > 0:
                        eixos_com_horas_count += 1
                    total_aproveitavel += horas_computadas
                    
                    if horas_brutas > 100.0:
                        situacao = "⚠️ Teto do Eixo Excedido (Limitado a 100h)"
                    elif horas_brutas > 0:
                        situacao = "✅ Horas Computadas"
                    else:
                        situacao = "⚪ Sem Horas Aprovadas"

                    resumo_eixos.append({
                        "Eixo / Dimensão": e,
                        "Total Bruto Aprovado": f"{horas_brutas:.1f} h",
                        "Total Aproveitável (Teto 100h)": f"{horas_computadas:.1f} h",
                        "Situação no Eixo": situacao
                    })
                
                st.table(pd.DataFrame(resumo_eixos))
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Total Aproveitável para Conclusão do Curso", f"{total_aproveitavel:.1f} horas")
                with col_m2:
                    st.metric("Eixos com Horas Válidas", f"{eixos_com_horas_count} de 4 eixos")
                
                # Validação de Requisito Multidimensional
                if eixos_com_horas_count < 2:
                    st.error("🚨 **Requisito Pendente:** O regulamento exige horas computadas em **pelo menos 2 eixos diferentes**. Atualmente você possui horas em apenas 1 eixo.")
                else:
                    st.success("✅ **Requisito Multidimensional Atendido:** Você possui horas computadas em 2 ou mais eixos!")
            else:
                st.info("Nenhuma solicitação cadastrada até o momento.")

        # ---------------------------------------------------------------------
        # ABA 3: QUADRO COMPLETO DE CONSULTA DO REGULAMENTO
        # ---------------------------------------------------------------------
        with tab_quadro:
            st.subheader("📋 Regulamento Oficial de Atividades Complementares (FCAP)")
            df_quadro = carregar_parametros()
            df_quadro.columns = [
                "Atividade / Modalidade", 
                "Eixo / Dimensão", 
                "Carga Horária por Item (Teto Unitário)", 
                "Carga Horária Máxima Total (Teto Geral)", 
                "Documento Comprobatório Exigido"
            ]
            st.dataframe(df_quadro, use_container_width=True, hide_index=True)

    # =========================================================================
    # 2. PAINEL DE AVALIAÇÃO DO DOCENTE / AVALIADOR
    # =========================================================================
    elif perfil == "Docente/Avaliador":
        st.header("📋 Painel de Avaliação do Docente / Avaliador")
        tab_eval, tab_ref = st.tabs(["Avaliar Solicitações Pendentes", "📊 Consulta do Regulamento"])
        
        with tab_eval:
            df_pendentes = carregar_solicitacoes_pendentes()
            
            if df_pendentes.empty:
                st.success("🎉 Nenhuma solicitação pendente para avaliação no momento.")
            else:
                st.subheader("Solicitações Aguardando Avaliação")
                st.dataframe(
                    df_pendentes[["id", "nome_aluno", "cpf", "dimensao", "tipo_atividade", "titulo", "ch_solicitada", "comprovativo_nome", "data_solicitacao"]], 
                    use_container_width=True
                )
                
                st.markdown("---")
                id_sel = st.number_input("Informe o ID do Processo para Avaliar:", min_value=1, step=1)
                solic = df_pendentes[df_pendentes["id"] == id_sel]
                
                if not solic.empty:
                    dados = solic.iloc[0]
                    st.markdown(f"### Avaliando Processo #{dados['id']} — Aluno: **{dados['nome_aluno']}**")
                    st.write(f"**CPF:** {dados['cpf']} | **E-mail:** {dados['email']}")
                    st.write(f"**Eixo:** {dados['dimensao']} | **Atividade:** {dados['tipo_atividade']}")
                    st.write(f"**Título:** {dados['titulo']} | **CH Solicitada pelo Aluno:** {dados['ch_solicitada']}h")
                    
                    conn = get_connection()
                    c = conn.cursor()
                    
                    # Consulta Saldo Atual do Aluno no Eixo
                    c.execute("""
                        SELECT SUM(ch_aprovada) FROM solicitacoes 
                        WHERE cpf = ? AND dimensao = ? AND status IN ('Aprovado', 'Aprovado Parcialmente', 'Concluído') AND id != ?
                    """, (dados['cpf'], dados['dimensao'], id_sel))
                    res_eixo = c.fetchone()
                    saldo_eixo_aluno = res_eixo[0] if res_eixo and res_eixo[0] else 0.0
                    
                    # Consulta Comprovante PDF Anexado
                    c.execute("SELECT comprovativo_nome, comprovativo_blob FROM solicitacoes WHERE id = ?", (id_sel,))
                    blob_row = c.fetchone()
                    
                    # Consulta Regras do Item
                    c.execute("SELECT ch_por_atividade, ch_maxima_total FROM parametros WHERE tipo_atividade = ?", (dados['tipo_atividade'],))
                    res_param = c.fetchone()
                    conn.close()
                    
                    st.markdown("**Documentação Comprobatória:**")
                    if dados['link_comprovativo']:
                        st.markdown(f"🔗 **Link Informado:** [{dados['link_comprovativo']}]({dados['link_comprovativo']})")
                    
                    if blob_row and blob_row[1]:
                        nome_pdf = blob_row[0] if blob_row[0] else f"comprovante_{id_sel}.pdf"
                        st.download_button(
                            label=f"📄 Baixar e Analisar PDF Anexado ({nome_pdf})",
                            data=blob_row[1],
                            file_name=nome_pdf,
                            mime="application/pdf"
                        )
                    elif not dados['link_comprovativo']:
                        st.warning("⚠️ Nenhum arquivo ou link de comprovante foi anexado a este processo.")
                    
                    teto_item = float(res_param[1]) if res_param else 20.0
                    teto_unitario_desc = res_param[0] if res_param else "N/A"
                    
                    st.info(f"""
                    ℹ️ **Regras para Validação do Item:**
                    * **Limite por Atividade/Unitário:** `{teto_unitario_desc}`
                    * **Teto Máximo do Item:** `{teto_item} horas`
                    * **Saldo do Aluno no Eixo {dados['dimensao']}:** `{saldo_eixo_aluno:.1f} / 100.0 horas`
                    """)
                    
                    if saldo_eixo_aluno >= 100.0:
                        st.warning(f"⚠️ **Aviso:** O aluno já atingiu **{saldo_eixo_aluno:.1f}h** no eixo **{dados['dimensao']}**. O regulamento aproveita no máximo **100 horas por eixo**.")

                    # Form de Decisão do Avaliador
                    with st.form("form_avaliacao_docente"):
                        decisao = st.radio(
                            "Parecer do Avaliador:", 
                            ["Aprovado", "Aprovado Parcialmente", "Negado"],
                            help="Selecione 'Aprovado Parcialmente' ou 'Negado' caso o valor seja reduzido por limites ou não atenda aos requisitos."
                        )
                        
                        if decisao == "Aprovado":
                            # No Aprovado total, sugere a CH total solicitada (limitada ao teto se ultrapassar)
                            ch_sugerida = min(float(dados['ch_solicitada']), teto_item)
                            ch_informada = st.number_input(
                                "Carga Horária Aprovada (CH):", 
                                min_value=0.0, 
                                max_value=float(dados['ch_solicitada']), 
                                value=float(ch_sugerida),
                                step=1.0
                            )
                            justificativa = st.text_area("Justificativa / Observações (Opcional):")
                        elif decisao == "Aprovado Parcialmente":
                            ch_informada = st.number_input(
                                "Carga Horária Aprovada Parcialmente (CH):", 
                                min_value=0.1, 
                                max_value=float(dados['ch_solicitada']), 
                                value=float(min(float(dados['ch_solicitada']), teto_item)),
                                step=1.0
                            )
                            justificativa = st.text_area("Justificativa Obrigatória (Informe o motivo pelo qual o total não foi aprovado, ex: aplicação de limites do regulamento):")
                        else:  # Negado
                            ch_informada = 0.0
                            st.info("Carga Horária Aprovada definida como **0.0 horas**.")
                            justificativa = st.text_area("Justificativa Obrigatória para Indeferimento/Negativa:")
                        
                        btn_salvar_eval = st.form_submit_button("💾 Gravar Avaliação no Sistema")
                        
                        if btn_salvar_eval:
                            if decisao in ["Aprovado Parcialmente", "Negado"] and not justificativa.strip():
                                st.error("🚫 **Gravação Bloqueada:** A justificativa é **obrigatória** para os pareceres 'Aprovado Parcialmente' e 'Negado'!")
                            else:
                                ch_final = ch_informada
                                ch_max_atingida = "Não"
                                status_final = decisao
                                
                                if decisao == "Aprovado":
                                    if ch_informada >= teto_item or dados['ch_solicitada'] >= teto_item:
                                        ch_final = min(ch_informada, teto_item)
                                        ch_max_atingida = "Sim"
                                        st.warning(f"⚠️ **Teto Aplicado:** A carga horária foi ajustada para o limite máximo de {teto_item}h da atividade.")
                                elif decisao == "Aprovado Parcialmente":
                                    if ch_informada >= teto_item:
                                        ch_max_atingida = "Sim"
                                elif decisao == "Negado":
                                    ch_final = 0.0
                                
                                conn = get_connection()
                                c = conn.cursor()
                                c.execute("""
                                    UPDATE solicitacoes 
                                    SET ch_aprovada = ?, ch_maxima_atingida = ?, status = ?, nome_avaliador = ?, justificativa = ?
                                    WHERE id = ?
                                """, (ch_final, ch_max_atingida, status_final, st.session_state["nome"], justificativa, id_sel))
                                conn.commit()
                                conn.close()
                                st.success(f"✅ Processo #{id_sel} avaliado como '{status_final}' com sucesso!")
                                st.rerun()

        with tab_ref:
            st.subheader("📋 Tabela de Consulta de Parâmetros e Tetos")
            df_quadro = carregar_parametros()
            st.dataframe(df_quadro, use_container_width=True, hide_index=True)

    # =========================================================================
    # 3. PAINEL DO TÉCNICO ADMINISTRATIVO
    # =========================================================================
    elif perfil == "Técnico Administrativo":
        st.header("⚙️ Painel do Técnico Administrativo")
        
        df_avaliados = carregar_solicitacoes_avaliadas()
        
        if df_avaliados.empty:
            st.info("Nenhum processo avaliado pendente de lançamento no sistema acadêmico (SIG@).")
        else:
            st.subheader("Processos Avaliados Prontos para Registro no SIG@")
            st.dataframe(df_avaliados, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Confirmar Integração / Lançamento no SIG@")
            
            with st.form("form_siga_tecnico"):
                id_processo = st.number_input("Informe o ID da Solicitação para Concluir:", min_value=1, step=1)
                confirmar_siga = st.checkbox("Confirmar lançamento efetuado no sistema oficial (SIG@)")
                
                btn_concluir = st.form_submit_button("Confirmar Conclusão do Processo")
                
                if btn_concluir:
                    if not confirmar_siga:
                        st.warning("Marque a caixa de confirmação de lançamento no SIG@ antes de finalizar.")
                    else:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE solicitacoes 
                            SET registado_siga = 'Sim', status = 'Concluído'
                            WHERE id = ? AND status IN ('Aprovado', 'Aprovado Parcialmente', 'Indeferido', 'Negado')
                        """, (id_processo,))
                        linhas_afetadas = c.rowcount
                        conn.commit()
                        conn.close()
                        
                        if linhas_afetadas > 0:
                            st.success(f"✅ **Processo #{id_processo} finalizado com sucesso!** Status atualizado para 'Concluído'.")
                            st.rerun()
                        else:
                            st.error(f"Solicitação #{id_processo} não encontrada ou ainda não avaliada por um docente.")
    else:
        st.warning(f"⚠️ Perfil de usuário '{perfil}' não reconhecido. Por favor, faça logout e entre novamente.")
