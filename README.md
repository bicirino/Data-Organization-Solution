## Solução para organização de dados de ministérios: 

### No quê a solução consiste? 

- A solução consiste na **criação de uma tabela associativa entre duas tabelas .csv**; 
- A primeira tabela é uma **tabela do ministério Kids**, em que temos o NOME, EMAIL e TELEFONE do responsável e, logo abaixo, a/as criança/crianças de sua responsabilidade; 
- A segunda tabela também é um arquivo .csv que **detalha os dados de todos membros da igreja**, em que uns dos muitos atributos é o NOME, EMAIL e também o TELEFONE; 
- Deve-se gerar uma **tabela associativa** de: ID do membro, NOME do membro, EMAIL do membro, TELEFONE do membro e NOME da criança de sua responsabilidade; 

### Documentação da solução: 

1. Deve-se, primeiramente, capitalziar e formatar a tabela do ministério Kids - esta que, contém muitos caracteres fora do formato padrão; 
2. Deve-se, antes de iniciar as operações, verificar a tabela .csv dos membros; 
3. Implementar uma solução que utiliza o match do EMAIL, NOME, TELEFONE das duas tabelas; 
4. Gerar a tabela .csv associativa das duas tabelas supracitadas. 
