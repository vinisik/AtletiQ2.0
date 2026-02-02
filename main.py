import flet as ft
import pandas as pd
import numpy as np 
from datetime import datetime
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

# CONFIGURAÇÕES VISUAIS & CORES
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

# COMPONENTES DE UI REUTILIZÁVEIS
def criar_card(content, padding=20, on_click=None):
    return ft.Container(
        content=content, bgcolor=COR_SURFACE, border_radius=15, padding=padding,
        border=ft.border.all(1, COR_BORDER), on_click=on_click,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#4D000000", offset=ft.Offset(0, 4)),
    )

def criar_stat_box(label, value, color="white", subtext=None):
    elements = [
        ft.Text(label, size=11, color=COR_TEXT_SEC, weight="w500"),
        ft.Text(str(value), size=22, weight="bold", color=color),
    ]
    if subtext: elements.append(ft.Text(subtext, size=10, color=COR_TEXT_SEC))
    return ft.Container(content=ft.Column(elements, horizontal_alignment="center", spacing=2), bgcolor="#0DFFFFFF", border_radius=10, padding=10, expand=True, alignment=ft.alignment.center)

def criar_bolinhas_forma(sequencia):
    if not sequencia: return ft.Row([ft.Text("-", color="grey")], alignment="center")
    ultimos_5 = sequencia[-5:]
    controles = []
    for res in ultimos_5:
        cor = "green" if res == 'V' else "red" if res == 'D' else "grey"
        controles.append(ft.Container(width=12, height=12, border_radius=6, bgcolor=cor))
    return ft.Row(controles, spacing=4, alignment="center")

def criar_tabela_estilizada(df: pd.DataFrame):
    if df is None or df.empty: return ft.Text("Sem dados.", color="red")
    columns = [ft.DataColumn(ft.Text(str(col), weight="bold", color=COR_ACCENT)) for col in df.columns]
    rows = [ft.DataRow([ft.DataCell(ft.Text(str(val), size=12)) for val in row]) for i, row in df.iterrows()]
    return ft.DataTable(
        columns=columns, 
        rows=rows, 
        heading_row_color="#1AFFFFFF", 
        width=float('inf'),
        column_spacing=15
    )

