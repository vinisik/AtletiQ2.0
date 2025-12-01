import pandas as pd
import numpy as np


def preparar_dados_para_modelo(df_historico):
    """
    Cria a variável alvo (resultado) e calcula features de forma (médias móveis).
    """
    print("Preparando dados e calculando features...")
    # Garantir que os dados estão ordenados por data
    df_historico['Date'] = pd.to_datetime(df_historico['Date'])
    df_historico = df_historico.sort_values(by='Date').reset_index(drop=True)

    # Criar a variável alvo
    df_historico['Resultado'] = np.where(df_historico['FTHG'] > df_historico['FTAG'], 'Casa',
                                         np.where(df_historico['FTHG'] < df_historico['FTAG'], 'Visitante', 'Empate'))

    def get_points(resultado):
        if resultado == 'Casa':
            return 3, 0
        elif resultado == 'Visitante':
            return 0, 3
        else:
            return 1, 1

    # Criar colunas de pontos para casa e visitante
    df_historico['HomePoints'], df_historico['AwayPoints'] = zip(*df_historico['Resultado'].apply(get_points))

    time_stats = {}
    features_calculadas = []

    # Calcular as features para cada jogo
    for index, row in df_historico.iterrows():
        time_casa, time_visitante = row['HomeTeam'], row['AwayTeam']
        features_jogo = {}

        for time, lado in [(time_casa, 'Home'), (time_visitante, 'Away')]:
            if time not in time_stats:
                time_stats[time] = {'pontos': [], 'gm': [], 'gs': []}

            if len(time_stats[time]['pontos']) > 0:
                features_jogo[f'ForcaGeral_{lado}'] = np.mean(time_stats[time]['pontos'])
            else:
                features_jogo[f'ForcaGeral_{lado}'] = 1.0

            features_jogo[f'FormaPontos_{lado}'] = sum(time_stats[time]['pontos'][-5:])
            features_jogo[f'MediaGolsMarcados_{lado}'] = np.mean(time_stats[time]['gm'][-5:]) if time_stats[time][
                'gm'] else 0
            features_jogo[f'MediaGolsSofridos_{lado}'] = np.mean(time_stats[time]['gs'][-5:]) if time_stats[time][
                'gs'] else 0

        features_calculadas.append(features_jogo)

        # Atualizar as estatísticas do time após calcular as features
        time_stats[time_casa]['pontos'].append(row['HomePoints'])
        time_stats[time_casa]['gm'].append(row['FTHG'])
        time_stats[time_casa]['gs'].append(row['FTAG'])

        time_stats[time_visitante]['pontos'].append(row['AwayPoints'])
        time_stats[time_visitante]['gm'].append(row['FTAG'])
        time_stats[time_visitante]['gs'].append(row['FTHG'])

    df_features = pd.DataFrame(features_calculadas, index=df_historico.index)
    df_final = pd.concat([df_historico, df_features], axis=1)

    df_final = df_final.iloc[20:].reset_index(drop=True)
    return df_final, time_stats