import pandas as pd
import cloudscraper
import time
import io

# Configuração global do scraper para simular um navegador real
def get_scraper():
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

def buscar_dados_brasileirao(ano):
    """
    Busca tabela de jogos (Scores & Fixtures).
    """
    print(f"Buscando tabela de jogos de {ano}...")
    url = f"https://fbref.com/en/comps/24/schedule/{ano}-Serie-A-Scores-and-Fixtures"
    
    scraper = get_scraper()
    
    try:
        response = scraper.get(url)
        if response.status_code == 429:
            print("Muitas requisições (429). Aguardando 10s...")
            time.sleep(10)
            response = scraper.get(url)
            
        if response.status_code != 200:
            print(f"Erro {response.status_code} ao acessar jogos.")
            return None

        html_content = io.StringIO(response.text)
        
        # Tenta pegar a tabela de resultados
        tabelas = pd.read_html(html_content, match="Home")
        if not tabelas: return None
        
        df = tabelas[0]
        
        # Limpeza e Padronização
        df = df[df['Wk'].notna() & (df['Wk'] != 'Wk')]
        df = df.rename(columns={'Home': 'HomeTeam', 'Away': 'AwayTeam'})
        
        if 'Score' in df.columns:
            df['Score'] = df['Score'].str.replace('–', '-', regex=False)
            gols = df['Score'].str.split('-', expand=True)
            if len(gols.columns) >= 2:
                df['FTHG'] = pd.to_numeric(gols[0], errors='coerce')
                df['FTAG'] = pd.to_numeric(gols[1], errors='coerce')
            else:
                df['FTHG'] = pd.NA
                df['FTAG'] = pd.NA
        
        return df[['Wk', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].rename(columns={'Wk': 'Rodada'})
    except Exception as e:
        print(f"Erro no scraper de jogos: {e}")
        return None

def buscar_artilheiros(ano):
    """
    Funcionalidade desativada para evitar erros de bloqueio e dependências.
    Retorna None para que a interface apenas ignore ou mostre aviso.
    """
    print("Busca de artilheiros desativada temporariamente.")
    return None