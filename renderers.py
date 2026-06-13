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


# --------------------------------------------------------------------------- #
# Arte ASCII para condições do tempo (estilo wttr.in)
# --------------------------------------------------------------------------- #
ARTE_TEMPO: dict[str, tuple[str, str]] = {
    # condicao: (arte multi-linha, cor)
    "sol": (
        "\\   /\n"
        " .-.\n"
        "‒ (   ) ‒\n"
        " `-´\n"
        "/   \\",
        NEON_YELLOW,
    ),
    "nuvem": (
        "\n"
        "    .--.\n"
        " .-(    ).\n"
        "(___.__)__)\n",
        NEON_CYAN,
    ),
    "nublado": (
        "\n"
        "    .--.\n"
        " .-(    ).\n"
        "(___.__)__)\n",
        DIM,
    ),
    "chuva": (
        "    .-.\n"
        "   (   ).\n"
        "  (___(__)\n"
        "   ʻ‚ʻ‚ʻ‚ʻ\n"
        "   ‚ʻ‚ʻ‚ʻ",
        NEON_CYAN,
    ),
    "tempestade": (
        "    .-.\n"
        "   (   ).\n"
        "  (___(__)\n"
        "   ⚡ʻ‚⚡‚\n"
        "   ‚ʻ⚡ʻ‚",
        NEON_YELLOW,
    ),
    "neve": (
        "    .-.\n"
        "   (   ).\n"
        "  (___(__)\n"
        "   *  *  *\n"
        "  *  *  *",
        "#ffffff",
    ),
    "neblina": (
        "\n"
        " _ - _ - _ -\n"
        "  _ - _ - _\n"
        " _ - _ - _ -\n",
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

        linhas = Text()
        linhas.append(arte + "\n", style=cor)
        temp_line = Text(justify="center")
        if tmax is not None:
            temp_line.append(f"{tmax}°", style=f"bold {NEON_RED}")
        if tmin is not None:
            temp_line.append(f" / {tmin}°", style=NEON_CYAN)
        linhas.append(temp_line)
        linhas.append(f"\n{descricao}", style="bold")
        if dia.get("umidade") is not None:
            linhas.append(f"\n💧 {dia['umidade']}%", style=DIM)
        if dia.get("vento"):
            linhas.append(f"\n🌬 {dia['vento']}", style=DIM)

        cards.append(
            Panel(
                Align.center(linhas),
                title=f"[b]{dia.get('dia', '—')}[/b]",
                border_style=cor,
                padding=(1, 2),
                width=24,
            )
        )

    titulo = Text(f"🌤  Previsão do tempo — {local}", style=f"bold {NEON_CYAN}")
    return Group(titulo, Text(), Columns(cards, align="center", expand=False))


def render_tabela(dados: dict[str, Any]) -> RenderableType:
    """Tabela rica (rich.Table).

    Schema de `dados`:
        {"titulo": "Vendas", "colunas": ["Produto", "Qtd"], "linhas": [["A", "10"], ...]}
    """
    colunas = dados.get("colunas", [])
    linhas = dados.get("linhas", [])
    if not isinstance(colunas, list) or not colunas:
        raise ValueError("tabela: 'colunas' deve ser uma lista não vazia")

    tabela = Table(
        title=dados.get("titulo"),
        title_style=f"bold {NEON_CYAN}",
        border_style=NEON_GREEN,
        header_style=f"bold {NEON_GREEN}",
        expand=True,
    )
    for col in colunas:
        tabela.add_column(str(col))
    for linha in linhas:
        celulas = [str(c) for c in linha]
        # Preenche colunas faltantes para evitar erro de contagem.
        while len(celulas) < len(colunas):
            celulas.append("")
        tabela.add_row(*celulas[: len(colunas)])
    return tabela


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
        plt.plotsize(70, 20)
        plt.theme("dark")
        corpo = Text.from_ansi(plt.build())
    except Exception:
        # Fallback: barras horizontais com blocos unicode.
        corpo = _grafico_fallback(labels, valores, unidade)

    return Panel(corpo, title=f"📈 {titulo}", border_style=NEON_CYAN, padding=(1, 2))


def _grafico_fallback(
    labels: list[str], valores: list[float], unidade: str
) -> RenderableType:
    """Barras horizontais com blocos unicode (sem plotext)."""
    largura_max = 40
    pico = max(valores) if valores else 1.0
    pico = pico if pico > 0 else 1.0
    largura_label = max((len(lb) for lb in labels), default=4)

    texto = Text()
    for label, valor in zip(labels, valores):
        n = int(round((valor / pico) * largura_max))
        barra = BLOCO_CHEIO * n
        texto.append(f"{label:<{largura_label}} ", style=DIM)
        texto.append(barra, style=NEON_GREEN)
        texto.append(f" {valor:g}{unidade}\n", style="bold")
    return texto


def render_metricas(dados: dict[str, Any]) -> RenderableType:
    """Painel de métricas/gauges com barras coloridas por limiar.

    Schema de `dados`:
        {"titulo": "Sistema", "metricas": [
            {"label": "CPU", "valor": 42, "max": 100, "unidade": "%"}, ...]}
    """
    metricas = dados.get("metricas", [])
    if not isinstance(metricas, list) or not metricas:
        raise ValueError("metricas: 'metricas' deve ser uma lista não vazia")

    largura_barra = 30
    tabela = Table.grid(padding=(0, 2))
    tabela.add_column(justify="left", style="bold")
    tabela.add_column(justify="left")
    tabela.add_column(justify="right")

    for m in metricas:
        label = str(m.get("label", "—"))
        valor = _num(m.get("valor"))
        maximo = _num(m.get("max", 100)) or 100.0
        unidade = str(m.get("unidade", ""))
        pct = max(0.0, min(100.0, (valor / maximo) * 100.0))
        cor = _cor_por_limiar(pct)
        cheios = int(round((pct / 100.0) * largura_barra))
        barra = Text()
        barra.append(BLOCO_CHEIO * cheios, style=cor)
        barra.append(BLOCO_VAZIO * (largura_barra - cheios), style=DIM)
        valor_txt = Text(f"{valor:g}{unidade}", style=cor)
        tabela.add_row(label, barra, valor_txt)

    return Panel(
        tabela,
        title=f"🎛  {dados.get('titulo', 'Métricas')}",
        border_style=NEON_GREEN,
        padding=(1, 2),
    )


def render_alerta(dados: dict[str, Any]) -> RenderableType:
    """Banner de alerta com texto gigante (pyfiglet).

    Schema de `dados`:
        {"texto": "ALERTA", "subtitulo": "Detalhe...", "nivel": "info|aviso|critico"}
    """
    texto = str(dados.get("texto", "")).strip()
    if not texto:
        raise ValueError("alerta: 'texto' é obrigatório")

    nivel = str(dados.get("nivel", "info")).lower()
    cores = {"info": NEON_CYAN, "aviso": NEON_YELLOW, "critico": NEON_RED}
    cor = cores.get(nivel, NEON_CYAN)

    try:
        from pyfiglet import figlet_format

        arte = figlet_format(texto, font="standard")
    except Exception:
        arte = texto.upper()

    grupo: list[RenderableType] = [Text(arte, style=f"bold {cor}", justify="center")]
    if dados.get("subtitulo"):
        grupo.append(Text(str(dados["subtitulo"]), style="bold", justify="center"))

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

    grupo: list[RenderableType] = [Text(arte, justify="center")]
    legenda = dados.get("legenda")
    grupo.append(Text(str(legenda) if legenda else conteudo, style=DIM, justify="center"))

    return Panel(
        Align.center(Group(*grupo)),
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
    """Lista de tarefas / checklist com prioridades coloridas.

    Schema de `dados`:
        {"titulo": "Hoje", "itens": [
            {"texto": "Comprar pão", "feito": false, "prioridade": "alta|media|baixa"}]}
    """
    itens = dados.get("itens", [])
    if not isinstance(itens, list) or not itens:
        raise ValueError("tarefas: 'itens' deve ser uma lista não vazia")

    cores_prio = {"alta": NEON_RED, "media": NEON_YELLOW, "baixa": NEON_GREEN}
    texto = Text()
    for item in itens:
        feito = bool(item.get("feito"))
        marca = "✓" if feito else "☐"
        marca_cor = NEON_GREEN if feito else NEON_CYAN
        descricao = str(item.get("texto", ""))
        estilo_desc = f"{DIM} strike" if feito else "default"

        texto.append(f" {marca} ", style=f"bold {marca_cor}")
        texto.append(descricao, style=estilo_desc)
        prio = str(item.get("prioridade", "")).lower()
        if prio in cores_prio:
            texto.append(f"  [{prio}]", style=f"bold {cores_prio[prio]}")
        texto.append("\n")

    return Panel(
        texto,
        title=f"✅ {dados.get('titulo', 'Tarefas')}",
        border_style=NEON_GREEN,
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
}
