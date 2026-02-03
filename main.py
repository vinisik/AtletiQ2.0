import flet as ft
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from web_scraper import AtletiQScraper
    from feature_engineering import preparar_dados_para_modelo
    from model_trainer import treinar_modelo
    from predictor import prever_jogo_especifico, simular_campeonato
    from analysis import gerar_confronto_direto
except ImportError as e:
    print(f"Erro crítico: {e}")
    raise e

# CONFIGURAÇÕES VISUAIS
COR_ACCENT = "#00E676"
COR_BG = "#121212"
COR_SURFACE = "#1E1E1E"
COR_TEXT_SEC = "#9E9E9E"
COR_BORDER = "#333333"
COR_ENCERRADO = "#797979"
CACHE_FILE = "atletiq_dataset.csv"

CORES_TIMES = {
    'Flamengo': '#C3281E',
    'Palmeiras': '#006437',
    'São Paulo': '#FE0000',
    'Corinthians': '#FFFFFF',
    'Vasco': '#FFFFFF',
    'Fluminense': '#9F022F',
    'Botafogo': '#F4F4F4',
    'Grêmio': '#0D80BF',
    'Internacional': '#E30613',
    'Atlético Mineiro': '#FFFFFF',
    'Cruzeiro': '#005CA9',
    'Bahia': '#005CA9',
    'Fortaleza': '#11519B',
    'Ceará': '#FFFFFF',
    'Vitória': '#E30613',
    'Athletico Paranaense': '#C3281E'
}


# AUXILIARES DE UI
def criar_card(content, padding=20, on_click=None):
    return ft.Container(
        content=content,
        bgcolor=COR_SURFACE,
        border_radius=15,
        padding=padding,
        border=ft.border.all(1, COR_BORDER),
        on_click=on_click
    )


def criar_stat_box(label, value, color="white", odd=None):
    # Probabilidades em porcentagens
    content_list = [
        ft.Text(label, size=10, color=COR_TEXT_SEC),
        ft.Text(str(value), size=20, weight="bold", color=color)
    ]
    
    # Odds decimais
    if odd:
        content_list.append(
            ft.Text(f"Odd: {odd:.2f}", size=11, color=COR_TEXT_SEC, italic=True)
        )

    return ft.Container(
        content=ft.Column(
            content_list, 
            horizontal_alignment="center", 
            spacing=2
        ),
        bgcolor="#0DFFFFFF",
        border_radius=10,
        padding=10,
        expand=True
    )


def criar_legenda_tabela():
    # Cria os itens da legenda com bolinhas coloridas
    def item_legenda(cor, texto):
        return ft.Row([
            ft.Container(width=10, height=10, bgcolor=cor, border_radius=5),
            ft.Text(texto, size=12, color=COR_TEXT_SEC)
        ], spacing=5)

    return ft.Container(
        content=ft.Row([
            item_legenda(ft.Colors.BLUE, "Libertadores"),
            item_legenda(ft.Colors.GREEN, "Pré-Libertadores"),
            item_legenda(ft.Colors.YELLOW, "Sul-Americana"),
            item_legenda(ft.Colors.RED_ACCENT, "Rebaixamento"),
        ], alignment="left"),
        margin=ft.margin.only(bottom=15, top=10)
    )


def criar_tabela_estilizada(df):
    if df is None or df.empty:
        return ft.Text("Sem dados disponíveis.", color=COR_TEXT_SEC)

    # Tamanho de fonte padrão para toda a tabela
    FONTE_SIZE = 13

    cols = [
        ft.DataColumn(ft.Text(str(c), weight="bold", color=COR_ACCENT, size=FONTE_SIZE))
        for c in df.columns
    ]
    
    rows = []
    for i, row in df.iterrows():
        posicao = i + 1
        cells = []
        
        for col_name, value in row.items():
            valor_celula = str(value)
            
            if col_name == "Time" and "   " in valor_celula:
                num_pos, nome_time = valor_celula.split("   ", 1)
                
                # Definir cor do número baseada na posição 
                cor_pos = "white"
                if posicao <= 4: cor_pos = ft.Colors.BLUE
                elif posicao == 5: cor_pos = ft.Colors.GREEN
                elif 6 <= posicao <= 11: cor_pos = ft.Colors.YELLOW
                elif posicao >= 17: cor_pos = ft.Colors.RED
                
                cells.append(ft.DataCell(ft.Row([
                    ft.Text(num_pos, color=cor_pos, weight="bold", size=FONTE_SIZE),
                    ft.Text(f"   {nome_time}", color="white", size=FONTE_SIZE)
                ])))
                continue 
            
            cells.append(ft.DataCell(
                ft.Text(valor_celula, size=FONTE_SIZE, color="white", weight="bold")
            ))
            
        rows.append(ft.DataRow(cells))

    return ft.DataTable(
        columns=cols,
        rows=rows,
        heading_row_color="#1AFFFFFF",
        width=float('inf'),
        column_spacing=15
    )


