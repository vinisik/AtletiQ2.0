import pandas as pd
import numpy as np

def preparar_features_jogo(time_casa, time_visitante, encoder, time_stats, colunas_modelo=None):
    """
    Função auxiliar para preparar a linha de dados de um único jogo.
    """
    dados_jogo = {}
    for time, lado in [(time_casa, 'Home'), (time_visitante, 'Away')]:
        if time not in time_stats:
            dados_jogo[f'ForcaGeral_{lado}'] = 1.0
            dados_jogo[f'FormaPontos_{lado}'] = 0
            dados_jogo[f'MediaGolsMarcados_{lado}'] = 0
            dados_jogo[f'MediaGolsSofridos_{lado}'] = 0
        else:
            dados_jogo[f'ForcaGeral_{lado}'] = np.mean(time_stats[time]['pontos']) if time_stats[time]['pontos'] else 1.0
            dados_jogo[f'FormaPontos_{lado}'] = sum(time_stats[time]['pontos'][-5:])
            dados_jogo[f'MediaGolsMarcados_{lado}'] = np.mean(time_stats[time]['gm'][-5:]) if time_stats[time]['gm'] else 0
            dados_jogo[f'MediaGolsSofridos_{lado}'] = np.mean(time_stats[time]['gs'][-5:]) if time_stats[time]['gs'] else 0

    df_jogo = pd.DataFrame([{'HomeTeam': time_casa, 'AwayTeam': time_visitante}])
    try:
        df_jogo_encoded = pd.DataFrame(
            encoder.transform(df_jogo[['HomeTeam', 'AwayTeam']]), 
            columns=encoder.get_feature_names_out(['HomeTeam', 'AwayTeam'])
        )
    except:
        df_jogo_encoded = pd.DataFrame()

    df_features_num = pd.DataFrame([dados_jogo])
    X_input = pd.concat([df_jogo_encoded, df_features_num], axis=1)
    
    if colunas_modelo is not None:
        for col in colunas_modelo:
            if col not in X_input.columns:
                X_input[col] = 0
        X_input = X_input[colunas_modelo]
        
    return X_input

def prever_jogo_especifico(time_casa, time_visitante, modelos, encoder, time_stats, colunas_modelo):
    """
    Prevê Resultado, Over 2.5 e BTTS para um jogo específico.
    """
    X_input = preparar_features_jogo(time_casa, time_visitante, encoder, time_stats, colunas_modelo)
    
    if X_input is None or X_input.empty:
        return {}
    
    odds = {}

    if 'resultado' in modelos:
        try:
            probs_res = modelos['resultado'].predict_proba(X_input)[0]
            classes_res = modelos['resultado'].classes_
            odds = {classe: prob for classe, prob in zip(classes_res, probs_res)}
        except Exception as e:
            print(f"Erro na previsão de resultado: {e}")
    
    if 'over25' in modelos:
        try:
            prob_over = modelos['over25'].predict_proba(X_input)[0][1] 
            odds['Over25'] = prob_over
        except:
            odds['Over25'] = 0.0
    
    if 'btts' in modelos:
        try:
            prob_btts = modelos['btts'].predict_proba(X_input)[0][1]
            odds['BTTS'] = prob_btts
        except:
            odds['BTTS'] = 0.0
    
    return odds

def simular_campeonato(rodada_final, df_jogos_futuros, df_resultados_atuais, modelos, encoder, time_stats, colunas_modelo):
    """
    Simula o restante do campeonato e retorna a tabela com a posição junto ao nome do time.
    """
    tabela = {}
    todos_times = set(df_resultados_atuais['HomeTeam']).union(set(df_resultados_atuais['AwayTeam']))
    
    for time in todos_times:
        tabela[time] = {'P': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0}

    # 1. Computa a tabela atual
    for _, row in df_resultados_atuais.iterrows():
        casa, visitante = row['HomeTeam'], row['AwayTeam']
        gp_casa, gp_visitante = row['FTHG'], row['FTAG']
        
        if casa in tabela and visitante in tabela:
            tabela[casa]['J'] += 1; tabela[visitante]['J'] += 1
            tabela[casa]['GP'] += gp_casa; tabela[casa]['GC'] += gp_visitante
            tabela[visitante]['GP'] += gp_visitante; tabela[visitante]['GC'] += gp_casa
            
            if gp_casa > gp_visitante:
                tabela[casa]['P'] += 3; tabela[casa]['V'] += 1; tabela[visitante]['D'] += 1
            elif gp_visitante > gp_casa:
                tabela[visitante]['P'] += 3; tabela[visitante]['V'] += 1; tabela[casa]['D'] += 1
            else:
                tabela[casa]['P'] += 1; tabela[casa]['E'] += 1; tabela[visitante]['P'] += 1; tabela[visitante]['E'] += 1

    # 2. Simula jogos futuros
    jogos_a_simular = df_jogos_futuros[pd.to_numeric(df_jogos_futuros['Rodada']) <= rodada_final]
    
    for _, jogo in jogos_a_simular.iterrows():
        casa, visitante = jogo['HomeTeam'], jogo['AwayTeam']
        if casa not in tabela or visitante not in tabela: continue

        X_input = preparar_features_jogo(casa, visitante, encoder, time_stats, colunas_modelo)
        
        if X_input is not None and not X_input.empty:
            try:
                resultado_previsto = modelos['resultado'].predict(X_input)[0]
                tabela[casa]['J'] += 1; tabela[visitante]['J'] += 1
                
                if resultado_previsto == 'Casa':
                    tabela[casa]['P'] += 3; tabela[casa]['V'] += 1; tabela[visitante]['D'] += 1
                elif resultado_previsto == 'Visitante':
                    tabela[visitante]['P'] += 3; tabela[visitante]['V'] += 1; tabela[casa]['D'] += 1
                else:
                    tabela[casa]['P'] += 1; tabela[casa]['E'] += 1; tabela[visitante]['P'] += 1; tabela[visitante]['E'] += 1
            except Exception:
                continue

    # 3. Formata para DataFrame
    df_tabela = pd.DataFrame.from_dict(tabela, orient='index')
    df_tabela.index.name = 'Time'
    df_tabela.reset_index(inplace=True)
    
    if not df_tabela.empty:
        df_tabela['SG'] = df_tabela['GP'] - df_tabela['GC']
        df_tabela = df_tabela.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        # Adiciona a posição do time ao lado do nome
        df_tabela['Time'] = (df_tabela.index + 1).astype(str) + "   " + df_tabela['Time']
    
    cols = ['Time', 'P', 'J', 'V', 'E', 'D', 'GP', 'GC', 'SG']
    return df_tabela[cols] if not df_tabela.empty else pd.DataFrame(columns=cols)