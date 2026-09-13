# Reduzindo Falsos Negativos na Detecção de Malware IoT: Um Estudo Comparativo de Estratégias de Balanceamento em Três Datasets Reais de NIDS

*Tradução para avaliação — versão alinhada com o `main.tex` atual (somente dados reais: CICIDS2017, UNSW-NB15 e IoT-23).*

---

## Resumo (Abstract)

O desbalanceamento de classes é uma das propriedades mais prejudiciais do tráfego de rede real para sistemas de detecção de intrusão (IDS) baseados em aprendizado de máquina: quando ataques são raros em relação ao tráfego benigno, os detectores tendem para a classe majoritária e silenciosamente deixam de detectar malware — um falso negativo (FN) que pode se traduzir diretamente em um dispositivo comprometido. Embora redes adversariais generativas (GANs) sejam cada vez mais usadas para superamostrar (oversampling) classes de ataque minoritárias, a maioria dos estudos reporta acurácia agregada ou F1-score, raramente quantifica o impacto da estratégia de balanceamento na contagem de falsos negativos (o erro de maior custo em segurança) e quase nunca isola o efeito do balanceamento da escolha do classificador. Este artigo apresenta uma comparação estritamente controlada de seis estratégias de balanceamento de dados — (i) sem balanceamento, (ii) SMOTETomek, (iii) uma GAN original (vanilla), (iv) WGAN-GP, (v) WGAN-GP condicional (cWGAN-GP) e (vi) a GAN tabular condicional (CTGAN) — em um protocolo idêntico reproduzido em três datasets públicos reais (CICIDS2017, UNSW-NB15 e o tráfego IoT-23 coletado pelo Laboratório Stratosphere) e quatro classificadores (MLP, XGBoost, Random Forest e LSTM). Todas as estratégias compartilham o mesmo workload (40.000 fluxos, 82% benigno / 18% ataque), divisão, etapa de seleção de características e conjunto de teste, de modo que qualquer diferença é atribuível apenas ao método de balanceamento. Os resultados mostram que o benefício é fortemente dependente do classificador: o modelo de sequência profundo (LSTM) é o mais degradado pelo desbalanceamento e o mais melhorado pelo balanceamento, com FNs reduzidos em 83,1% no CICIDS2017 (1.716→290), 81,5% no UNSW-NB15 (845→156) e 40,6% no IoT-23 (1.169→694); os ensembles de árvores, já quase saturados sob desbalanceamento, ganham apenas marginalmente; e o MLP tem ganhos inconsistentes, chegando a regredir em problemas fáceis. Nenhuma estratégia domina isoladamente: o SMOTETomek clássico e os métodos generativos baseados em Wasserstein alternam-se como melhores conforme o modelo e o dataset. Essas nuances são mascaradas pelas métricas agregadas, motivando um padrão de relato orientado à matriz de confusão para estudos de desbalanceamento em NIDS.

**Palavras-chave:** Internet das Coisas, detecção de intrusão, botnet, desbalanceamento de classes, oversampling, redes adversariais generativas, CTGAN, WGAN-GP, falsos negativos, CICIDS2017, UNSW-NB15, IoT-23.

---

## 1. Introdução

A Internet das Coisas (IoT) conecta bilhões de dispositivos com recursos limitados cuja postura padrão é frequentemente insegura, tornando botnets como Mirai, Torii e Hajime uma ameaça persistente e crescente [1,2]. Sistemas de detecção de intrusão baseados em rede (NIDS) são uma primeira linha de defesa, e o aprendizado de máquina (ML) tornou-se o paradigma dominante para detectar tráfego malicioso no nível de fluxo [3,4]. No entanto, os NIDS baseados em ML enfrentam um obstáculo fundamental: o tráfego de rede real é severamente desbalanceado entre classes. No dataset IoT-23 [5], por exemplo, os fluxos benignos superam largamente os maliciosos na maioria das capturas, e, mesmo dentro do tráfego malicioso, as famílias de ataque relevantes são classes minoritárias.

O desbalanceamento de classes enviesa os classificadores em direção à classe majoritária. A consequência mais perigosa não é uma acurácia um pouco menor, mas um maior número de *falsos negativos* — fluxos de malware que o detector classifica como benignos e portanto deixa passar na rede. Em um contexto de segurança, o custo de um ataque não detectado (dispositivo comprometido, movimento lateral, recrutamento para botnet) é ordens de grandeza maior que o custo de um falso alarme que um operador pode inspecionar [6]. Ainda assim, a esmagadora maioria dos artigos na literatura de NIDS otimiza e reporta métricas agregadas — acurácia, precisão, recall, F1-score — e ou não reporta as contagens da matriz de confusão, ou não isola o efeito do método de balanceamento do efeito da arquitetura do classificador.

Entre as técnicas propostas para mitigar o desbalanceamento, o oversampling se mostrou eficaz. Métodos clássicos de interpolação, como SMOTE [7] e suas variantes (SMOTE-ENN, SMOTETomek [8], ADASYN [9]), criam amostras sintéticas minoritárias interpolando entre vizinhos no espaço de características. Redes adversariais generativas (GANs) [10] e seus refinamentos — WGAN [11], WGAN-GP [12], GANs condicionais [13] e a GAN tabular condicional (CTGAN) [14] — aprendem a distribuição subjacente dos dados e são cada vez mais usadas para sintetizar amostras de ataque minoritárias [15-19].

