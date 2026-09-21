# Reduzindo Falsos Negativos na Detecção de Malware IoT: Um Estudo Comparativo de Estratégias de Balanceamento em Três Datasets Reais de NIDS

*Tradução para avaliação — versão alinhada com o `main.tex` atual (somente dados reais: Edge-IIoTset, TON_IoT e IoT-23).*

---

## Resumo (Abstract)

Este artigo estuda como o desbalanceamento do tráfego de rede real degrada os sistemas de detecção de intrusão (IDSs) baseados em aprendizado de máquina. Quando os ataques são raros frente aos fluxos benignos, os detectores enviesam-se para a classe majoritária e silenciosamente deixam de detectar malware---um falso negativo (FN), o erro de maior custo em segurança. As redes adversariais generativas (GANs) são cada vez mais usadas para superamostrar classes de ataque minoritárias, mas a maioria dos estudos reporta acurácia agregada ou F1-score e raramente quantifica o impacto do balanceamento sobre a contagem de falsos negativos ou o isola do classificador. Comparamos seis estratégias---nenhuma, SMOTETomek, uma GAN vanilla, WGAN-GP, cWGAN-GP e CTGAN---sob protocolo estritamente controlado e idêntico, reproduzido em três datasets públicos reais de IoT/IIoT (Edge-IIoTset, TON_IoT e IoT-23) e quatro classificadores (MLP, XGBoost, Random Forest e LSTM), compartilhando a mesma carga (40.000 fluxos, 82% / 18%), divisão, seleção de características e teste, de modo que diferenças reflitam apenas o método de balanceamento. O benefício é fortemente dependente do classificador: o LSTM é de longe o mais degradado pelo desbalanceamento (F1 desbalanceado de 0,18–0,63) e o mais melhorado pela reamostragem, cortando os falsos negativos em 89,9% no TON_IoT, 41,3% no IoT-23 e 14,1% no Edge-IIoTset; os ensembles de árvores ganham no máximo ≈11% no TON_IoT e no IoT-23, mas são integralmente limpos no Edge-IIoTset, onde o SMOTETomek elimina todo falso negativo residual; e os ganhos do MLP são pequenos porém consistentes (−9% a −13%). Nenhuma estratégia domina isoladamente---o SMOTETomek clássico é selecionado melhor em sete das doze configurações, seguido do WGAN-GP---e a GAN vanilla é a mais cara, tornando o WGAN-GP o gerador robusto mais barato. Em custo, o SMOTETomek remove mais falsos negativos por minuto de computação, e o WGAN-GP oferece o melhor custo-benefício generativo (≈3,5 min por dataset); a GAN vanilla só compensa no tráfego mais difícil.

**Palavras-chave:** Internet das Coisas, detecção de intrusão, botnet, desbalanceamento de classes, oversampling, redes adversariais generativas, CTGAN, WGAN-GP, falsos negativos, Edge-IIoTset, TON_IoT, IoT-23.

---

## 1. Introdução

A Internet das Coisas (IoT) conecta bilhões de dispositivos com recursos limitados cuja postura padrão é frequentemente insegura, tornando botnets como Mirai, Torii e Hajime uma ameaça persistente e crescente [1,2]. Sistemas de detecção de intrusão baseados em rede (NIDS) são uma primeira linha de defesa, e o aprendizado de máquina (ML) tornou-se o paradigma dominante para detectar tráfego malicioso no nível de fluxo [3,4]. No entanto, os NIDS baseados em ML enfrentam um obstáculo fundamental: o tráfego de rede real é severamente desbalanceado entre classes. No dataset IoT-23 [5], por exemplo, os fluxos benignos superam largamente os maliciosos na maioria das capturas, e, mesmo dentro do tráfego malicioso, as famílias de ataque relevantes são classes minoritárias.

O desbalanceamento de classes enviesa os classificadores em direção à classe majoritária. A consequência mais perigosa não é uma acurácia um pouco menor, mas um maior número de *falsos negativos* — fluxos de malware que o detector classifica como benignos e portanto deixa passar na rede. Em um contexto de segurança, o custo de um ataque não detectado (dispositivo comprometido, movimento lateral, recrutamento para botnet) é ordens de grandeza maior que o custo de um falso alarme que um operador pode inspecionar [6]. Ainda assim, a esmagadora maioria dos artigos na literatura de NIDS otimiza e reporta métricas agregadas — acurácia, precisão, recall, F1-score — e ou não reporta as contagens da matriz de confusão, ou não isola o efeito do método de balanceamento do efeito da arquitetura do classificador.

Entre as técnicas propostas para mitigar o desbalanceamento, o oversampling se mostrou eficaz. Métodos clássicos de interpolação, como SMOTE [7] e suas variantes (SMOTE-ENN, SMOTETomek [8], ADASYN [9]), criam amostras sintéticas minoritárias interpolando entre vizinhos no espaço de características. Redes adversariais generativas (GANs) [10] e seus refinamentos — WGAN [11], WGAN-GP [12], GANs condicionais [13] e a GAN tabular condicional (CTGAN) [14] — aprendem a distribuição subjacente dos dados e são cada vez mais usadas para sintetizar amostras de ataque minoritárias [15-19].

Vários trabalhos recentes reportam resultados impressionantes com oversampling baseado em GAN em NIDS. A-NIDS [20] combina clusterização com CTGAN empilhado para lidar com drift de dados e esquecimento catastrófico. He et al. [6] propõem CWVAEGAN-1DCNN, um autoencoder variacional Wasserstein condicional com GAN que gera amostras minoritárias e alcança alto recall para classes de ataque raras. Soflaei et al. [21] usam dados balanceados com CTGAN com um duplo ensemble de classificadores fracos, atingindo 98% de acurácia binária no UNSW-NB15. CE-GAN [22] acopla uma GAN condicional a um encoder-decoder de agregação e uma perda composta, melhorando métricas de classes minoritárias no NSL-KDD e UNSW-NB15. SYN-GAN [18] treina modelos de NIDS inteiramente com tráfego sintetizado por GAN (UNSW-NB15, NSL-KDD e BoT-IoT). No entanto, esses estudos diferem em datasets, características, classificadores e protocolos de avaliação, o que torna seus resultados difíceis de comparar e impede qualquer conclusão sobre qual família de geradores é mais eficaz na redução de falsos negativos em um dado benchmark de IDS.

