import flet as ft
import pandas as pd
import numpy as np 
from datetime import datetime
import time

try:
    from web_scraper import buscar_dados_brasileirao
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

# Cores Oficiais dos Times 
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
    """Cria um container estilizado (Card)."""
    return ft.Container(
        content=content,
        bgcolor=COR_SURFACE,
        border_radius=15,
        padding=padding,
        border=ft.border.all(1, COR_BORDER),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#4D000000", offset=ft.Offset(0, 4)),
        on_click=on_click,
    )

def criar_stat_box(label, value, color="white", subtext=None):
    """Cria uma caixinha de estatística vertical."""
    elements = [
        ft.Text(label, size=11, color=COR_TEXT_SEC, weight="w500"),
        ft.Text(str(value), size=22, weight="bold", color=color),
    ]
    if subtext:
        elements.append(ft.Text(subtext, size=10, color=COR_TEXT_SEC))
        
    return ft.Container(
        content=ft.Column(elements, horizontal_alignment="center", spacing=2),
        bgcolor="#0DFFFFFF",
        border_radius=10,
        padding=10,
        expand=True,
        alignment=ft.alignment.center
    )

def criar_bolinhas_forma(sequencia):
    """
    Cria a visualização de 'Form Guide' (V-E-D) com bolinhas coloridas.
    Recebe uma lista ex: ['V', 'E', 'D', 'V', 'V']
    """
    if not sequencia:
        return ft.Row([ft.Text("-", color="grey")], alignment="center")
    
    # Pega apenas os últimos 5 jogos
    ultimos_5 = sequencia[-5:]
    
    controles = []
    for res in ultimos_5:
        if res == 'V': cor, tip = "green", "Vitória"
        elif res == 'D': cor, tip = "red", "Derrota"
        else: cor, tip = "grey", "Empate"
        
        controles.append(
            ft.Container(
                width=12, height=12, border_radius=6, bgcolor=cor,
                tooltip=f"{tip} (Últimos Jogos)"
            )
        )
    return ft.Row(controles, spacing=4, alignment="center")

def criar_tabela_estilizada(df: pd.DataFrame):
    if df is None or df.empty: return ft.Text("Sem dados.", color="red")
    columns = [ft.DataColumn(ft.Text(str(col), weight="bold", color=COR_ACCENT)) for col in df.columns]
    rows = []
    for i, row in df.iterrows():
        bg = "#05FFFFFF" if i % 2 == 0 else "transparent"
        cells = [ft.DataCell(ft.Text(str(val), size=13)) for val in row]
        rows.append(ft.DataRow(cells=cells, color=bg))
    return ft.DataTable(columns=columns, rows=rows, heading_row_color="#1AFFFFFF", width=float('inf'), divider_thickness=0)

