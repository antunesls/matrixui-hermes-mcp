#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Registry de renderizadores de skills.

Cada skill é uma função que recebe um dicionário `dados` (estrutura definida pelo
agente via tool MCP) e devolve um *renderable* do Rich (Panel, Table, Columns,
Text, etc.) para ser exibido no painel principal da TUI.

O dicionário `RENDERERS` mapeia o campo `tipo` do protocolo NDJSON para a função
correspondente. A TUI (`tui_display.py`) consulta esse registry em
`_processar_mensagem`.

Schemas de `dados` por skill estão documentados na docstring de cada `render_*`.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Callable

from rich.align import Align
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# --------------------------------------------------------------------------- #
# Paleta (espelha as cores neon do CSS da TUI)
# --------------------------------------------------------------------------- #
NEON_GREEN = "#00ff9c"
NEON_CYAN = "#00e5ff"
NEON_RED = "#ff5c7c"
NEON_YELLOW = "#ffd166"
DIM = "#5c6773"

# Caracteres de bloco para barras (do mais baixo ao mais cheio).
BLOCOS = " ▁▂▃▄▅▆▇█"
BLOCO_CHEIO = "█"
BLOCO_VAZIO = "░"

# --------------------------------------------------------------------------- #
# Sistema de largura dinâmica — atualizado pela TUI antes de cada render
# --------------------------------------------------------------------------- #
_PANEL_WIDTH: int = 80  # fallback para terminal padrão


def set_panel_width(width: int) -> None:
    """Chamado por tui_display.py para informar a largura real do painel."""
    global _PANEL_WIDTH
    _PANEL_WIDTH = max(60, width)


def _pw(frac: float = 1.0, minus: int = 0) -> int:
    """Fração da largura do painel menos margem fixa. Mínimo de 20."""
    return max(20, int(_PANEL_WIDTH * frac) - minus)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _cor_por_limiar(pct: float) -> str:
    """Retorna uma cor por faixa de percentual (verde/amarelo/vermelho)."""
    if pct < 60:
        return NEON_GREEN
    if pct < 85:
        return NEON_YELLOW
    return NEON_RED