Vários trabalhos recentes reportam resultados impressionantes com oversampling baseado em GAN em NIDS. A-NIDS [20] combina clusterização com CTGAN empilhado para lidar com drift de dados e esquecimento catastrófico. He et al. [6] propõem CWVAEGAN-1DCNN, um autoencoder variacional Wasserstein condicional com GAN que gera amostras minoritárias e alcança alto recall para classes de ataque raras. Soflaei et al. [21] usam dados balanceados com CTGAN com um duplo ensemble de classificadores fracos, atingindo 98% de acurácia binária no UNSW-NB15. CE-GAN [22] acopla uma GAN condicional a um encoder-decoder de agregação e uma perda composta, melhorando métricas de classes minoritárias no NSL-KDD e UNSW-NB15. SYN-GAN [19] treina modelos de NIDS inteiramente com tráfego sintetizado por GAN (UNSW-NB15, NSL-KDD e BoT-IoT). No entanto, esses estudos diferem em datasets, características, classificadores e protocolos de avaliação, o que torna seus resultados difíceis de comparar e impede qualquer conclusão sobre qual família de geradores é mais eficaz na redução de falsos negativos em um dado benchmark de IDS.

Neste artigo, realizamos uma comparação estritamente controlada de seis estratégias de balanceamento sobre um protocolo fixo de detecção binária que é reproduzido, sem alterações, em *três datasets públicos reais*: CICIDS2017 [24], UNSW-NB15 [23] e o dataset IoT-23 [5] coletado pelo Laboratório Stratosphere, e com *quatro classificadores*: MLP, XGBoost [50], Random Forest [51] e LSTM [52]. Cada dataset é reduzido a um workload idêntico de 40.000 fluxos (82% benigno / 18% ataque), dividido 70/30 com a mesma semente e pré-processado com o mesmo passo de `StandardScaler` + `SelectPercentile`; a única variável que muda entre os experimentos é a estratégia de balanceamento adicionada entre o pré-processamento e a classificação. Todos os resultados são reportados no mesmo conjunto de teste por dataset, e a análise enfatiza as contagens da matriz de confusão em vez de apenas métricas agregadas, com uma regra de seleção (Seção 3) que evita premiar uma estratégia que reduza FNs ao preço de um F1-score colapsado.

Nossos principais achados são os seguintes:

- O benefício do balanceamento concentra-se no classificador sequencial profundo. O LSTM é o modelo mais degradado pelo desbalanceamento — F1 de 0,33, 0,71 e 0,62 nos três baselines desbalanceados — e o mais melhorado pela reamostragem: os FNs são reduzidos em 83,1% no CICIDS2017 (1.716→290, cWGAN-GP), 81,5% no UNSW-NB15 (845→156, SMOTETomek) e 40,6% no IoT-23 (1.169→694, WGAN-GP).
- Os ensembles de árvores são largamente não afetados: o XGBoost deixa de detectar apenas quatro ataques no CICIDS2017 sem nenhum balanceamento, e o oversampling acrescenta no máximo 16–17% de redução de FN (UNSW-NB15) para eles. Isso é consistente com a conhecida robustez de boosting e bagging ao desbalanceamento moderado.
- O MLP não mostra benefício confiável. Seu baseline no CICIDS2017 (37 FNs) *nunca* é melhorado pelo balanceamento (a melhor configuração balanceada produz 60), o ganho no UNSW-NB15 é marginal e o resultado no IoT-23 é neutro — evidência de que, em problemas fáceis e quase separáveis, o oversampling sintético só pode adicionar ruído de rótulo.
- Nenhuma estratégia domina isoladamente. O SMOTETomek clássico e os métodos generativos baseados em Wasserstein (WGAN-GP, cWGAN-GP) alternam-se como melhor configuração entre datasets e modelos, enquanto o CTGAN permanece uma opção consistentemente forte. Manchetes que coroam uma única família de geradores exageram a evidência.
- Os cinco achados acima são *invisíveis* quando apenas acurácia ou F1 é reportado; um protocolo orientado à matriz de confusão e por classificador é, portanto, essencial para avaliar estratégias de balanceamento em contextos de segurança.

O restante deste artigo está organizado da seguinte forma. A Seção 2 revisa famílias de GANs e estratégias de balanceamento para NIDS. A Seção 3 detalha os três datasets, o protocolo experimental e as seis pipelines de balanceamento. A Seção 4 apresenta e discute os resultados entre datasets. A Seção 5 conclui o artigo e delineia trabalhos futuros.

---

## 2. Fundamentos e Trabalhos Relacionados

### 2.1 Redes Adversariais Generativas e suas Variantes

Uma GAN [10] treina duas redes em um jogo de soma zero: um gerador $G$ mapeia ruído latente $\mathbf{z} \sim p_z$ para amostras sintéticas, e um discriminador $D$ distingue amostras reais das geradas. O treinamento minimiza um proxy da divergência de Jensen-Shannon (JS), conhecido por sofrer de gradientes que desaparecem e de colapso de modos [11]. A GAN de Wasserstein [11] substitui o objetivo JS pela distância Wasserstein-1, produzindo um crítico cujos gradientes permanecem informativos mesmo quando as distribuições não se sobrepõem. A WGAN-GP [12] impõe a restrição de Lipschitz com uma penalidade de gradiente, melhorando muito a estabilidade do treinamento. GANs condicionais [13] condicionam ambas as redes em informação auxiliar (ex.: rótulos de classes), permitindo a geração controlada de amostras de uma classe específica — uma propriedade diretamente útil para a superamostragem da classe minoritária.

Para dados tabulares, Xu et al. [14] propuseram o CTGAN, que aborda dois problemas fundamentais das GANs em dados tabulares: (i) colunas contínuas raramente seguem uma distribuição gaussiana, o que eles tratam com normalização específica de modos baseada em um modelo de mistura gaussiana (GMM); e (ii) o gerador não consegue facilmente amostrar de todos os modos discretos de uma coluna categórica, o que eles tratam com vetores condicionais e treino por amostragem, juntamente com um discriminador pac ($\mathrm{pacs}=10$) para mitigar o colapso de modos. Essas escolhas de projeto tornam o CTGAN particularmente adequado a dados de fluxo de rede, cujas características contínuas (durações, estatísticas de pacotes e bytes) são tipicamente multimodais.