Neste artigo, realizamos uma comparação estritamente controlada de seis estratégias de balanceamento sobre um protocolo fixo de detecção binária que é reproduzido, sem alterações, em *três datasets públicos reais de IoT/IIoT*: Edge-IIoTset [23], TON_IoT [24] e o dataset IoT-23 [5] coletado pelo Laboratório Stratosphere, e com *quatro classificadores*: MLP, XGBoost [25], Random Forest [26] e LSTM [27]. Cada dataset é reduzido a um workload idêntico de 40.000 fluxos (82% benigno / 18% ataque), dividido 70/30 com a mesma semente e pré-processado com o mesmo passo de `StandardScaler` + `SelectPercentile`; a única variável que muda entre os experimentos é a estratégia de balanceamento adicionada entre o pré-processamento e a classificação. Todos os resultados são reportados no mesmo conjunto de teste por dataset, e a análise enfatiza as contagens da matriz de confusão em vez de apenas métricas agregadas, com uma regra de seleção (Seção 3.4) que evita premiar uma estratégia que reduza FNs ao preço de um F1-score colapsado.

Nossos principais achados são os seguintes:

- O benefício do balanceamento concentra-se no classificador sequencial profundo. O LSTM é o modelo mais degradado pelo desbalanceamento — F1 desbalanceado de 0,18 no TON_IoT, 0,61 no IoT-23 e 0,63 no Edge-IIoTset — e o mais melhorado pela reamostragem: os FNs são reduzidos em 89,9% no TON_IoT (1.930→194, SMOTETomek), 41,3% no IoT-23 (1.190→698, WGAN-GP) e 14,1% no Edge-IIoTset (1.156→993, WGAN-GP).
- Os ensembles de árvores estão quase saturados no TON_IoT (o XGBoost deixa de detectar 70 ataques e o Random Forest, 62) e no IoT-23 (273 e 269), onde o balanceamento acrescenta no máximo ≈11% de redução de FN; no Edge-IIoTset, porém, o SMOTETomek remove *todos* os falsos negativos residuais de XGBoost e Random Forest (35→0 e 37→0) ao preço de um F1 0,6 pp menor — a saturação de ensembles de árvores depende do dataset, não é intrínseca.
- O MLP mostra ganhos pequenos, porém consistentes, em todas as bases (−8,8% no TON_IoT, −10,1% no IoT-23, −13,1% no Edge-IIoTset) e nunca regride sob o F1-guard — em desbalanceamentos moderados, a reamostragem é segura para redes rasas, mas seu benefício é uma ordem de grandeza menor que para o LSTM.
- Nenhuma estratégia domina isoladamente. O SMOTETomek clássico é selecionado melhor em sete das doze configurações e o WGAN-GP em quatro, enquanto o CTGAN fica consistentemente próximo (ex.: 211 FNs para o LSTM do TON_IoT), mas nunca é o vencedor único. Manchetes que coroam uma única família de geradores exageram a evidência.
- Os cinco achados acima são *invisíveis* quando apenas acurácia ou F1 é reportado; um protocolo orientado à matriz de confusão e por classificador é, portanto, essencial para avaliar estratégias de balanceamento em contextos de segurança.

O restante deste artigo está organizado da seguinte forma. A Seção 2 revisa famílias de GANs e estratégias de balanceamento para NIDS. A Seção 3 detalha os três datasets, o protocolo experimental e as seis pipelines de balanceamento. A Seção 4 apresenta e discute os resultados entre datasets. A Seção 5 conclui o artigo e delineia trabalhos futuros.

---

## 2. Fundamentos e Trabalhos Relacionados

### 2.1 Redes Adversariais Generativas e suas Variantes

Uma GAN [10] treina duas redes em um jogo de soma zero: um gerador $G$ mapeia ruído latente $\mathbf{z} \sim p_z$ para amostras sintéticas, e um discriminador $D$ distingue amostras reais das geradas. O treinamento minimiza um proxy da divergência de Jensen-Shannon (JS), conhecido por sofrer de gradientes que desaparecem e de colapso de modos [11]. A GAN de Wasserstein [11] substitui o objetivo JS pela distância Wasserstein-1, produzindo um crítico cujos gradientes permanecem informativos mesmo quando as distribuições não se sobrepõem. A WGAN-GP [12] impõe a restrição de Lipschitz com uma penalidade de gradiente, melhorando muito a estabilidade do treinamento. GANs condicionais [13] condicionam ambas as redes em informação auxiliar (ex.: rótulos de classes), permitindo a geração controlada de amostras de uma classe específica — uma propriedade diretamente útil para a superamostragem da classe minoritária.

Para dados tabulares, Xu et al. [14] propuseram o CTGAN, que aborda dois problemas fundamentais das GANs em dados tabulares: (i) colunas contínuas raramente seguem uma distribuição gaussiana, o que eles tratam com normalização específica de modos baseada em um modelo de mistura gaussiana (GMM); e (ii) o gerador não consegue facilmente amostrar de todos os modos discretos de uma coluna categórica, o que eles tratam com vetores condicionais e treino por amostragem, juntamente com um discriminador pac ($\mathrm{pacs}=10$) para mitigar o colapso de modos. Essas escolhas de projeto tornam o CTGAN particularmente adequado a dados de fluxo de rede, cujas características contínuas (durações, estatísticas de pacotes e bytes) são tipicamente multimodais.

### 2.2 Estratégias de Oversampling para Detecção de Intrusão em Rede

O reamostragem é a contramedida mais usada contra o desbalanceamento em NIDS. O SMOTE [7] interpola entre vizinhos da classe minoritária; SMOTETomek e SMOTE-ENN [8] combinam SMOTE com regras de limpeza (links de Tomek ou vizinhos mais próximos editados) para remover amostras ruidosas e sobrepostas; o ADASYN [9] adapta o número de amostras geradas à densidade local da classe minoritária. Esses métodos são simples e rápidos, mas sua interpolação linear pode gerar amostras irreais quando a classe minoritária é multimodal ou se sobrepõe à classe majoritária, e estudos recentes em larga escala ainda reportam ganhos inconsistentes em ambientes IoT [28-30].

O oversampling baseado em GAN aprende a distribuição dos dados em vez de interpolar localmente. Engelmann e Lessmann [19] mostraram que GANs condicionais de Wasserstein são competitivas com o oversampling clássico para dados tabulares de crédito, e essa linha de trabalho foi estendida a NIDS por numerosos autores, incluindo o aumento GAN para detecção de intrusão baseada em imagem [31]. Zheng et al. [32] introduziram CWGAN-GP para classificação desbalanceada, e Yao e Zhao [17] aplicaram oversampling CWGAN-GP à detecção de intrusão, reportando melhor classificação que algoritmos tradicionais de oversampling em dois datasets benchmark. Ding et al. [33] propuseram TMG-GAN, um método de aprendizado desbalanceado baseado em GAN para NIDS publicado no IEEE TIFS. Swadi e Al-Mashhadi [34] usaram GANs de Wasserstein condicionais para balanceamento de classes em datasets de detecção de intrusão. WCGAN-GP também foi combinado com classificadores XGBoost em IDS baseados em fluxo [35], e a detecção de anomalias aumentada por GAN foi aplicada à detecção de malware IoT [36].

