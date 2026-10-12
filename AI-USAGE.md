# Uso de IA e revisão

ChatGPT/Codex escreveu a API, as regras explicáveis, o gerador de dados sintéticos, os testes e esta documentação. O coordenador solicitou Sol 6.1 Extra High e recebeu essa configuração da thread de origem; workers Luna 6 Max fizeram revisão adversarial. Não se afirma revisão humana concluída.

Foram revisados o enunciado, limites de entrada, condições de cada sinal, independência dos rótulos sintéticos, prudência com dados escassos e regeneração da taxa de falsos positivos. Uma revisão independente encontrou que o piso do plateau usava a mediana, contrariando o piso de 500 em cada hora descrito no README. O coordenador reproduziu o caso, corrigiu o código para o piso individual e leu diretamente o código e os testes alterados. A suíte própria passou 16 testes locais; outro agente aprovou sete casos adversariais de piso, variação, queda e interação com pico isolado.

O gerador foi executado novamente com Python 3.12; os 60 casos e as métricas em evidence/metrics.json permaneceram idênticos, com FPR 2,50% (1/40). A revisão independente final aprovou o snapshot corrigido com 16 testes próprios e sete casos adversariais. O coordenador também conferiu diretamente o código, os testes e os documentos. Não houve revisão humana declarada, uso de dados reais ou operação com serviços externos.
