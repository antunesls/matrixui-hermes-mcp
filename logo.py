#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Logo ASCII do projeto.

Pode ser executado diretamente para visualizar o logo no terminal:
    python logo.py
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text

# --------------------------------------------------------------------------- #
# Arte ASCII do logo — HERMES (pyfiglet doom) + MATRIXUI (estilo Matrix)
# --------------------------------------------------------------------------- #
HERMES_LOGO_ASCII = r"""
 _   _ _____ ____  __  __ _____ ____
| | | | ____|  _ \|  \/  | ____/ ___|
| |_| |  _| | |_) | |\/| |  _| \___ \
|  _  | |___|  _ <| |  | | |___ ___) |
|_| |_|_____|_| \_\_|  |_|_____|____/
"""

# MATRIXUI em estilo "digital" (caixa de segmentos LCD/Matrix)
MATRIXUI_ASCII = r"""
╔╦╗╔═╗╔╦╗╦═╗╦╔═╗ ╦ ╦╦
║║║╠═╣ ║ ╠╦╝║╚═╗ ║ ║║
╩ ╩╩ ╩ ╩ ╩╚═╩╚═╝ ╚═╝╩
"""

# Chuva digital estilo Matrix (decoração lateral)
_RAIN = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ01"

SUBTITLE_ASCII = "A G E N T   O S   ·   T E R M I N A L   D A S H B O A R D"

DECO_LINE = "─" * 56
MATRIX_RAIN_LINE = "  " + "  ".join(_RAIN[i % len(_RAIN)] for i in range(28)) + "  "

# Versão do projeto (mantida aqui como fonte de verdade).
VERSION = "1.5.0"


def render_logo(cor: str = "#00ff9c", largura: int = 60) -> RenderableType:
    """Retorna o logo do projeto como um renderable Rich.

    Args:
        cor: Cor hex neon do logo (default: verde neon).
        largura: Largura do painel envolvente.

    Returns:
        Rich renderable pronto para exibição.
    """
    hermes_art = _gerar_arte_hermes(cor)
    matrixui_art = _gerar_arte_matrixui()

    rain = Text(MATRIX_RAIN_LINE, style=f"dim {cor}", justify="center")
    sep = Text(DECO_LINE, style=f"dim {cor}", justify="center")
    subtitulo = Text(SUBTITLE_ASCII, style=f"bold {cor}", justify="center")
    versao = Text(f"v{VERSION}", style="dim", justify="center")

    corpo = Group(
        rain,
        sep,
        hermes_art,
        Text(""),
        matrixui_art,
        sep,
        subtitulo,
        versao,
        rain,
    )

    return Panel(
        Align.center(corpo),
        border_style=cor,
        padding=(1, 4),
    )


def _gerar_arte_hermes(cor: str) -> RenderableType:
    """Gera a arte ASCII de HERMES via pyfiglet (doom) ou fallback."""
    try:
        from pyfiglet import figlet_format

        arte = figlet_format("HERMES", font="doom")
    except Exception:
        arte = HERMES_LOGO_ASCII

    return Text(arte.rstrip(), style=f"bold {cor}", justify="center")


def _gerar_arte_matrixui() -> RenderableType:
    """Gera MATRIXUI no estilo Matrix: verde intenso com efeito digital."""
    try:
        from pyfiglet import figlet_format

        arte = figlet_format("MATRIXUI", font="digital")
    except Exception:
        arte = MATRIXUI_ASCII

    # Verde Matrix clássico (#00ff00) para diferenciar do tema do HERMES
    linha = Text(arte.rstrip(), style="bold #00ff00", justify="center")
    return linha


# --------------------------------------------------------------------------- #
# Execução standalone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    console = Console()
    console.print()
    console.print(render_logo())
    console.print(f"  [dim]Hermes Terminal Dashboard v{VERSION}[/dim]")
    console.print()
