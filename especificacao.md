# especificacao.md - Especificação do Sistema de Controle de AC

## 1. Contexto e Problema
A coordenação e o corpo técnico analisam manualmente centenas de comprovativos de Atividades Complementares (AC) no final do curso, gerando atrasos na validação de horas e na libertação de formandos para a colação de grau.

## 2. Utilizadores Identificados
- **Discente (Aluno)**: Submete os pedidos e acompanha o saldo de horas.
- **Avaliador (Docente/Coordenador)**: Analisa o conteúdo e valida a carga horária aprovada.
- **Técnico Administrativo**: Regista o processo e confirma a inserção no SIGA.

## 3. Escopo do Sistema
### Dentro do Escopo
- Registo de solicitações vinculadas a Dimensão, Tipo de Atividade e hiperligação para o comprovativo.
- Cálculo automático dos tetos máximos de carga horária por atividade e dimensão.
- Ecrã de avaliação com validação obrigatória de justificativa para indeferimentos.
- Painel de controlo administrativo (envio de e-mail e confirmação de registo no SIGA).
- Consulta de extrato de saldo pendente e aprovado pelo aluno.

### Fora do Escopo
- Leitura automática de comprovativos em PDF via OCR/IA.
- Verificação automática da validade da ligação externa.
- Assinatura digital de certificados.

## 4. Requisitos Funcionais (EARS) e Critérios de Aceitação (Dado/Quando/Então)

### RF-01: Submissão de Solicitação de AC
Quando o discente submeter o formulário de solicitação com a documentação associada, o sistema deve gravar a solicitação com o estado "Pendente".
- **CA-01 (Sucesso)**: Dado que o discente preencheu a dimensão, o tipo, o título, a CH solicitada e uma ligação válida para o comprovativo, quando clica em "Submeter", então o sistema grava a solicitação com o estado "Pendente" e a data atual.
- **CA-02 (Validação de Entrada)**: Dado que o discente introduz um valor de CH solicitada menor ou igual a zero, quando tenta submeter a solicitação, então o sistema impede o envio e sinaliza o erro.

### RF-02: Avaliação de Carga Horária com Tetos
Quando o avaliador processar uma solicitação, o sistema deve calcular a CH aprovada aplicando os limites da atividade e da dimensão.
- **CA-03 (Aplicação do Teto de CH)**: Dado que o tipo de atividade possui um teto de 20 horas e o discente solicitou 30 horas, quando o avaliador aprova o pedido, então o sistema atribui 20 horas aprovadas e marca o indicador "CH máxima atingida" como "Sim".
- **CA-04 (Obrigatoriedade de Justificativa)**: Dado que o avaliador atribui 0 horas (indeferimento), quando tenta guardar a avaliação sem preencher o campo de justificativa, então o sistema bloqueia a gravação e exige o preenchimento do motivo.

### RF-03: Conclusão do Processo e Integração
Quando o técnico administrativo confirmar o lançamento no sistema académico oficial, o sistema deve registar a finalização do processo.
- **CA-05 (Confirmação no SIGA)**: Dado que a solicitação foi avaliada, quando o técnico marca a opção "Registado no SIGA?", então o sistema atualiza o estado da solicitação para "Concluído".