def _num(valor: Any, default: float = 0.0) -> float:
    """Converte valor para float de forma tolerante."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _barra(pct: float, largura: int | None = None) -> Text:
    """Barra de progresso colorida por limiar, escala com o painel."""
    if largura is None:
        largura = _pw(0.88, 10)
    cor = _cor_por_limiar(pct)
    cheios = int(round((pct / 100.0) * largura))
    t = Text()
    t.append(BLOCO_CHEIO * cheios, style=f"bold {cor}")
    t.append(BLOCO_VAZIO * (largura - cheios), style=DIM)
    return t


def _figlet(texto: str, font: str = "standard") -> str:
    """Gera arte ASCII com pyfiglet; retorna texto puro se indisponível."""
    try:
        from pyfiglet import figlet_format
        return figlet_format(texto, font=font)
    except Exception:
        return texto.upper()


def _sep() -> Text:
    """Separador horizontal que acompanha a largura do painel."""
    return Text("─" * _pw(0.92), style=DIM)


# --------------------------------------------------------------------------- #
# Arte ASCII para condições do tempo (estilo wttr.in)
# --------------------------------------------------------------------------- #
ARTE_TEMPO: dict[str, tuple[str, str]] = {
    # condicao: (arte multi-linha, cor)
    "sol": (
        "  \\   /  \n"
        "   .-.   \n"
        "‒ (   ) ‒\n"
        "   `-´   \n"
        "  /   \\  ",
        NEON_YELLOW,
    ),
    "nuvem": (
        "          \n"
        "   .---.  \n"
        " .(     ). \n"
        "(___.__)__)\n",
        NEON_CYAN,
    ),
    "nublado": (
        "          \n"
        "   .---.  \n"
        " .(     ). \n"
        "(___.__)__)\n",
        DIM,
    ),
    "chuva": (
        "   .---.  \n"
        " .(     ). \n"
        "(___.__)__)\n"
        " ʻ‚ʻ‚ʻ‚ʻ‚ \n"
        " ‚ʻ‚ʻ‚ʻ‚ ",
        NEON_CYAN,
    ),
    "tempestade": (
        "   .---.  \n"
        " .(     ). \n"
        "(___.__)__)\n"
        "  ⚡ʻ‚⚡‚  \n"
        "  ‚ʻ⚡ʻ‚  ",
        NEON_YELLOW,
    ),
    "neve": (
        "   .---.  \n"
        " .(     ). \n"
        "(___.__)__)\n"
        "  *  *  * \n"
        " *  *  *  ",
        "#ffffff",
    ),
    "neblina": (
        "          \n"
        " _ - _ - _\n"
        "  _ - _ - \n"
        " _ - _ - _\n",
        DIM,
    ),
}


# --------------------------------------------------------------------------- #
# Renderizadores
# --------------------------------------------------------------------------- #
def render_previsao_tempo(dados: dict[str, Any]) -> RenderableType:
    """Card de previsão do tempo estilo ncurses/wttr.in.

    Schema de `dados`:
        {
          "local": "São Paulo, BR",
          "dias": [
            {
              "dia": "Hoje",
              "condicao": "sol|nuvem|nublado|chuva|tempestade|neve|neblina",
              "temp_max": 28, "temp_min": 18,
              "descricao": "Ensolarado",
              "umidade": 60,        # opcional
              "vento": "12 km/h"    # opcional
            }, ...
          ]
        }
    """
    local = str(dados.get("local", "—"))
    dias = dados.get("dias", [])
    if not isinstance(dias, list) or not dias:
        raise ValueError("previsao_tempo: 'dias' deve ser uma lista não vazia")

    cards: list[Panel] = []
    for dia in dias:
        condicao = str(dia.get("condicao", "nuvem")).lower()
        arte, cor = ARTE_TEMPO.get(condicao, ARTE_TEMPO["nuvem"])
        tmax = dia.get("temp_max")
        tmin = dia.get("temp_min")
        descricao = str(dia.get("descricao", condicao.capitalize()))

        linhas = Text(justify="center")
        linhas.append(arte + "\n", style=cor)
        linhas.append("\n")

        temp_line = Text(justify="center")
        if tmax is not None:
            temp_line.append(f" {tmax}°", style=f"bold {NEON_RED}")
        if tmax is not None and tmin is not None:
            temp_line.append(" ↕ ", style=DIM)
        if tmin is not None:
            temp_line.append(f"{tmin}° ", style=NEON_CYAN)
        linhas.append(temp_line)
        linhas.append(f"\n{descricao}", style="bold")
        if dia.get("umidade") is not None:
            linhas.append(f"\n💧 {dia['umidade']}%", style=DIM)
        if dia.get("vento"):
            linhas.append(f"\n🌬  {dia['vento']}", style=DIM)
        linhas.append("\n")

        # Largura do card escala com o painel: 4 cards cabem entre 32 e 54 chars.
        card_w = max(32, min(54, _pw(1.0) // max(1, len(dias)) - 2))
        cards.append(
            Panel(
                Align.center(linhas),
                title=f"[bold]{dia.get('dia', '—')}[/bold]",
                border_style=cor,
                padding=(1, max(2, card_w // 10)),
                width=card_w,
            )
        )

    headline = Rule(
        title=f"[bold {NEON_CYAN}]🌤  {local}[/bold {NEON_CYAN}]",
        style=DIM,
    )
    return Group(headline, Text(), Columns(cards, align="center", expand=False))


def render_tabela(dados: dict[str, Any]) -> RenderableType:
    """Tabela rica (rich.Table) com linhas alternadas e rodapé de contagem.

    Schema de `dados`:
        {"titulo": "Vendas", "colunas": ["Produto", "Qtd"], "linhas": [["A", "10"], ...]}
    """
    colunas = dados.get("colunas", [])
    linhas = dados.get("linhas", [])
    if not isinstance(colunas, list) or not colunas:
        raise ValueError("tabela: 'colunas' deve ser uma lista não vazia")

    titulo = dados.get("titulo")

    def _is_numeric(valor: str) -> bool:
        try:
            float(valor.replace(",", ".").replace("R$", "").replace("%", "").strip())
            return True
        except ValueError:
            return False

    # Detecta colunas numéricas pela primeira linha de dados.
    col_numerica = [False] * len(colunas)
    if linhas:
        primeira = [str(c) for c in linhas[0]]
        for i, cel in enumerate(primeira[: len(colunas)]):
            col_numerica[i] = _is_numeric(cel)

    tabela = Table(
        title=titulo,
        title_style=f"bold {NEON_CYAN}",
        border_style=NEON_GREEN,
        header_style=f"bold {NEON_GREEN}",
        row_styles=["", DIM],  # zebra: linhas pares em dim
        expand=True,
        show_footer=False,
    )
    for i, col in enumerate(colunas):
        justify = "right" if col_numerica[i] else "left"
        tabela.add_column(str(col), justify=justify)

    for linha in linhas:
        celulas = [str(c) for c in linha]
        while len(celulas) < len(colunas):
            celulas.append("")
        tabela.add_row(*celulas[: len(colunas)])

    n = len(linhas)
    rodape = Text(justify="center")
    rodape.append(f"── {n} registro{'s' if n != 1 else ''} ──", style=DIM)

    header = Rule(title=f"[bold {NEON_CYAN}]{titulo or 'Tabela'}[/bold {NEON_CYAN}]", style=DIM) if titulo else Text()
    return Group(header, tabela, rodape)


def render_grafico(dados: dict[str, Any]) -> RenderableType:
    """Gráfico de barras a partir de uma série de valores.

    Schema de `dados`:
        {"titulo": "Temp", "series": [{"label": "Seg", "valor": 23}, ...], "unidade": "°C"}
    """
    series = dados.get("series", [])
    if not isinstance(series, list) or not series:
        raise ValueError("grafico: 'series' deve ser uma lista não vazia")

    titulo = str(dados.get("titulo", "Gráfico"))
    unidade = str(dados.get("unidade", ""))
    labels = [str(s.get("label", "")) for s in series]
    valores = [_num(s.get("valor")) for s in series]

    corpo: RenderableType
    try:
        import plotext as plt

        plt.clear_figure()
        plt.bar(labels, valores)
        plt.title(f"{titulo} ({unidade})" if unidade else titulo)
        plt.plotsize(_pw(0.95), max(20, min(40, _PANEL_WIDTH // 5)))
        plt.theme("dark")
        corpo = Text.from_ansi(plt.build())
    except Exception:
        corpo = _grafico_fallback(labels, valores, unidade)

    headline = Rule(title=f"[bold {NEON_CYAN}]📈  {titulo}[/bold {NEON_CYAN}]", style=DIM)
    return Group(headline, Text(), corpo)


def _grafico_fallback(
    labels: list[str], valores: list[float], unidade: str
) -> RenderableType:
    """Barras horizontais coloridas por valor relativo (sem plotext)."""
    if not valores:
        return Text("(sem dados)", style=DIM)

    LARGURA = _pw(0.88, 10)
    pico = max(valores) or 1.0
    minimo = min(valores)
    largura_label = max((len(lb) for lb in labels), default=4)

    idx_max = valores.index(max(valores))
    idx_min = valores.index(min(valores))

    texto = Text()
    for i, (label, valor) in enumerate(zip(labels, valores)):
        # Cor relativa ao range dos dados (não ao limiar de % fixo).
        rel = (valor - minimo) / (pico - minimo + 1e-9)
        if rel >= 0.8:
            cor = NEON_RED
        elif rel >= 0.4:
            cor = NEON_YELLOW
        else:
            cor = NEON_GREEN

        n = int(round((valor / pico) * LARGURA))
        texto.append(f"{label:<{largura_label}} ", style=DIM)
        texto.append(BLOCO_CHEIO * n, style=f"bold {cor}")
        texto.append(BLOCO_VAZIO * (LARGURA - n), style=DIM)
        sufixo = ""
        if i == idx_max:
            sufixo = "  ▲ máx"
        elif i == idx_min:
            sufixo = "  ▼ mín"
        texto.append(f"  {valor:g}{unidade}{sufixo}\n", style="bold" if sufixo else "default")

    anotacao = Text()
    anotacao.append(f"\n  ▲ Máx: {max(valores):g}{unidade} ({labels[idx_max]})", style=f"bold {NEON_RED}")
    anotacao.append(f"    ▼ Mín: {min(valores):g}{unidade} ({labels[idx_min]})", style=f"bold {NEON_GREEN}")

    return Group(texto, anotacao)


def render_metricas(dados: dict[str, Any]) -> RenderableType:
    """Painel de métricas/gauges com barras largas coloridas por limiar.

    Schema de `dados`:
        {"titulo": "Sistema", "metricas": [
            {"label": "CPU", "valor": 42, "max": 100, "unidade": "%"}, ...]}
    """
    metricas = dados.get("metricas", [])
    if not isinstance(metricas, list) or not metricas:
        raise ValueError("metricas: 'metricas' deve ser uma lista não vazia")

    # Calcula percentuais uma vez para o sumário.
    pcts: list[tuple[float, str, float, str]] = []
    for m in metricas:
        valor = _num(m.get("valor"))
        maximo = _num(m.get("max", 100)) or 100.0
        unidade = str(m.get("unidade", ""))
        pct = max(0.0, min(100.0, (valor / maximo) * 100.0))
        pcts.append((pct, _cor_por_limiar(pct), valor, unidade))

    n_normal = sum(1 for p, *_ in pcts if p < 60)
    n_alerta = sum(1 for p, *_ in pcts if 60 <= p < 85)
    n_critico = sum(1 for p, *_ in pcts if p >= 85)

    sumario = Text()
    sumario.append(f"  ◉ {n_normal} normal{'is' if n_normal != 1 else ''}", style=f"bold {NEON_GREEN}")
    if n_alerta:
        sumario.append(f"   ⚠  {n_alerta} atenção", style=f"bold {NEON_YELLOW}")
    if n_critico:
        sumario.append(f"   🔴 {n_critico} crítico{'s' if n_critico != 1 else ''}", style=f"bold {NEON_RED}")

    grupo: list[RenderableType] = [sumario, Text()]

    wide = _PANEL_WIDTH > 110

    if wide:
        # Layout 2 colunas: pares de métricas lado a lado.
        bar_w = _pw(0.40, 14)
        for i in range(0, len(metricas), 2):
            par = list(zip(metricas, pcts))[i : i + 2]
            row_grid = Table.grid(padding=(0, 3), expand=True)
            row_grid.add_column(ratio=1)
            if len(par) > 1:
                row_grid.add_column(ratio=1)

            celulas: list[RenderableType] = []
            for m, (pct, cor, valor, unidade) in par:
                label = str(m.get("label", "—"))
                alerta_ico = " ⚠" if pct >= 85 else ""
                cheios = int(round((pct / 100.0) * bar_w))
                cel = Text()
                cel.append(f"{label:<10}", style="bold")
                cel.append("\n")
                cel.append(BLOCO_CHEIO * cheios, style=f"bold {cor}")
                cel.append(BLOCO_VAZIO * (bar_w - cheios), style=DIM)
                cel.append(f"  {valor:g}{unidade}", style=f"bold {cor}")
                cel.append(alerta_ico, style=f"bold {NEON_RED}")
                celulas.append(cel)

            row_grid.add_row(*celulas)
            grupo.append(row_grid)
            grupo.append(Text())
    else:
        # Layout 1 coluna: barra larga.
        bar_w = _pw(0.88, 10)
        for m, (pct, cor, valor, unidade) in zip(metricas, pcts):
            label = str(m.get("label", "—"))
            alerta_ico = "  ⚠ " if pct >= 85 else ""
            cheios = int(round((pct / 100.0) * bar_w))

            grupo.append(Text(f"  {label}", style="bold"))
            linha_barra = Text()
            linha_barra.append("  ")
            linha_barra.append(BLOCO_CHEIO * cheios, style=f"bold {cor}")
            linha_barra.append(BLOCO_VAZIO * (bar_w - cheios), style=DIM)
            linha_barra.append(f"  {valor:g}{unidade}", style=f"bold {cor}")
            linha_barra.append(alerta_ico, style=f"bold {NEON_RED}")
            grupo.append(linha_barra)
            grupo.append(Text())

    return Panel(
        Group(*grupo),
        title=f"🎛  {dados.get('titulo', 'Métricas')}",
        border_style=NEON_GREEN,
        padding=(1, 2),
    )


def render_alerta(dados: dict[str, Any]) -> RenderableType:
    """Banner de alerta dramático com texto gigante (pyfiglet) e moldura.

    Schema de `dados`:
        {"texto": "ALERTA", "subtitulo": "Detalhe...", "nivel": "info|aviso|critico"}
    """
    texto = str(dados.get("texto", "")).strip()
    if not texto:
        raise ValueError("alerta: 'texto' é obrigatório")

    nivel = str(dados.get("nivel", "info")).lower()
    cores = {"info": NEON_CYAN, "aviso": NEON_YELLOW, "critico": NEON_RED}
    icones = {"info": "ℹ ", "aviso": "⚠ ", "critico": "🚨"}
    cor = cores.get(nivel, NEON_CYAN)
    icone = icones.get(nivel, "🚨")

    arte = _figlet(texto, font="standard")
    moldura = "═" * _pw(0.92, 4)

    icone_line = Text(f"{icone}  {icone}  {icone}", style=f"bold {cor}", justify="center")
    arte_txt = Text(arte, style=f"bold {cor}", justify="center")
    linha_sup = Text(moldura, style=f"bold {cor}", justify="center")
    linha_inf = Text(moldura, style=f"bold {cor}", justify="center")

    grupo: list[RenderableType] = [icone_line, Text(), linha_sup, arte_txt, linha_inf]

    if dados.get("subtitulo"):
        grupo.append(Text())
        grupo.append(Text(str(dados["subtitulo"]), style=f"bold {NEON_YELLOW}", justify="center"))

    return Panel(
        Align.center(Group(*grupo)),
        title=f"🚨 {nivel.upper()}",
        border_style=cor,
        padding=(1, 2),
    )


def render_qrcode(dados: dict[str, Any]) -> RenderableType:
    """QR Code em ASCII.

    Schema de `dados`:
        {"conteudo": "https://...", "legenda": "Aponte a câmera"}
    """
    conteudo = str(dados.get("conteudo", "")).strip()
    if not conteudo:
        raise ValueError("qrcode: 'conteudo' é obrigatório")

    try:
        import qrcode

        qr = qrcode.QRCode(border=2)
        qr.add_data(conteudo)
        qr.make(fit=True)
        buf = io.StringIO()
        qr.print_ascii(out=buf, invert=True)
        arte = buf.getvalue()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"qrcode: falha ao gerar ({exc})") from exc

    legenda = dados.get("legenda")
    legenda_txt = Text(str(legenda) if legenda else conteudo, style=f"bold {DIM}", justify="center")
    instrucao = Text("📷  Aponte a câmera para o código", style=DIM, justify="center")

    return Panel(
        Align.center(Group(Text(arte, justify="center"), legenda_txt, instrucao)),
        title="🔳 QR CODE",
        border_style=NEON_GREEN,
        padding=(1, 2),
    )


def render_boas_vindas(dados: dict[str, Any]) -> RenderableType:
    """Tela de boas-vindas com logo do projeto e painel de informações do sistema.

    Schema de `dados` (todos opcionais — sem nada, exibe o padrão):
        {
          "titulo":    "HERMES AGENT OS",
          "subtitulo": "Terminal Dashboard",
          "mensagem":  "Aguardando comandos do agente...",
          "cor_tema":  "#00ff9c",
          "host":      "127.0.0.1",
          "porta":     9999,
          "versao":    "1.4.0"
        }
    """
    from logo import VERSION, render_logo

    cor = str(dados.get("cor_tema", NEON_GREEN))
    subtitulo = str(dados.get("subtitulo", "Terminal Dashboard  ·  Modo de Espera"))
    mensagem = str(dados.get("mensagem", "◈  Aguardando comandos do agente...  ◈"))
    host = str(dados.get("host", "127.0.0.1"))
    porta = str(dados.get("porta", "9999"))
    versao = str(dados.get("versao", VERSION))
    boot_time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    logo = render_logo(cor="#00ff00")

    # Grade de informações do sistema.
    info = Table.grid(padding=(0, 4))
    info.add_column(justify="right", style=f"dim {cor}")
    info.add_column(justify="left", style="bold")
    info.add_row("CANAL", f"TCP NDJSON  ·  {host}:{porta}")
    info.add_row("VERSÃO", f"v{versao}")
    info.add_row("BOOT", boot_time)
    info.add_row("STATUS", f"[bold {NEON_GREEN}]◉  ONLINE[/bold {NEON_GREEN}]")

    info_panel = Panel(
        Align.center(info),
        border_style=f"dim {cor}",
        padding=(0, 6),
    )

    sep = Text("─" * 56, style=f"dim {cor}", justify="center")
    msg = Text(mensagem, style=f"bold {cor}", justify="center")
    sub = Text(subtitulo, style="dim", justify="center")

    return Group(logo, Text(), info_panel, sep, msg, sub)


def render_tarefas(dados: dict[str, Any]) -> RenderableType:
    """Lista de tarefas com barra de progresso, seções por prioridade e checklist.

    Schema de `dados`:
        {"titulo": "Hoje", "itens": [
            {"texto": "Comprar pão", "feito": false, "prioridade": "alta|media|baixa"}]}
    """
    itens = dados.get("itens", [])
    if not isinstance(itens, list) or not itens:
        raise ValueError("tarefas: 'itens' deve ser uma lista não vazia")

    cores_prio = {"alta": NEON_RED, "media": NEON_YELLOW, "baixa": NEON_GREEN}
    total = len(itens)
    feitos = sum(1 for it in itens if bool(it.get("feito")))
    pct_prog = (feitos / total * 100.0) if total > 0 else 0.0
    cor_prog = _cor_por_limiar(pct_prog)

    # Barra de progresso larga no topo.
    barra_prog = _barra(pct_prog)
    progresso = Text()
    progresso.append("  ")
    progresso.append_text(barra_prog)
    progresso.append(f"  {feitos}/{total} concluída{'s' if feitos != 1 else ''}", style=f"bold {cor_prog}")

    grupo: list[RenderableType] = [progresso, Text()]

    # Agrupa itens por prioridade (alta → media → baixa → sem prioridade) e por status.
    ordem_prio = ["alta", "media", "baixa", ""]
    pendentes_por_prio: dict[str, list[dict]] = {k: [] for k in ordem_prio}
    concluidos: list[dict] = []

    for item in itens:
        if bool(item.get("feito")):
            concluidos.append(item)
        else:
            prio = str(item.get("prioridade", "")).lower()
            chave = prio if prio in cores_prio else ""
            pendentes_por_prio[chave].append(item)

    def _render_item(item: dict, feito: bool = False) -> Text:
        marca = "✓" if feito else "☐"
        marca_cor = NEON_GREEN if feito else NEON_CYAN
        descricao = str(item.get("texto", ""))
        estilo_desc = f"{DIM} strike" if feito else "default"
        prio = str(item.get("prioridade", "")).lower()

        t = Text()
        t.append(f"  {marca} ", style=f"bold {marca_cor}")
        t.append(descricao, style=estilo_desc)
        if prio in cores_prio and not feito:
            t.append(f"  [{prio.upper()}]", style=f"bold {cores_prio[prio]}")
        return t

    rotulos = {"alta": "ALTA PRIORIDADE", "media": "MÉDIA PRIORIDADE", "baixa": "BAIXA PRIORIDADE", "": "SEM PRIORIDADE"}
    for prio in ordem_prio:
        seccao = pendentes_por_prio[prio]
        if seccao:
            cor_sec = cores_prio.get(prio, DIM)
            grupo.append(Rule(title=f"[bold {cor_sec}]{rotulos[prio]}[/bold {cor_sec}]", style=DIM))
            for item in seccao:
                grupo.append(_render_item(item, feito=False))
            grupo.append(Text())

    if concluidos:
        grupo.append(Rule(title=f"[{DIM}]CONCLUÍDAS[/{DIM}]", style=DIM))
        mostrar = concluidos[-3:] if len(concluidos) > 3 else concluidos
        if len(concluidos) > 3:
            grupo.append(Text(f"  ... e mais {len(concluidos) - 3} concluída(s)", style=DIM))
        for item in mostrar:
            grupo.append(_render_item(item, feito=True))

    return Panel(
        Group(*grupo),
        title=f"✅ {dados.get('titulo', 'Tarefas')}",
        border_style=NEON_GREEN,
        padding=(1, 2),
    )


def render_noticias(dados: dict[str, Any]) -> RenderableType:
    """Lista de notícias com destaque para a primeira e lista compacta para as demais.

    Schema de `dados`:
        {
          "titulo": "Últimas Notícias",
          "fonte": "BBC Brasil",        # opcional
          "itens": [
            {
              "titulo": "Manchete da notícia",
              "resumo": "Breve resumo de 1-2 linhas.",
              "categoria": "Política",  # opcional
              "tempo": "há 2 horas"     # opcional
            }, ...
          ]
        }
    """
    itens = dados.get("itens", [])
    if not isinstance(itens, list) or not itens:
        raise ValueError("noticias: 'itens' deve ser uma lista não vazia")

    titulo_feed = str(dados.get("titulo", "Notícias"))
    fonte = dados.get("fonte")
    fonte_str = f" · {fonte}" if fonte else ""

    cores_cat: dict[str, str] = {}
    _paleta_cat = [NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED]

    def _cor_cat(cat: str) -> str:
        if cat not in cores_cat:
            cores_cat[cat] = _paleta_cat[len(cores_cat) % len(_paleta_cat)]
        return cores_cat[cat]

    grupo: list[RenderableType] = []

    # Cabeçalho com Rule.
    grupo.append(Rule(
        title=f"[bold {NEON_CYAN}]📰  {titulo_feed}{fonte_str}[/bold {NEON_CYAN}]",
        style=f"bold {NEON_CYAN}",
    ))
    grupo.append(Text())

    # Primeiro item em painel de DESTAQUE.
    destaque = itens[0]
    titulo_dest = str(destaque.get("titulo", "—"))
    resumo_dest = str(destaque.get("resumo", "")).strip()
    cat_dest = destaque.get("categoria")
    tempo_dest = destaque.get("tempo")

    corpo_dest = Text()
    corpo_dest.append(f"  {titulo_dest}\n", style=f"bold {NEON_YELLOW}")
    if resumo_dest:
        corpo_dest.append(f"  {resumo_dest}\n", style="default")
    meta_dest = Text()
    if cat_dest:
        meta_dest.append(f"  [{cat_dest.upper()}]", style=f"bold {_cor_cat(cat_dest)}")
    if tempo_dest:
        meta_dest.append(f"  {tempo_dest}", style=DIM)
    corpo_dest.append_text(meta_dest)

    grupo.append(Panel(
        corpo_dest,
        title=f"[bold {NEON_YELLOW}]★  DESTAQUE[/bold {NEON_YELLOW}]",
        border_style=NEON_YELLOW,
        padding=(1, 1),
    ))

    # Itens restantes em lista compacta.
    for i, item in enumerate(itens[1:], start=2):
        grupo.append(Rule(style=DIM))
        titulo_item = str(item.get("titulo", "—"))
        resumo_item = str(item.get("resumo", "")).strip()
        cat = item.get("categoria")
        tempo = item.get("tempo")

        # Grade: número + título + [CAT] + tempo alinhados.
        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(width=4, justify="left")
        grid.add_column(ratio=1, justify="left")
        grid.add_column(width=12, justify="right")

        num_txt = Text(f"[{i}]", style=f"bold {NEON_CYAN}")
        tit_txt = Text(titulo_item, style=f"bold {NEON_GREEN}")
        cat_tempo = Text()
        if cat:
            cat_tempo.append(f"[{cat[:8].upper()}]", style=f"bold {_cor_cat(cat)}")
        if tempo:
            cat_tempo.append(f" {tempo}", style=DIM)
        grid.add_row(num_txt, tit_txt, cat_tempo)

        if resumo_item:
            res_grid = Table.grid(padding=(0, 1), expand=True)
            res_grid.add_column(width=4)
            res_grid.add_column(ratio=1)
            res_grid.add_row(Text(), Text(resumo_item, style=DIM))
            grupo.append(grid)
            grupo.append(res_grid)
        else:
            grupo.append(grid)

    return Panel(
        Group(*grupo),
        title=f"📰  {titulo_feed.upper()}",
        border_style=NEON_CYAN,
        padding=(1, 2),
    )


def render_jogos_futebol(dados: dict[str, Any]) -> RenderableType:
    """Painel de jogos com card grande para ao vivo e seções por status.

    Schema de `dados`:
        {
          "titulo": "Rodada 15 — Brasileirão",
          "data": "13/06/2026",          # opcional
          "jogos": [
            {
              "time_casa": "Flamengo",
              "time_fora": "Palmeiras",
              "placar_casa": 2,           # opcional (omitir = jogo não iniciado)
              "placar_fora": 1,           # opcional
              "status": "encerrado|ao_vivo|agendado",
              "horario": "16:00",         # opcional, usado em agendado
              "estadio": "Maracanã",      # opcional
              "destaque": "Gol 45'"       # opcional, destaque da partida
            }, ...
          ]
        }
    """
    jogos = dados.get("jogos", [])
    if not isinstance(jogos, list) or not jogos:
        raise ValueError("jogos_futebol: 'jogos' deve ser uma lista não vazia")

    titulo_rodada = str(dados.get("titulo", "Jogos de Futebol"))
    data = dados.get("data")
    data_str = f"  ·  {data}" if data else ""

    # Separa por seção.
    ao_vivo = [j for j in jogos if str(j.get("status", "")).lower() == "ao_vivo"]
    encerrados = [j for j in jogos if str(j.get("status", "")).lower() == "encerrado"]
    agendados = [j for j in jogos if str(j.get("status", "")).lower() == "agendado"]

    grupo: list[RenderableType] = []

    headline = Rule(
        title=f"[bold {NEON_YELLOW}]⚽  {titulo_rodada}{data_str}[/bold {NEON_YELLOW}]",
        style=f"bold {NEON_YELLOW}",
    )
    grupo.append(headline)

    # ── AO VIVO ──
    if ao_vivo:
        grupo.append(Rule(title=f"[bold {NEON_RED}]🔴  AO VIVO[/bold {NEON_RED}]", style=NEON_RED))
        for jogo in ao_vivo:
            tc = str(jogo.get("time_casa", "—")).upper()
            tf = str(jogo.get("time_fora", "—")).upper()
            pc = jogo.get("placar_casa")
            pf = jogo.get("placar_fora")
            estadio = jogo.get("estadio", "")
            destaque = jogo.get("destaque", "")

            # Placar em pyfiglet — fonte maior "banner" em telas largas.
            if pc is not None and pf is not None:
                font_score = "banner" if _PANEL_WIDTH > 100 else "big"
                score_arte = _figlet(f"{pc}  x  {pf}", font=font_score)
                score_txt = Text(score_arte, style=f"bold {NEON_YELLOW}", justify="center")
            else:
                score_txt = Text("AO VIVO", style=f"bold {NEON_RED}", justify="center")

            times_txt = Text(justify="center")
            times_txt.append(f"{tc}  ", style=f"bold {NEON_GREEN}")
            times_txt.append("vs", style=DIM)
            times_txt.append(f"  {tf}", style=f"bold {NEON_CYAN}")

            corpo_live: list[RenderableType] = [times_txt, score_txt]
            if destaque:
                corpo_live.append(Text(f"  ↳ {destaque}", style=f"bold {NEON_YELLOW}", justify="center"))
            if estadio:
                corpo_live.append(Text(f"📍 {estadio}", style=DIM, justify="center"))

            grupo.append(Panel(
                Align.center(Group(*corpo_live)),
                border_style=NEON_RED,
                padding=(1, 2),
            ))

    # ── ENCERRADOS ──
    if encerrados:
        grupo.append(Rule(title=f"[bold {NEON_GREEN}]✅  ENCERRADOS[/bold {NEON_GREEN}]", style=DIM))
        for jogo in encerrados:
            tc = str(jogo.get("time_casa", "—"))
            tf = str(jogo.get("time_fora", "—"))
            pc = jogo.get("placar_casa")
            pf = jogo.get("placar_fora")
            estadio = jogo.get("estadio", "")
            destaque = jogo.get("destaque", "")

            # Destaca o vencedor em verde.
            grid = Table.grid(padding=(0, 2), expand=True)
            grid.add_column(ratio=1, justify="right")
            grid.add_column(width=9, justify="center")
            grid.add_column(ratio=1, justify="left")
            grid.add_column(justify="right")

            if pc is not None and pf is not None:
                cor_casa = NEON_GREEN if pc > pf else (DIM if pc < pf else "bold")
                cor_fora = NEON_GREEN if pf > pc else (DIM if pf < pc else "bold")
                placar_txt = Text(f"{pc}  ×  {pf}", style=f"bold {NEON_YELLOW}", justify="center")
            else:
                cor_casa = cor_fora = "bold"
                placar_txt = Text("× ×", style=DIM, justify="center")

            est_txt = Text(f"[{estadio}]" if estadio else "", style=DIM)
            grid.add_row(
                Text(tc, style=f"bold {cor_casa}"),
                placar_txt,
                Text(tf, style=f"bold {cor_fora}"),
                est_txt,
            )
            grupo.append(grid)
            if destaque:
                grupo.append(Text(f"    ↳ {destaque}", style=f"{NEON_YELLOW}"))

    # ── AGENDA ──
    if agendados:
        grupo.append(Rule(title=f"[{NEON_CYAN}]🕐  AGENDA[/{NEON_CYAN}]", style=DIM))
        for jogo in agendados:
            tc = str(jogo.get("time_casa", "—"))
            tf = str(jogo.get("time_fora", "—"))
            horario = str(jogo.get("horario", "—"))
            estadio = jogo.get("estadio", "")

            grid = Table.grid(padding=(0, 2), expand=True)
            grid.add_column(width=7, justify="left")
            grid.add_column(ratio=1, justify="right")
            grid.add_column(width=5, justify="center")
            grid.add_column(ratio=1, justify="left")
            grid.add_column(justify="right")

            grid.add_row(
                Text(horario, style=f"bold {NEON_CYAN}"),
                Text(tc, style="bold"),
                Text(" vs ", style=DIM),
                Text(tf, style="bold"),
                Text(f"[{estadio}]" if estadio else "", style=DIM),
            )
            grupo.append(grid)

    return Panel(
        Group(*grupo),
        title=f"⚽  {titulo_rodada.upper()}",
        border_style=NEON_YELLOW,
        padding=(1, 2),
    )


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
RENDERERS: dict[str, Callable[[dict[str, Any]], RenderableType]] = {
    "previsao_tempo": render_previsao_tempo,
    "tabela": render_tabela,
    "grafico": render_grafico,
    "metricas": render_metricas,
    "alerta": render_alerta,
    "qrcode": render_qrcode,
    "tarefas": render_tarefas,
    "boas_vindas": render_boas_vindas,
    "noticias": render_noticias,
    "jogos_futebol": render_jogos_futebol,
}

# Títulos amigáveis para o border_title do painel principal.
TITULOS_SKILL: dict[str, str] = {
    "previsao_tempo": "🌤  PREVISÃO DO TEMPO",
    "tabela": "📊 TABELA",
    "grafico": "📈 GRÁFICO",
    "metricas": "🎛  MÉTRICAS",
    "alerta": "🚨 ALERTA",
    "qrcode": "🔳 QR CODE",
    "tarefas": "✅ TAREFAS",
    "boas_vindas": "⌂  BOAS-VINDAS",
    "noticias": "📰 NOTÍCIAS",
    "jogos_futebol": "⚽ JOGOS DE FUTEBOL",
}