O CTGAN, em particular, tem atraído atenção crescente na literatura de NIDS. Habibi et al. [16] modelaram dados tabulares IoT desbalanceados com CTGAN e aprendizado de máquina para melhorar a detecção de ataques de botnet IoT. Alabsi et al. [37] construíram um IDS baseado em CTGAN para ataques DDoS e DoS. A-NIDS [20] usa CTGAN empilhado para detecção ciente de aprendizado contínuo. Soflaei et al. [21] combinaram dados balanceados com CTGAN com classificadores fracos e um meta-classificador XGBoost, reportando 98% de acurácia binária no UNSW-NB15. CE-GAN [22] aumenta amostras raras com um encoder-decoder condicional de agregação e uma perda composta. Outras abordagens generativas incluem CWVAEGAN-1DCNN [6], que usa uma decomposição variacional de mistura gaussiana antes da geração, MCGAN [38], DAE-GAN [39] e SYN-GAN [18], que mira a segurança IoT.

### 2.3 Dados Generativos para Segurança IoT e Datasets

A escolha do benchmark influencia fortemente o desempenho reportado. Datasets comuns de NIDS de IoT e de uso geral incluem N-BaIoT [40], Bot-IoT [41], Edge-IIoTset [23], UNSW-NB15 [42], NSL-KDD [43] e os levantamentos recentes em [3,4]. O dataset IoT-23 [5] foi capturado no Laboratório Stratosphere com 20 capturas de malware (Mirai, Torii, Hajime, Gagfyt e outros) e três capturas de dispositivos IoT benignos (Philips HUE, Amazon Echo, fechadura Somfy). É um dos datasets IoT rotulados mais realistas e recentemente coletados, e foi usado em desafios recentes de detecção baseada em ML [36]. No entanto, a maioria dos estudos com IoT-23 ou usa características de nível de fluxo da captura completa de vários gigabytes, ou se restringe a um único cenário, e poucos reportam a matriz de confusão detalhada que revelaria a contagem de falsos negativos. Baselines de detecção de anomalias como Kitsune [44], geração de tráfego de nível de fluxo com GANs [45] e modelos profundos híbridos que analisam desbalanceamento e robustez conjuntamente [46] complementam a literatura de oversampling generativo. Moti et al. [36] usaram GANs para detectar malware IoT não visto, e Rahman et al. [18] treinaram modelos de NIDS em dados totalmente sintéticos de GAN, mas nenhum realiza uma comparação frente a frente de famílias de geradores sob um pipeline fixo.

### 2.4 Lacunas e Posicionamento

Três lacunas motivam nosso trabalho. Primeiro, os estudos existentes comparam métodos generativos de oversampling entre si ou contra o SMOTE sob classificadores, datasets ou conjuntos de características *diferentes*, tornando impossível isolar a contribuição marginal do gerador. Segundo, quase nenhum estudo reporta falsos negativos como métrica de primeira classe, mesmo sendo o erro crítico de segurança. Terceiro, não há benchmark controlado de reamostragem clássica (SMOTETomek) contra baselines generativos (GAN vanilla, WGAN-GP, cWGAN-GP, CTGAN) reproduzido de forma idêntica em múltiplos datasets e classificadores reais. Nossa contribuição aborda essas lacunas com um protocolo estritamente controlado em três datasets reais, descrito a seguir. Além da comparação empírica, fazemos uma contribuição metodológica, até onde sabemos, ausente da literatura de oversampling em NIDS: reportamos a *matriz de confusão completa* (incluindo a contagem de FNs, crítica para a segurança) para toda configuração estratégia-classificador-dataset, e estruturamos o artigo em torno do que *cada estratégia não corrige*, em vez das melhores linhas. Este enquadramento honesto é o que permite concluir que nenhuma família de geradores domina e que os benefícios do balanceamento dependem do classificador e do dataset—conclusões que artigos focados apenas em métricas agregadas não sustentam.

---

## 3. Metodologia

### 3.1 Datasets e Pré-processamento

Usamos três datasets reais e públicos de tráfego de rede rotulado de *IoT/IIoT*. O **Edge-IIoTset** [23] foi coletado em um testbed realista de sete camadas (Ferrag et al., IEEE Access 2022) com mais de dez tipos de sensores/atuadores de IoT/IIoT e catorze tipos de ataque (ex.: DDoS, MITM, ransomware, backdoor, SQL injection, XSS e port scanning); o arquivo oficial selecionado `DNN-EdgeIIoT-dataset.csv` fornece 61 características de fluxo de rede (MQTT, Modbus/TCP, HTTP, TCP/UDP, DNS), um `Attack_label` binário e um `Attack_type` multiclasse. O **TON_IoT** [24] (Alsaedi et al., IEEE Access 2020) foi capturado no Cyber Range da UNSW Canberra em uma rede de IoT/IIoT de escala média e contém fluxos de rede Zeek/Argus (44 colunas: durações, bytes, pacotes, estado de conexão e campos DNS/TLS/HTTP/`weird`), com um `label` binário e um `type` multiclasse; usamos o subconjunto de tráfego de rede. O **IoT-23** [5] foi capturado pelo Laboratório Stratosphere e contém fluxos benignos de três dispositivos reais de casa inteligente (Philips HUE, Amazon Echo, fechadura Somfy) e fluxos maliciosos de múltiplos botnets (Mirai, Torii, Hajime, Gagfyt e outros); usamos um espelho pré-processado dos registros Zeek `conn.log` (6,05 milhões de fluxos, 21 colunas), mantido binário como benigno vs. malicioso.

Para tornar os três datasets diretamente comparáveis, cada um é reduzido a um workload idêntico por amostragem estratificada. De cada dataset completo extraímos uma amostra estratificada de exatamente **40.000 fluxos com 82% benigno (32.800) e 18% ataque (7.200)** usando uma semente fixa (42), que espelha o regime de desbalanceamento do tráfego IoT real no qual os ataques são minoria. A amostra é dividida 70/30 estratificada: **28.000 fluxos de treino** (22.960 benignos, 5.040 ataque) e **12.000 fluxos de teste** (9.840 benignos, 2.160 ataque), garantindo que o conjunto de teste seja idêntico em todas as seis estratégias de balanceamento para um dado dataset. As características numéricas de fluxo são padronizadas com `StandardScaler`, e a seleção de características é realizada com `SelectPercentile` (ANOVA $f$-classif, 60%), ajustada apenas na divisão de treino e reutilizada na divisão de teste para evitar qualquer vazamento de informação. Para o IoT-23 as características são os campos do Zeek `conn.log` (durações, bytes, pacotes, portas, `missed_bytes`); para Edge-IIoTset e TON_IoT são as características numéricas de nível de fluxo retidas por seus respectivos parsers. A pipeline está resumida na Figura 1.