def main(page: ft.Page):
    page.title = "AtletiQ 2.5"
    page.theme_mode = "dark"
    page.bgcolor = COR_BG
    page.padding = 0

    # SPLASH SCREEN
    txt_load = ft.Text("Iniciando AtletiQ 2.5...", color=COR_TEXT_SEC)
    pb = ft.ProgressBar(width=300, color=COR_ACCENT)
    splash_content = ft.Column([
        ft.Icon("sports_soccer", size=80, color=COR_ACCENT),
        ft.Text("AtletiQ 2.5", size=40, weight="bold"),
        pb,
        txt_load
    ], alignment="center", horizontal_alignment="center")

    splash = ft.Container(content=splash_content, expand=True)
    page.add(splash)
    page.update()

    # LÓGICA DE CARREGAMENTO
    scraper = AtletiQScraper()
    ano_atual = datetime.now().year
    anos_para_processar = list(range(ano_atual - 4, ano_atual + 1))

    df_cache = pd.DataFrame()
    if os.path.exists(CACHE_FILE):
        try:
            df_cache = pd.read_csv(CACHE_FILE)
            df_cache['Date'] = pd.to_datetime(df_cache['Date'], utc=True)
        except Exception:
            df_cache = pd.DataFrame()

    dfs_finais = []
    for ano in anos_para_processar:
        txt_load.value = f"Sincronizando Temporada {ano}..."
        page.update()

        if not df_cache.empty and ano < ano_atual:
            dados_ano = df_cache[df_cache['Date'].dt.year == ano]
            if len(dados_ano) > 50:
                dfs_finais.append(dados_ano)
                continue

        try:
            df_download = scraper.buscar_dados_hibrido(str(ano))
            if df_download is not None and not df_download.empty:
                df_download['Date'] = pd.to_datetime(
                    df_download['Date'], utc=True
                )
                dfs_finais.append(df_download)
        except Exception:
            continue

    if not dfs_finais:
        txt_load.value = "Erro: Sem dados (Internet ou Cache falhou)."
        page.update()
        return

    df_total = pd.concat(dfs_finais).drop_duplicates().reset_index(drop=True)
    df_total['Date'] = pd.to_datetime(df_total['Date'], utc=True)
    # Converte para o horário de Brasília (UTC-3)
    df_total['Date'] = df_total['Date'].dt.tz_convert('America/Sao_Paulo')
    df_total.to_csv(CACHE_FILE, index=False)

    df_res = df_total[df_total['FTHG'].notna()].copy()
    df_calendario = df_total[df_total['Date'].dt.year == ano_atual].copy()

    df_treino, time_stats = preparar_dados_para_modelo(df_res)
    modelos, encoder, cols_model = treinar_modelo(df_treino)
    df_artilharia_completa = scraper.fetch_scorers(str(ano_atual))

    times_list = sorted(list(
        set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))
    ))
    page.clean()

    # UI: MODAL DETALHES
    def abrir_detalhes(row):

        mandante, visitante = row['HomeTeam'], row['AwayTeam']
        ano_atual = datetime.now().year # Garante que os dados sejam do ano atual

        foi_realizado = pd.notna(row['FTHG'])
        status_text = "PARTIDA ENCERRADA" if foi_realizado else "PARTIDA AGENDADA"
        status_color = COR_ACCENT if foi_realizado else COR_TEXT_SEC
        mandante, visitante = row['HomeTeam'], row['AwayTeam']
        
        # Lógica de Placar
        foi_realizado = pd.notna(row['FTHG'])
        placar_mandante = str(int(row['FTHG'])) if foi_realizado else "-"
        placar_visitante = str(int(row['FTAG'])) if foi_realizado else "-"

        # Adicionar bolinhas com resultados dos últimos jogos 
        def obter_forma(time):
            # Filtra jogos do time no ano atual que já possuem resultado
            jogos_time = df_total[
                ((df_total['HomeTeam'] == time) | (df_total['AwayTeam'] == time)) & 
                (df_total['FTHG'].notna()) &
                (df_total['Date'].dt.year == ano_atual)
            ].sort_values(by='Date', ascending=False).head(5)
            
            icones_forma = []
            resultados = []
            
            for _, j in jogos_time.iterrows():
                if j['FTHG'] == j['FTAG']:
                    resultados.append("E")
                elif (j['HomeTeam'] == time and j['FTHG'] > j['FTAG']) or \
                    (j['AwayTeam'] == time and j['FTAG'] > j['FTHG']):
                    resultados.append("V")
                else:
                    resultados.append("D")

            resultados.reverse() 

            for i in range(5):
                if i < len(resultados):
                    res = resultados[i]
                    cor = COR_ACCENT if res == "V" else "red" if res == "D" else "grey"
                    icones_forma.append(ft.Container(width=8, height=8, bgcolor=cor, border_radius=4))
                else:
                    # Bolinhas vazias para completar as 5
                    icones_forma.append(ft.Container(width=8, height=8, border=ft.border.all(1, COR_TEXT_SEC), border_radius=4))
            
            return ft.Row(icones_forma, spacing=3, alignment="center")

        forma_mandante = obter_forma(mandante)
        forma_visitante = obter_forma(visitante)
        
        odds_ia = prever_jogo_especifico(
            mandante, visitante, modelos, encoder, time_stats, cols_model
        )

        # Probabilidades em %
        prob_casa = odds_ia.get('Casa', 0)
        prob_empate = odds_ia.get('Empate', 0)
        prob_visitante = odds_ia.get('Visitante', 0)

        # Cálculo de odds decimais
        odd_casa = 1 / prob_casa if prob_casa > 0 else 0
        odd_empate = 1 / prob_empate if prob_empate > 0 else 0
        odd_visitante = 1 / prob_visitante if prob_visitante > 0 else 0

        res_h2h, df_h2h = gerar_confronto_direto(
            df_total, mandante, visitante
        )

        def fechar(e):
            modal.open = False
            page.update()

        modal_content = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Container(
                        content=ft.Text(status_text, size=10, weight="bold", color="black"),
                        bgcolor=status_color, padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=5,
                    ),
                    ft.Text(row['Date'].strftime("%d/%m/%Y - %H:%M"), size=12, weight="bold"),
                ], spacing=5),
                ft.IconButton(ft.Icons.CLOSE, on_click=fechar)
            ], alignment="spaceBetween"),

            ft.Divider(color=COR_BORDER),
            
            # Cabeçalho com Placar
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        # ft.Text("Mandante", size=10, color=COR_TEXT_SEC, text_align="center"),
                        ft.Text(mandante, weight="bold", size=20, text_align="center"),
                        ft.Text("Últimos jogos", size=9),
                        forma_mandante, # Bolinhas dos úlimos jogos
                    ], expand=True, horizontal_alignment="center", spacing=5),
                    
                    # Área do Placar Central
                    ft.Container(
                        content=ft.Row([
                            ft.Text(placar_mandante, size=24, weight="bold"),
                            ft.Text("x", size=14, color=COR_TEXT_SEC),
                            ft.Text(placar_visitante, size=24, weight="bold"),
                        ], alignment="center", spacing=15),
                        bgcolor="#1AFFFFFF",
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        border_radius=10,
                    ),
                    
                    ft.Column([
                        # ft.Text("Visitante", size=10, color=COR_TEXT_SEC, text_align="center"),
                        ft.Text(visitante, weight="bold", size=20, text_align="center"),
                        ft.Text("Últimos jogos", size=9),
                        forma_visitante, # Bolinhas dos úlimos jogos
                    ], expand=True, horizontal_alignment="center", spacing=5),
                ], alignment="center"),
                margin=ft.margin.symmetric(vertical=10)
            ),

            ft.Text("Análise de Probabilidades (IA)", size=13, color=COR_ACCENT, weight="bold"),
            ft.Row([
                criar_stat_box(
                    "Vitória " + mandante, 
                    f"{prob_casa:.0%}",
                    CORES_TIMES.get(mandante, COR_ACCENT),
                    odd=odd_casa
                ),
                criar_stat_box(
                    "Empate", 
                    f"{prob_empate:.0%}", 
                    "grey",
                    odd=odd_empate
                ),
                criar_stat_box(
                    "Vitória " + visitante, 
                    f"{prob_visitante:.0%}", 
                    "#00B0FF",
                    odd=odd_visitante
                )
            ], spacing=10),
            
            ft.Text(
                f"Histórico Geral ({res_h2h['total_partidas']} partidas)",
                size=13, color=COR_ACCENT, weight="bold"
            ),
            ft.Row([
                criar_stat_box(
                    "Vitórias " + mandante, res_h2h['vitorias'].get(mandante, 0)
                ),
                criar_stat_box("Empates", res_h2h['empates']),
                criar_stat_box(
                    "Vitórias " + visitante,
                    res_h2h['vitorias'].get(visitante, 0)
                ),
            ], spacing=10),
            
            ft.Text("Últimos confrontos diretos:", size=11, color=COR_TEXT_SEC),
            ft.Container(
                content=criar_tabela_estilizada(df_h2h.head(5)),
                padding=5,
                bgcolor="#0DFFFFFF",
                border_radius=10
            ),
        ], scroll=ft.ScrollMode.AUTO, spacing=15)

        modal = ft.BottomSheet(
            ft.Container(
                content=modal_content,
                padding=25,
                bgcolor=COR_SURFACE,
                border_radius=ft.border_radius.only(top_left=20, top_right=20)
            ),
            is_scroll_controlled=True
        )
        page.overlay.append(modal)
        modal.open = True
        page.update()

    # ABA 1: CALENDÁRIO
    times_atuais = sorted(list(
        set(df_calendario['HomeTeam']).union(set(df_calendario['AwayTeam']))
    ))
    
    lista_jogos_container = ft.Column()

    # Filtrar o calendário por times
    def filtrar_calendario(e):
        termo = dd_filtro_jogos.value
        conteudo_filtrado = []

        if termo != "Todos os Times":
            mask = (df_calendario['HomeTeam'] == termo) | \
                   (df_calendario['AwayTeam'] == termo)
            df_f = df_calendario[mask].copy()
        else:
            df_f = df_calendario.copy()

        if df_f.empty:
            lista_jogos_container.controls = [
                ft.Text("Nenhum jogo encontrado.", color=COR_TEXT_SEC)
            ]
            page.update()
            return

        df_f['Rodada_Num'] = pd.to_numeric(df_f['Rodada'], errors='coerce')

        for r in sorted(df_f['Rodada_Num'].dropna().unique()):
            jogos_r = ft.ResponsiveRow(spacing=10)
            df_rodada = df_f[df_f['Rodada_Num'] == r]

            conteudo_filtrado.append(
                ft.Text(f"Rodada {int(r)}", size=16,
                        weight="bold", color=COR_ACCENT)
            )

            for _, row in df_rodada.iterrows():
                foi_realizado = pd.notna(row['FTHG'])
                status_txt = "ENCERRADO" if foi_realizado else "AGENDADO"
                status_bg = COR_ENCERRADO if foi_realizado else COR_TEXT_SEC

                status_label = ft.Container(
                    content=ft.Text(status_txt, size=9,
                                    weight="bold", color="black"),
                    bgcolor=status_bg,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )

                if foi_realizado:
                    info_central = ft.Row([
                        ft.Text(str(int(row['FTHG'])), size=14,
                                weight="bold", color=COR_ACCENT),
                        ft.Text("x", size=12, color=COR_TEXT_SEC),
                        ft.Text(str(int(row['FTAG'])), size=14,
                                weight="bold", color=COR_ACCENT)
                    ], spacing=10)
                else:
                    info_central = ft.Text("vs", size=10, color=COR_TEXT_SEC)

                card_content = ft.Row([
                    ft.Column([
                        ft.Row([
                            status_label,
                            ft.Text(row['Date'].strftime("%d/%m - %H:%M"),
                                    size=11, color=COR_TEXT_SEC, weight="bold")
                        ], spacing=10),
                        ft.Row([
                            ft.Text(row['HomeTeam'], size=13, weight="bold",
                                    expand=True, text_align="right"),
                            info_central,
                            ft.Text(row['AwayTeam'], size=13, weight="bold",
                                    expand=True, text_align="left")
                        ], spacing=10)
                    ], expand=True),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=COR_TEXT_SEC, size=16)
                ], alignment="center")

                card = criar_card(
                    card_content, padding=12,
                    on_click=lambda _, r=row: abrir_detalhes(r)
                )
                jogos_r.controls.append(
                    ft.Container(content=card, col={"xs": 12, "sm": 6})
                )
            conteudo_filtrado.append(jogos_r)

        lista_jogos_container.controls = conteudo_filtrado
        page.update()

    dd_filtro_jogos = ft.Dropdown(
        label="Filtrar Calendário por Time",
        options=[ft.dropdown.Option("Todos os Times")] +
                [ft.dropdown.Option(t) for t in times_atuais],
        value="Todos os Times",
        on_change=filtrar_calendario,
        expand=True
    )

    filtrar_calendario(None)

    tab_jogos = ft.Container(
        content=ft.Column([
            criar_card(ft.Row([dd_filtro_jogos, ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: setattr(dd_filtro_jogos, "value", "Todos os Times") or filtrar_calendario(None))])),
            lista_jogos_container
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )

    # ABA 2: ARTILHARIA
    opts_art = [ft.dropdown.Option("Todos")] + [
        ft.dropdown.Option(t) for t in times_list
    ]
    dd_time_art = ft.Dropdown(
        label="Filtrar por Clube", options=opts_art,
        value="Todos", expand=True
    )
    lista_artilharia = ft.Column()

    def atualizar_artilharia(e):
        if df_artilharia_completa is None:
            return
        df_f = df_artilharia_completa.copy()
        if dd_time_art.value != "Todos":
            df_f = df_f[df_f['Time'].str.contains(dd_time_art.value, na=False)]

        lista_artilharia.controls = [
            ft.Text(f"Top Marcadores - {dd_time_art.value}", size=18, weight="bold"),
            criar_tabela_estilizada(df_f)
        ]
        page.update()

    def limpar_filtro_artilharia(e):
        dd_time_art.value = "Todos"
        atualizar_artilharia(None)

    btn_filtro_art = ft.IconButton("search", on_click=atualizar_artilharia)
    btn_limpar_art = ft.IconButton(
        "refresh", on_click=limpar_filtro_artilharia, icon_color=COR_TEXT_SEC
    )

    atualizar_artilharia(None)
    row_filtros = ft.Row([dd_time_art, btn_filtro_art, btn_limpar_art], spacing=10)
    tab_artilharia = ft.Container(
        content=ft.Column([
            criar_card(row_filtros),
            lista_artilharia
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )

    # ABA 3: EVOLUÇÃO 
    dd_time_ev = ft.Dropdown(
        label="Selecione o Time para Análise",
        options=[ft.dropdown.Option(t) for t in times_list],
        expand=True
    )

    chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, COR_BORDER),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=5, color=ft.Colors.with_opacity(0.1, COR_TEXT_SEC), width=1
        ),
        vertical_grid_lines=ft.ChartGridLines(
            interval=1, color=ft.Colors.with_opacity(0.1, COR_TEXT_SEC), width=1
        ),
        left_axis=ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10))
                    for i in range(0, 120, 10)],
            title=ft.Text("Pontos Acumulados", size=12, weight="bold"),
            title_size=40
        ),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Jornadas", size=12, weight="bold"),
            title_size=40
        ),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, COR_SURFACE),
        expand=True
    )

    def gerar_grafico(e):
        if not dd_time_ev.value:
            return
        
        time_sel = dd_time_ev.value
        mask_time = (
            (df_res['HomeTeam'] == time_sel) | (df_res['AwayTeam'] == time_sel)
        ) & (df_res['Date'].dt.year == ano_atual)
        
        jogos_time = df_res[mask_time].sort_values('Date').copy()
        
        pontos_acumulados = 0
        data_points = [ft.LineChartDataPoint(0, 0)]
        
        for idx, row in enumerate(jogos_time.itertuples(), 1):
            if row.HomeTeam == time_sel:
                pts = 3 if row.FTHG > row.FTAG else (1 if row.FTHG == row.FTAG else 0)
            else:
                pts = 3 if row.FTAG > row.FTHG else (1 if row.FTAG == row.FTHG else 0)
            
            pontos_acumulados += pts
            data_points.append(ft.LineChartDataPoint(idx, pontos_acumulados))
        
        chart.data_series = [
            ft.LineChartData(
                data_points=data_points,
                stroke_width=4,
                color=COR_ACCENT,
                curved=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.1, COR_ACCENT),
                below_line_gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.Colors.with_opacity(0.2, COR_ACCENT), ft.Colors.TRANSPARENT]
                ),
                point=True
            )
        ]
        page.update()

    dd_time_ev.on_change = gerar_grafico
    tab_evolucao = ft.Container(
        content=ft.Column([
            ft.Text("Evolução de Pontos na Temporada", size=20, weight="bold"),
            criar_card(dd_time_ev),
            ft.Container(
                content=chart,
                height=400,
                padding=20,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                border_radius=15
            )
        ], scroll=ft.ScrollMode.AUTO, spacing=20),
        padding=20
    )

    # ABA 4: SIMULAÇÃO
    area_sim = ft.Column()

    def rodar(e):
        btn_s.content = ft.ProgressRing(width=20, color="black")
        page.update()
        
        df_res_at = df_total[
            (df_total['Date'].dt.year == ano_atual) & df_total['FTHG'].notna()
        ]
        df_fut_at = df_total[
            (df_total['Date'].dt.year == ano_atual) & df_total['FTHG'].isna()
        ]
        
        res = simular_campeonato(
            38, df_fut_at, df_res_at, modelos, encoder, time_stats, cols_model
        )
        
        # Atualização da área de simulação com a legenda e a nova tabela
        area_sim.controls = [
            criar_legenda_tabela(),
            criar_tabela_estilizada(res)
        ]
        
        btn_s.content = ft.Text("SIMULAR CAMPEONATO")
        page.update()

    btn_s = ft.ElevatedButton(
        "SIMULAR CAMPEONATO", bgcolor=COR_ACCENT,
        color="black", on_click=rodar, width=float('inf')
    )
    
    tab_sim = ft.Container(
        content=ft.Column([
            ft.Text(
                "Tabela simulada utilizando o modelo de IA da AtletiQ\n"
                "Os resultados são imparciais e baseados puramente em cálculos matemáticos.",
                color=COR_TEXT_SEC,
            ),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT), 
            btn_s, 
            ft.Text("Resultado da Simulação:", size=18, weight="bold"),
            area_sim
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )

    # HEADER E TABS
    header_content = ft.Row([
        ft.Row([
            ft.Icon("sports_soccer", color=COR_ACCENT),
            ft.Text("AtletiQ 2.5", size=22, weight="bold", color="white")
        ]),
        ft.Text("v2.1", size=10, color=COR_TEXT_SEC)
    ], alignment="spaceBetween")

    header = ft.Container(
        content=header_content, padding=15,
        border=ft.border.only(bottom=ft.border.BorderSide(1, COR_BORDER))
    )

    tabs = ft.Tabs(
        selected_index=0,
        indicator_color=COR_ACCENT,
        label_color=COR_ACCENT,     
        unselected_label_color=COR_TEXT_SEC,
        tabs=[
            ft.Tab(text="Jogos", icon="calendar_today", content=tab_jogos),
            ft.Tab(text="Evolução", icon="show_chart", content=tab_evolucao),
            ft.Tab(text="Artilharia", icon="local_fire_department", content=tab_artilharia),
            ft.Tab(text="Simulação", icon="table_chart", content=tab_sim)
        ],
        expand=True
    )

    page.add(header, tabs)


if __name__ == "__main__":
    ft.app(target=main)