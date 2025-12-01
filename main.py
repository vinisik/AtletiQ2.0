import flet as ft
import pandas as pd
from datetime import datetime
import time

# -----------------------------------
# IMPORTS E TRATAMENTO DE ERRO
# -----------------------------------
try:
    from web_scraper import buscar_dados_brasileirao
    from feature_engineering import preparar_dados_para_modelo
    from model_trainer import treinar_modelo
    from predictor import prever_jogo_especifico, simular_campeonato
    from analysis import gerar_confronto_direto
except ImportError as e:
    print(f"Erro crítico de importação: {e}")
    raise e

# -----------------------------------
# CONSTANTES DE ESTILO (PALETA)
# -----------------------------------
COR_ACCENT = "#00E676"  
COR_BG = "#121212"      
COR_SURFACE = "#1E1E1E" 
COR_TEXT_SEC = "#9E9E9E"
COR_BORDER = "#333333"  

# -----------------------------------
# COMPONENTES DE UI REUTILIZÁVEIS
# -----------------------------------
def criar_card(content, padding=20):
    """Cria um container estilizado com bordas arredondadas e fundo cinza."""
    return ft.Container(
        content=content,
        bgcolor=COR_SURFACE,
        border_radius=15,
        padding=padding,
        border=ft.border.all(1, COR_BORDER),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color="#4D000000",
            offset=ft.Offset(0, 4),
        ),
    )

def criar_stat_box(label, value, color="white", subtext=None):
    """Cria uma caixinha de estatística vertical."""
    elements = [
        ft.Text(label, size=12, color=COR_TEXT_SEC, weight="w500"),
        ft.Text(str(value), size=24, weight="bold", color=color),
    ]
    if subtext:
        elements.append(ft.Text(subtext, size=10, color=COR_TEXT_SEC))
        
    return ft.Container(
        content=ft.Column(elements, horizontal_alignment="center", spacing=2),
        bgcolor="#0DFFFFFF",
        border_radius=10,
        padding=15,
        expand=True,
        alignment=ft.alignment.center
    )

def criar_tabela_estilizada(df: pd.DataFrame):
    """Cria uma tabela moderna e limpa com LARGURA TOTAL."""
    if df is None or df.empty:
        return ft.Text("Sem dados disponíveis.", color="red")
    
    columns = [ft.DataColumn(ft.Text(str(col), weight="bold", color=COR_ACCENT)) for col in df.columns]
    rows = []
    for i, row in df.iterrows():
        bg_color = "#05FFFFFF" if i % 2 == 0 else "transparent"
        cells = [ft.DataCell(ft.Text(str(val), size=13)) for val in row]
        rows.append(ft.DataRow(cells=cells, color=bg_color))
    
    return ft.DataTable(
        columns=columns,
        rows=rows,
        heading_row_color="#1AFFFFFF",
        heading_row_height=40,
        data_row_max_height=40,
        column_spacing=20,
        divider_thickness=0,
        # --- ALTERAÇÃO AQUI: FORÇA LARGURA TOTAL ---
        width=float('inf'), 
    )