# APP PRINCIPAL
def main(page: ft.Page):
    page.title = "AtletiQ Pro"
    page.theme_mode = "dark" 
    page.padding = 0 
    page.bgcolor = COR_BG
    page.fonts = {"Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"}

    # --- LOADING SCREEN ---
    loading_text = ft.Text("Carregando inteligência...", color=COR_TEXT_SEC, size=12)
    loading_bar = ft.ProgressBar(width=200, color=COR_ACCENT, bgcolor="#333333")
    splash = ft.Container(
        content=ft.Column([
            ft.Image(src="logo.png", width=120, error_content=ft.Icon(name="sports_soccer", size=80, color=COR_ACCENT)),
            ft.Text("AtletiQ", size=40, weight="bold"), 
            ft.Container(height=20), loading_bar, loading_text
        ], alignment="center", horizontal_alignment="center"),
        alignment=ft.alignment.center, expand=True, bgcolor=COR_BG
    )
    page.add(splash); page.update()

    # --- DADOS (BACKEND) ---
    loading_text.value = "Conectando ao banco de dados..."
    page.update()
    
    ano = datetime.now().year
    df_total = buscar_dados_brasileirao(str(ano))
    if df_total is None or df_total.empty:
        loading_text.value = f"Tentando {ano-1}..."
        page.update()
        df_total = buscar_dados_brasileirao(str(ano - 1))

    if df_total is None: loading_text.value = "Erro Fatal de Conexão"; loading_text.color="red"; return

    loading_text.value = "Treinando IA..."
    page.update()

    df_res = df_total[df_total['FTHG'].notna()].copy()
    df_fut = df_total[df_total['FTHG'].isna()].copy()
    
    # Prepara dados e sequência
    df_treino, time_stats = preparar_dados_para_modelo(df_res)
    dados_evolucao = gerar_dados_evolucao(df_total)
    
    modelos, encoder, cols_model = None, None, None
    if not df_treino.empty and len(df_treino) > 10:
        modelos, encoder, cols_model = treinar_modelo(df_treino)
    
    times = sorted(list(set(df_total['HomeTeam']).union(set(df_total['AwayTeam']))))
    opts = [ft.dropdown.Option(t) for t in times]
    page.clean()

    
    # 1. ABA DE JOGOS (CALENDÁRIO COMPLETO)
    def criar_card_jogo(row):
        mandante = row['HomeTeam']
        visitante = row['AwayTeam']
        # Tenta formatar a data se ela existir
        try:
            data_obj = pd.to_datetime(row['Date'])
            data_str = data_obj.strftime("%d/%m - %H:%M")
        except:
            data_str = str(row['Date'])
        
        # Ação ao clicar no card: Preenche a aba de previsão automaticamente
        def ir_para_previsao(e):
            tabs.selected_index = 1 # Índice da aba Previsão
            dd_c.value = mandante
            dd_v.value = visitante
            page.update()
            # Dispara a previsão se o modelo estiver pronto
            if modelos: on_prev(None) 

        return criar_card(
            ft.Row([
                ft.Column([
                    ft.Text(f"{data_str}", size=11, color=COR_TEXT_SEC),
                    ft.Row([
                        ft.Text(mandante, weight="bold", size=13, expand=True, text_align="right"),
                        ft.Container(content=ft.Text("vs", size=10, color="black", weight="bold"), bgcolor=COR_ACCENT, padding=4, border_radius=4),
                        ft.Text(visitante, weight="bold", size=13, expand=True, text_align="left"),
                    ], alignment="center", spacing=10)
                ], spacing=2, expand=True)
            ], alignment="center"),
            padding=12,
            on_click=ir_para_previsao
        )

    # Lógica para agrupar jogos por rodada
    conteudo_jogos = []
    
    if df_fut.empty:
        conteudo_jogos.append(ft.Text("Nenhum jogo futuro encontrado.", color="grey", size=16))
    else:
        # Garante que a coluna Rodada é numérica para ordenar corretamente
        df_fut['Rodada_Num'] = pd.to_numeric(df_fut['Rodada'], errors='coerce')
        rodadas_futuras = sorted(df_fut['Rodada_Num'].dropna().unique())
        
        for rodada in rodadas_futuras:
            jogos_da_rodada = df_fut[df_fut['Rodada_Num'] == rodada]
            
            # Título da Rodada
            conteudo_jogos.append(
                ft.Container(
                    content=ft.Text(f"Rodada {int(rodada)}", size=16, weight="bold", color=COR_ACCENT),
                    padding=ft.padding.only(top=15, bottom=5)
                )
            )
            
            grid_rodada = ft.ResponsiveRow(spacing=10, run_spacing=10)
            
            for _, row in jogos_da_rodada.iterrows():
                # col={"xs": 12, "sm": 6} significa: 1 coluna em mobile, 2 em telas maiores
                grid_rodada.controls.append(
                    ft.Container(content=criar_card_jogo(row), col={"xs": 12, "sm": 6})
                )
                
            conteudo_jogos.append(grid_rodada)
            conteudo_jogos.append(ft.Divider(color="#222222"))

    # Container com scroll para todos os jogos
    scroll_jogos = ft.Column(
        controls=conteudo_jogos,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    tab_jogos = ft.Container(
        content=ft.Column([
            ft.Text("Calendário de Jogos", size=22, weight="bold"),
            ft.Text("Clique em um jogo para ver a previsão da IA", size=12, color=COR_TEXT_SEC),
            ft.Divider(color=COR_BORDER),
            scroll_jogos
        ]), 
        padding=20,
    )


    dd_c = ft.Dropdown(label="Mandante", options=opts, expand=True, border_color=COR_BORDER, border_radius=10, text_size=14)
    dd_v = ft.Dropdown(label="Visitante", options=opts, expand=True, border_color=COR_BORDER, border_radius=10, text_size=14)
    
    # Controles para Forma 
    forma_c_cont = ft.Container()
    forma_v_cont = ft.Container()
    
    # Controle para Alerta de Zebra
    zebra_alert = ft.Container(visible=False)
    
    res_area = ft.Column(visible=False, spacing=15)

    def on_prev(e):
        if not modelos: 
            page.snack_bar = ft.SnackBar(ft.Text("IA em calibração (dados insuficientes).")); page.snack_bar.open=True; page.update(); return
        if not dd_c.value or not dd_v.value: return
        
        # Atualiza Forma 
        if dd_c.value in time_stats:
            seq_c = time_stats[dd_c.value].get('seq', [])
            forma_c_cont.content = criar_bolinhas_forma(seq_c)
        if dd_v.value in time_stats:
            seq_v = time_stats[dd_v.value].get('seq', [])
            forma_v_cont.content = criar_bolinhas_forma(seq_v)

        btn_prev.content = ft.ProgressRing(width=20, height=20, color="black", stroke_width=2); page.update()
        time.sleep(0.5)

        odds = prever_jogo_especifico(dd_c.value, dd_v.value, modelos, encoder, time_stats, cols_model)
        pc, pe, pv = odds.get('Casa', 0.0), odds.get('Empate', 0.0), odds.get('Visitante', 0.0)
        
        # Cores Personalizadas
        cor_c = CORES_TIMES.get(dd_c.value, COR_ACCENT)
        cor_v = CORES_TIMES.get(dd_v.value, "#00B0FF")
        
        # Lógica da Zebra 
        # Se o mandante tem média de pontos menor mas chance > 40%, ou vice-versa
        pts_c = np.mean(time_stats[dd_c.value]['pontos']) if dd_c.value in time_stats and time_stats[dd_c.value]['pontos'] else 0
        pts_v = np.mean(time_stats[dd_v.value]['pontos']) if dd_v.value in time_stats and time_stats[dd_v.value]['pontos'] else 0
        
        eh_zebra = False
        if (pts_c < pts_v and pc > 0.40) or (pts_v < pts_c and pv > 0.40):
            eh_zebra = True
            
        zebra_alert.content = ft.Container(
            content=ft.Row([
                ft.Icon(name="warning", color="yellow"),
                ft.Text("ALERTA DE ZEBRA: Probabilidade alta para o azarão!", color="yellow", weight="bold")
            ], alignment="center"),
            bgcolor="#332b00", border=ft.border.all(1, "yellow"), border_radius=10, padding=10
        )
        zebra_alert.visible = eh_zebra

        res_area.controls = [
            ft.Divider(color=COR_BORDER),
            zebra_alert,
            ft.Row([
                criar_stat_box("CASA", f"{pc:.0%}", cor_c if cor_c != "#FFFFFF" else "white"),
                criar_stat_box("EMPATE", f"{pe:.0%}", "grey"),
                criar_stat_box("VISITANTE", f"{pv:.0%}", cor_v if cor_v != "#FFFFFF" else "white"),
            ]),
            # Barra de Progresso Customizada
            ft.Stack([
                ft.Container(bgcolor="#333", height=8, width=float('inf'), border_radius=4),
                ft.Row([
                    ft.Container(bgcolor=cor_c, height=8, width=0, expand=int(pc*100), border_radius=ft.border_radius.only(top_left=4, bottom_left=4)),
                    ft.Container(bgcolor="grey", height=8, width=0, expand=int(pe*100)),
                    ft.Container(bgcolor=cor_v, height=8, width=0, expand=int(pv*100), border_radius=ft.border_radius.only(top_right=4, bottom_right=4)),
                ], spacing=1, width=float('inf'))
            ]),
            ft.Row([
                criar_stat_box("OVER 2.5", f"{odds.get('Over25',0):.0%}", COR_ACCENT if odds.get('Over25',0)>0.5 else "grey"),
                criar_stat_box("AMBAS MARCAM", f"{odds.get('BTTS',0):.0%}", COR_ACCENT if odds.get('BTTS',0)>0.5 else "grey")
            ])
        ]
        res_area.visible = True
        btn_prev.content = ft.Text("CALCULAR", weight="bold", color="black"); page.update()

    btn_prev = ft.ElevatedButton("CALCULAR", bgcolor=COR_ACCENT, color="black", height=50, on_click=on_prev, width=float('inf'))
    
    tab_prev = ft.Container(content=ft.Column([
        criar_card(ft.Column([
            ft.Text("IA Predictor", size=18, weight="bold"),
            ft.Row([dd_c, ft.Text("x"), dd_v], alignment="center"),
            ft.Row([
                ft.Column([ft.Text("Recentes", size=10), forma_c_cont], horizontal_alignment="center"),
                ft.Container(width=20),
                ft.Column([ft.Text("Recentes", size=10), forma_v_cont], horizontal_alignment="center"),
            ], alignment="center"),
            btn_prev
        ])),
        res_area
    ]), padding=20)


    # 3. ABA SIMULAÇÃO (COM EXPORTAR)
    sld = ft.Slider(min=1, max=38, divisions=38, label="{value}", active_color=COR_ACCENT)
    tbl_sim = ft.Column(scroll="hidden", height=400)
    
    def salvar_csv(e):
        try:
            # Recalcula a tabela atual para garantir dados frescos
            tb = simular_campeonato(int(sld.value), df_fut, df_res, modelos, encoder, time_stats, cols_model)
            nome = f"simulacao_rodada_{int(sld.value)}.csv"
            tb.to_csv(nome, index=False)
            page.snack_bar = ft.SnackBar(ft.Text(f"Sucesso! Salvo como: {nome}", color="white"), bgcolor="green")
            page.snack_bar.open=True; page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {ex}"), bgcolor="red"); page.snack_bar.open=True; page.update()

    def on_sim(e):
        if not modelos: return
        tb = simular_campeonato(int(sld.value), df_fut, df_res, modelos, encoder, time_stats, cols_model)
        tbl_sim.controls = [criar_tabela_estilizada(tb)]
        btn_exp.disabled = False; page.update()

    btn_exp = ft.ElevatedButton("EXPORTAR CSV", icon="download", on_click=salvar_csv, disabled=True, bgcolor="#444", color="white")
    
    tab_sim = ft.Container(content=ft.Column([
        criar_card(ft.Column([
            ft.Text("Simulador", weight="bold"),
            ft.Row([ft.Text("Até rodada:"), sld], alignment="spaceBetween"),
            ft.Row([
                ft.ElevatedButton("RODAR", bgcolor="#333", color="white", on_click=on_sim, expand=True),
                btn_exp
            ])
        ])),
        criar_card(tbl_sim, padding=0)
    ]), padding=20)

    # 4. H2H 
    h_c = ft.Dropdown(label="A", options=opts, expand=True, border_color=COR_BORDER); h_v = ft.Dropdown(label="B", options=opts, expand=True, border_color=COR_BORDER)
    h_res = ft.Row([], alignment="spaceEvenly"); h_list = ft.Column(scroll="auto", height=250)
    def on_h2h(e):
        if not h_c.value or not h_v.value: return
        res, df = gerar_confronto_direto(df_total, h_c.value, h_v.value)
        h_res.controls = [criar_stat_box("VIT A", res['vitorias'].get(h_c.value,0), COR_ACCENT), criar_stat_box("EMP", res.get('empates',0)), criar_stat_box("VIT B", res['vitorias'].get(h_v.value,0), "#00B0FF")]
        h_list.controls = [criar_tabela_estilizada(df)]; page.update()
    tab_h2h = ft.Container(content=ft.Column([criar_card(ft.Column([ft.Text("H2H", weight="bold"), ft.Row([h_c, h_v]), ft.ElevatedButton("BUSCAR", bgcolor="#333", on_click=on_h2h)])), h_res, criar_card(h_list, padding=10)]), padding=20)

    # 5. EVOLUÇÃO 
    c_dd = ft.Dropdown(label="Time", options=opts, border_color=COR_BORDER); c_box = ft.Container(height=300)
    def on_chart(e):
        t = c_dd.value
        if not t or t not in dados_evolucao: return
        pts = [ft.LineChartDataPoint(r, 21-p) for r, p in dados_evolucao[t]]
        # Usa cor do time ou verde padrão
        cor = CORES_TIMES.get(t, COR_ACCENT)
        c_box.content = ft.LineChart(data_series=[ft.LineChartData(data_points=pts, color=cor, stroke_width=3, curved=True)], min_y=1, max_y=20, border=ft.border.all(1, COR_BORDER))
        page.update()
    tab_evo = ft.Container(content=ft.Column([criar_card(ft.Column([ft.Text("Evolução", weight="bold"), ft.Row([c_dd, ft.IconButton(icon="check", on_click=on_chart)])])), criar_card(c_box, padding=20)]), padding=20)

    # HEADER & TABS
    header = ft.Container(content=ft.Row([
        ft.Row([ft.Icon(name="sports_soccer", color=COR_ACCENT), ft.Text("AtletiQ Pro", size=20, weight="bold")]),
        ft.IconButton(icon="settings", icon_color=COR_TEXT_SEC)
    ], alignment="spaceBetween"), padding=15, bgcolor=COR_BG, border=ft.border.only(bottom=ft.border.BorderSide(1, COR_BORDER)))

    tabs = ft.Tabs(selected_index=0, indicator_color=COR_ACCENT, label_color=COR_ACCENT, unselected_label_color=COR_TEXT_SEC, divider_color="transparent",
        tabs=[
            ft.Tab(text="Jogos", icon="calendar_today", content=tab_jogos),
            ft.Tab(text="Previsão", icon="analytics", content=tab_prev),
            ft.Tab(text="Simulação", icon="table_chart", content=tab_sim),
            ft.Tab(text="H2H", icon="compare_arrows", content=tab_h2h),
            ft.Tab(text="Evolução", icon="show_chart", content=tab_evo),
        ], expand=True)

    page.add(header, tabs)

if __name__ == "__main__":
    ft.app(target=main)