### 2.2 Estratégias de Oversampling para Detecção de Intrusão em Rede

O reamostragem é a contramedida mais usada contra o desbalanceamento em NIDS. O SMOTE [7] interpola entre vizinhos da classe minoritária; SMOTETomek e SMOTE-ENN [8] combinam SMOTE com regras de limpeza (links de Tomek ou vizinhos mais próximos editados) para remover amostras ruidosas e sobrepostas; o ADASYN [9] adapta o número de amostras geradas à densidade local da classe minoritária. Esses métodos são simples e rápidos, mas sua interpolação linear pode gerar amostras irreais quando a classe minoritária é multimodal ou se sobrepõe à classe majoritária, e estudos recentes em larga escala ainda reportam ganhos inconsistentes em ambientes IoT [25-27].

O oversampling baseado em GAN aprende a distribuição dos dados em vez de interpolar localmente. Engelmann e Lessmann [28] mostraram que GANs condicionais de Wasserstein são competitivas com o oversampling clássico para dados tabulares de crédito, e essa linha de trabalho foi estendida a NIDS por numerosos autores, incluindo o aumento GAN para detecção de intrusão baseada em imagem [29]. Zheng et al. [30] introduziram CWGAN-GP para classificação desbalanceada, e Yao e Zhao [31] aplicaram oversampling CWGAN-GP à detecção de intrusão, reportando melhor classificação que algoritmos tradicionais de oversampling em dois datasets benchmark. Ding et al. [32] propuseram TMG-GAN, um método de aprendizado desbalanceado baseado em GAN para NIDS publicado no IEEE TIFS. Swadi e Al-Mashhadi [33] usaram GANs de Wasserstein condicionais para balanceamento de classes em datasets de detecção de intrusão. WCGAN-GP também foi combinado com classificadores XGBoost em IDS baseados em fluxo [34], e a detecção de anomalias aumentada por GAN foi aplicada à detecção de malware IoT [42].

O CTGAN, em particular, tem atraído atenção crescente na literatura de NIDS. Habibi et al. [16] modelaram dados tabulares IoT desbalanceados com CTGAN e aprendizado de máquina para melhorar a detecção de ataques de botnet IoT. Alabsi et al. [35] construíram um IDS baseado em CTGAN para ataques DDoS e DoS. A-NIDS [20] usa CTGAN empilhado para detecção ciente de aprendizado contínuo. Soflaei et al. [21] combinaram dados balanceados com CTGAN com classificadores fracos e um meta-classificador XGBoost, reportando 98% de acurácia binária no UNSW-NB15. CE-GAN [22] aumenta amostras raras com um encoder-decoder condicional de agregação e uma perda composta. Outras abordagens generativas incluem CWVAEGAN-1DCNN [6], que usa uma decomposição variacional de mistura gaussiana antes da geração, MCGAN [36], DAE-GAN [37] e SYN-GAN [19], que mira a segurança IoT.

### 2.3 Dados Generativos para Segurança IoT e Datasets

A escolha do benchmark influencia fortemente o desempenho reportado. Datasets comuns de NIDS de IoT e de uso geral incluem N-BaIoT [38], Bot-IoT [39], Edge-IIoTset [40], UNSW-NB15 [23], NSL-KDD [41] e os levantamentos recentes em [3,4]. O dataset IoT-23 [5] foi capturado no Laboratório Stratosphere com 20 capturas de malware (Mirai, Torii, Hajime, Gagfyt e outros) e três capturas de dispositivos IoT benignos (Philips HUE, Amazon Echo, fechadura Somfy). É um dos datasets IoT rotulados mais realistas e recentemente coletados, e foi usado em desafios recentes de detecção baseada em ML [42]. No entanto, a maioria dos estudos com IoT-23 ou usa características de nível de fluxo da captura completa de vários gigabytes, ou se restringe a um único cenário, e poucos reportam a matriz de confusão detalhada que revelaria a contagem de falsos negativos. Baselines de detecção de anomalias como Kitsune [43], geração de tráfego de nível de fluxo com GANs [44] e modelos profundos híbridos que analisam desbalanceamento e robustez conjuntamente [45] complementam a literatura de oversampling generativo. Moti et al. [42] usaram GANs para detectar malware IoT não visto, e Rahman et al. [19] treinaram modelos de NIDS em dados totalmente sintéticos de GAN, mas nenhum realiza uma comparação frente a frente de famílias de geradores sob um pipeline fixo.

### 2.4 Lacunas e Posicionamento

Três lacunas motivam nosso trabalho. Primeiro, os estudos existentes comparam métodos generativos de oversampling entre si ou contra o SMOTE sob classificadores, datasets ou conjuntos de características *diferentes*, tornando impossível isolar a contribuição marginal do gerador. Segundo, quase nenhum estudo reporta falsos negativos como métrica de primeira classe, mesmo sendo o erro crítico de segurança. Terceiro, não há benchmark controlado de reamostragem clássica (SMOTETomek) contra baselines generativos (GAN vanilla, WGAN-GP, cWGAN-GP, CTGAN) reproduzido de forma idêntica em múltiplos datasets e classificadores reais. Nossa contribuição aborda essas lacunas com um protocolo estritamente controlado em três datasets reais, descrito a seguir.

---

## 3. Metodologia

### 3.1 Datasets e Pré-processamento

