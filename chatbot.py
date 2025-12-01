import pandas as pd
import time
from datetime import datetime
from web_scraper import buscar_dados_brasileirao
from feature_engineering import preparar_dados_para_modelo
from model_trainer import treinar_modelo
from predictor import prever_jogo_especifico, simular_campeonato


def main():
    """
    Função principal que executa o chatbot.
    """
    print("Bem-vindo ao Chatbot de Previsão de Futebol!")

    ano_atual = datetime.now().year
    ano_anterior = ano_atual - 1

    df_anterior = buscar_dados_brasileirao(str(ano_anterior))
    time.sleep(1)
    df_atual = buscar_dados_brasileirao(str(ano_atual))

    if df_anterior is None or df_atual is None:
        print("Não foi possível obter os dados necessários. Encerrando.")
        return

    df_total = pd.concat([df_anterior, df_atual], ignore_index=True)

    df_resultados = df_total[df_total['FTHG'].notna()].copy()
    df_futuro = df_total[df_total['FTHG'].isna()].copy()

    df_treino, time_stats = preparar_dados_para_modelo(df_resultados)

    if df_treino.empty:
        print("Não há dados de treino suficientes após o pré-processamento. Encerrando.")
        return

    modelo, encoder, colunas_modelo = treinar_modelo(df_treino)

    lista_times = sorted(list(set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))))

    # Essa parte não será acessada caso use o Streamlit ------------------------
    while True:
        print("\n" + "=" * 50)
        print("O que você gostaria de fazer?")
        print("1. Prever o resultado de um jogo específico")
        print("2. Simular a classificação do campeonato até uma rodada")
        print("3. Sair")

        escolha = input("Digite o número da sua escolha: ")

        if escolha == '1':
            print("\nTimes disponíveis:")
            print(", ".join(lista_times))
            time_casa = input("Digite o nome EXATO do time da casa: ")
            time_visitante = input("Digite o nome EXATO do time visitante: ")

            if time_casa not in lista_times or time_visitante not in lista_times:
                print("Erro: Um ou ambos os times não foram encontrados na lista.")
                continue

            odds = prever_jogo_especifico(time_casa, time_visitante, modelo, encoder, time_stats, colunas_modelo)
            
            print("\n--- Previsão do Jogo ---")
            print(f"{time_casa} vs {time_visitante}")

            # Adicionado um check para caso a previsão falhe
            if odds:
                for resultado, prob in odds.items():
                    print(f"  - Chance de '{resultado}': {prob:.1%}")
            else:
                print("Não foi possível gerar a previsão para este jogo.")


        elif escolha == '2':
            try:
                rodada = int(input("Digite até qual rodada você quer simular a classificação (ex: 38): "))
                if rodada <= 0 or rodada > 38:
                    print("Por favor, digite um número de rodada válido (1-38).")
                    continue

                print(f"\nSimulando a classificação até a rodada {rodada}...")
                tabela_simulada = simular_campeonato(rodada, df_futuro, df_treino, modelo, encoder, time_stats, colunas_modelo)
                print("\n--- Tabela de Classificação Prevista ---")
                print(tabela_simulada)

            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")

        elif escolha == '3':
            print("Obrigado por usar o chatbot! Até a próxima.")
            break

        else:
            print("Escolha inválida. Por favor, digite 1, 2 ou 3.")


if __name__ == "__main__":
    main()