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


def criar_stat_box(label, value, color="white"):
    return ft.Container(
        content=ft.Column([
            ft.Text(label, size=10, color=COR_TEXT_SEC),
            ft.Text(str(value), size=20, weight="bold", color=color)
        ], horizontal_alignment="center", spacing=2),
        bgcolor="#0DFFFFFF",
        border_radius=10,
        padding=10,
        expand=True
    )


def criar_tabela_estilizada(df):
    if df is None or df.empty:
        return ft.Text("Sem dados disponíveis.", color=COR_TEXT_SEC)

    cols = [
        ft.DataColumn(ft.Text(str(c), weight="bold", color=COR_ACCENT))
        for c in df.columns
    ]
    rows = [
        ft.DataRow([ft.DataCell(ft.Text(str(v), size=11)) for v in row])
        for i, row in df.iterrows()
    ]
    return ft.DataTable(
        columns=cols,
        rows=rows,
        heading_row_color="#1AFFFFFF",
        width=float('inf'),
        column_spacing=15
    )


def main(page: ft.Page):
    page.title = "AtletiQ 2.1"
    page.theme_mode = "dark"
    page.bgcolor = COR_BG
    page.padding = 0

    # SPLASH SCREEN
    txt_load = ft.Text("Iniciando AtletiQ 2.1...", color=COR_TEXT_SEC)
    pb = ft.ProgressBar(width=300, color=COR_ACCENT)
    splash_content = ft.Column([
        ft.Icon("sports_soccer", size=80, color=COR_ACCENT),
        ft.Text("AtletiQ 2.1", size=40, weight="bold"),
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
    df_total['Date'] = pd.to_datetime(
        df_total['Date'], utc=True
    ).dt.tz_localize(None)
    df_total.to_csv(CACHE_FILE, index=False)

    df_res = df_total[df_total['FTHG'].notna()].copy()
    mask_fut = (df_total['FTHG'].isna()) & (df_total['Date'].dt.year == ano_atual)
    df_fut = df_total[mask_fut].copy()

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
        odds = prever_jogo_especifico(
            mandante, visitante, modelos, encoder, time_stats, cols_model
        )
        res_h2h, df_h2h = gerar_confronto_direto(
            df_total, mandante, visitante
        )

        def fechar(e):
            modal.open = False
            page.update()

        modal_content = ft.Column([
            ft.Row([
                ft.Text("Match Center", size=18, weight="bold"),
                ft.IconButton(ft.Icons.CLOSE, on_click=fechar)
            ], alignment="spaceBetween"),
            ft.Divider(color=COR_BORDER),
            ft.Row([
                ft.Text(
                    mandante, weight="bold", size=15,
                    expand=True, text_align="right"
                ),
                ft.Container(
                    ft.Text("VS", size=10, weight="bold", color="black"),
                    bgcolor=COR_ACCENT, padding=5, border_radius=5
                ),
                ft.Text(
                    visitante, weight="bold", size=15,
                    expand=True, text_align="left"
                )
            ]),
            ft.Text("IA Predictor", size=13, color=COR_ACCENT, weight="bold"),
            ft.Row([
                criar_stat_box(
                    mandante, f"{odds.get('Casa', 0):.0%}",
                    CORES_TIMES.get(mandante, COR_ACCENT)
                ),
                criar_stat_box("Empate", f"{odds.get('Empate', 0):.0%}", "grey"),
                criar_stat_box(
                    visitante, f"{odds.get('Visitante', 0):.0%}", "#00B0FF"
                )
            ]),
            ft.Text(
                f"Histórico ({res_h2h['total_partidas']} partidas)",
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
            ]),
            ft.Text("Últimos resultados:", size=11, color=COR_TEXT_SEC),
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
    conteudo_jogos = []
    if not df_fut.empty:
        df_fut['Rodada_Num'] = pd.to_numeric(df_fut['Rodada'], errors='coerce')
        for r in sorted(df_fut['Rodada_Num'].dropna().unique()):
            jogos_r = ft.ResponsiveRow(spacing=10)
            df_rodada = df_fut[df_fut['Rodada_Num'] == r]
            conteudo_jogos.append(
                ft.Text(f"Rodada {int(r)}", size=16, weight="bold", color=COR_ACCENT)
            )
            for _, row in df_rodada.iterrows():
                card_content = ft.Row([
                    ft.Column([
                        ft.Text(
                            row['Date'].strftime("%d/%m - %H:%M"),
                            size=10, color=COR_TEXT_SEC
                        ),
                        ft.Row([
                            ft.Text(
                                row['HomeTeam'], size=13, weight="bold",
                                expand=True, text_align="right"
                            ),
                            ft.Text("vs", size=10, color=COR_TEXT_SEC),
                            ft.Text(
                                row['AwayTeam'], size=13, weight="bold",
                                expand=True, text_align="left"
                            )
                        ], spacing=10)
                    ], expand=True),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=COR_TEXT_SEC, size=16)
                ], alignment="center")

                card = criar_card(
                    card_content, padding=12,
                    on_click=lambda _, r=row: abrir_detalhes(r)
                )
                jogos_r.controls.append(ft.Container(content=card, col={"xs": 12, "sm": 6}))
            conteudo_jogos.append(jogos_r)
    tab_jogos = ft.Container(
        content=ft.Column(conteudo_jogos, scroll=ft.ScrollMode.AUTO),
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

    # ABA 3: SIMULAÇÃO
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
        area_sim.controls = [criar_tabela_estilizada(res)]
        btn_s.content = ft.Text("SIMULAR CAMPEONATO")
        page.update()

    btn_s = ft.ElevatedButton(
        "SIMULAR CAMPEONATO", bgcolor=COR_ACCENT,
        color="black", on_click=rodar, width=float('inf')
    )
    tab_sim = ft.Container(
        content=ft.Column([btn_s, area_sim], scroll=ft.ScrollMode.AUTO),
        padding=20
    )

    # HEADER E TABS
    header_content = ft.Row([
        ft.Row([
            ft.Icon("sports_soccer", color=COR_ACCENT),
            ft.Text("AtletiQ 2.1", size=22, weight="bold", color="white")
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
        tabs=[
            ft.Tab(text="Jogos", icon="calendar_today", content=tab_jogos),
            ft.Tab(text="Artilharia", icon="local_fire_department", content=tab_artilharia),
            ft.Tab(text="Simulação", icon="table_chart", content=tab_sim)
        ],
        expand=True
    )

    page.add(header, tabs)


if __name__ == "__main__":
    ft.app(target=main)