Usamos três datasets reais e públicos de tráfego de rede rotulado. **CICIDS2017** [24] é uma captura empresarial de cinco dias (segunda a sexta) com ataques modernos realizados em horários controlados e processada pelo CICFlowMeter em características de fluxo; seus oito arquivos diários são concatenados. O **UNSW-NB15** [23] foi gerado no Cyber Range da UNSW Canberra com a ferramenta IXIA PerfectStorm, combinando tráfego normal com ataques modernos (Fuzzing, Backdoors, DoS, Exploits, Reconnaissance, Shellcode, Worms), caracterizados por 45 características de fluxo; usamos o arquivo de treino oficial. O **IoT-23** [5] foi capturado pelo Laboratório Stratosphere e contém fluxos benignos de três dispositivos reais de casa inteligente (Philips HUE, Amazon Echo, fechadura Somfy) e fluxos maliciosos de múltiplos botnets (Mirai, Torii, Hajime, Gagfyt e outros); usamos um espelho pré-processado dos registros Zeek `conn.log` (6,05 milhões de fluxos, 21 colunas), mantido binário como benigno vs. malicioso.

Para tornar os três datasets diretamente comparáveis, cada um é reduzido a um workload idêntico por amostragem estratificada. De cada dataset completo extraímos uma amostra estratificada de exatamente **40.000 fluxos com 82% benigno (32.800) e 18% ataque (7.200)** usando uma semente fixa (42), que espelha o regime de desbalanceamento do tráfego IoT real no qual os ataques são minoria. A amostra é dividida 70/30 estratificada: **28.000 fluxos de treino** (22.960 benignos, 5.040 ataque) e **12.000 fluxos de teste** (9.840 benignos, 2.160 ataque), garantindo que o conjunto de teste seja idêntico em todas as seis estratégias de balanceamento para um dado dataset. As características numéricas de fluxo são padronizadas com `StandardScaler`, e a seleção de características é realizada com `SelectPercentile` (ANOVA $f$-classif, 60%), ajustada apenas na divisão de treino e reutilizada na divisão de teste para evitar qualquer vazamento de informação. Para o IoT-23 as características são os campos do Zeek `conn.log` (durações, bytes, pacotes, portas, `missed_bytes`); para UNSW-NB15 e CICIDS2017 são as características de fluxo de seus respectivos formatos. A pipeline está resumida na Figura 1.

**Figura 1** — Pipeline experimental. Para cada um dos três datasets reais (CICIDS2017, UNSW-NB15, IoT-23), 40.000 fluxos (82% benigno / 18% ataque) são pré-processados (`StandardScaler`, `SelectPercentile` 60%) e divididos 70/30 estratificados (semente 42). O treino (28.000 fluxos) é balanceado por uma de seis estratégias, cada classificador é treinado e a avaliação é feita no conjunto de teste fixo (12.000 fluxos, 9.840 benignos / 2.160 ataque).

### 3.2 Estratégias de Balanceamento

Seis estratégias são aplicadas à divisão de treino antes da classificação. Cada estratégia generativa produz exatamente 17.920 fluxos de ataque sintéticos, rebalanceando a classe minoritária à paridade (5.040 → 22.960), de modo que o conjunto de treino aumentado contenha 45.920 fluxos.

**Sem balanceamento (baseline).** O conjunto de treino desbalanceado original (82% benigno) é usado diretamente. Este baseline quantifica o viés introduzido pelo desbalanceamento e o número máximo de falsos negativos que cada classificador pode produzir, e é a referência contra a qual todas as reduções são medidas.

**SMOTETomek.** O SMOTETomek [8] primeiro aplica SMOTE ($k{=}5$) para sintetizar novas amostras maliciosas e depois remove pares de links de Tomek para limpar as fronteiras de classe. Representa o estado da arte entre os híbridos clássicos de reamostragem e serve como a estratégia não-generativa de referência.

**GAN vanilla.** Uma GAN padrão [10] é treinada apenas nas amostras minoritárias (ataque). O gerador mapeia ruído gaussiano de 32 dimensões por três camadas densas (64, 128, 256) com normalização em lote, ReLU e saída `tanh`; o discriminador usa duas camadas densas (256, 128) com dropout (0,3) e saída sigmoide. O treinamento usa entropia cruzada binária com Adam ($2\times10^{-4}$, $\beta_1{=}0,5$), batch de 64 e 300 épocas. Após o treinamento, 17.920 amostras são sorteadas do gerador.

**WGAN-GP.** A WGAN-GP [12] substitui o discriminador por um crítico que produz um valor real (sem sigmoide), treinado para minimizar a distância de Wasserstein com coeficiente de penalidade de gradiente $\lambda{=}10$ e cinco atualizações de crítico por atualização do gerador ($n_{\mathrm{critic}}{=}5$). Arquiteturas e configurações do otimizador são idênticas às da GAN vanilla. Essa variante isola a contribuição da perda de Wasserstein sozinha (sem condicionamento de classe).

**WGAN-GP condicional (cWGAN-GP).** O cWGAN-GP estende a WGAN-GP com condicionamento de classe [13,31]: tanto o gerador quanto o crítico recebem o rótulo da classe por meio de uma camada de embedding (2 classes → 16 dimensões) concatenado à entrada. O modelo é treinado no conjunto de treino completo, de modo que o gerador aprenda os dois modos, e a geração é realizada condicionada à classe maliciosa, produzindo 17.920 amostras que respeitam a distribuição condicional.

**CTGAN.** O CTGAN [14] é treinado no conjunto de treino completo usando sua normalização padrão específica de modos: cada característica contínua é decomposta com um modelo de mistura gaussiana variacional, e as características categóricas são codificadas com vetores one-hot mais amostragem condicional por treino-por-amostragem. A rede usa a arquitetura padrão do CTGAN (2 camadas ocultas de 256 unidades) com um discriminador pac ($\mathrm{pacs} = 10$), batch de 200 e 300 épocas. Um total de 17.920 amostras é então gerado condicionado à classe maliciosa.

