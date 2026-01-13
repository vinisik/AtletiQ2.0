# **⚽ AtletiQ \- Estatísticas do Brasileirão com IA**

**AtletiQ** é uma aplicação desktop moderna desenvolvida em Python e Flet que utiliza Inteligência Artificial (Machine Learning) para prever resultados, simular classificações e analisar estatísticas do Campeonato Brasileiro (Série A).

## **🎨 Sobre o Projeto**

O AtletiQ combina o poder da análise de dados com uma interface visual sofisticada. O sistema coleta dados em tempo real da web, processa estatísticas históricas e treina um modelo de Regressão Logística para oferecer insights sobre partidas futuras.

## **🚀 Funcionalidades Principais**

* **🤖 Previsão de Partidas (AI):** Utiliza algoritmos de Machine Learning treinados com dados da temporada atual para calcular a probabilidade de vitória de cada time ou empate.  
* **📊 Simulador de Campeonato:** Permite simular o restante da temporada rodada a rodada, projetando a tabela final com base no desempenho atual das equipes.  
* **⚔️ Confronto Direto (H2H):** Análise histórica detalhada entre dois clubes, mostrando retrospecto de vitórias, empates e lista dos últimos jogos.  
* **🌐 Coleta de Dados em Tempo Real:** Sistema de *Web Scraping* integrado que busca os dados mais recentes diretamente da web (FBref).  
* **🌙 Interface Moderna:** Design "Dark Mode" nativo com elementos visuais sofisticados, animações suaves e responsividade.

## **🛠️ Tecnologias Utilizadas**

* [**Python**](https://www.python.org/)**:** Linguagem principal do projeto.  
* [**Flet**](https://flet.dev/)**:** Framework para construção da interface gráfica (UI) moderna e multiplataforma.  
* [**Pandas**](https://pandas.pydata.org/)**:** Manipulação e análise de dados estruturados (DataFrames).  
* [**Scikit-Learn**](https://scikit-learn.org/)**:** Criação, treinamento e execução do modelo de Machine Learning.  
* **Requests & lxml:** Bibliotecas para requisições HTTP e extração de dados (Web Scraping).

## **📦 Instalação e Execução**

Siga os passos abaixo para rodar o projeto localmente em sua máquina.

### **1\. Pré-requisitos**

Certifique-se de ter o **Python 3.10** ou superior instalado.

### **2\. Configurar o Ambiente**

Crie uma pasta para o projeto e coloque todos os arquivos .py nela.

### **3\. Instalar Dependências**

Abra o terminal na pasta do projeto e execute o comando abaixo para instalar todas as bibliotecas necessárias:

pip install flet pandas scikit-learn requests lxml

### **4\. Executar a Aplicação**

Para iniciar o AtletiQ Pro com a interface nativa, execute:

python main.py

*Nota: Certifique-se de que o arquivo logo.png esteja na mesma pasta do script para que a logomarca seja carregada corretamente.*

## **📂 Estrutura do Projeto**

A arquitetura do sistema é modular para facilitar a manutenção e escalabilidade:

AtletiQ/  
│  
├── main.py                 \# Interface Gráfica (Frontend \- Flet)  
├── web\_scraper.py          \# Coleta de dados da web  
├── feature\_engineering.py  \# Processamento de dados e criação de features  
├── model\_trainer.py        \# Treinamento do modelo de IA  
├── predictor.py            \# Lógica de previsão e simulação  
├── analysis.py             \# Lógica de análise histórica (H2H)  
├── logo.png                \# Logotipo da aplicação  
└── README.md               \# Documentação do projeto

## **⚠️ Aviso Legal**

Este software foi desenvolvido para fins educacionais e de aprendizado em Ciência de Dados e Desenvolvimento de Software.

* As previsões são baseadas em estatísticas históricas e **não garantem resultados futuros**.  
* O uso de Web Scraping deve respeitar os termos de serviço dos sites provedores de dados.

## **👨‍💻 Autor**

Desenvolvido com foco em Clean Code, UI Design e Data Science.
