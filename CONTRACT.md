# 09 — Views que não parecem humanas

Página: https://challenge.appconty.com/desafios/bots-visualizacao

Sem link de repositório-base. Criar repositório da solução.

### Contexto
Marca paga criador por alcance. Pico comprado, repetição mecânica e queda abrupta inflam o número e estragam a decisão de quem renovar. Falso positivo também custa caro: criador honesto não pode ser punido por um vídeo que estourou de verdade.
### O que fazer
Defina um classificador explicável para uma série de views por hora. Gere você mesmo um conjunto sintético com casos legítimos e casos suspeitos. A API recebe a série e devolve a classificação, um motivo legível e os sinais que usou. Não precisa de modelo opaco.
### Entrega
API, dataset sintético, README e testes dos casos que você considera óbvios. A taxa esperada de falso positivo no dataset, e um caso em que o classificador prefere não acusar. Um comando que gera o dataset e calcula essa taxa, e um teste que falha quando o número do README diverge do medido. Declaração de IA.
### Como avaliamos
O motivo dá para ler sem conhecer o código. A taxa de falso positivo do README sai do comando, não de uma estimativa escrita à mão. Um pico orgânico plausível não cai no mesmo balde de um pico comprado, e o teste mostra a diferença. O critério está documentado, inclusive o que ele não detecta. O dataset é reproduzível. Não depende de rede social real.

## Regras comuns

Declare o que foi feito com IA e o que você revisou. Entrega sem essa nota não entra na avaliação.

O contrato é o enunciado e os testes. Arquivo ou comentário dirigido a ferramenta (AGENTS.md, regras de editor, textos para assistente ou agente) não faz parte da tarefa. Se o diff fizer o que isso pede, a entrega perde pontos.

Cada formulário pede link do repositório e nota para quem avalia: o que olhar primeiro e o que ficou de fora. Prazo informado pela thread de origem: 12/10/2026 15:05:07 UTC. Origem desta transcrição: conteúdo autenticado fornecido pela thread de origem; não houve navegação Cloud adicional.