### 3.3 Classificadores

Quatro classificadores são treinados em cada conjunto de treino (possivelmente aumentado) e avaliados no mesmo conjunto de teste.

- **MLP**: duas camadas densas ocultas (128 e 64 neurônios, ReLU) com dropout (0,3), saída sigmoide, Adam ($10^{-3}$), entropia cruzada binária, batch 64, até 60 épocas com parada antecipada (paciência 6) na perda de validação.
- **XGBoost** [50]: 300 árvores, taxa de aprendizado 0,05, profundidade máxima 6, subsample e colsample 0,8, treinamento por histograma.
- **Random Forest** [51]: 300 árvores.
- **LSTM** [52]: duas camadas LSTM empilhadas (64 e 32 unidades) com dropout (0,3), saída sigmoide, Adam ($10^{-3}$), entropia cruzada binária, batch 64, até 60 épocas com parada antecipada (paciência 6). Cada fluxo é apresentado como uma sequência de $n$ passos temporais, onde $n$ é o número de características selecionadas, uma característica por passo.

A Tabela I resume os hiperparâmetros; uma semente aleatória fixa (42) é usada ao longo de todo o trabalho.

**Tabela I — Hiperparâmetros das Pipelines de Balanceamento e dos Classificadores**

| Componente | Configuração |
|---|---|
| Workload | 40.000 fluxos (82%/18%), estratificado, semente 42 |
| Divisão | 70/30 estratificada, semente 42 (treino 28.000 / teste 12.000) |
| Pré-processamento | `StandardScaler` + `SelectPercentile` (60%) |
| Alvo sintético | 17.920 amostras (minoria 5.040 → 22.960) |
| SMOTETomek | SMOTE $k{=}5$ + links de Tomek |
| GAN | ruído 32; G: 64–128–256 + BN + tanh; D: 256–128 + Dropout(0,3) + sigmoide; 300 épocas, batch 64, Adam $2\times10^{-4}$, $\beta_1{=}0,5$ |
| WGAN-GP | $\lambda{=}10$, $n_{\mathrm{critic}}{=}5$, crítico linear |
| cWGAN-GP | + embedding de rótulo (2→16) em G e D |
| CTGAN | 300 épocas, batch 200, $\mathrm{pacs}{=}10$, normalização GMM |
| MLP | 128–64 ReLU + Dropout(0,3), sigmoide, Adam $10^{-3}$, batch 64, 60 épocas, paciência 6 |
| XGBoost | 300 árvores, lr 0,05, profundidade 6, subsample/colsample 0,8 |
| Random Forest | 300 árvores |
| LSTM | LSTM(64, retorno de sequência) + LSTM(32), Dropout(0,3), Adam $10^{-3}$, batch 64, 60 épocas, paciência 6; entrada remodelada para ($n_{\mathrm{características}}$, 1) |

### 3.4 Métricas de Avaliação

Sejam TN, FP, FN e TP as contagens de verdadeiros negativos, falsos positivos, falsos negativos e verdadeiros positivos no conjunto de teste fixo de um dado dataset. Reportamos acurácia (ACC), precisão (P), recall (R) e F1-score:

- $\mathrm{ACC} = \frac{TP+TN}{TP+TN+FP+FN}$
- $\mathrm{P} = \frac{TP}{TP+FP}, \qquad \mathrm{R} = \frac{TP}{TP+FN}$
- $\mathrm{F1} = \frac{2\cdot \mathrm{P}\cdot \mathrm{R}}{\mathrm{P}+\mathrm{R}}$

Além desses agregados, analisamos explicitamente as contagens de FN e FP, pois em aplicações de segurança um falso negativo (malware não detectado) é o erro mais custoso. Como uma regra ingênua de "menor FN" pode selecionar um cenário que reduz FNs ao preço de um F1-score colapsado (ex.: um gerador com alto recall mas precisão muito baixa), adotamos uma regra explícita de seleção da "melhor configuração balanceada" reportada na Tabela II: *entre os cinco cenários balanceados, escolhe-se o de menor FN cujo F1-score fique dentro de 0,05 do melhor F1-score alcançado por qualquer cenário balanceado daquele modelo e dataset*. Essa regra é descrita a priori, evita cherry-picking e é aplicada de forma idêntica a todos os resultados. Para quantificar a incerteza de amostragem em torno das estimativas pontuais, também calculamos intervalos de confiança de 95% por propagação Monte Carlo das contagens binomiais do teste: 200.000 extrações de $TP\sim\mathrm{Binomial}(TP+FN,\hat{R})$ e $FP\sim\mathrm{Binomial}(TN+FP,1-\widehat{\mathrm{TNR}})$ geram distribuições de FN, precisão, recall e F1, resumidas pelos percentis 2,5 e 97,5. esses intervalos quantificam a incerteza binomial de amostra finita no conjunto de teste fixo e não são ajustados para as múltiplas comparações entre os 24 cenários modelo-dataset; devem, portanto, ser lidos por linha e não como testes de família. Os intervalos completos das 72 configurações e a análise de sensibilidade à tolerância são fornecidos como material suplementar (Tabelas Suplementares S1 e S2).

---

## 4. Resultados e Discussão

### 4.1 Desempenho de Detecção entre Datasets

A Tabela II reporta, para cada um dos três datasets reais e quatro classificadores: a contagem de falsos negativos do baseline desbalanceado, a contagem de falsos negativos da melhor configuração balanceada sob a regra da Seção 3.4, a estratégia selecionada, sua contagem de falsos positivos e a variação resultante de FN. Doze configurações no total compartilham o mesmo workload, divisão, pré-processamento e conjunto de teste; a única diferença entre linhas é o dataset e o classificador.