**Figura 1** — Pipeline experimental. Para cada um dos três datasets reais (Edge-IIoTset, TON_IoT, IoT-23), 40.000 fluxos (82% benigno / 18% ataque) são pré-processados (`StandardScaler`, `SelectPercentile` 60%) e divididos 70/30 estratificados (semente 42). O treino (28.000 fluxos) é balanceado por uma de seis estratégias, cada classificador é treinado e a avaliação é feita no conjunto de teste fixo (12.000 fluxos, 9.840 benignos / 2.160 ataque).

### 3.2 Estratégias de Balanceamento

Seis estratégias são aplicadas à divisão de treino antes da classificação. Cada estratégia generativa produz exatamente 17.920 fluxos de ataque sintéticos, rebalanceando a classe minoritária à paridade (5.040 → 22.960), de modo que o conjunto de treino aumentado contenha 45.920 fluxos.

**Sem balanceamento (baseline).** O conjunto de treino desbalanceado original (82% benigno) é usado diretamente. Este baseline quantifica o viés introduzido pelo desbalanceamento e o número máximo de falsos negativos que cada classificador pode produzir, e é a referência contra a qual todas as reduções são medidas.

**SMOTETomek.** O SMOTETomek [8] primeiro aplica SMOTE ($k{=}5$) para sintetizar novas amostras maliciosas e depois remove pares de links de Tomek para limpar as fronteiras de classe. Representa o estado da arte entre os híbridos clássicos de reamostragem e serve como a estratégia não-generativa de referência.

**GAN vanilla.** Uma GAN padrão [10] é treinada apenas nas amostras minoritárias (ataque). O gerador mapeia ruído gaussiano de 32 dimensões por três camadas densas (64, 128, 256) com normalização em lote [48], ReLU e saída `tanh`; o discriminador usa duas camadas densas (256, 128) com dropout (0,3) e saída sigmoide. O treinamento usa entropia cruzada binária com Adam [49] ($2\times10^{-4}$, $\beta_1{=}0,5$), batch de 64 e 300 épocas. Após o treinamento, 17.920 amostras são sorteadas do gerador.

**WGAN-GP.** A WGAN-GP [12] substitui o discriminador por um crítico que produz um valor real (sem sigmoide), treinado para minimizar a distância de Wasserstein com coeficiente de penalidade de gradiente $\lambda{=}10$ e cinco atualizações de crítico por atualização do gerador ($n_{\mathrm{critic}}{=}5$). Arquiteturas e configurações do otimizador são idênticas às da GAN vanilla. Essa variante isola a contribuição da perda de Wasserstein sozinha (sem condicionamento de classe).

**WGAN-GP condicional (cWGAN-GP).** O cWGAN-GP estende a WGAN-GP com condicionamento de classe [13,17]: tanto o gerador quanto o crítico recebem o rótulo da classe por meio de uma camada de embedding (2 classes → 16 dimensões) concatenado à entrada. O modelo é treinado no conjunto de treino completo, de modo que o gerador aprenda os dois modos, e a geração é realizada condicionada à classe maliciosa, produzindo 17.920 amostras que respeitam a distribuição condicional.

**CTGAN.** O CTGAN [14] é treinado no conjunto de treino completo usando sua normalização padrão específica de modos: cada característica contínua é decomposta com um modelo de mistura gaussiana variacional, e as características categóricas são codificadas com vetores one-hot mais amostragem condicional por treino-por-amostragem. A rede usa a arquitetura padrão do CTGAN (2 camadas ocultas de 256 unidades) com um discriminador pac ($\mathrm{pacs} = 10$), batch de 200 e 300 épocas. Um total de 17.920 amostras é então gerado condicionado à classe maliciosa.

### 3.3 Classificadores

Quatro classificadores são treinados em cada conjunto de treino (possivelmente aumentado) e avaliados no mesmo conjunto de teste.

- **MLP**: duas camadas densas ocultas (128 e 64 neurônios, ReLU) com dropout (0,3), saída sigmoide, Adam ($10^{-3}$), entropia cruzada binária, batch 64, até 60 épocas com parada antecipada (paciência 6) na perda de validação.
- **XGBoost** [25]: 300 árvores, taxa de aprendizado 0,05, profundidade máxima 6, subsample e colsample 0,8, treinamento por histograma.
- **Random Forest** [26]: 300 árvores.
- **LSTM** [27]: duas camadas LSTM empilhadas (64 e 32 unidades) com dropout (0,3), saída sigmoide, Adam ($10^{-3}$), entropia cruzada binária, batch 64, até 60 épocas com parada antecipada (paciência 6). Cada fluxo é apresentado como uma sequência de $n$ passos temporais, onde $n$ é o número de características selecionadas, uma característica por passo.

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

Além desses agregados, analisamos explicitamente as contagens de FN e FP, pois em aplicações de segurança um falso negativo (malware não detectado) é o erro mais custoso. Como uma regra ingênua de "menor FN" pode selecionar um cenário que reduz FNs ao preço de um F1-score colapsado (ex.: um gerador com alto recall mas precisão muito baixa), adotamos uma regra explícita de seleção da "melhor configuração balanceada" reportada na Tabela II: *entre os cinco cenários balanceados, escolhe-se o de menor FN cujo F1-score fique dentro de 0,05 do melhor F1-score alcançado por qualquer cenário balanceado daquele modelo e dataset*. Essa regra é descrita a priori, evita cherry-picking e é aplicada de forma idêntica a todos os resultados. Para quantificar a incerteza de amostragem em torno das estimativas pontuais, também calculamos intervalos de confiança de 95% por propagação Monte Carlo das contagens binomiais do teste: 200.000 extrações de $TP\sim\mathrm{Binomial}(TP+FN,\hat{R})$ e $FP\sim\mathrm{Binomial}(TN+FP,1-\widehat{\mathrm{TNR}})$ geram distribuições de FN, precisão, recall e F1, resumidas pelos percentis 2,5 e 97,5. Esses intervalos quantificam a incerteza binomial de amostra finita no conjunto de teste fixo e não são ajustados para as múltiplas comparações entre os 24 cenários modelo-dataset; devem, portanto, ser lidos por linha e não como testes de família. Os intervalos completos das 72 configurações e a análise de sensibilidade à tolerância são fornecidos como material suplementar (Tabelas Suplementares S1 e S2).

---

## 4. Resultados e Discussão

### 4.1 Desempenho de Detecção entre Datasets

A Tabela II reporta, para cada um dos três datasets reais e quatro classificadores: a contagem de falsos negativos do baseline desbalanceado, a contagem de falsos negativos da melhor configuração balanceada sob a regra da Seção 3.4, a estratégia selecionada, sua contagem de falsos positivos e a variação resultante de FN. Doze configurações no total compartilham o mesmo workload, divisão, pré-processamento e conjunto de teste; a única diferença entre linhas é o dataset e o classificador.

**Tabela II — Validação entre Datasets em Três Datasets Reais: Redução de Falsos Negativos na Melhor Estratégia de Balanceamento (contagens de FN no conjunto de teste fixo de 12.000 fluxos)**

