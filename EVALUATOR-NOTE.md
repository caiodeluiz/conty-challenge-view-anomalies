# Nota para quem avalia

Comece pelas regras em classifier.py e execute python3.12 dataset.py --check-readme README.md. A comparação do viral gradual com o pico isolado está nos testes; o contraexemplo ao vivo legítimo permanece no dataset e aparece como falso positivo. Confira evidence/metrics.json e o teste que detecta divergência do README.

Confira também a regressão do piso individual de 500 em cada hora do plateau. As séries com uma hora de 490 ou 499 não confirmam esse sinal; mediana, tolerância de variação e queda não substituem o piso individual. A taxa foi recalculada após a correção e permaneceu em 2,50% (1/40) nos mesmos 60 casos sintéticos.

Ficaram de fora autenticação, integração com redes sociais, sinais de IP/dispositivo e validação em dados reais. Os rótulos do dataset foram definidos pelos cenários sintéticos, independentemente da previsão. A nota de uso de IA está em AI-USAGE.md.
