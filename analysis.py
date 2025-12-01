import pandas as pd
import numpy as np

def carregar_historico():
    """
    Carrega a base de dados histórica de confrontos a partir de um arquivo CSV.
    """
    try:
        return pd.read_csv("historico_confrontos.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=['Time1', 'Time2', 'Vitorias_Time1', 'Vitorias_Time2', 'Empates'])

def gerar_confronto_direto(df_total, time_A_selecionado, time_B_selecionado):
    """
    Filtra o histórico de jogos recentes, SOMA com uma base de dados histórica,
    e calcula as estatísticas totais do confronto.
    """
    # Garantir ordem alfabética para consistência
    time1_alfa, time2_alfa = sorted([time_A_selecionado, time_B_selecionado])
    df_historico_total = carregar_historico()
    historico_base = df_historico_total[
        (df_historico_total['Time1'] == time1_alfa) & (df_historico_total['Time2'] == time2_alfa)
    ]
    stats_base = {time1_alfa: {'vitorias': 0}, time2_alfa: {'vitorias': 0}, 'empates': 0}
    if not historico_base.empty:
        stats_base[time1_alfa]['vitorias'] = int(historico_base.iloc[0]['Vitorias_Time1'])
        stats_base[time2_alfa]['vitorias'] = int(historico_base.iloc[0]['Vitorias_Time2'])
        stats_base['empates'] = int(historico_base.iloc[0]['Empates'])
    historico_recente = df_total[
        ((df_total['HomeTeam'] == time_A_selecionado) & (df_total['AwayTeam'] == time_B_selecionado)) |
        ((df_total['HomeTeam'] == time_B_selecionado) & (df_total['AwayTeam'] == time_A_selecionado))
    ].copy()
    stats_recentes = {time_A_selecionado: {'vitorias': 0, 'gols': 0}, time_B_selecionado: {'vitorias': 0, 'gols': 0}, 'empates': 0}
    if not historico_recente.empty:
        historico_recente['Resultado'] = np.where(
            historico_recente['FTHG'] > historico_recente['FTAG'], 'Casa',
            np.where(historico_recente['FTHG'] < historico_recente['FTAG'], 'Visitante', 'Empate')
        )
        # Calcula vitórias, empates e gols recentes
        stats_recentes[time_A_selecionado]['vitorias'] = len(historico_recente[((historico_recente['HomeTeam'] == time_A_selecionado) & (historico_recente['Resultado'] == 'Casa')) | ((historico_recente['AwayTeam'] == time_A_selecionado) & (historico_recente['Resultado'] == 'Visitante'))])
        stats_recentes[time_B_selecionado]['vitorias'] = len(historico_recente[((historico_recente['HomeTeam'] == time_B_selecionado) & (historico_recente['Resultado'] == 'Casa')) | ((historico_recente['AwayTeam'] == time_B_selecionado) & (historico_recente['Resultado'] == 'Visitante'))])
        stats_recentes['empates'] = len(historico_recente[historico_recente['Resultado'] == 'Empate'])
        stats_recentes[time_A_selecionado]['gols'] = int(historico_recente.loc[historico_recente['HomeTeam'] == time_A_selecionado, 'FTHG'].sum() + historico_recente.loc[historico_recente['AwayTeam'] == time_A_selecionado, 'FTAG'].sum())
        stats_recentes[time_B_selecionado]['gols'] = int(historico_recente.loc[historico_recente['HomeTeam'] == time_B_selecionado, 'FTHG'].sum() + historico_recente.loc[historico_recente['AwayTeam'] == time_B_selecionado, 'FTAG'].sum())

    # Soma os resultados históricos com os recentes
    vitorias_total_A = stats_base.get(time_A_selecionado, {}).get('vitorias', 0) + stats_recentes[time_A_selecionado]['vitorias']
    vitorias_total_B = stats_base.get(time_B_selecionado, {}).get('vitorias', 0) + stats_recentes[time_B_selecionado]['vitorias']
    empates_total = stats_base['empates'] + stats_recentes['empates']

    resumo_final = {
        'vitorias': {
            time_A_selecionado: vitorias_total_A,
            time_B_selecionado: vitorias_total_B
        },
        'empates': empates_total,
        'gols': {
            time_A_selecionado: stats_recentes[time_A_selecionado]['gols'],
            time_B_selecionado: stats_recentes[time_B_selecionado]['gols']
        },
        # Adiciona a chave com o total de jogos
        'total_partidas': vitorias_total_A + vitorias_total_B + empates_total
    }

    # Prepara o DataFrame de exibição (2025)
    historico_exibicao = historico_recente[['Date', 'HomeTeam', 'FTHG', 'FTAG', 'AwayTeam']].copy()
    historico_exibicao.rename(columns={'Date': 'Data', 'HomeTeam': 'Mandante', 'FTHG': 'Gols Mandante', 'FTAG': 'Gols Visitante', 'AwayTeam': 'Visitante'}, inplace=True)
    historico_exibicao = historico_exibicao.sort_values(by='Data', ascending=False)

    return resumo_final, historico_exibicao