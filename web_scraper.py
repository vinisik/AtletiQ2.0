import pandas as pd
import requests
import time

class AtletiQScraper:
    def __init__(self, api_key="API_KEY"):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4/"
        self.headers = {'X-Auth-Token': self.api_key}

    def buscar_dados_hibrido(self, ano):
        print(f"Buscando partidas ({ano})...")
        url = f"{self.base_url}competitions/BSA/matches"
        params = {'season': int(ano)}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200: return None
            data = response.json()
            matches = []
            de_para = {'Botafogo FR': 'Botafogo', 'CR Flamengo': 'Flamengo', 'Fluminense FC': 'Fluminense',
                       'São Paulo FC': 'São Paulo', 'SE Palmeiras': 'Palmeiras', 'SC Internacional': 'Internacional',
                       'Grêmio FBPA': 'Grêmio', 'Clube Atlético Mineiro': 'Atlético Mineiro', 'EC Bahia': 'Bahia',
                       'Fortaleza EC': 'Fortaleza', 'Cuiabá EC': 'Cuiabá', 'Vasco da Gama': 'Vasco',
                       'SC Corinthians Paulista': 'Corinthians', 'EC Vitória': 'Vitória', 'RB Bragantino': 'Bragantino'}
            for m in data.get('matches', []):
                h_raw, a_raw = m['homeTeam'].get('name', ''), m['awayTeam'].get('name', '')
                home = de_para.get(h_raw, h_raw.replace(' SAF', '').replace(' EC', '').strip())
                away = de_para.get(a_raw, a_raw.replace(' SAF', '').replace(' EC', '').strip())
                matches.append({'Rodada': m.get('matchday'), 'Date': m.get('utcDate'), 'HomeTeam': home, 'AwayTeam': away,
                                'FTHG': m['score']['fullTime'].get('home'), 'FTAG': m['score']['fullTime'].get('away')})
            return pd.DataFrame(matches)
        except: return None

    def fetch_scorers(self, ano):
        """Busca os artilheiros da competição no ano especificado."""
        print(f"Buscando artilharia ({ano})...")
        url = f"{self.base_url}competitions/BSA/scorers"
        params = {'season': int(ano)}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200: return None
            data = response.json()
            scorers = []
            for s in data.get('scorers', []):
                scorers.append({
                    'Jogador': s['player']['name'],
                    'Time': s['team']['name'],
                    'Gols': s['goals'],
                    'Assistências': s.get('assists', 0),
                    'Jogos': s.get('playedMatches', 0)
                })
            return pd.DataFrame(scorers)
        except: return None