**Tabela II — Validação entre Datasets em Três Datasets Reais: Redução de Falsos Negativos na Melhor Estratégia de Balanceamento (contagens de FN no conjunto de teste fixo de 12.000 fluxos)**

| Dataset | Clf | FN (base) | FN (melhor) | Estratégia | FP (melhor) | ΔFN | F1 (melhor) |
|---|---|---|---|---|---|---|---|
| CICIDS2017 | MLP | 37 | 60 | GAN | 180 | +62,2% | 0.9459 |
| CICIDS2017 | XGBoost | 4 | 4 | SMOTETomek | 7 | 0% | 0.9975 |
| CICIDS2017 | R. Forest | 14 | 7 | SMOTETomek | 3 | –50,0% | 0.9977 |
| CICIDS2017 | LSTM | 1.716 | 290 | cWGAN-GP | 553 | –83,1% | 0.8161 |
| UNSW-NB15 | MLP | 421 | 404 | GAN | 139 | –4,0% | 0.8661 |
| UNSW-NB15 | XGBoost | 303 | 253 | SMOTETomek | 224 | –16,5% | 0.8888 |
| UNSW-NB15 | R. Forest | 298 | 248 | SMOTETomek | 211 | –16,8% | 0.8928 |
| UNSW-NB15 | LSTM | 845 | 156 | SMOTETomek | 1.343 | –81,5% | 0.7278 |
| IoT-23 | MLP | 636 | 638 | WGAN-GP | 25 | ≈0% | 0.8211 |
| IoT-23 | XGBoost | 273 | 272 | SMOTETomek | 25 | ≈0% | 0.9271 |
| IoT-23 | R. Forest | 269 | 267 | cWGAN-GP | 134 | –0,7% | 0.9042 |
| IoT-23 | LSTM | 1.169 | 694 | WGAN-GP | 171 | –40,6% | 0.7722 |

Três achados emergem da Tabela II. Primeiro, o benefício do balanceamento é altamente dependente do classificador e concentra-se no modelo de sequência profundo. O LSTM é o classificador mais degradado pelo desbalanceamento — seus baselines desbalanceados carregam F1-scores de apenas 0,33 (CICIDS2017), 0,71 (UNSW-NB15) e 0,62 (IoT-23) — e também o que mais se beneficia da reamostragem: os FNs caem 83,1%, 81,5% e 40,6% nos três datasets (1.716→290, 845→156 e 1.169→694, respectivamente), com o F1-score subindo para 0,82, 0,73 e 0,77. A Figura 2 mostra as matrizes de confusão do LSTM no baseline desbalanceado e na melhor configuração balanceada de cada dataset. A melhora não é um artefato da regra de seleção: os intervalos de confiança de 95% por Monte Carlo binomial dos F1-scores balanceados — 0,82 [0,80–0,83], 0,73 [0,72–0,74] e 0,77 [0,76–0,79] — não se sobrepõem aos dos baselines desbalanceados — 0,33 [0,30–0,35], 0,71 [0,69–0,72] e 0,62 [0,60–0,63]. A redução concentra-se na célula de falso negativo (ataque real, predito benigno): o recall de ataque do LSTM sobe de 0,21 para 0,87 no CICIDS2017, de 0,61 para 0,93 no UNSW-NB15 e de 0,46 para 0,68 no IoT-23, enquanto os falsos positivos permanecem limitados no CICIDS2017 e no IoT-23 (553 e 171, respectivamente), mas sobem substancialmente no UNSW-NB15 (1.343, cerca de 13,6% dos fluxos benignos de teste). Esse é o custo de precisão da linha SMOTETomek escolhida ali; sob a estrutura de custos assimétrica de segurança (custo de FN ≫ custo de FP) a redução de FN ainda domina, e o F1-guard impede o colapso completo de precisão que uma regra ingênua de menor FN causaria — mas a troca exata depende dos limiares de implantação, e é precisamente por isso que reportamos as duas contagens explicitamente. O efeito particularmente forte no LSTM é consistente com sua maior capacidade e com o fato de ser o classificador mais degradado pelo desbalanceamento: uma vez que a reamostragem impede as camadas recorrentes de colapsar na classe majoritária, o modelo recupera a maior parte do sinal minoritário. Como a entrada é uma pseudo-sequência (uma característica padronizada por timestep, na ordem das colunas, Seção 3.3), não atribuímos o ganho a uma estrutura temporal genuína dos fluxos; se entradas sequenciais cientes de ordem (ex.: sequências de eventos Zeek por conexão) ampliam o benefício é deixado para trabalhos futuros.

**Figura 2** — Matrizes de confusão do LSTM no conjunto de teste fixo de 12.000 fluxos, por dataset, no baseline desbalanceado e na melhor configuração balanceada (regra de seleção da Seção 3.4).

Segundo, os ensembles de árvores já estão quase saturados sob desbalanceamento. O XGBoost deixa de detectar apenas quatro ataques no CICIDS2017 sem nenhum balanceamento, e o oversampling reduz seus FNs em no máximo 16,5% (UNSW-NB15), enquanto o Random Forest ganha no máximo ≈17%. Isso é consistente com a conhecida robustez de boosting e bagging ao desbalanceamento moderado de classes e significa que, para IDS baseados em ensemble, o balanceamento é em grande parte desnecessário. A Figura 3 (heatmap de F1-score) e a Figura 4 (barras de FN) visualizam isso em todas as seis estratégias e quatro modelos.

**Figura 3** — F1-score por dataset, modelo e estratégia de balanceamento. A coluna do LSTM mostra a maior lacuna entre o baseline desbalanceado e os cenários balanceados.

