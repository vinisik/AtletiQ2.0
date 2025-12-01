import pandas as pd
import numpy as np

def prever_jogo_especifico(time_casa, time_visitante, modelo, encoder, time_stats, colunas_modelo):
    """
    Prevê o resultado e as probabilidades para um jogo específico.
    """
    dados_jogo = {}
    
    # Preencher as features com base nas estatísticas dos times
    for time, lado in [(time_casa, 'Home'), (time_visitante, 'Away')]:
        if time not in time_stats:
            print(f"Atenção: Não há dados históricos suficientes para '{time}'. Usando valores padrão.")
            dados_jogo[f'ForcaGeral_{lado}'] = 1.0 
            dados_jogo[f'FormaPontos_{lado}'] = 0
            dados_jogo[f'MediaGolsMarcados_{lado}'] = 0
            dados_jogo[f'MediaGolsSofridos_{lado}'] = 0
        else:
            # Evitar divisão por zero ou listas vazias
            dados_jogo[f'ForcaGeral_{lado}'] = np.mean(time_stats[time]['pontos']) if time_stats[time]['pontos'] else 1.0
            dados_jogo[f'FormaPontos_{lado}'] = sum(time_stats[time]['pontos'][-5:])
            dados_jogo[f'MediaGolsMarcados_{lado}'] = np.mean(time_stats[time]['gm'][-5:]) if time_stats[time]['gm'] else 0
            dados_jogo[f'MediaGolsSofridos_{lado}'] = np.mean(time_stats[time]['gs'][-5:]) if time_stats[time]['gs'] else 0

    # Criar o DataFrame para o jogo
    df_jogo_features_num = pd.DataFrame([dados_jogo])
    
    df_jogo_times = pd.DataFrame([{'HomeTeam': time_casa, 'AwayTeam': time_visitante}])
    df_jogo_encoded_teams = encoder.transform(df_jogo_times[['HomeTeam', 'AwayTeam']])
    df_jogo_encoded_df = pd.DataFrame(df_jogo_encoded_teams,
                                      columns=encoder.get_feature_names_out(['HomeTeam', 'AwayTeam']))
    
    # Combinar features numéricas e categóricas
    df_jogo_final = pd.concat([df_jogo_encoded_df, df_jogo_features_num], axis=1)

    df_jogo_final = df_jogo_final.reindex(columns=colunas_modelo, fill_value=0)

    probabilidades = modelo.predict_proba(df_jogo_final)[0]
    classes = modelo.classes_

    odds = {classe: prob for classe, prob in zip(classes, probabilidades)}
    return odds

def simular_campeonato(rodada_final, df_jogos_futuros, df_resultados_atuais, modelo, encoder, time_stats, colunas_modelo):
    """
    Simula o campeonato até uma rodada específica.
    """
    df_resultados_atuais['Resultado'] = np.where(
        df_resultados_atuais['FTHG'] > df_resultados_atuais['FTAG'], 'Casa',
        np.where(df_resultados_atuais['FTHG'] < df_resultados_atuais['FTAG'], 'Visitante', 'Empate')
    )
    
    tabela = {}
    times_atuais = set(df_resultados_atuais['HomeTeam']).union(set(df_resultados_atuais['AwayTeam']))
    times_futuros = set(df_jogos_futuros['HomeTeam']).union(set(df_jogos_futuros['AwayTeam']))
    todos_times = sorted(list(times_atuais.union(times_futuros)))

    for time in todos_times:
        tabela[time] = {'P': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0}

    # Popula a tabela com os resultados atuais
    for _, row in df_resultados_atuais.iterrows():
        casa, visitante, gp_casa, gp_visitante = row['HomeTeam'], row['AwayTeam'], row['FTHG'], row['FTAG']
        tabela[casa]['J'] += 1; tabela[visitante]['J'] += 1
        tabela[casa]['GP'] += gp_casa; tabela[casa]['GC'] += gp_visitante
        tabela[visitante]['GP'] += gp_visitante; tabela[visitante]['GC'] += gp_casa
        if row['Resultado'] == 'Casa':
            tabela[casa]['P'] += 3; tabela[casa]['V'] += 1; tabela[visitante]['D'] += 1
        elif row['Resultado'] == 'Visitante':
            tabela[visitante]['P'] += 3; tabela[visitante]['V'] += 1; tabela[casa]['D'] += 1
        else:
            tabela[casa]['P'] += 1; tabela[casa]['E'] += 1; tabela[visitante]['P'] += 1; tabela[visitante]['E'] += 1

    # Simula os jogos futuros
    jogos_a_simular = df_jogos_futuros[pd.to_numeric(df_jogos_futuros['Rodada']) <= rodada_final]
    for _, jogo in jogos_a_simular.iterrows():
        casa, visitante = jogo['HomeTeam'], jogo['AwayTeam']
        odds = prever_jogo_especifico(casa, visitante, modelo, encoder, time_stats, colunas_modelo)
        if not odds: continue
        resultado_previsto = max(odds, key=lambda k: odds[k])
        tabela[casa]['J'] += 1; tabela[visitante]['J'] += 1
        if resultado_previsto == 'Casa':
            tabela[casa]['P'] += 3; tabela[casa]['V'] += 1; tabela[visitante]['D'] += 1
        elif resultado_previsto == 'Visitante':
            tabela[visitante]['P'] += 3; tabela[visitante]['V'] += 1; tabela[casa]['D'] += 1
        else:
            tabela[casa]['P'] += 1; tabela[casa]['E'] += 1; tabela[visitante]['P'] += 1; tabela[visitante]['E'] += 1

    df_tabela = pd.DataFrame.from_dict(tabela, orient='index')
    df_tabela['SG'] = df_tabela['GP'] - df_tabela['GC']
    df_tabela = df_tabela.sort_values(by=['P', 'V', 'SG'], ascending=False)

    # Transforma o índice (que tem os nomes dos times) em uma coluna regular
    df_tabela = df_tabela.reset_index()
    df_tabela = df_tabela.rename(columns={'index': 'Time'})

    # Insere a coluna de posição '#' na primeira posição 
    df_tabela.insert(0, '#', np.arange(1, len(df_tabela) + 1))

    return df_tabela