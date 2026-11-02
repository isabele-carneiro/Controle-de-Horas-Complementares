Alunos: ID_Aluno, Nome, CPF, Email, Entrada, Turno.
Regras_Atividades: ID_Regra, Dimensao, Tipo_Atividade, CH_Maxima_Atividade, CH_Maxima_Tipo.
Solicitacoes_AC:
ID_Solicitacao (Chave Primária)
ID_Aluno (Chave Estrangeira)
Data_Solicitacao, Dimensao, Tipo_Atividade, Titulo, CH_Solicitada, Data_Inicio, Data_Fim, Link_Comprovativo
CH_Aprovada, Max_Atividade_Atingida (Booleano), Max_Dimensao_Atingida (Booleano)
Nome_Avaliador, Justificativa_Indeferimento
Email_Enviado (Booleano), Registado_SIGA (Booleano)