| Dataset | Clf | FN (base) | FN (melhor) | Estratégia | FP (melhor) | ΔFN | F1 (melhor) |
|---|---|---|---|---|---|---|---|
| Edge-IIoTset | MLP | 327 | 284 | SMOTETomek | 90 | –13,1% | 0,9094 |
| Edge-IIoTset | XGBoost | 35 | 0 | SMOTETomek | 64 | –100% | 0,9854 |
| Edge-IIoTset | R. Forest | 37 | 0 | SMOTETomek | 66 | –100% | 0,9850 |
| Edge-IIoTset | LSTM | 1.156 | 993 | WGAN-GP | 151 | –14,1% | 0,6711 |
| TON_IoT | MLP | 283 | 258 | GAN | 159 | –8,8% | 0,9012 |
| TON_IoT | XGBoost | 70 | 64 | SMOTETomek | 72 | –8,6% | 0,9686 |
| TON_IoT | R. Forest | 62 | 55 | SMOTETomek | 67 | –11,3% | 0,9718 |
| TON_IoT | LSTM | 1.930 | 194 | SMOTETomek | 2.933 | –89,9% | 0,5570 |
| IoT-23 | MLP | 705 | 634 | WGAN-GP | 24 | –10,1% | 0,8226 |
| IoT-23 | XGBoost | 273 | 272 | SMOTETomek | 25 | –0,4% | 0,9271 |
| IoT-23 | R. Forest | 269 | 268 | WGAN-GP | 133 | –0,4% | 0,9042 |
| IoT-23 | LSTM | 1.190 | 698 | WGAN-GP | 114 | –41,3% | 0,7827 |

Três achados emergem da Tabela II. Primeiro, o benefício do balanceamento é dependente do classificador e concentra-se no modelo de sequência profundo. O LSTM é o classificador mais degradado pelo desbalanceamento — seus baselines desbalanceados carregam F1-scores de apenas 0,63 (Edge-IIoTset), 0,18 (TON_IoT) e 0,61 (IoT-23) — e também o de maior redução absoluta de FN: os FNs caem 14,1%, 89,9% e 41,3% nos três datasets (1.156→993, 1.930→194 e 1.190→698, respectivamente), com o F1-score balanceado subindo para 0,67, 0,56 e 0,78. O resultado do TON_IoT é o mais notável: o LSTM desbalanceado entra em colapso (recall de ataque de apenas 0,11; no protocolo out-of-fold ele classifica oito das dez dobras de validação quase inteiramente como benignas), e o SMOTETomek restaura o recall para 0,91 enquanto corta os FNs em 89,9%. A Figura 2 mostra as matrizes de confusão do LSTM no baseline desbalanceado e na melhor configuração balanceada de cada dataset. A melhora não é um artefato da regra de seleção: os intervalos de confiança de 95% por Monte Carlo binomial dos F1-scores balanceados — 0,67 [0,66–0,68], 0,56 [0,55–0,57] e 0,78 [0,78–0,79] — não se sobrepõem aos dos baselines desbalanceados — 0,63 [0,62–0,65], 0,18 [0,16–0,20] e 0,61 [0,60–0,62]. A redução concentra-se na célula de falso negativo (ataque real, predito benigno): o recall de ataque do LSTM sobe de 0,46 para 0,54 no Edge-IIoTset, de 0,11 para 0,91 no TON_IoT e de 0,45 para 0,68 no IoT-23, enquanto os falsos positivos permanecem limitados no Edge-IIoTset e no IoT-23 (151 e 114, respectivamente), mas sobem substancialmente no TON_IoT (2.933, cerca de 29,8% dos fluxos benignos de teste). Esse é o custo de precisão da linha SMOTETomek escolhida ali; sob a estrutura de custos assimétrica de segurança (custo de FN ≫ custo de FP) a redução de FN ainda domina, e o F1-guard impede o colapso completo de precisão que uma regra ingênua de menor FN causaria — mas a troca exata depende dos limiares de implantação, e é precisamente por isso que reportamos as duas contagens explicitamente. O efeito particularmente forte no LSTM é consistente com sua maior capacidade e com o fato de ser o classificador mais degradado pelo desbalanceamento: uma vez que a reamostragem impede as camadas recorrentes de colapsar na classe majoritária, o modelo recupera boa parte do sinal minoritário. Como a entrada é uma pseudo-sequência (uma característica padronizada por passo temporal, em ordem de coluna, Seção 3.4), não atribuímos o ganho a uma estrutura temporal genuína dos fluxos; se entradas sequenciais ordenadas por conexão (ex.: sequências de eventos Zeek) ampliam o benefício, isso fica para trabalho futuro.

**Figura 2** — Matrizes de confusão do LSTM no conjunto de teste fixo de 12.000 fluxos, por dataset, no baseline desbalanceado e na melhor configuração balanceada (regra de seleção da Seção 3.4).

Segundo, os ensembles de árvores já são fortes sob desbalanceamento, mas sua saturação depende do dataset. No TON_IoT e no IoT-23 o XGBoost e o Random Forest desbalanceados já deixam de detectar poucos ataques (70/62 e 273/269, respectivamente), e o balanceamento acrescenta no máximo ≈11% de redução de FN (TON_IoT) ou é marginal (IoT-23); isso é consistente com a conhecida robustez de boosting e bagging ao desbalanceamento moderado. No Edge-IIoTset, por outro lado, o SMOTETomek elimina *todos* os falsos negativos residuais dos dois ensembles de árvores (35→0 e 37→0) ao custo de apenas 64–66 alarmes falsos e um F1 0,6 pp menor — o reamostrador clássico fecha a lacuna residual sem nenhum gerador. A Figura 3 (heatmap de F1-score) e a Figura 4 (barras de FN) visualizam esses padrões em todas as seis estratégias e quatro modelos.

**Figura 3** — F1-score por dataset, modelo e estratégia de balanceamento. A coluna do LSTM mostra a maior lacuna entre o baseline desbalanceado e os cenários balanceados.

**Figura 4** — Falsos negativos por modelo e estratégia de balanceamento no conjunto de teste fixo de cada dataset.

Terceiro, o MLP mostra ganhos pequenos, porém consistentes, e nunca regride sob o F1-guard: os FNs caem 13,1% no Edge-IIoTset (SMOTETomek), 8,8% no TON_IoT (GAN vanilla) e 10,1% no IoT-23 (WGAN-GP), com o F1 balanceado permanecendo dentro de 0,02 do melhor valor em cada caso. Nesses cenários moderadamente desbalanceados e quase separáveis, o ganho do MLP é real, mas uma ordem de grandeza menor que o do LSTM — o oversampling importa exatamente onde o desbalanceamento já degradou o detector, como mostra o LSTM. O artigo atinge, assim, uma conclusão mais matizada do que as manchetes "oversampling generativo é melhor" encontradas em parte da literatura: o valor do balanceamento é real, mas condicionado ao classificador, e é maior precisamente onde o desbalanceamento degrada mais o detector (redes profundas em tráfego difícil).

