# **AtletiQ**

Este é um aplicativo desenvolvido em Python com Flet que utiliza técnicas de web scraping e machine learning para analisar e prever resultados de partidas do Campeonato Brasileiro de Futebol.

A aplicação busca dados atualizados da API da football-data.org, treina um modelo de regressão logística e apresenta diversas funcionalidades analíticas em uma interface amigável.

## **Novidades e Otimizações**

O projeto evoluiu para uma arquitetura baseada em **Big Data** e **Performance**, superando limitações de conectividade e processamento:

1. **Motor de Big Data (5 Anos):** O sistema agora procura automaticamente dados das últimas 5 temporadas. Isso permite que os modelos de IA aprendam com um volume muito maior de dados, aumentando a precisão das probabilidades.  
2. **Sistema de Cache Inteligente:** Implementada a persistência em atletiq\_dataset.csv. O app carrega instantaneamente os dados históricos do disco e utiliza a API apenas para atualizar os resultados mais recentes, reduzindo drasticamente o tempo de inicialização.  
3. **Interface Sofascore Style (Match Center):** Eliminada as abas redundantes de "Previsão" e "H2H". Agora, ao clicar em qualquer partida no Calendário, abre-se um **BottomSheet** contextual com todas as probabilidades e o histórico de confronto direto daquele jogo específico.  
4. **Tratamento Robusto de Dados:** Correção de conflitos de *timezone* (UTC) e validações de segurança para garantir que jogos futuros não interfiram nas estatísticas de vitórias passadas.

## **Funcionalidades Principais**

* **Previsão de Partidas (AI):** Modelo de Machine Learning que calcula a probabilidade de vitória (Mandante/Empate/Visitante).
* **Aba de Artilharia:** Aba dedicada aos artilheiros do campeonato. 
* **Simulador de Tabela Final:** Projeta a classificação final do campeonato processando os jogos restantes através do motor de IA.  
* **Match Center (H2H \+ Predictor):** Visualização integrada de probabilidades e retrospecto histórico (secular \+ recente) num único painel deslizante.  
* **Calendário Inteligente:** Navegação por jornadas com acesso direto à análise detalhada de cada confronto.  
* **UI Moderna:** Design focado em usabilidade com "Dark Mode" nativo e componentes visuais de alta fidelidade.

## **Tecnologias Utilizadas**

* [**Python**](https://www.python.org/): Linguagem base.  
* [**Flet**](https://flet.dev/): Framework de interface gráfica (baseado em Flutter).  
* [**Pandas**](https://pandas.pydata.org/): Manipulação de dados e análise de séries temporais.  
* [**Scikit-learn**](https://scikit-learn.org/): Modelagem preditiva (IA).  
* [**Requests**](https://requests.readthedocs.io/): Consumo de dados via API REST.

## **Estrutura do Projeto**

AtletiQ/

│

├── main.py \# Interface Gráfica e Lógica Principal

├── web\_scraper.py \# Consumo de dados via API (Football-Data.org)

├── feature\_engineering.py \# Engenharia de atributos para IA

├── model\_trainer.py \# Treino dos modelos (Random Forest/LogReg)

├── predictor.py \# Motor de inferência e simulador de tabela

├── analysis.py \# Processamento de H2H e histórico secular

├── atletiq\_dataset.csv \# Cache local de dados multi-ano

├── historico\_confrontos.csv \# Base de dados histórica secular

├── escudos.json \# Base de dados utilizada para os escudos da plataforma (buscados da web)

└── README.md \# Documentação do projeto

## **Como Instalar e Rodar**

### **1\. Obter uma API Key**

Obtenha o  token gratuito em [Football-Data.org](https://www.football-data.org/).

### **2\. Configurar o Token**

No ficheiro web\_scraper.py, insira o  token na variável correspondente:

self.api\_key \= "API\_KEY"

### **3\. Instalar Dependências**

pip install -r requirements.txt

### **4\. Executar**

python main.py

*Nota: A primeira execução pode demorar alguns segundos extra enquanto o sistema constrói o cache inicial de 5 anos.*

## **Aviso Legal**

Este software é uma ferramenta de análise estatística. As previsões baseiam-se em probabilidades matemáticas e **não constituem garantia de lucro ou resultados**. O uso para fins de apostas é de inteira responsabilidade do utilizador.
