import pandas as pd
import requests
import time

class AtletiQScraper:
    def __init__(self, api_key="API_KEY"):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4/"
        self.headers = {'X-Auth-Token': self.api_key}

    def buscar_dados_hibrido(self, ano):
        print(f"Buscando dados da Série A ({ano}) via API-Football-Data...")
        url = f"{self.base_url}competitions/BSA/matches"
        params = {'season': int(ano)}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                print(f"Erro na API: {response.status_code}")
                return None

            data = response.json()
            matches = []

            # Dicionário de limpeza manual para casos específicos da API
            de_para = {
                'Botafogo FR': 'Botafogo',
                'CR Flamengo': 'Flamengo',
                'Fluminense FC': 'Fluminense',
                'São Paulo FC': 'São Paulo',
                'SE Palmeiras': 'Palmeiras',
                'SC Internacional': 'Internacional',
                'Grêmio FBPA': 'Grêmio',
                'Clube Atlético Mineiro': 'Atlético Mineiro',
                'Athletico Paranaense': 'Athletico Paranaense',
                'EC Bahia': 'Bahia',
                'Fortaleza EC': 'Fortaleza',
                'Cuiabá EC': 'Cuiabá',
                'Vasco da Gama': 'Vasco',
                'SC Corinthians Paulista': 'Corinthians',
                'EC Vitória': 'Vitória',
                'RB Bragantino': 'Bragantino'
            }

            for match in data.get('matches', []):
                home_raw = match['homeTeam'].get('name', '')
                away_raw = match['awayTeam'].get('name', '')
                
                # Aplica a limpeza via dicionário ou remove sufixos padrão
                home = de_para.get(home_raw, home_raw.replace(' SAF', '').replace(' EC', '').strip())
                away = de_para.get(away_raw, away_raw.replace(' SAF', '').replace(' EC', '').strip())

                matches.append({
                    'Rodada': match.get('matchday'),
                    'Date': match.get('utcDate'),
                    'HomeTeam': home,
                    'AwayTeam': away,
                    'FTHG': match['score']['fullTime'].get('home'),
                    'FTAG': match['score']['fullTime'].get('away')
                })

            return pd.DataFrame(matches)
        except Exception as e:
            print(f"Erro no scraper: {e}")
            return None