### 4.2 O Método de Balanceamento em Isolamento

Como para cada modelo e dataset todos os cenários compartilham o mesmo conjunto de teste, conjunto de características e divisão de treino, as diferenças na Tabela II são atribuíveis apenas à estratégia de balanceamento. Nenhuma estratégia domina isoladamente. O SMOTETomek — a referência clássica, não-generativa — é selecionado como melhor em sete das doze configurações (nos três datasets, principalmente para MLP e ensembles), o método Wasserstein WGAN-GP em quatro (as três linhas do LSTM em Edge-IIoTset e IoT-23 mais o MLP do IoT-23) e a GAN vanilla em uma (o MLP do TON_IoT); o cWGAN-GP nunca é o único melhor, e o CTGAN — consistentemente o gerador mais forte para o LSTM (ex.: 211 FNs para o LSTM do TON_IoT antes do guard de precisão, contra 194 do SMOTETomek) — também nunca vence sob o F1-guard. Esse padrão distribuído, que contradiz a noção de uma única família vencedora de geradores, é precisamente o tipo de evidência que o relato por métricas agregadas esconde: diferenças de F1 reportadas entre cenários costumam estar dentro de 0,05, enquanto as contagens de FN/FP que implicam podem diferir por uma ordem de grandeza na classe minoritária.

Para garantir que os vencedores da Tabela II não sejam um artefato da tolerância 0,05 da regra de seleção, repetimos a seleção para tolerâncias de 0,00, 0,02, 0,05 e 0,10. O padrão geral é estável no nível da redução de FN: para o LSTM a redução permanece grande em toda tolerância — TON_IoT de −86,9% a −89,9%, IoT-23 constante em −41,3%, Edge-IIoTset de −12,2% a −38,1% —, e a estratégia escolhida é fixa no TON_IoT (SMOTETomek a partir da tolerância 0,02) e no IoT-23 (WGAN-GP), enquanto no Edge-IIoTset ela se alterna entre SMOTETomek, WGAN-GP e GAN vanilla conforme a tolerância relaxa, sempre mantendo o F1 balanceado dentro de 0,08 do melhor. Por outro lado, tolerâncias frouxas podem ser contraproducentes em problemas fáceis: com 0,10, o LSTM do Edge-IIoTset trocaria o WGAN-GP (FN 993, FP 151, F1 0,67) pelo cenário de GAN vanilla (FN 716, FP 1.243, F1 0,60), trocando uma redução leve de FN por uma alta de oito vezes nos alarmes falsos — exatamente o colapso que o F1-guard evita.

### 4.3 Robustez das Pipelines Propostas

Para verificar que os ganhos de balanceamento da Tabela II não são um artefato da divisão 70/30, reexecutamos a cadeia-chave sob um **protocolo honesto de 10-fold out-of-fold (OOF)** que os notebooks implementam na seção `[OOF-10]`, sem vazamento:

- **Verdade de campo.** A mesma amostra estratificada $(X_s,y_s)$ e o mesmo construtor real de LSTM (`criar_lstm`);
- **K-fold estratificado.** `StratifiedKFold(10, shuffle, random_state=42)` sobre $(X_s,y_s)$;
- **Por dobra, sem vazamento.** O scaler, o seletor de características e a estratégia de balanceamento são ajustados *somente* na partição de treino da dobra; a partição de validação é transformada com o scaler/seletor ajustados no treino daquela dobra (nunca reajustados na validação) — nenhuma informação de validação de qualquer dobra afeta o treino;
- **GANs apenas em inferência.** Os geradores WGAN-GP e cWGAN-GP já treinados (nas células GAN do notebook) geram amostras sintéticas minoritárias para o treino da dobra em modo *inferência* ($\mathrm{training}=\mathrm{False}$); não são retreinados por dobra. Documentamos essa limitação de forma honesta: o retreino de GAN por dobra teria custo multiplicativo e é evitado por projeto. O LSTM é retreinado por dobra com parada antecipada;
- **Agregação.** Cada dobra contribui com uma predição out-of-fold sobre sua partição de validação; as dez predições OOF são agrupadas para reportar média±desvio de ACC/Recall/F1 por estratégia e os falsos negativos totais.

O protocolo é deliberadamente conservador: mede a robustez da *cadeia classificadora* sob validação cruzada mantendo os geradores fixos, o que mantém o custo total aceitável (≈6–8 h). As três rodadas (Edge-IIoTset, TON_IoT e IoT-23) reportadas na Tabela III estão completas; cada valor é tomado literalmente da agregação dos `resultados_oof10_<dataset>.csv` (nenhuma estimativa é inserida, nenhum valor é inventado).

**Tabela III — Robustez out-of-fold (média±desvio sobre 10 dobras; FN é o total crítico para a segurança). Valores reportados literalmente dos `resultados_oof10_<dataset>.csv` para os três datasets (nenhuma estimativa inserida).**

| Dataset | Estratégia | ACC | Recall | F1 | FN |
|---|---|---|---|---|---|
| Edge-IIoTset | LSTM, Original | 0,9503±0,0246 | 0,7896±0,0442 | 0,8543±0,0535 | 1.515 |
| Edge-IIoTset | LSTM, SMOTETomek | 0,9714±0,0136 | 0,9113±0,0369 | 0,9201±0,0372 | 639 |
| Edge-IIoTset | LSTM, WGAN-GP | 0,9635±0,0092 | 0,8235±0,0296 | 0,8902±0,0276 | 1.271 |
| Edge-IIoTset | LSTM, cWGAN-GP | 0,9419±0,0351 | 0,7533±0,1315 | 0,8212±0,1093 | 1.776 |
| TON_IoT | LSTM, Original | 0,8421±0,0483 | 0,1426±0,3022 | 0,1576±0,3344 | 6.173 |
| TON_IoT | LSTM, SMOTETomek | 0,9679±0,0037 | 0,9246±0,0145 | 0,9121±0,0098 | 543 |
| TON_IoT | LSTM, WGAN-GP | 0,9719±0,0035 | 0,9142±0,0152 | 0,9214±0,0101 | 618 |
| TON_IoT | LSTM, cWGAN-GP | 0,9631±0,0185 | 0,8917±0,0726 | 0,8965±0,0543 | 780 |
| IoT-23 | LSTM, Original | 0,9445±0,0142 | 0,6996±0,0807 | 0,8173±0,0497 | 2.163 |
| IoT-23 | LSTM, SMOTETomek | 0,9534±0,0135 | 0,7781±0,0723 | 0,8558±0,0431 | 1.598 |
| IoT-23 | LSTM, WGAN-GP | 0,9499±0,0047 | 0,7392±0,0281 | 0,8414±0,0172 | 1.878 |
| IoT-23 | LSTM, cWGAN-GP | 0,9532±0,0135 | 0,7533±0,0757 | 0,8512±0,0443 | 1.776 |

