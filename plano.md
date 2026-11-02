# plano.md - Plano Técnico e Arquitetura de Dados

## 1. Decisão Técnica e Ferramentas
- **Modelo de Implementação**: Aplicação web simples / Formulário integrado com Base de Dados Relacional (ou Folha de Cálculo com scripts de validação).
- **Interface**: Formulários diferenciados por perfil de acesso (Aluno, Avaliador, Técnico).

## 2. Modelo de Dados (Entidades e Campos)

### Tabela `Alunos`
- `ID_Aluno` (Chave Primária)
- `Nome` (Texto)
- `CPF` (Texto)
- `Email` (Texto)
- `Entrada` (Texto, ex: 2023.1)
- `Turno` (Texto)

### Tabela `Parametros_Atividades`
- `ID_Tipo` (Chave Primária)
- `Dimensao` (Texto)
- `Tipo_Atividade` (Texto)
- `CH_Maxima_Atividade` (Número)
- `CH_Maxima_Tipo` (Número)

### Tabela `Solicitacoes_AC`
- `ID_Solicitacao` (Chave Primária)
- `ID_Aluno` (Chave Estrangeira -> Alunos)
- `Data_Solicitacao` (Data)
- `Dimensao` (Texto)
- `Tipo_Atividade` (Texto)
- `Titulo_Atividade` (Texto)
- `CH_Solicitada` (Número)
- `Data_Inicio` (Data)
- `Data_Fim` (Data)
- `Link_Comprovativo` (Texto)
- `CH_Aprovada` (Número)
- `Max_Atividade_Atingida` (Booleano)
- `Max_Dimensao_Atingida` (Booleano)
- `Nome_Avaliador` (Texto)
- `Justificativa` (Texto)
- `Email_Enviado` (Booleano)
- `Registado_SIGA` (Booleano)

## 3. Análise de Riscos Técnicos e Mitigação
- **Risco 1**: Acumulação indevida de carga horária por submissões duplicadas da mesma atividade pelo aluno.
  - *Mitigação*: Exibir no ecrã do avaliador um alerta de solicitações com títulos idênticos para o mesmo aluno.
- **Risco 2**: Ultrapassagem do teto da dimensão total ao aprovar múltiplos itens.
  - *Mitigação*: Implementar uma fórmula de validação automática que consulta o somatório prévio antes de confirmar o saldo aprovado.
