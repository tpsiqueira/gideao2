# Introdução

Este projeto contempla a versão do GIDEÃO que contém o `monitor_app`. É com essa versão de GIDEÃO que as equipes de Elevação e Escoamento da Petrobras cadastram e rotulam instâncias que após extraídas são incorporadas no 3W dataset.

# Backlog

As melhorias priorizadas atualmente para este projeto são as que seguem.

* Corrigir bugs já conhecidos:
    * Fazer tabela com amostras ser atualizada após uma instância ser salva (seja nova ou editada);
    * Fazer trends serem atualizados apenas qnd necessário: botões editar, criar e atualizar;
    * Fazer abertura inicial do app mostrar instâncias já cadastradas do tipo 0.
* Atualizar o Dygraph para poder atualizar formato de legenda;
* Fazer abertura inicial do sistema mostrar alguma tela útil;
* Ordenar a tabela em função do rótulo de evento e/o estado do poço;
* Desenvolver script para checar compatibilidade entre planilha de controle e base de dados;
* Desenvolver recurso para detectar interseção entre instâncias (talvez visualizador por poço);
* Buscar instâncias legadas (fora do PI System) de arquivos CSV exportados no passado;
* Substituição de AF SDK para PI Web API.

# Contatos

Para dúvidas e/ou sugestões, contate:

* Tiago Pereira Siqueira (POCOS/EP/SASD)
* Ricardo Vargas (POCOS/EP/SASD)