### 4.4 Comparação com Trabalhos Relacionados

A Tabela IV posiciona nosso protocolo contra estudos recentes de oversampling generativo para NIDS. A comparação numérica direta é dificultada por diferenças em datasets, características e classificadores — precisamente o problema que nos propusemos a resolver —, mas dois pontos qualitativos se destacam. Primeiro, estudos que reportam métricas detalhadas de classe minoritária consistentemente identificam recall/falsos negativos como a métrica que o balanceamento generativo mais melhora [6,22,38]. Segundo, nossa comparação controlada mostra que pipelines baseadas em CTGAN [20,21,16] são fortes, mas não unicamente: o SMOTETomek clássico as iguala em várias configurações, algo que estudos de dataset e classificador únicos não conseguem revelar.

**Tabela IV — Trabalhos Relacionados sobre Oversampling Generativo para NIDS (representativos)**

| Trabalho | Modelo | Datasets | Contribuição-chave |
|---|---|---|---|
| Habibi et al. [16] | CTGAN | IoT-23 | Modelagem tabular balanceada com CTGAN para botnets IoT |
| A-NIDS [20] | CTGAN empilhado | CICIDS-2017/18 | IDS adaptativo a drift, latência de 5 µs |
| Alabsi et al. [37] | CTGAN | CICIDS-2017 | IDS CTGAN para DDoS/DoS |
| Yao et al. [17] | CWGAN-GP | NSL-KDD, UNSW-NB15 | Oversampling CWGAN-GP estável |
| SYN-GAN [18] | SYN-GAN | UNSW-NB15, NSL-KDD, BoT-IoT | Treino com dados 100% sintéticos de GAN |
| CWVAEGAN [6] | CWVAEGAN+1D-CNN | NSL-KDD, UNSW-NB15 | Decomposição VGM, alto recall minoritário |
| Park et al. [15] | Baseado em GAN | datasets NIDS | NIDS aumentado por GAN baseado em IA |
| Soflaei et al. [21] | CTGAN+ensembles | UNSW-NB15 | 98% de acurácia binária |
| CE-GAN [22] | CE-GAN | NSL-KDD, UNSW-NB15 | Perda composta, ensemble teórico de jogos |
| Swadi et al. [34] | WCGAN | UNSW-NB15, KDD CUP99 | Balanceamento de classes Wasserstein |
| TMG-GAN [33] | TMG-GAN | CICIDS2017, UNSW-NB15 | Aprendizado desbalanceado por GAN |
| **Nosso** | **6 estratégias × 4 clf** | **Edge-IIoTset, TON_IoT, IoT-23** | **Benchmark controlado de 6 vias × 4 clf focado em FN** |

### 4.5 Custo Computacional

O custo do balanceamento é dominado pelas estratégias generativas: treinar cada gerador por 300 épocas foi o passo único mais caro de cada cenário, enquanto o SMOTETomek (apenas reamostragem) e os classificadores acrescentaram poucos segundos. A Tabela V reporta o tempo de relógio dos quatro loops de treino dos geradores, medido no mesmo perfil de GPU do Google Colab ao executar os notebooks que produziram os resultados da Tabela II. A GAN clássica (Seção 3.2), cujos loops gerador/discriminador rodam em Python interpretado, é de longe a mais lenta e consumiu ≈16–21 min por dataset (≈4–6× o WGAN-GP). As variantes Wasserstein convergem em 3,4–4,7 min, e o CTGAN em 2,2–5,4 min, escalando com o número de fluxos da classe minoritária. Treinar os quatro geradores ainda leva menos de ≈34 min por dataset, confortavelmente dentro de uma sessão única do Colab.

**Tabela V — Tempo de Treino dos Geradores por Dataset (segundos de relógio, GPU única, 300 épocas)**

| Dataset | GAN | WGAN-GP | cWGAN-GP | CTGAN |
|---|---|---|---|---|
| Edge-IIoTset | 971 | 222 | 273 | 321 |
| TON_IoT | 1280 | 207 | 253 | 282 |
| IoT-23 | 953 | 211 | 265 | 130 |

### 4.6 Custo-benefício: redução de falsos negativos versus tempo de treinamento

Como o LSTM é o classificador em que o balanceamento mais importa, a Tabela VI confronta, por dataset, a contagem de falsos negativos (FN) do LSTM em cada cenário com o tempo de relógio necessário para produzi-la (tempo de treinamento do gerador; o SMOTETomek e o baseline sem balanceamento têm custo desprezível). Três padrões valem para todos os datasets. Primeiro, o SMOTETomek tem o melhor custo-benefício: corta os FNs em segundos (−89,9% no TON_IoT, −41,2% no IoT-23, −12,2% no Edge-IIoTset) a custo zero de gerador. Segundo, entre os métodos generativos o WGAN-GP é o mais eficiente, recuperando −75,5% (TON_IoT), −41,3% (IoT-23) e −14,1% (Edge-IIoTset) dos ataques em cerca de 3,5 minutos, seguido de perto pelo CTGAN no TON_IoT (−89,1% em 4,7 min). Terceiro, a GAN vanilla alcança o menor FN no Edge-IIoTset e no IoT-23 (716 e 554; reduções de −38,1% e −53,4%), mas exige 16–21 minutos — o gerador mais caro —, e o cWGAN-GP é o de pior custo-benefício, chegando a *aumentar* os FNs no Edge-IIoTset (1.156→1.445). Na prática, um operador com orçamento apertado de tempo deve começar pelo SMOTETomek; se o oversampling generativo for necessário, o WGAN-GP oferece o melhor trade-off de FN por minuto, reservando a GAN vanilla para os casos mais difíceis, em que seu custo extra é pago de volta pelo menor FN. A Figura 5 visualiza esses trade-offs.

**Tabela VI — Custo-benefício do LSTM por dataset: falsos negativos (FN, no teste fixo de 12.000 fluxos) versus tempo de treinamento do gerador (TT, em segundos). ΔFN é relativo ao baseline desbalanceado.**

