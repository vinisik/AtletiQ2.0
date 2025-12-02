import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder

def treinar_modelo(df_treino):
    """
    Treina três modelos distintos (Resultado, Over 2.5, BTTS) e retorna
    os modelos, o encoder e a lista de colunas finais para garantir a ordem na previsão.
    """
    print("Treinando modelos de previsão...")
    
    # Features base (numéricas) que já vêm do feature_engineering
    cols_base = [
        'ForcaGeral_Home', 'ForcaGeral_Away', 
        'FormaPontos_Home', 'FormaPontos_Away', 
        'MediaGolsMarcados_Home', 'MediaGolsMarcados_Away',
        'MediaGolsSofridos_Home', 'MediaGolsSofridos_Away'
    ]
    
    # Verifica se todas as colunas base existem no DataFrame
    # (Segurança caso o feature_engineering mude no futuro)
    cols_existentes = [c for c in cols_base if c in df_treino.columns]
    
    # Separação das variáveis preditoras (X)
    # Começamos apenas com os times para o OneHotEncoder
    X_times = df_treino[['HomeTeam', 'AwayTeam']]
    
    # One-Hot Encoding para os nomes dos times
    # handle_unknown='ignore' é importante para não quebrar se aparecer um time novo no futuro
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    # Cria o DataFrame com as colunas dos times (ex: HomeTeam_Flamengo, AwayTeam_Palmeiras...)
    X_enc = pd.DataFrame(
        encoder.fit_transform(X_times), 
        columns=encoder.get_feature_names_out(['HomeTeam', 'AwayTeam'])
    )
    
    # Junta as features numéricas (Força, Forma, Gols) com as codificadas (Times)
    # reset_index(drop=True) é vital para alinhar os índices na concatenação
    X_final = pd.concat([X_enc, df_treino[cols_existentes].reset_index(drop=True)], axis=1)
    
    modelos = {}
    
    # Lista de alvos para treinar
    # Tuplas: (Nome da coluna no DataFrame, Chave para guardar no dicionário de modelos)
    alvos = [
        ('Resultado', 'resultado'), 
        ('Target_Over25', 'over25'), 
        ('Target_BTTS', 'btts')
    ]

    for col_alvo, key_modelo in alvos:
        if col_alvo in df_treino.columns:
            # Configuração do modelo Logístico
            # solver='lbfgs' é eficiente para datasets pequenos/médios
            # max_iter=2000 garante convergência
            m = LogisticRegression(solver='lbfgs', max_iter=2000)
            
            # Treina o modelo
            m.fit(X_final, df_treino[col_alvo])
            
            # Salva no dicionário
            modelos[key_modelo] = m

    # Retorna:
    # 1. Dicionário com os 3 modelos treinados
    # 2. O encoder usado para transformar os nomes dos times (precisaremos dele na previsão)
    # 3. A lista de colunas finais (CRUCIAL para garantir a mesma ordem na hora de prever)
    return modelos, encoder, X_final.columns.tolist()