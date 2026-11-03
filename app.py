import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema de Controle de Atividades Complementares", layout="wide")

# Conexão com o banco de dados SQLite
def get_connection():
    return sqlite3.connect("banco.db", check_same_thread=False)

# Inicialização e auto-migração da Tabela Oficial de Parâmetros
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
    
    # 2. Tabela de Parâmetros: Recria para garantir a distribuição exata por dimensão
    c.execute("DROP TABLE IF EXISTS parametros")
    c.execute('''
        CREATE TABLE parametros (
            tipo_atividade TEXT PRIMARY KEY,
            dimensao TEXT,
            teto_horas REAL
        )
    ''')
    
    # Reorganização exata dos 20 itens conforme a nova distribuição dos eixos
    tabela_oficial_parametros = [
        # --- EIXO: ENSINO (6 Opções) ---
        ("Disciplinas cursadas com aproveitamento satisfatório em outros cursos da IES ou em outras IES", "Ensino", 45.0),
        ("Cursos de língua estrangeira em instituições credenciadas com aproveitamento", "Ensino", 20.0),
        ("Cursos livres relacionados à área de graduação em instituições de ensino com aproveitamento", "Ensino", 30.0),
        ("Monitoria realizada na FCAP em disciplinas teóricas ou práticas", "Ensino", 45.0),
        ("Estágio não curricular", "Ensino", 40.0),
        ("Participação em projetos de ensino", "Ensino", 90.0),

        # --- EIXO: PESQUISA (3 Opções) ---
        ("Participação em projetos de iniciação científica", "Pesquisa", 90.0),
        ("Publicação de artigos completos em jornais, revistas científicas e anais de eventos", "Pesquisa", 80.0),
        ("Apresentação de trabalho em evento científico com publicação", "Pesquisa", 90.0),

        # --- EIXO: EXTENSÃO (9 Opções) ---
        ("Participação em palestras como ouvinte", "Extensão", 60.0),
        ("Participação como palestrante ou instrutor em minicurso e oficina", "Extensão", 40.0),
        ("Participação em congressos, seminários, simpósio, ciclo de conferências, debate, workshop, jornada, oficina e fórum", "Extensão", 40.0),
        ("Visita técnica orientada (que não faça parte da carga horária regular)", "Extensão", 15.0),
        ("Participação em projetos de extensão", "Extensão", 90.0),
        ("Participação em cursos de extensão", "Extensão", 30.0),
        ("Participação como Presidente ou Diretor da Empresa Júnior", "Extensão", 90.0),
        ("Participação como membro da Empresa Júnior", "Extensão", 60.0),
        ("Participação em atividades acadêmicas ou comunitário-voluntárias oferecidas pelo curso", "Extensão", 30.0),

        # --- EIXO: GESTÃO (2 Opções) ---
        ("Representação de Presidência ou Diretoria do Diretório Acadêmico", "Gestão", 90.0),
        ("Participação voluntária no Diretório Acadêmico", "Gestão", 60.0)
    ]
    c.executemany("INSERT INTO parametros VALUES (?, ?, ?)", tabela_oficial_parametros)

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
    
    # Garantia de integridade das colunas da tabela de solicitações
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
        tab_submeter, tab_extrato = st.tabs(["Submeter Solicitação", "Extrato de Horas"])
        
        with tab_submeter:
            st.subheader("Formulário de Solicitação de AC")
            
            # Carrega a tabela de parâmetros
            conn = get_connection()
            df_param = pd.read_sql("SELECT tipo_atividade, dimensao, teto_horas FROM parametros", conn)
            conn.close()
            
            # 1. Seleção da Dimensão (Eixo) - Colocada fora do formulário para reatividade instantânea
            dimensoes_disponiveis = ["Ensino", "Pesquisa", "Extensão", "Gestão"]
            dimensao = st.selectbox("1. Selecione a Dimensão (Eixo):", dimensoes_disponiveis)
            
            # 2. Filtragem Dinâmica das Atividades da Dimensão Escolhida
            df_filtrado = df_param[df_param["dimensao"] == dimensao]
            tipos_filtrados = df_filtrado["tipo_atividade"].tolist()
            
            with st.form("form_solicitacao"):
                st.text_input("Nome do Discente:", value=st.session_state["nome"], disabled=True)
                st.text_input("CPF:", value=st.session_state["cpf"], disabled=True)
                
                tipo = st.selectbox("2. Selecione o Tipo de Atividade Realizada:", tipos_filtrados)
                
                titulo = st.text_input("3. Título / Descrição da Atividade:")
                ch_solic = st.number_input("4. Carga Horária Solicitada (CH):", min_value=0.0, step=1.0)
                
                st.markdown("---")
                st.markdown("**5. Comprovante da Atividade (Anexe o arquivo PDF e/ou insira o Link):**")
                arquivo_pdf = st.file_uploader("📎 Anexar Comprovante (Arquivo PDF):", type=["pdf"])
                link_doc = st.text_input("🔗 OU Link para o Documento Comprovativo:")
                
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
                    if not arquivo_pdf and not link_doc.strip():
                        erros.append("Documento comprobatório (anexe o PDF ou insira o Link)")
                    
                    if erros:
                        st.error(f"⚠️ **Envio Impedido:** É necessário corrigir os seguintes campos: **{', '.join(erros)}**.")
                    else:
                        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        pdf_nome = arquivo_pdf.name if arquivo_pdf is not None else None
                        pdf_bytes = arquivo_pdf.read() if arquivo_pdf is not None else None
                        link_final = link_doc.strip() if link_doc.strip() else None
                        
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO solicitacoes 
                            (nome_aluno, cpf, email, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, comprovativo_nome, comprovativo_blob, data_solicitacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (st.session_state["nome"], st.session_state["cpf"], st.session_state["email"], dimensao, tipo, titulo, ch_solic, link_final, pdf_nome, pdf_bytes, data_atual))
                        conn.commit()
                        conn.close()
                        st.success("✅ **Solicitação gravada com sucesso!** Estado: **Pendente** | Data: " + data_atual)

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
    # PAINEL DE AVALIAÇÃO DO DOCENTE / AVALIADOR
    # -----------------------------------------------------------------------------
    elif perfil == "Docente/Avaliador":
        st.header("📋 Painel de Avaliação do Docente / Avaliador")
        
        conn = get_connection()
        df_pendentes = pd.read_sql_query("SELECT id, nome_aluno, cpf, dimensao, tipo_atividade, titulo, ch_solicitada, link_comprovativo, comprovativo_nome, data_solicitacao FROM solicitacoes WHERE status = 'Pendente'", conn)
        conn.close()
        
        if df_pendentes.empty:
            st.success("Nenhuma solicitação pendente para avaliação no momento.")
        else:
            st.subheader("Solicitações Pendentes de Avaliação")
            st.dataframe(df_pendentes[["id", "nome_aluno", "cpf", "dimensao", "tipo_atividade", "titulo", "ch_solicitada", "comprovativo_nome", "data_solicitacao"]], use_container_width=True)
            
            id_sel = st.number_input("Informe o ID da Solicitação para Avaliar:", min_value=1, step=1)
            solic = df_pendentes[df_pendentes["id"] == id_sel]
            
            if not solic.empty:
                dados = solic.iloc[0]
                st.markdown("---")
                st.markdown(f"### Avaliando Processo #{dados['id']} - Aluno: {dados['nome_aluno']}")
                st.write(f"**Dimensão:** {dados['dimensao']} | **Tipo:** {dados['tipo_atividade']}")
                st.write(f"**Título:** {dados['titulo']} | **CH Solicitada:** {dados['ch_solicitada']}h")
                
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT comprovativo_nome, comprovativo_blob FROM solicitacoes WHERE id = ?", (id_sel,))
                blob_row = c.fetchone()
                
                st.markdown("**Documentação Comprobatória:**")
                if dados['link_comprovativo']:
                    st.markdown(f"🔗 **Link Externo:** [{dados['link_comprovativo']}]({dados['link_comprovativo']})")
                
                if blob_row and blob_row[1]:
                    nome_arquivo = blob_row[0] if blob_row[0] else f"comprovante_{id_sel}.pdf"
                    st.download_button(
                        label=f"📄 Baixar PDF Anexado ({nome_arquivo})",
                        data=blob_row[1],
                        file_name=nome_arquivo,
                        mime="application/pdf"
                    )
                elif not dados['link_comprovativo']:
                    st.warning("Nenhum comprovante anexado.")
                
                # Busca teto da atividade
                c.execute("SELECT teto_horas FROM parametros WHERE tipo_atividade = ?", (dados['tipo_atividade'],))
                res_teto = c.fetchone()
                conn.close()
                
                teto_atividade = res_teto[0] if res_teto else 20.0
                st.info(f"ℹ️ **Teto Máximo Configurado para esta atividade:** {teto_atividade} horas.")
                
                with st.form("form_avaliacao"):
                    decisao = st.radio("Ação do Avaliador:", ["Aprovar", "Indeferir"])
                    ch_informada = st.number_input("Carga Horária Aprovada (CH):", min_value=0.0, max_value=float(dados['ch_solicitada']), step=1.0)
                    justificativa = st.text_area("Justificativa da Avaliação (Obrigatória para indeferimentos ou 0h):")
                    
                    btn_confirmar_eval = st.form_submit_button("Guardar Avaliação")
                    
                    if btn_confirmar_eval:
                        if (decisao == "Indeferir" or ch_informada == 0) and not justificativa.strip():
                            st.error("🚫 **Gravação Bloqueada:** Quando a CH aprovada for 0 horas (ou em caso de indeferimento), o preenchimento da justificativa é obrigatório!")
                        else:
                            ch_final = 0.0
                            ch_max_atingida = "Não"
                            nuevo_status = "Indeferido"
                            
                            if decisao == "Aprovar":
                                nuevo_status = "Aprovado"
                                if ch_informada >= teto_atividade or dados['ch_solicitada'] >= teto_atividade:
                                    ch_final = min(ch_informada, teto_atividade)
                                    ch_max_atingida = "Sim"
                                    st.warning(f"⚠️ **Teto Atingido:** O limite de {teto_atividade}h da atividade foi aplicado. Indicador 'CH máxima atingida' marcado como **Sim**.")
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
    # PAINEL DO TÉCNICO ADMINISTRATIVO
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
                            st.success(f"✅ **Processo #{id_processo} finalizado com sucesso!** Estado atualizado para **Concluído**.")
                            st.rerun()
                        else:
                            st.error(f"Solicitação #{id_processo} não encontrada ou ainda não avaliada pelo docente.")