| Dataset | Cenário | FN | TT (s) | ΔFN |
|---|---|---|---|---|
| Edge-IIoTset | Original | 1.156 | 0 | — |
| Edge-IIoTset | SMOTETomek | 1.015 | ≈0 | −12,2% |
| Edge-IIoTset | GAN | 716 | 971 | −38,1% |
| Edge-IIoTset | WGAN-GP | 993 | 222 | −14,1% |
| Edge-IIoTset | cWGAN-GP | 1.445 | 273 | +25,0% |
| Edge-IIoTset | CTGAN | 1.039 | 321 | −10,1% |
| TON_IoT | Original | 1.930 | 0 | — |
| TON_IoT | SMOTETomek | 194 | ≈0 | −89,9% |
| TON_IoT | GAN | 253 | 1.280 | −86,9% |
| TON_IoT | WGAN-GP | 472 | 207 | −75,5% |
| TON_IoT | cWGAN-GP | 1.611 | 253 | −16,5% |
| TON_IoT | CTGAN | 211 | 282 | −89,1% |
| IoT-23 | Original | 1.190 | 0 | — |
| IoT-23 | SMOTETomek | 700 | ≈0 | −41,2% |
| IoT-23 | GAN | 554 | 953 | −53,4% |
| IoT-23 | WGAN-GP | 698 | 211 | −41,3% |
| IoT-23 | cWGAN-GP | 702 | 265 | −41,0% |
| IoT-23 | CTGAN | 833 | 130 | −30,0% |

**Figura 5** — Custo-benefício do LSTM: falsos negativos no teste fixo (eixo vertical) versus tempo de treinamento do gerador em segundos (eixo horizontal) para cada cenário de balanceamento e dataset. O SMOTETomek (TT≈0) ocupa a fronteira eficaz superior-esquerda, seguido do gerador barato WGAN-GP.

### 4.7 Ameaças à Validade

Diversas limitações devem ser reconhecidas. Primeiro, os três datasets são reais e públicos, mas o subconjunto IoT-23 usado aqui consiste em 6,05 milhões de fluxos Zeek `conn.log` preparados por um pré-processamento de terceiros, que cobre uma porção grande, mas não completa, das capturas oficiais do IoT-23; o Edge-IIoTset e o TON_IoT usam suas distribuições oficiais selecionadas/processadas (o arquivo DNN-EdgeIIoT distribuído via Kaggle/IEEE DataPort e o CSV de tráfego de rede da UNSW), e cada dataset contribui características de um parser diferente (campos no estilo Wireshark/Zeek/Argus), mesmo com pipeline idêntico. Segundo, os resultados são reportados para uma única divisão e semente e sem busca de hiperparâmetros; o protocolo fixo garante reprodutibilidade interna, mas não quantificamos a variância entre divisões. Terceiro, a "melhor configuração balanceada" é selecionada post-hoc por uma regra explícita e a priori (Seção 3.4) que protege contra colapso de precisão, mas a multiplicidade de testes entre seis estratégias pode inflar a chance de selecionar um FN espurimente baixo; por isso enfatizamos *padrões* de efeito entre datasets (ex.: o LSTM melhorando consistentemente) em vez de linhas individuais. Quarto, as amostras sintéticas foram validadas apenas implicitamente, via classificação a jusante e projeções PCA, e não com testes formais de fidelidade (ex.: treino-em-sintético/teste-em-real, estatísticas KS). Quinto, nosso estudo está restrito à classificação binária (benigno vs. malware); a detecção multiclasse por família e a análise por captura dos registros do IoT-23 permanecem em aberto. Finalmente, apenas quatro famílias de classificadores foram consideradas; detectores modernos convolucionais e baseados em atenção não foram avaliados.

---

## 5. Conclusão e Trabalhos Futuros

Apresentamos uma comparação estritamente controlada de seis estratégias de balanceamento — nenhuma, SMOTETomek, GAN vanilla, WGAN-GP, cWGAN-GP e CTGAN — para detecção binária de intrusão, reproduzida de forma idêntica em três datasets reais de IoT/IIoT (Edge-IIoTset, TON_IoT e IoT-23) e quatro classificadores (MLP, XGBoost, Random Forest e LSTM), com workload, divisão, etapa de seleção de características e conjunto de teste compartilhados. Os resultados mostram que o benefício do balanceamento é fortemente dependente do classificador. O modelo de sequência profundo, o mais degradado pelo desbalanceamento (F1 desbalanceado de 0,18–0,63 entre datasets), é também o mais melhorado pela reamostragem, com falsos negativos reduzidos em 89,9% no TON_IoT (1.930→194), 41,3% no IoT-23 (1.190→698) e 14,1% no Edge-IIoTset (1.156→993). Os ensembles de árvores, já fortes sob desbalanceamento, ganham no máximo ≈11% no TON_IoT e no IoT-23, mas são integralmente limpos no Edge-IIoTset pelo SMOTETomek (FN→0); o MLP ganha pequenos, porém consistentes, 9–13%. Nenhuma estratégia domina isoladamente: o SMOTETomek clássico e o WGAN-GP baseado em Wasserstein alternam-se como melhores entre configurações, e o CTGAN é consistentemente próximo, mas nunca o único melhor. Em termos de custo-benefício, o SMOTETomek é a forma mais barata de reduzir FNs (segundos por dataset), o WGAN-GP é o melhor valor generativo (≈3,5 min por dataset), e a GAN vanilla só se justifica no tráfego mais difícil, onde seu custo extra é pago de volta pelo menor FN.

Essas nuances são invisíveis em relatos apenas de acurácia ou F1, o que motiva a principal contribuição metodológica deste trabalho. Além dos resultados empíricos, contribuímos com um protocolo de avaliação cuja tese central é a *honestidade*: estudos de desbalanceamento em NIDS devem (i) reportar as contagens da matriz de confusão — especialmente falsos negativos, o erro crítico de segurança — como métricas de primeira classe, (ii) isolar o efeito do balanceamento da escolha do classificador, mantendo workload, divisão, seleção de características e teste fixos, e (iii) declarar a priori uma regra de seleção que recuse uma redução de falso negativo comprada ao preço de um F1 colapsado. Deliberadamente, *não* afirmamos que a reamostragem reduz drasticamente os FNs em todos os cenários; a evidência mostra que o benefício é fortemente dependente do classificador e do dataset, e nosso protocolo é projetado explicitamente para que essas nuances sejam reportáveis em vez de descartadas por médias. Nosso template reproduzível — código, notebooks e datasets em um repositório público — permite que qualquer leitor reexecute a comparação de seis estratégias e quatro classificadores sobre seus próprios dados e obtenha as confusões que reportamos.

Trabalhos futuros incluem (i) estender o benchmark à detecção multiclasse por família e às capturas brutas completas de Edge-IIoTset e TON_IoT [23,24]; (ii) avaliar métricas de fidelidade treino-em-sintético/teste-em-real e geração com preservação de privacidade diferencial; (iii) combinar balanceamento com focal loss [50] e detectores profundos não sequenciais (CNNs, transformers) para testar se o achado específico do LSTM generaliza; e (iv) quantificar a variância entre divisões por validação cruzada de sementes repetidas.

---

## Referências citadas (numeração de exemplo)

A tradução mantém as referências do `.bib`; a numeração ([1]–[50]) segue a ordem de primeira citação no `main.tex` (padrão IEEEtran). O texto em inglês (`main.tex`) é a fonte de verdade; confira a numeração após compilar no Overleaf.