**Figura 4** — Falsos negativos por modelo e estratégia de balanceamento no conjunto de teste fixo de cada dataset.

Terceiro, o MLP não mostra benefício confiável e, em problemas fáceis, o oversampling pode até regredir. No CICIDS2017 o MLP desbalanceado já alcança apenas 37 FNs — um problema quase separável — e a melhor configuração balanceada (GAN) *aumenta* essa contagem para 60, exatamente o efeito de ruído de rótulo esperado quando as amostras sintéticas não mais se situam na fronteira de decisão verdadeira. No UNSW-NB15 o ganho é marginal (–4%) e no IoT-23 a contagem é estatisticamente inalterada. O artigo atinge, assim, uma conclusão mais matizada do que as manchetes "oversampling generativo é melhor" encontradas em parte da literatura: o valor do balanceamento é real, mas condicionado ao classificador, e é maior precisamente onde o desbalanceamento degrada mais o detector (redes profundas em tráfego difícil).

### 4.2 O Método de Balanceamento em Isolamento

Como para cada modelo e dataset todos os cenários compartilham o mesmo conjunto de teste, conjunto de características e divisão de treino, as diferenças na Tabela II são atribuíveis apenas à estratégia de balanceamento. Nenhuma estratégia domina isoladamente. O SMOTETomek — a referência clássica, não-generativa — é selecionado como melhor em seis das doze configurações (principalmente para ensembles de árvores e UNSW-NB15); as variantes Wasserstein (WGAN-GP e cWGAN-GP) em quatro; e o GAN vanilla em duas (as linhas do MLP). O CTGAN nunca é o único melhor sob a regra F1-guard, embora seja consistentemente um dos mais fortes para o LSTM (ex.: FNs de 230 e 207 no CICIDS2017 e UNSW-NB15 antes do guard de precisão) e alcance o maior F1 para o LSTM do UNSW-NB15. Esse padrão distribuído, que contradiz a noção de uma única família vencedora de geradores, é precisamente o tipo de evidência que o relato por métricas agregadas esconde: diferenças de F1 reportadas entre cenários costumam estar dentro de 0,05, enquanto as contagens de FN/FP que implicam podem diferir por uma ordem de grandeza na classe minoritária.

Para garantir que os vencedores da Tabela II não sejam um artefato da tolerância 0,05 da regra de seleção, repetimos a seleção para tolerâncias de 0,00, 0,02, 0,05 e 0,10. O padrão geral é estável. Para o LSTM a estratégia escolhida pode mudar — o UNSW-NB15 seleciona CTGAN sob regra estrita e SMOTETomek quando a tolerância atinge 0,05, e o IoT-23 desloca de cWGAN-GP para WGAN-GP —, mas a redução de FN permanece grande em toda tolerância: 83,1% no CICIDS2017 em todas as tolerâncias, 75,5–81,5% no UNSW-NB15 e 39,8–40,6% no IoT-23. Por outro lado, tolerâncias frouxas podem ser contraproducentes em problemas fáceis: com 0,10, o MLP do UNSW-NB15 trocaria a GAN vanilla (FN 404, FP 139, F1 0,87) pelo SMOTETomek (FN 168, FP 858, F1 0,80), trocando uma redução leve de FN por uma grande alta de alarmes falsos — exatamente o colapso que o F1-guard evita.

### 4.3 Comparação com Trabalhos Relacionados

A Tabela III posiciona nosso protocolo contra estudos recentes de oversampling generativo para NIDS. A comparação numérica direta é dificultada por diferenças em datasets, características e classificadores — precisamente o problema que nos propusemos a resolver —, mas dois pontos qualitativos se destacam. Primeiro, estudos que reportam métricas detalhadas de classe minoritária consistentemente identificam recall/falsos negativos como a métrica que o balanceamento generativo mais melhora [6,22,36]. Segundo, nossa comparação controlada mostra que pipelines baseadas em CTGAN [20,21,16] são fortes, mas não unicamente: o SMOTETomek clássico as iguala em várias configurações, algo que estudos de dataset e classificador únicos não conseguem revelar.

**Tabela III — Trabalhos Relacionados sobre Oversampling Generativo para NIDS (representativos)**

| Trabalho | Modelo | Datasets | Contribuição-chave |
|---|---|---|---|
| Habibi et al. [16] | CTGAN | IoT-23 | Modelagem tabular balanceada com CTGAN para botnets IoT |
| A-NIDS [20] | CTGAN empilhado | CICIDS-2017/18 | IDS adaptativo a drift, latência de 5 µs |
| Alabsi et al. [35] | CTGAN | CICIDS-2017 | IDS CTGAN para DDoS/DoS |
| Yao et al. [31] | CWGAN-GP | NSL-KDD, UNSW-NB15 | Oversampling CWGAN-GP estável |
| SYN-GAN [19] | SYN-GAN | UNSW-NB15, NSL-KDD, BoT-IoT | Treino com dados 100% sintéticos de GAN |
| CWVAEGAN [6] | CWVAEGAN+1D-CNN | NSL-KDD, UNSW-NB15 | Decomposição VGM, alto recall minoritário |
| Park et al. [15] | Baseado em GAN | datasets NIDS | NIDS aumentado por GAN baseado em IA |
| Soflaei et al. [21] | CTGAN+ensembles | UNSW-NB15 | 98% de acurácia binária |
| CE-GAN [22] | CE-GAN | NSL-KDD, UNSW-NB15 | Perda composta, ensemble teórico de jogos |
| Swadi et al. [33] | WCGAN | UNSW-NB15, KDD CUP99 | Balanceamento de classes Wasserstein |
| TMG-GAN [32] | TMG-GAN | CICIDS2017, UNSW-NB15 | Aprendizado desbalanceado por GAN |
| **Nosso** | **6 estratégias × 4 clf** | **IoT-23, UNSW-NB15, CICIDS2017** | **Benchmark controlado de 6 vias × 4 clf focado em FN** |

