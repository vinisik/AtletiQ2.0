import flet as ft
import pandas as pd
import numpy as np 
from datetime import datetime, timedelta
import time

try:
    from web_scraper import AtletiQScraper
    from feature_engineering import preparar_dados_para_modelo, gerar_dados_evolucao
    from model_trainer import treinar_modelo
    from predictor import prever_jogo_especifico, simular_campeonato
    from analysis import gerar_confronto_direto
except ImportError as e:
    print(f"Erro crítico de importação: {e}")
    raise e

# CONFIGURAÇÕES VISUAIS
COR_ACCENT = "#00E676"  
COR_BG = "#121212"      
COR_SURFACE = "#1E1E1E" 
COR_TEXT_SEC = "#9E9E9E"
COR_BORDER = "#333333"

CORES_TIMES = {
    'Flamengo': '#C3281E', 'Palmeiras': '#006437', 'São Paulo': '#FE0000', 
    'Corinthians': '#FFFFFF', 'Vasco': '#FFFFFF', 'Fluminense': '#9F022F',
    'Botafogo': '#F4F4F4', 'Grêmio': '#0D80BF', 'Internacional': '#E30613',
    'Atlético Mineiro': '#FFFFFF', 'Cruzeiro': '#005CA9', 'Bahia': '#005CA9',
    'Fortaleza': '#11519B', 'Ceará': '#FFFFFF', 'Vitória': '#E30613',
    'Athletico Paranaense': '#C3281E', 'Coritiba': '#00522D', 'Goiás': '#006633',
    'Cuiabá': '#018036', 'Bragantino': '#FFFFFF', 'Juventude': '#006633'
}

def criar_card(content, padding=20, on_click=None):
    return ft.Container(
        content=content, bgcolor=COR_SURFACE, border_radius=15, padding=padding,
        border=ft.border.all(1, COR_BORDER), on_click=on_click,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#4D000000", offset=ft.Offset(0, 4))
    )

def criar_stat_box(label, value, color="white"):
    return ft.Container(
        content=ft.Column([
            ft.Text(label, size=11, color=COR_TEXT_SEC, weight="w500"), 
            ft.Text(str(value), size=22, weight="bold", color=color)
        ], horizontal_alignment="center", spacing=2), 
        bgcolor="#0DFFFFFF", border_radius=10, padding=10, expand=True, alignment=ft.alignment.center
    )

def criar_tabela_estilizada(df: pd.DataFrame):
    if df is None or df.empty: return ft.Text("Sem registros encontrados.", color=COR_TEXT_SEC)
    columns = [ft.DataColumn(ft.Text(str(col), weight="bold", color=COR_ACCENT)) for col in df.columns]
    rows = [ft.DataRow([ft.DataCell(ft.Text(str(val), size=11)) for val in row]) for i, row in df.iterrows()]
    return ft.DataTable(columns=columns, rows=rows, heading_row_color="#1AFFFFFF", width=float('inf'), column_spacing=15)

