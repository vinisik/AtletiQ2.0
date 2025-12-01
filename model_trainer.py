import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder


def treinar_modelo(df_treino):
    """
    Treinando o modelo de regressão logística.
    """
    print("Treinando o modelo de previsão...")
    features_cols = [
        'HomeTeam', 'AwayTeam', 'ForcaGeral_Home', 'ForcaGeral_Away',
        'FormaPontos_Home', 'FormaPontos_Away', 'MediaGolsMarcados_Home', 'MediaGolsMarcados_Away',
        'MediaGolsSofridos_Home', 'MediaGolsSofridos_Away'
    ]

    # Garante que não há valores nulos nas features numéricas
    numeric_features = [col for col in features_cols if col not in ['HomeTeam', 'AwayTeam']]
    df_treino[numeric_features] = df_treino[numeric_features].fillna(0)


    X = df_treino[features_cols]
    y = df_treino['Resultado']

    # Separar colunas categóricas e numéricas
    X_categorico = X[['HomeTeam', 'AwayTeam']]
    X_numerico = X.drop(['HomeTeam', 'AwayTeam'], axis=1)

    # Aplicar OneHotEncoder nas colunas categóricas
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_encoded_teams = encoder.fit_transform(X_categorico)
    
    # Criar DataFrame com os nomes das colunas encodadas
    encoded_cols = encoder.get_feature_names_out(['HomeTeam', 'AwayTeam'])
    X_encoded_df = pd.DataFrame(X_encoded_teams, columns=encoded_cols, index=X.index)

    # Juntar as features encodadas com as numéricas
    X_final = pd.concat([X_encoded_df, X_numerico], axis=1)

    # Obter a lista de colunas do modelo treinado
    colunas_modelo = X_final.columns.tolist()

    modelo = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=2000)
    modelo.fit(X_final, y)

    print("Modelo treinado com sucesso.")
    
    return modelo, encoder, colunas_modelo