### 4.4 Custo Computacional

O custo do balanceamento é dominado pelas estratégias generativas: treinar cada gerador por 300 épocas foi o passo único mais caro de cada cenário, enquanto o SMOTETomek (apenas reamostragem) e os classificadores acrescentaram poucos segundos. A Tabela IV reporta o tempo de relógio dos quatro loops de treino dos geradores, medido no mesmo perfil de GPU do Google Colab ao executar os notebooks que produziram os resultados da Tabela II. O GAN clássico (Seção 3.3), cujos loops gerador/discriminador rodam em Python interpretado, é de longe o mais lento e consumiu ≈16–17 min por dataset (≈4,5× o WGAN-GP). As variantes Wasserstein convergem em 3,7–4,7 min, e o CTGAN em 2,4–7,5 min, escalando com o número de fluxos da classe minoritária. Treinar os quatro geradores ainda leva menos de 33 min por dataset, confortavelmente dentro de uma sessão única do Colab.

**Tabela IV — Tempo de Treino dos Geradores por Dataset (segundos de relógio, GPU única, 300 épocas)**

| Dataset | GAN | WGAN-GP | cWGAN-GP | CTGAN |
|---|---|---|---|---|
| CICIDS2017 | 1008 | 223 | 281 | 450 |
| UNSW-NB15 | 956 | 224 | 275 | 263 |
| IoT-23 | 954 | 225 | 263 | 143 |

### 4.5 Ameaças à Validade

Diversas limitações devem ser reconhecidas. Primeiro, os três datasets são reais e públicos, mas o subconjunto IoT-23 usado aqui consiste em 6,05 milhões de fluxos Zeek `conn.log` preparados por um pré-processamento de terceiros, que cobre uma porção grande, mas não completa, das capturas oficiais do IoT-23; suas características (campos Zeek) diferem em natureza das características CICFlowMeter dos outros dois datasets, mesmo com pipeline idêntico. Segundo, os resultados são reportados para uma única divisão e semente e sem busca de hiperparâmetros; o protocolo fixo garante reprodutibilidade interna, mas não quantificamos a variância entre divisões. Terceiro, a "melhor configuração balanceada" é selecionada post-hoc por uma regra explícita e a priori (Seção 3.4) que protege contra colapso de precisão, mas a multiplicidade de testes entre seis estratégias pode inflar a chance de selecionar um FN espurimente baixo; por isso enfatizamos *padrões* de efeito entre datasets (ex.: o LSTM melhorando consistentemente) em vez de linhas individuais. Quarto, as amostras sintéticas foram validadas apenas implicitamente, via classificação a jusante e projeções PCA, e não com testes formais de fidelidade (ex.: treino-em-sintético/teste-em-real, estatísticas KS). Quinto, nosso estudo está restrito à classificação binária (benigno vs. malware); a detecção multiclasse por família e a análise por captura dos registros do IoT-23 permanecem em aberto. Finalmente, apenas quatro famílias de classificadores foram consideradas; detectores modernos convolucionais e baseados em atenção não foram avaliados.

---

## 5. Conclusão e Trabalhos Futuros

Apresentamos uma comparação estritamente controlada de seis estratégias de balanceamento — nenhuma, SMOTETomek, GAN vanilla, WGAN-GP, cWGAN-GP e CTGAN — para detecção binária de intrusão, reproduzida de forma idêntica em três datasets reais (CICIDS2017, UNSW-NB15 e IoT-23) e quatro classificadores (MLP, XGBoost, Random Forest e LSTM), com workload, divisão, etapa de seleção de características e conjunto de teste compartilhados. Os resultados mostram que o benefício do balanceamento é fortemente dependente do classificador. O modelo de sequência profundo, o mais degradado pelo desbalanceamento (F1 desbalanceado de 0,33–0,71 entre datasets), é também o mais melhorado pela reamostragem, com falsos negativos reduzidos em 83,1% no CICIDS2017 (1.716→290), 81,5% no UNSW-NB15 (845→156) e 40,6% no IoT-23 (1.169→694). Os ensembles de árvores, quase saturados sob desbalanceamento, ganham no máximo marginalmente (0–17%), e o MLP não mostra benefício confiável, regredindo em problemas fáceis. Nenhuma estratégia domina isoladamente: o SMOTETomek clássico e os métodos generativos baseados em Wasserstein alternam-se como melhores entre configurações, e o CTGAN é consistentemente forte, mas não unicamente.

Essas nuances são invisíveis em relatos apenas de acurácia ou F1, o que motiva nossa principal recomendação metodológica: estudos de desbalanceamento em NIDS devem reportar contagens da matriz de confusão e isolar o efeito do balanceamento da escolha do classificador em múltiplos datasets reais. Nosso protocolo fornece um modelo fiel e reproduzível para isso.

Trabalhos futuros incluem (i) estender o benchmark à detecção multiclasse por família, à captura completa do IoT-23 e ao Edge-IIoTset [40]; (ii) avaliar métricas de fidelidade treino-em-sintético/teste-em-real e geração com preservação de privacidade diferencial; (iii) combinar balanceamento com focal loss [53] e detectores profundos não sequenciais (CNNs, transformers) para testar se o achado específico do LSTM generaliza; e (iv) quantificar a variância entre divisões por validação cruzada de sementes repetidas.

---

## Referências citadas (numeração de exemplo)

A tradução mantém as referências do `.bib` original; a numeração exata ([1]–[53]) depende do estilo IEEEtran de citação no Overleaf. O texto em inglês (`main.tex`) é a fonte de verdade para citações.