# APP PRINCIPAL
def main(page: ft.Page):
    page.title = "AtletiQ 2.1"
    page.theme_mode = "dark" 
    page.padding = 0 
    page.bgcolor = COR_BG
    page.fonts = {"Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"}

    # TELA DE CARREGAMENTO
    loading_text = ft.Text("Carregando inteligência...", color=COR_TEXT_SEC, size=12)
    loading_bar = ft.ProgressBar(width=200, color=COR_ACCENT, bgcolor="#333333")
    splash = ft.Container(content=ft.Column([ft.Icon(name="sports_soccer", size=80, color=COR_ACCENT), ft.Text("AtletiQ", size=40, weight="bold"), ft.Container(height=20), loading_bar, loading_text], alignment="center", horizontal_alignment="center"), expand=True, bgcolor=COR_BG)
    page.add(splash); page.update()

    # LÓGICA DE DADOS
    ano_atual = datetime.now().year
    scraper = AtletiQScraper() 
    
    loading_text.value = f"Sincronizando temporadas {ano_atual-1}/{ano_atual}..."
    page.update()
    
    df_temp_atual = scraper.buscar_dados_hibrido(str(ano_atual))
    df_temp_ant = scraper.buscar_dados_hibrido(str(ano_atual - 1))

    valid_dfs = [df for df in [df_temp_ant, df_temp_atual] if df is not None and not df.empty]

    if not valid_dfs:
        loading_text.value = "Erro: API indisponível."; loading_text.color="red"; page.update(); return

    df_total = pd.concat(valid_dfs).drop_duplicates().reset_index(drop=True)
    df_total['Date'] = pd.to_datetime(df_total['Date'])

    loading_text.value = "Analisando estatísticas e treinando IA..."
    page.update()

    df_res = df_total[df_total['FTHG'].notna()].copy()
    df_fut = df_total[df_total['FTHG'].isna()].copy()
    
    df_treino, time_stats = preparar_dados_para_modelo(df_res)
    dados_evolucao = gerar_dados_evolucao(df_total)
    
    modelos, encoder, cols_model = None, None, None
    if not df_treino.empty:
        modelos, encoder, cols_model = treinar_modelo(df_treino)
    
    times = sorted(list(set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))))
    opts = [ft.dropdown.Option(t) for t in times]
    page.clean()

    # ABA DE JOGOS
    def criar_card_jogo(row):
        mandante, visitante = row['HomeTeam'], row['AwayTeam']
        data_str = row['Date'].strftime("%d/%m - %H:%M")
        def ir_para_previsao(e):
            tabs.selected_index = 1; dd_c.value = mandante; dd_v.value = visitante
            page.update(); on_prev(None) 
        return criar_card(ft.Row([ft.Column([ft.Text(data_str, size=11, color=COR_TEXT_SEC), ft.Row([ft.Text(mandante, weight="bold", size=13, expand=True, text_align="right"), ft.Container(content=ft.Text("vs", size=10, color="black", weight="bold"), bgcolor=COR_ACCENT, padding=4, border_radius=4), ft.Text(visitante, weight="bold", size=13, expand=True, text_align="left")], alignment="center", spacing=10)], spacing=2, expand=True)], alignment="center"), padding=12, on_click=ir_para_previsao)

    conteudo_jogos = []
    if not df_fut.empty:
        df_fut_disp = df_fut.copy()
        df_fut_disp['Rodada_Num'] = pd.to_numeric(df_fut_disp['Rodada'], errors='coerce')
        for rodada in sorted(df_fut_disp['Rodada_Num'].dropna().unique()):
            jogos_r = df_fut_disp[df_fut_disp['Rodada_Num'] == rodada]
            conteudo_jogos.append(ft.Container(content=ft.Text(f"Rodada {int(rodada)}", size=16, weight="bold", color=COR_ACCENT), padding=ft.padding.only(top=15, bottom=5)))
            grid = ft.ResponsiveRow(spacing=10, run_spacing=10)
            for _, r in jogos_r.iterrows(): grid.controls.append(ft.Container(content=criar_card_jogo(r), col={"xs": 12, "sm": 6}))
            conteudo_jogos.append(grid)

    tab_jogos = ft.Container(content=ft.Column([ft.Text("Calendário de Jogos", size=22, weight="bold"), ft.Divider(color=COR_BORDER), ft.Column(conteudo_jogos, scroll=ft.ScrollMode.AUTO, expand=True)], expand=True), padding=20)

    # ABA PREVISÃO
    dd_c = ft.Dropdown(label="Mandante", options=opts, expand=True); dd_v = ft.Dropdown(label="Visitante", options=opts, expand=True)
    forma_c_cont = ft.Container(); forma_v_cont = ft.Container()
    res_area = ft.Column(visible=False, spacing=15)

    def on_prev(e):
        if not modelos or not dd_c.value or not dd_v.value: return
        btn_prev.content = ft.ProgressRing(width=20, color="black"); page.update()
        if dd_c.value in time_stats: forma_c_cont.content = criar_bolinhas_forma(time_stats[dd_c.value].get('seq', []))
        if dd_v.value in time_stats: forma_v_cont.content = criar_bolinhas_forma(time_stats[dd_v.value].get('seq', []))
        odds = prever_jogo_especifico(dd_c.value, dd_v.value, modelos, encoder, time_stats, cols_model)
        res_area.controls = [
            ft.Divider(color=COR_BORDER),
            ft.Row([criar_stat_box(dd_c.value, f"{odds.get('Casa',0):.0%}", CORES_TIMES.get(dd_c.value, COR_ACCENT)), criar_stat_box("Empate", f"{odds.get('Empate',0):.0%}", "grey"), criar_stat_box(dd_v.value, f"{odds.get('Visitante',0):.0%}", CORES_TIMES.get(dd_v.value, "#00B0FF"))]),
            ft.Row([criar_stat_box("Over 2.5", f"{odds.get('Over25',0):.0%}"), criar_stat_box("Ambas Marcam", f"{odds.get('BTTS',0):.0%}")])
        ]
        res_area.visible = True; btn_prev.content = ft.Text("CALCULAR"); page.update()

    btn_prev = ft.ElevatedButton("CALCULAR", bgcolor=COR_ACCENT, color="black", height=50, on_click=on_prev, width=float('inf'))
    tab_prev = ft.Container(content=ft.Column([criar_card(ft.Column([ft.Text("Predictor Engine", size=18, weight="bold"), ft.Row([dd_c, dd_v]), ft.Row([forma_c_cont, ft.Text("Forma Recente"), forma_v_cont], alignment="center"), btn_prev])), res_area], scroll=ft.ScrollMode.AUTO), padding=20)

    # ABA H2H
    h_c = ft.Dropdown(label="Time A", options=opts, expand=True); h_v = ft.Dropdown(label="Time B", options=opts, expand=True)
    h_res = ft.Row([], alignment="spaceEvenly"); h_list = ft.Column(scroll="auto", height=250)
    def on_h2h(e):
        if not h_c.value or not h_v.value: return
        res, df_h2h = gerar_confronto_direto(df_total, h_c.value, h_v.value)
        h_res.controls = [
            criar_stat_box(h_c.value, res['vitorias'].get(h_c.value, 0), CORES_TIMES.get(h_c.value, COR_ACCENT)),
            criar_stat_box("Empates", res.get('empates', 0), "grey"),
            criar_stat_box(h_v.value, res['vitorias'].get(h_v.value, 0), CORES_TIMES.get(h_v.value, "#00B0FF"))
        ]
        h_list.controls = [criar_tabela_estilizada(df_h2h)]; page.update()

    tab_h2h = ft.Container(content=ft.Column([
        criar_card(ft.Column([
            ft.Text("Histórico Head-to-Head", size=18, weight="bold"),
            ft.Text("Dados dos útltimos quatro confrontos.", size=11, color=COR_TEXT_SEC),
            ft.Row([h_c, h_v]),
            ft.ElevatedButton("BUSCAR CONFRONTO", on_click=on_h2h, width=float('inf'))
        ])),
        h_res,
        criar_card(h_list, padding=10)
    ], scroll=ft.ScrollMode.AUTO), padding=20)

    # ABA SIMULADOR
    tabela_sim_cont = ft.Column(scroll=ft.ScrollMode.AUTO)
    def rodar_sim(e):
        if not modelos: return
        btn_sim.content = ft.ProgressRing(width=20, color="black"); page.update()
        try:
            # Chama a simulação completa para a rodada 38
            df_simulado = simular_campeonato(38, df_fut, df_res, modelos, encoder, time_stats, cols_model)
            tabela_sim_cont.controls = [criar_tabela_estilizada(df_simulado)]
        except Exception as ex:
            print(f"Erro na simulação: {ex}")
            tabela_sim_cont.controls = [ft.Text(f"Erro: {ex}", color="red")]
        btn_sim.content = ft.Text("RODAR SIMULAÇÃO COMPLETA"); page.update()

    btn_sim = ft.ElevatedButton("RODAR SIMULAÇÃO COMPLETA", bgcolor=COR_ACCENT, color="black", on_click=rodar_sim, width=float('inf'))
    tab_sim = ft.Container(content=ft.Column([
        criar_card(ft.Column([
            ft.Text("Simular a Tabela Final", size=18, weight="bold"),
            ft.Text("Projeta a classificação final com base na IA.", size=11, color=COR_TEXT_SEC),
            btn_sim
        ])),
        tabela_sim_cont
    ], scroll=ft.ScrollMode.AUTO), padding=20)

    # HEADER E TABS
    header = ft.Container(content=ft.Row([ft.Row([ft.Icon(name="sports_soccer", color=COR_ACCENT), ft.Text("AtletiQ 2.0", size=20, weight="bold")]), ft.IconButton(icon="settings")], alignment="spaceBetween"), padding=15, border=ft.border.only(bottom=ft.border.BorderSide(1, COR_BORDER)))
    tabs = ft.Tabs(selected_index=0, indicator_color=COR_ACCENT, tabs=[
        ft.Tab(text="Jogos", icon="calendar_today", content=tab_jogos),
        ft.Tab(text="Previsão", icon="analytics", content=tab_prev),
        ft.Tab(text="H2H", icon="compare_arrows", content=tab_h2h),
        ft.Tab(text="Simular Tabela", icon="table_chart", content=tab_sim)
    ], expand=True)

    page.add(header, tabs)

if __name__ == "__main__":
    ft.app(target=main)