def main(page: ft.Page):
    page.title = "AtletiQ 2.1"
    page.theme_mode = "dark" 
    page.padding = 0 
    page.bgcolor = COR_BG

    # SPLASH SCREEN
    loading_text = ft.Text("Carregando inteligência...", color=COR_TEXT_SEC, size=12)
    loading_bar = ft.ProgressBar(width=200, color=COR_ACCENT, bgcolor="#333333")
    page.add(ft.Container(content=ft.Column([ft.Icon(name="sports_soccer", size=80, color=COR_ACCENT), ft.Text("AtletiQ", size=40, weight="bold"), loading_bar, loading_text], alignment="center", horizontal_alignment="center"), expand=True, bgcolor=COR_BG))
    page.update()

    # DADOS
    ano_atual = datetime.now().year
    scraper = AtletiQScraper() 
    df_temp_atual = scraper.buscar_dados_hibrido(str(ano_atual))
    df_temp_ant = scraper.buscar_dados_hibrido(str(ano_atual - 1))
    df_artilharia = scraper.fetch_scorers(str(ano_atual))

    valid_dfs = [df for df in [df_temp_ant, df_temp_atual] if df is not None and not df.empty]
    if not valid_dfs:
        loading_text.value = "Erro: API indisponível."; page.update(); return

    df_total = pd.concat(valid_dfs).drop_duplicates().reset_index(drop=True)
    df_total['Date'] = pd.to_datetime(df_total['Date']).dt.tz_localize(None) - timedelta(hours=3)
    
    df_res = df_total[df_total['FTHG'].notna()].copy()
    df_fut = df_total[df_total['FTHG'].isna()].copy()
    df_treino, time_stats = preparar_dados_para_modelo(df_res)
    modelos, encoder, cols_model = treinar_modelo(df_treino) if not df_treino.empty else (None, None, None)
    
    times_list = sorted(list(set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))))
    opts = [ft.dropdown.Option(t) for t in times_list]
    page.clean()

    # MODAL DE DETALHES 
    def abrir_detalhes(row):
        mandante, visitante = row['HomeTeam'], row['AwayTeam']
        odds = prever_jogo_especifico(mandante, visitante, modelos, encoder, time_stats, cols_model)
        res_h2h, df_h2h = gerar_confronto_direto(df_total, mandante, visitante)

        def fechar(e): 
            modal.open = False
            page.update()

        modal = ft.BottomSheet(
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("Análise da Partida", size=18, weight="bold"), ft.IconButton(ft.Icons.CLOSE, on_click=fechar)], alignment="spaceBetween"),
                    ft.Divider(color=COR_BORDER),
                    ft.Row([
                        ft.Text(mandante, weight="bold", size=15, expand=True, text_align="right"),
                        ft.Container(ft.Text("VS", size=10, weight="bold", color="black"), bgcolor=COR_ACCENT, padding=5, border_radius=5),
                        ft.Text(visitante, weight="bold", size=15, expand=True, text_align="left")
                    ]),
                    ft.Text("Probabilidades AtletiQ", size=14, color=COR_ACCENT, weight="bold"),
                    ft.Row([
                        criar_stat_box(mandante, f"{odds.get('Casa',0):.0%}", CORES_TIMES.get(mandante, COR_ACCENT)),
                        criar_stat_box("Empate", f"{odds.get('Empate',0):.0%}", "grey"),
                        criar_stat_box(visitante, f"{odds.get('Visitante',0):.0%}", CORES_TIMES.get(visitante, "#00B0FF"))
                    ]),
                    ft.Text("Histórico Recente (H2H)", size=14, color=COR_ACCENT, weight="bold"),
                    ft.Row([
                        criar_stat_box("Vitórias " + mandante, res_h2h['vitorias'].get(mandante, 0)),
                        criar_stat_box("Empates", res_h2h['empates']),
                        criar_stat_box("Vitórias " + visitante, res_h2h['vitorias'].get(visitante, 0)),
                    ]),
                    ft.Text("Últimos Jogos:", size=11, color=COR_TEXT_SEC),
                    ft.Container(content=criar_tabela_estilizada(df_h2h), padding=5, bgcolor="#0AFFFFFF", border_radius=10),
                ], scroll=ft.ScrollMode.AUTO, spacing=15),
                padding=20, bgcolor=COR_SURFACE, border_radius=ft.border_radius.only(top_left=20, top_right=20)
            ),
            is_scroll_controlled=True
        )
        page.overlay.append(modal); modal.open = True; page.update()

    # ABA JOGOS
    def criar_card_jogo(row):
        return criar_card(
            ft.Row([
                ft.Column([
                    ft.Text(row['Date'].strftime("%d/%m - %H:%M"), size=11, color=COR_TEXT_SEC), 
                    ft.Row([
                        ft.Text(row['HomeTeam'], weight="bold", size=13, expand=True, text_align="right"), 
                        ft.Container(ft.Text("vs", size=10, color="black", weight="bold"), bgcolor=COR_ACCENT, padding=4, border_radius=4), 
                        ft.Text(row['AwayTeam'], weight="bold", size=13, expand=True, text_align="left")
                    ], alignment="center", spacing=10)
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=COR_TEXT_SEC)
            ], alignment="center"), 
            padding=12, on_click=lambda _: abrir_detalhes(row)
        )

    conteudo_jogos = []
    if not df_fut.empty:
        df_fut_disp = df_fut.copy()
        df_fut_disp['Rodada_Num'] = pd.to_numeric(df_fut_disp['Rodada'], errors='coerce')
        for r in sorted(df_fut_disp['Rodada_Num'].dropna().unique()):
            jogos_r = df_fut_disp[df_fut_disp['Rodada_Num'] == r]
            conteudo_jogos.append(ft.Text(f"Rodada {int(r)}", size=16, weight="bold", color=COR_ACCENT))
            grid = ft.ResponsiveRow(spacing=10, run_spacing=10)
            for _, row in jogos_r.iterrows(): grid.controls.append(ft.Container(content=criar_card_jogo(row), col={"xs": 12, "sm": 6}))
            conteudo_jogos.append(grid)
    
    tab_jogos = ft.Container(content=ft.Column([ft.Text("Calendário", size=22, weight="bold"), ft.Divider(color=COR_BORDER), ft.Column(conteudo_jogos, scroll=ft.ScrollMode.AUTO, expand=True)], expand=True), padding=20)

    # ABA JOGADORES
    dd_time_jog = ft.Dropdown(label="Time", options=opts, expand=True)
    area_jogadores = ft.Column()
    def buscar_jogadores(e):
        if not dd_time_jog.value: return
        df_f = df_artilharia[df_artilharia['Time'].str.contains(dd_time_jog.value, case=False, na=False)].copy()
        area_jogadores.controls = [ft.Text(f"Artilharia: {dd_time_jog.value}", size=18, weight="bold"), criar_tabela_estilizada(df_f.drop(columns=['Time']))]
        page.update()
    tab_jogadores = ft.Container(content=ft.Column([criar_card(ft.Row([dd_time_jog, ft.IconButton("search", on_click=buscar_jogadores)])), area_jogadores], scroll=ft.ScrollMode.AUTO), padding=20)

    # ABA SIMULAÇÃO 
    tabela_sim_cont = ft.Column(scroll=ft.ScrollMode.AUTO)
    def rodar_sim(e):
        btn_sim.content = ft.ProgressRing(width=20, color="black"); page.update()
        df_res_sim = df_temp_atual[df_temp_atual['FTHG'].notna()].copy()
        df_fut_sim = df_temp_atual[df_temp_atual['FTHG'].isna()].copy()
        df_simulado = simular_campeonato(38, df_fut_sim, df_res_sim, modelos, encoder, time_stats, cols_model)
        tabela_sim_cont.controls = [criar_tabela_estilizada(df_simulado)]
        btn_sim.content = ft.Text("RODAR SIMULAÇÃO 38 RODADAS"); page.update()
    
    btn_sim = ft.ElevatedButton("RODAR SIMULAÇÃO 38 RODADAS", bgcolor=COR_ACCENT, color="black", on_click=rodar_sim, width=float('inf'), height=50)
    tab_sim = ft.Container(content=ft.Column([criar_card(ft.Column([ft.Text("Simular Tabela Final", size=18, weight="bold"), btn_sim])), tabela_sim_cont], scroll=ft.ScrollMode.AUTO), padding=20)

    # UI FINAL
    header = ft.Container(content=ft.Row([ft.Row([ft.Icon("sports_soccer", color=COR_ACCENT), ft.Text("AtletiQ 2.1", size=20, weight="bold")]), ft.IconButton("settings")], alignment="spaceBetween"), padding=15, border=ft.border.only(bottom=ft.border.BorderSide(1, COR_BORDER)))
    tabs = ft.Tabs(selected_index=0, indicator_color=COR_ACCENT, tabs=[ft.Tab(text="Jogos", icon="calendar_today", content=tab_jogos), ft.Tab(text="Jogadores", icon="person", content=tab_jogadores), ft.Tab(text="Tabela", icon="table_chart", content=tab_sim)], expand=True)
    page.add(header, tabs)

if __name__ == "__main__":
    ft.app(target=main)