# **⚽ AtletiQ \- Estatísticas do Brasileirão com IA**

**AtletiQ** é uma aplicação desktop moderna desenvolvida em Python e Flet que utiliza Inteligência Artificial (Machine Learning) para prever resultados, simular classificações e analisar estatísticas do Campeonato Brasileiro (Série A).

## **🔄 Novidades e Atualização de Fontes**

O projeto foi reformulado para garantir estabilidade e precisão nos dados, superando as limitações de bloqueios de acesso:

1. **Transição para API-Football-Data:** Abandonamos o *Web Scraping* instável do FBRef em favor de dados estruturados via JSON através da [Football-Data.org](https://www.football-data.org/). Isso garante carregamentos mais rápidos e maior fiabilidade.  
2. **Base de Dados Histórica (CSV):** Agora o sistema utiliza o ficheiro historico\_confrontos.csv para integrar estatísticas seculares no módulo de Confronto Direto (H2H), combinando a história do futebol com dados atuais.  
3. **Resiliência (Fallback):** O sistema agora tenta automaticamente carregar temporadas anteriores (2025) caso os dados da temporada atual (2026) ainda não estejam disponíveis ou ocorram erros de conexão.

## **🚀 Funcionalidades Principais**

* **🤖 Previsão de Partidas (AI):** Modelo de Regressão Logística que calcula a probabilidade de vitória (Mandante/Empate/Visitante), probabilidade de mais de 2.5 golos e "Ambas Marcam" (BTTS).  
* **📊 Simulador de Tabela Final:** Projeta a classificação final do campeonato processando todos os jogos restantes através do motor de IA.  
* **⚔️ Confronto Direto (H2H) Avançado:** Analisa o retrospecto entre dois clubes utilizando uma base histórica pré-carregada somada aos resultados das últimas temporadas.  
* **📅 Calendário Inteligente:** Visualize as próximas jornadas e clique diretamente num jogo para enviar os dados para o módulo de previsão.  
* **🌙 Interface Moderna:** Design focado em usabilidade com "Dark Mode" nativo, animações e componentes visuais sofisticados.

## **🛠️ Tecnologias Utilizadas**

* [**Python**](https://www.python.org/): Linguagem base do projeto.  
* [**Flet**](https://flet.dev/): Framework para criação da interface gráfica (UI).  
* [**Pandas**](https://pandas.pydata.org/): Processamento e manipulação de grandes volumes de dados.  
* [**Scikit-learn**](https://scikit-learn.org/): Implementação dos modelos de Machine Learning.  
* [**Requests**](https://requests.readthedocs.io/): Comunicação com a API de dados de futebol.

## **📂 Estrutura do Projeto**

AtletiQ/

│

├── main.py \# Interface Gráfica e Lógica da UI

├── web\_scraper.py \# Consumo de dados via API e limpeza de nomes

├── feature\_engineering.py \# Cálculo de força, forma recente e métricas de IA

├── model\_trainer.py \# Treino dos modelos (Resultado, Over 2.5, BTTS)

├── predictor.py \# Motor de previsão e simulador de tabela

├── analysis.py \# Processamento do histórico H2H e CSV

├── historico\_confrontos.csv \# Base de dados histórica de vitórias e empates

├── logo.png \# Identidade visual

└── README.md \# Documentação

## **⚙️ Como Instalar e Rodar**

### **1\. Obter uma API Key**

Crie uma conta gratuita em [Football-Data.org](https://www.football-data.org/) e obtenha o token de acesso.

### **2\. Configurar o Scraper**

No ficheiro web\_scraper.py, insira o token:

self.api\_key \= "API\_KEY"

### **3\. Instalar Dependências**

pip install -r requirements.txt

### **4\. Executar**

python main.py

## **⚠️ Aviso Legal**

Este software é um projeto de análise estatística. As previsões baseiam-se em probabilidades matemáticas e **não constituem garantia de resultados**. O uso das informações é de inteira responsabilidade do utilizador.