# -----------------------------------
# APP PRINCIPAL
# -----------------------------------
def main(page: ft.Page):
    # Configurações Globais
    page.title = "AtletiQ Pro"
    page.theme_mode = "dark"
    page.padding = 0 
    page.bgcolor = COR_BG
    page.fonts = {"Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"}

    # --- TELA DE CARREGAMENTO (SPLASH SCREEN) ---
    loading_text = ft.Text("Inicializando Neural Engine...", color=COR_TEXT_SEC, size=12)
    loading_bar = ft.ProgressBar(width=200, color=COR_ACCENT, bgcolor="#333333")
    
    splash = ft.Container(
        content=ft.Column([
            ft.Image(src="logo.png", width=120, error_content=ft.Icon(name="sports_soccer", size=80, color=COR_ACCENT)),
            ft.Text("AtletiQ", size=40, weight="bold"), 
            ft.Container(height=20),
            loading_bar,
            loading_text
        ], alignment="center", horizontal_alignment="center"),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=COR_BG
    )
    
    page.add(splash)
    page.update()

    # --- LÓGICA DE BACKEND (CARREGAMENTO) ---
    loading_text.value = "Conectando ao banco de dados..."
    page.update()
    
    ano_atual = datetime.now().year
    df_total = buscar_dados_brasileirao(str(ano_atual))
    
    if df_total is None or df_total.empty:
        loading_text.value = f"Tentando dados de {ano_atual-1}..."
        page.update()
        df_total = buscar_dados_brasileirao(str(ano_atual - 1))

    if df_total is None or df_total.empty:
        loading_text.value = "Erro crítico de conexão."
        loading_text.color = "red"
        return

    loading_text.value = "Treinando Modelos de IA..."
    page.update()

    df_resultados = df_total[df_total['FTHG'].notna()].copy()
    df_futuro = df_total[df_total['FTHG'].isna()].copy()
    
    df_treino, time_stats = preparar_dados_para_modelo(df_resultados)
    
    modelo = None
    encoder = None
    colunas_modelo = None
    
    if not df_treino.empty and len(df_treino) > 10:
        modelo, encoder, colunas_modelo = treinar_modelo(df_treino)
    
    lista_times = sorted(list(set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))))
    opcoes_times = [ft.dropdown.Option(t) for t in lista_times]

    page.clean()

    # -----------------------------------
    # UI PRINCIPAL
    # -----------------------------------

    # HEADER MODERNO
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Image(src="logo.png", width=40, height=40, error_content=ft.Icon(name="sports_soccer", color=COR_ACCENT)),
                ft.Text("AtletiQ", size=22, weight="bold"),
                ft.Container(
                    content=ft.Text("PRO 2025", size=10, weight="bold", color="black"),
                    bgcolor=COR_ACCENT, padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                )
            ], alignment="center"),
            ft.IconButton(icon="settings", icon_color=COR_TEXT_SEC, tooltip="Configurações")
        ], alignment="spaceBetween"),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        border=ft.border.only(bottom=ft.border.BorderSide(1, COR_BORDER)),
        bgcolor=COR_BG
    )

    # -----------------------------------
    # CONTEÚDO DA ABA 1: PREVISÃO
    # -----------------------------------
    
    dd_casa = ft.Dropdown(label="Mandante", options=opcoes_times, expand=True, text_size=14, border_color=COR_BORDER, border_radius=10, focused_border_color=COR_ACCENT)
    dd_visitante = ft.Dropdown(label="Visitante", options=opcoes_times, expand=True, text_size=14, border_color=COR_BORDER, border_radius=10, focused_border_color=COR_ACCENT)

    display_resultado = ft.Column(visible=False, spacing=20)

    def click_prever(e):
        if not dd_casa.value or not dd_visitante.value:
            page.snack_bar = ft.SnackBar(ft.Text("Selecione os dois times!"))
            page.snack_bar.open = True; page.update(); return
        
        if dd_casa.value == dd_visitante.value:
            page.snack_bar = ft.SnackBar(ft.Text("Times iguais selecionados.")); page.snack_bar.open = True; page.update(); return

        if modelo is None:
            page.snack_bar = ft.SnackBar(ft.Text("IA em calibração (dados insuficientes).")); page.snack_bar.open = True; page.update(); return

        btn_prever.content = ft.ProgressRing(width=20, height=20, color="black", stroke_width=2)
        page.update()
        time.sleep(0.5)

        odds = prever_jogo_especifico(dd_casa.value, dd_visitante.value, modelo, encoder, time_stats, colunas_modelo)
        
        p_c = odds.get('Casa', 0.0)
        p_e = odds.get('Empate', 0.0)
        p_v = odds.get('Visitante', 0.0)

        cor_c = COR_ACCENT if p_c > p_v and p_c > p_e else "white"
        cor_v = COR_ACCENT if p_v > p_c and p_v > p_e else "white"
        
        display_resultado.controls = [
            ft.Divider(color=COR_BORDER),
            ft.Row([
                criar_stat_box("VITÓRIA CASA", f"{p_c:.1%}", cor_c),
                criar_stat_box("EMPATE", f"{p_e:.1%}", "grey"),
                criar_stat_box("VITÓRIA VISITANTE", f"{p_v:.1%}", cor_v),
            ]),
            ft.Stack([
                ft.Container(bgcolor="#333333", height=10, border_radius=5, width=float('inf')),
                ft.Row([
                    ft.Container(bgcolor=COR_ACCENT, height=10, width=0, expand=int(p_c*100), border_radius=ft.border_radius.only(top_left=5, bottom_left=5)),
                    ft.Container(bgcolor="grey", height=10, width=0, expand=int(p_e*100)),
                    ft.Container(bgcolor="#00B0FF", height=10, width=0, expand=int(p_v*100), border_radius=ft.border_radius.only(top_right=5, bottom_right=5)),
                ], spacing=1, width=float('inf'))
            ])
        ]
        display_resultado.visible = True
        
        btn_prever.content = ft.Text("CALCULAR PROBABILIDADES", weight="bold")
        page.update()

    btn_prever = ft.ElevatedButton(
        content=ft.Text("CALCULAR PROBABILIDADES", weight="bold"),
        bgcolor=COR_ACCENT,
        color="black",
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=click_prever,
        width=float('inf') 
    )

    tab_previsao = ft.Container(
        content=ft.Column([
            criar_card(
                ft.Column([
                    ft.Text("Match Predictor", size=18, weight="bold", color="white"),
                    ft.Text("Selecione o confronto para análise da IA", size=12, color=COR_TEXT_SEC),
                    ft.Container(height=10),
                    ft.Row([
                        dd_casa,
                        ft.Icon(name="close", size=20, color=COR_TEXT_SEC),
                        dd_visitante
                    ], alignment="center"),
                    ft.Container(height=10),
                    btn_prever
                ])
            ),
            display_resultado
        ], spacing=20),
        padding=20
    )

    # -----------------------------------
    # CONTEÚDO DA ABA 2: SIMULAÇÃO
    # -----------------------------------
    slider_rodada = ft.Slider(min=1, max=38, value=38, divisions=38, label="{value}ª Rodada", active_color=COR_ACCENT)
    container_tabela = ft.Column(scroll=ft.ScrollMode.HIDDEN, height=400)

    def click_simular(e):
        page.splash = ft.ProgressBar(color=COR_ACCENT); page.update()
        
        tabela = simular_campeonato(int(slider_rodada.value), df_futuro, df_resultados, modelo, encoder, time_stats, colunas_modelo)
        
        container_tabela.controls = [criar_tabela_estilizada(tabela)]
        page.splash = None
        page.update()

    tab_simulacao = ft.Container(
        content=ft.Column([
            criar_card(
                ft.Column([
                    ft.Text("Simulador de Temporada", size=18, weight="bold"),
                    ft.Text("Projete a tabela futura baseada no desempenho atual", size=12, color=COR_TEXT_SEC),
                    ft.Container(height=10),
                    ft.Row([ft.Text("Até rodada:"), slider_rodada], alignment="spaceBetween"),
                    ft.ElevatedButton("SIMULAR TABELA", bgcolor="#333333", color="white", on_click=click_simular, height=45, width=float('inf'))
                ])
            ),
            criar_card(container_tabela, padding=0)
        ]),
        padding=20
    )

    # -----------------------------------
    # CONTEÚDO DA ABA 3: H2H
    # -----------------------------------
    h2h_t1 = ft.Dropdown(label="Time A", options=opcoes_times, expand=True, border_color=COR_BORDER, border_radius=10)
    h2h_t2 = ft.Dropdown(label="Time B", options=opcoes_times, expand=True, border_color=COR_BORDER, border_radius=10)
    h2h_stats = ft.Row([], alignment="spaceEvenly")
    h2h_lista_jogos = ft.Column(scroll=ft.ScrollMode.AUTO, height=250)

    def click_h2h(e):
        if not h2h_t1.value or not h2h_t2.value: return
        resumo, df_jogos = gerar_confronto_direto(df_total, h2h_t1.value, h2h_t2.value)
        
        h2h_stats.controls = [
            criar_stat_box("VITÓRIAS A", resumo['vitorias'].get(h2h_t1.value, 0), COR_ACCENT),
            criar_stat_box("EMPATES", resumo.get('empates', 0)),
            criar_stat_box("VITÓRIAS B", resumo['vitorias'].get(h2h_t2.value, 0), "#00B0FF"),
        ]
        
        h2h_lista_jogos.controls = [criar_tabela_estilizada(df_jogos)]
        page.update()

    tab_h2h = ft.Container(
        content=ft.Column([
            criar_card(
                ft.Column([
                    ft.Text("Histórico (H2H)", size=18, weight="bold"),
                    ft.Row([h2h_t1, h2h_t2]),
                    ft.ElevatedButton("ANALISAR CONFRONTO", bgcolor="#333333", color="white", on_click=click_h2h, width=float('inf'))
                ])
            ),
            h2h_stats,
            criar_card(ft.Column([
                ft.Text("Últimos Jogos", weight="bold", size=14),
                h2h_lista_jogos
            ], scroll=ft.ScrollMode.HIDDEN), padding=10)
        ]),
        padding=20
    )

    # -----------------------------------
    # NAVEGAÇÃO (TABS)
    # -----------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        indicator_color=COR_ACCENT,
        label_color=COR_ACCENT,
        unselected_label_color=COR_TEXT_SEC,
        divider_color="transparent",
        tabs=[
            ft.Tab(text="PREVISÃO", icon="analytics", content=tab_previsao),
            ft.Tab(text="SIMULAÇÃO", icon="table_chart", content=tab_simulacao),
            ft.Tab(text="H2H", icon="compare_arrows", content=tab_h2h),
        ],
        expand=True
    )

    page.add(header, tabs)

if __name__ == "__main__":
    ft.app(target=main)