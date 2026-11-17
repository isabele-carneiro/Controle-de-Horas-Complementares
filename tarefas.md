# tarefas.md - Decomposição de Tarefas e Rastreabilidade

## 1. Fila de Tarefas (Backlog)

| ID Tarefa | Descrição da Tarefa | Requisito / Critério Relacionado | Estado |
| :--- | :--- | :--- | :--- |
| **T-00** | Permitir o login apenas com credenciais válidas. | Pré-requisito para RF-01 | Aprovado |
| **T-01** | Criar a tabela de parâmetros com os limites de CH por atividade e dimensão. | Pré-requisito para RF-02 | Aprovado |
| **T-02** | Desenvolver o formulário de submissão do discente com validações de campos obrigatórios. | RF-01, CA-01, CA-02 | Aprovado |
| **T-03** | Implementar a lógica de cálculo automático dos tetos de carga horária e alertas de limite atingido. | RF-02, CA-03 | Aprovado |
| **T-04** | Desenvolver o ecrã de avaliação para o docente com bloqueio de indeferimento sem justificativa. | RF-02, CA-04 | Aprovado |
| **T-05** | Criar o painel administrativo para atualização de estado (E-mail enviado e Registo SIGA). | RF-03, CA-05 | Aprovado |
| **T-06** | Montar o relatório sintético de saldo de horas acumuladas por aluno em cada dimensão. | P3 (Visualização restrita) | Aprovado |

---

## 2. Registo do Uso de IA

| Tarefa | Assistente de IA Utilizado | Conteúdo Gerado pela IA | Revisão / Correção Humana Realizada |
| :--- | :--- | :--- | :--- |
| **T-00** | Gemini | Login com credenciais válidas | A equipe adicionou um arquivo de usuários permitidos |
| **T-01** | Gemini | Estrutura inicial da tabela de limites de CH | A equipe ajustou os valores dos tetos por dimensão |
| **T-02** | Gemini | Código/interface do formulário de envio do discente | Adicionada a validação de bloqueio quando a CH solicitada é <= 0 |
| **T-03** | Gemini | Fórmula de cálculo automático de acumulação de horas | Corrigida a regra para travar o saldo no limite máximo da dimensão |
| **T-04** | Gemini | Interface do ecrã de avaliação e botão de indeferimento | Adicionada obrigatoriedade de preenchimento do campo de justificativa |
| **T-05** | Gemini | Estrutura das caixas de seleção de registro SIGA | Mantida conforme sugerido pela IA |
| **T-06** | Gemini | Layout do relatório visual de saldo de horas | Restrito o acesso para exibir apenas os dados do próprio aluno ligado |
