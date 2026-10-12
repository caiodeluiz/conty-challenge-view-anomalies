# 09 — Views que não parecem humanas

API local Python 3.12, sem dependências ou redes sociais reais. Uma série é uma lista de contagens **por hora**, em horas consecutivas; não é um contador acumulado. Os rótulos são `legitimate`, `suspicious` e `inconclusive`. A resposta explica a decisão e expõe todos os sinais; um rótulo suspeito não prova compra de views.

## Rodar e reproduzir

```sh
python3.12 api.py --port 3009
```

```sh
python3.12 dataset.py --output data/synthetic.json --metrics evidence/metrics.json --check-readme README.md
python3.12 -m unittest discover -s tests -v
```

```sh
python3.12 api.py --port 3009
curl -s http://127.0.0.1:3009/classify -H 'Content-Type: application/json' -d '{"views":[30,30,30,30,30,30,30,30,30,30,9000,30,30,30,30,30,30,30,30,30,30,30,30,30]}'
```

`GET /health` devolve `{ "ok": true }`. `POST /classify` recebe `{ "views": [inteiros...] }`; retorna `classification`, `reason`, `reasons` e `signals`, incluindo mediana, pico, participação do pico, repetição, queda e número de horas. JSON inválido, booleanos, contagens negativas ou fracionárias e listas vazias retornam 400. Limites de entrada: 8760 horas e contagem até 2^53−1, explicitados para interoperabilidade JSON; o corpo HTTP tem teto 131072 bytes.

## Regras explícitas

Antes de acusar, exige pelo menos 12 horas e atividade em pelo menos 3 delas. Fora disso prefere `inconclusive`, por insuficiência de evidência. Entre as séries restantes, considera suspeito qualquer um dos sinais:

- Pelo menos 6 horas consecutivas com a mesma contagem de no mínimo 500 views.
- Pico interior de pelo menos 500 views, 10 vezes a mediana e 6 vezes ambos os vizinhos, concentrando pelo menos 45% das views, com queda de pelo menos 90% na hora seguinte.
- 6 horas com pelo menos 500 views **em cada hora**, amplitude máxima de 2% da mediana local, seguidas de queda de pelo menos 90% em relação à mediana local.

O piso de volume é individual; a mediana serve para a tolerância de variação e a referência da queda. Uma revisão encontrou que o código anterior usava a mediana também para o piso, aceitando `[490,500,500,500,500,500]`. O código foi corrigido para cumprir o piso de cada hora, preservando a regra anunciada. Assim, `[10]*6 + [490,500,500,500,500,500] + [10]*12` recebe `legitimate` pelas regras, pois não confirma outro sinal suspeito. Isso não prova origem orgânica real. Os testes cobrem também 499 e uma janela inteira no piso ou acima dele.

Sem esses sinais, a série é compatível com tráfego orgânico pelas regras. Um grande pico na primeira ou última hora recebe `inconclusive`: falta um vizinho e não se inventa contexto ou queda futura. O dataset mostra um viral gradual legítimo e um pico comprado isolado em classes distintas. Mostra também `[0,...,0,900]`, em que o classificador prefere não acusar.

## Dataset e taxa medida

Seed fixa 20261011; 60 casos sintéticos, 40 legítimos e 20 suspeitos. Os rótulos vêm dos cenários do gerador, não da previsão. Inclui variação orgânica, viral gradual, baixo volume/evidência, pico isolado, repetição mecânica e plateau com queda. Um evento ao vivo legítimo com contagem constante é um falso positivo intencionalmente preservado para expor a limitação da regra.

Falso positivo no dataset: **2.50% (1/40)**.

O comando de geração calcula essa taxa do classificador atual e grava `evidence/metrics.json`. O teste lê o número do README e falha se divergir do medido; também verifica que o arquivo do dataset corresponde à regeneração. Neste conjunto foram medidos 20 verdadeiros positivos e 0 falsos negativos entre 20 suspeitos, com 1 abstenção. Taxas deste conjunto sintético não estimam desempenho em redes sociais reais.

## Decisões, custo e limites

Regras fixas, transparentes e sem treinamento. A passagem usa O(n) tempo e O(n) memória para o input; janelas têm tamanho fixo 6 e a resposta usa espaço constante. Mediana ordena internamente, portanto o custo total é **O(n log n)** no pior caso, e não apenas O(n). Não detecta bots que imitam variação natural, não autentica usuários, não verifica origem/fuso dos horários e não integra dados reais. Volume baixo e dados escassos favorecem abstenção. Um evento ao vivo pode parecer repetição mecânica; por isso o caso falso positivo está documentado.

Para avaliar, começar por `classifier.py`, depois `python3.12 dataset.py --check-readme README.md` e `tests/test_classifier.py`. Veja [declaração de IA](AI-USAGE.md).
